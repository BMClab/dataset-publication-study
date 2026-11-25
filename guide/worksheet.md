# Dataset publication decision record

Copy this page into the project, fill it in, and link to the observations used for the decision. Mark missing evidence as untested.

| Project question | Record your answer |
|---|---|
| Which release and audience is this for? | Dataset, version, decision date, author, users and their analysis environments |
| What must survive a round trip? | Units, keys, axes, clocks, types, missing values, zeros, binary objects and expected checks |
| Where will files be read? | Versioned host, approximate total and largest-file size, local download path, network and client constraints |
| Which criteria decide the outcome? | Required capabilities first, then preferences in priority order and their rationale |

| User task and frequency | Input selection and independent expected answer | Format, physical layout, reader and environment | First / repeat latency, memory, bytes and requests | Pass, failure or untested |
|---|---|---|---|---|
| Typical selective read | | | | |
| Cross-table join or array slice | | | | |
| Whole-dataset analysis or download | | | | |
| Binary object or other project-specific task | | | | |

**Toolkit decision.** Record files and examples alone, adoption of an existing reader, maintenance of a domain package, or a combination. Describe the shortest direct path for one user task. Which steps repeat or can silently change the result? Which existing tool covers them? What belongs in shared code, dataset code and the example? Name the maintainer, users, supported releases and installation route. Attach one operation's input, output type, units, missing-data behavior, expected error and independent reference check. For a decision against a package, record what future evidence would justify one.

**Decision and follow-up.** State the chosen storage layout, reader and toolkit scope separately. Link the dated report, package versions and results. Name the strongest alternative, the trade-off accepted, the next experiment that could change the decision, and who will revisit it. [Toolkit decision standard](toolkit-decision.md) · [PPDS example](../case-studies/ppds/decision.md)

## Worked example for another project

Consider a hypothetical 120 MB release of hourly rainfall from 40 gauges. Each row is keyed by station and UTC hour and stores an integer count of tenths of a millimetre. A zero means a dry hour and a null means the gauge failed. Most readers want one station-week. Occasionally a reader aggregates a year across the network.

- **Reference answer.** For four hours at gauge G07 with values `[0, 12, null, 8]`, return 2.0 mm over three valid hours and report four expected hours. A total alone would conceal a missing observation.
- **Provisional decision.** Try time-sorted records within station in Parquet, ordinary SQL and a worked example. The release already provides calibrated totals with one table and one documented unit conversion. Examples suffice for this task. Reopen the toolkit decision if users need to reconstruct rainfall from cumulative gauges with resets.
- **Next experiment.** Compare monthly and station-grouped Parquet layouts on the intended HTTP host and after download. Use the same data for the station-week and annual queries. Verify sums and valid-hour counts, then record first and repeated latencies, request counts and body bytes for each layout.

This illustrates how to fill in the worksheet. The rainfall workload has no measured results in this study.
