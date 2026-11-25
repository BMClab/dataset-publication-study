# Choosing formats and readers

Start with a question someone will ask of the published data. “How much force did older participants produce while walking slowly?” determines which identifiers, units, joins and files a user needs. “What was the total rainfall at each gauge last July?” and “Read the pressure under one sensor through time” can favor different physical layouts for the same kind of measurements. Write down the common questions before choosing candidates.

1. **Define what must survive publication.** State the observation represented by a row or array element, its key, unit, axis order, sampling clock and missing-value convention. Record how to distinguish a measured zero, a missing measurement and a time outside the recording. If original objects must survive intact, retain their sizes and hashes as references.
2. **Describe where analysis happens.** Record expected release size, largest and smallest objects, file-count constraints, deposition host, local and offline paths, languages and notebook environments. Decide whether selecting one observation must save network traffic. Record the host's rate limit and whether anonymous users get a lower one.
3. **Choose representative work.** Include an individual selection, the most important join or slice, a full pass and any large binary object. Write a reference result before timing each query. For joins check both row counts and values. For arrays check shape and axis order as well. State the expected frequency of each workload and which requirements are mandatory.
4. **Compare one choice at a time.** Try multiple readers on identical files, then alternative encodings of the same logical data. Write down sort order, row groups, array chunks, indexes, compression, schema metadata and file sizes. These settings also determine how many requests a hosted read makes. Record the reader version and client. An engine can query external files and also store its own database. Those are separate candidates.
5. **Measure a successful answer.** Verify the answer first. Record first query, repeat on the same reader, cache state, peak memory and repetition count. On HTTP record the layer at which bodies and request attempts were counted. A correct result can follow a whole-file download. Keep local, simulated network and hosted observations in separate rows. Preserve failures and missing measurements.
6. **Decide on measured requirements.** Rank candidates first on the mandatory capabilities they demonstrated, then on preferences. Mark support known only from documentation as untested. A preference backed only by documentation should not outweigh a measured failure.
7. **Decide who owns the access code.** Run the [two-analyst test](toolkit-decision.md#test-one-user-task-without-a-helper) with the ordinary reader and one worked example. Record the outcome, scope, evidence and cost using the [toolkit decision standard](toolkit-decision.md).

## Simple array files such as NPZ

NumPy's NPZ format is a ZIP archive with one `.npy` member per array. It is easy to write and load in Python, so it is a common working format. The PPDS study used NPZ only for its source data and reference answers and did not test it as a publication candidate. Its documented properties make it a weak main format when users need selections or joins:

- **Whole-array reads.** A reader can fetch one member of the archive by byte range, but standard NumPy loading reads the whole member, and a compressed member must be decompressed in full. Selecting one frame or sensor therefore costs the whole array. Chunked formats such as Zarr and HDF5 can read a slice.
- **No tables or queries.** Each member is a single array with no keys. Joining participants to trials to measurements needs code written by each user. None of the readers in this study, including DuckDB, Polars, pandas and PyArrow, read NPZ.
- **Limited reach outside Python.** Libraries for other languages exist, but they are third-party and not part of the common analysis tools.
- **Minimal metadata.** Each array records only its data type, shape and memory order. Units, axis names and missing-value conventions must come from a separate dictionary.
- **Unsafe loading when pickles are enabled.** Arrays of Python objects are stored as pickles. Loading them requires `allow_pickle=True`, which can run code embedded in the file. Publish only numeric arrays, and tell users never to enable that option for downloaded files.

NPZ can still suit a few small dense arrays that users always load whole, such as a calibration table or a template, published alongside the main files. Record its checksum, and document each array's units and axes in the release dictionary.

## Check the final public release

Results from a local copy, a mirror or an authenticated draft do not show how the public release behaves. Before publishing a recommendation, check it against the release itself.

- **Use the final public record without credentials.** Run the representative tasks with each recommended reader and the versions you will document. Hosts can treat anonymous requests differently from authenticated ones.
- **Include the smallest file.** A reader's first request for a file's index can be larger than the whole file, and some hosts answer that request incorrectly. A reader that works on a large hosted file can still fail on a small one.
- **Estimate the throttling floor.** Divide the request count of each hosted workload by the host's rate limit. The result is a minimum time that no connection speed can beat. When a full pass needs many requests, tell users to download the files for whole-table work, or use fewer, larger row groups or chunks.
- **Account for layout changes.** If the released layout differs from the benchmarked one, rerun the affected tasks or state which measured results still apply.
- **Say what can be rerun.** Regenerating tables from archived observations shows that the archive is consistent. It does not reproduce the measurement. Where possible, publish benchmark code that runs against the public release.

Use the [worksheet](worksheet.md) to state what would change the choice. A project serving mostly single trials might optimize selective transfers. One serving full daily aggregations could accept extra work per trial to reduce requests across the full dataset. The [PPDS case](../case-studies/ppds/decision.md) measured both.
