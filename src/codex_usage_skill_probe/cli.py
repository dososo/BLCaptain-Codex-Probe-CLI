"""Command line interface."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import __version__
from . import errors
from .models import ImportBatch
from .reports import (
    findings_to_json,
    render_doctor_markdown,
    render_skill_markdown,
    render_usage_markdown,
    write_json,
    write_text,
)
from .skill_linter import lint_file
from .storage import Store
from .usage_analyzer import analyze_usage, build_decision_card
from .usage_parser import load_manual_json, load_status_file


DEFAULT_DB = Path(".probe/probe.db")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="codex-probe",
        description="Local read-only Codex usage governance and Skill output inspection CLI.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB, help="SQLite database path. Default: .probe/probe.db")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")

    sub = parser.add_subparsers(dest="command", required=True)

    import_cmd = sub.add_parser("import", help="Import user-provided usage data.")
    source = import_cmd.add_mutually_exclusive_group(required=True)
    source.add_argument("--status", type=Path, help="Path to a Codex /status text export.")
    source.add_argument("--manual-json", type=Path, help="Path to a manual usage JSON file.")
    import_cmd.add_argument("--goal", default="", help="Optional task goal.")
    import_cmd.add_argument("--model", default="", help="Optional model hint.")

    usage_cmd = sub.add_parser("usage-report", help="Generate a task-level usage report.")
    usage_cmd.add_argument("--task-id", default=None, help="Task id. Defaults to latest task.")
    usage_cmd.add_argument("--budget-tokens", type=int, default=None, help="Token budget threshold.")
    usage_cmd.add_argument("--budget-credits", type=float, default=None, help="Credit budget threshold.")
    usage_cmd.add_argument("--out", type=Path, default=Path("reports/usage-report.md"), help="Report output path.")

    doctor_cmd = sub.add_parser("doctor", help="Run usage report and Skill inspection in one local check.")
    doctor_source = doctor_cmd.add_mutually_exclusive_group(required=False)
    doctor_source.add_argument("--status", type=Path, help="Path to a Codex /status text export.")
    doctor_source.add_argument("--manual-json", type=Path, help="Path to a manual usage JSON file.")
    doctor_cmd.add_argument("--skill", type=Path, default=None, help="Skill, prompt, or output file to inspect.")
    doctor_cmd.add_argument("--goal", default="", help="Optional task goal.")
    doctor_cmd.add_argument("--model", default="", help="Optional model hint.")
    doctor_cmd.add_argument("--budget-tokens", type=int, default=None, help="Token budget threshold.")
    doctor_cmd.add_argument("--budget-credits", type=float, default=None, help="Credit budget threshold.")
    doctor_cmd.add_argument("--out-dir", type=Path, default=Path("reports/doctor"), help="Directory for doctor reports.")

    lint_cmd = sub.add_parser("skill-lint", help="Inspect a Skill, prompt, or output file.")
    lint_cmd.add_argument("path", type=Path, help="Text file to inspect.")
    lint_cmd.add_argument("--out", type=Path, default=Path("reports/skill-lint-report.md"), help="Report output path.")

    delete_cmd = sub.add_parser("delete", help="Delete local business data.")
    delete_cmd.add_argument("--all", action="store_true", help="Delete all local business data.")
    delete_cmd.add_argument("--yes", action="store_true", help="Confirm deletion without prompting.")

    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    store = Store(args.db)
    try:
        if args.command == "import":
            cmd_import(args, store)
        elif args.command == "usage-report":
            cmd_usage_report(args, store)
        elif args.command == "skill-lint":
            cmd_skill_lint(args, store)
        elif args.command == "doctor":
            cmd_doctor(args, store)
        elif args.command == "delete":
            cmd_delete(args, store)
        else:
            fail("UNKNOWN_COMMAND", f"Unsupported command: {args.command}", args.json)
    finally:
        store.close()


def cmd_import(args: argparse.Namespace, store: Store) -> None:
    try:
        if args.status:
            batch, record = load_status_file(args.status, goal=args.goal, model_hint=args.model)
        else:
            batch, record = load_manual_json(args.manual_json, goal=args.goal, model_hint=args.model)
    except FileNotFoundError as exc:
        fail(errors.INVALID_SOURCE, str(exc), args.json)
    except (json.JSONDecodeError, ValueError) as exc:
        fail(errors.PARSE_FAILED, str(exc), args.json)

    store.add_import(batch)
    if batch.parsed_count:
        store.add_usage_record(record)
    store.event("import_completed", {"source_type": batch.source_type, "parsed_count": batch.parsed_count})
    store.conn.commit()

    payload = {
        "ok": bool(batch.parsed_count),
        "import_id": batch.id,
        "task_id": record.task_id,
        "parsed_count": batch.parsed_count,
        "status": record.status,
    }
    print_payload(payload, args.json)
    if not batch.parsed_count:
        sys.exit(1)


def cmd_usage_report(args: argparse.Namespace, store: Store) -> None:
    record = store.usage_record(args.task_id)
    if record is None:
        fail(errors.NO_USAGE_DATA, "No local usage data. Import a /status text or manual JSON first.", args.json)

    findings = analyze_usage(record, budget_tokens=args.budget_tokens, budget_credits=args.budget_credits)
    store.add_findings(findings)
    report = render_usage_markdown(record, findings)
    write_text(args.out, report)
    store.add_report("usage_report", str(args.out), f"{len(findings)} findings")

    payload = {
        "ok": True,
        "task_id": record.task_id,
        "report_path": str(args.out),
        "findings": findings_to_json(findings),
    }
    print_payload(payload, args.json)


def cmd_skill_lint(args: argparse.Namespace, store: Store) -> None:
    if not args.path.exists():
        fail(errors.INVALID_SOURCE, f"File not found: {args.path}", args.json)
    batch, findings = lint_file(args.path)
    store.add_import(batch)
    store.add_findings(findings)
    report = render_skill_markdown(findings)
    write_text(args.out, report)
    store.add_report("skill_lint", str(args.out), f"{len(findings)} findings")
    store.event("skill_lint_generated", {"risk_score": risk_score(findings), "finding_count": len(findings)})
    store.conn.commit()

    payload = {
        "ok": True,
        "import_id": batch.id,
        "report_path": str(args.out),
        "risk_score": risk_score(findings),
        "findings": findings_to_json(findings),
    }
    print_payload(payload, args.json)


def cmd_doctor(args: argparse.Namespace, store: Store) -> None:
    if not args.status and not args.manual_json and not args.skill:
        fail(errors.INVALID_SOURCE, "Provide --status, --manual-json, or --skill for doctor.", args.json)

    record = None
    usage_findings = []
    usage_report_path = None
    skill_findings = []
    skill_report_path = None

    if args.status or args.manual_json:
        try:
            if args.status:
                batch, record = load_status_file(args.status, goal=args.goal, model_hint=args.model)
            else:
                batch, record = load_manual_json(args.manual_json, goal=args.goal, model_hint=args.model)
        except FileNotFoundError as exc:
            fail(errors.INVALID_SOURCE, str(exc), args.json)
        except (json.JSONDecodeError, ValueError) as exc:
            fail(errors.PARSE_FAILED, str(exc), args.json)

        store.add_import(batch)
        if not batch.parsed_count:
            fail(errors.PARSE_FAILED, "No usage fields parsed from the provided source.", args.json)
        store.add_usage_record(record)
        usage_findings = analyze_usage(record, budget_tokens=args.budget_tokens, budget_credits=args.budget_credits)
        store.add_findings(usage_findings)
        usage_report_path = args.out_dir / "usage-report.md"
        write_text(usage_report_path, render_usage_markdown(record, usage_findings))
        store.add_report("usage_report", str(usage_report_path), f"{len(usage_findings)} findings")

    if args.skill:
        if not args.skill.exists():
            fail(errors.INVALID_SOURCE, f"File not found: {args.skill}", args.json)
        batch, skill_findings = lint_file(args.skill)
        store.add_import(batch)
        store.add_findings(skill_findings)
        skill_report_path = args.out_dir / "skill-lint-report.md"
        write_text(skill_report_path, render_skill_markdown(skill_findings))
        store.add_report("skill_lint", str(skill_report_path), f"{len(skill_findings)} findings")

    doctor_report_path = args.out_dir / "doctor-report.md"
    write_text(
        doctor_report_path,
        render_doctor_markdown(record, usage_findings, skill_findings, usage_report_path, skill_report_path),
    )
    store.add_report("doctor", str(doctor_report_path), "doctor summary")
    store.event("doctor_generated", {"out_dir": str(args.out_dir)})
    store.conn.commit()

    payload = {
        "ok": True,
        "doctor_report_path": str(doctor_report_path),
        "usage_report_path": str(usage_report_path) if usage_report_path else None,
        "skill_report_path": str(skill_report_path) if skill_report_path else None,
        "decision": build_decision_card(record, usage_findings) if record else None,
        "usage_findings": findings_to_json(usage_findings),
        "skill_findings": findings_to_json(skill_findings),
    }
    print_payload(payload, args.json)


def cmd_delete(args: argparse.Namespace, store: Store) -> None:
    if not args.all:
        fail(errors.DELETE_FAILED, "Only --all is supported in the current release.", args.json)
    if not args.yes:
        fail(errors.DELETE_FAILED, "Refusing to delete without --yes confirmation.", args.json)
    deleted = store.delete_business_data()
    print_payload({"ok": True, "deleted_count": deleted}, args.json)


def risk_score(findings: list[object]) -> int:
    score = 0
    for finding in findings:
        severity = getattr(finding, "severity", "info")
        score += {"info": 5, "medium": 25, "high": 45}.get(severity, 10)
    return min(100, score)


def print_payload(payload: dict[str, object], as_json: bool) -> None:
    if as_json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return
    for key, value in payload.items():
        if key == "findings":
            print(f"{key}: {len(value) if isinstance(value, list) else value}")
        else:
            print(f"{key}: {value}")


def fail(code: str, message: str, as_json: bool) -> None:
    payload = {"ok": False, "error": {"code": code, "message": message}}
    if as_json:
        print(json.dumps(payload, ensure_ascii=False, indent=2), file=sys.stderr)
    else:
        print(f"{code}: {message}", file=sys.stderr)
    sys.exit(1)
