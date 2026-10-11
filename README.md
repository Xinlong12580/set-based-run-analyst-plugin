# Set-Based Run Analyst

Skills-only plugin for blind, label-agnostic analysis of EDT/ERL JSON reports.
Includes a Python standard-library parser, reference data, synthetic examples,
and 21 tests. Requires Python 3.10+.

| Path | Purpose |
| --- | --- |
| .agents/plugins/marketplace.json | Marketplace catalog |
| .codex/config.toml | Project plugin enablement |
| plugins/set-based-run-analyst/plugin.json | Portable manifest |
| plugins/set-based-run-analyst/.codex-plugin/plugin.json | Codex compatibility manifest |
| plugins/set-based-run-analyst/skills/analyze-set-runs/ | Skill, scripts, references, agent metadata |
| plugins/set-based-run-analyst/examples/ | EDT/ERL examples |
| plugins/set-based-run-analyst/tests/ | Parser tests |
| INSTALL.md | Publishing and installation commands |
| COMMIT_FILES.txt | Exact commit inventory |
| SOURCE.json | Source identity and hashes |
| SHA256SUMS | Distribution checksums |

The catalog points to ./plugins/set-based-run-analyst relative to the repository
root. Preserve hidden directories. The marketplace name remains
set-based-run-analyst-local for compatibility with the original export;
it also works for Git distribution.

See [INSTALL.md](INSTALL.md) and the [plugin README](plugins/set-based-run-analyst/README.md).
All 14 original plugin files are unchanged. No GitHub repository has been
published by preparing this package.
