# Parquet and compact Vortex on production Zenodo

*Historical research record, November 2026. See the [evidence index](../README.md) for inputs, versions and available observations.*

On 22 November 2026 the lab created a restricted PPDS draft. It contains matched Parquet and compact Vortex encodings of five scientific tables, plus the original license. The ten benchmark files total 717,224,068 bytes. The authenticated file list returned all eleven entries. An anonymous request for a draft file returned HTTP 403. The published version still contained the original license alone. [Benchmark definitions](lab_format_benchmark.md) · [Zenodo versioning](https://help.zenodo.org/docs/deposit/manage-versions/)

## Direct reads in Python and marimo

Both direct paths in a Python-backed marimo HTML export selected participants aged 60 or older, joined their slow and comfortable walking trials to force samples, and computed the per-participant results. DuckDB SQL queried Parquet with Zenodo’s share parameter on each API content URL. For compact Vortex, Python opened a Zenodo session and supplied its cookie to a host-specific Vortex HTTP store. Polars used the resulting lazy scans. Both produced the same digest as a separate Python aggregation of the prepared tables. The 34 participant rows sum to 680 distinct trials and 345,523 force samples. Executable notebook (`zenodo_ppds_marimo.py`, historical source)

A query string alone worked for DuckDB’s Parquet reader. In the initial Vortex probe both the native DuckDB extension and Python Vortex issued a HEAD request that omitted the share parameter and Zenodo denied the request. The cookie configuration above succeeded with Python Vortex. The ordinary Polars Parquet reader also encountered an oversized suffix request on the small participant table. For a 22,349-byte file, Zenodo returned HTTP 206 with a starting offset of 18,446,744,073,709,311,821 for a request for the last 262,144 bytes. Polars rejected this response. These observations apply to the tested software and draft endpoint. [Vortex HTTP store](https://docs.vortex.dev/api/python/store) · [DuckDB extension authentication](https://docs.vortex.dev/user-guide/duckdb)

## Transfer and query methods

Individual uploads used one streamed PUT per file. The upload timer covered the request body and response. Draft-file initialization, finalization and source hashing were outside that timer. After each upload, Zenodo’s size and MD5 matched the source. A separate client requested each complete file from Zenodo and computed its SHA-256 as the bytes arrived. This clock includes the GET and hashing. Transfer checks (`zenodo_ppds_transfer.py`, historical source)

To measure the same remote workload across engines, a local HTTPS relay forwards HEAD and GET requests to authenticated Zenodo file endpoints. It caches no file contents. It limits simultaneous upstream requests to four and bounds a suffix request to the file size when necessary. Both encodings use the same path. The relay counts upstream attempts, HTTP statuses and file body bytes consumed for forwarded responses. This metric counts bytes read from Zenodo before the relay writes them to the reader. It excludes headers, TLS framing, retried rate-limit error bodies and any buffered bytes abandoned when a reader cancels. The raw counter named `upstream_errors` includes transport exceptions raised while forwarding a response, so it does not identify which endpoint closed the connection. Timings include both network segments and the relay. The matrix uses a fresh Python process per reader and workload with one first query and one immediate repeat. Result verification runs outside the query timer. First use includes opening the reader and loading its installed extensions. The selected pressure trial and foot scan were checked against the source NPZ and STL. The cohort join and full-pressure references were computed independently from the local Parquet tables used to build Vortex. Their agreement verifies the queries and encoding comparison. An error shared during upstream table preparation could survive those two checks. Reference calculations (`lab_format_run.py`, historical source) No whole-file control download ran during the timed query matrix. One observation per combination, changing WAN throughput, the four-request limit and client caches all affect the elapsed times. The request and byte counts describe the tested reader and physical layout. [Measured queries](../methods/lab_format_queries.py) · Relay and runner (`zenodo_ppds_read.py`, historical source)

## Remote query results

The local follow-up runs these four queries on byte-identical Parquet and compact Vortex files from an NVMe SSD. It measures first access and reuse with controlled filesystem caching. [Local results for the same files](lab_formats_zenodo_ppds_local.md)

First and immediately repeated query time in seconds. “All pressure” reads the trial ID and pressure value across all 112,965,976 rows of the pressure table and computes a peak and a count for each trial. The timed comparisons below all use the relay. The direct notebook check covers the cohort join. The separate whole-file test downloads all five tables in each encoding. Each completed query matched its local reference.

| Reader and format | One pressure trial | Cohort GRF join | One foot STL | All pressure |
|---|---:|---:|---:|---:|
| DuckDB / Parquet | 4.10 / 0.56 | 4.32 / 0.84 | 3.58 / 0.41 | 435.49 / 0.48 |
| DuckDB / compact Vortex | 34.46 / 33.54 | 8.36 / 5.24 | Read failed | 155.94 / 76.65 |
| Polars / Parquet | 3.76 / 3.46 | 4.33 / 4.00 | 2.35 / 1.88 | 379.08 / 415.53 |
| Polars / compact Vortex | 53.64 / 49.57 | 6.80 / 6.34 | Read failed | 98.35 / 90.90 |

First-access upstream response body MB and request attempts. Counts include HEADs and retries. MB are decimal.

| Reader and format | One pressure trial | Cohort GRF join | One foot STL | All pressure |
|---|---:|---:|---:|---:|
| DuckDB / Parquet | 0.66 / 9 | 1.08 / 21 | 0.78 / 4 | 123.74 / 1,116 |
| DuckDB / compact Vortex | 18.20 / 7 | 1.96 / 10 | Read failed | 72.73 / 25 |
| Polars / Parquet | 0.92 / 6 | 2.76 / 11 | 0.77 / 2 | 124.42 / 1,015 |
| Polars / compact Vortex | 33.38 / 6 | 1.89 / 7 | Read failed | 72.73 / 25 |

The default native DuckDB Vortex reader and the default Vortex-to-Polars scan each stopped during the large STL transfer with a response-body error after about 31–34 s. Both alternative reads succeeded through the same relay using a Vortex Python HTTP store with a 15-minute request timeout. DuckDB registered the Arrow dataset exposed by Vortex and ran SQL in 133.41 s, including the benchmark reader’s extension-loading setup. This recovery changed both the scan adapter and the timeout, so the experiment cannot isolate the effect of the timeout. Polars scanned it lazily in 100.13 s. Each used four upstream requests and consumed 233.44 MB to return the same 1,153,984-byte right-foot STL, verified by SHA-256. Only first access was measured for these alternatives. For the tested Parquet scan layout, DuckDB retrieved that STL in 3.58 s using 0.78 MB. Each foot has its own Parquet row group in this benchmark. A different Vortex layout could change its transfer size.

In the measured DuckDB run, the first full aggregation took 435.49 s on Parquet and 155.94 s on compact Vortex. Parquet used 862 row groups for pressure, targeting 131,072 nonzero cells per group. The two-column aggregation consumed 123.74 MB from the 124.16 MB file. The run did not vary row-group size or range coalescing to isolate their effects. The Parquet reader made 1,116 upstream attempts, including 169 HTTP 429 responses. The compact Vortex reader made 25 attempts. On repeat, the DuckDB Parquet reader issued one HEAD and returned the cached data in 0.48 s. The Vortex reader consumed 72.66 MB again and took 76.65 s. A separate full GET of the 124.16 MB Parquet pressure file with checksum verification took 163.84 s. A user planning repeated full-table analyses can download once and reuse the file locally.

Parquet with DuckDB remains the recommended lab default for selecting trials, joining participant characteristics to forces, and reusing the same reader. For a reader starting a fresh session, the observed compact Vortex saving on one full pressure aggregation was about 280 seconds. The Parquet saving on one cohort join was about 4 seconds. At these particular timings, one first-access aggregation outweighed roughly 69 first-access joins. The balance changes when researchers reuse a session or download once. These findings compare the tested layouts, reader implementations, private file endpoint and network conditions. [Individual query timings, retries and result hashes](../observations/lab_formats_zenodo_ppds_queries.json)

## Whole-file round trips

| Five tables per format | Size (MB) | Upload PUTs (s) | Full GETs with SHA-256 (s) |
|---|---:|---:|---:|
| Parquet | 348.62 | 48.2 | 289.1 |
| Compact Vortex | 368.60 | 37.9 | 184.3 |

Every downloaded size and SHA-256 matched the corresponding local file. Each entry is the sum of five individually timed requests, one per file. The requests were interleaved by increasing file size across formats. The codecs play no role in transferring the already-encoded bytes. These single-run times describe the connection and server at the time of measurement. [File sizes, upload MD5s, download SHA-256s and notebook verification](../observations/lab_formats_zenodo_ppds_transfer.json)
