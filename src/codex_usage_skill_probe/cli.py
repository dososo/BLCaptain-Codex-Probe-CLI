"""Command line interface."""

from __future__ import annotations

import argparse
import json
import sys
import webbrowser
from datetime import datetime, timedelta, timezone
from pathlib import Path

from . import __version__
from . import errors
from .export_mapping import inspect_export, inspection_payload, write_mapping_template
from .ledger_adapters import import_official_export, import_snapshot_delta
from .ledger_reports import (
    render_dashboard_html,
    render_ledger_report_markdown,
    render_privacy_markdown,
    render_session_detail_markdown,
    render_sessions_markdown,
    render_watch_status_html,
)
from .ledger_storage import (
    add_privacy_audit,
    ledger_summary,
    privacy_audit_rows,
    read_watch_state,
    session_snapshots,
    source_rows,
    write_static_file,
    write_watch_state,
)
from .local_history import collect_redacted_rollout_samples, import_local_history, inspect_local_codex
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
from .source_doctor import deep_local_payload, run_source_doctor, source_doctor_payload
from .storage import Store
from .usage_analyzer import analyze_usage, build_decision_card
from .usage_parser import load_manual_json, load_status_file
from .watcher import collect_once, delete_watcher_files, read_state, run_forever, start_watcher, stop_watcher, watcher_logs


DEFAULT_DB = Path(".probe/probe.db")


def add_range_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--range", default="7d", help="Time range: today, yesterday, 24h, 3d, 7d, 30d.")
    parser.add_argument("--since", default=None, help="Alias range such as 24h or 7d.")
    parser.add_argument("--from", dest="date_from", default=None, help="Start datetime/date, ISO format.")
    parser.add_argument("--to", dest="date_to", default=None, help="End datetime/date, ISO format.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="codex-probe",
        description="Local read-only Codex usage governance and Skill output inspection CLI.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB, help="SQLite database path. Default: .probe/probe.db")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")

    sub = parser.add_subparsers(dest="command", required=True)

    setup_cmd = sub.add_parser("setup", help="Initialize ledger, dry-run local history, generate reports, and open dashboard.")
    add_range_args(setup_cmd)
    setup_cmd.add_argument("--out-dir", type=Path, default=Path("reports/ledger"), help="Report output directory.")
    setup_cmd.add_argument("--root", type=Path, default=None, help="Codex data root. Defaults to ~/.codex.")
    setup_cmd.add_argument("--demo", action="store_true", help="Use repository synthetic samples for a safe first run.")
    setup_cmd.add_argument("--import-history", action="store_true", help="Import local history after dry-run.")
    setup_cmd.add_argument("--limit-files", type=int, default=None)
    setup_cmd.add_argument("--no-open", action="store_true", help="Do not open the generated dashboard.")

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

    sources_cmd = sub.add_parser("sources", help="Inspect safe ledger data sources.")
    sources_sub = sources_cmd.add_subparsers(dest="sources_command", required=True)
    sources_doctor = sources_sub.add_parser("doctor", help="Detect available safe data sources without reading chat content.")
    sources_doctor.add_argument("--deep", action="store_true", help="Safely inspect local Codex rollout schema counts.")

    ledger_cmd = sub.add_parser("ledger", help="Initialize and import session-level token ledger data.")
    ledger_sub = ledger_cmd.add_subparsers(dest="ledger_command", required=True)
    ledger_sub.add_parser("init", help="Initialize local ledger schema and privacy audit.")
    ledger_import = ledger_sub.add_parser("import", help="Import user-provided ledger data.")
    ledger_source = ledger_import.add_mutually_exclusive_group(required=True)
    ledger_source.add_argument("--official-export", type=Path, help="User-provided official CSV/JSON export.")
    ledger_source.add_argument("--snapshot", type=Path, help="User-provided local snapshot CSV/JSON.")
    ledger_import.add_argument("--mapping", type=Path, default=None, help="Optional mapping JSON for official export fields.")
    inspect_cmd = ledger_sub.add_parser("inspect-export", help="Inspect official CSV/JSON/JSONL export fields.")
    inspect_cmd.add_argument("file", type=Path)
    inspect_cmd.add_argument("--mapping", type=Path, default=None)
    map_cmd = ledger_sub.add_parser("map-export", help="Generate an editable official export mapping JSON.")
    map_cmd.add_argument("file", type=Path)
    map_cmd.add_argument("--out", type=Path, required=True)
    history_cmd = ledger_sub.add_parser("import-history", help="Import local Codex rollout token history.")
    history_cmd.add_argument("--source", choices=["local-codex"], default="local-codex")
    history_cmd.add_argument("--root", type=Path, default=None, help="Codex data root. Defaults to ~/.codex.")
    history_cmd.add_argument("--dry-run", action="store_true", help="Preview import without writing ledger data.")
    history_cmd.add_argument("--limit-files", type=int, default=None, help="Only scan the newest N rollout files.")

    watch_cmd = sub.add_parser("watch", help="Control explicit local ledger watcher state.")
    watch_sub = watch_cmd.add_subparsers(dest="watch_command", required=True)
    watch_once = watch_sub.add_parser("once", help="Run one safe local history collection.")
    watch_once.add_argument("--root", type=Path, default=None)
    watch_once.add_argument("--limit-files", type=int, default=None)
    watch_start = watch_sub.add_parser("start", help="Start a background local watcher.")
    watch_start.add_argument("--interval-seconds", type=int, default=60, help="Capture interval.")
    watch_start.add_argument("--root", type=Path, default=None)
    watch_start.add_argument("--limit-files", type=int, default=None)
    watch_sub.add_parser("status", help="Show watcher state.")
    watch_logs = watch_sub.add_parser("logs", help="Show watcher logs.")
    watch_logs.add_argument("--limit", type=int, default=80)
    watch_status_page = watch_sub.add_parser("status-page", help="Generate a friendly local watcher status page.")
    add_range_args(watch_status_page)
    watch_status_page.add_argument("--out", type=Path, default=Path("reports/ledger/watch-status.html"))
    watch_status_page.add_argument("--open", action="store_true", help="Open the generated status page.")
    watch_sub.add_parser("stop", help="Stop watcher state.")
    watch_run = watch_sub.add_parser("_run", help=argparse.SUPPRESS)
    watch_run.add_argument("--interval-seconds", type=int, default=60)
    watch_run.add_argument("--root", type=Path, default=None)
    watch_run.add_argument("--limit-files", type=int, default=None)

    sessions_cmd = sub.add_parser("sessions", help="Rank Codex sessions by token delta.")
    add_range_args(sessions_cmd)
    sessions_cmd.add_argument("--min-confidence", choices=["low", "medium", "high", "exact"], default=None)
    sessions_cmd.add_argument("--out", type=Path, default=None, help="Optional Markdown report path.")

    session_report = sub.add_parser("session-report", help="Export one session detail report.")
    session_report.add_argument("session_id", help="Ledger session id.")
    session_report.add_argument("--out", type=Path, default=Path("reports/ledger/session-report.md"))

    ledger_report = sub.add_parser("ledger-report", help="Export a ledger summary report.")
    add_range_args(ledger_report)
    ledger_report.add_argument("--out", type=Path, default=Path("reports/ledger/ledger-report.md"))

    privacy_cmd = sub.add_parser("privacy", help="Inspect local privacy boundaries.")
    privacy_sub = privacy_cmd.add_subparsers(dest="privacy_command", required=True)
    privacy_inspect = privacy_sub.add_parser("inspect", help="Show enabled sources and privacy audit logs.")
    privacy_inspect.add_argument("--out", type=Path, default=Path("reports/ledger/privacy-report.md"))

    dashboard_cmd = sub.add_parser("dashboard", help="Generate a local HTML dashboard.")
    add_range_args(dashboard_cmd)
    dashboard_cmd.add_argument("--out", type=Path, default=Path("reports/ledger/dashboard.html"))
    dashboard_cmd.add_argument("--open", action="store_true", help="Open the generated dashboard.")

    samples_cmd = sub.add_parser("samples", help="Collect redacted calibration samples.")
    samples_sub = samples_cmd.add_subparsers(dest="samples_command", required=True)
    collect_cmd = samples_sub.add_parser("collect-rollout", help="Write redacted rollout calibration samples.")
    collect_cmd.add_argument("--root", type=Path, default=None)
    collect_cmd.add_argument("--out", type=Path, default=Path("reports/ledger/redacted-rollout-samples.jsonl"))
    collect_cmd.add_argument("--limit-files", type=int, default=40)
    collect_cmd.add_argument("--max-records", type=int, default=80)

    delete_cmd = sub.add_parser("delete", help="Delete local business data.")
    delete_cmd.add_argument("--all", action="store_true", help="Delete all local business data.")
    delete_cmd.add_argument("--ledger", action="store_true", help="Delete local ledger business data.")
    delete_cmd.add_argument("--watcher", action="store_true", help="Delete watcher state, lock, stop flag, and logs.")
    delete_cmd.add_argument("--yes", action="store_true", help="Confirm deletion without prompting.")

    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    store = Store(args.db)
    try:
        if args.command == "import":
            cmd_import(args, store)
        elif args.command == "setup":
            cmd_setup(args, store)
        elif args.command == "usage-report":
            cmd_usage_report(args, store)
        elif args.command == "skill-lint":
            cmd_skill_lint(args, store)
        elif args.command == "doctor":
            cmd_doctor(args, store)
        elif args.command == "sources":
            cmd_sources(args, store)
        elif args.command == "ledger":
            cmd_ledger(args, store)
        elif args.command == "watch":
            cmd_watch(args, store)
        elif args.command == "sessions":
            cmd_sessions(args, store)
        elif args.command == "session-report":
            cmd_session_report(args, store)
        elif args.command == "ledger-report":
            cmd_ledger_report(args, store)
        elif args.command == "privacy":
            cmd_privacy(args, store)
        elif args.command == "dashboard":
            cmd_dashboard(args, store)
        elif args.command == "samples":
            cmd_samples(args, store)
        elif args.command == "delete":
            cmd_delete(args, store)
        else:
            fail("UNKNOWN_COMMAND", f"Unsupported command: {args.command}", args.json)
    finally:
        store.close()


def cmd_setup(args: argparse.Namespace, store: Store) -> None:
    root = args.root
    if args.demo and root is None:
        root = Path("examples/ledger-samples/local-codex")
    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    range_label, start, end = resolve_range(args)

    local_summary = inspect_local_codex(root, limit_files=args.limit_files)
    sources = run_source_doctor(store.conn, Path.cwd(), deep=True, local_codex=local_summary)
    add_privacy_audit(
        store.conn,
        "setup_initialized",
        {"db_name": store.db_path.name, "demo": args.demo, "local_codex_records": local_summary.importable_record_count},
    )
    store.conn.commit()
    dry_run = import_local_history(store.conn, root=root, dry_run=True, limit_files=args.limit_files)
    imports: list[dict[str, object]] = []

    if args.demo:
        imports.extend(import_demo_samples(store))
        imports.append(import_local_history(store.conn, root=root, dry_run=False, limit_files=args.limit_files))
    elif args.import_history:
        imports.append(import_local_history(store.conn, root=root, dry_run=False, limit_files=args.limit_files))

    sessions = ledger_summary(store.conn, start=start, end=end)
    sessions_path = out_dir / "sessions.md"
    ledger_path = out_dir / "ledger-report.md"
    privacy_path = out_dir / "privacy-report.md"
    dashboard_path = out_dir / "dashboard.html"
    status_path = out_dir / "watch-status.html"
    write_text(sessions_path, render_sessions_markdown(sessions, range_label))
    write_text(ledger_path, render_ledger_report_markdown(sessions, range_label))
    write_text(privacy_path, render_privacy_markdown(source_rows(store.conn), privacy_audit_rows(store.conn)))
    write_static_file(dashboard_path, render_dashboard_html(sessions, range_label))
    write_static_file(status_path, render_watch_status_html(read_state(store.db_path), watcher_logs(store.db_path)["lines"], sessions))
    store.add_report("setup_dashboard", str(dashboard_path), f"{len(sessions)} sessions")
    store.conn.commit()

    if not args.no_open:
        open_local_file(dashboard_path)

    payload = {
        "ok": True,
        "db_path": str(store.db_path),
        "range": range_label,
        "demo": args.demo,
        "dry_run": dry_run,
        "imports": imports,
        "sources": source_doctor_payload(sources, deep=True),
        "reports": {
            "sessions": str(sessions_path),
            "ledger": str(ledger_path),
            "privacy": str(privacy_path),
            "dashboard": str(dashboard_path),
            "watch_status": str(status_path),
        },
        "opened": not args.no_open,
    }
    print_payload(payload, args.json)


def import_demo_samples(store: Store) -> list[dict[str, object]]:
    sample_dir = Path("examples/ledger-samples")
    imports: list[dict[str, object]] = []
    official_csv = sample_dir / "official-export.csv"
    official_jsonl = sample_dir / "official-export.jsonl"
    alt_json = sample_dir / "official-export-alt.json"
    alt_mapping = sample_dir / "official-export-alt.mapping.json"
    snapshot = sample_dir / "snapshot-delta.json"
    if official_csv.exists():
        imports.append({"source_type": "official_export", **import_official_export(store.conn, official_csv)})
    if official_jsonl.exists():
        imports.append({"source_type": "official_export", **import_official_export(store.conn, official_jsonl)})
    if alt_json.exists() and alt_mapping.exists():
        imports.append({"source_type": "official_export", **import_official_export(store.conn, alt_json, mapping_path=alt_mapping)})
    if snapshot.exists():
        imports.append({"source_type": "snapshot_delta", **import_snapshot_delta(store.conn, snapshot)})
    return imports


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


def cmd_sources(args: argparse.Namespace, store: Store) -> None:
    if args.sources_command != "doctor":
        fail("UNKNOWN_COMMAND", f"Unsupported sources command: {args.sources_command}", args.json)
    local_summary = inspect_local_codex(limit_files=40) if args.deep else None
    results = run_source_doctor(store.conn, Path.cwd(), deep=args.deep, local_codex=local_summary)
    payload = source_doctor_payload(results, deep=args.deep)
    if args.deep:
        payload["local_codex"] = deep_local_payload(local_summary)
    print_payload(payload, args.json)


def cmd_ledger(args: argparse.Namespace, store: Store) -> None:
    if args.ledger_command == "init":
        results = run_source_doctor(store.conn, Path.cwd())
        add_privacy_audit(
            store.conn,
            "ledger_initialized",
            {"db_name": store.db_path.name, "source_count": len(results)},
        )
        store.conn.commit()
        payload = {
            "ok": True,
            "db_path": str(store.db_path),
            "sources": len(results),
            "privacy_boundary": "本地账本不读取浏览器 cookie、OpenAI token、钥匙串、系统凭据或聊天正文。",
        }
        print_payload(payload, args.json)
        return

    if args.ledger_command == "import":
        try:
            if args.official_export:
                result = import_official_export(store.conn, args.official_export, mapping_path=args.mapping)
                source_type = "official_export"
            else:
                result = import_snapshot_delta(store.conn, args.snapshot)
                source_type = "snapshot_delta"
        except FileNotFoundError as exc:
            fail(errors.INVALID_SOURCE, str(exc), args.json)
        except (ValueError, json.JSONDecodeError) as exc:
            fail(errors.PARSE_FAILED, str(exc), args.json)
        payload = {"ok": True, "source_type": source_type, **result}
        print_payload(payload, args.json)
        return

    if args.ledger_command == "inspect-export":
        try:
            inspection = inspect_export(args.file, args.mapping)
        except FileNotFoundError as exc:
            fail(errors.INVALID_SOURCE, str(exc), args.json)
        except (ValueError, json.JSONDecodeError) as exc:
            fail(errors.PARSE_FAILED, str(exc), args.json)
        print_payload(inspection_payload(inspection), args.json)
        return

    if args.ledger_command == "map-export":
        try:
            inspection = inspect_export(args.file)
            write_mapping_template(args.out, inspection)
        except FileNotFoundError as exc:
            fail(errors.INVALID_SOURCE, str(exc), args.json)
        except (ValueError, json.JSONDecodeError) as exc:
            fail(errors.PARSE_FAILED, str(exc), args.json)
        print_payload({"ok": True, "mapping_path": str(args.out), **inspection_payload(inspection)}, args.json)
        return

    if args.ledger_command == "import-history":
        try:
            result = import_local_history(
                store.conn,
                root=args.root,
                dry_run=args.dry_run,
                limit_files=args.limit_files,
            )
        except FileNotFoundError as exc:
            fail(errors.INVALID_SOURCE, str(exc), args.json)
        except (ValueError, json.JSONDecodeError) as exc:
            fail(errors.PARSE_FAILED, str(exc), args.json)
        print_payload(result, args.json)
        return

    fail("UNKNOWN_COMMAND", f"Unsupported ledger command: {args.ledger_command}", args.json)


def cmd_watch(args: argparse.Namespace, store: Store) -> None:
    if args.watch_command == "once":
        try:
            result = collect_once(store, root=args.root, limit_files=args.limit_files)
        except (ValueError, json.JSONDecodeError) as exc:
            fail(errors.PARSE_FAILED, str(exc), args.json)
        print_payload({"ok": True, **result}, args.json)
        return
    if args.watch_command == "start":
        state = start_watcher(store.db_path, args.interval_seconds, root=args.root, limit_files=args.limit_files)
        write_watch_state(
            store.conn,
            status=state.get("status", "running"),
            interval_seconds=args.interval_seconds,
            source_ids=["source_local_codex_rollout"],
            message="watcher 后台采集已启动；只读取 token 用量白名单字段。",
        )
        store.conn.commit()
        print_payload({"ok": True, **state}, args.json)
        return
    if args.watch_command == "status":
        state = read_state(store.db_path)
        legacy = read_watch_state(store.conn)
        print_payload({"ok": True, **legacy, **state}, args.json)
        return
    if args.watch_command == "logs":
        print_payload(watcher_logs(store.db_path, limit=args.limit), args.json)
        return
    if args.watch_command == "status-page":
        range_label, start, end = resolve_range(args)
        sessions = ledger_summary(store.conn, start=start, end=end)
        logs = watcher_logs(store.db_path, limit=80)["lines"]
        write_static_file(args.out, render_watch_status_html(read_state(store.db_path), logs, sessions))
        store.add_report("watch_status_page", str(args.out), f"{len(sessions)} sessions")
        if args.open:
            open_local_file(args.out)
        print_payload({"ok": True, "range": range_label, "status_page": str(args.out), "opened": args.open}, args.json)
        return
    if args.watch_command == "stop":
        state = stop_watcher(store.db_path)
        write_watch_state(store.conn, status="stopped", message="watch 已停止。")
        store.conn.commit()
        print_payload({"ok": True, **state}, args.json)
        return
    if args.watch_command == "_run":
        run_forever(store, args.interval_seconds, root=args.root, limit_files=args.limit_files)
        return
    fail("UNKNOWN_COMMAND", f"Unsupported watch command: {args.watch_command}", args.json)


def cmd_sessions(args: argparse.Namespace, store: Store) -> None:
    range_label, start, end = resolve_range(args)
    sessions = ledger_summary(store.conn, start=start, end=end, min_confidence=args.min_confidence)
    if args.out:
        write_text(args.out, render_sessions_markdown(sessions, range_label))
        store.add_report("ledger_sessions", str(args.out), f"{len(sessions)} sessions")
    payload = {
        "ok": True,
        "range": range_label,
        "session_count": len(sessions),
        "sessions": [session_to_json(item) for item in sessions],
        "report_path": str(args.out) if args.out else None,
    }
    print_payload(payload, args.json)
    if not args.json:
        print(render_sessions_markdown(sessions, range_label))


def cmd_session_report(args: argparse.Namespace, store: Store) -> None:
    sessions = ledger_summary(store.conn)
    session = next((item for item in sessions if item.session_id == args.session_id), None)
    if session is None:
        fail("SESSION_NOT_FOUND", f"Session not found: {args.session_id}", args.json)
    snapshots = session_snapshots(store.conn, args.session_id)
    write_text(args.out, render_session_detail_markdown(session, snapshots))
    store.add_report("ledger_session_report", str(args.out), args.session_id)
    payload = {
        "ok": True,
        "session_id": args.session_id,
        "report_path": str(args.out),
        "snapshot_count": len(snapshots),
    }
    print_payload(payload, args.json)


def cmd_ledger_report(args: argparse.Namespace, store: Store) -> None:
    range_label, start, end = resolve_range(args)
    sessions = ledger_summary(store.conn, start=start, end=end)
    write_text(args.out, render_ledger_report_markdown(sessions, range_label))
    store.add_report("ledger_report", str(args.out), f"{len(sessions)} sessions")
    print_payload({"ok": True, "range": range_label, "report_path": str(args.out), "session_count": len(sessions)}, args.json)


def cmd_privacy(args: argparse.Namespace, store: Store) -> None:
    if args.privacy_command != "inspect":
        fail("UNKNOWN_COMMAND", f"Unsupported privacy command: {args.privacy_command}", args.json)
    sources = source_rows(store.conn)
    audits = privacy_audit_rows(store.conn)
    write_text(args.out, render_privacy_markdown(sources, audits))
    store.add_report("ledger_privacy", str(args.out), f"{len(sources)} sources")
    payload = {
        "ok": True,
        "report_path": str(args.out),
        "sources": sources,
        "audit_count": len(audits),
        "privacy_boundary": "不读取浏览器 cookie、OpenAI token、钥匙串、系统凭据或聊天正文。",
    }
    print_payload(payload, args.json)


def cmd_dashboard(args: argparse.Namespace, store: Store) -> None:
    range_label, start, end = resolve_range(args)
    sessions = ledger_summary(store.conn, start=start, end=end)
    write_static_file(args.out, render_dashboard_html(sessions, range_label))
    store.add_report("ledger_dashboard", str(args.out), f"{len(sessions)} sessions")
    if args.open:
        open_local_file(args.out)
    print_payload({"ok": True, "dashboard_path": str(args.out), "session_count": len(sessions), "opened": args.open}, args.json)


def cmd_samples(args: argparse.Namespace, store: Store) -> None:
    if args.samples_command != "collect-rollout":
        fail("UNKNOWN_COMMAND", f"Unsupported samples command: {args.samples_command}", args.json)
    result = collect_redacted_rollout_samples(
        args.root,
        args.out,
        limit_files=args.limit_files,
        max_records=args.max_records,
    )
    add_privacy_audit(
        store.conn,
        "redacted_rollout_samples_collected",
        {"out": str(args.out), "records": result.get("records"), "root_hash": result.get("root_hash")},
    )
    store.conn.commit()
    print_payload(result, args.json)


def cmd_delete(args: argparse.Namespace, store: Store) -> None:
    if not args.all and not args.ledger and not args.watcher:
        fail(errors.DELETE_FAILED, "Use --all, --ledger, or --watcher to choose deletion scope.", args.json)
    if not args.yes:
        fail(errors.DELETE_FAILED, "Refusing to delete without --yes confirmation.", args.json)
    deleted = 0
    if args.all:
        deleted += store.delete_business_data()
    if args.ledger:
        deleted += store.delete_ledger_business_data()
    if args.watcher:
        deleted += delete_watcher_files(store.db_path)
    scope = "all" if args.all else "ledger" if args.ledger else "watcher"
    print_payload({"ok": True, "deleted_count": deleted, "scope": scope}, args.json)


def risk_score(findings: list[object]) -> int:
    score = 0
    for finding in findings:
        severity = getattr(finding, "severity", "info")
        score += {"info": 5, "medium": 25, "high": 45}.get(severity, 10)
    return min(100, score)


def resolve_range(args: argparse.Namespace) -> tuple[str, str | None, str | None]:
    if args.date_from or args.date_to:
        return f"{args.date_from or '开始'}..{args.date_to or '现在'}", normalize_date(args.date_from), normalize_date(args.date_to)
    token = args.since or getattr(args, "range", None) or "7d"
    now = datetime.now(timezone.utc).replace(microsecond=0)
    if token == "today":
        start_dt = now.replace(hour=0, minute=0, second=0)
    elif token == "yesterday":
        today = now.replace(hour=0, minute=0, second=0)
        return "yesterday", (today - timedelta(days=1)).isoformat(), today.isoformat()
    elif token.endswith("h"):
        start_dt = now - timedelta(hours=int(token[:-1]))
    elif token.endswith("d"):
        start_dt = now - timedelta(days=int(token[:-1]))
    else:
        start_dt = now - timedelta(days=7)
        token = "7d"
    return token, start_dt.isoformat(), now.isoformat()


def normalize_date(value: str | None) -> str | None:
    if not value:
        return None
    if "T" in value:
        return value
    return f"{value}T00:00:00+00:00"


def session_to_json(session: object) -> dict[str, object]:
    return {
        "session_id": session.session_id,
        "title": session.title,
        "project": session.project,
        "model": session.model,
        "started_at": session.started_at,
        "ended_at": session.ended_at,
        "token_delta": session.token_delta,
        "credits_delta": session.credits_delta,
        "context_peak_percent": session.context_peak_percent,
        "confidence_level": session.confidence_level,
        "confidence_score": session.confidence_score,
        "source_type": session.source_type,
        "recommendation": session.recommendation,
        "evidence_summary": session.evidence_summary,
    }


def print_payload(payload: dict[str, object], as_json: bool) -> None:
    if as_json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return
    for key, value in payload.items():
        if key == "findings":
            print(f"{key}: {len(value) if isinstance(value, list) else value}")
        else:
            print(f"{key}: {value}")


def open_local_file(path: Path) -> None:
    try:
        webbrowser.open(path.resolve().as_uri())
    except Exception:
        pass


def fail(code: str, message: str, as_json: bool) -> None:
    payload = {"ok": False, "error": {"code": code, "message": message}}
    if as_json:
        print(json.dumps(payload, ensure_ascii=False, indent=2), file=sys.stderr)
    else:
        print(f"{code}: {message}", file=sys.stderr)
    sys.exit(1)
