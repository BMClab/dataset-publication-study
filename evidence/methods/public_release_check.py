"""Check direct reads of the public PPDS v1.0.0 record without credentials.

Usage: python public_release_check.py OUTPUT.json

Requires duckdb and polars (the versions in the repository lock file) and
network access to zenodo.org. Every request is a read-only GET or HEAD.
"""

import hashlib
import json
import platform
import sys
import time
import urllib.request
from datetime import datetime, timezone

import duckdb
import polars as pl

RECORD = 24432612
URL = "https://zenodo.org/api/records/{}/files/{{}}/content".format(RECORD)
TRIALS = URL.format("trials.parquet")
PRESSURE = URL.format("pressure.parquet")
TRIAL_KEY = {"subject": "s045", "condition": "wc", "trial": 3}
COHORT_SQL = "SELECT count(*) AS trials, count(DISTINCT subject) AS participants FROM trials WHERE Age >= 60"

# Fixed expectations for v1.0.0. The cohort counts are those DuckDB returned in the
# first run of this check; the 34 participants agree with the benchmark cohort. The trial
# expectations are the trial table's recorded cell and frame counts for that trial.
REFERENCE = {
    "cohort": {"rows": [[1174, 34]], "origin": "Counts DuckDB returned in the first run of this check; 34 participants, as in the benchmark cohort"},
    "trial": {"trial_id": 1566, "n_cells": 32266, "n_frames": 280, "origin": "n_cells and n_frames columns of trials.parquet"},
}


def digest(rows):
    return hashlib.sha256(json.dumps(rows, default=str).encode()).hexdigest()


def http_log(con, file_url):
    rows = con.sql(
        "SELECT request.type, request.headers['Range'], response.status, "
        "TRY_CAST(response.headers['content-length'] AS BIGINT) "
        "FROM duckdb_logs_parsed('HTTP') WHERE request.url = ?", params=[file_url]).fetchall()
    keys = ["method", "range", "status", "content_length"]
    return [dict(zip(keys, row)) for row in rows]


def rate_limit_headers():
    """DuckDB's HTTP log redacts these headers, so read them with one 1-byte range request."""
    request = urllib.request.Request(TRIALS, headers={"Range": "bytes=0-0"})
    with urllib.request.urlopen(request, timeout=30) as response:
        names = ["x-ratelimit-limit", "x-ratelimit-remaining", "x-ratelimit-reset", "retry-after"]
        return {"status": response.status, **{name: response.headers.get(name) for name in names}}


def summarize(log):
    gets = [r for r in log if r["method"] == "GET"]
    unknown = sum(r["content_length"] is None for r in gets)
    return {
        "requests": len(log),
        "get_requests": len(gets),
        "head_requests": len(log) - len(gets),
        "declared_get_body_bytes": sum(r["content_length"] for r in gets if r["content_length"] is not None),
        "gets_without_content_length": unknown,
        "byte_total": "complete" if unknown == 0 else "partial: lower bound, some GET lengths unknown",
        "statuses": sorted({str(r["status"]) for r in log}),
    }


def cohort_verdict(rows):
    return "pass" if [list(r) for r in rows] == REFERENCE["cohort"]["rows"] else "mismatch"


def cohort_duckdb():
    con = duckdb.connect()
    con.sql("CALL enable_logging('HTTP')")
    # Timer and request log both start here and cover view creation plus the query.
    start = time.perf_counter()
    con.read_parquet(TRIALS).create_view("trials")
    setup = time.perf_counter() - start
    rows = con.sql(COHORT_SQL).fetchall()
    elapsed = time.perf_counter() - start
    log = http_log(con, TRIALS)
    return {"reader": "duckdb", "status": cohort_verdict(rows),
            "timer": "view creation and query; matches the request log",
            "seconds": round(elapsed, 3), "setup_seconds": round(setup, 3),
            "rows": rows, "sha256": digest(rows), "http": summarize(log), "http_log": log}


def cohort_polars(style):
    start = time.perf_counter()
    try:
        if style == "sql":
            frame = pl.SQLContext(trials=pl.scan_parquet(TRIALS)).execute(COHORT_SQL)
        else:
            frame = pl.scan_parquet(TRIALS).filter(pl.col("Age") >= 60).select(
                pl.len().alias("trials"), pl.col("subject").n_unique().alias("participants"))
        rows = frame.collect().rows()
    except Exception as exc:  # the observation is the failure itself
        return {"reader": f"polars_{style}", "status": "fail", "timer": "scan setup and query",
                "seconds": round(time.perf_counter() - start, 3),
                "error_class": type(exc).__name__, "error": str(exc)}
    return {"reader": f"polars_{style}", "status": cohort_verdict(rows), "timer": "scan setup and query",
            "seconds": round(time.perf_counter() - start, 3), "rows": rows, "sha256": digest(rows)}


def one_trial_duckdb():
    with duckdb.connect() as lookup:
        trial_id, n_cells, n_frames = lookup.sql(
            f"SELECT trial_id, n_cells, n_frames FROM read_parquet('{TRIALS}') "
            "WHERE subject = ? AND condition = ? AND trial = ?",
            params=list(TRIAL_KEY.values())).fetchall()[0]
    con = duckdb.connect()
    con.sql("CALL enable_logging('HTTP')")
    start = time.perf_counter()
    rows = con.sql(
        f"SELECT frame, y, x, value FROM read_parquet('{PRESSURE}') WHERE trial_id = ? ORDER BY frame, y, x",
        params=[trial_id]).fetchall()
    elapsed = time.perf_counter() - start
    log = http_log(con, PRESSURE)
    reference = REFERENCE["trial"]
    checks = {
        "trial_id_matches_reference": trial_id == reference["trial_id"],
        "trials_table_matches_reference": (n_cells, n_frames) == (reference["n_cells"], reference["n_frames"]),
        "row_count_equals_n_cells": len(rows) == n_cells,
        "cells_unique": len({r[:3] for r in rows}) == len(rows),
        "frames_within_recording": all(0 <= r[0] < n_frames for r in rows),
        "values_positive": all(r[3] > 0 for r in rows),
    }
    return {
        "reader": "duckdb",
        "selection": {**TRIAL_KEY, "trial_id": trial_id},
        "trials_table": {"n_cells": n_cells, "n_frames": n_frames},
        "query": "Fetch every stored (frame, y, x, value) row for the trial into Python",
        "status": "pass" if all(checks.values()) else "mismatch",
        "checks": checks,
        "timer": "pressure query and row transfer to Python; the trial lookup ran in a separate connection",
        "seconds": round(elapsed, 3),
        "rows_returned": len(rows),
        "rows_sha256": digest(rows),
        "http": summarize(log),
        "http_log": log,
    }


def main(output):
    record = {
        "purpose": "Direct reads of the public PPDS v1.0.0 Zenodo record without credentials",
        "record": RECORD,
        "files": {"trials": TRIALS, "pressure": PRESSURE},
        "started_utc": datetime.now(timezone.utc).isoformat(),
        "python": platform.python_version(),
        "packages": {"duckdb": duckdb.__version__, "polars": pl.__version__},
        "byte_counting": "Declared Content-Length of GET responses from DuckDB's HTTP log; not measured wire bytes",
        "repetitions": "One observation per reader and task over the public internet",
        "reference": REFERENCE,
        "rate_limit_headers": rate_limit_headers(),
        "cohort_selection": {"sql": COHORT_SQL,
                             "results": [cohort_duckdb(), cohort_polars("scan"), cohort_polars("sql")]},
        "one_trial": one_trial_duckdb(),
        "not_checked": ["mesh retrieval", "full pressure read", "authenticated access"],
    }
    record["finished_utc"] = datetime.now(timezone.utc).isoformat()
    with open(output, "w") as stream:
        json.dump(record, stream, indent=2)
        stream.write("\n")


if __name__ == "__main__":
    main(sys.argv[1])
