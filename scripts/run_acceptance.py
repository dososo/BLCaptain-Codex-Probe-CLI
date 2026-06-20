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
    after_delete = out_dir / "after-delete.md"

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
