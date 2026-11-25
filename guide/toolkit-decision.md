# Deciding whether to create a dataset toolkit

Use this proposed lab standard when planning a public release. The decision to record is what access software the lab will support. A file format defines released bytes, a query engine reads them, and a lab-maintained toolkit makes a promise about operations users can rely on across releases.

## Start with one user task

Give an analyst the file guide, an ordinary reader and a representative task. Write down the steps from selecting a release to obtaining an answer in scientific units. Identify which steps the analyst must repeat, which depend on domain knowledge, and which could produce a plausible wrong answer. Record the direct route alongside any proposed helper. A second analyst should be able to check the helper's result against that route or an independent reference.

| Outcome to record | When it earns its place | What to publish |
|---|---|---|
| Files and worked examples | Standard tools express the common tasks clearly. The metadata and a short example suffice to interpret the result. | File specification, versioned download and a runnable example with an expected answer. |
| Adopt an existing reader | Named resources, local and hosted access, or selective reads recur across datasets and an existing reader covers them. | Supported reader version, minimal manifest, a local and hosted example, and a fallback using the documented files. |
| Maintain a dataset toolkit | Users repeatedly implement scientific rules such as reconstruction, coordinate transforms or synchronization. There is a known answer and someone can maintain the interface. | A small installable package with named operations, input and result contracts, reference tests and versioned examples. Reuse the existing reader where it fits. |
| Extract shared code | A second dataset or a dataset-independent fixture demonstrates the same operation with different domain names and units. | A shared component with its own contract and tests. Each dataset owns its domain rules and can evolve them separately. |

## Define the contract before adding an operation

For each public operation, record the selector and its scope, release versions supported, result type, units, order, shape, missing-data semantics and expected failure or empty result. For storage access, specify how the same resource is found after download and on the host. A notebook can illustrate or visualize the operation. Put the scientific definition and its reference test next to the maintained implementation.

Before adopting a toolkit, record the owner, installation path, dependency and release effort, and how compatibility will be checked when the dataset changes. Test a normal selection, an absent or ambiguous key, and a known reference result. Where hosted selective access is promised, run the same operation locally and remotely, compare values and measure bytes. Record actual coverage for each promised client, including an in-browser runtime if offered.

Keep formats, keys, units and direct reading examples documented so another language can consume the release. If the lab cannot name an owner, record a narrower supported interface or provide a worked example. Revisit the decision when a second dataset needs the same code, users repeat a scientific conversion, or a release breaks an existing example.

## How the standard applies to PPDS

The shared reader resolves named resources and exposes Parquet views. The PPDS package reconstructs sparse pressure cells into a trial and returns the physical array in kPa. One routine can be exercised with generic tables. The other needs known pressure values, axes and frame counts. The lab's benchmarks measured storage and query behavior. The rationale for maintaining packages comes from these documented responsibilities and the released interfaces. [Worked PPDS decision](../case-studies/ppds/decision.md#why-ppds-has-a-toolkit)
