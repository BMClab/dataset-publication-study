# Choosing how to publish a research dataset

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.24546052.svg)](https://doi.org/10.5281/zenodo.24546052)

This repository helps a lab decide how to publish a research dataset: which file format to release, which reader to recommend, and whether to maintain a toolkit for users. It focuses on releases that must work both directly from a public repository and from a local download. It provides a step-by-step guide, a test for deciding on a toolkit, and a worksheet for recording the evidence behind each choice.

- **Choose for your project.** Use the [format and reader guide](guide/choosing-formats-and-readers.md), decide [whether to provide a toolkit](guide/toolkit-decision.md), and record your evidence in the [decision worksheet](guide/worksheet.md).
- **See a worked case.** BMClab used its plantar pressure dataset (PPDS) to investigate how researchers could retrieve one trial, join a cohort to its measurements, or work offline from the same release. The lab selected Parquet for tabular storage, DuckDB for querying, and a Python toolkit. Follow the [case study](case-studies/ppds/decision.md) from its initial requirements through the measured alternatives. The [evidence index](evidence/README.md) identifies the inputs, environments and limits of each experiment.

## Try the comparison

From the repository root, run the example with uv and Python 3.12–3.14. The recorded check used CPython 3.14.9 on Linux. Package installation requires access to the dependencies on first use.

```sh
uv run --locked python examples/cohort_join.py
```

The example creates three tiny Parquet tables in a temporary directory. DuckDB and Polars run the same SQL over them. Both return participant A with two qualifying trials, three force samples and a 220 N peak, and B with one trial, two samples and a 190 N peak. Each answer is checked against those values. The printed times describe this invocation on generated data. Agreement on local files does not show that both readers work with a hosted copy. [Check the final public release](guide/choosing-formats-and-readers.md#check-the-final-public-release) separately. [Example source](examples/cohort_join.py)

### Run the checks in a notebook, locally or in the cloud

[`examples/reader_checks.py`](examples/reader_checks.py) is a [marimo](https://marimo.io) notebook for anyone who wants to try simple tests without setting up the study. Part 1 repeats the comparison above and adds a marimo SQL cell, and all three readers must match the reference. Part 2 opens a Parquet file directly from its host, or from a local path, with DuckDB and Polars. It reports whether each reader succeeded, and for URLs the requests and declared bytes DuckDB used. Paste the URL of a file on your own host to test it. A reader failure in part 2 is recorded as an observation.

[![Open in molab](https://marimo.io/molab-shield.svg)](https://molab.marimo.io/notebooks/nb_jrdWVXnqpnoecRnKvQff3W/app) runs the notebook as an app in marimo's hosted service, with nothing to install. To read the code, or to copy the notebook and change it, open the [notebook page on molab](https://molab.marimo.io/notebooks/nb_jrdWVXnqpnoecRnKvQff3W).

To run it locally from the repository root:

```sh
uv run --locked --group notebook marimo edit examples/reader_checks.py   # interactive
uv run --locked --group notebook python examples/reader_checks.py        # as a script; fails if part 1 disagrees
```

The notebook also declares its dependencies inline, so `uvx marimo edit --sandbox reader_checks.py` works on a copy outside this repository.

To regenerate the local timing and loopback transfer tables from the November 2026 PPDS study, run the original report generator with Python's standard library. The archive includes the observations and their reference digests.

```sh
python3 evidence/methods/lab_format_tables.py evidence/observations
```

The first table reports first and repeated queries in milliseconds and peak memory in MiB. The second reports decimal MB of response bodies and request counts for first queries over loopback HTTPS. [Published tables and methods](evidence/reports/lab_format_benchmark.md)

## Credit

Cite this investigation using the [study citation](CITATION.cff) or its DOI, [10.5281/zenodo.24546052](https://doi.org/10.5281/zenodo.24546052), which resolves to the latest version. Version 0.1.0 has its own DOI, [10.5281/zenodo.24546053](https://doi.org/10.5281/zenodo.24546053). Cite the PPDS dataset for its measurements and the PPDS software for its toolkit or notebooks. The selected case uses dataset v1.0.0 and toolkit v0.1.1. The study's software and documentation carry BMClab's MIT license. [Dataset v1.0.0](https://doi.org/10.5281/zenodo.24432612) · [Software citation](https://doi.org/10.5281/zenodo.24490656) · [License](LICENSE)
