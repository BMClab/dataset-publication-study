# Choosing a public data format and query toolkit for the lab

*Historical research record, November 2026. See the [evidence index](../../evidence/README.md) for inputs, versions and available observations.*

## Selection criteria

Researchers should be able to open a biomechanics dataset from its Zenodo record, select participants by characteristics, join their trials to measurements, and retrieve just the data needed for an analysis. Someone working offline should be able to download the same files and run the same analysis. The intended size was about **10 MB to 1 GB for a whole dataset**. The lab used its plantar pressure dataset (PPDS) to test the following requirements.

| Requirement or preference | What counted as evidence |
|---|---|
| Zenodo publication and retrieval | Versioned files, full downloads and direct partial reads from file URLs. The analysis runs on the user’s machine or notebook server. A correct filtered result alone does not establish a partial transfer. |
| Scientific fidelity | Exact pressure values, recoverable frame dimensions, original scan bytes, stable participant and trial keys, units, coordinates, timestamps and documented missing values. |
| Scientific queries | One frame, trial or participant, a subset selected by condition, a join from participant characteristics through trials to force samples, a complete aggregation and one foot scan. |
| Usable interfaces | An installable Python library and compatibility with the lab’s marimo notebooks were required. Reusable examples for R and other languages, established readers, and the choice of SQL or DataFrame operations were desirable. |
| Practical performance | Time to the first result, time on reuse, memory, requests, bytes transferred, package size and number of files. A small file count and one pressure file were preferences. Selective access and usability took priority. |

Zenodo accepts arbitrary file formats and preserves deposited bytes. Its documented default at the time of the tests was 50 GB and up to 100 files per record. A handful of queryable files would fit comfortably and give researchers a practical alternative to downloading an entire archive. [Zenodo records](https://help.zenodo.org/docs/deposit/about-records/) · [Hosting assessment](../../evidence/reports/storage_hosting_assessment.md)

## Initial candidates and how the field narrowed

The existing distribution stored pressure in participant-specific Parquet files, other measurements in tables and meshes in individual STL files. The initial question was whether a few consolidated tables, a database file or an array container could make those data easier to publish and query. A format determines which bytes the lab publishes. A toolkit determines how users read, join and transform them. DuckDB competed in both roles. [Initial requirements and alternatives](../../evidence/reports/storage_format_discussion.md) · [First storage experiment](../../evidence/reports/storage_benchmark.md)

| Candidate | Why it entered the comparison | Outcome |
|---|---|---|
| **Parquet** | Typed, compressed columnar tables. A reader can skip columns and row groups and combine several files in a query. | **Selected for storage.** Small full package, efficient selective transfers and independent readers across languages. |
| **Native DuckDB** | One file can hold independent tables, views and scan bytes. The same engine can query this file or external Parquet. | Viable single-file alternative and fast for repeated local analysis. The tested database was larger and reading one stored mesh transferred much more data. **DuckDB was selected as the query toolkit.** |
| **HDF5 and Zarr** | Dense, chunked arrays fit frame and sensor slices. HDF5 and a Zarr ZIP could each package the pressure prototype in one file. | Both supported selected array reads on Zenodo. Participant selection and joins across trial and force tables mattered more for the lab standard. |
| **Lance and LanceDB Embedded** | Multimodal tables, scalar filtering and selective binary-object access. Vector search was unnecessary. | Local and object-store tests worked. Adoption and reader coverage were narrower. The tested generic HTTPS paths rejected the scheme, and a complete native Lance table query on Zenodo was unverified. |
| **SQLite and sqlite-vec** | Another portable single-file database, initially raised with its vector extension. | Vector search had no scientific requirement. An ordinary SQLite remote-reader probe received HTTP 403 through the tested web VFS. Local queries worked. SQLite did not enter the final performance comparison. |
| **PyArrow, pandas and Polars** | Alternative APIs over the same Parquet files. PyArrow offered indexed row-group reads, pandas a familiar baseline and Polars lazy DataFrame and SQL queries. | The lab dropped PyArrow as its public API because it wanted the same queries to be reusable outside Python. Arrow remained useful for interchange and validation. pandas stayed in the tests for a quantitative comparison. Polars advanced to the final reader decision. |
| **Vortex**, added in the final storage round | Composable encodings, native scans, integration with Polars and DuckDB, and promising scan benchmarks. | Default and compact layouts were tested. Compact Vortex was the strongest alternative for a broad remote pressure scan. Selective trial and mesh reads and ecosystem coverage favored Parquet. |

The principal shortlist was Parquet with Polars or DuckDB, native DuckDB, and Lance with LanceDB. The lab subsequently dropped Lance, HDF5 and PyArrow as public defaults and brought Vortex into the matched comparison. Interest in Vortex also came from F3’s reuse of its encodings and AnyBlox’s experiment with a WebAssembly decoder. Vortex also documents backward readability for frozen format editions. Those findings made it worth testing the current readers on the lab’s workloads. [F3 paper](https://db.cs.cmu.edu/papers/2025/zeng-sigmod2025.pdf) · [AnyBlox paper](https://gienieczko.com/anyblox-paper) · [Vortex format and compatibility](https://docs.vortex.dev/specs/file-format)

## What the early experiments established

The early storage and reader benchmarks used a pre-closure snapshot with **319 gait reports**. Standing was represented by foot-local peak images. Its pressure-only package included the participant and trial indexes. Consolidated Parquet occupied **123–133 MB in four files**, HDF5 150 MB, Zarr ZIP 230 MB and native DuckDB 347 MB. The dense array and sparse table prototypes used different representations. HDF5 was fast for a single frame. Computing peak pressure for every trial took 84 s in the dense HDF5 layout and 22 s in Zarr ZIP, compared with under 1 s for the sparse SQL layouts in that single pass. [Layouts, verification and timings](../../evidence/reports/storage_benchmark.md)

With all measurement tables and 190 meshes, the early Parquet layouts occupied **386–396 MB in nine files**, native DuckDB 633 MB in one, and Lance 481 MB in 53 objects with compressed binary scans or 755 MB in 57 with Blob v2. For a 2.15 MB STL, controlled HTTP tests transferred 235.42 MB from native DuckDB and 4.64 MB from the consolidated Parquet bundle. For frame and trial access, the choice of Parquet row groups, an explicit index and reader reuse all mattered. Keeping a single file offered little advantage to someone waiting for a single foot. [Historical storage and mesh diagnostics](../../evidence/reports/storage_benchmark.md#scan-blob-limitation-in-the-native-bundle) · [Expanded reader comparison](../../evidence/reports/reader_benchmark.md)

Public Zenodo fixtures supplied an independent check of hosting. On a 3.33 MB Parquet file, DuckDB returned a verified one-row selection with less than 0.5 MB of declared GET response bodies. PyArrow and pandas on a seekable HTTP handle with known file size consumed 0.364 MB. The ordinary pandas URL path downloaded the whole file. Both Polars query styles returned the right rows, but the native socket trace did not demonstrate a transfer below file size. Read-only attachment to a public 20.98 MB DuckDB file used 1.59 MB. HDF5 and Zarr ZIP returned verified slices. An S3-compatible Lance configuration read byte ranges from Zenodo, but a complete table query through it remained untested. These were different public files and the counters measured different layers of network traffic. [Direct Zenodo tests](../../evidence/reports/zenodo_access_tests.md)

At this stage **Parquet with Polars** was the provisional preference. Polars was fast on common local selections. Its SQL and native expressions returned equivalent values for a selection, trial maxima and a cohort join. The two forms could differ in output types, such as the integer width of a count, and in their optimized plans. At that point a second SQL engine would have added a dependency without an established need. The final round compared the two engines for the public interface across future projects. [Early recommendation](../../evidence/reports/storage_format_discussion.md#polars-sql-and-native-access-follow-up) · [SQL equivalence checks](../../evidence/observations/polars_sql_check.json)

## Matched comparison on the curated dataset

The curated benchmark (21 November 2026) and its Zenodo and local follow-ups (22 November) used **95 participants, 3,217 gait trials, 95 stance trials, 322 gait reports and 190 separate foot meshes**. All four encodings held the same eight logical tables covering participants, trials, pressure, force waveforms, cycle-average forces, spatiotemporal parameters, registered footprints and scans. Pressure comprised 112,965,976 nonzero observations from cleaned gait trials at 100 Hz and the last 100 stance frames at 10 Hz. The stored pressure unit was kPa on a 353 × 64 sensor grid. The frame count and grid shape preserve empty cells as zero within a recorded frame. Time-series axes are `(frame, y, x)`. Older package sizes describe the earlier dataset. These figures exclude any additional complete native gait recordings. [Fixture and schema audit](../../evidence/reports/lab_format_benchmark.md#what-was-compared)

| Encoding | Files | Eight tables including STL (decimal MB) | Pressure alone (MB) |
|---|---:|---:|---:|
| Parquet | 8 | 389.94 | 124.16 |
| Native DuckDB | 1 | 599.01 | — |
| Vortex, default | 8 | 782.81 | 245.60 |
| Vortex, compact | 8 | 400.89 | 131.59 |

The Parquet pressure file used Zstandard level 9 and 131,072 nonzero rows per target row group, ordered by participant, condition, trial, frame, y and x. Each foot had its own scan row group. DuckDB used native compression with no added indexes. Compact Vortex occupied **167.52 MB excluding scans**, slightly less than Parquet’s 171.98 MB. Values and original mesh bytes matched across encodings after normalizing result types. The prepared Parquet files carried nine schema annotations across six tables. The tested DuckDB and Vortex conversions exposed none of those annotations. The earlier reader study separately tested synthetic exports through PyArrow, pandas, Polars, DuckDB and Lance/LanceDB. Some default DataFrame conversions lost units or changed types even when values agreed. Reapplying an explicit schema restored the scientific contract in every tested route. Readers raised errors on all six damaged-input fixtures. [Build and schema checks](../../evidence/observations/lab_formats_schemas.json) · [Export and damaged-file checks](../../evidence/reports/reader_benchmark.md#synthetic-default-export-contract)

The four benchmark queries covered retrieving a trial with 138,035 nonzero cells, joining older participants to their slow and comfortable walking trials and ground reaction forces (GRF), fetching one 1,153,984-byte STL, and computing per-trial peaks and counts across all pressure rows. The cohort answer contained **34 participants, 680 trials and 345,523 force samples**. The selected trial and mesh were checked against their source files. The two aggregate references were calculated independently from the prepared tables, so their agreement checks the queries and encodings but cannot detect an error common to table preparation. [Workloads and verification](../../evidence/reports/lab_format_benchmark.md#workloads)

Vortex exposed three working query interfaces. Its native scan, its lazy Polars adapter and DuckDB’s `read_vortex` SQL function all returned the same trial from local files. The native predicate needed a literal with the stored unsigned integer type in the tested version. DuckDB and Polars also reproduced the cohort join over both Vortex layouts. [Tested Vortex APIs](../../evidence/reports/lab_format_benchmark.md#querying-vortex-files-from-a-notebook)

### From a local SSD

First-query elapsed time in **milliseconds**, median of five fresh readers, with the relevant data pages verified as evicted before each run. Reader creation and extension setup count toward first access. Process startup, imports and result verification were outside the timer. The matched readers used byte-identical copies of the five tables uploaded in each format. A separate control series tested pandas on the same Parquet files and a prebuilt native DuckDB database containing all eight tables (599.01 MB). No physical SSD byte counts were collected. The experiment used four engine threads on an NVMe SSD, DuckDB 2.0.1, Polars 2.1.0, vortex-data 0.93.0 and pandas 3.1.1. Including memory-resident starts and repeated queries gave 480 checked executions. [Local methods, complete tables and reproduction](../../evidence/reports/lab_formats_zenodo_ppds_local.md)

| Reader and storage | One trial | Cohort GRF join | One foot STL | All pressure |
|---|---:|---:|---:|---:|
| DuckDB / Parquet | 54.7 | 42.7 | 32.6 | 248.5 |
| Polars / Parquet | 12.2 | 31.1 | 11.3 | 300.2 |
| DuckDB / compact Vortex | 131.0 | 125.9 | 891.9 | 383.2 |
| Polars / compact Vortex | 69.9 | 37.7 | 806.0 | 348.6 |
| DuckDB / prebuilt native database | 37.7 | 47.2 | 953.1 | 268.3 |
| pandas / Parquet | 36.9 | 90.5 | 13.0 | 1,040.1 |

**With data pages evicted, Polars on Parquet led the three selective first reads and DuckDB on Parquet led the first full-pressure aggregation.** With data pages resident, the prebuilt native DuckDB database led the first full aggregation at 149.2 ms. With the connection still open it repeated the aggregation in **74.9 ms** and the join in **11.8 ms**, excluding the cost of building the database. pandas was competitive for a mesh, but its first resident full aggregation took 1,012 ms and peaked at 2,446 MiB, against 247 ms and 238 MiB for DuckDB on Parquet. This combination of time and memory was the quantitative reason to drop pandas as the default. [First and repeated reads](../../evidence/reports/lab_formats_zenodo_ppds_local.md#what-changes-after-download)

### Controlled HTTPS on the same machine

On counted loopback HTTPS, DuckDB reading compact Vortex needed 25 requests and 72.73 MB for all pressure, versus 883 requests and 124.05 MB for Parquet. For one foot the same layouts sent 233.44 MB and 1.03 MB respectively. Despite the difference in request count, DuckDB completed the loopback aggregation in 315 ms on Parquet and 449 ms on compact Vortex. [Controlled HTTPS measurements](../../evidence/reports/lab_format_benchmark.md#remote-access-to-the-same-ppds-data)

### From Zenodo

A real Zenodo test then uploaded **five** tables in both Parquet and compact Vortex. The tables were participants, trials, GRF, pressure and scans. The five Parquet files totalled 348.62 MB and the five compact Vortex files 368.60 MB. Every uploaded size and MD5 and every complete download’s SHA-256 matched. Uploads took 48.2 and 37.9 s in total, and full downloads with hashing took 289.1 and 184.3 s. Each file was transferred once in each direction. The difference in whole-file transfer times reflects the connection and service at the time of measurement, independently of reader performance. [Zenodo round trips](../../evidence/reports/lab_formats_zenodo_ppds.md#whole-file-round-trips)

**Direct notebook access.** A Python-backed marimo notebook ran the cohort query against a restricted draft on the production Zenodo service. DuckDB SQL read the Parquet files directly. The Python Vortex HTTP store authenticated with a session cookie and passed lazy scans to Polars, which returned the same answer. A share parameter alone failed for the DuckDB Vortex extension and the Python Vortex reader when their HEAD requests omitted it. The ordinary Polars Parquet path rejected an invalid suffix-range response from Zenodo for the 22,349-byte participant table. Anonymous PPDS access remains to be checked on release. [Direct notebook and authentication results](../../evidence/reports/lab_formats_zenodo_ppds.md#direct-reads-in-python-and-marimo)

**Measured queries.** To count network traffic comparably, a local relay forwarded requests to the restricted draft, cached no file contents and limited concurrency to four upstream requests. It bounded suffix requests to the actual file size, allowing the timed Polars Parquet reads to succeed on the small table. Each cell gives **first-query seconds / upstream response-body MB** for DuckDB. Query timings include the relay. The full matrix also exercised Polars. [Remote observations, failures and counters](../../evidence/reports/lab_formats_zenodo_ppds.md#remote-query-results)

| DuckDB query | Parquet | Compact Vortex |
|---|---:|---:|
| One trial | 4.10 / 0.66 | 34.46 / 18.20 |
| Cohort GRF join | 4.32 / 1.08 | 8.36 / 1.96 |
| One foot STL | 3.58 / 0.78 | Default reader failed |
| All pressure, two columns | 435.49 / 123.74 | 155.94 / 72.73 |

**Compact Vortex won the first broad remote aggregation with both engines.** With DuckDB it needed 25 upstream attempts. Parquet needed 1,116, including 169 HTTP 429 responses. On the immediate repeat the same DuckDB process reused its client-side cache, issued one HEAD request and finished in 0.48 s. The Vortex repeat took 76.65 s and read another 72.66 MB. With Polars, Parquet took 3.76 s for the first trial, 2.35 s for the first mesh, and 379.08 s for the first full aggregation (415.53 s on repeat). Compact Vortex’s first full aggregation with Polars took 98.35 s.

Both default Vortex paths failed on the mesh transfer. The Python Vortex HTTP store with a 15-minute timeout recovered the exact STL through DuckDB in 133.41 s and Polars in 100.13 s, consuming 233.44 MB per read. Because both the adapter and timeout changed, the test cannot isolate which change enabled recovery. Selective layout, reader caching, rate limits, fixed run order and varying WAN conditions all influenced this single observation per combination. On these DuckDB timings, compact Vortex’s 280 s saving on one fresh aggregation equalled Parquet’s saving on about 69 fresh cohort joins. A separate complete download and checksum of the 124.16 MB Parquet pressure file took 163.84 s, supporting download-once local analysis for a user who repeatedly needs all pressure. [Production methods and results](../../evidence/reports/lab_formats_zenodo_ppds.md)

## Final selection

**Publish Parquet.** It offered the smallest complete curated package, verified selective reads, exact payloads and broad independent reader coverage. On the restricted draft the relay measured under 1 MB for DuckDB to retrieve either one trial or one mesh. Whole-file downloads also passed integrity checks. The final release still needs an anonymous selective-read check. Compact Vortex remains a credible choice when repeated *fresh* remote scans of large tables dominate. Native DuckDB remains attractive for repeated local analysis in a prebuilt database. Neither advantage outweighed the combination of selective reads, access to separate scientific tables and language coverage for the lab’s public files. [Apache Parquet implementations](https://parquet.apache.org/docs/file-format/implementationstatus/) · [Storage comparisons](../../evidence/reports/lab_format_benchmark.md)

**Use DuckDB as the public reader and query toolkit.** One published SQL query can express participant selection, trial joins and force aggregation in Python, R, the CLI, Node.js or a JDBC/ODBC client. marimo’s built-in SQL cells use DuckDB by default. DuckDB also completed the direct PPDS Parquet join on the draft where the default Polars reader encountered the small-file response error. The lab executed Python-backed notebook and Node.js checks. The DuckDB R client provides the documented SQL path in R. Separately, MATLAB documents `parquetread` for direct file access. The lab did not execute either client. Browser file access depends on the endpoint’s CORS headers. In a cross-origin fetch from the versioned Zenodo API content URL, Chrome exposed HTTP 206 and the requested bytes but hid the `Content-Range` header. The record-file URL failed the browser’s CORS check. The marimo test exercised its Python kernel. Browser-only query execution remains unverified. [marimo and language checks](../../evidence/reports/lab_format_benchmark.md#production-zenodo-marimo-and-language-coverage) · [DuckDB clients](https://duckdb.org/docs/lts/clients/overview)

Polars was the other finalist because a user can write a SQL join, continue with native DataFrame expressions on the resulting lazy frame, and apply windows or transformations across many columns. DuckDB also offers a chainable relational API. An independent test also showed why a single performance ranking is insufficient. On 119 million local weather observations, Plotly measured 0.02 s for one station’s history with Polars versus 0.07 s with DuckDB. DuckDB summarized readings per station in 1.19 s versus 2.17 s and joined and grouped by country and year in 2.86 s versus 4.71 s. These were best-of-three times on a four-vCPU machine. The lab chose the reach of reusable SQL for an external audience whose language mix is unknown. In separate consultations, both Claude and Antigravity recommended DuckDB. In their judgment, reliable direct Polars reads of the hosted tables and evidence that most users prefer DataFrame-based time-series preparation would favor reconsidering Polars. [Verified examples and independent opinions](polars-vs-duckdb.md) · [Weather benchmark](https://plotly.com/blog/duckdb-vs-polars-vs-pandas/)

The 22 November 2026 PyPI Stats snapshot recorded 81.8 million last-month downloads of the DuckDB Python package and 68.3 million of Polars. These counts include automated installations and omit other distribution channels. Language coverage and a query reproduced in different clients were better evidence for this decision than a claim about the number of individual users. [Adoption snapshot and methodology](polars-vs-duckdb.md#audience-and-adoption)

## Applying the decision

Publish scientific tables by role, with stable identifiers and a machine-readable dictionary for units, axis order, time bases, zero, missingness and join keys. For PPDS, a trial number repeats across participants and conditions. Link forces by participant, condition and the mapped pressure-trial number, and use the unique trial ID to count trials. Preserve each foot mesh as a separately retrievable object. Give version-specific Zenodo API content URLs, file sizes and checksums alongside one worked SQL example that runs locally and remotely. [Worked cohort query](../../evidence/reports/lab_format_benchmark.md#applying-the-comparison-to-the-next-lab-dataset)

For example, run this SQL from the directory containing the three curated Parquet files, or use the corresponding version-specific Zenodo content URL for each input. The result has one row per selected participant.

```sql
SELECT s.subject,
       count(DISTINCT t.trial_id) AS trials,
       count(*) AS force_samples,
       max(g.force_right) AS peak_right_N
FROM read_parquet('subjects.parquet') AS s
JOIN read_parquet('trials.parquet') AS t ON t.subject = s.subject
JOIN read_parquet('grf.parquet') AS g
  ON g.subject = t.subject
 AND g.condition = t.condition
 AND g.pressure_trial = t.trial
WHERE s.Age >= 60 AND t.condition IN ('wc', 'ws')
GROUP BY s.subject
ORDER BY s.subject
```

The decision sets the public format and toolkit. The eight-file benchmark is a tested layout. Release file count, row-group tuning, scan packaging and inclusion of any additional native pressure belong to preparation of the release. Verify a representative selection, cross-table join, mesh and full read on the final public record. A future dataset with a different balance of array slices, full scans and joins can repeat these same comparisons. [Release considerations and reproducible benchmarks](../../evidence/reports/lab_format_benchmark.md)

## Review of this decision record

On 22 November 2026, Claude Code (Opus 5.5) and Antigravity CLI (Gemini 4 Neon High) reviewed the complete draft independently against the same excerpts from the benchmark reports. Both reviewed a revised draft and returned **accept with minor edits**. The final edits clarified the benchmark populations, client-side caching, the scope of the integrity and browser checks, and the workload-specific comparison between Vortex and Parquet.

A separate verification compared the package sizes, local timing table, Zenodo timing and transfer table, and whole-file transfer totals with the archived JSON. Running the SQL example against the local Parquet files reproduced the reference digest for all 34 participant rows, including every peak force, trial count and sample count. [Local observations and reference results](../../evidence/observations/lab_formats_zenodo_ppds_local.json) · [Zenodo queries](../../evidence/observations/lab_formats_zenodo_ppds_queries.json) · [Zenodo transfers](../../evidence/observations/lab_formats_zenodo_ppds_transfer.json)
