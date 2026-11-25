"""Matched analytical workloads for the lab-format study. Public readers only."""

import os
from contextlib import ExitStack

import duckdb
import fsspec
import pandas as pd
import polars as pl
import vortex as vx

ENGINES = (
    "polars_parquet",
    "sql_parquet",
    "sql_duckdb",
    "sql_vortex",
    "polars_vortex",
    "pandas_parquet",
)
TASKS = ("trial", "cohort_force", "all_pressure", "mesh")
CELLS = ["frame", "y", "x", "value"]
KEYS = ["subject", "condition", "pressure_trial"]
TARGET = ("s053", "ws", 4)


def sql_literal(value):
    return "'" + str(value).replace("'", "''") + "'"


def cohort_sql(src):
    return f"""SELECT s.subject,count(*) AS samples,max(g.force_right) AS peak,
                count(DISTINCT t.trial_id) AS trials FROM {src("subjects")} s
                JOIN {src("trials")} t ON t.subject=s.subject
                JOIN {src("grf")} g ON (g.subject,g.condition,g.pressure_trial)=(t.subject,t.condition,t.trial)
                WHERE s.Age>=60 AND t.condition IN ('wc','ws') GROUP BY s.subject"""


class Reader:
    def __init__(self, engine, base, sizes=None):
        self.engine = engine
        self.base = str(base).rstrip("/")
        self.sizes = sizes or {}
        self.remote = self.base.startswith(("http://", "https://"))
        self.stack = ExitStack()
        self.con = None
        if engine.startswith("sql_"):
            self.con = duckdb.connect(config={"threads": 4})
            self.stack.callback(self.con.close)
            if self.remote:
                self.con.execute("LOAD httpfs")
                if self.base.startswith("https://127.0.0.1:") and os.environ.get(
                    "PPDS_LOOPBACK_CA"
                ):
                    self.con.execute(
                        "SET GLOBAL ca_cert_file = ?", [os.environ["PPDS_LOOPBACK_CA"]]
                    )
            if engine.endswith("vortex"):
                self.con.execute("LOAD vortex")
            if engine == "sql_duckdb":
                self.con.execute(
                    f"ATTACH {sql_literal(self.base + '/ppds.duckdb')} AS pub (READ_ONLY)"
                )
        if engine == "pandas_range":
            self.fs = fsspec.filesystem(
                "http", skip_instance_cache=True, block_size=65536, cache_type="none"
            )

    def close(self):
        self.stack.close()

    def file(self, table):
        fmt = "vortex" if self.engine.endswith("vortex") else "parquet"
        folder = "vortex_compact" if "_compact_" in self.engine else fmt
        return f"{self.base}/{folder}/{table}.{fmt}"

    def source(self, table):
        if self.engine == "sql_duckdb":
            return f'pub."{table}"'
        fmt = "vortex" if self.engine.endswith("vortex") else "parquet"
        return f"read_{fmt}({sql_literal(self.file(table))})"

    def lazy(self, table):
        if self.engine.endswith("vortex"):
            return vx.open(self.file(table)).to_polars()
        return pl.scan_parquet(self.file(table))

    def pandas(self, name, columns, filters=None):
        url = self.file(name)
        if self.engine == "pandas_range":
            with self.fs.open(url, "rb", size=self.sizes[name]["bytes"]) as stream:
                return pd.read_parquet(stream, columns=columns, filters=filters)
        options = (
            {"dtype_backend": "pyarrow"} if self.engine == "pandas_arrow_dtypes" else {}
        )
        return pd.read_parquet(url, columns=columns, filters=filters, **options)

    def read(self, task):
        if self.con is not None:
            return self.sql(task)
        if self.engine.startswith("polars"):
            return self.polars(task)
        return self.pd(task)

    def sql(self, task):
        src = self.source
        if task == "trial":
            tid = self.con.execute(
                f"SELECT trial_id FROM {src('trials')} WHERE subject=? AND condition=? AND trial=?",
                TARGET,
            ).fetchall()[0][0]
            query = f"SELECT frame,y,x,value FROM {src('pressure')} WHERE trial_id={int(tid)}"
        elif task == "mesh":
            query = f"SELECT stl FROM {src('scans')} WHERE subject='s053' AND side='r'"
        elif task == "all_pressure":
            query = f"SELECT trial_id,max(value) AS peak,count(*) AS cells FROM {src('pressure')} GROUP BY trial_id"
        elif task == "cohort_force":
            query = cohort_sql(src)
        else:
            raise ValueError(task)
        return self.con.sql(query).to_arrow_table()

    def polars(self, task):
        col = pl.col
        if task == "trial":
            sub, cond, num = TARGET
            tid = (
                self.lazy("trials")
                .filter(
                    (col("subject") == sub)
                    & (col("condition") == cond)
                    & (col("trial") == num)
                )
                .select("trial_id")
                .collect()
                .item()
            )
            data = self.lazy("pressure").filter(col("trial_id") == tid).select(CELLS)
        elif task == "mesh":
            data = (
                self.lazy("scans")
                .filter((col("subject") == "s053") & (col("side") == "r"))
                .select("stl")
            )
        elif task == "all_pressure":
            data = (
                self.lazy("pressure")
                .group_by("trial_id")
                .agg(col("value").max().alias("peak"), pl.len().alias("cells"))
            )
        elif task == "cohort_force":
            people = self.lazy("subjects").filter(col("Age") >= 60).select("subject")
            trials = (
                self.lazy("trials")
                .filter(col("condition").is_in(["wc", "ws"]))
                .select("subject", "condition", "trial", "trial_id")
            )
            trials = trials.rename({"trial": "pressure_trial"})
            forces = (
                self.lazy("grf")
                .filter(col("condition").is_in(["wc", "ws"]))
                .select(*KEYS, "force_right")
            )
            data = (
                people.join(trials, on="subject")
                .join(forces, on=KEYS)
                .group_by("subject")
                .agg(
                    pl.len().alias("samples"),
                    col("force_right").max().alias("peak"),
                    col("trial_id").n_unique().alias("trials"),
                )
            )
        else:
            raise ValueError(task)
        return data.collect()

    def pd(self, task):
        if task == "trial":
            sub, cond, num = TARGET
            tid = self.pandas(
                "trials",
                ["trial_id"],
                [
                    ("subject", "==", sub),
                    ("condition", "==", cond),
                    ("trial", "==", num),
                ],
            ).iloc[0, 0]
            return self.pandas("pressure", CELLS, [("trial_id", "==", int(tid))])
        if task == "mesh":
            return self.pandas(
                "scans", ["stl"], [("subject", "==", "s053"), ("side", "==", "r")]
            )
        if task == "all_pressure":
            data = self.pandas("pressure", ["trial_id", "value"])
            return data.groupby("trial_id", sort=False, as_index=False).agg(
                peak=("value", "max"), cells=("value", "size")
            )
        if task == "cohort_force":
            people = self.pandas("subjects", ["subject"], [("Age", ">=", 60)])
            filters = [
                ("condition", "in", ["wc", "ws"]),
                ("subject", "in", people.subject.tolist()),
            ]
            trials = self.pandas(
                "trials", ["subject", "condition", "trial", "trial_id"], filters
            ).rename(columns={"trial": "pressure_trial"})
            grf = self.pandas("grf", [*KEYS, "force_right"], filters)
            joined = people.merge(trials, on="subject").merge(grf, on=KEYS)
            return joined.groupby("subject", as_index=False, sort=False).agg(
                samples=("force_right", "size"),
                peak=("force_right", "max"),
                trials=("trial_id", "nunique"),
            )
        raise ValueError(task)
