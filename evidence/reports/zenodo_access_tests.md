# Direct Zenodo access tests — 2026-11-13

*Historical research record, November 2026. See the [evidence index](../README.md) for inputs, versions and available observations.*

The [minimum requirements](reader_benchmark.md#minimum-requirements-behind-the-search) include
Python installation, marimo compatibility, multimodal whole datasets of about 10 MB–1 GB,
Zenodo publication and selective retrieval. This follow-up tests the formats and readers in
the PPDS comparison against **existing public Zenodo files**, without uploading PPDS or new
fixtures. It separates successful selected output, reduced transfer and reader configuration.

These are feasibility and integrity tests. The files have different scientific contents,
compression and layouts; their times and transfer fractions do **not** rank format performance.
The controlled PPDS measurements remain in the [storage](storage_benchmark.md) and
[reader](reader_benchmark.md) reports. Small public fixtures below 10 MB verify protocol access,
not the target size range or the final PPDS package.

## Results

| Format / reader path | Real selected read | Transfer evidence |
| --- | --- | --- |
| Parquet / Arrow + known-size HTTPFile | Pass: both selections match checked local data | 364,240 response-body bytes in 2 range requests from a 3,330,851-byte file |
| Parquet / pandas + known-size HTTPFile | Pass: both selections match checked local data | Same 364,240 bytes and 2 range requests |
| Parquet / DuckDB HTTPFS | Pass: both selections match checked local data | First selection: 405,434 declared GET-body bytes; second: 405,387 |
| Parquet / native Polars expressions and SQL | Pass: both selections match checked local data | Four native socket checks receive 3.57–3.58 MB including TLS/HTTP overhead; no below-file-size transfer demonstrated on this fixture |
| Parquet / default pandas URL | Pass for selected values; complete download | 3,330,851 response-body bytes per selection |
| Parquet / Polars scan over an HTTP file-like object | Pass for selected values; complete download | 3,330,851 response-body bytes per selection |
| Native DuckDB / remote read-only ATTACH | Pass: catalog, schema and selected rows match checked local database | 1,585,152 declared GET-body bytes, 6 range GETs + 2 HEADs, from a 20,983,808-byte file (7.55%) |
| HDF5 / h5py + known-size HTTPFile | Pass: array slice matches checked local data | 2,768 response-body bytes, 12 range GETs, from a 2,060,096-byte file (0.134%) |
| Zarr ZIP / native ZipStore + known-size HTTPFile | Pass: array slice matches checked local data | 6,073,947 response-body bytes, 9 range GETs, from a 16,861,207-byte archive (36.02%) |
| Lance/LanceDB / raw HTTPS URIs | Rejected before network access | Six installed API paths reject the provider; this is separate from file-format validity |
| Lance / configured native S3 provider with Zenodo endpoint | Byte transport passes; complete Lance query untested | Independently matching prefix/tail reads from a real Zenodo object, without a bridge |
| SQLite / packaged GenomicSQLite web VFS | Blocked on both tested URL forms: HTTP 403 | Independent Python range control and checksum-verified local SQLite queries pass; remote-query bytes unknown |

File-payload body counts exclude HTTP/TLS overhead, record-discovery API traffic and the separate
local-reference downloads. DuckDB figures come from logged response lengths, rather than packet
capture. Native Polars socket counts use a different measurement layer and are reported separately.

## Parquet reader configurations

[Record 19115351](https://zenodo.org/records/19115351) supplies `co_min_mean.parquet`: 1,352,295
rows, three columns and 11 row groups. The complete independent reference download matches
Zenodo's MD5. Each selected result is compared with that local reference, including its values,
column order and selected-output SHA-256.

The [matrix](../observations/zenodo_parquet_matrix.json) executes **18 fresh-process accesses**:
nine reader configurations, each selecting one municipality/date (one row) and two municipalities
over ten dates (20 rows). All 18 return the expected output. Each worker has a 90-second limit.

The ordinary URL-plus-filesystem Arrow/pandas paths also return the correct data, but their
discovery includes full-file GET responses whose bodies are not explicitly consumed. The
aiohttp read callback does not count data buffered before those responses are closed. Their
364,240-byte explicit-read counter therefore does not establish total network traffic.

Opening a handle with the official record size avoids this discovery ambiguity:

```python
fs = fsspec.filesystem("http", block_size=65_536, cache_type="none")
with fs.open(url, "rb", size=record_file_size) as stream:
    table = pyarrow.parquet.read_table(stream, columns=columns, filters=filters)
```

The same handle works with `pandas.read_parquet`. Both known-size paths issue only two range
GETs and explicitly consume 364,240 bytes (10.94% of the file). The ordinary pandas URL path
downloads the complete file before filtering. Giving Polars a Python file-like object also
consumes the complete file in the tested path; it is not a substitute for its native URL scanner.

## Native Polars transport diagnostic

The supported logging probe (`zenodo_polars_transport_probe.json`, historical source) verifies both native
interfaces but does not expose a full HTTP request/body ledger. Its single 262,144-byte RTT
sample is not a total-transfer measurement. The separate
[socket diagnostic](../observations/zenodo_polars_socket_probe.json) traces fresh processes at the
unchanged Zenodo URL and counts successful TCP receive/read bytes, including TLS and HTTP
framing. It reconstructs unfinished/resumed syscalls and withholds a transfer verdict if a
receive path cannot be accounted for. A pandas full-download control checks the instrumentation.

<!-- POLARS_SOCKET_RESULTS -->

| Query form | Interface | TCP receive/read bytes, including TLS/HTTP overhead |
| --- | --- | ---: |
| Full-download control | pandas URL | 3,343,389 |
| Single-element IN | Native Polars expressions | 3,575,621 |
| Single-element IN | Polars SQL | 3,569,083 |
| Equality | Native Polars expressions | 3,576,153 |
| Equality | Polars SQL | 3,579,167 |

All five results match the independently checked reference. Parser controls, coverage checks
and independent re-parsing pass; no unresolved receive paths or `MSG_PEEK`/`MSG_TRUNC` calls
were observed. The equality follow-up rules out blaming this result solely on a single-element
IN predicate. No native Polars case demonstrates transfer below the 3,330,851-byte file size.

<!-- END_POLARS_SOCKET_RESULTS -->

These socket figures are neither HTTP payload counts nor a WAN speed benchmark. A count below
the file size can demonstrate reduced transport when receive coverage is complete; a larger
encrypted count alone does not prove every byte of the file was downloaded. Query form and
Parquet statistics must be considered before generalizing this fixture to PPDS.

## Native DuckDB

[PUDL record 24119965](https://zenodo.org/records/24119965) supplies `ferc60_xbrl.duckdb`. The
probe attaches its HTTPS URL read-only, lists 66 tables, describes nine columns and selects five
filtered/projected rows. Catalog, schema, first query and cached repeat all match a separately
downloaded, MD5-verified local database. The [captured evidence](../observations/zenodo_duckdb_probe.json)
therefore establishes actual direct Zenodo querying, rather than documentation-only support.

Attach took 5.539 s and the first selected-row query 0.991 s in this run; the cached repeat took
0.00195 s. These are descriptive observations on a different fixture, not a comparison with
Parquet. Both remote and local workers have a 60-second limit and a 256 MB engine memory limit.
This result does not remove the larger package and scan-transfer costs measured for the PPDS
native layout, or validate every DuckDB storage-version combination.

## HDF5 and Zarr ZIP

The [array results](../observations/zenodo_array_probe.json) use checksum-verified complete local
references, with reference downloads accounted separately from the selective reads. Every
selective request returned HTTP 206. Both file handles remain open until their container reader
is closed; their sizes come from Zenodo metadata.

- [HDF5 record 7646236](https://zenodo.org/records/7646236): select
  `X_train[100:104, 100:108]` from a contiguous `(702, 256)` float64 array. The output is 256 bytes.
  The Python file-object driver works; the installed h5py build has no ROS3 driver.
- [Zarr ZIP record 20559997](https://zenodo.org/records/20559997): native Zarr-Python 3.4.2
  `ZipStore(HTTPFile)` reads a **format-2** image with shape `(1, 1, 2160, 5120)` and chunks
  `(1, 1, 2160, 2560)`. Selecting an 8×8 uint16 region returns 128 bytes but reads one large
  compressed image chunk (5,996,922 bytes), plus ZIP directory/metadata. This illustrates why
  chunk layout matters. An unpacked Zenodo Zarr tree and a public format-3 ZIP remain untested.

## Lance and LanceDB

[Edge-RAG record 20807937](https://zenodo.org/records/20807937) contains a 115,822,643-byte ZIP
with actual legacy Lance tables. Bounded ZIP-range discovery and selective extraction transfer
785,753 declared GET-response bytes over ten range GETs plus one HEAD. PyLance and LanceDB
agree on selected locally extracted data. This is an archive/extraction control, not direct
Lance querying inside the ZIP. The DuckDB extension requires more fragments for the original
partially extracted table; a separately rewritten one-row control succeeds.

The [probe](../observations/zenodo_lance_probe.json) distinguishes these results:

- Six raw HTTPS API paths reject the scheme before network access, including the standalone
  file reader. `strace` records no INET connects for those attempts.
- Native Lance object access **does** work with an anonymous path-style S3 endpoint pointed
  at `https://zenodo.org`. Prefix/tail bytes match an independent HTTPS read. This is a client
  configuration, without an S3 mirror or custom service.
- File-like handles, PyArrow filesystem arguments and fsspec ZIP-chain URIs are not accepted
  by the tested native APIs. The archive's legacy fragments are also distinct from a current
  standalone Lance file; the probe includes a generated local positive control.
- No suitable unpacked public Lance file/table was found in the bounded search. Complete
  querying through the S3 endpoint configuration is **not tested**, rather than proven
  impossible. A final publication would still need validated object-path, manifest and fixed
  snapshot discovery. Reading ZIP magic alone does not establish that contract.

## Marimo integration

The smoke notebook (`zenodo_marimo_smoke.py`, historical source) executes fresh remote reads inside
marimo **0.25.2** through Arrow, pandas, native Polars expressions, Polars SQL, native DuckDB,
HDF5 and Zarr ZIP. All seven match existing checked references without repeating full reference
downloads. Headless HTML export exits zero with no stderr in 30.994 s under a 240-second limit.
The [proof](../observations/zenodo_marimo_smoke.json) records a unique run ID, fresh timestamps and
the HTML checksum. This covers cell evaluation and static export; browser interaction and
reactive reruns are not tested here. Lance's unvalidated direct-query path is not assigned a
marimo success verdict.

## SQLite baseline

SQLite was mentioned among the initial possibilities, so this follow-up also checks a packaged
Python HTTP VFS rather than assuming all database formats share Lance or DuckDB's behavior.
It does not add vector-similarity workloads or benchmark the sqlite-vec extension.

[Record 13328867](https://zenodo.org/records/13328867) supplies `RM009_axons_2.db`, a
1,888,256-byte SQLite file. Its complete download matches Zenodo's MD5; local catalog and
three-row queries pass. GenomicSQLite **0.10.0**, including its packaged native web VFS,
installs in a separate Python environment, while stdlib SQLite alone has no registered `web` VFS.

The [actual probe](../observations/zenodo_sqlite_probe.json) receives **HTTP 403** through that VFS
on both API-content and canonical download URLs. A separate Python request to the same source
returns 206 and 100 correct prefix bytes. Thus this tested adapter/endpoint combination is
blocked, while the bytes are accessible and the database is valid. Remote transfer totals are
unknown. This is not a proof that SQLite cannot work through another HTTP VFS or client
configuration. A custom VFS, full database download, and sqlite-vec queries were not substituted
for the failed direct path. No marimo success is claimed for this blocked reader.
