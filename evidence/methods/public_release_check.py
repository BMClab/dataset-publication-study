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
    return {
        "requests": len(log),
        "get_requests": len(gets),
        "head_requests": len(log) - len(gets),
        "declared_get_body_bytes": sum(r["content_length"] or 0 for r in gets),
        "statuses": sorted({str(r["status"]) for r in log}),
    }


def cohort_duckdb():
    con = duckdb.connect()
    con.sql("CALL enable_logging('HTTP')")
    con.read_parquet(TRIALS).create_view("trials")
    start = time.perf_counter()
    rows = con.sql(COHORT_SQL).fetchall()
    elapsed = time.perf_counter() - start
    log = http_log(con, TRIALS)
    return {"reader": "duckdb", "status": "pass", "seconds": round(elapsed, 3),
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
        return {"reader": f"polars_{style}", "status": "fail", "seconds": round(time.perf_counter() - start, 3),
                "error_class": type(exc).__name__, "error": str(exc)}
    return {"reader": f"polars_{style}", "status": "pass", "seconds": round(time.perf_counter() - start, 3),
            "rows": rows, "sha256": digest(rows)}


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
        f"SELECT count(*), max(frame), max(value) FROM read_parquet('{PRESSURE}') WHERE trial_id = ?",
        params=[trial_id]).fetchall()
    elapsed = time.perf_counter() - start
    count, max_frame, _ = rows[0]
    log = http_log(con, PRESSURE)
    return {
        "reader": "duckdb",
        "selection": {**TRIAL_KEY, "trial_id": trial_id},
        "expected_from_trials_table": {"n_cells": n_cells, "n_frames": n_frames},
        "status": "pass" if count == n_cells and max_frame < n_frames else "fail",
        "timer": "pressure query only; trial lookup ran in a separate connection",
        "seconds": round(elapsed, 3),
        "rows": rows,
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
