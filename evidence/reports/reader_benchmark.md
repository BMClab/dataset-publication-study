# PPDS readers, multimodal storage and hosting — 2026-11-13

*Historical research record, November 2026. See the [evidence index](../README.md) for inputs, versions and available observations.*

Subject identifiers in this historical benchmark refer to the pre-renumbering snapshot; current dataset files use sequential release IDs. Benchmark values and source artifacts are preserved.

## Minimum requirements behind the search

The search started from an existing Python project whose examples already run as **marimo
notebooks**. This is the consolidated record of the minimum requirements, including those made
explicit during the discussion. Marimo compatibility was confirmed explicitly after the benchmark;
it was already the repository's notebook framework, rather than a new framework chosen by this search.

| Requirement | Expected behavior |
| --- | --- |
| Python installation | Install and run in a regular Python environment. |
| Marimo compatibility | Work well in the existing marimo notebooks, including interactive subject/trial selection, tabular analysis, array retrieval and scientific visualization. A replacement reader must preserve that integration. |
| Multimodal scientific data | Handle numeric measurements, arrays/time series, subject/trial metadata and original 3D scan payloads within the same dataset. |
| Dataset size | Suit **whole datasets of approximately 10 MB–1 GB**, rather than assuming that range describes each individual scan or other object. |
| Zenodo publication and access | Store the dataset as files in Zenodo and read it back from the published file URLs, without requiring a separate live database service. |
| Partial retrieval | Retrieve one subject or subsets of subjects, trials and conditions, with selective remote reads rather than requiring a complete dataset download before selection. |
| Scientific fidelity | Preserve measurement values, scan bytes, types, units, coordinates, trial relationships and descriptive metadata, with reproducible validation. |

Performance, memory use, compressed size, reliability, usability and reader/host availability were
comparison criteria once the required capabilities were established. Fewer publication files and
one physical pressure file were preferences subordinate to performance and usability. Parquet,
Polars, DuckDB, and choosing SQL or a native query API were candidate solutions, not prerequisites.

## Scope of this comparison

This extends the [first storage experiment](storage_benchmark.md) with Lance/LanceDB, Polars and
pandas. It uses the real consolidated PPDS measurements, rather than vector-search or synthetic
performance claims. Products remain outside `data/`; production dependencies and the working
distribution are unchanged. The [experiment scope](reader_benchmark_plan.md) and
[conversation notes](storage_format_discussion.md) record the user's requirements.

**Dataset snapshot.** These measurements use 319 gait reports. The [later benchmark](lab_format_benchmark.md) uses 322. Timings and sizes in this report describe the original snapshot.

Direct partial reads from published files are the delivery target. A local reader or an S3-only
workflow does not establish the Zenodo requirement. The measured full PPDS publication candidates
fall inside the target size range; this is not a controlled size sweep over every point in that
range. The command-line backend benchmarks do not constitute a new end-to-end marimo UI test.

Storage and execution are separate choices. Pandas and Polars read the same Parquet files as
Arrow and DuckDB. Lance supplies a file/table format; LanceDB Embedded supplies management and
query APIs over it. The DuckDB Lance extension supplies an additional SQL path over Lance. None
of the measured local paths requires a managed database account or embeddings.

## Results

<!-- READER_TABLES -->

### Complete measurement tables and original scans

| Product | MB (decimal) | Files |
| --- | --- | --- |
| Trial-aligned Parquet | 395.77 | 9 |
| 128k-group Parquet | 386.43 | 9 |
| Native DuckDB | 633.09 | 1 |
| Lance, compressed binary scans | 480.86 | 53 |
| Lance, original bytes through Blob v2 | 754.92 | 57 |

These totals exclude accompanying documentation/code and do not count both Lance scan
alternatives in the same publication. Every measured full-data candidate is under 1 GB.

### Local pressure access

| Reader | Frame first ms | Trial first ms | Trial reused ms | Whole subject ms |
| --- | --- | --- | --- | --- |
| Arrow / indexed Parquet | 33.3 | 34.3 | 4.7 | 93.5 |
| DuckDB / trial Parquet | 234.3 | 223.4 | 145.0 | 243.9 |
| DuckDB / 128k Parquet | 89.1 | 87.9 | 42.7 | 125.6 |
| Native DuckDB | 36.0 | 38.3 | 4.0 | 77.1 |
| Polars / trial Parquet | 27.2 | 28.9 | 6.3 | 68.1 |
| Polars / 128k Parquet | 16.5 | 19.2 | 4.5 | 56.1 |
| Pandas / trial Parquet | 147.8 | 113.8 | 88.3 | 101.4 |
| Pandas / 128k Parquet | 62.8 | 54.7 | 34.7 | 76.4 |
| Lance / Arrow reductions | 39.7 | 37.8 | 27.5 | 63.4 |
| LanceDB / Arrow reductions | 63.0 | 73.4 | 65.3 | 253.2 |
| DuckDB / Lance | 212.1 | 221.1 | 27.8 | 264.6 |

First totals are medians of five fresh readers; reused medians contain two timings from
each reader. Small differences are subject to shared-host noise and warm-cache behavior.

### Analysis, scan and multi-selection access

| Reader | Trial maxima s | Cohort first ms | STL first ms | 8-trial subset ms |
| --- | --- | --- | --- | --- |
| Arrow / indexed Parquet | 1.589 | 14.9 | 17.1 | 57.2 |
| DuckDB / trial Parquet | 0.466 | 34.5 | 43.2 | 240.7 |
| DuckDB / 128k Parquet | 0.331 | 37.4 | 42.8 | 108.9 |
| Native DuckDB | 0.307 | 31.7 | 812.3 | 54.6 |
| Polars / trial Parquet | 0.342 | 10.5 | 20.4 | 42.7 |
| Polars / 128k Parquet | 0.291 | 9.3 | 20.4 | 33.8 |
| Pandas / trial Parquet | 1.163 | 28.4 | 28.1 | 129.2 |
| Pandas / 128k Parquet | 0.914 | 28.7 | 26.3 | 81.5 |
| Lance / Arrow reductions | 1.000 | 13.5 | 17.9 | 69.3 |
| LanceDB / Arrow reductions | 1.477 | 20.9 | 26.8 | 166.2 |
| DuckDB / Lance | 1.999 | 201.2 | 220.4 | 262.1 |

The dedicated Blob-v2 STL path measured **18.4 ms** locally.
Aggregate and subset medians use three first-reader measurements; cohort/STL use five.

### Short and long trials

| Reader | 63 frames ms | 280 frames ms | 1,306 frames ms |
| --- | --- | --- | --- |
| Arrow / indexed Parquet | 26.7 | 34.3 | 47.0 |
| DuckDB / trial Parquet | 220.2 | 223.4 | 231.5 |
| DuckDB / 128k Parquet | 85.5 | 87.9 | 93.7 |
| Native DuckDB | 36.2 | 38.3 | 44.1 |
| Polars / trial Parquet | 25.2 | 28.9 | 33.6 |
| Polars / 128k Parquet | 14.3 | 19.2 | 26.2 |
| Pandas / trial Parquet | 102.3 | 113.8 | 125.2 |
| Pandas / 128k Parquet | 39.6 | 54.7 | 49.4 |
| Lance / Arrow reductions | 42.2 | 37.8 | 61.0 |
| LanceDB / Arrow reductions | 76.7 | 73.4 | 141.6 |
| DuckDB / Lance | 215.5 | 221.1 | 238.1 |

### Separate sampled-worker memory profile

| Reader | Trial peak MiB | Subject peak MiB | Maxima peak MiB |
| --- | --- | --- | --- |
| Arrow / indexed Parquet | 209.9 | 567.5 | 300.8 |
| DuckDB / trial Parquet | 238.9 | 581.5 | 206.7 |
| DuckDB / 128k Parquet | 208.1 | 553.3 | 187.2 |
| Native DuckDB | 206.0 | 564.3 | 498.0 |
| Polars / trial Parquet | 208.4 | 564.9 | 202.1 |
| Polars / 128k Parquet | 210.5 | 555.7 | 194.8 |
| Pandas / trial Parquet | 230.4 | 608.9 | 2341.5 |
| Pandas / 128k Parquet | 229.5 | 580.7 | 2367.2 |
| Lance / Arrow reductions | 277.9 | 620.5 | 385.3 |
| LanceDB / Arrow reductions | 285.0 | 625.3 | 382.5 |
| DuckDB / Lance | 302.7 | 642.7 | 468.8 |

The batch-reduced pandas aggregate used **303.3 MiB** sampled peak RSS and **2.096 s** median unsampled execution.
Memory is a separate one-pass profile per configuration; sampling interval is 2 ms.

### Partial reads over generic HTTP

| Reader | Trial MB | Requests | 0 ms delay, ms | 20 ms delay, ms | 8-trial subset MB |
| --- | --- | --- | --- | --- | --- |
| Arrow / indexed Parquet | 2.497 | 6 | 44.8 | 173.5 | 2.845 |
| DuckDB / trial Parquet | 7.775 | 19 | 255.0 | 588.1 | 7.970 |
| DuckDB / 128k Parquet | 2.554 | 18 | 120.0 | 447.2 | 3.453 |
| Native DuckDB | 3.158 | 9 | 69.1 | 211.7 | 10.236 |
| Polars / trial Parquet | 2.664 | 5 | 35.3 | 139.5 | 2.859 |
| Polars / 128k Parquet | 1.419 | 7 | 28.5 | 130.2 | 2.034 |
| Pandas / trial Parquet | 2.497 | 6 | 124.1 | 253.9 | 2.845 |
| Pandas / 128k Parquet | 1.318 | 7 | 62.0 | 212.4 | 1.999 |

Ordinary `pd.read_parquet(url, filters=...)` transferred **132.552 MB** for the same trial; explicit fsspec/PyArrow transferred **2.497 MB**.
A row filter does not guarantee a selective network read when the URL handler first downloads
the complete file. All eight generic-HTTP Lance attempts failed at URI-provider selection,
before data IO; they are not successful low-latency reads.

### Supplementary object-store protocol experiment: one STL

| Reader | Body MB | Requests | LISTs | 0 ms delay, ms | 20 ms delay, ms | Reused scan ms |
| --- | --- | --- | --- | --- | --- | --- |
| Arrow / indexed Parquet | 1.124 | 5 | 0 | 25.9 | 128.7 | 6.1 |
| Polars / 128k Parquet | 1.290 | 4 | 0 | 28.0 | 111.0 | 8.8 |
| Lance / Arrow reductions | 1.069 | 14 | 0 | 2045.1 | 2333.4 | 7.7 |
| LanceDB / Arrow reductions | 1.074 | 19 | 3 | 1044.5 | 1434.7 | 8.9 |
| LanceDB / Blob v2 | 2.215 | 17 | 3 | 1042.6 | 1392.7 | 8.5 |

These are client+fixture-server measurements, not production S3 or Zenodo timings.
Lance reads use its supported S3 provider; Parquet controls use ordinary range URLs on
the same object map. Totals include reader setup and fixture request handling; fixture-server
startup is excluded. The roughly one-second SDK opening overhead was not isolated, so these
figures cannot attribute that delay solely to the storage format. Reused scans share the reader/cache.

### Synthetic default export contract

| Route | Pressure dtype | All values exact | Units metadata retained | Exact Arrow schema | Explicit schema restores contract |
| --- | --- | --- | --- | --- | --- |
| pyarrow | uint16 | True | True | True | True |
| pandas_default | double | True | False | False | True |
| pandas_arrow_backed | uint16 | True | False | False | True |
| polars_default | uint16 | True | False | False | True |
| duckdb_default | uint16 | True | False | False | True |
| lance_arrow_export | uint16 | True | True | True | True |
| lancedb_arrow_export | uint16 | True | True | True | True |

All six damaged-input fixtures raised errors. These are tested behaviors, not a
long-term reliability score. A data reader must preserve the scientific schema explicitly.

**Evidence totals:** 985 timed first accesses plus 34 separately sampled profiling accesses matched the reference, with zero unexpected failures. Eight additional generic-HTTP Lance attempts failed with the expected unsupported-provider error.

**Decision supported by these results:** consolidated Parquet remains the leading PPDS
publication candidate under the direct-Zenodo requirement. Polars is a strong general
reader for these selections and reductions; indexed Arrow provides efficient reused
pressure access, and DuckDB retains a useful SQL interface. Pandas remains practical for
selected data, with deliberate remote IO and memory/schema handling. Lance/LanceDB is a
valid local/object-store alternative worth considering for other projects, but the tested
native readers do not satisfy direct generic-HTTPS Zenodo access. An adapter would need
its own validation before that conclusion changes.

<!-- END_READER_TABLES -->

## Implication of direct Zenodo querying

The user emphasized that querying the published files directly is central to their appeal;
being able to archive a format on Zenodo is insufficient. This strengthens the preference for
Parquet, whose Python reader paths have already returned matching selections from a real public
Zenodo file. Local or object-store performance cannot establish this delivery capability.

The expanded [real Zenodo tests](zenodo_access_tests.md) now confirm selective reads of native
DuckDB, HDF5 and Zarr ZIP as well as Parquet. Native DuckDB's read-only remote `ATTACH` returned
the catalog and selected rows from a public 20.98 MB database using 1.59 MB of declared GET
response bodies, matching a separately downloaded, checksum-verified local reference. Its PPDS
size and scan-transfer disadvantages remain properties of the tested PPDS layout, not a lack of
Zenodo transport support.

The tested Lance/LanceDB APIs still reject raw HTTPS dataset URIs. However, an anonymous,
path-style **native S3 endpoint configuration reads Zenodo object ranges without a bridge**.
Successful querying of a valid unpacked Lance file/table through that configuration remains
untested: the located public fixture is a ZIP of legacy Lance tables. Preserve the distinction
between provider rejection, working byte transport and a complete dataset query. The access
report also records Parquet configuration pitfalls and the marimo integration check.

Native Polars expressions and SQL both return the expected Zenodo selections, but four socket
checks (IN and equality predicates) receive 3.57–3.58 MB including TLS/HTTP overhead for a
3.33 MB fixture: no below-file-size transfer is demonstrated. Known-size Arrow/pandas handles
read 364 KB in range-only responses. These different measurement layers and the unrelated
fixture do not override PPDS timings, but qualify any assumption that the fastest local reader
also gives the best remote IO. A packaged SQLite HTTP VFS was additionally tested and received
HTTP 403; Python range controls and local database queries pass. All seven working reader
classes execute correctly in a headless marimo notebook. Full details and limitations are in
[the access report](zenodo_access_tests.md).

## What was measured

**SQL-interface follow-up:** the user proposed using Polars for SQL as well as native retrieval.
Polars SQL translates into its expression engine; a separate DuckDB requirement is unnecessary
unless a concrete query or integration needs it. A later functional check matched PPDS native
results for multi-subject filtering, all-trial maxima and a cohort join/aggregation. Output types
and optimized plans can differ. See [discussion and saved queries](storage_format_discussion.md#polars-sql-and-native-access-follow-up).
The timing tables above measure the native Polars expression path, not a separately timed SQL path.
The official [Polars 2.0 release](https://pola.rs/posts/release-polars-2/) explicitly treats SQL as
first class and benchmarks that interface against DuckDB. The
[2.1 changelog](https://pola.rs/posts/polars-2-1-changelog/) expands SQL and Parquet support further.
Both our measured native path and the SQL correctness checks already used 2.1.0. These sources
strengthen the recommendation to expose both Polars interfaces; their benchmark methodology and
versions differ from PPDS, so their reported speedups are not substituted into our tables.

The full input is unchanged from the first experiment: 95 subjects, 3,188 pressure trials,
867,585 dynamic frames, 109,852,252 sparse pressure records, 190 standing foot images, the subject
and trial indexes, four derived gait/footprint/force tables and 190 original STL scans. Dense
dynamic frames alone would occupy 39.20 GB before compression; whole-publication compressed
size is not the amount of RAM needed to materialize those arrays.

The main selection is `s050`, comfortable walking trial 3, with 280 frames; the frame query reads
frame 140. Other workloads retrieve every dynamic trial of that subject, both standing feet,
left comfortable-walking footprints, the comfortable-walking force trace, the left STL bytes,
and gait-speed cohort counts/means joined by age group, sex and condition. The broad pressure
query computes maximum pressure for every trial. Short/long trial checks use `s073 rc 2`
(63 frames) and `s036 ws 10` (1,306 frames).

The multi-selection retrieves exactly eight trials: subjects `s001` and `s050`, conditions `wc`
and `wf`, trial numbers 1 and 3. It compares the resulting list of dense arrays with the reference,
and applies the subject/condition/trial predicates in each reader. It does not fetch every
subject and then select the requested ones in notebook code.

The Parquet artifacts are identical to the first experiment: Zstd level 9, either 3,188
trial-aligned row groups or 885 groups of up to 131,072 rows. The indexed Arrow path addresses
trial-aligned groups directly. SQL views are now created lazily for the tables actually used;
the first experiment eagerly bound multiple views. Compare engines **within this run series**,
rather than interpreting changes from the first report as storage regressions or improvements.

Polars uses lazy scans, predicate/projection pushdown and streaming collection. Pandas uses
PyArrow with selected columns and filters; the remote comparison explicitly passes a seekable
fsspec file. The ordinary pandas URL handler is tested separately. For pressure maxima, ordinary
pandas materializes only the required `trial_id`/`value` columns before grouping; the separate
batch variant reduces PyArrow batches with pandas. The indexed Arrow aggregate uses bounded
Arrow batches and Arrow group reductions. Lance/LanceDB SDK aggregates also use Arrow batch
reductions; their cohort calculation uses an Arrow join/group reduction. These SDK paths are
not claims about a standalone SQL aggregator. DuckDB and DuckDB–Lance execute the same SQL query;
Polars uses native lazy group/join operations, and pandas uses DataFrame merge/group operations.

Lance uses explicit **file-format 2.2**, Zstd level-9 field hints, up to 16,777,216 rows per data
file, and Bitmap indexes on pressure trial IDs and subject IDs. Other tables have subject indexes.
Old versions/unreferenced objects are pruned only in these isolated build products, retaining a
self-contained current snapshot. The two scan alternatives are ordinary compressed binary and
the dedicated Blob-v2 API holding the original payload bytes; their package sizes must be counted
separately. Each selection uses a pinned table snapshot where the SDK supports it.

A development BTree index on repeated pressure trial IDs was a poor layout choice: the initial
pressure product occupied 650.14 MB, versus about 205.14 MB with Bitmap indexes and retained-current
snapshot packaging. Its timings are not used in the comparison. The
layout diagnostic (`reader_layout_diagnostics.json`, historical source) preserves that experiment. Index
type and snapshot cleanup matter independently of format branding.

## Timing and memory limits

Each measured access runs in a fresh subprocess/reader; small selections are followed by two
queries in the same reader. Module setup is recorded separately. Shared dependencies, including
pandas lazily used by Arrow-to-NumPy conversion, are loaded before the storage timer for every
engine. An early series with inconsistent lazy-import costs was discarded; the
diagnostic (`reader_import_diagnostic.json`, historical source) explains the change.

Cases are interleaved in a seeded random order within each workload. Main selective local
measurements have five first-reader repetitions, most supplemental/remote/aggregate measurements
have three. Timed series run sequentially after full integrity verification and artifact builds.
There are four configured worker/CPU threads where the engines expose those controls; all thread
environment settings are saved. This is a shared Linux x86-64 host with 16 logical CPUs and about
65.75 GB RAM. OS page cache is uncontrolled and generally warm; these are not cold-disk results.
Load averages are retained. Do not use small timing differences as a universal engine ranking.

Peak-memory comparisons use a separate profiling pass, sampling the worker's RSS every 2 ms
after dependency setup. This avoids an inherited high-water floor in `getrusage` when a worker
is forked from a parent that built a reference result. Samples can miss brief peaks and include
reader setup, output verification and reused-query allocations. Profiling-pass timings are not
used in the performance tables. The original OS maximum-RSS field remains in raw records for
diagnosis; it is not substituted for the sampled-worker figures in this report.

Output hashing and equivalence checks are outside the query timer. First-access totals include
opening the reader, loading trial indexes, reading data and creating the returned dense arrays
or bytes. Plot rendering and STL mesh decoding are excluded. Different returned DataFrame/Arrow
construction paths are part of each tested package-and-reader implementation.

## Network and hosting evidence

Generic HTTP tests use a loopback range server with zero or 20 ms delay **per request**. They
have no WAN bandwidth limit, TLS cost, real authentication, server rate limit or real Zenodo
latency. Counts stop after the first query; warm traffic is saved separately. The fsspec path
uses fresh 64 KiB readahead caches. Native Rust/SQL readers use their own IO/cache policies.

The tested Lance/LanceDB/extension releases reject generic HTTP and HTTPS dataset schemes before
requesting data. The eight HTTP attempts (`reader_lance_http_capability.json`, historical source) and
separate HTTPS provider probes (`lance_https_capability.json`, historical source) establish this specific
client-path limitation. They do not establish that the format cannot be published as a
downloadable archive or accessed through a new adapter. A custom adapter is not implemented or
validated by this comparison.

The supplementary S3 experiment uses a small read-only protocol subset (`s3_range_server.py`, historical source)
on loopback, with explicit object mappings, HEAD/GET/Range and object listing. Lance and LanceDB
use unsigned path-style S3 URLs and pinned snapshots; Parquet controls read the same mapped
objects through HTTP range URLs. Successful metadata-discovery 404 probes are counted as HTTP
responses, not failed data queries. The helper's tiny fixture check (`s3_fixture_probe.json`, historical source)
establishes its limited protocol behavior. This is not a production S3 service, a durability test,
or a way to claim that Zenodo exposes S3.

A separate read-only test uses an existing public **3.33 MB Parquet file on Zenodo**, selecting
one municipality/day and projecting two columns. It checks Arrow/fsspec, DuckDB HTTPFS, Polars
native HTTP and pandas/fsspec against the same nonempty result. Arrow/pandas have received-body
counters; DuckDB has HTTP response-log evidence; Polars native wire bytes are uninstrumented.
This is an actual reader/host integration check, not a PPDS-hosted-data or controlled Internet
performance comparison. See code (`zenodo_reader_probe.py`, historical source) and
raw results (`zenodo_reader_probe.json`, historical source). No PPDS data were uploaded.

The sourced [hosting assessment](storage_hosting_assessment.md) distinguishes documented support,
observed tests and unknowns, including Zenodo quotas, path/namespace requirements, correction
policy, package/platform availability and offline extension installation. A DOI or popular
library does not itself establish byte immutability, failure rate or long-term availability.

## Scientific fidelity and failure handling

[Full-data verification](../observations/reader_verification.json) checks every sparse pressure record
by SHA-256, all original non-pressure tables and scientific schema/field metadata, all 190 scans
in both Lance representations, a selected-trial Parquet export, and all 296 source-file hashes.
Every reported successful query is checked against the same reference output, including exact
pressure integer values and scan bytes; cohort floating-point means are rounded to 12 decimal
places to tolerate reduction order.

The independent synthetic reliability probe (`reliability_probes.py`, historical source) tests unsigned
integers, null versus zero, finite floating-point bits, arbitrary binary bytes, nullability and
schema/field metadata. Its [results](../observations/reader_reliability.json) separate values from schema
contracts. Different integer-null and binary-width mappings are not automatically data corruption.
Explicitly reapplying a known scientific schema after checking values restores the fixture contract
in all tested routes. The same suite exercises truncated Parquet and missing Lance data files.
Observed error handling on six damaged-input fixtures is not a statistical reliability study.

These tests do not prove crash recovery, years of backward compatibility, resistance to every
corruption mode, simultaneous-writer behavior or installation on every OS. The source and binary
availability review is dated; the actual timed environment is Python 3.12.14, PyArrow 26.0.1,
DuckDB 2.0.0, Polars 2.1.0, pandas 3.1.1, LanceDB 0.41.0 and pylance 14.0.2. The loaded DuckDB
Lance extension identifies itself as `86118537da`. Native SDK and extension internals need not
share the same Lance release; exact version compatibility belongs in a deployed reader contract.
