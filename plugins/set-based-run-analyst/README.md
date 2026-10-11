# Set-Based Run Analyst 0.1.0

Private report-only plugin for label-agnostic EDT/ERL characterization.

## Use and connection

Install/enable the private plugin in ChatGPT Work or a compatible skill host with Python 3.10+ execution and authorized file access. Select Set-Based Run Analyst and attach a report, asking: "Inspect this report through blind ingestion and explain the retained paths." Prefer neutral filenames and a fresh session. Host attachment previews can expose raw material before ingestion; no plugin can retroactively erase that exposure.

This is a skill plus a deterministic local analysis utility. There is no hosted MCP server, endpoint, UI, credential setup, network service, or unrestricted command tool. The utility uses only the Python standard library. Enabling the plugin does not itself grant data access. If a host cannot execute packaged scripts, run the command below locally and supply only the sanitized JSON; the skill must not analyze the raw report as a fallback.

From the extracted plugin directory:

```bash
python skills/analyze-set-runs/scripts/inspect_report.py /authorized/neutral-report.txt 0 20
python -m unittest discover -s tests -v
```

The final two arguments are optional pagination offset and page size (1–100). Input is read-only JSON of any suffix, maximum 16 MiB. Output is JSON with neutral IDs, configuration, observable definitions, structured paths, metrics and arithmetic warnings. Exit 1 emits a generic error without paths or raw exception text. Unsupported schema versions are explicitly reported. Unrecognized metadata/custom features are withheld, so arbitrary extensions need a reviewed adapter. The schema snapshot and vetted vocabulary are packaged with the skill.

## Implemented

- Blind report inspection, pagination and structured pruning explanations.
- EDT/current and older version-1 ERL optional-field handling, including empty rule lists and .txt JSON.
- Counts, acceptances, training-class purity, score/penalty, rate, prefix monotonicity, IDs, rank order, priority completion, witness arithmetic, EDT partitions/default selection checks.
- Physical object categories and recorded validated metadata; unknown features become neutral aliases.
- Comparison through the skill using separate neutral run IDs and explicit metadata caveats.

## Not implemented

Tensor ingestion, tensor predicate re-evaluation, empirical overlaps/ORs, distributions, local threshold scans, holdout evaluation, or training. No .pt, pickle, supplied code, or raw_rule execution is attempted. The tests preserve guard/branch/pair/count semantics in report records; they do **not** validate tensor-level padding, shared-member evaluation or inherited EDT slot execution. Those require a future isolated tensor backend and matching core tests. No live post-install host execution has been verified merely by saving a plugin.

Source: Xinlong12580/Set_Based_Models, erl-workflow-release, retrieved commit 90ae91001090110a3689688bfde6140584ede102. The run's revision remains unknown unless independently established. The repository is unchanged.

## Verification

21 automated tests pass. Fixtures are the upstream hand-authored synthetic reports with truth fields removed and neutral input aliases. Tests mutate labels, label counts, revealing filenames and malicious metadata; sanitized results remain invariant. Invalid JSON, duplicate keys, nonfinite constants and non-JSON loading fail safely. A separate skill execution correctly explained retained rules, signed logical pruning and zero-pass limits.

See DEMO.md for the blinded synthetic demonstration and skills/analyze-set-runs/references/semantics.md for source-grounded interpretation rules.
