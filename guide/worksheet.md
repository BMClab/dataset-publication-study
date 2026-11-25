# Dataset publication decision record

Copy this page into the project, fill it in, and link to the observations used for the decision. Mark missing evidence as untested.

| Project question | Record your answer |
|---|---|
| Which release and audience is this for? | Dataset, version, decision date, author, users and their analysis environments |
| What must survive a round trip? | Units, keys, axes, clocks, types, missing values, zeros, binary objects and expected checks |
| Where will files be read? | Versioned host and its rate limit, approximate total, largest and smallest file sizes, local download path, network and client constraints |
| Which criteria decide the outcome? | Required capabilities first, then preferences in priority order and their rationale |

| User task and frequency | Input selection and independent expected answer | Format, physical layout, reader and environment | First / repeat latency, memory, bytes and requests | Pass, failure or untested |
|---|---|---|---|---|
| Typical selective read | | | | |
| Cross-table join or array slice | | | | |
| Whole-dataset analysis or download | | | | |
| Binary object or other project-specific task | | | | |

In the last column, mark support known only from documentation as untested. Record whether each hosted result came from the final public record without credentials or from a draft, mirror or simulation.

**Toolkit decision.** Record files and examples alone, adoption of an existing reader, maintenance of a domain package, or a combination. Files and examples are the default. Run the [two-analyst test](toolkit-decision.md#test-one-user-task-without-a-helper) on one user task and record each analyst's steps, answer and divergence from the reference. Could a sentence in the guide or a few lines in the example have prevented each error? Which existing tool covers the access steps? What belongs in shared code, dataset code and the example? For a package, name the maintainer, users, supported releases and installation route. Attach one operation's input, output type, units, missing-data behavior, expected error and independent reference check. For a decision against a package, record what future evidence would justify one.

**Decision and follow-up.** State the chosen storage layout, reader and toolkit scope separately. Link the dated report, package versions and results. Name the strongest alternative, the trade-off accepted, the next experiment that could change the decision, and who will revisit it. [Toolkit decision standard](toolkit-decision.md) · [PPDS example](../case-studies/ppds/decision.md)

## Worked example for another project

Consider a hypothetical 120 MB release of hourly rainfall from 40 gauges. Each row is keyed by station and UTC hour and stores an integer count of tenths of a millimetre. A zero means a dry hour and a null means the gauge failed. Most readers want one station-week. Occasionally a reader aggregates a year across the network.

- **Reference answer.** For four hours at gauge G07 with values `[0, 12, null, 8]`, return 2.0 mm over three valid hours and report four expected hours. A total alone would conceal a missing observation.
- **Toolkit test.** Summing the values silently gives 2.0 mm without revealing the failed hour, so this is the step to test. In the two-analyst test, one analyst missed it. Counting valid hours alongside the total in the SQL example, plus one sentence in the guide, prevented the error for a new analyst.
- **Provisional decision.** Try time-sorted records within station in Parquet, ordinary SQL and the revised worked example. The correct route fits in the documentation, so no package is needed. Reopen the toolkit decision if users need to reconstruct rainfall from cumulative gauges with resets.
- **Next experiment.** Compare monthly and station-grouped Parquet layouts after download and on the final public record without credentials. Use the same data for the station-week and annual queries, and include the smallest file in the release. Verify sums and valid-hour counts, then record first and repeated latencies, request counts and body bytes for each layout. Divide the annual query's request count by the host's rate limit to find its minimum time.

This illustrates how to fill in the worksheet. The rainfall workload and its analyst test are hypothetical and have no measured results in this study. The [toolkit standard](toolkit-decision.md#two-worked-records) compares it with a project whose test leads to a toolkit.
