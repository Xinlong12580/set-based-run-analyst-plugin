# Publish and install

Extract the ZIP and use the contents of set-based-run-analyst-github as your
repository root, without an extra enclosing directory. Commit all files in
COMMIT_FILES.txt, including hidden directories.

## Publish

Create an empty GitHub repository. Replace YOUR_GITHUB_OWNER and YOUR_REPOSITORY
below with actual values; this URL is a placeholder.

```bash
git init -b main
git add -- .agents .codex .gitignore README.md INSTALL.md COMMIT_FILES.txt SOURCE.json SHA256SUMS plugins
git commit -m "Add Set-Based Run Analyst plugin and marketplace"
git remote add origin https://github.com/YOUR_GITHUB_OWNER/YOUR_REPOSITORY.git
git push -u origin main
```

For an existing repository, preserve its branch and remote instead of running
git init or git remote add.

## Codex CLI: install from a clone

Requires a CLI version supporting plugin marketplaces.

```bash
git clone https://github.com/YOUR_GITHUB_OWNER/YOUR_REPOSITORY.git set-based-run-analyst
cd set-based-run-analyst
codex plugin marketplace add .
codex plugin marketplace list
codex
```

Trust the project when prompted. Its .codex/config.toml enables the plugin.
Keep the clone because the registered source uses its files.

## Alternative: track the GitHub source directly

```bash
codex plugin marketplace add https://github.com/YOUR_GITHUB_OWNER/YOUR_REPOSITORY.git --ref main
```

Registration alone does not enable the plugin. Merge this into your existing
~/.codex/config.toml for use across projects, preserving other settings:

```toml
[plugins."set-based-run-analyst@set-based-run-analyst-local"]
enabled = true
```

Then refresh and restart:

```bash
codex plugin marketplace upgrade set-based-run-analyst-local
codex plugin marketplace list
codex
```

Choose one registration approach. Fetch the full repository: a sparse checkout
of only .agents/plugins omits the plugin payload. Private repositories require
Git access.

## Usage and checks

Ask Codex: "Use analyze-set-runs to inspect my authorized report through blind
ingestion." Prefer a neutral filename and a fresh session. Requires Python
3.10+, with no third-party Python dependencies or MCP server.

```bash
python3 -m unittest discover -s plugins/set-based-run-analyst/tests -v
python3 plugins/set-based-run-analyst/skills/analyze-set-runs/scripts/inspect_report.py plugins/set-based-run-analyst/examples/edt.json 0 20
sha256sum -c SHA256SUMS
```

All 21 tests passed in the original export. All 14 original files remain
byte-for-byte unchanged. Repository paths and checksums were validated.
Live installation was not tested: Codex CLI is unavailable in this environment.

Official setup documentation (checked 2026-10-11):
https://developers.openai.com/plugins/build/plugins
