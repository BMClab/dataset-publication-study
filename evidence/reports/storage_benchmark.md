# PPDS storage benchmark — 2026-11-13

*Historical research record, November 2026. See the [evidence index](../README.md) for inputs, versions and available observations.*

Subject identifiers in this historical benchmark refer to the pre-renumbering snapshot; current dataset files use sequential release IDs. Benchmark values and source artifacts are preserved.

This is an exploratory comparison of the actual consolidated PPDS cohort, using its existing
array-access and analysis workloads. **The publication format and access engine remain open.**
The conversation and priorities are recorded in [storage_format_discussion.md](storage_format_discussion.md).
The experiment creates separate products outside `data/`; it does not migrate the working dataset.

After reviewing these results, the user preferred consolidated Parquet among the tested candidates
and proposed a replaceable storage reader. Lance/LanceDB is still under consideration for both
storage and querying; it was not measured here. See the [follow-up discussion](storage_format_discussion.md#lancelancedb-follow-up).

The subsequent [expanded reader benchmark](reader_benchmark.md) measures Lance/LanceDB, Polars
and pandas, adds multi-subject/condition/trial selection, a live Zenodo Parquet check and explicit
reliability/hosting evidence. Its within-series comparisons supersede using this initial experiment
alone to choose the reader; the original measurements and their scope remain unchanged below.

## Scope and correctness

**Dataset snapshot.** These measurements use 319 gait reports. The [later benchmark](lab_format_benchmark.md) uses 322. Timings and sizes in this report describe the original snapshot.

The input contains 95 subjects, 3,188 dynamic pressure trials, 867,585 frames and 109,852,252
nonzero pressure records, plus 190 standing foot images and 190 original STL scans. Reconstructing
the dynamic measurements as `uint16[frame,353,64]` requires **39.20 GB** before compression.
Values are lossless integer kPa. Standing remains a separate logical measurement: two foot-local
peak images per subject, without an invented time series.

Two scopes must be compared separately:

- **Primary-pressure package:** dynamic pressure, standing, subject information and the trial index.
  HDF5 and Zarr implement only this scope. Their metadata are a JSON representation of the index
  and subject values, rather than a validated round trip of every original table's Arrow types and
  scientific data dictionary.
- **All measurement tables and scans:** pressure, standing, subjects, trials, footprints,
  spatiotemporal, grf, grf_cycle and scans. The Parquet and native DuckDB bundles implement this
  scope. Manuscript, workbook, coding document, README, example code and other documentation are
  outside these file-size totals and would still accompany a release.

[Full verification](../observations/verification.json) passed: SHA-256 over every sparse pressure
record in both consolidated Parquet layouts and native DuckDB, and over every reconstructed
dense pressure cell in HDF5 and Zarr; all 190 standing images in both array containers also matched.
The source-file SHA-256 checks confirmed that the benchmark left `data/` unchanged.
[Bundle verification](../observations/bundle_verification.json) compared all seven original non-pressure
tables with the native tables in both directions, checked the bytes of all 190 scans and checked
the values, types and scientific metadata of a selected-trial Parquet export. SQL cohort averages
are compared after rounding to 12 decimal places to tolerate floating-point reduction order.

These are benchmark prototypes, rather than interchangeable release candidates. In particular,
the current source `trials.row_group` values address the original subject files; a production
consolidation must rebuild those physical locators and port the access API. The indexed prototype
uses the verified build rule `trial_id == consolidated row_group` instead.

## Layouts and readers

| Label | Physical pressure representation and access |
| --- | --- |
| Current / Arrow | Existing 95 subject Parquet files; trial-aligned row groups, PyArrow statistics filtering |
| Trial Parquet / Arrow | One dynamic-pressure file, 3,188 trial-aligned row groups; generic statistics filtering |
| Indexed Parquet / Arrow | The same file; trial index selects row groups directly |
| 128k Parquet / Arrow | One dynamic-pressure file, 885 row groups, up to 131,072 rows each; statistics filtering |
| Trial Parquet / SQL | Trial-aligned file queried by DuckDB |
| 128k Parquet / SQL | Larger-row-group file queried by DuckDB |
| Native DuckDB | Persistent tables, ordered dynamic rows; queried by the same DuckDB engine |
| HDF5 | Dense `uint16` frames, chunks `(64,353,64)`, gzip level 4 and shuffle |
| Zarr ZIP | Same dense shape/chunks, Zarr v3, Blosc Zstd level 3 and bitshuffle, one ZipStore file |

Consolidated Parquet uses Zstd level 9 and dictionary encoding. Its pressure package also needs
`standing.parquet`, `subjects.parquet` and `trials.parquet`: four files total. Native DuckDB, HDF5
and Zarr put those logical components inside their respective single containers. This tests a
small-file-count package without forcing standing and dynamic pressure into the same row schema.
All-tables Parquet adds four derived tables and a scan table, for nine files. Each scan is one row
group containing the unchanged original STL bytes, compressed with Zstd level 9; scan-BLOB min/max
statistics are disabled. The resulting scan table is 217.94 MB, versus 491.91 MB of original STL.

DuckDB uses four threads and a 4 GB memory limit. Zarr concurrency and worker limits are four;
HDF5 has a 16 MiB raw chunk cache. Array chunks span consecutive global frames and may cross trial
boundaries. These are concrete settings, not an exhaustive optimization of every codec and layout.
Different sparse/dense representations also affect the results: this is a package-and-reader
comparison, not a claim about container formats independent of their schemas.

## Size and access measurements

<!-- MEASURED_TABLES -->

### Package sizes

| Primary-pressure package | MB (decimal) | Files |
| --- | --- | --- |
| Current / Arrow | 132.81 | 98 |
| Trial Parquet / Arrow | 132.61 | 4 |
| 128k Parquet / Arrow | 123.27 | 4 |
| Native DuckDB | 347.35 | 1 |
| HDF5 | 150.32 | 1 |
| Zarr ZIP | 229.76 | 1 |

### All measurement tables and scans

| Package | MB (decimal) | Files |
| --- | --- | --- |
| Current Parquet + original STL | 669.94 | 292 |
| Consolidated Parquet | 395.77 | 9 |
| Native DuckDB | 633.09 | 1 |

The indexed and SQL trial-Parquet readers share the trial-Parquet file; the 128k SQL
reader shares the 128k file. They do not add duplicate publication files.

### Local first access

| Reader | Frame ms | Trial ms | Subject ms | Standing ms |
| --- | --- | --- | --- | --- |
| Current / Arrow | 21.5 | 24.9 | 97.3 | 14.8 |
| Trial Parquet / Arrow | 134.4 | 117.8 | 173.9 | 18.2 |
| Indexed Parquet / Arrow | 57.0 | 58.3 | 133.7 | 18.3 |
| 128k Parquet / Arrow | 82.9 | 75.7 | 123.2 | 18.8 |
| Trial Parquet / SQL | 376.6 | 277.5 | 357.8 | 120.1 |
| 128k Parquet / SQL | 131.4 | 128.8 | 186.8 | 75.0 |
| Native DuckDB | 49.6 | 56.2 | 109.4 | 49.3 |
| HDF5 | 20.8 | 46.9 | 780.6 | 9.6 |
| Zarr ZIP | 105.3 | 104.2 | 265.9 | 78.6 |

Medians of five fresh-reader repetitions. Subject reads return every dynamic frame of
the selected subject; first-access totals include opening/index discovery.

### Opening versus reused readers

| Reader | Trial open ms | Trial first query ms | Trial warm ms | Frame warm ms |
| --- | --- | --- | --- | --- |
| Current / Arrow | 14.1 | 11.4 | 9.7 | 7.6 |
| Trial Parquet / Arrow | 14.9 | 102.8 | 57.2 | 67.6 |
| Indexed Parquet / Arrow | 14.5 | 44.0 | 7.7 | 5.8 |
| 128k Parquet / Arrow | 11.0 | 65.2 | 50.3 | 53.3 |
| Trial Parquet / SQL | 94.7 | 188.1 | 205.8 | 231.4 |
| 128k Parquet / SQL | 63.1 | 59.5 | 56.9 | 73.7 |
| Native DuckDB | 43.7 | 12.0 | 6.2 | 3.3 |
| HDF5 | 12.0 | 34.2 | 33.9 | 8.2 |
| Zarr ZIP | 92.6 | 11.2 | 8.9 | 3.6 |

Warm medians use ten timings (two queries in each of five readers). Independently
reported component medians need not add to the median total.

### Process memory

| Reader | Trial peak MiB | Subject peak MiB |
| --- | --- | --- |
| Current / Arrow | 206.7 | 550.6 |
| Trial Parquet / Arrow | 227.4 | 575.2 |
| Indexed Parquet / Arrow | 225.4 | 577.5 |
| 128k Parquet / Arrow | 254.4 | 558.0 |
| Trial Parquet / SQL | 208.8 | 551.1 |
| 128k Parquet / SQL | 188.0 | 529.5 |
| Native DuckDB | 181.3 | 535.2 |
| HDF5 | 155.0 | 477.1 |
| Zarr ZIP | 161.0 | 476.2 |

### Full-corpus maximum pressure by trial

| Configuration | Seconds | Peak MiB |
| --- | --- | --- |
| Current / Arrow | 0.763 | 194.5 |
| Trial Parquet / Arrow | 0.908 | 196.2 |
| 128k Parquet / Arrow | 0.639 | 180.9 |
| Trial Parquet / SQL | 0.987 | 174.4 |
| 128k Parquet / SQL | 0.794 | 155.5 |
| Native DuckDB | 0.507 | 466.3 |
| HDF5 | 83.930 | 156.0 |
| Zarr ZIP | 22.214 | 179.2 |

One pass per configuration. The sparse-table configurations all use DuckDB SQL for this
aggregation, including configurations labeled Arrow for selective reads. Dense array
candidates scan reconstructed grid chunks and reduce in NumPy. The indexed-Parquet
variant is omitted here because its aggregate path equals the trial-Parquet path.

### HTTP trial access

| Reader | Body MB | Requests | 0 ms first ms | 20 ms first ms | 20 ms warm ms |
| --- | --- | --- | --- | --- | --- |
| Current / Arrow | 0.209 | 5 | 156.6 | 196.0 | 6.7 |
| Trial Parquet / Arrow | 2.497 | 6 | 255.0 | 290.3 | 50.1 |
| Indexed Parquet / Arrow | 2.497 | 6 | 180.2 | 243.1 | 5.4 |
| 128k Parquet / Arrow | 1.318 | 7 | 207.7 | 280.3 | 78.3 |
| Trial Parquet / SQL | 7.791 | 21 | 429.1 | 649.3 | 296.3 |
| 128k Parquet / SQL | 2.570 | 20 | 203.9 | 502.7 | 198.5 |
| Native DuckDB | 3.158 | 10 | 110.4 | 237.6 | 4.5 |
| HDF5 | 0.482 | 8 | 166.2 | 284.1 | 32.1 |
| Zarr ZIP | 1.261 | 9 | 188.6 | 335.8 | 73.4 |

### HTTP complete-subject access

| Reader | Body MB | Requests | 0 ms first ms |
| --- | --- | --- | --- |
| Current / Arrow | 1.245 | 5 | 195.9 |
| Trial Parquet / Arrow | 3.575 | 6 | 343.7 |
| Indexed Parquet / Arrow | 3.575 | 6 | 268.6 |
| 128k Parquet / Arrow | 1.800 | 6 | 244.9 |
| Trial Parquet / SQL | 8.872 | 68 | 1725.8 |
| 128k Parquet / SQL | 3.404 | 30 | 265.6 |
| Native DuckDB | 8.139 | 21 | 1192.4 |
| HDF5 | 1.993 | 29 | 1031.4 |
| Zarr ZIP | 3.204 | 34 | 427.5 |

HTTP 0 ms medians use five readers; 20 ms medians use three. Delay is per request,
not a prescribed end-to-end round-trip time. Payload and request columns describe the
zero-delay first access. No candidate transfers its entire package for a trial.

### All-tables bundle access

| Query | Parquet local ms | Native local ms | Parquet HTTP 20 ms | Native HTTP 20 ms | Parquet body MB | Native body MB |
| --- | --- | --- | --- | --- | --- | --- |
| cohort | 91.6 | 32.6 | 871.5 | 229.6 | 3.538 | 2.109 |
| footprints | 110.6 | 33.2 | 815.8 | 210.3 | 4.355 | 2.896 |
| grf | 89.6 | 32.1 | 755.8 | 205.9 | 4.005 | 2.634 |
| scan | 93.9 | 798.8 | 739.4 | 20926.5 | 4.644 | 235.418 |

Local medians use five readers; HTTP medians use three. HTTP body sizes use zero-delay
runs. HTTP 20 ms columns show total first-access time in milliseconds, including the
injected per-request delay. Both packages are queried with DuckDB. Complete Parquet
eagerly binds nine table views; these totals include that setup cost.

**Interpretation:** consolidation is viable, and it does not require one file per subject.
Indexed Parquet retains millisecond-scale repeated trial access; generic filtering and SQL
over thousands of small row groups cost more in this implementation. Native DuckDB
provides fast reused SQL access and a single complete data file, with a larger package.
The tested dense layouts offer useful array access but do more work for broad pressure
reductions and subject reads. Their performance is not evidence against other chunk/codec
choices or sparse array representations.

My provisional preference is to keep consolidated Parquet as the leading portable-release
candidate and assess native DuckDB as a convenience bundle or a generated local cache.
The results do not yet select a final publication layout: actual Zenodo reads, several
subjects/trial lengths, metadata/export contracts and the intended notebook runtime
should be checked before migration. LanceDB/SQLite scalar workloads and alternative
array layouts remain unmeasured.

<!-- END_MEASURED_TABLES -->

## Timing and HTTP protocol

Selective pressure access uses `s050`, comfortable walking trial 3 (280 frames), frame 140,
all of that subject's dynamic trials, and both standing feet. These are representative access
patterns, but only one subject and one dynamic trial are sampled for selective timings.
The full-corpus query computes maximum pressure for every trial. Bundle queries perform an
age-group/sex/condition cohort aggregation of gait speed, reconstruct left comfortable-walking
footprints, read comfortable-walking force traces, and extract the subject's left STL bytes.
Scan parsing and plot rendering are excluded; the benchmark measures data delivery to those steps.

Each repetition uses a fresh process and reader. Module imports happen before the storage timer;
their setup time is recorded separately. First-access totals include reader setup, trial-index
loading, selection and conversion to the returned dense arrays or bytes. Two subsequent queries
reuse the same reader for the small selections; their warm-query timings are recorded separately.
The full-subject access is not warm-repeated. Output hashing is outside the timer. Peak RSS includes
imports, validation and warm repeats; it is not isolated query working memory.

The OS page cache was not flushed and was generally warm. This is **not a cold-disk benchmark**.
The Linux machine has 16 logical CPUs and 65.75 GB RAM and was shared with other work. Load averages
are retained in the measurement records where available. Five consecutive repetitions per selective
local/zero-delay HTTP selection and three per latency-injected or bundle HTTP selection reduce noise,
but do not justify interpreting small timing differences as intrinsic format advantages. The global
pressure aggregation has one measurement per configuration and no uncertainty estimate.

HTTP tests use a localhost range-capable server, with either no injected delay or 20 ms added to
each HEAD/GET request. This models request overhead only: it has no WAN bandwidth limit, TLS,
redirects, authentication, server-side cache model or real Zenodo connection. Requests include HEAD;
bytes count successful response body payloads, excluding headers. Counters stop after the first
query; warm-repeat traffic is stored separately. The fsspec readers use fresh file caches and
64 KiB readahead blocks; DuckDB uses its HTTPFS behavior. HTTPFS installation occurs before timing.
Zarr ZIP remote access here depends on the tested ZipStore/fsspec versions, not a generic assumption
that all ZIP-based products support efficient remote reads.

The SQL Parquet readers eagerly register views before loading the index; the complete reader
registers all nine table views. This pays additional footer/discovery cost on opening. Native SQL
versus Parquet SQL uses the same query definitions, while the Arrow variants demonstrate another
access strategy. Warm-query and first-query times must therefore be read together. Lazy discovery,
explicit Parquet schemas and longer-lived notebook connections could change first-access behavior.

## Scan BLOB limitation in the native bundle

The default native bundle returned the correct STL, but first access transferred **235.42 MB in
898 requests**, versus **4.64 MB in 30 requests** from the complete Parquet package. The requested
STL itself is 2,146,884 bytes. With 20 ms injected per request, native first access had a median
of **20.93 seconds**, versus **0.74 seconds** for Parquet. This is a material limitation for a
single-file native release containing scans in the tested layout.

Diagnostics (`scan_diagnostics.json`, historical source) show a sequential scan with both scalar predicates
pushed down, and one Zstd BLOB segment covering all 190 scans with 890 additional storage blocks.
The large transfer is consistent with that coarse scan/storage granularity; this is an inference
from the plans and counters, rather than proof that every DuckDB BLOB representation behaves this
way. A single diagnostic run with `SET storage_block_prefetch='NEVER'` still transferred 234.89 MB.
Adding `CREATE INDEX scans_subject ON scans(subject)` to a separate copy retained a sequential
scan for the original two-filter query and transferred 235.42 MB. A subject-only predicate used
the index, but that was a different query and was not included in the repeated comparison.
These two changes did not resolve the original workload. DuckDB documents the scope of eligible
[ART index scans](https://duckdb.org/docs/2.0/guides/performance/indexing); the observed execution
plans, rather than index existence alone, determine what ran here.

Further work could test a different native scan representation or a two-file package with native
tabular data plus scans in Parquet. The current evidence supports keeping the scan layout as an
explicit decision; fast native pressure queries do not establish efficient native scan delivery.

## Build measurements and portability

The combined pressure build took about 606 seconds. It shares source reads, sparse-to-dense
reconstruction and buffers across candidates, so its individual write-kernel timings are **not**
comparable standalone conversion times. The manifest retains them for diagnostic purposes.
The native pressure build took 23.42 seconds after consolidated Parquet existed; the scan Parquet
write took 19.09 seconds. These have different starting inputs and must not be ranked as complete
build pipelines. The selected-trial native-to-Parquet COPY took 23 ms in one check; restoring custom
scientific metadata was a separate step and is essential for a release-quality export.

A Parquet release can be read without DuckDB, and its independent tables may have different schemas.
A native DuckDB release can hold those tables and definitions in one physical file, but needs a
declared compatible reader/storage version. Neither format requires downloading the entire dataset
for every selection under the tested HTTP readers. HDF5 and Zarr would need additional metadata,
derived-table and scan packaging work to become complete publication candidates.

LanceDB and sqlite-vec were raised during discussion but were not benchmarked here. The user
selected existing PPDS workloads, with no vector-similarity requirement; that does not exclude
LanceDB's scalar or multimodal access capabilities. The user subsequently asked to consider it as
both storage and database, so it remains an active comparison candidate. No ranking of LanceDB
against Parquet, or conclusion about vector-index performance, follows from these measurements.
SQLite without vector extensions could also be tested separately if its portability or query
model becomes a specific requirement.
