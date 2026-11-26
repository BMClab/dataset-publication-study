# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "duckdb==2.0.1",
#     "marimo==0.26.0",
#     "polars==2.1.0",
#     "sqlglot==30.35.0",
# ]
# ///

import marimo

__generated_with = "0.26.0"
app = marimo.App(width="medium")


@app.cell
def _():
    from pathlib import Path
    from tempfile import TemporaryDirectory
    from time import perf_counter

    import duckdb
    import marimo as mo
    import polars as pl

    return Path, TemporaryDirectory, duckdb, mo, perf_counter, pl


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Check readers locally and on a host

    This notebook runs two small tests. The first gives three readers the same SQL over generated
    Parquet files and checks each answer against a hand-calculated reference. The second opens a
    Parquet file directly from its host, or from a local path, with DuckDB and Polars and reports
    whether each reader succeeded.

    Agreement on local files does not show that a reader works with a hosted copy. Readers request
    byte ranges differently, and hosts answer some requests differently.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 1. Same SQL, same local files

    Participants aged 60 or older are joined to their slow and comfortable walking trials and to the
    force samples of those trials. The expected answer is participant A with two trials, three samples
    and a 220 N peak, and participant B with one trial, two samples and a 190 N peak.
    """)
    return


@app.cell
def _(Path, TemporaryDirectory, pl):
    workdir = TemporaryDirectory()
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
    files = {}
    for _name, _columns in tables.items():
        files[_name] = Path(workdir.name) / f"{_name}.parquet"
        pl.DataFrame(_columns).write_parquet(files[_name])
    return files, tables, workdir


@app.cell
def _(mo, pl, tables):
    mo.hstack(
        [mo.vstack([mo.md(f"**{_name}**"), pl.DataFrame(_columns)]) for _name, _columns in tables.items()],
        justify="start",
        gap=2,
    )
    return


@app.cell
def _():
    # Table names are placeholders so each reader can supply its own source.
    COHORT_SQL = """
    SELECT p.participant, COUNT(DISTINCT t.trial_id) AS trials,
           COUNT(*) AS samples, MAX(f.force_n) AS peak_force_n
    FROM {participants} p
    JOIN {trials} t ON t.participant = p.participant
    JOIN {forces} f ON f.trial_id = t.trial_id
    WHERE p.age_years >= 60 AND t.condition IN ('slow', 'comfortable')
    GROUP BY p.participant
    ORDER BY p.participant
    """
    EXPECTED = [("A", 2, 3, 220), ("B", 1, 2, 190)]
    return COHORT_SQL, EXPECTED


@app.cell
def _(COHORT_SQL, EXPECTED, duckdb, files, mo, perf_counter, pl):
    names = {_name: _name for _name in files}

    def _duckdb_rows():
        with duckdb.connect() as con:
            for name, path in files.items():
                con.read_parquet(str(path)).create_view(name)
            return con.sql(COHORT_SQL.format(**names)).fetchall()

    def _polars_rows():
        frames = {name: pl.scan_parquet(path) for name, path in files.items()}
        with pl.SQLContext(frames) as context:
            return context.execute(COHORT_SQL.format(**names)).collect().rows()

    def _marimo_sql_rows():
        # The same SQL as a marimo SQL cell would run it, reading the files directly.
        sources = {name: f"read_parquet('{path}')" for name, path in files.items()}
        result = mo.sql(COHORT_SQL.format(**sources), output=False)
        return result.rows() if hasattr(result, "rows") else result.fetchall()

    local_results = []
    for _label, _query in [
        ("DuckDB", _duckdb_rows),
        ("Polars SQL", _polars_rows),
        ("marimo SQL cell (DuckDB)", _marimo_sql_rows),
    ]:
        _start = perf_counter()
        _rows = [tuple(_row) for _row in _query()]
        local_results.append({
            "reader": _label,
            "result": "pass" if _rows == EXPECTED else "mismatch",
            "rows": str(_rows),
            "ms": round((perf_counter() - _start) * 1000, 1),
        })
    mo.ui.table(local_results, selection=None)
    return (local_results,)


@app.cell
def _(local_results):
    # Stop with an error when any reader disagrees with the reference, so a scripted run fails.
    _failed = [_r["reader"] for _r in local_results if _r["result"] != "pass"]
    if _failed:
        raise ValueError(f"Readers disagreed with the reference: {', '.join(_failed)}")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 2. Open a file directly from its host

    Enter the URL of a Parquet file on your host, or a local path, and press the button. Each reader
    counts the rows without downloading the file first. For URLs, DuckDB also reports its HTTP
    requests and the declared size of the response bodies it received, compared with the file size.

    The default is the 54 KB participant and trial table of a public dataset on Zenodo. On
    26 November 2026 (UTC), DuckDB 2.0.1 read it directly and Polars 2.1.0 failed with an invalid
    range response. For a file this small a reader may fetch most of its bytes. To see a selective
    read, try the same dataset's 125 MB pressure table, which both readers counted from its metadata:

    `https://zenodo.org/api/records/24432612/files/pressure.parquet/content`

    A failure here is an observation about that reader and host, not an error in the notebook.
    """)
    return


@app.cell
def _(mo):
    DEFAULT_SOURCE = "https://zenodo.org/api/records/24432612/files/trials.parquet/content"
    source_form = mo.ui.text(
        value=DEFAULT_SOURCE, label="Parquet file URL or local path", full_width=True
    ).form(submit_button_label="Test this file")
    source_form
    return DEFAULT_SOURCE, source_form


@app.cell
def _(DEFAULT_SOURCE, duckdb, mo, perf_counter, pl, source_form):
    source = (source_form.value or DEFAULT_SOURCE).strip()
    remote = source.startswith(("http://", "https://"))

    def _duckdb_check():
        con = duckdb.connect()
        if remote:
            con.sql("CALL enable_logging('HTTP')")
        start = perf_counter()
        try:
            rows = con.read_parquet(source).aggregate("count(*)").fetchall()[0][0]
        except Exception as exc:
            return {"reader": "DuckDB", "result": "fail", "rows": None,
                    "seconds": round(perf_counter() - start, 2), "detail": f"{type(exc).__name__}: {exc}"}
        seconds = round(perf_counter() - start, 2)
        detail = "local file"
        if remote:
            log = con.sql(
                "SELECT request.type, TRY_CAST(response.headers['content-length'] AS BIGINT) "
                "FROM duckdb_logs_parsed('HTTP')").fetchall()
            gets = [length for method, length in log if method == "GET"]
            heads = [length for method, length in log if method == "HEAD" and length is not None]
            known = sum(length for length in gets if length is not None)
            partial = " (partial: some lengths unknown)" if None in gets else ""
            size = f" of a {max(heads):,}-byte file" if heads else ""
            detail = f"{len(log)} requests, {known:,} declared GET bytes{partial}{size}"
        return {"reader": "DuckDB", "result": "pass", "rows": rows, "seconds": seconds, "detail": detail}

    def _polars_check():
        start = perf_counter()
        try:
            rows = pl.scan_parquet(source).select(pl.len()).collect().item()
        except Exception as exc:
            return {"reader": "Polars", "result": "fail", "rows": None,
                    "seconds": round(perf_counter() - start, 2), "detail": f"{type(exc).__name__}: {exc}"}
        return {"reader": "Polars", "result": "pass", "rows": rows,
                "seconds": round(perf_counter() - start, 2),
                "detail": "transfer not instrumented" if remote else "local file"}

    host_results = [_duckdb_check(), _polars_check()]
    mo.vstack([mo.md(f"Tested `{source}`"), mo.ui.table(host_results, selection=None)])
    return host_results, remote, source


if __name__ == "__main__":
    app.run()
