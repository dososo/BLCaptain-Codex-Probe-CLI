#!/usr/bin/env python3
"""Run local acceptance commands and save evidence artifacts."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    env = os.environ.copy()
    src_path = str(ROOT / "src")
    env["PYTHONPATH"] = src_path if not env.get("PYTHONPATH") else f"{src_path}{os.pathsep}{env['PYTHONPATH']}"

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_dir = ROOT / "acceptance-artifacts" / stamp
    out_dir.mkdir(parents=True, exist_ok=True)
    db = out_dir / "probe.db"
    usage_report = out_dir / "usage-report.md"
    skill_report = out_dir / "skill-lint-report.md"
    doctor_dir = out_dir / "doctor"
    after_delete = out_dir / "after-delete.md"
    ledger_sessions = out_dir / "ledger-sessions.md"
    ledger_session_report = out_dir / "ledger-session-report.md"
    ledger_report = out_dir / "ledger-report.md"
    ledger_privacy_report = out_dir / "ledger-privacy-report.md"
    ledger_dashboard = out_dir / "ledger-dashboard.html"
    mapping_json = out_dir / "official-export-alt.mapping.json"

    commands = [
        {
            "name": "import_status",
            "cmd": [
                sys.executable,
                "-m",
                "codex_usage_skill_probe",
                "--db",
                str(db),
                "--json",
                "import",
                "--status",
                "examples/status.txt",
                "--goal",
                "验收：生成任务级用量报告",
            ],
            "expect": 0,
        },
        {
            "name": "usage_report",
            "cmd": [
                sys.executable,
                "-m",
                "codex_usage_skill_probe",
                "--db",
                str(db),
                "--json",
                "usage-report",
                "--budget-tokens",
                "100000",
                "--out",
                str(usage_report),
            ],
            "expect": 0,
        },
        {
            "name": "skill_lint",
            "cmd": [
                sys.executable,
                "-m",
                "codex_usage_skill_probe",
                "--db",
                str(db),
                "--json",
                "skill-lint",
                "examples/risky-skill.md",
                "--out",
                str(skill_report),
            ],
            "expect": 0,
        },
        {
            "name": "doctor",
            "cmd": [
                sys.executable,
                "-m",
                "codex_usage_skill_probe",
                "--db",
                str(db),
                "--json",
                "doctor",
                "--status",
                "examples/status-codex-desktop.txt",
                "--skill",
                "examples/risky-skill.md",
                "--budget-tokens",
                "100000",
                "--out-dir",
                str(doctor_dir),
            ],
            "expect": 0,
            "must_contain": "doctor-report.md",
        },
        {
            "name": "ledger_init",
            "cmd": [
                sys.executable,
                "-m",
                "codex_usage_skill_probe",
                "--db",
                str(db),
                "--json",
                "ledger",
                "init",
            ],
            "expect": 0,
            "must_contain": "不读取浏览器 cookie",
        },
        {
            "name": "sources_doctor",
            "cmd": [
                sys.executable,
                "-m",
                "codex_usage_skill_probe",
                "--db",
                str(db),
                "--json",
                "sources",
                "doctor",
            ],
            "expect": 0,
            "must_contain": "official_export",
        },
        {
            "name": "sources_doctor_deep",
            "cmd": [
                sys.executable,
                "-m",
                "codex_usage_skill_probe",
                "--db",
                str(db),
                "--json",
                "sources",
                "doctor",
                "--deep",
            ],
            "expect": 0,
            "must_contain": "local_codex_rollout",
        },
        {
            "name": "ledger_inspect_export_jsonl",
            "cmd": [
                sys.executable,
                "-m",
                "codex_usage_skill_probe",
                "--db",
                str(db),
                "--json",
                "ledger",
                "inspect-export",
                "examples/ledger-samples/official-export.jsonl",
            ],
            "expect": 0,
            "must_contain": '"format": "jsonl"',
        },
        {
            "name": "ledger_map_export",
            "cmd": [
                sys.executable,
                "-m",
                "codex_usage_skill_probe",
                "--db",
                str(db),
                "--json",
                "ledger",
                "map-export",
                "examples/ledger-samples/official-export-alt.json",
                "--out",
                str(mapping_json),
            ],
            "expect": 0,
            "must_contain": "mapping_path",
        },
        {
            "name": "ledger_import_official",
            "cmd": [
                sys.executable,
                "-m",
                "codex_usage_skill_probe",
                "--db",
                str(db),
                "--json",
                "ledger",
                "import",
                "--official-export",
                "examples/ledger-samples/official-export.csv",
            ],
            "expect": 0,
            "must_contain": "official_export",
        },
        {
            "name": "ledger_import_official_jsonl",
            "cmd": [
                sys.executable,
                "-m",
                "codex_usage_skill_probe",
                "--db",
                str(db),
                "--json",
                "ledger",
                "import",
                "--official-export",
                "examples/ledger-samples/official-export.jsonl",
            ],
            "expect": 0,
            "must_contain": "official_export",
        },
        {
            "name": "ledger_import_official_mapping",
            "cmd": [
                sys.executable,
                "-m",
                "codex_usage_skill_probe",
                "--db",
                str(db),
                "--json",
                "ledger",
                "import",
                "--official-export",
                "examples/ledger-samples/official-export-alt.json",
                "--mapping",
                "examples/ledger-samples/official-export-alt.mapping.json",
            ],
            "expect": 0,
            "must_contain": "official_export",
        },
        {
            "name": "ledger_import_snapshot",
            "cmd": [
                sys.executable,
                "-m",
                "codex_usage_skill_probe",
                "--db",
                str(db),
                "--json",
                "ledger",
                "import",
                "--snapshot",
                "examples/ledger-samples/snapshot-delta.json",
            ],
            "expect": 0,
            "must_contain": "snapshot_delta",
        },
        {
            "name": "ledger_import_history_dry_run",
            "cmd": [
                sys.executable,
                "-m",
                "codex_usage_skill_probe",
                "--db",
                str(db),
                "--json",
                "ledger",
                "import-history",
                "--dry-run",
                "--source",
                "local-codex",
                "--root",
                "examples/ledger-samples/local-codex",
            ],
            "expect": 0,
            "must_contain": '"wrote": false',
        },
        {
            "name": "ledger_import_history",
            "cmd": [
                sys.executable,
                "-m",
                "codex_usage_skill_probe",
                "--db",
                str(db),
                "--json",
                "ledger",
                "import-history",
                "--source",
                "local-codex",
                "--root",
                "examples/ledger-samples/local-codex",
            ],
            "expect": 0,
            "must_contain": "imported_snapshots",
        },
        {
            "name": "watch_once",
            "cmd": [
                sys.executable,
                "-m",
                "codex_usage_skill_probe",
                "--db",
                str(db),
                "--json",
                "watch",
                "once",
                "--root",
                "examples/ledger-samples/local-codex",
            ],
            "expect": 0,
            "must_contain": "local_codex_rollout",
        },
        {
            "name": "watch_start",
            "cmd": [
                sys.executable,
                "-m",
                "codex_usage_skill_probe",
                "--db",
                str(db),
                "--json",
                "watch",
                "start",
                "--interval-seconds",
                "1",
                "--root",
                "examples/ledger-samples/local-codex",
            ],
            "expect": 0,
            "must_contain": "running",
        },
        {
            "name": "watch_status",
            "cmd": [
                sys.executable,
                "-m",
                "codex_usage_skill_probe",
                "--db",
                str(db),
                "--json",
                "watch",
                "status",
            ],
            "expect": 0,
            "must_contain": "pid",
        },
        {
            "name": "watch_logs",
            "cmd": [
                sys.executable,
                "-m",
                "codex_usage_skill_probe",
                "--db",
                str(db),
                "--json",
                "watch",
                "logs",
            ],
            "expect": 0,
            "must_contain": "log_path",
        },
        {
            "name": "watch_stop",
            "cmd": [
                sys.executable,
                "-m",
                "codex_usage_skill_probe",
                "--db",
                str(db),
                "--json",
                "watch",
                "stop",
            ],
            "expect": 0,
            "must_contain": "stopped",
        },
        {
            "name": "ledger_sessions",
            "cmd": [
                sys.executable,
                "-m",
                "codex_usage_skill_probe",
                "--db",
                str(db),
                "--json",
                "sessions",
                "--range",
                "7d",
                "--out",
                str(ledger_sessions),
            ],
            "expect": 0,
            "must_contain": "session_readme_release",
        },
        {
            "name": "ledger_session_report",
            "cmd": [
                sys.executable,
                "-m",
                "codex_usage_skill_probe",
                "--db",
                str(db),
                "--json",
                "session-report",
                "session_readme_release",
                "--out",
                str(ledger_session_report),
            ],
            "expect": 0,
            "must_contain": "session_readme_release",
        },
        {
            "name": "ledger_report",
            "cmd": [
                sys.executable,
                "-m",
                "codex_usage_skill_probe",
                "--db",
                str(db),
                "--json",
                "ledger-report",
                "--range",
                "30d",
                "--out",
                str(ledger_report),
            ],
            "expect": 0,
            "must_contain": "ledger-report.md",
        },
        {
            "name": "ledger_privacy",
            "cmd": [
                sys.executable,
                "-m",
                "codex_usage_skill_probe",
                "--db",
                str(db),
                "--json",
                "privacy",
                "inspect",
                "--out",
                str(ledger_privacy_report),
            ],
            "expect": 0,
            "must_contain": "不读取浏览器 cookie",
        },
        {
            "name": "ledger_dashboard",
            "cmd": [
                sys.executable,
                "-m",
                "codex_usage_skill_probe",
                "--db",
                str(db),
                "--json",
                "dashboard",
                "--range",
                "7d",
                "--out",
                str(ledger_dashboard),
            ],
            "expect": 0,
            "must_contain": "ledger-dashboard.html",
        },
        {
            "name": "delete_ledger",
            "cmd": [
                sys.executable,
                "-m",
                "codex_usage_skill_probe",
                "--db",
                str(db),
                "--json",
                "delete",
                "--ledger",
                "--yes",
            ],
            "expect": 0,
            "must_contain": "deleted_count",
        },
        {
            "name": "delete_watcher",
            "cmd": [
                sys.executable,
                "-m",
                "codex_usage_skill_probe",
                "--db",
                str(db),
                "--json",
                "delete",
                "--watcher",
                "--yes",
            ],
            "expect": 0,
            "must_contain": "deleted_count",
        },
        {
            "name": "sessions_after_ledger_delete",
            "cmd": [
                sys.executable,
                "-m",
                "codex_usage_skill_probe",
                "--db",
                str(db),
                "--json",
                "sessions",
                "--range",
                "30d",
            ],
            "expect": 0,
            "must_contain": '"session_count": 0',
        },
        {
            "name": "delete_all",
            "cmd": [
                sys.executable,
                "-m",
                "codex_usage_skill_probe",
                "--db",
                str(db),
                "--json",
                "delete",
                "--all",
                "--yes",
            ],
            "expect": 0,
        },
        {
            "name": "usage_after_delete",
            "cmd": [
                sys.executable,
                "-m",
                "codex_usage_skill_probe",
                "--db",
                str(db),
                "--json",
                "usage-report",
                "--out",
                str(after_delete),
            ],
            "expect": 1,
            "must_contain": "NO_USAGE_DATA",
        },
    ]

    evidence = []
    for item in commands:
        result = subprocess.run(item["cmd"], cwd=ROOT, env=env, text=True, capture_output=True)
        record = {
            "name": item["name"],
            "cmd": item["cmd"],
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }
        evidence.append(record)
        (out_dir / f"{item['name']}.stdout.txt").write_text(result.stdout, encoding="utf-8")
        (out_dir / f"{item['name']}.stderr.txt").write_text(result.stderr, encoding="utf-8")

        if result.returncode != item["expect"]:
            write_summary(out_dir, evidence)
            print(f"acceptance failed: {item['name']} expected {item['expect']} got {result.returncode}", file=sys.stderr)
            return 1
        must = item.get("must_contain")
        if must and must not in (result.stdout + result.stderr):
            write_summary(out_dir, evidence)
            print(f"acceptance failed: {item['name']} missing {must}", file=sys.stderr)
            return 1

    write_summary(out_dir, evidence)
    print(f"acceptance passed: {out_dir}")
    return 0


def write_summary(out_dir: Path, evidence: list[dict[str, object]]) -> None:
    summary_path = out_dir / "commands.md"
    lines = ["# 验收命令证据", ""]
    for record in evidence:
        lines.extend(
            [
                f"## {record['name']}",
                "",
                "```bash",
                " ".join(str(part) for part in record["cmd"]),
                "```",
                "",
                f"退出码：`{record['returncode']}`",
                "",
                "stdout:",
                "",
                "```text",
                str(record["stdout"]).strip(),
                "```",
                "",
                "stderr:",
                "",
                "```text",
                str(record["stderr"]).strip(),
                "```",
                "",
            ]
        )
    summary_path.write_text("\n".join(lines), encoding="utf-8")
    (out_dir / "commands.json").write_text(json.dumps(evidence, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
