import tempfile
import unittest
from pathlib import Path

from codex_usage_skill_probe.export_mapping import inspect_export
from codex_usage_skill_probe.ledger_adapters import import_official_export, import_snapshot_delta
from codex_usage_skill_probe.ledger_reports import (
    local_time,
    render_alerts_markdown,
    render_confidence_markdown,
    render_project_summary_markdown,
    render_sessions_markdown,
    render_task_report_markdown,
    render_timeline_markdown,
    render_weekly_report_markdown,
)
from codex_usage_skill_probe.ledger_storage import (
    budget_alerts,
    delete_ledger_data,
    ledger_summary,
    privacy_audit_rows,
    project_summary,
    session_intervals,
    source_confidence_summary,
    task_type_summary,
    weekly_summary,
)
from codex_usage_skill_probe.local_history import import_local_history, inspect_local_codex
from codex_usage_skill_probe.source_doctor import run_source_doctor, source_doctor_payload
from codex_usage_skill_probe.storage import Store


ROOT = Path(__file__).resolve().parents[1]


class LedgerTests(unittest.TestCase):
    def test_source_doctor_declares_privacy_boundary(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = Store(Path(tmp) / "ledger.db")
            try:
                results = run_source_doctor(store.conn, ROOT)
                payload = source_doctor_payload(results)
            finally:
                store.close()

        self.assertEqual(payload["max_confidence"], "exact")
        self.assertIn("不读取浏览器 cookie", payload["privacy_boundary"])
        source_types = {item["source_type"] for item in payload["sources"]}
        self.assertIn("official_export", source_types)
        self.assertIn("snapshot_delta", source_types)
        self.assertIn("local_codex_rollout", source_types)

    def test_official_export_inspection_supports_jsonl_and_mapping(self):
        inspection = inspect_export(ROOT / "examples" / "ledger-samples" / "official-export.jsonl")
        self.assertEqual(inspection.format, "jsonl")
        self.assertEqual(inspection.row_count, 2)
        self.assertEqual(inspection.mapping["session_id"], "session_id")

        alt = inspect_export(
            ROOT / "examples" / "ledger-samples" / "official-export-alt.json",
            ROOT / "examples" / "ledger-samples" / "official-export-alt.mapping.json",
        )
        self.assertEqual(alt.mapping["session_id"], "conversation_id")
        self.assertEqual(alt.mapping["total_tokens"], "tokens")

    def test_official_and_snapshot_import_build_session_ledger(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = Store(Path(tmp) / "ledger.db")
            try:
                import_official_export(store.conn, ROOT / "examples" / "ledger-samples" / "official-export.csv")
                import_official_export(store.conn, ROOT / "examples" / "ledger-samples" / "official-export.jsonl")
                import_official_export(
                    store.conn,
                    ROOT / "examples" / "ledger-samples" / "official-export-alt.json",
                    mapping_path=ROOT / "examples" / "ledger-samples" / "official-export-alt.mapping.json",
                )
                import_snapshot_delta(store.conn, ROOT / "examples" / "ledger-samples" / "snapshot-delta.json")
                sessions = ledger_summary(store.conn)
                high_or_better = ledger_summary(store.conn, min_confidence="high")
            finally:
                store.close()

        by_id = {item.session_id: item for item in sessions}
        self.assertEqual(by_id["session_readme_release"].token_delta, 142047)
        self.assertEqual(by_id["session_readme_release"].confidence_level, "exact")
        self.assertEqual(by_id["session_jsonl_release"].token_delta, 47400)
        self.assertEqual(by_id["session_alt_mapping"].token_delta, 36600)
        self.assertEqual(by_id["session_ci_fix"].token_delta, 22400)
        self.assertEqual(by_id["session_ci_fix"].confidence_level, "high")
        self.assertEqual(by_id["session_research"].token_delta, 18200)
        self.assertEqual(by_id["session_research"].confidence_level, "medium")
        low = [item for item in sessions if item.confidence_level == "low"]
        self.assertEqual(len(low), 1)
        self.assertEqual(low[0].token_delta, 6400)
        self.assertEqual({item.confidence_level for item in high_or_better}, {"exact", "high"})

    def test_local_codex_history_dry_run_and_import(self):
        root = ROOT / "examples" / "ledger-samples" / "local-codex"
        dry = inspect_local_codex(root)
        self.assertEqual(dry.file_count, 1)
        self.assertEqual(dry.importable_record_count, 2)
        with tempfile.TemporaryDirectory() as tmp:
            store = Store(Path(tmp) / "ledger.db")
            try:
                preview = import_local_history(store.conn, root, dry_run=True)
                result = import_local_history(store.conn, root)
                second = import_local_history(store.conn, root)
                sessions = ledger_summary(store.conn)
            finally:
                store.close()

        self.assertFalse(preview["wrote"])
        self.assertEqual(result["imported_snapshots"], 2)
        self.assertEqual(second["skipped_duplicates"], 2)
        self.assertEqual(len(sessions), 1)
        self.assertEqual(sessions[0].token_delta, 58000)
        self.assertEqual(sessions[0].confidence_level, "high")
        self.assertEqual(sessions[0].model, "gpt-5.5")
        self.assertIn("降配", sessions[0].recommendation)

    def test_local_codex_history_variant_aliases_and_missing_model(self):
        root = ROOT / "examples" / "ledger-samples" / "local-codex-variants"
        dry = inspect_local_codex(root)
        self.assertEqual(dry.file_count, 1)
        self.assertEqual(dry.importable_record_count, 3)
        with tempfile.TemporaryDirectory() as tmp:
            store = Store(Path(tmp) / "ledger.db")
            try:
                result = import_local_history(store.conn, root)
                sessions = ledger_summary(store.conn)
            finally:
                store.close()

        self.assertEqual(result["imported_snapshots"], 3)
        by_id = {item.session_id: item for item in sessions}
        self.assertEqual(len(sessions), 3)
        self.assertTrue(any(item.model == "gpt-5.5" for item in sessions))
        self.assertTrue(any(item.model == "" for item in sessions))
        self.assertTrue(any(item.token_delta == 19_000 for item in sessions))
        self.assertTrue(all("[REDACTED_PROJECT_PATH" not in item.project for item in sessions))

    def test_reports_show_local_time_and_precision_notes(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = Store(Path(tmp) / "ledger.db")
            try:
                import_official_export(store.conn, ROOT / "examples" / "ledger-samples" / "official-export.csv")
                sessions = ledger_summary(store.conn)
            finally:
                store.close()

        rendered = render_sessions_markdown(sessions, "7d")
        self.assertIn("开始时间", rendered)
        self.assertIn("结束时间", rendered)
        self.assertIn("credits delta（来源值）", rendered)
        self.assertIn("本工具不换算成美元、人民币或官方账单金额", rendered)
        self.assertRegex(local_time("2026-06-22T09:00:00+00:00"), r"2026-06-22 .* UTC[+-][0-9]{2}:[0-9]{2}")

    def test_project_summary_and_weekly_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = Store(Path(tmp) / "ledger.db")
            try:
                import_official_export(store.conn, ROOT / "examples" / "ledger-samples" / "official-export.csv")
                import_snapshot_delta(store.conn, ROOT / "examples" / "ledger-samples" / "snapshot-delta.json")
                projects = project_summary(store.conn)
                weeks = weekly_summary(store.conn)
            finally:
                store.close()

        self.assertGreaterEqual(len(projects), 2)
        cli_project = next(item for item in projects if item.project == "Codex Probe CLI")
        self.assertGreaterEqual(cli_project.token_delta, 203367)
        self.assertEqual(cli_project.confidence_counts["exact"], 2)
        self.assertIn("停止", cli_project.recommendation)
        self.assertTrue(any(item.week_label.startswith("2026-W") for item in weeks))

        project_report = render_project_summary_markdown(projects, "30d")
        weekly_report = render_weekly_report_markdown(weeks, "30d")
        self.assertIn("Codex 项目级用量汇总", project_report)
        self.assertIn("置信度分布", project_report)
        self.assertIn("Codex 周报", weekly_report)
        self.assertIn("本地日期范围", weekly_report)

    def test_v080_timeline_alerts_tasks_and_source_confidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = Store(Path(tmp) / "ledger.db")
            try:
                import_official_export(store.conn, ROOT / "examples" / "ledger-samples" / "official-export.csv")
                import_snapshot_delta(store.conn, ROOT / "examples" / "ledger-samples" / "snapshot-delta.json")
                import_local_history(store.conn, ROOT / "examples" / "ledger-samples" / "local-codex-stress")
                intervals = session_intervals(store.conn)
                alerts = budget_alerts(store.conn, session_threshold=20_000, project_threshold=60_000, ledger_threshold=120_000)
                tasks = task_type_summary(store.conn)
                sources = source_confidence_summary(store.conn)
            finally:
                store.close()

        self.assertTrue(any(item.stage_label in {"文档报告", "调试修复", "调研分析", "未知任务"} for item in intervals))
        self.assertTrue(any(item.token_delta >= 20_000 for item in intervals))
        self.assertTrue(any(item.scope == "session" for item in alerts))
        self.assertTrue(any(item.scope == "ledger" for item in alerts))
        self.assertTrue(any(item.task_type == "发布交付" for item in tasks))
        self.assertTrue(any(item.source_type == "local_codex_rollout" for item in sources))
        self.assertTrue(any("total_tokens" in item.fields_present for item in sources))

        timeline_report = render_timeline_markdown(intervals, "30d")
        alerts_report = render_alerts_markdown(alerts, "30d")
        task_report = render_task_report_markdown(tasks, "30d")
        confidence_report = render_confidence_markdown(sources)
        self.assertIn("阶段级高消耗时间线", timeline_report)
        self.assertIn("本地预算与停止线预警", alerts_report)
        self.assertIn("任务类型归因报告", task_report)
        self.assertIn("数据源可信度报告", confidence_report)
        self.assertIn("为什么有些字段不能更精确", confidence_report)

    def test_delete_ledger_keeps_privacy_audit(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = Store(Path(tmp) / "ledger.db")
            try:
                import_official_export(store.conn, ROOT / "examples" / "ledger-samples" / "official-export.csv")
                deleted = delete_ledger_data(store.conn)
                remaining = ledger_summary(store.conn)
                audits = privacy_audit_rows(store.conn)
            finally:
                store.close()

        self.assertGreater(deleted, 0)
        self.assertEqual(remaining, [])
        self.assertTrue(any(item["action"] == "delete_ledger_business_data" for item in audits))


if __name__ == "__main__":
    unittest.main()
