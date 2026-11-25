# Deciding whether to create a dataset toolkit

Use this proposed lab standard when planning a public release. The decision to record is what access software the lab will support. A file format defines released bytes, a query engine reads them, and a lab-maintained toolkit makes a promise about operations users can rely on across releases.

**Files and worked examples are the default.** A toolkit must pass the test below and have a named owner who accepts its costs.

## Test each consequential operation without a helper

Decide per operation, not per dataset. A release can pass the test for selecting data and fail it for reconstructing a measurement in physical units, so an easy task says nothing about a harder one.

1. List the operations users will perform between selecting data and reporting an answer in scientific units, such as selection, joins, reconstruction, unit conversion and synchronization. Mark each operation whose error could silently change a scientific result, and test every marked operation. For each, write the reference answer before anyone attempts it, including units, shape or row count, and how missing data appear.
2. Give two analysts who did not prepare the release the file guide, the planned worked example and an ordinary reader such as a SQL engine or DataFrame library. Ask for a variation of the example, such as a different selection or parameter, so the test shows whether users can adapt it. Provide no helper code.
3. Each analyst records the steps from selecting the release to an answer in scientific units. Compare both answers with the reference. Note where they diverged and why.

| What the test showed | Outcome |
|---|---|
| Both analysts reached the reference answer. | Files and worked examples. |
| An analyst went wrong, and a sentence in the file guide or a few lines in the example would have prevented it. | Files and worked examples. Revise the guide or example, then repeat the test with a new analyst. |
| The difficulty was finding and opening resources, such as names, paths or hosted versus downloaded copies. | Adopt an existing reader, or document the paths. Write lab code only when no existing reader covers the access pattern. |
| The correct route needs an algorithm or release-specific parameters that analysts could not reproduce from the guide and a short example. | Candidate for a dataset toolkit. Define its contract and record its costs. |

Record a verdict for each operation. A toolkit covers only the operations whose verdict calls for one, and the release can combine outcomes, such as files and examples for selection and a toolkit for reconstruction. A step that can silently produce a plausible wrong answer is the most important thing to test. It does not by itself justify a toolkit. If the fix fits in the documentation, document it.

## Outcomes and what to publish

| Outcome | When it earns its place | What to publish |
|---|---|---|
| Files and worked examples | The default. Analysts reach the reference answer from the guide and examples, possibly after revising them. | File specification, versioned download and a runnable example with an expected answer. |
| Adopt an existing reader | Named resources, local and hosted access, or selective reads recur, and an existing reader covers them. | Supported reader version, minimal manifest, a local and hosted example, and a fallback using the documented files. |
| Maintain a dataset toolkit | The test found an operation that analysts cannot reproduce from documentation. The operation has an independent reference answer, and a named owner accepts the costs below. | A small installable package with named operations, input and result contracts, reference tests and versioned examples. Reuse an existing reader where it fits. Keep a prose or formula description of each operation in the file guide so other languages can implement it. |
| Extract shared code | A second real dataset needs the same operation with different domain names and units. | A shared component with its own contract and tests. Each dataset owns its domain rules and can evolve them separately. |

A fixture the lab writes itself can test shared code. It does not show that a second dataset needs it. Until one does, keep the code in the dataset toolkit or mark the shared component provisional.

## Define the contract before adding an operation

For each public operation, record the selector and its scope, release versions supported, result type, units, order, shape, missing-data semantics and expected failure or empty result. For storage access, specify how the same resource is found after download and on the host. A notebook can illustrate or visualize the operation. Put the scientific definition and its reference test next to the maintained implementation.

## Record the costs and coverage

Before adopting a toolkit, record the owner, supported releases, installation path, dependencies, release effort and how compatibility will be checked when the dataset changes. Test a normal selection, an absent or ambiguous key, and a known reference result. Where hosted selective access is promised, run the same operation locally and against the final public record without credentials. Compare values and measure bytes and requests. Record actual coverage for each promised client, including an in-browser runtime if offered. Mark support known only from documentation as untested.

Keep formats, keys, units and direct reading examples documented so another language can consume the release. If the lab cannot name an owner, publish a narrower supported interface or a worked example. Revisit the decision when a second dataset needs the same code, users repeat a scientific conversion, or a release breaks an existing example.

## Two worked records

These hypothetical projects show the same test reaching different outcomes. Neither has measured results in this study.

- **Rainfall.** A 120 MB release of hourly rainfall from 40 gauges. Each row is keyed by station and UTC hour and stores an integer count of tenths of a millimetre. Zero means a dry hour and null means the gauge failed.
- **Accelerometry.** A 600 MB release of raw tri-axial counts from 200 wrist devices. Converting counts to acceleration needs each device's offset and gain from a static calibration. A firmware update partway through collection changed the axis convention. Each device clock drifts and is resynchronized whenever the device is docked.

| Record | Rainfall | Accelerometry |
|---|---|---|
| Operations tested and reference answers | Selecting a station-week, and totalling it with missing hours. For four hours at gauge G07 with values `[0, 12, null, 8]`, return 2.0 mm over three valid hours and report four expected hours. | Selecting a device-day, calibration, axis convention and clock correction. A device lying still face up must read (0, 0, +1.00) ± 0.02 g in the documented axes on both firmware versions, with z pointing out of the watch face. A tap recorded between two dock events must appear within 0.1 s of its time on an independent reference clock. A hand-converted sample from the calibration table must match to 0.001 g. |
| What the test showed | Both analysts selected the station-week. One reported 2.0 mm without noticing the failed hour. Adding the valid-hour count to the example and one sentence to the guide fixed it. A new analyst then passed. | Both analysts selected the device-day and applied the calibration correctly. One applied the original axis convention to every device, which preserves the magnitude but not the face-up vector. The other ignored clock drift and placed the tap 4 s late. Fixing either required interpolating between dock events and selecting per-device firmware parameters, which a short example could not carry. |
| Outcome | Files and worked examples for both operations. | Files and examples for selection. Toolkit for conversion to g on UTC, which combines calibration, axis convention and clock correction. |
| Public interface | Parquet sorted by station and hour, SQL example returning total, valid hours and expected hours. | `calibrated_acceleration(device, start, stop)` returning a table with drift-corrected `time_utc` and `x`, `y` and `z` in g in the documented axes. Samples missing within the interval appear as rows with null acceleration at their expected times. An unknown device raises an error and an interval without recorded data returns an empty table. |
| Owner, releases and installation | The release maintainer keeps the example running against each version. No package. | A named data manager supports releases 1.x. The package is installable from a public index. A formula description in the file guide is the fallback for other languages. |
| Reference check | The example asserts the four-hour answer. | Package tests assert the face-up vector on each firmware version, the tap's UTC time and the hand-converted sample. |
| What would reopen it | Users need rainfall reconstructed from cumulative gauges with resets. | A second dataset recorded on the same devices, which would justify extracting the calibration as shared code. |

The [worksheet](worksheet.md) records the full rainfall decision, including the storage experiment. The [PPDS case](../case-studies/ppds/decision.md#why-ppds-has-a-toolkit) shows how one lab applied this reasoning to a real release.
