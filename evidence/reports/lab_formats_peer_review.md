# Antigravity review of the PPDS storage benchmark

*Historical research record, November 2026. See the [evidence index](../README.md) for inputs, versions and available observations.*

On 21 November 2026, Antigravity CLI 1.5.14 (`agy`, Gemini 3.8 Flash High) reviewed the original report, a summary of the claims, per-configuration timing medians and selected raw HTTPS observations supplied in its prompt. Its first verdict was **major revision required**. It returned seven findings before the print session reached its time limit. The reviewer assessed supplied evidence. The author then checked the findings against the saved JSON and independently reran the participant–trial–force join on the benchmark database. [Revised report](lab_format_benchmark.md)

| Issue raised | Resolution |
|---|---|
| The Vortex headline implied a general speed advantage. | The revised report gives body bytes, request counts and elapsed time. Compact Vortex required 25 requests versus 883 for DuckDB over Parquet. On the same aggregation its first-query time was longer with DuckDB and shorter with Polars. Selective trial and mesh measurements appear alongside the broad scan. |
| A loopback byte count could be read as a production transfer measurement. | The report describes response bodies written by the server. Zenodo checks used public Parquet and DuckDB fixtures. The public Vortex fixture was on GitHub. The production performance of a PPDS deposit is still an open measurement. |
| “384 results” lacked a denominator. | The count comprises four workloads executed twice in each of 192 fresh processes. The additional hosted and notebook checks are counted separately. The 4.1× pandas ratio compares local first queries over the same Parquet pressure table. |
| The pandas join was optimized manually. | The measured implementation filters both child tables by selected participant ID before merging. Its timing applies to that implementation. Alternative pandas merge orders would require their own measurements. |
| Trial identifiers could be confused. | The report distinguishes the trial number within participant and condition from the globally unique trial ID. The independent SQL check reproduced 34 participants, 680 trials and 345,523 force samples. |
| Notebook and language coverage were grouped together. | Python and JavaScript were exercised. marimo was a Python notebook integration test. R and MATLAB coverage comes from documentation. |
| HTTPS timings had only two first-query observations per configuration. | Elapsed times are identified as exploratory midpoints. The JSON retains both observations. |

The reviewer also suggested explanations involving Vortex decompression, predicted Zenodo throttling and interpreted the catalogue search as showing that no Vortex files exist there. The experiments provide timings, transfer counters and a bounded search. Each of those stronger claims would require different evidence. [Local measurements](../observations/lab_formats_local.json) · [Loopback measurements](../observations/lab_formats_https.json) · [Hosted checks](../observations/lab_formats_hosted.json) · Vortex discovery (`lab_formats_vortex_discovery.json`, historical source)

## Follow-up verdict

A second `agy` session reviewed the revised claims and their numerical evidence. Its verdict was **“Accept”**, with **“Remaining material errors: None.”** This follow-up assessed the supplied corrections. It did not rerun the benchmarks.

Antigravity also reviewed the subsequent production Zenodo transport check. It agreed that the evidence supports an expectation of partial Vortex queries and establishes partial transport on Zenodo. The test used a known Parquet footer as a negative format control. Zenodo transport results (`lab_formats_zenodo_vortex_transport.json`, historical source)

## Independent recommendations for a single lab standard

On 21 November 2026, Antigravity CLI (Gemini 4 Neon High) and Claude Code (Claude Opus 5.5) were each asked to choose one public storage format and one primary query toolkit for PPDS and future lab projects. Each received the same requirements, measurements and research context, including the lab’s willingness to invest in Vortex. Neither received the earlier recommendation or the other response. These opinions interpret the existing tests.

| Reviewer | Choice | What most influenced the choice |
|---|---|---|
| Antigravity | Parquet + DuckDB | Practical access for outside researchers, including MATLAB and R. It would reconsider after a representative Zenodo test shows that a tuned Vortex layout can retrieve a single trial or foot scan near Parquet’s transfer volume, alongside a practical path for those users. |
| Claude | Parquet + DuckDB | Selective public reads and SQL joins across participant, trial and force tables. A real-network result showing that Parquet’s many requests materially slow routine analyses would weigh in Vortex’s favor. |

Both identified the strongest case for compact Vortex in the full pressure aggregation. With DuckDB it used 25 requests versus 883 for Parquet on loopback HTTPS. Both also recommended keeping the scientific table names and columns stable so that a change of file reader can be confined to the definitions of SQL views. [Benchmark results](lab_format_benchmark.md)

The research case is tangible. Wes McKinney and his F3 coauthors reused Vortex encodings in their prototype. The AnyBlox team compiled a Vortex decoder to WebAssembly and tested it in their framework. Vortex guarantees backward readability for frozen editions. Its specification describes embedding decoders for older readers as a proposed extension. [F3 paper](https://db.cs.cmu.edu/papers/2025/zeng-sigmod2025.pdf) · [AnyBlox paper](https://gienieczko.com/anyblox-paper) · [Vortex compatibility specification](https://docs.vortex.dev/specs/file-format)

Both reviewers retained Parquet + DuckDB after seeing the verified native Vortex scan, lazy Polars selection and direct SQL join. Both asked that summaries identify the Vortex layout. The benchmark tables give both layouts for local and HTTPS runs. Claude asked for a measurable criterion for selective access. Antigravity pointed out that Parquet request counts depend on the layout and reader, and preferred a 1.0 release for preservation. Vortex already documents a backward-readability guarantee for frozen editions. The production test will measure how long users wait for a single trial, a cohort join, one STL and a full pressure aggregation. [Tested notebook queries and local timings](lab_format_benchmark.md#querying-vortex-files-from-a-notebook) · [Vortex compatibility specification](https://docs.vortex.dev/specs/file-format)

## Restricted production Zenodo follow-up

Antigravity (Gemini 4 Neon High) reviewed the experimental method and then reviewed the measured DuckDB comparisons for a single trial, cohort join and full pressure aggregation. The review used aggregate results and had no access to credentials or files. It found no numerical inconsistency. It recommended distinguishing the direct Vortex-to-Polars check from the DuckDB extension measurements through the authenticated relay. It also noted that the broad Parquet run included rate-limit responses, while its immediate repeat issued only one HEAD. Reader caching, layout, rate limits, fixed run order and competing WAN conditions limit conclusions about format speed. The measurements do not isolate how much of the elapsed-time difference came from any one of those factors. [Production results and methods](lab_formats_zenodo_ppds.md)

## Independent review of the completed Zenodo test

On 22 November 2026, Codex CLI 0.169.0 (GPT-6.2 Astra) and Antigravity CLI 1.5.14 (Gemini 4 Neon High) received the same frozen packet of benchmark code, reported results, two archived measurement files, four reference signatures and earlier coverage evidence. Each reviewed it independently. Credentials, participant files and prior reviewer verdicts were excluded. Neither reviewer reran the network test. Packet SHA-256 was `2a301b5d1bfeb441e23123a3eee621179c821474d42f2a156f4494d1cbb91cef`. [Revised production report](lab_formats_zenodo_ppds.md)

| Reviewer | Verdict | Most consequential finding |
|---|---|---|
| Codex | Retain Parquet with DuckDB for the lab’s usual selective queries and same-session reuse. | The workload mix can reverse the choice. For DuckDB, the observed 279.55 s saving on one first-access full pressure aggregation with compact Vortex was comparable to the 4.04 s saving with Parquet on each of 69 first-access cohort joins. This ratio illustrates this run’s sensitivity to usage. |
| Antigravity | Accept with minor revisions. | DuckDB’s broad Parquet query touched nearly the entire pressure file and incurred 169 rate-limit responses. Physical layout, the relay and changing network conditions limit causal attribution. A direct public-release test would be needed to claim anonymous PPDS endpoint performance. |

Both reviewers accepted the numerical tables and the recommendation within the measured scope. The report now documents how each reference was constructed, the two-column pressure workload, the physical layouts, actual run order, the mesh adapter switch and how the receipts were assembled. The archived controls do not establish whether the preceding Parquet runs caused the single HTTP 429 on the later DuckDB/Vortex mesh attempt.

The local verification for this review recomputed all four reference signatures, checked every displayed timing and transport table cell against its underlying observation, and rehashed all ten local upload files against the archived Zenodo MD5s and downloaded SHA-256s. A separate SQL sum over the cohort results returned 34 participant rows, 680 distinct trials and 345,523 samples. The cohort digest was `ed6d50446ad4d042ac19b09142adcdd3f2dce181a757c6fb7385bb37d578ce93`. The default matrix has 28 matching results and two recorded first-read mesh failures. Both alternative mesh queries matched the original STL hash. All 138,035 nonzero pressure values in the reference trial were integral after conversion to kPa, so the reviewer’s rounding concern did not alter its digest. [Query measurements](../observations/lab_formats_zenodo_ppds_queries.json) · [Transfer measurements](../observations/lab_formats_zenodo_ppds_transfer.json)

Two points matter for future reruns. The relay can classify a downstream reset as `upstream_errors` and attempt a new error response after streaming headers. Its counters support upstream attempts, HTTP statuses and bytes consumed, but do not establish which endpoint closed a stream or how many bytes reached the reader. Also, the runner resumes by record, reader and workload, including previously saved failures. Use fresh output paths for independent timing repetitions and separate outputs for different adapters. Repeated, interleaved measurements across representative datasets and their public endpoints would be needed to establish a broader speed ranking.

## Review of the local SSD comparison

Codex (GPT-6.2 Astra) and Antigravity (Gemini 4 Neon High) independently reviewed the local experiment’s results, runner and timing boundaries. Both accepted the measured timings and Parquet’s first-query advantage for these PPDS layouts. Codex emphasized that native DuckDB’s repeated full aggregation used a prebuilt database. Antigravity highlighted the cost of opening a reader, the absence of a warm-reader test after data-page eviction, and the narrow basis for choosing one toolkit for every local analysis. The revised report gives setup and query-only timings for the DuckDB cohort join and identifies the three selective workloads where Polars on Parquet had the lower first-query median. [Local benchmark and raw observations](lab_formats_zenodo_ppds_local.md)

The shared worker sets the Polars thread limit before imports and opens DuckDB connections with four threads. A separate check of those runtime settings returned four for each reader. The local experiment measures elapsed time and peak process memory. It did not instrument local physical bytes read, so the large Vortex mesh timing does not establish that the reader fetched the whole file from the SSD. Worker (`lab_format_run.py`, historical source) · [Reader and queries](../methods/lab_format_queries.py)
