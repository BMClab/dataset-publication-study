# Dataset storage discussion

*Historical research record, November 2026. See the [evidence index](../README.md) for inputs, versions and available observations.*

Subject identifiers in this historical benchmark refer to the pre-renumbering snapshot; current dataset files use sequential release IDs. Benchmark values and source artifacts are preserved.

## Current benchmark for the lab standard

The [curated PPDS benchmark](lab_format_benchmark.md) compares Parquet, native DuckDB and two Vortex encodings. It includes the participant–trial–force join, a quantitative pandas comparison, actual Zenodo queries and an executed marimo notebook. It supersedes the reader shortlist below.

## Earlier proposal after the final gait curation — 2026-11-21

Publish a small set of ordinary, compressed Parquet files. Use the PPDS Python
reader for scientific selections such as one trial as a `(frame, y, x)` array.
Use Polars for DataFrame analysis in marimo and DuckDB for SQL across the same
files. Python callers that need predictable partial transfers can use PyArrow
with a seekable HTTP handle, the file size from the Zenodo record, and a trial
index locating the relevant row groups. This is a proposed release design.
[PyArrow row-group reads](https://arrow.apache.org/docs/python/generated/pyarrow.parquet.ParquetFile.html)
and [marimo SQL](https://docs.marimo.io/guides/working_with_data/sql/).

The one-row, two-column query was repeated against a public 3,330,851-byte
Zenodo Parquet file. PyArrow received 364,240 body bytes across two HTTP 206
responses. DuckDB reported 405,434 bytes in GET responses. Both returned the
same row and matched the checksum-verified reference. The earlier native Polars
tests also returned the correct row, but their socket counts did not demonstrate
a transfer below file size on this fixture. The previous PPDS benchmark favored
Polars for several local workloads. [Public Zenodo fixture](https://zenodo.org/records/19115351),
[reader and transfer results](zenodo_access_tests.md) and [local PPDS timings](reader_benchmark.md).

Native DuckDB is the proven single-file alternative, including selective remote
attachment. HDF5 is a credible pressure-array alternative when rectangular
frame or sensor slices dominate. A complete Lance table query directly from
Zenodo remains unverified. Vortex is an additional candidate for a future speed
comparison. Its Python library documents a generic HTTPS store and its file
format has a compatibility policy. PPDS performance, reader adoption and
end-to-end Zenodo behavior would still need evaluation before choosing it.
[DuckDB HTTP access](https://duckdb.org/docs/2.0/core_extensions/httpfs/https),
[Lance storage providers](https://lance.org/guide/object_store/),
[Vortex storage providers](https://docs.vortex.dev/api/python/store) and [Vortex compatibility](https://vortex.dev/faq).

Choose the gait data to publish (cleaned, native, or both) before fixing the
file count. Test trial-aligned row groups against larger groups sorted by
participant, condition, trial and frame. Include a frame, one trial, several
participants and conditions, a cohort aggregation, one foot mesh and a full
read. Measure transferred bytes, requests and elapsed time, and verify values,
units and scan bytes. The older bundle sizes and timings predate the final
gait selections and the 10 Hz standing time series. The final hosted file layout
still needs this check. Dataset coverage (`README.md`, historical source) and
[historical storage comparison](storage_benchmark.md).

## Minimum requirements behind the search

The search began with an existing Python dataset project and marimo notebooks. For historical
context, its minimum requirements, consolidated from the brief and later clarifications, were:

- Installation and use within a Python environment.
- Compatibility with the **existing marimo notebook framework**, including interactive retrieval,
  analysis and visualization. The user confirmed this explicitly later; marimo was already in use.
- Support for multimodal scientific **whole datasets of about 10 MB–1 GB**, including measurements,
  metadata and original scan payloads.
- Publication as Zenodo files and reading back from their published URLs.
- Partial retrieval by subject, subsets of subjects, trials and conditions, including selective
  remote access without a mandatory complete dataset download.
- Preservation of scientific values and meaning: types, units, coordinates, identifiers and metadata.

Performance, memory, reliability and usability guide comparison among suitable solutions. A small
file count is a preference; a particular format, engine or SQL syntax was not an initial requirement.
The [comparison report](reader_benchmark.md#minimum-requirements-behind-the-search) records these
requirements before presenting methods or results.

## Discussion context

Discussion recorded on 2026-11-13. Consolidated Parquet is now the user's preferred option among
the measured formats. The expanded experiment also measures Lance/LanceDB for storage and
querying; the exact publication layout and reader implementation are not finalized. Parquet and
DuckDB were the outcome of preliminary discussion and testing with Claude.

The participant workbook (`ppds_info.xlsx`, historical source) supplies participant characteristics.

## User priorities

- Preserve complete, exact scientific measurements and their interpretation.
- Put performance and usability ahead of file count or presentation aesthetics.
- Prefer a small number of published data files when this does not compromise those priorities.
- Prefer all primary pressure data in one physical file if practical.
- Provide functional access code and several worked examples, with export functions where useful.
- Preserve the existing marimo notebook workflow when introducing the chosen reader.
- Compare the existing PPDS notebook workloads. Vector similarity search is not a requirement.
- The user requested actual comparisons of Lance/LanceDB, Polars and Pandas, including performance,
  reliability and availability from the data-host perspective, useful for future projects.
- Required: Python installation, Zenodo publication and reading, and partial selections by subject,
  subject subsets, trial numbers and conditions. The target size is **10 MB–1 GB per whole dataset**.
  Direct partial remote access is the delivery target; local performance or S3 support alone does
  not establish that requirement.

## Data and representation

- Dynamic pressure contains the pressure of every frame of walking and running trials, in a
  walkway coordinate system.
- Standing belongs with the primary pressure measurements. The available standing exports are
  peak-pressure images for each foot, using foot-image coordinates, without a time series.
- 3D scans are primary measurements from another modality.
- Registered footprints and Zebris gait and force outputs are derived measurements.
- Subject characteristics and trial indexes are descriptive and structural metadata.

Combining the standing and dynamic records must preserve their measurement type and coordinate
system. A standing peak image must not acquire an invented time sample. One physical database
can alternatively retain separate logical tables for these representations.

## Options discussed

| Option | Motivation | Question to test |
| --- | --- | --- |
| Consolidated Parquet tables, queried by DuckDB | Broad support for typed tables and selective remote reads | Suitable ordering and row-group boundaries for individual frames, trials and cohort queries |
| One native DuckDB database | One file containing independent tables, definitions and potentially scan bytes; direct SQL access | Actual size, selective local and remote reads, and export fidelity |
| HDF5 | Dense multidimensional arrays in one physical container | Whether array access improves pressure visualization and what it costs for whole-dataset analysis and HTTP access |
| Zarr | Compressed, chunked multidimensional arrays | Chunk and packaging choices, remote request overhead and publication file count |
| Lance format and LanceDB Embedded | Scalar tables, selective array/row access and multimodal BLOB handling, with optional DuckDB SQL integration | Actual PPDS pressure/scan access, compression, file count, Zenodo delivery and export fidelity; no embeddings required |
| sqlite-vec | Raised during format and engine exploration | Vector search is not required; ordinary SQLite scalar workloads remain unmeasured |

Parquet files can have numeric, text and nested columns, but combining independent tables in one
file requires a shared or nested schema. The current table separation reflects different row
meanings, rather than an inability to store mixed column types. A DuckDB file can contain those
independent tables directly.

DuckDB is not assumed to be smaller than compressed Parquet. Published engine benchmarks do not
establish PPDS performance. Native DuckDB and Parquet both support selective HTTP reading, subject
to the access implementation and server behavior. A native database would need a declared reader
and storage version, and exports should preserve units, descriptions, provenance and values.

## Measurements needed

Use actual PPDS data and report correctness checks, build time, physical file size and count,
selective frame and trial reads, standing and scan access, cohort analysis, process memory,
and HTTP bytes and requests. Separate the effect of sparse tables versus dense arrays from the
effect of their container or query engine. Report the exact scope, codecs, chunking, versions,
machine, repetitions and caching conditions. Localhost HTTP results measure range-reading behavior;
they do not establish real Zenodo latency.

Keep benchmark products outside `data/` and preserve the current sources and distribution. No
format migration, upload, subject renaming or history rewrite is authorized by this comparison.

## Quantitative follow-up

[Full-data benchmark results](storage_benchmark.md) compare sparse
Parquet and native DuckDB tables with dense HDF5 and Zarr ZIP pressure arrays. The experiment
also tests all measurement tables and original scans in nine Parquet files versus one native
database. Saved per-repetition measurements include first/reused-reader times, memory, HTTP
payloads and request counts. Full-data lossless checks passed; the working distribution is unchanged.

Pressure packages measured 123–133 MB for consolidated Parquet (four files including standing and
the indexes), 150 MB for HDF5, 230 MB for Zarr ZIP and 347 MB for native DuckDB. The complete
measurement-table/scan bundles measured 396 MB for Parquet and 633 MB for native DuckDB.
Selective HTTP reading worked for all tested containers. Native scan BLOB delivery had a substantial
unresolved read-amplification issue in this layout; see the report before judging the one-file option.

The user agreed that consolidated Parquet looks preferable given the measured size and convenience,
and proposed a general reader that initially accesses Parquet but permits a later storage change.
They then specifically asked whether LanceDB could provide both storage and database functionality.
Parquet remains the preferred measured candidate; that preference does not settle the unmeasured
Lance/LanceDB comparison or authorize a production migration. Real Zenodo measurements, more
selective targets, reader-runtime support and a final metadata/export contract remain to be checked.

## Reader direction discussed

Build on the existing public functions in `src/ppds/dataset.py`: subject/trial selection, pressure,
standing, footprints, gait/force data and scans. Most example code already uses this interface.
The implementation currently mixes physical Parquet paths, row-group access and HTTP handling
with scientific array reconstruction; its SQL entry point separately exposes a DuckDB connection.

The proposed change is a small internal storage interface behind those domain functions, preserving
their selectors, returned NumPy arrays/DataFrames, units, coordinate conventions and missing-data
behavior. It would own physical paths, manifests, row-group locators, file/connection lifetimes and
local/remote access. A Parquet implementation comes first; a Lance implementation could later
serve the same logical data without changing visualization code. Do not build a broad plugin
framework or implement hypothetical backends in advance.

DuckDB remains a good candidate for the SQL examples and cohort analysis. Direct indexed PyArrow
access can remain an internal optimization for pressure selections if the actual workload benefits.
The portable domain API should return data rather than require a DuckDB relation/connection;
advanced SQL access remains an explicit engine-specific facility. Sharing logical table names and
schemas helps SQL examples survive a storage change, but does not guarantee that every engine's
SQL, BLOB APIs or export behavior are interchangeable. This is a design direction, not implemented
reader functionality.

## Lance/LanceDB follow-up

Current primary documentation was checked through Context7 and the official sites:

- [LanceDB Embedded tables](https://docs.lancedb.com/oss/v0-41-0/management/table) use Arrow schemas,
  support numeric and binary columns, and document selective blob access without requiring an
  embedding column. Some blob facilities are marked early access; a benchmark must pin working
  released library and storage versions and distinguish Embedded from Enterprise features.
- [Lance Blob API](https://lance.org/guide/blob/) supports selected payload reads and seekable blob
  handles. This makes original STL retrieval a relevant workload to measure. Documentation alone
  does not establish that its transfer volume or latency beats Parquet on PPDS.
- [DuckDB integration](https://docs.lancedb.com/integrations/data/duckdb) documents the Lance
  extension for SQL analytics, including joins, with queries pushed to Lance. Storage and SQL
  engine therefore need not be chosen as an inseparable pair. Extension/platform compatibility
  still needs verification in the intended example runtime.
- [Lance dataset layout](https://lance.org/format/table/layout/) uses manifests and data files,
  with additional blob/index files depending on representation. A native LanceDB dataset should
  not be assumed to be one downloadable file. Zenodo file count, path mapping, version discovery
  and selective HTTP delivery need a concrete feasibility test; no incompatibility is asserted.

The absence of vector search is not a reason to dismiss LanceDB. The existing benchmark did not
test it and cannot rank it against Parquet. A useful follow-up compares Lance/LanceDB on the same
pressure frame/trial/subject, full-corpus, standing, scalar cohort and scan workloads, including
storage size/file count, memory, HTTP payloads/requests and scientific metadata/export fidelity.
Use the same sparse pressure schema first to separate format/engine effects from representation
changes; any frame-oriented or other multimodal layout should be reported as a separate variant.
The original DuckDB BLOB transfer result was reproduced in three first-reader runs at each HTTP
delay setting; it is evidence about that layout, not a prediction of Lance behavior.

The user subsequently authorized the expanded experiments. Their results are in
[reader_benchmark.md](reader_benchmark.md), with the scope in
[reader_benchmark_plan.md](reader_benchmark_plan.md) and a separately sourced
[hosting and reliability assessment](storage_hosting_assessment.md). The experiments preserve
the working distribution and use an isolated Python environment.

The completed comparison supports Parquet under the user's direct-Zenodo requirement: Polars,
Arrow, DuckDB and pandas/fsspec returned the same partial result from a real public Zenodo
Parquet file. Native Lance/LanceDB readers in the tested releases reject HTTP/HTTPS dataset
schemes; their local and supported-object-store paths remain useful alternatives for other
projects. The measurement-table/scan package is about 386–396 MB in nine Parquet files, versus
481 MB in 53 Lance objects using compressed binary scans or 755 MB in 57 objects using Blob v2.
These are complete dataset package sizes, not individual scan sizes.

For the future reader, Polars is a strong general access/analysis candidate, indexed Arrow offers
efficient reused pressure reads, and DuckDB remains useful for SQL. Pandas is suitable for selected
data with an explicit range filesystem; its ordinary URL path downloaded a complete 133 MB file
for one trial in the experiment. The synthetic export probes show why the shared reader needs
an explicit schema/dictionary contract: values were preserved across all tested routes, while
default dtype/nullability and scientific metadata behavior differed. These are recommendations
from the tests, rather than implementation choices already made by the user.

## Polars SQL and native access follow-up

The user pointed out that Polars also exposes SQL, and that using its native pandas-like expression
interface would let users skip SQL entirely. Their intended read-only data-science queries are
limited in scope; a second SQL engine should not be required without a concrete missing capability.

The revised recommendation is Parquet with Polars for both native lazy queries and optional
`SQLContext` queries. Register the same `scan_parquet` LazyFrames under stable logical table names;
both interfaces can be mixed and collected explicitly. Keep scientific convenience methods
returning arrays/metadata, and treat raw LazyFrames/SQL as the advanced Polars interface. DuckDB
remains a comparison/reference and an optional tool for a demonstrated need, rather than a
requirement just because examples use SQL. This is a reader design recommendation, not a completed
production migration.

[Current Polars documentation](https://docs.pola.rs/user-guide/sql/intro/) explains that SQL is
translated into Polars expressions and executed by the same engine. The user subsequently supplied
version-specific release notes that explicitly establish SQL as a first-class interface since 2.0;
the earlier generic-guide wording understated the current SQL support. A functional check using
Polars 2.1.0 matched native
results for an eight-trial multi-subject selection (185,664 sparse rows), maxima for all 3,188 trials
and a cohort join/aggregation (16 groups). [Saved queries and plans](../observations/polars_sql_check.json)
record the checks. Plans are not identical: SQL can introduce casts and different sort policies;
SQL `COUNT` is Int64 while native `pl.len` is UInt32 in this fixture. Values match, with cohort
means compared after rounding to 12 decimals. This was not a new timing/HTTP benchmark, so the
earlier Polars timings remain measurements of the native expression path.

The user also supplied [this external benchmark](https://medium.com/@reliabledataengineering/polars-vs-sql-the-fair-comparison-everyone-demanded-with-actual-benchmarks-ae65bc778182).
Its comparison is Polars 0.20.3 on EC2 versus Snowflake on a different compute configuration,
rather than Polars SQL versus native expressions. The linked code repository resolves to a
placeholder `yourusername` URL and returned 404 when checked. It is contextual reading rather
than reproducible evidence for choosing the PPDS interface. The
[Polars PDS-H benchmark](https://pola.rs/posts/benchmarks/) is a primary-source engine comparison
with linked code; its larger-scale workloads also differ from direct Zenodo PPDS access.

### Polars 2.0 and 2.1 release-specific evidence

The user supplied the official [2.0 release post](https://pola.rs/posts/release-polars-2/) and
[2.1 changelog](https://pola.rs/posts/polars-2-1-changelog/). These are more directly relevant to
the tested version than old API comparisons. Polars 2.0 establishes SQL as first class, improves
its optimizer and makes streaming the default for lazy collection. Its derived TPC-H/TPC-DS
comparison explicitly executes Polars SQL, with a working
[reproduction repository](https://github.com/pola-rs/polars-2.0-benchmark). The published summary
uses the best of five hot runs and includes DuckDB 1.5.6 and a 2.0 development build; PPDS used
medians, stable DuckDB 2.0.0, different workloads and explicit HTTP-transfer measurements.
The studies are complementary, rather than interchangeable performance figures.

Polars 2.1 adds recursive CTEs, more correlated subqueries, ASOF SQL joins and additional functions.
Its Parquet changes include encrypted-file support, SQL LIKE/string prefiltering, top-k row-group
pruning and corrected unsigned statistics. Out-of-core group-by support also expands. Some features
are marked unstable in the release post. Not every addition is needed by PPDS or exercised by our
tests; unsigned types, filtered scans and group reductions are directly relevant to its pressure data.

Both our main benchmark and the later SQL correctness checks already used **Polars 2.1.0**, so no
version upgrade or retrospective adjustment to measured times is needed. The recommended default
is now stated explicitly as **Parquet + Polars, with native expressions and SQL both supported**.
Retain DuckDB only for a demonstrated additional requirement. The PPDS SQL-interface timing and
network paths were not separately benchmarked; native expression timings should retain that label.

## Direct Zenodo querying clarification

The user emphasized that poor support for querying the published files directly significantly
reduces a solution's appeal; merely storing those files on Zenodo is insufficient. This reinforces
the preference for Parquet and its demonstrated Python-reader access to a public Zenodo file.

This does not give native DuckDB and Lance the same verdict. The tested Lance/LanceDB readers
reject generic HTTPS dataset URIs. DuckDB supports read-only remote `ATTACH` of its native database
format over HTTPS with partial reads. At this point that path had not yet been validated on Zenodo;
the follow-up below subsequently confirmed it.
Its measured PPDS package size and scan-transfer amplification remain disadvantages of the
tested layout. DuckDB querying Parquet remains a separate, working reader option.
[Documented native DuckDB access](https://duckdb.org/docs/2.0/core_extensions/httpfs/https),
[comparison implications](reader_benchmark.md#implication-of-direct-zenodo-querying).

## Real Zenodo tests across the candidates

The user then requested actual Zenodo tests for all solutions in the comparison. The expanded
[access report](zenodo_access_tests.md) covers Parquet via Arrow, pandas, DuckDB and Polars
(native expressions and SQL), native DuckDB, HDF5, Zarr ZIP and Lance/LanceDB paths. Tests use
existing public files; no PPDS data or new fixtures were uploaded.

Native DuckDB, HDF5 and Zarr ZIP now have successful selective reads matching checksum-verified
local references. The native DuckDB check retrieves catalog/schema/selected rows using 1.59 MB
of declared range-response bodies from a 20.98 MB database. This corrects any inference that
Zenodo inherently prevents native DuckDB queries. The previous PPDS size and scan-layout
measurements remain valid, and the unrelated fixtures do not supply a fair speed ranking.

For Parquet, ordinary pandas URL reading and passing an HTTP file-like object to Polars consume
the complete 3.33 MB file despite returning filtered rows. Arrow/pandas with a known-size range
handle avoid unmeasured discovery GETs. Both native Polars expressions and SQL match the reference;
transport evidence and the marimo execution check are recorded separately in the access report.

Lance's raw HTTPS APIs reject the URI scheme, but its native S3 provider can read actual Zenodo
byte ranges with an anonymous path-style endpoint configuration. No bridge is required for this
object access. Complete querying of a valid unpacked Lance file/table through that route remains
untested; the located public Lance dataset is packaged as a ZIP of legacy tables. Keep these
distinct results rather than labeling all Lance access impossible.

The native Polars transport follow-up tests both IN and equality predicates through expressions
and SQL. All results are correct, but TCP receive totals (including TLS/HTTP overhead) are
3.57–3.58 MB for the 3.33 MB Parquet fixture, so no sub-file transfer is demonstrated. This does
not prove whole-file HTTP payload access or predict the consolidated PPDS layout. It qualifies
the reader recommendation: retain Polars for analysis/native SQL, while validating a known-size
Arrow range-read strategy for remote selections instead of assuming local speed implies minimal
Zenodo IO. No production reader migration was made.

A separate SQLite baseline uses GenomicSQLite's packaged web VFS. Both Zenodo URL forms fail
with HTTP 403, while Python range requests and checksum-verified local SQLite queries pass.
This is an adapter/endpoint failure; sqlite-vec similarity queries were not introduced. The
seven successful reader classes also pass actual remote queries inside marimo 0.25.2 during
headless HTML export. Browser interactions and reactive reruns remain untested.

## Benchmark population

The original measurements use 319 gait reports. The later comparison uses 322. See the [benchmark definitions](lab_format_benchmark.md).
