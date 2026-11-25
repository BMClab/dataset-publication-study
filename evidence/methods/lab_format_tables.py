"""Render the PPDS tables from checked benchmark observations in a receipts directory."""

import argparse
import json
from itertools import product
from pathlib import Path
from statistics import median

TASKS = ("trial", "cohort_force", "all_pressure", "mesh")
LABEL = {
    "sql_parquet": "DuckDB / Parquet",
    "polars_parquet": "Polars / Parquet",
    "pandas_parquet": "pandas / Parquet",
    "pandas_range": "pandas / Parquet, seekable HTTP",
    "sql_duckdb": "DuckDB / native DuckDB",
    "sql_vortex": "DuckDB / Vortex",
    "polars_vortex": "Polars / Vortex",
    "sql_compact_vortex": "DuckDB / compact Vortex",
    "polars_compact_vortex": "Polars / compact Vortex",
}


def matrix(directory, filename, engines, repeat_count):
    report = json.loads((directory / f"lab_formats_{filename}.json").read_text())
    actual = {(r["engine"], r["task"], r["repetition"]): r for r in report["rows"]}
    expected = set(product(engines, TASKS, range(1, repeat_count + 1)))
    if set(actual) != expected or len(actual) != len(report["rows"]):
        raise ValueError(f"Incomplete or duplicate measurements in {filename}")
    for key, r in actual.items():
        if not r["matches"] or r["result"] != report["reference"][key[1]]:
            raise ValueError(f"Result mismatch in {filename}: {key}")
    return list(actual.values())


def render(directory):
    local = matrix(directory, "local", [e for e in LABEL if e != "pandas_range"], 3)
    network = matrix(directory, "https", LABEL, 2)

    def sampled(rows, engine, task, measure):
        return median(
            measure(r) for r in rows if r["engine"] == engine and r["task"] == task
        )

    print(
        "| Reader and storage | One trial | Cohort force join | All pressure | One STL | Peak RSS, all pressure |"
    )
    print("|---|---:|---:|---:|---:|---:|")
    for e, label in LABEL.items():
        if e == "pandas_range":
            continue
        cells = [
            f"{sampled(local, e, t, lambda r: r['first_s']) * 1000:,.0f} / "
            f"{sampled(local, e, t, lambda r: r['repeat_s']) * 1000:,.0f}"
            for t in TASKS
        ]
        rss = sampled(local, e, "all_pressure", lambda r: r["process_peak_MiB"])
        print("|", " | ".join([label, *cells, f"{rss:,.0f} MiB"]), "|")
    print(
        "\n| Reader and storage | One trial | Cohort force join | All pressure | One STL |"
    )
    print("|---|---:|---:|---:|---:|")
    for e, label in LABEL.items():
        cells = [
            f"{sampled(network, e, t, lambda r: r['first_http']['bytes']) / 1e6:.2f} / "
            f"{sampled(network, e, t, lambda r: r['first_http']['requests']):g}"
            for t in TASKS
        ]
        print("|", " | ".join([label, *cells]), "|")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("receipts", type=Path)
    render(parser.parse_args().receipts)
