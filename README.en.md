# BLCaptain Codex Probe CLI

> A local-first Codex session-level token ledger, usage governance, and Skill / output inspection CLI. It helps you locate which session, project, and time window consumed tokens or credits, then explains why it is expensive, how to downgrade, and when to stop.

[中文 README](README.md)

![Python](https://img.shields.io/badge/Python-%3E%3D3.10-2b2622.svg)
![CLI](https://img.shields.io/badge/Type-CLI-d98e3a.svg)
![Local First](https://img.shields.io/badge/Data-Local--First-2f5ea7.svg)
![Release](https://img.shields.io/badge/Release-v0.5.0-4b5563.svg)
![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)

> **Fastest path in the Codex desktop app**
>
> Open this repository folder and send this prompt to Codex:
>
> ```text
> Please use BLCaptain Codex Probe CLI to open the local Codex token session ledger, analyze which session consumed the most tokens in the last 7 days, and generate reports.
> ```
>
> Keep the boundary explicit: only process repository samples or local files I explicitly provide; do not read browser cookies, tokens, keychains, system credentials, or chat content; do not upload any data.

> **Developer install**
>
> ```bash
> git clone https://github.com/dososo/BLCaptain-Codex-Probe-CLI.git
> cd BLCaptain-Codex-Probe-CLI
> python3 -m venv .venv
> . .venv/bin/activate
> python -m pip install .
> codex-probe --version
> ```

---

## What It Is

BLCaptain Codex Probe CLI is a local command-line tool. It is not a Codex Skill, and it is not a replacement for the official OpenAI usage dashboard.

In v0.5.0, the product moves from an importable sample ledger to **real local data-source ingestion plus a stable watcher**. The primary question is:

> Which Codex session, project, and time window consumed the tokens or credits?

It also keeps two earlier workflows:

1. **Task-level `/status` usage reports**: explain why one task is expensive, how to downgrade, and when to stop.
2. **Skill / output inspection**: check AI-smell, plugin risk, sensitive data, and missing privacy boundaries.

If local Codex structured rollout logs contain token-usage fields, the CLI can import historical session usage locally. If a source does not contain token fields, it imports only metadata or clearly reports that precise attribution is unavailable. It does not invent numbers.

It does not promise savings, bypass quotas, read login state, or replace official billing. Think of it as a local ledger and brake pedal for long Codex sessions.

## Output Preview

### Session-Level Token Ledger

The local ledger ranks sessions by time range. Each row includes token delta, credits delta, project, source, confidence, and recommended action.

Example reports:

- [Session ranking report](examples/reports/ledger/sessions.md)
- [Single-session detail report](examples/reports/ledger/session-readme-release.md)
- [Ledger summary report](examples/reports/ledger/ledger-report.md)
- [Privacy audit report](examples/reports/ledger/privacy-report.md)
- [Local HTML dashboard](examples/reports/ledger/dashboard.html)

<p>
  <img src="assets/screenshots/ledger-dashboard.png" alt="Local Codex session-level token ledger dashboard" width="100%">
</p>

### Existing Workflows: Task Report and Skill Inspection

| Task-level usage report | Skill / output quality inspection |
|---|---|
| <img src="assets/screenshots/usage-report-preview.svg" alt="Task-level usage report preview" width="100%"> | <img src="assets/screenshots/skill-lint-preview.svg" alt="Skill / output quality inspection preview" width="100%"> |
| Puts `total_tokens`, context remaining, 5-hour / 7-day quota, and the continue / downgrade / stop decision in one view. | Flags AI-smell, plugin risk, sensitive data, and missing privacy boundaries with redacted evidence snippets. |

## Naming

| Purpose | Name |
|---|---|
| Product name | BLCaptain Codex Probe CLI |
| GitHub repository | `BLCaptain-Codex-Probe-CLI` |
| Python package | `blcaptain-codex-probe` |
| Primary command | `codex-probe` |
| Short alias | `probe` |
| Compatibility commands | `blcaptain-codex-probe`, `codex-usage-skill-probe` |

Why not call it a Skill: this project is not an instruction package loaded by an Agent. It is a CLI that can be used by humans or Agents. It can inspect Skills, but it is not itself a Skill.

## Core Capabilities

| Capability | Command | Result |
|---|---|---|
| Safe source check | `codex-probe sources doctor` | Shows available sources, maximum confidence, and privacy boundary |
| Deep source check | `codex-probe sources doctor --deep` | Safely checks local Codex rollout field coverage with hashes and counts only |
| Initialize ledger | `codex-probe ledger init` | Creates SQLite schema and privacy audit record |
| Inspect official export | `codex-probe ledger inspect-export <file>` | Detects CSV / JSON / JSONL fields and suggested mappings |
| Generate field mapping | `codex-probe ledger map-export <file> --out mapping.json` | Writes an editable mapping JSON |
| Import official export | `codex-probe ledger import --official-export <file>` | Supports CSV / JSON / JSONL with exact-confidence session attribution |
| Import local history | `codex-probe ledger import-history --source local-codex` | Imports historical token snapshots from allowlisted local Codex rollout fields |
| Import local snapshots | `codex-probe ledger import --snapshot <file>` | high / medium / low-confidence delta attribution |
| One-shot collection | `codex-probe watch once` | Runs one safe local history collection |
| Background watcher | `codex-probe watch start/status/logs/stop` | Tracks PID, state, logs, last collection, errors, and collection count |
| Rank sessions | `codex-probe sessions --range 7d` | Finds the most expensive sessions |
| Session detail | `codex-probe session-report <session_id>` | Shows timeline, snapshots, and high-consumption windows |
| Ledger report | `codex-probe ledger-report --range 30d` | Summarizes tokens, credits, projects, and actions |
| Local dashboard | `codex-probe dashboard` | Generates a readable local HTML page |
| Privacy audit | `codex-probe privacy inspect` | Shows enabled sources, read fields, and audit logs |
| Delete watcher data | `codex-probe delete --watcher --yes` | Deletes watcher state, lock, stop flag, and logs |
| Delete ledger data | `codex-probe delete --ledger --yes` | Deletes ledger business data while keeping a non-sensitive audit trail |

Confidence levels:

- `exact`: a user-provided official export contains session ID and token data.
- `high`: local structured snapshots can attribute delta to one session.
- `medium`: multiple sessions or overlapping windows require metadata-based estimation.
- `low`: only global quota movement is available, so it is not an exact bill.

## Three-Minute Example

```bash
mkdir -p .probe reports/ledger

codex-probe --db .probe/ledger.db ledger init

codex-probe --db .probe/ledger.db sources doctor

codex-probe --db .probe/ledger.db sources doctor --deep

codex-probe --db .probe/ledger.db ledger import \
  --official-export examples/ledger-samples/official-export.csv

codex-probe --db .probe/ledger.db ledger inspect-export \
  examples/ledger-samples/official-export.jsonl

codex-probe --db .probe/ledger.db ledger import \
  --official-export examples/ledger-samples/official-export.jsonl

codex-probe --db .probe/ledger.db ledger import-history \
  --dry-run \
  --source local-codex \
  --root examples/ledger-samples/local-codex

codex-probe --db .probe/ledger.db ledger import-history \
  --source local-codex \
  --root examples/ledger-samples/local-codex

codex-probe --db .probe/ledger.db watch once \
  --root examples/ledger-samples/local-codex

codex-probe --db .probe/ledger.db ledger import \
  --snapshot examples/ledger-samples/snapshot-delta.json

codex-probe --db .probe/ledger.db sessions \
  --range 7d \
  --out reports/ledger/sessions.md

codex-probe --db .probe/ledger.db session-report \
  session_readme_release \
  --out reports/ledger/session-readme-release.md

codex-probe --db .probe/ledger.db ledger-report \
  --range 30d \
  --out reports/ledger/ledger-report.md

codex-probe --db .probe/ledger.db dashboard \
  --range 7d \
  --out reports/ledger/dashboard.html

codex-probe --db .probe/ledger.db privacy inspect \
  --out reports/ledger/privacy-report.md
```

Delete local ledger business data:

```bash
codex-probe --db .probe/ledger.db delete --ledger --yes
codex-probe --db .probe/ledger.db delete --watcher --yes
```

## Time Ranges

The ledger is not hardcoded to the last 7 days:

```bash
codex-probe sessions --range today
codex-probe sessions --range yesterday
codex-probe sessions --since 24h
codex-probe sessions --range 3d
codex-probe sessions --range 7d
codex-probe sessions --range 30d
codex-probe sessions --from 2026-06-01 --to 2026-06-23
```

## Sample Data

| File | Purpose |
|---|---|
| `examples/ledger-samples/official-export.csv` | Redacted official-export sample covering exact confidence |
| `examples/ledger-samples/official-export.json` | Redacted official JSON export sample |
| `examples/ledger-samples/official-export.jsonl` | Redacted official JSONL export sample |
| `examples/ledger-samples/official-export-alt.json` | Export sample with non-standard field names |
| `examples/ledger-samples/official-export-alt.mapping.json` | Field mapping sample |
| `examples/ledger-samples/snapshot-delta.json` | Redacted snapshot sample covering high / medium / low confidence |
| `examples/ledger-samples/local-status-snapshots.json` | local_status allowlist example |
| `examples/ledger-samples/local-codex/` | Synthetic Codex rollout sample for local history import |
| `examples/reports/ledger/` | v0.5.0 ledger sample reports |
| `examples/status-samples/` | Earlier `/status` sample library |
| `examples/risky-skill.md` | Risky Skill / output inspection sample |

Samples should be redacted and should not contain real cookies, tokens, emails, phone numbers, or private user paths.

## Codex Desktop Usage

The friendliest path is to open this repository folder in the **Codex desktop app** and say:

```text
Please use BLCaptain Codex Probe CLI to open the local Codex token session ledger, analyze which session consumed the most tokens in the last 7 days, and generate reports.

Requirements:
1. If it is not installed yet, create a local virtual environment in this project and install it.
2. Use examples/ledger-samples/official-export.csv, official-export.jsonl, snapshot-delta.json, and the local-codex synthetic rollout.
3. Generate reports/ledger/sessions.md, session-readme-release.md, ledger-report.md, privacy-report.md, and dashboard.html.
4. Tell me the highest-token session, key risks, and whether I should continue, downgrade, or stop.
5. Do not upload any data. Do not read browser cookies, tokens, keychains, system credentials, or chat content.
```

More copyable prompts: [Codex desktop prompts](docs/CODEX_DESKTOP_PROMPT.md).

## Existing Workflow: `/status` Usage Check

If you only want to analyze one `/status` output:

```bash
codex-probe --db .probe/demo.db doctor \
  --status examples/status-codex-desktop.txt \
  --skill examples/risky-skill.md \
  --budget-tokens 100000 \
  --out-dir reports/doctor
```

Or generate only a usage report:

```bash
codex-probe --db .probe/demo.db import \
  --status examples/status-codex-desktop.txt \
  --goal "Generate delivery report"

codex-probe --db .probe/demo.db usage-report \
  --budget-tokens 100000 \
  --out reports/usage-report.md
```

## Existing Workflow: Skill / Output Inspection

```bash
codex-probe --db .probe/demo.db skill-lint \
  examples/risky-skill.md \
  --out reports/skill-lint-report.md
```

The inspection checks:

- AI-smell and template-like wording.
- Risky plugin-related claims, bypass language, account sharing, or billing avoidance.
- Missing acceptance criteria.
- Missing privacy and deletion boundaries.
- API keys, cookies, tokens, emails, phone numbers, and similar sensitive data.

## Data and Privacy

- Does not log in to OpenAI or Codex.
- Does not read browser cookies, tokens, keychains, or system credentials.
- Does not proxy, intercept, or modify Codex requests.
- Does not read chat content.
- Does not upload data to the cloud.
- Does not start background collection by default; `watch start` or the macOS LaunchAgent must be explicit.
- Local history reads only allowlisted token-usage fields from Codex rollout JSONL; it skips chat content, prompts, assistant outputs, and tool arguments.
- Full private paths are hidden by default and stored only as hashes.
- `dashboard` writes a local HTML file and does not start a cloud service.
- `delete --ledger --yes` deletes ledger business data while keeping audit logs without sensitive raw content.
- `delete --watcher --yes` deletes watcher state, logs, and control files.
- Does not promise savings, unlimited quota, or replacement of the official dashboard or bill.

See [Privacy and Security](docs/PRIVACY_SECURITY.md).

## Local Commands

Run tests:

```bash
PYTHONPATH=src python3 -m unittest discover -s tests
```

Compile check:

```bash
python3 -m compileall src tests scripts/run_acceptance.py
```

End-to-end acceptance:

```bash
python3 scripts/run_acceptance.py
```

The acceptance script writes local evidence:

```text
acceptance-artifacts/<timestamp>/
├── commands.md
├── commands.json
├── usage-report.md
├── skill-lint-report.md
├── doctor/
├── ledger-sessions.md
├── ledger-session-report.md
├── ledger-report.md
├── ledger-privacy-report.md
├── ledger-dashboard.html
└── probe.db
```

`acceptance-artifacts/` is ignored by Git and should not be committed.

## Directory Structure

```text
BLCaptain-Codex-Probe-CLI/
├── assets/screenshots/               # README screenshots
├── examples/ledger-samples/          # Redacted ledger samples
├── examples/reports/ledger/          # Ledger sample reports
├── README.md                         # Chinese README
├── README.en.md                      # English README
├── CHANGELOG.md                      # Changelog
├── LICENSE                           # MIT License
├── pyproject.toml                    # Python package and CLI entry points
├── docs/
│   ├── CODEX_DESKTOP_PROMPT.md       # Codex desktop prompts
│   ├── MACOS_WATCHER.md              # macOS LaunchAgent watcher entry
│   ├── PRIVACY_SECURITY.md           # Privacy and security boundaries
│   ├── RELEASE_CHECKLIST.md          # Release checklist
│   └── SOCIAL_POSTS.md               # Social post drafts
├── scripts/
│   ├── macos/                        # macOS LaunchAgent install/uninstall scripts
│   └── run_acceptance.py             # End-to-end acceptance script
├── src/codex_usage_skill_probe/       # CLI source code
└── tests/                            # Unit and end-to-end tests
```

## Release Acceptance

Before v0.5.0 release:

- The project can be installed from a clean environment with `python -m pip install .`.
- `codex-probe --version` returns `0.5.0`.
- The CLI can import official CSV / JSON / JSONL exports, mapping samples, local synthetic rollout history, and snapshot samples.
- The CLI can run `sources doctor --deep`, `ledger inspect-export`, `ledger map-export`, and `ledger import-history --dry-run`.
- The CLI can run `watch once/start/status/logs/stop` and `delete --watcher --yes`.
- The CLI can generate session ranking, single-session report, ledger report, privacy audit report, and local HTML dashboard.
- Every session has a source and `exact/high/medium/low` confidence.
- The CLI can delete local ledger business data.
- Reports do not leak full API keys, cookies, tokens, emails, phone numbers, or private user paths.
- README, English README, CHANGELOG, CI, privacy docs, and release checklist are present.

## Roadmap

- Expand the redacted rollout sample library and keep calibrating across Codex versions.
- Add project-level aggregation and weekly reports.
- Add HTML / JSON report schema snapshot tests.
- Add finer-grained Skill risk rules.
- Provide lighter installation options such as Homebrew or uvx.
- Evaluate a menu bar app or desktop component without reading login state.

## FAQ

**Q: Is this a Codex Skill?**

A: No. It is a CLI. It can inspect Skills or output text, but it is not an Agent-loaded Skill instruction package.

**Q: Does it require an OpenAI API key?**

A: No. It only analyzes local files and samples explicitly provided by the user.

**Q: Can it automatically read token usage from my historical sessions?**

A: If your local Codex structured rollout logs contain token-usage fields, use `ledger import-history --source local-codex` to import them locally. It only reads allowlisted fields and does not read chat content, prompts, assistant outputs, cookies, tokens, keychains, or system credentials. If the logs do not contain token fields, it will not invent usage.

**Q: Can it read my official bill directly?**

A: It does not log in and read billing pages. It supports user-provided official export files and token fields found in local Codex structured logs. It does not read login state, browser cookies, or hidden official dashboard data.

**Q: Can it know the exact token usage of every real session?**

A: Only when the source itself provides session ID and token data. Snapshots and global quota movement are labeled `high`, `medium`, or `low`.

**Q: Can it guarantee lower cost?**

A: No. It locates consumption, explains risk, and suggests downgrade or stop actions. Final decisions remain yours.

**Q: Does it store my data?**

A: It stores data only in the local SQLite database path you provide. Use `delete --ledger --yes` to delete ledger business data, or `delete --all --yes` for the earlier business tables.

## Author

Created and maintained independently by **BLCaptain**.

- GitHub: [@dososo](https://github.com/dososo)
- X / Twitter: [@thinkszyg](https://x.com/thinkszyg)
- Email: [blteam2026@outlook.com](mailto:blteam2026@outlook.com)
- Maintainer of the open Chinese traditional pattern archive: [wenyang.net](https://wenyang.net)

If this project helps you, stars, shares, and conversations on X are welcome.

## License

MIT License. See [LICENSE](LICENSE).
