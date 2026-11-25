# Polars and DuckDB for public research datasets

*Historical research record, November 2026. See the [evidence index](../../evidence/README.md) for inputs, versions and available observations.*

**DuckDB is the selected reader and query toolkit.** On 22 November 2026 the final comparison considered DuckDB and Polars for the lab’s public datasets. Use DuckDB SQL for published query examples and marimo SQL cells. A collaborator can reuse a query from a paper in Python, R, a command line or a database client. This reach is the deciding criterion because users outside the lab choose their own analysis environment. Polars has an advantage when authoring Python notebooks that clean and transform measurements. An analyst can join tables in SQL, then use Python expressions on the resulting lazy frame. A DuckDB user can also return a query result as a Polars DataFrame with `.pl()`. Researchers who prefer Polars can open the public Parquet files directly. [DuckDB clients](https://duckdb.org/docs/lts/clients/overview) · [Polars SQL guide](https://docs.pola.rs/user-guide/sql/intro/)

## What the choice changes

| Question | Polars | DuckDB |
|---|---|---|
| How would a Python user work? | Chain operations such as `filter`, `with_columns`, `group_by` and `agg`. Expressions can select many columns by name or type and apply a transformation to all of them. The workflow feels familiar to pandas users. Polars has its own syntax and works without a pandas-style row index. | Write SQL or build a lazy relation with methods such as `filter`, `project`, `aggregate` and `order`. Many methods accept compact SQL fragments. There is also a Python expression API for building conditions programmatically. |
| How far does SQL go? | SQL translates to Polars expressions. A `SQLContext` can join named lazy frames. Its result can be extended in Python before `collect()`. Its SQL dialect covers a subset of database SQL. New query features typically reach the expression API first. | SQL is the main interface. A persistent database can store tables, views and macros for reuse across sessions. A query can also read Parquet directly in an in-memory connection. |
| How does this work in marimo? | Use Python cells for both native expressions and Polars SQL. | Built-in SQL cells use DuckDB by default. They can query a Python DataFrame and return a Polars DataFrame. Choosing a Polars output type in a default SQL cell still executes the SQL in DuckDB. |
| Who can reuse examples? | A Python example carries over naturally to other Python notebooks. Polars also has Rust and R interfaces, with their own syntax. | The same DuckDB SQL can be used through Python, R, the CLI, Java/JDBC, ODBC and DuckDB-Wasm. File access and extension availability depend on the client, particularly in browsers. |
| What determines remote performance? | A lazy Parquet scan can read selected columns and skip row groups using statistics. With a range-capable reader and host this can reduce bytes transferred. | Parquet column selection, row-group pruning and HTTP ranges also enable partial reads. For both engines, file layout, selectivity, caching and hosting influence bytes transferred. |

[Polars for pandas users](https://docs.pola.rs/user-guide/migration/pandas/) · [Polars expression expansion](https://docs.pola.rs/user-guide/expressions/expression-expansion/) · [Polars interfaces](https://github.com/pola-rs/polars) · [DuckDB relational API](https://duckdb.org/docs/api/python/relational_api) · [DuckDB expression API](https://duckdb.org/docs/current/clients/python/expression) · [marimo SQL cells](https://docs.marimo.io/guides/working_with_data/sql/) · [Polars Parquet scans](https://docs.pola.rs/user-guide/io/parquet/) · [DuckDB HTTP reads](https://duckdb.org/docs/stable/core_extensions/httpfs/https)

## One question in both styles

Suppose a file called `measurements.parquet` has the columns `site`, `reading` and a Boolean `valid`. We want the mean valid reading per site. Both engines accept this SQL.

```python
sql = """
    SELECT site, AVG(reading) AS mean_reading
    FROM measurements
    WHERE valid
    GROUP BY site
    ORDER BY site
"""
```

In Polars, the two paths below each return a lazy frame. An analyst can add another transformation to either one before collecting the answer.

```python
import polars as pl

measurements = pl.scan_parquet("measurements.parquet")
from_sql = pl.SQLContext(measurements=measurements).execute(sql)
from_expressions = (
    measurements.filter(pl.col("valid"))
    .group_by("site")
    .agg(pl.col("reading").mean().alias("mean_reading"))
    .sort("site")
)
above_threshold = from_sql.filter(pl.col("mean_reading") > 25).collect()
```

In DuckDB, the same choice is available through SQL or a relation. The connection below reads the same file. The view gives it the name used by the shared SQL.

```python
import duckdb

with duckdb.connect() as con:
    readings = con.from_parquet("measurements.parquet")
    readings.create_view("measurements")
    from_sql = con.sql(sql)
    from_methods = (
        readings.filter("valid")
        .aggregate("site, avg(reading) AS mean_reading", "site")
        .order("site")
    )
    above_threshold = from_sql.filter("mean_reading > 25").pl()
```

With Polars 2.1.0 and DuckDB 2.0.1, the four forms returned the same ordered means for a four-reading fixture. The two mixed-style examples also returned the same Polars DataFrame after applying the threshold. The shared SQL returned the same ordered values unchanged in Node.js 22.22.0 with `@duckdb/node-api` 2.0.1-r.1. One practical SQL difference on these versions is that DuckDB accepted `CREATE VIEW valid_rows AS SELECT * FROM measurements WHERE valid`. Polars SQLContext rejected that statement. In Polars, the filtered lazy frame can instead be given a name with `SQLContext.register`. [Polars SQLContext](https://docs.pola.rs/api/python/stable/reference/sql/python_api.html) · [DuckDB views](https://duckdb.org/docs/sql/statements/create_view)

## Performance beyond this lab

Plotly compared Polars 2.1.0 and DuckDB 2.0.0 on public NOAA weather observations in local Parquet, partitioned by year and sorted by station. At **119 million rows**, the engine that finished first depended on what the reader asked. Timings are the best of three runs in the same process on a four-vCPU VM with 16 GB RAM and a 12 GB process limit. The timings cover local Parquet using Polars expressions and DuckDB SQL. Remote transfer and a within-engine comparison of the two query styles were outside the experiment. [Plotly benchmark and query definitions](https://plotly.com/blog/duckdb-vs-polars-vs-pandas/)

| Query on the same 119 million readings | Polars | DuckDB |
|---|---:|---:|
| Retrieve one station’s history | 0.02 s | 0.07 s |
| Summarize readings per station | 2.17 s | 1.19 s |
| Join station metadata and summarize by country and year | 4.71 s | 2.86 s |

## Audience and adoption

On 22 November 2026, the PyPI Stats API reported **81.8 million** downloads for the `duckdb` Python package and **68.3 million** for `polars` in its last-month window. Each includes repeated installations and dependencies and omits other distribution channels. Neither figure counts distinct users. For a public research project, DuckDB’s more consequential advantage is that a collaborator using R or a JDBC/ODBC client can reuse the lab’s published SQL directly. An R user who prefers the tidyverse can also write a dplyr pipeline and have dbplyr translate it to DuckDB SQL. [DuckDB package counts](https://pypistats.org/api/packages/duckdb/recent) · [Polars package counts](https://pypistats.org/api/packages/polars/recent) · [PyPI Stats methodology](https://pypistats.org/faqs) · [DuckDB clients](https://duckdb.org/docs/lts/clients/overview) · [DuckDB with dbplyr](https://duckdb.org/docs/2.0/clients/r/dbplyr)

## Independent opinions on the final toolkit choice

On 22 November 2026, Claude Code (Opus 5.5) and Antigravity CLI (Gemini 4 Neon High) separately received the same brief. It fixed Parquet as the format, specified Python and marimo as requirements, included the arguments for both query styles, and summarized local, Zenodo and NOAA results. Both were asked to choose one toolkit and identify evidence that would change their choice. Each received the brief without the lab’s selection or the other reviewer’s answer. The reviews interpret the existing measurements. [Local experiment](../../evidence/reports/lab_formats_zenodo_ppds_local.md) · [Zenodo experiment](../../evidence/reports/lab_formats_zenodo_ppds.md)

| Reviewer | Choice | Deciding consideration | What would favor switching to Polars |
|---|---|---|---|
| Claude | **DuckDB** | Outside researchers can reuse SQL across languages and in marimo. DuckDB also completed the direct join on the restricted Zenodo draft. | Reliable direct Polars reads on the lab’s hosted datasets, plus audience evidence that roughly 80% or more of users work in Python and that transformation-heavy workflows predominate. The percentage is Claude’s suggested threshold. |
| Antigravity | **DuckDB** | Public users choose their own tools. Joining a small participant table to a large measurement table directly on Zenodo matters for this audience. | Reliable direct Polars reads of small hosted Parquet tables across releases, plus an audience dominated by Python or R analysts who prefer DataFrame time-series pipelines. |

Both reviewers saw Polars’ strongest advantage in preparing time series with expressions, selectors and windows. The audience mix is still unknown, and the small-table read issue was observed on one restricted Zenodo endpoint with the tested versions.
