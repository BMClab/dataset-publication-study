# Choosing how to publish a research dataset

BMClab used its plantar pressure dataset (PPDS) to investigate how researchers could retrieve one trial, join a cohort to its measurements, or work offline from the same release. The lab selected Parquet for tabular storage, DuckDB for querying, and a Python toolkit for operations such as reconstructing a pressure recording in physical units. This repository documents the evidence and gives the next project a way to make its own choices.

- **Choose for your project.** Use the [format and reader guide](guide/choosing-formats-and-readers.md), decide [whether to provide a toolkit](guide/toolkit-decision.md), and record your evidence in the [decision worksheet](guide/worksheet.md).
- **See how PPDS decided.** Follow the [case study](case-studies/ppds/decision.md) from its initial requirements through the measured alternatives to the published files and Python interface. The [evidence index](evidence/README.md) identifies the inputs, environments and limits of each experiment.

## Try the comparison

From the repository root, run the example with uv and Python 3.12–3.14. The recorded check used CPython 3.14.9 on Linux. Package installation requires access to the dependencies on first use.

```sh
uv run --locked python examples/cohort_join.py
```

The example creates three tiny Parquet tables in a temporary directory. DuckDB and Polars run the same SQL over them. Both return participant A with two qualifying trials, three force samples and a 220 N peak, and B with one trial, two samples and a 190 N peak. Each answer is checked against those values. The printed times describe this invocation on generated data. [Example source](examples/cohort_join.py)

To regenerate the local timing and loopback transfer tables from the November 2026 PPDS study, run the original report generator with Python's standard library. The archive includes the observations and their reference digests.

```sh
python3 evidence/methods/lab_format_tables.py evidence/observations
```

The first table reports first and repeated queries in milliseconds and peak memory in MiB. The second reports decimal MB of response bodies and request counts for first queries over loopback HTTPS. [Published tables and methods](evidence/reports/lab_format_benchmark.md)

## Credit

Cite this investigation using the [study citation](CITATION.cff). Cite the PPDS dataset for its measurements and the PPDS software for its toolkit or notebooks. The selected case uses dataset v1.0.0 and toolkit v0.1.1. The study's software and documentation carry BMClab's MIT license. [Dataset v1.0.0](https://doi.org/10.5281/zenodo.24432612) · [Software citation](https://doi.org/10.5281/zenodo.24490656) · [License](LICENSE)
