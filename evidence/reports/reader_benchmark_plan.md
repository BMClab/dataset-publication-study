# Extended PPDS reader comparison

*Historical research record, November 2026. See the [evidence index](../README.md) for inputs, versions and available observations.*

Authorized on 2026-11-13 as an exploratory benchmark, extending the existing storage experiment.
The user requested Lance/LanceDB, Polars and Pandas, plus performance, reliability and hosting
availability useful for PPDS and future projects. This is not a production reader implementation
or publication migration.

## Required capabilities clarified by the user

- Installable and usable in a Python environment.
- Compatible with the existing **marimo notebooks** for interactive retrieval, analysis and
  visualization; this existing project constraint was confirmed explicitly during the follow-up.
- Suitable for multimodal **whole datasets of approximately 10 MB to 1 GB**. The range does not
  describe the size of an individual scan or other binary object.
- Publishable as files in Zenodo and readable back from those published files.
- Partial selections, including one subject or a subset of subjects, trial numbers and conditions.
  This assessment uses direct selective remote reads as the hosting target, and distinguishes that
  capability from downloading a complete archive and filtering it locally.

These are pass/fail requirements before performance rankings. A supported object-store simulation
is useful for future-project context, but is not evidence of direct Zenodo compatibility. Existing
public Zenodo fixtures can be queried read-only to validate reader/host integration without
publishing PPDS prematurely. Do not claim a controlled 10 MB–1 GB size sweep from one dataset:
the full PPDS publication-size candidates lie in that range, while trial-length variants address
selection-size differences.

## Comparison

- Keep the existing sparse pressure representation for a controlled storage comparison.
- Compare Pandas/PyArrow and lazy Polars on the existing consolidated Parquet layouts.
- Compare Lance storage via Lance/LanceDB Embedded, with scalar indexes where appropriate and
  a dedicated scan-blob representation; report storage/index bytes and physical file counts.
- Repeat selected Arrow/DuckDB controls in the same environment and run series.
- Investigate DuckDB's Lance extension as a separate query path if an installed, compatible
  release is available. Record availability failures rather than silently replacing it with
  eager materialization.
- Retain the original HDF5/Zarr results as dated context; they use a different dense representation.

## Workloads and evidence

Use the same pressure frame/trial/whole-subject, standing feet, maximum-by-trial, subject/gait
cohort join, footprints, force trace and original STL-byte selection as the first experiment.
Add an eight-trial selection spanning two subjects, two conditions and two trial numbers, with
filters applied in the reader and exact dense outputs compared with the reference.
Include additional pressure subjects/trial lengths if practical. Compare exact output signatures,
full sparse-record hashes and scan bytes, original metadata types, nulls and export metadata.
Record first and reused-reader latency, RSS, module setup, source/product versions, selected
columns, materialization strategy and thread settings. Use fresh processes, sequential timed
runs, several selective repetitions and explicitly distinguish warm OS cache from cold storage.

Measure localhost HTTP bytes, requests and per-request latency separately from real hosting.
Test generic HTTP feasibility for Lance's multi-file discovery, not just local reads. Assess
Zenodo range behavior, file limits/path requirements, version/snapshot handling and whether a
standard library can use the published layout without downloading or running a service.
Do not upload data. Public hosting checks are read-only.

Report observed correctness and failure handling separately from documentation-based support and
unmeasured long-term reliability. Exercise missing/corrupt input on temporary fixtures and preserve
actual errors. Reproducible exports, checksums, pinned versions, platform requirements and managed
versus embedded features belong in the assessment. Performance claims are workload-specific;
Pandas/Polars are readers/analysis tools and do not define competing native publication formats.

All products remain outside `data/`, with production dependencies unchanged. Save code, pinned
benchmark requirements, raw measurements, diagnostic evidence and a readable comparative report.

## Expanded direct Zenodo checks

The user subsequently requested real hosted access tests across the candidates, including native
DuckDB, HDF5, Zarr ZIP, Lance/LanceDB, a SQLite HTTP-VFS baseline and all Parquet reader configurations. Use existing public
records with bounded read-only requests, checksum-verified local references where practical, and
explicit distinctions between selected output, reduced transfer and protocol/provider failures.
Include Polars SQL alongside native expressions and a headless marimo integration smoke. Record
adapter and native-provider configuration alternatives; do not treat unrelated fixture sizes,
chunk layouts or WAN timings as a controlled performance ranking. Results are in
[zenodo_access_tests.md](zenodo_access_tests.md).
