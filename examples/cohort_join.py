"""Compare two readers on the same synthetic participant–trial–force join."""

from pathlib import Path
from tempfile import TemporaryDirectory
from time import perf_counter

import duckdb
import polars as pl

SQL = """
SELECT p.participant, COUNT(DISTINCT t.trial_id) AS trials,
       COUNT(*) AS samples, MAX(f.force_n) AS peak_force_n
FROM participants p
JOIN trials t ON t.participant = p.participant
JOIN forces f ON f.trial_id = t.trial_id
WHERE p.age_years >= 60 AND t.condition IN ('slow', 'comfortable')
GROUP BY p.participant
ORDER BY p.participant
"""


def write_fixture(directory):
    tables = {
        "participants": {"participant": ["A", "B", "C"], "age_years": [60, 72, 59]},
        "trials": {
            "trial_id": [1, 2, 3, 4, 5],
            "participant": ["A", "A", "B", "B", "C"],
            "condition": ["slow", "comfortable", "comfortable", "fast", "slow"],
        },
        "forces": {
            "trial_id": [1, 1, 2, 3, 3, 4, 5],
            "force_n": [180, 200, 220, 170, 190, 800, 900],
        },
    }
    for name, columns in tables.items():
        pl.DataFrame(columns).write_parquet(directory / f"{name}.parquet")
    return {name: directory / f"{name}.parquet" for name in tables}


def duckdb_query(files):
    with duckdb.connect() as connection:
        for name, path in files.items():
            connection.read_parquet(str(path)).create_view(name)
        return connection.sql(SQL).fetchall()


def polars_query(files):
    tables = {name: pl.scan_parquet(path) for name, path in files.items()}
    with pl.SQLContext(tables) as context:
        return context.execute(SQL).collect().rows()


def main():
    expected = [("A", 2, 3, 220), ("B", 1, 2, 190)]
    with TemporaryDirectory() as directory:
        files = write_fixture(Path(directory))
        for label, query in [("DuckDB", duckdb_query), ("Polars", polars_query)]:
            start = perf_counter()
            rows = query(files)
            elapsed = perf_counter() - start
            if rows != expected:
                raise ValueError(f"{label}: expected {expected!r}, got {rows!r}")
            print(f"{label}: {rows} ({elapsed * 1000:.1f} ms)")
    print("Both readers matched the hand-calculated reference.")


if __name__ == "__main__":
    main()
