# Querying PPDS after download

*Historical research record, November 2026. See the [evidence index](../README.md) for inputs, versions and available observations.*

This test runs the four Zenodo workloads against files on a local NVMe SSD. The scientific comparison uses DuckDB and Polars on the same ten files that went through the Zenodo upload and download check. Each local file matched the archived download SHA-256 before testing. The five tables in each format total 348.62 MB for Parquet and 368.60 MB for compact Vortex. [Zenodo measurements](lab_formats_zenodo_ppds.md) · [Transfer checksums](../observations/lab_formats_zenodo_ppds_transfer.json)

## Local query results

**First query with data pages evicted, in milliseconds.** Each value is the median of five fresh readers. The four Parquet/Vortex configurations form the matched Zenodo comparison. The last two rows are supplementary local controls measured in a second series with the same cache and timing procedure. The prebuilt native DuckDB database contains all eight prepared tables and occupies 599.01 MB. The timings exclude conversion to that database. pandas opens the same Parquet files as the other readers.

| Reader and local file | One trial | Cohort force join | One foot STL | All pressure |
|---|---:|---:|---:|---:|
| DuckDB / Parquet | 54.7 | 42.7 | 32.6 | 248.5 |
| Polars / Parquet | 12.2 | 31.1 | 11.3 | 300.2 |
| DuckDB / compact Vortex | 131.0 | 125.9 | 891.9 | 383.2 |
| Polars / compact Vortex | 69.9 | 37.7 | 806.0 | 348.6 |
| DuckDB / native database | 37.7 | 47.2 | 953.1 | 268.3 |
| pandas / Parquet | 36.9 | 90.5 | 13.0 | 1040.1 |

**First / repeat query with data pages initially resident, in milliseconds.** The first query still opens a fresh reader. The repeat reuses that reader. The underlying observations also include repeat timings for the initially evicted series.

| Reader and local file | One trial | Cohort force join | One foot STL | All pressure |
|---|---:|---:|---:|---:|
| DuckDB / Parquet | 51.9 / 27.6 | 38.6 / 15.8 | 28.5 / 6.3 | 247.1 / 227.9 |
| Polars / Parquet | 8.8 / 4.5 | 28.4 / 17.5 | 7.2 / 4.4 | 296.1 / 290.2 |
| DuckDB / compact Vortex | 123.1 / 28.5 | 123.9 / 25.9 | 815.0 / 731.1 | 339.2 / 237.7 |
| Polars / compact Vortex | 60.5 / 53.5 | 33.9 / 25.0 | 709.1 / 715.4 | 319.2 / 328.2 |
| DuckDB / native database | 30.8 / 3.6 | 37.8 / 11.8 | 818.7 / 668.4 | 149.2 / 74.9 |
| pandas / Parquet | 32.2 / 28.7 | 88.5 / 78.4 | 8.0 / 5.8 | 1012.4 / 989.7 |

Across both series, 240 workers executed 480 queries. Every result matched the corresponding Zenodo reference, including the STL byte hash. All mesh timings use the standard readers. [Matched observations and file hashes](../observations/lab_formats_zenodo_ppds_local.json) · [Native DuckDB and pandas controls](../observations/lab_formats_zenodo_ppds_local_baselines.json)

## What changes after download

Across the two encodings staged on Zenodo, Parquet had the lower first-query median for every workload with both readers and both starting cache states on this machine. The full pressure aggregation illustrates why local and remote timings matter separately. With DuckDB and evicted data pages, Parquet took 248.5 ms and compact Vortex took 383.2 ms. The five first-query measurements ranged from 246 to 258 ms and 379 to 396 ms, respectively. The earlier Zenodo test observed 435 s for Parquet and 156 s for compact Vortex, with many more HTTP requests for Parquet. On the local SSD the Vortex reader also retrieved the STL with its default settings. [Comparable Zenodo measurements](lab_formats_zenodo_ppds.md#remote-query-results)

Reader setup accounts for much of the first-query difference for the DuckDB cohort join. With file pages evicted, median connection and reader setup was 18.5 ms for Parquet and 91.5 ms for compact Vortex, including its extension load. Measuring the first query from the end of setup gave medians of 23.8 and 36.6 ms, respectively. These query-only medians use the paired timings from each worker.

Reader reuse matters. For a full pressure aggregation repeated on an open DuckDB connection after a memory-resident start, median time was 227.9 ms for Parquet and 237.7 ms for compact Vortex. Their five-run ranges overlapped. The native DuckDB file had the fastest repeated full aggregation at 74.9 ms and repeated cohort join at 11.8 ms. Polars on Parquet was particularly quick for an individual trial or scan, taking 12.2 ms and 11.3 ms on a first read with data pages evicted.

For a local analyst who mostly opens individual trials, joins cohorts or retrieves a scan, Polars on Parquet had the fastest first queries among the two matched toolkits. DuckDB on Parquet had the fastest first full pressure aggregation. The lab’s preference for DuckDB as its primary toolkit also draws on the SQL workflow and hosted access. [Broader comparison](lab_format_benchmark.md) A researcher repeatedly aggregating the entire table locally can benefit from a native DuckDB copy. On the resident first full aggregation, pandas took 1,012 ms and its median process peak was 2,446 MiB, versus 247 ms and 238 MiB for DuckDB on the same Parquet file. Peak memory includes imported libraries and result verification. These are measurements of the PPDS layouts, reader versions and hardware described below.

## Workloads and timing

- **One trial** selects the 138,035 nonzero pressure cells from the 840 frames of one slow-walking trial.
- **Cohort force join** selects participants aged 60 or older and joins their slow and comfortable walking trials to the force samples. Each participant contributes a sample count, trial count and peak right-foot force. The result covers 34 participants, 680 trials and 345,523 samples.
- **One foot STL** retrieves the 1,153,984-byte right-foot scan from the scans table.
- **All pressure** projects trial ID and pressure value across 112,965,976 nonzero cells and computes each trial’s count and peak. The result has 3,312 rows.

The test used an eight-core Intel Xeon W-2245 and a CT2000T500SSD8 NVMe SSD with ext4. The benchmark requested four engine threads. It used Python 3.14.9, DuckDB 2.0.1, Polars 2.1.0, vortex-data 0.93.0 and pandas 3.1.1. Five randomized blocks ran serially. Each reader, workload and starting cache state got its own fresh Python process in each block. The first query includes reader creation and loading the installed DuckDB Vortex extension where applicable. The repeat uses the same reader after the first result has been checked. Process startup, module imports, file preparation and result hashing are outside the timers. Download time is accounted for separately in the Zenodo report. [Workload implementations](../methods/lab_format_queries.py) · Timing and result checks (`lab_format_run.py`, historical source)

The timings measure the Python readers. An earlier Python-backed marimo export verified the local cohort join with all four matched reader/format combinations and with marimo’s built-in SQL cell on Parquet. Notebook startup and rendering are outside these measurements. [marimo notebook results](../observations/lab_formats_marimo.json)

For the SSD-first measurement, Linux evicted the relevant file pages from the page cache using `POSIX_FADV_DONTNEED` on disposable copies. For the memory-resident measurement, the runner read those files sequentially before starting the worker. Linux `fincore` verified zero or all pages resident for every participating file before each worker started. For the native DuckDB control, this check covers the whole database file. The repeats reflect reuse immediately after a successful read. An already-open reader after eviction of its data pages was outside this test. No local physical I/O byte counter was collected, so mesh elapsed time and peak memory alone cannot determine which bytes the SSD supplied. The cache condition applies to the data files. SSD controller caches, filesystem metadata and package code retained their normal system state. Local runner (`zenodo_ppds_local.py`, historical source)
