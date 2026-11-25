# PPDS storage, reader support and hosting assessment

*Historical research record, November 2026. See the [evidence index](../README.md) for inputs, versions and available observations.*

Reviewed **2026-11-13**. This assessment accompanies the exploratory
[storage benchmark](storage_benchmark.md) and its [priorities and discussion](storage_format_discussion.md).
It separates documented capabilities, saved PPDS measurements and a small live hosting check.
It does not choose or migrate the publication format. No PPDS data were uploaded.

The user's acceptance requirements are now explicit: an **installable Python solution compatible
with the existing marimo notebooks** for the
**whole multimodal dataset, roughly 10 MB–1 GB**, publishable on **Zenodo**, with direct partial
reads from the published files for subjects/subsets, trials and conditions. A package that works
only after downloading/extracting everything does not meet that partial-read requirement. Whole
dataset scope includes primary pressure, standing and original scan bytes, associated tables and
their scientific metadata; a pressure-only array benchmark is insufficient. A local S3 simulation
is supplementary evidence and cannot pass the Zenodo delivery requirement.
The [opening requirements record](reader_benchmark.md#minimum-requirements-behind-the-search)
includes this existing notebook framework constraint; the standalone reader probes do not by
themselves verify a replacement reader's complete marimo integration.

The practical distinction is between **an archive that users can download and open offline** and
**a layout that readers can query selectively at its published URLs**. All candidates can be
archived as files. Direct selective Zenodo access requires a working reader, addressable metadata
and payloads, and suitable server responses; fitting within the upload quota is insufficient.
**Unknown below means untested or undocumented in the reviewed material, not unsupported.**

## Format, reader and service are separate decisions

- **Parquet** is an open columnar file format. **Arrow** specifies an in-memory representation and
  interchange/serialization protocols; **PyArrow** supplies readers and writers. **DuckDB, Polars
  and pandas** are alternative query or DataFrame engines that can read the same Parquet files.
  Comparing these readers does not introduce three additional storage formats.
  [Parquet overview](https://parquet.apache.org/docs/overview/),
  [Arrow format specification](https://arrow.apache.org/docs/format/Columnar.html).
- **Native DuckDB** is the engine's persistent database format. One closed, checkpointed database
  can contain independent logical tables. It is a different publication product from Parquet
  queried by DuckDB. [Storage format](https://duckdb.org/docs/2.0/internals/storage),
  [checkpointing](https://duckdb.org/docs/2.0/sql/statements/checkpoint).
- **Lance** has a columnar **file** format and a versioned **table** format. A `.lance` table path
  normally denotes a directory/tree of objects, not one physical file. **LanceDB Embedded** adds
  database/table management and query APIs over Lance and executes inside the user's process.
  [Lance specification](https://lance.org/format/file/),
  [table format](https://lance.org/format/table/),
  [Embedded architecture](https://docs.lancedb.com/oss/v0-41-0/basics/lancedb-embedded).
- **HDF5** stores typed datasets and hierarchy; **h5py** is a reader/writer binding.
  **Zarr** describes chunked array storage; **Zarr-Python** supplies stores/readers. **ZIP** is the
  packaging layer around the benchmark's Zarr hierarchy.
  [h5py datasets](https://docs.h5py.org/en/stable/high/dataset.html),
  [Zarr storage guide](https://zarr.readthedocs.io/en/stable/user-guide/storage/).

The local engines/libraries in this comparison require no managed database account for local
reads. LanceDB Embedded is explicitly free and open source; its local process performs queries,
index building and maintenance. Enterprise is a separate commercial deployment/service, and its
distributed execution, operational services and support must not be credited to Embedded results.
[Embedded](https://docs.lancedb.com/oss/v0-41-0/basics/lancedb-embedded),
[Enterprise](https://docs.lancedb.com/enterprise).

Likewise, local open-source Polars is distinct from the commercial distributed platform, now named
**Polars Nanook** (formerly Polars Cloud). That platform has free and paid plans; none is required
for the local Parquet benchmark. Platform features and paid support are not evidence about a
static Zenodo file's availability. [Current product/pricing distinction](https://pola.rs/pricing/).

## Capability and publication matrix

“Selective” means a reader can avoid fetching some stored data; it does not promise one request,
minimal transfer, index use, or fast PPDS execution. The benchmark reports those empirical costs.

| Physical product / reader | Local and offline use | Plain HTTP(S) selective access | Layout and discovery needed for a static release |
| --- | --- | --- | --- |
| Parquet / PyArrow | Local file/dataset and explicit row-group or filtered reads | Via a suitable seekable HTTP file or fsspec integration; HTTP is absent from PyArrow's native filesystem list | Named files or an explicit file list; row-group metadata in file footers. Hive-style directory partitioning needs paths preserved. A publication manifest can remove reliance on directory crawling. [Filesystems](https://arrow.apache.org/docs/python/filesystems.html), [Parquet reads](https://arrow.apache.org/docs/python/generated/pyarrow.parquet.read_table.html), [datasets](https://arrow.apache.org/docs/python/dataset.html) |
| Same Parquet / DuckDB | Embedded SQL over local files | Documented `httpfs` range reads and read-only access | Named URL or explicit URL list. Column selection and statistics can reduce reads; SQL filters alone do not prove reduced transfer. [HTTP support](https://duckdb.org/docs/2.0/core_extensions/httpfs/https) |
| Same Parquet / Polars | Local eager reads or lazy scans | Native HTTP scanning exists; endpoint-specific transfer and pushdown must be measured with the pinned runtime | Explicit URLs avoid assuming a generic HTTP directory-listing/glob service. Lazy `scan_parquet` documents projection/predicate pushdown; a collected result still has a concrete output size. [Current scan API](https://docs.pola.rs/api/python/stable/reference/api/polars.scan_parquet.html), [project HTTP implementation history](https://github.com/pola-rs/polars/pull/12517) |
| Same Parquet / pandas + PyArrow | Local selected columns/filters returning a DataFrame | The ordinary URL path and an explicit range filesystem are different configurations | `read_parquet` accepts URLs and an explicit filesystem. In pandas 3.1.1 the ordinary HTTP URL handler reads the response into `BytesIO`, so a selective Parquet filter does not make that path a selective network reader. A range-capable filesystem must be configured and measured separately. [API](https://pandas.pydata.org/docs/reference/api/pandas.read_parquet.html), [versioned URL-handler source](https://github.com/pandas-dev/pandas/blob/v3.1.1/pandas/io/common.py#L398-L424) |
| Native DuckDB / DuckDB | Local read-only database; no server needed | Documented read-only remote `ATTACH` using ranges | One database file after checkpoint/close; internal catalog locates tables. Declare the minimum storage reader version. A range read can still fetch large column segments, as the saved PPDS scan-BLOB experiment demonstrates. [Remote attach](https://duckdb.org/docs/2.0/core_extensions/httpfs/https), [format versions](https://duckdb.org/docs/2.0/internals/storage), [PPDS evidence](storage_benchmark.md) |
| Lance table / Lance or LanceDB Embedded | Copy the complete referenced tree; open locally with pinned clients | The tested released readers reject generic `http://` and `https://` schemes before making requests; see the release-specific observation below | Preserve manifests, data, required deletion/index/blob objects and relative paths. Pin the snapshot. Local/S3/Azure/GCS/Hugging Face support is not generic HTTPS-record support. [Object-store configuration](https://lance.org/guide/object_store/), [supported-storage list](https://github.com/lance-format/lance#supported-storage), [layout](https://lance.org/format/table/layout/) |
| HDF5 / h5py | Typed multidimensional datasets, chunked selections, attributes | Seekable Python file objects can provide remote IO; `ros3` is another read-only S3-oriented driver | One file for the tested layout. h5py's PyPI wheels omit `ros3`; the benchmark's file-object adapter must be distinguished from that driver. File objects must remain open through HDF5 access. [File drivers/lifetimes](https://docs.h5py.org/en/stable/high/file.html) |
| Zarr v3 ZIP / Zarr-Python | One ZIP containing metadata and chunk keys | `ZipStore` accepts an open binary object, including a remote reader; HTTP range behavior belongs to that reader | Keep internal member names and the ZIP directory intact. Do not treat a ZIP URL as an object-store directory URL. The ZIP store specification is currently draft. [ZipStore documentation](https://zarr.readthedocs.io/en/stable/user-guide/storage/#zip-store) |

For a native Zarr directory/object-store layout, metadata and chunks are separate keys; remote
`FsspecStore` uses an asynchronous filesystem. Consolidated metadata reduces discovery requests,
but Zarr-Python currently marks consolidation for v3 stores experimental. This differs from
putting the hierarchy in one ZIP, where ZIP member lookup supplies another metadata layer.
[Remote store](https://zarr.readthedocs.io/en/stable/user-guide/storage/#remote-store),
[v3 consolidated metadata status](https://zarr.readthedocs.io/en/stable/user-guide/consolidated_metadata/).

Lance's latest-version lookup also deserves a separate test. Its optional
`_versions/latest_version_hint.json` can reduce listing, but readers may fall back to listing when
the hint is missing/stale. A fixed snapshot avoids a moving “latest” target; it does not by itself
supply an HTTP backend or translate object paths to Zenodo URLs. ZIP-and-download is an archive
fallback, not evidence of selective reads inside that archive by an unmodified Lance reader.
[Lance layout and version discovery](https://lance.org/format/table/layout/).

The follow-up smoke checks observed a narrower, concrete limitation: **pylance 14.0.2,
LanceDB Embedded 0.41.0 and the tested DuckDB Lance extension reject generic HTTP/HTTPS URIs**
with “No object store provider found for scheme” before network access. A pinned snapshot and
`allow_http=true` did not change that result; this failed before directory listing or Zenodo path
mapping could be evaluated. Polars' native HTTP path and pandas with an explicit fsspec range
filesystem succeeded against the same localhost server. This is evidence about those released
reader/backend paths, not a universal incompatibility of Lance bytes with HTTP hosting. A later
[real Zenodo probe](zenodo_access_tests.md#lance-and-lancedb) also found that an anonymous native
S3 endpoint configuration reads Zenodo byte ranges without a custom bridge. It does not yet
validate complete Lance file/table queries through that configuration. The synthetic S3 backend
check below succeeds, demonstrating that this is not a rejection of all remote storage. See the follow-up reader benchmark's
saved error diagnostics for the exact extension/backend identifiers and messages.

## Zenodo: verified limits and remaining delivery questions

### Current status against the direct partial-read requirement

| Candidate path | Observed status | Remaining acceptance gate |
| --- | --- | --- |
| Parquet / PyArrow + fsspec | **Pass with a known-size HTTPFile:** range-only requests and results matching a checksum-verified local reference | Repeat on the complete proposed PPDS package and its subject/trial/condition selectors; avoid unmeasured discovery GETs |
| Parquet / pandas + fsspec | **Pass with the same known-size adapter:** selected result and bounded range bodies | Preserve the required types/metadata in the complete PPDS workflow; default URL handling downloads the file |
| Parquet / DuckDB HTTPFS | **Pass on the same public fixture:** selected result plus logged Range/206 responses | Validate the complete PPDS schema, scans and actual published layout |
| Parquet / native Polars expressions and SQL | **Both selected queries pass** against a checksum-verified reference; four socket checks receive more TCP/TLS bytes than the fixture's size | No transfer reduction demonstrated for this fixture; validate the final PPDS layout and IO strategy. [Diagnostic](zenodo_access_tests.md#native-polars-transport-diagnostic) |
| Native DuckDB | **Pass:** catalog and selected rows match a checksum-verified local database; range GETs declare 1,585,152 bytes of a 20,983,808-byte public file | Validate PPDS tables, scans and intended storage version on the final publication |
| HDF5 / h5py + HTTPFile | **Pass:** a selected array slice matches a checksum-verified local reference; 2,768 bytes of a 2,060,096-byte file | Validate the PPDS chunk/layout choices and actual published package |
| Zarr ZIP / ZipStore + HTTPFile | **Pass:** a selected array slice matches a checksum-verified local reference; 6,073,947 bytes of a 16,861,207-byte archive | The fixture is Zarr format 2; test the proposed format-3 layout and avoid assuming small slices imply small chunks |
| Lance/LanceDB's tested generic HTTP URI paths | **Do not meet this gate as tested:** schemes are rejected before network access | Demonstrate a Python-installable delivery/adapter path that reads subsets from actual Zenodo files; an S3 mirror or full download alone does not satisfy this requirement |
| Lance native S3 provider with Zenodo endpoint | **Byte transport passes without a bridge:** independently matched prefix/tail ranges from a real Zenodo file | Valid unpacked Lance file/table querying remains untested; establish manifest/path/version discovery, not just object access |
| SQLite / packaged GenomicSQLite web VFS | **Blocked:** HTTP 403 on both URL forms; independent Python range and local database controls pass | Resolve this adapter/endpoint failure or validate a different Python HTTP VFS; no universal SQLite format failure inferred. [SQLite check](zenodo_access_tests.md#sqlite-baseline) |

These are path- and fixture-specific verdicts. They are not a final ranking of every possible
implementation of the underlying formats.

The user subsequently emphasized direct querying as a major selection factor. Keep the native
formats' verdicts distinct: Lance/LanceDB's raw HTTPS URI paths fail, while its configured S3
provider can reach Zenodo objects; complete table discovery is a remaining gate. Native DuckDB
remote `ATTACH` now passes on an actual Zenodo fixture. The measured PPDS size/scan-transfer
costs are separate concerns from protocol support. [Expanded evidence and scope](zenodo_access_tests.md),
[DuckDB HTTP(S) support](https://duckdb.org/docs/2.0/core_extensions/httpfs/https).

Zenodo currently documents **100 files per record**, a default **50 GB** record quota, and file
uploads up to **50 GB**. It recommends ZIP packaging above 20 files. Its newer quota guidance
allows allocating up to **150 GB additional allowance**, permitting records up to **200 GB**;
this does not establish a higher individual-file or file-count limit. The quota actually available
to the publishing account must be checked before publication. These are distinct limits, rather
than a single unconditional “50 GB maximum dataset” rule.
[Manage files](https://help.zenodo.org/docs/deposit/manage-files/),
[manage storage quota](https://help.zenodo.org/docs/deposit/manage-quota/).

Zenodo exposes records and file entries, not a documented S3-compatible bucket or general
directory filesystem contract. The supported publication workflow is file based; ZIP can retain
an internal directory tree. **Do not conclude that slash characters in file keys are forbidden:**
the live [record 7352326 API](https://zenodo.org/api/records/7352326) returned the key
`Wild-Minds/GreatApeDictionary-v1.1.zip`, with a matching nested content URL. That is evidence of
one accepted slash-containing key, not proof that current uploads can reproduce every Lance path
or that directory listing/version discovery will work. The API's folder-like “bucket” description
must not be mistaken for the S3 protocol. [Zenodo file API](https://developers.zenodo.org/#quickstart-upload).

Consequently, a flat publication manifest with explicit file URLs is a straightforward mapping for
a few consolidated Parquet files. A native database, HDF5 file or Zarr ZIP also has a simple
single-file mapping. A Lance release needs a concrete mapping from **every referenced object path**
to a published file URL, plus snapshot/table discovery. It might use native slash-containing keys,
a reader adapter, or a separate object-store mirror; these are alternatives to test, not validated
solutions. Count actual emitted files, including indexes, manifests and blob sidecars, before
judging the 100-file limit. Renaming files without preserving references is insufficient.

### Bounded live check, distinct from PPDS timings

On **2026-11-13 at approximately 16:15 UTC**, a new read-only check of
[this existing public PDF](https://zenodo.org/records/10890096/files/publishing_data_zenodo_v0.pdf)
returned:

| Request | Observed response |
| --- | --- |
| `HEAD` | `200`, `Content-Length: 721659`; no body read |
| `GET`, `Range: bytes=0-15`, identity encoding | `206`, `Content-Range: bytes 0-15/721659`, `Content-Length: 16`, `Accept-Ranges: bytes`; exactly 16 body bytes read |

Recorded check details (`hosting_checks.json`, historical source) include the file-key observation above.
This proves range delivery for that URL at that time. It is **not** a PPDS Zenodo benchmark,
proof of universal server behavior, a concurrency/rate-limit test, an availability history, or a
browser CORS check. No large file was downloaded. The existing PPDS HTTP results used localhost;
their injected latency is not measured Zenodo latency. [Benchmark method](storage_benchmark.md#timing-and-http-protocol).

### Actual public Zenodo Parquet reader check

Probe code (`zenodo_reader_probe.py`, historical source) and
raw responses/results (`zenodo_reader_probe.json`, historical source) test the official API content URL for
[`co_min_mean.parquet`, record 19115351](https://zenodo.org/api/records/19115351), an existing
**3,330,851-byte** public file. Its schema is `code_muni: double`, `date: date32`, `value: double`,
with 1,352,295 rows in 11 row groups. A suffix-range request returned **206**, the correct
`Content-Range` and the Parquet footer. No PPDS upload or remote modification was involved.

All four requested paths—PyArrow + fsspec, DuckDB's native HTTPFS, native Polars and pandas +
fsspec—filtered municipality `1100015` on `2025-01-01`, projected `code_muni,value` and returned
the same nonempty row (`value=0.13`) with the same selected-output SHA-256. Fresh PyArrow/pandas
fsspec paths each recorded **364,240 explicitly consumed response-body bytes**, seven client
requests and two Range/206 responses. The traces also contain header-only full-file discovery
GETs whose buffered bodies were not measured, so that original counter alone does not establish
total network transfer. The expanded matrix avoids this ambiguity by opening an HTTPFile with
the official record's size: both readers then use two range-only requests totaling 364,240 bytes.
DuckDB's HTTP logs contain Range/206 responses totaling **405,434 declared GET body bytes**;
these are logged response lengths, rather than an independent packet capture. Native Polars'
result is verified, while its wire transfer volume is unmeasured in this original probe.
[Expanded native/SQL and transport checks](zenodo_access_tests.md).

This is **real Zenodo reader feasibility evidence**, not localhost simulation. It is a small,
scalar public fixture below the target whole-dataset size, so it does not establish PPDS
multimodal fidelity, final layout efficiency, latency, concurrency or uptime. The matching hash
covers the selected output; the whole-file checksum advertised by Zenodo was not verified through
a complete download. No timed performance conclusions are drawn while the main benchmark runs.

### Synthetic S3 backend check

The independent read-only S3 subset server (`s3_range_server.py`, historical source) wraps the existing
range server with path-style bucket routing and ListObjectsV2 XML. In a four-row, four-file fixture,
**pylance 14.0.2 and LanceDB 0.41.0 both read a fixed-version `s3://ppds/...` table and filtered row
with exact values, schema and metadata**. Explicit settings select an unsigned localhost endpoint,
path-style addressing and non-TLS connections. HEAD/Range delivery, prefix/delimiter listing and
write/traversal/wrong-bucket rejection also pass. Raw fixture evidence (`s3_fixture_probe.json`, historical source).

This is deterministic **protocol simulation**, not a full S3 implementation, real object-store
service, Zenodo bridge, WAN experiment or performance ranking. Its ETags use file size/mtime as
opaque validators. It has no authentication, uploads, durability or recovery service. HTTP error
counters include expected metadata-discovery misses even when the complete read succeeds.

## Snapshot reproducibility, compatibility and export fidelity

Zenodo recommends creating a new version for significant file changes; a version has a distinct
record, identifier and files. However, current policy permits minor file corrections initiated
within **30 days** after publication and republished within **45 days**, without changing the DOI.
Exceptional later corrections are also possible. Thus “published DOI means bytes can never change”
is too strong. Use a version-specific record/DOI and a published cryptographic file manifest, and
verify checksums when obtaining an offline copy.
[Versioning](https://help.zenodo.org/docs/deposit/manage-versions/),
[post-publication corrections](https://help.zenodo.org/docs/deposit/manage-files/#modify-files-after-publication).

| Product or transition | Reproducibility and scientific-fidelity implications |
| --- | --- |
| Parquet → Arrow → Parquet | Record the Parquet format version, codec, Arrow schema and custom schema/field metadata. PyArrow normally stores a serialized `ARROW:schema` to restore details beyond Parquet's physical types, such as timezone/duration semantics. Other readers need not use or retain that metadata. [Writer schema behavior](https://arrow.apache.org/docs/python/generated/pyarrow.parquet.ParquetWriter.html) |
| Parquet → pandas → Parquet | Explicitly choose index handling and dtypes. pandas documents round-trip caveats for categorical types and unsupported Python objects; Arrow-backed dtypes can reduce conversions but do not prove arbitrary scientific field-metadata preservation. [pandas Parquet caveats](https://pandas.pydata.org/docs/user_guide/io.html#parquet), [Arrow/pandas integration](https://arrow.apache.org/docs/python/pandas.html) |
| Parquet → Polars → Parquet | Polars can write Parquet and explicitly attach file metadata; current native metadata-writing options are marked experimental. Test preservation of field units/descriptions and exact Arrow types rather than assuming a DataFrame round trip preserves the source schema. [Writer](https://docs.pola.rs/api/python/stable/reference/api/polars.DataFrame.write_parquet.html) |
| Native DuckDB → Arrow/Parquet | Pin the engine and explicit storage compatibility target. Newer readers provide backward compatibility; older-reader forward compatibility is best effort. SQL `COPY` can export Parquet, but table values alone are not a scientific metadata contract: persist/reapply the PPDS dictionary and validate exported schema/field metadata. [Compatibility](https://duckdb.org/docs/2.0/internals/storage), [export](https://duckdb.org/docs/2.0/sql/statements/copy) |
| Lance/LanceDB → Arrow/Parquet | Pin the client, table snapshot and explicit data-file version. `stable` depends on the installed release; `next` and current format 2.3 are unstable. Stable formats also have documented pattern-specific encoder compatibility caveats. [File-version contract](https://lance.org/format/file/versioning/) |
| Lance Blob v2 → ordinary binary export | A descriptor, lazy blob handle and materialized payload are different results. Exporting descriptors does not preserve the original STL bytes in a self-contained ordinary Parquet file. Select/fetch payload bytes explicitly and hash them. The Embedded docs distinguish `blob_mode` outputs and version-dependent restrictions. [Embedded blob reads](https://docs.lancedb.com/oss/v0-41-0/management/table#read-bytes-in-query-results), [Lance Blob API](https://lance.org/guide/blob/) |
| HDF5/Zarr arrays → Arrow/Parquet | Retain dimension order, shape, dtype, zero/null/fill semantics, measurement type, coordinate system, units and trial/subject identifiers explicitly. Array chunks/attributes do not automatically define a canonical tabular mapping. The prototypes' JSON index metadata are not proof of a full original-table schema round trip. [Dataset semantics](https://docs.h5py.org/en/stable/high/dataset.html), [PPDS verification scope](storage_benchmark.md#scope-and-correctness) |

For offline reproducibility, retain the entire dependency lock and Python/runtime version,
platform/architecture, codecs, extension identifiers, schema dictionary, reconstruction/export
code and file checksums. For DuckDB HTTP or Lance SQL integration, archive or preinstall compatible
extensions and verify installation from an empty cache: `INSTALL` normally retrieves a binary from
an extension repository. A warmed extension cache does not demonstrate an offline installation.
[DuckDB extension installation](https://duckdb.org/docs/2.0/extensions/installing_extensions).

For a self-contained Lance snapshot, preserve all referenced payloads and avoid relying on external
blob URLs or shallow-clone base paths that can disappear independently. Format portability is
conditional on copying referenced contents; a manifest alone is insufficient. For native DuckDB,
checkpoint and close before hashing/upload so required WAL data are in the database file.
[Lance portability](https://lance.org/format/table/layout/),
[DuckDB checkpoint](https://duckdb.org/docs/2.0/sql/statements/checkpoint).

## Platform availability and maintenance evidence

The table below is a **live package-distribution snapshot**, read from project-published PyPI JSON
metadata on 2026-11-13. “Wheel” means an artifact was present for at least one Python/ABI combination
on the listed architecture; it is not an installation test, a full support policy, or a promise
that all optional drivers/extensions work there. The latest releases listed here happen to match
the follow-up benchmark's principal tabular engines; the benchmark's complete environment remains
authoritative for measurements.

| Package | Current release; first artifact upload date | Declared Python minimum | Observed binary availability / qualification |
| --- | --- | --- | --- |
| [PyArrow](https://pypi.org/pypi/pyarrow/json) | 26.0.1; 2026-11-03 | 3.11 | Linux x86-64/ARM64, macOS Intel/ARM64, Windows x86-64. Official docs say Windows/macOS/Linux are built and tested. [Installation](https://arrow.apache.org/docs/python/install.html) |
| [DuckDB](https://pypi.org/pypi/duckdb/json) | 2.0.0; 2026-10-21 | 3.11 | Linux x86-64/ARM64, macOS Intel/ARM64, Windows x86-64/ARM64 wheels. The 2.0 platform policy gives Intel macOS partial support and community extensions best-effort availability; check the Lance extension separately. [Platform policy](https://duckdb.org/docs/2.0/dev/building/overview#platforms) |
| [Polars](https://pypi.org/pypi/polars/json) + [runtime](https://pypi.org/pypi/polars-runtime-32/json) | 2.1.0; 2026-10-25 | 3.11 | The top-level wheel is platform-independent; its compiled runtime has Linux x86-64/ARM64, macOS Intel/ARM64, Windows x86-64/ARM64 wheels. Choose the documented compatibility runtime for older CPUs. [Installation](https://docs.pola.rs/user-guide/installation/) |
| [pandas](https://pypi.org/pypi/pandas/json) | 3.1.1; 2026-11-04 | 3.11 | Linux x86-64/ARM64, macOS Intel/ARM64, Windows x86-64/ARM64 wheels. Parquet also needs a working PyArrow installation. [Current Parquet API](https://pandas.pydata.org/docs/reference/api/pandas.read_parquet.html) |
| [Lance (`pylance`)](https://pypi.org/pypi/pylance/json) | 14.0.2; 2026-10-29 | 3.10 | Linux x86-64/ARM64, macOS ARM64, Windows x86-64 wheels observed. No Intel macOS wheel in this release's file list; source-build feasibility was not tested. |
| [LanceDB](https://pypi.org/pypi/lancedb/json) | 0.41.0; 2026-10-29 | 3.10 | Linux x86-64/ARM64, macOS ARM64, Windows x86-64 wheels observed. No Intel macOS wheel observed; that is not a proof that every installation route is unsupported. |
| [h5py](https://pypi.org/pypi/h5py/json) | 3.16.0; 2026-03-06 | 3.10 | Linux x86-64/ARM64, macOS Intel/ARM64, Windows x86-64/ARM64 wheels; bundled HDF5 version and optional drivers matter. [Installation caveats](https://docs.h5py.org/en/stable/build.html) |
| [Zarr-Python](https://pypi.org/pypi/zarr/json) | 3.4.2; 2026-10-27 | 3.12 | Platform-independent Python wheel; codec/NumPy/remote-filesystem dependencies still constrain the complete environment. Zarr-Python 2 and 3 have different store APIs. [Storage/API change](https://zarr.readthedocs.io/en/stable/user-guide/storage/) |

Recent release artifacts, public source, compatibility documentation and accessible issue/release
channels are concrete maintenance evidence. They do **not** establish comparative failure rates,
archive longevity, corruption resistance or a reliability ranking. The reviewed sources do not
provide a common controlled reliability study for these PPDS layouts. Report actual failures and
their reproduction conditions, and distinguish a fixed-version result from guarantees about future
clients. HDF5 filter plugins, Zarr codecs, Arrow extension types and DuckDB/Lance extensions are
additional compatibility surfaces, even when the outer file format remains readable.

## Independent synthetic fidelity and error probes

Reproducible probe code (`reliability_probes.py`, historical source) and
[raw results](../observations/reader_reliability.json) cover **eight synthetic rows** in a 2,898-byte
Parquet fixture, using the six package versions above. Every route reads that source and exports
Parquet; Lance and LanceDB first persist a file-format-2.2 snapshot, then export through Arrow.
The fixture includes nullable `uint16` with distinct zero/null, finite float32/float64 boundary
values and signed zero, arbitrary binary bytes including invalid UTF-8 and empty/null payloads,
and required schema/field metadata including pressure units. No PPDS files are involved.

| Default round-trip route | Values, null/zero distinction, float bits, binary bytes | Exact Arrow types | Required scientific schema/field metadata |
| --- | --- | --- | --- |
| PyArrow | Preserved | Preserved | Preserved |
| pandas default dtypes | Preserved | Nullable `uint16` became `double` | Lost |
| pandas Arrow-backed dtypes | Preserved | Preserved | Lost |
| Polars default writer | Preserved | `binary` became `large_binary` | Lost |
| DuckDB default writer | Preserved | Preserved | Lost |
| Lance → Arrow → Parquet | Preserved | Preserved | Preserved |
| LanceDB Embedded → Arrow → Parquet | Preserved | Preserved | Preserved |

pandas and Polars also changed the non-nullable row-key field to nullable. After exact value
checks, **explicit safe casts and reapplication of the externally known Arrow schema** restored
all required types, nullability and metadata in all seven routes. This is a working export
strategy for this fixture, not evidence that those engines automatically retained the dictionary.
Type widening or dropped custom metadata is an interoperability result, not a corruption or
library-reliability verdict.

All **six expected failure probes rejected** their damaged inputs: truncated Parquet raised
`ArrowInvalid` through PyArrow/pandas, `ComputeError` through Polars and `InvalidInputException`
through DuckDB. Deleting one referenced Lance data file from guarded temporary copies raised
`ArrowInvalid` through Lance and `RuntimeError` through LanceDB. The original probe recorded the messages;
there was no silent success in those six cases, and the pristine Parquet fixture's hash remained
unchanged. These checks do not cover every PPDS type, silent corruption of otherwise valid data,
Blob v2 descriptors, concurrent writes, hardware failure, recovery or comparative failure rates.



## Questions that still need empirical answers

1. Can the intended Python environment query actual published PPDS file URLs after redirects,
   without full downloads, across fresh/reused readers and several subjects/trial sizes? Record
   ranges, bytes, requests, retries, errors and cold-start/extension setup separately.
2. Which supported object-store mirror, adapter or download workflow makes a minimal
   **fixed-snapshot Lance table** usable from the Zenodo publication? The tested direct HTTP URI
   path is rejected; a new path must first pass scheme support, then path escaping, discovery,
   listing and referenced-payload checks against the exact published layout.
3. Does Lance's ordinary binary-column layout versus dedicated Blob v2 layout improve actual STL
   transfer while preserving every byte? Treat compression/layout differences as separate variants.
4. Do Arrow, DuckDB, Polars and pandas produce identical values **and** the required scientific
   metadata/types on selected and complete exports? Include nulls, integer widths, categorical
   values, table keys, ordering, standing coordinates and scan bytes; do not substitute descriptors
   for payloads.
5. Can a clean, offline environment open the downloaded package and run the examples on intended
   Windows/Linux/macOS architectures? Browser/WASM requires its own extension and CORS checks.
6. What happens on a truncated download, wrong checksum, missing referenced object, stale cache or
   incompatible reader/storage version? Correct failure reporting and recovery are useful
   reliability measurements; a short successful timing run cannot answer them.

These questions keep the publication choice reviewable: documented capability establishes what is
reasonable to test, the PPDS benchmark establishes measured behavior, and a real hosted prototype
establishes the final delivery contract.
