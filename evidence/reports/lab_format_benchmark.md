# Storage and query readers for public laboratory datasets

*Historical research record, November 2026. See the [evidence index](../README.md) for inputs, versions and available observations.*

**PPDS benchmark, 21 November 2026.** For a lab adopting one public format and one primary query toolkit, we recommend **Parquet with DuckDB SQL**. The same SQL joins participant, trial and measurement files in Python and in a marimo notebook. Polars also reads the published Parquet files directly. Native DuckDB is a practical single-file alternative. The production Zenodo tests demonstrated selective reads on public Parquet and DuckDB fixtures. The initial PPDS timing comparisons used local files and loopback HTTPS. Production measurements on a restricted PPDS draft are reported separately. [Zenodo PPDS measurements](lab_formats_zenodo_ppds.md) [Independent recommendations and review](lab_formats_peer_review.md)

The [consolidated format and toolkit decision](../../case-studies/ppds/selection-record.md) traces the initial candidates through the selection of Parquet and DuckDB. The [Polars and DuckDB comparison](../../case-studies/ppds/polars-vs-duckdb.md) covers Python query styles, cross-language reach, marimo and independent timings on weather data.

## What was compared

The inputs came from the current curated PPDS sources. All configurations represented the same eight tables, in the same row order. We checked every value against the reference encoding, including nulls, pressure coordinates and all 190 original STL byte strings. The numerical comparison converts returned types to the reference schema. The Parquet schemas held nine table or field annotations across six files. The native DuckDB result schemas and both Vortex dtype schemas exposed zero of those annotations in these conversions. A separate data dictionary can carry units, axis order, file roles and join semantics through every reader. [Build results](../observations/lab_formats_build.json) · [Compact Vortex results](../observations/lab_formats_compact.json) · [Schema audit](../observations/lab_formats_schemas.json) · PPDS axes (`pressure_axes.md`, historical source)

| Published content represented in the test | Rows |
|---|---:|
| Participants (`subjects.parquet`) | 95 |
| Trials | 3,312 (3,217 gait, 95 stance) |
| Pressure | 112,965,976 nonzero sensor observations |
| GRF waveforms | 1,503,305 samples |
| GRF cycle averages | 64,400 samples |
| Spatiotemporal reports | 322 |
| Registered footprint values | 4,219,239 |
| Foot scans | 190 STL payloads, keyed by participant and side |

The pressure grid was 353 × 64. Each trial records frame count and sampling frequency. Gait is 100 Hz. The stance selection is the last 100 frames at 10 Hz. Within a recorded frame an omitted sensor cell means zero. Frame, y and x are zero-based indices and the pressure unit is kPa. The measured package uses cleaned pressure. Adding complete native recordings would change the sizes. Embedding one byte string per foot allowed the same single-mesh test in all three formats and preserved the two separate scans. Fixture builder (`lab_format_fixture.py`, historical source) · Dataset coverage (`README.md`, historical source)

| Encoding | Files | Eight tables, MB | Tables excluding STL, MB | Pressure alone, MB |
|---|---:|---:|---:|---:|
| Parquet | 8 | 389.94 | 171.98 | 124.16 |
| Native DuckDB | 1 | 599.01 | — | — |
| Vortex, default | 8 | 782.81 | 290.89 | 245.60 |
| Vortex, compact | 8 | 400.89 | 167.52 | 131.59 |

MB means 1,000,000 bytes. The native database shares allocated blocks across its tables, so the comparison uses its whole-file size. Pressure and STL Parquet use Zstandard level 9. The pressure file is sorted by participant, condition, trial, frame, y and x, with 131,072 nonzero cells per row group. The scan file has one row group per foot. The release builders supply the other scientific tables. Vortex received streamed batches of up to 65,536 rows with its default and compact write strategies. DuckDB ingested the same Parquet tables with its native compression and no added indexes. Codec and layout choices affect these sizes. Compact Vortex used fewer bytes than Parquet for GRF and registered footprints. Excluding scans it was the smallest of the two comparable multi-file packages. [Encoding code](../methods/lab_format_build.py)

Each complete package was also downloaded twice over loopback HTTPS. Every file matched its local SHA-256. Median time to receive and checksum all files was 0.99 s for Parquet, 1.49 s for native DuckDB, 1.96 s for default Vortex and 1.00 s for compact Vortex. These are whole-package controls on one machine. Internet download times depend on the connection. [Complete downloads and per-file checksums](../observations/lab_formats_downloads.json)

## Workloads

1. **One pressure trial.** Resolve participant `s053`, slow walking, trial 4 through the trial table. Fetch all 138,035 loaded sensor cells from its 840 frames. Check coordinates and values against the source NPZ.
2. **Participant selection and force join.** Select participants aged 60 or older, their slow and comfortable walking trials, and the corresponding force samples. Compute the peak right-foot vertical GRF in N, number of matched samples and number of distinct trials per participant. The answer covers **34 participants, 680 trials and 345,523 force samples**. The trial number (`trials.trial`) is scoped to a participant and condition. Each force sample links to it through `grf.pressure_trial` and those same two keys. The distinct-trial count uses `trials.trial_id`, which is unique across the fixture.
3. **All pressure.** Scan the trial and value columns across gait and stance. Return peak pressure and nonzero-cell count for each of the 3,312 trials. This measures whole-table analytical access. Complete eight-table value verification was performed separately during encoding.
4. **One foot scan.** Retrieve the right foot of `s053` as a materialized 1,153,984-byte STL and compare its SHA-256 with the independent source file.

The two aggregate reference answers were computed with a streamed NumPy reduction and a Python keyed accumulation over the reference inputs. Each worker checked that its first and repeated query returned the same result, then compared that result with the reference. The local, loopback HTTPS and supplemental pandas matrices ran 96, 72 and 24 workers respectively. Together they verified 384 query executions across four workloads. pandas received column projections and supported predicates. For the join, the pandas implementation explicitly passed the selected participant IDs into the reads of both trials and GRF before merging. Its 88 ms applies to that implementation. DuckDB and Polars optimized their SQL and lazy expressions respectively. The remote matrix includes both the ordinary pandas URL interface and an explicit seekable fsspec handle given the file size. PyArrow is an implementation dependency for pandas' Parquet reader, fixture generation and interchange during verification. The compared user-facing APIs are DuckDB, Polars and pandas. [Exact queries](../methods/lab_format_queries.py) · Reference and timing code (`lab_format_run.py`, historical source)

## Local performance

A follow-up measured the exact files used on Zenodo with their Linux file pages verified as either resident in memory or evicted before each fresh reader. [Controlled local comparison](lab_formats_zenodo_ppds_local.md)

Each cell gives **first / immediately repeated query** in milliseconds, as medians of three fresh Python processes. First includes reader construction, extension loading and database attachment where relevant. Package imports, correctness hashing and process launch are outside the timer. The second run uses the same reader after the first result was checked. Filesystem caches were left in their normal state. Process peak RSS includes imported libraries and result verification. An uncached disk or a different machine can produce different results. [Local observations](../observations/lab_formats_local.json)

| Reader and storage | One trial | Cohort force join | All pressure | One STL | Peak RSS, all pressure |
|---|---:|---:|---:|---:|---:|
| DuckDB / Parquet | 53 / 29 | 38 / 18 | 245 / 222 | 28 / 7 | 249 MiB |
| Polars / Parquet | 9 / 5 | 28 / 19 | 305 / 299 | 9 / 3 | 237 MiB |
| pandas / Parquet | 33 / 28 | 88 / 80 | 1,000 / 986 | 9 / 6 | 2,455 MiB |
| DuckDB / native DuckDB | 28 / 4 | 36 / 11 | 152 / 73 | 790 / 648 | 458 MiB |
| DuckDB / Vortex | 126 / 30 | 95 / 14 | 216 / 117 | 318 / 223 | 274 MiB |
| Polars / Vortex | 59 / 51 | 28 / 21 | 332 / 306 | 206 / 188 | 405 MiB |
| DuckDB / compact Vortex | 107 / 28 | 112 / 27 | 336 / 242 | 806 / 718 | 281 MiB |
| Polars / compact Vortex | 68 / 56 | 35 / 30 | 381 / 379 | 730 / 702 | 398 MiB |

On Parquet, ordinary pandas took 88 ms for the cohort join, compared with 28 ms for Polars and 38 ms for DuckDB. For the pressure aggregation pandas took 1.00 s and peaked at 2,455 MiB, versus 245 ms and 249 MiB for DuckDB. For one local foot scan pandas and Polars both took about 9 ms. These results support keeping pandas as a consumer while using a different default for cohort analyses and whole-table work. A second, paired pandas test compared its default dtypes with `dtype_backend="pyarrow"`. The force join took 86 versus 89 ms. Full pressure took 986 versus 1,760 ms and peaked at 2,454 versus 3,214 MiB. The alternate dtypes did not improve either of these larger tasks. [pandas dtype measurements](../observations/lab_formats_pandas_dtypes.json)

Native DuckDB was the fastest tested local pressure aggregation at 152 ms. DuckDB scanning default Vortex took 216 ms, ahead of its 245 ms Parquet scan. Polars selected a trial from Parquet in 9 ms. With a warm connection, DuckDB over Parquet reduced the cohort join to 18 ms. Reader choice, setup and workload all affect the timing.

### Querying Vortex files from a notebook

All three examples select the same 138,035 pressure cells for trial ID 1835 (participant s053, slow walking, trial 4). Run them in the fixture’s Vortex directory. Each result matched the reference derived from the original trial NPZ.

```python
import polars as pl
import vortex as vx
from vortex import expr as ve

columns = ["frame", "y", "x", "value"]
pressure = vx.open("pressure.vortex")

# Native scan. The stored trial_id is an unsigned 16-bit integer.
trial = pressure.scan(columns, expr=ve.column("trial_id") == ve.literal(vx.uint(16), 1835))

# The Polars adapter returns a LazyFrame. collect() executes the selection.
trial_frame = pressure.to_polars().filter(pl.col("trial_id") == 1835).select(columns).collect()
```

The native scan returns an iterator. In vortex-data 0.93.0 the plain Python integer in the native comparison produced a type mismatch, so this example uses a typed literal. Polars accepted the plain integer. Its optimized plan placed the predicate at the file scan. Vortex documents its Polars integration as experimental and supports pushdown for a subset of expressions. [Vortex scan API](https://docs.vortex.dev/api/python/io) · [Vortex Polars guide](https://docs.vortex.dev/user-guide/polars)

```sql
LOAD vortex;
SELECT frame, y, x, value
FROM read_vortex('pressure.vortex')
WHERE trial_id = 1835;
```

The DuckDB example uses the installed Vortex extension. SQL joins can scan each file in place. Both DuckDB and Polars reproduced all 34 participant-level results for the cohort join on both Vortex layouts. First and repeat timings above include the query and delivery of the result. DuckDB’s first-query timing also includes loading its installed extension. [DuckDB Vortex guide](https://docs.vortex.dev/user-guide/duckdb) · [Complete SQL and Polars joins](../methods/lab_format_queries.py)

## Remote access to the same PPDS data

Here the same files were served from a counted loopback **HTTPS** endpoint. Each cell gives **MB of response bodies written / number of file requests** for the first access, using the midpoint of two independent fresh-reader runs. Counts include HEAD requests and ranged or whole GETs. Request counts ending in .5 reflect variation between the two runs. The server excludes counter lookups, HTTP headers and TLS overhead. It can count bytes accepted by the socket before a client cancels. The JSON also records elapsed times, repeated-query traffic and range-request counts. Loopback latency differs from an actual Zenodo download. [Controlled HTTPS observations](../observations/lab_formats_https.json)

| Reader and storage | One trial | Cohort force join | All pressure | One STL |
|---|---:|---:|---:|---:|
| DuckDB / Parquet | 1.30 / 12 | 1.06 / 27 | 124.05 / 883 | 1.03 / 5 |
| Polars / Parquet | 0.92 / 6 | 2.76 / 11 | 124.42 / 864 | 0.77 / 2 |
| pandas / Parquet | 124.19 / 2 | 6.51 / 3 | 124.16 / 1 | 217.95 / 1 |
| pandas / Parquet, seekable HTTP | 0.73 / 5 | 0.69 / 15 | 82.44 / 865 | 0.57 / 2 |
| DuckDB / native DuckDB | 3.94 / 13 | 17.84 / 52 | 448.41 / 1712.5 | 234.89 / 898 |
| DuckDB / Vortex | 18.87 / 8 | 3.04 / 11 | 90.17 / 38 | 491.98 / 6 |
| Polars / Vortex | 27.53 / 6.5 | 2.97 / 7 | 90.17 / 38 | 491.98 / 4 |
| DuckDB / compact Vortex | 18.20 / 7 | 1.96 / 10 | 72.73 / 25 | 233.44 / 6 |
| Polars / compact Vortex | 25.82 / 6 | 1.89 / 7 | 72.73 / 25 | 233.44 / 4 |

The two first-query timings per configuration are exploratory. For the cohort query, the server wrote 1.06 MB in response to 27 DuckDB requests and 2.76 MB in response to 11 Polars requests over the same Parquet files. For one foot, the server wrote 1.03 MB for SQL over Parquet, 234.89 MB for native DuckDB, and 491.98 MB for default Vortex. For a single trial through DuckDB, the server wrote 18.20 MB with compact Vortex and 1.30 MB with Parquet. For one foot, it wrote 233.44 MB and 1.03 MB respectively. These differences apply to the tested layouts.

For the full pressure aggregation, compact Vortex reduced the server’s response bodies to **72.73 MB in 25 requests** with either reader. DuckDB over Parquet used **124.05 MB in 883 requests**. The elapsed-time result depended on the reader. With DuckDB, the median first query took 449 ms on compact Vortex and 315 ms on Parquet. With Polars, it took 370 ms on compact Vortex and 415 ms on Parquet. Compact Vortex merits testing when bandwidth or request count limits a workload. For repeated analyses, downloading the 124.16 MB Parquet pressure file once also permits local reuse. [First-query timings and server counts](../observations/lab_formats_https.json)

## Production Zenodo, marimo and language coverage

Zenodo hosts versioned files. The reader runs the SQL or DataFrame expression on the user's machine or notebook server and can request portions of the files. The examples below used public, version-specific Zenodo content URLs. They exercise transport and integrity on unrelated public fixtures. PPDS timings and package sizes above use the private, curated benchmark inputs. [Zenodo records and file preservation](https://help.zenodo.org/docs/deposit/about-records/) · [DuckDB HTTP range reading](https://duckdb.org/docs/2.0/core_extensions/httpfs/https)

| Path exercised | Result |
|---|---|
| DuckDB SQL over Zenodo Parquet | Both the one-row and 20-row projections matched the checked reference. For one row, DuckDB logged 323,344 declared GET-body bytes from a 3,330,851-byte file. |
| Polars over Zenodo Parquet | Both result hashes matched. Native Polars received 3.58 MB of TCP/TLS data for the one-row query. The trace did not demonstrate a saving on this fixture and cannot isolate HTTP body bytes. |
| pandas over Zenodo Parquet | Both selections matched. For either selection the direct URL delivered the entire 3,330,851 bytes. The known-size seekable reader received 364,240 bytes across two HTTP 206 responses. |
| Native DuckDB on Zenodo | Read-only HTTPS attachment and a five-row selection matched the downloaded reference. DuckDB reported 1,585,152 GET-body bytes from a 20,983,808-byte database. |
| Vortex over public HTTPS | DuckDB and the Vortex-to-Polars scan each selected three IDs, including a null, from the same pinned public GitHub fixture and matched a whole-file checksum-verified local reference. This 24,500-byte fixture establishes HTTPS compatibility. Zenodo and Vortex support the required protocols. A native Vortex transport check on Zenodo is described below. A subsequent Python-backed marimo run queried actual PPDS Vortex files on a restricted production Zenodo draft. [PPDS draft results](lab_formats_zenodo_ppds.md) |
| marimo | A headless HTML export reproduced the PPDS cohort join with all eight local reader/encoding combinations and with marimo’s built-in `mo.sql` on Parquet. The notebook also made nine fresh queries against Zenodo and two against the GitHub Vortex fixture. Browser-only WebAssembly and interactive widgets fall outside this test. |
| JavaScript | Node.js 22 with the DuckDB Neo client reproduced the complete participant-level force result for all three local formats and the single-row Zenodo Parquet result. |

The WAN observations use separate source datasets and different transfer instruments. DuckDB reports declared HTTP response sizes, pandas counters observe delivered body bytes, and the additional native Polars probe traces TCP receives including TLS. Each is compared with the same object's file size. [Hosted Python results](../observations/lab_formats_hosted.json) · [Polars socket probe](../observations/lab_formats_zenodo_socket.json) · [marimo results](../observations/lab_formats_marimo.json) · [Node.js results](../observations/lab_formats_node.json) · [Zenodo Parquet record](https://zenodo.org/records/19115351) · [Zenodo DuckDB record](https://zenodo.org/records/24119965)

### Can Vortex query a standalone file on Zenodo?

**Yes.** A cohort query over three compact Vortex files on a restricted PPDS draft matched the independent reference. The Python Vortex HTTP store authenticated with the Zenodo session cookie, then passed its lazy scans to Polars. Direct marimo query (`zenodo_ppds_marimo.py`, historical source) Zenodo accepts arbitrary file formats. Its documented default record quota is 50 GB in total across up to 100 files. Vortex can open a generic HTTPS URL, inspect the footer and use the file layout to select segments for a query. How much it reads depends on the file layout, the columns and the predicate. [Zenodo file policy](https://help.zenodo.org/docs/deposit/about-records/) · [Zenodo quotas and rate limits](https://developers.zenodo.org/) · [Vortex file layout](https://docs.vortex.dev/concepts/file-format) · [Vortex HTTP store](https://docs.vortex.dev/api/python/store)

We checked the transport separately on production Zenodo using the known 3,330,851-byte Parquet fixture. Anonymous GETs to the versioned record-file URL and its API content URL both returned exactly the requested final eight bytes with HTTP 206 and no redirect. When pointed at the API content URL, Python’s `vortex.open` reached the footer and rejected its `PAR1` signature as expected. The reader process received **73,074 TCP bytes including protocol overhead**, well below the object size. This establishes partial access by Vortex’s own transport on Zenodo. A successful row selection additionally requires a valid Vortex object. Protocol and browser results (`lab_formats_zenodo_vortex_transport.json`, historical source) · Reproducible probe (`zenodo_vortex_transport.py`, historical source)

For browser applications, the URL mattered. In a cross-origin JavaScript fetch, Chrome read the eight bytes from the API content URL. JavaScript could see the 206 status and the body, while the browser hid the `Content-Range` header. The equivalent record-file response lacked `Access-Control-Allow-Origin`, and the browser fetch failed. This tested browser fetch only. In the marimo configuration used here, the Python kernel fetches the data. For public programmatic reads, prefer the versioned API content URL and respect Zenodo’s rate-limit headers. Authenticated clients also have limits. Observed response headers (`lab_formats_zenodo_vortex_transport.json`, historical source) · [Zenodo rate-limit documentation](https://developers.zenodo.org/#rate-limiting)

For Vortex, the Zenodo catalogue searches for `"vortex.dev"`, `"vortex-data/vortex"`, `"Vortex file format"` and Vortex with columnar-storage terms did not identify a usable standalone fixture. Searches by extension also missed a known DuckDB positive control. The lab subsequently uploaded a restricted PPDS draft with matched Vortex and Parquet files to test production hosting. The hosted probe accepts a content URL for a mirror of the pinned test file. Vortex's own benchmarks distinguish default and compact encoding and test dedicated Graviton instances with local NVMe and same-region S3. Its SQL suites and PPDS exercise different data, hardware and transport. Zenodo catalogue search results (`lab_formats_vortex_discovery.json`, historical source) · [Pinned Vortex fixture](https://github.com/dfa1/vortex-java/blob/439d22c44a21d608646a7f65dffb3a2ed27bb0b3/reader/src/test/resources/fixtures/chunked.vortex) · [Vortex benchmark methodology](https://bench.vortex.dev/methodology) · [Vortex DuckDB integration](https://docs.vortex.dev/user-guide/duckdb)

The production PPDS test used five tables (`subjects`, `trials`, `grf`, `pressure`, `scans`) in Parquet and compact Vortex. The ten files total 717.22 MB. The draft remains restricted, so anonymous access to a public PPDS release is a separate check. [Production measurements and reproducible commands](lab_formats_zenodo_ppds.md)

Parquet also has documented independent implementations in Java, C++, Rust, Go and JavaScript. MATLAB supplies `parquetread`. R users can use DuckDB SQL or Arrow. Vortex documents bindings in Rust, Python, C++ and Java, plus integrations with DuckDB and Polars. We executed Python and JavaScript (Node.js), including a notebook integration test in marimo’s Python kernel. Coverage for R and MATLAB is based on their documentation. [Apache Parquet implementation matrix](https://parquet.apache.org/docs/file-format/implementationstatus/) · [MATLAB reader](https://www.mathworks.com/help/matlab/ref/parquetread.html) · [DuckDB R client](https://duckdb.org/docs/2.0/clients/r) · [Vortex language and engine guides](https://docs.vortex.dev/user-guide/duckdb) · [marimo SQL](https://docs.marimo.io/guides/working_with_data/sql/)

## Applying the comparison to the next lab dataset

- Publish queryable tables separately by scientific role, with stable keys for participant, trial/condition and measurements. Keep each participant's repeated trials distinguishable. Supply a machine-readable dictionary for keys, units, time base, axes, missingness, zero and any transformations. For PPDS the pressure representation reconstructs `(frame, y, x)` using the recorded trial length.
- Keep common selection keys as typed scalar columns. Sort or cluster large measurements on the keys readers use, then benchmark candidate row-group sizes with a real selection. Whole-file downloads remain available to users who want an offline copy.
- Document version-specific file URLs, sizes and checksums. Show one worked participant selection with the corresponding trial/force join in SQL and a DataFrame example for notebook users. Provide original-format binary assets, such as individual left and right foot scans, for applications that consume them.
- On a new dataset, repeat at least a common selection, a cross-table scientific join and a full aggregation. Include a large binary selection when the dataset has one. Verify against an independent answer, then measure first access, reuse and bytes transferred. Repeat a representative query against the deposited files before advertising remote selectivity.

The following query runs from the fixture’s Parquet directory. For hosted files, replace each filename with its version-specific Zenodo content URL. The same expression runs through DuckDB’s Python client or marimo’s SQL interface. The notebook also exercises the equivalent lazy Polars joins. Executable notebook (`lab_format_marimo.py`, historical source) · [Polars implementation](../methods/lab_format_queries.py)

```sql
SELECT s.subject, count(*) AS samples, max(g.force_right) AS peak_right_N,
       count(DISTINCT t.trial_id) AS trials
FROM read_parquet('subjects.parquet') AS s
JOIN read_parquet('trials.parquet') AS t ON t.subject = s.subject
JOIN read_parquet('grf.parquet') AS g
  ON g.subject = t.subject AND g.condition = t.condition AND g.pressure_trial = t.trial
WHERE s.Age >= 60 AND t.condition IN ('wc', 'ws')
GROUP BY s.subject
ORDER BY s.subject
```
