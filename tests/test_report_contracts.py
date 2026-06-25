import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class ReportContractTests(unittest.TestCase):
    def run_probe(self, *args):
        cmd = [sys.executable, "-m", "codex_usage_skill_probe", *args]
        result = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True)
        if result.returncode != 0:
            raise AssertionError(f"command failed: {cmd}\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}")
        return result

    def test_json_and_html_report_contracts(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            db = tmp_path / "contracts.db"
            dashboard = tmp_path / "dashboard.html"
            privacy = tmp_path / "privacy.md"
            ledger_report = tmp_path / "ledger.md"
            timeline_report = tmp_path / "timeline.md"
            alerts_report = tmp_path / "alerts.md"
            task_report = tmp_path / "task.md"
            confidence_report = tmp_path / "confidence.md"

            self.run_probe("--db", str(db), "--json", "ledger", "init")
            self.run_probe(
                "--db",
                str(db),
                "--json",
                "ledger",
                "import",
                "--official-export",
                "examples/ledger-samples/official-export.csv",
            )
            self.run_probe(
                "--db",
                str(db),
                "--json",
                "ledger",
                "import",
                "--snapshot",
                "examples/ledger-samples/snapshot-delta.json",
            )
            self.run_probe(
                "--db",
                str(db),
                "--json",
                "ledger",
                "import-history",
                "--source",
                "local-codex",
                "--root",
                "examples/ledger-samples/local-codex-variants",
            )

            sessions = json.loads(self.run_probe("--db", str(db), "--json", "sessions", "--range", "30d").stdout)
            projects = json.loads(self.run_probe("--db", str(db), "--json", "projects", "--range", "30d").stdout)
            weeks = json.loads(self.run_probe("--db", str(db), "--json", "weekly-report", "--range", "30d").stdout)
            intervals = json.loads(
                self.run_probe("--db", str(db), "--json", "timeline", "--range", "30d", "--out", str(timeline_report)).stdout
            )
            alerts = json.loads(
                self.run_probe(
                    "--db",
                    str(db),
                    "--json",
                    "alerts",
                    "--range",
                    "30d",
                    "--session-threshold",
                    "20000",
                    "--out",
                    str(alerts_report),
                ).stdout
            )
            tasks = json.loads(
                self.run_probe("--db", str(db), "--json", "task-report", "--range", "30d", "--out", str(task_report)).stdout
            )
            confidence = json.loads(
                self.run_probe("--db", str(db), "--json", "confidence-report", "--out", str(confidence_report)).stdout
            )
            privacy_payload = json.loads(
                self.run_probe("--db", str(db), "--json", "privacy", "inspect", "--out", str(privacy)).stdout
            )

            self.assertEqual(
                {
                    "ok",
                    "range",
                    "session_count",
                    "sessions",
                    "report_path",
                },
                set(sessions),
            )
            self.assertTrue(
                {
                    "session_id",
                    "title",
                    "project",
                    "model",
                    "started_at",
                    "ended_at",
                    "token_delta",
                    "credits_delta",
                    "context_peak_percent",
                    "confidence_level",
                    "confidence_score",
                    "source_type",
                    "recommendation",
                    "evidence_summary",
                }.issubset(sessions["sessions"][0])
            )
            self.assertTrue(
                {
                    "project",
                    "session_count",
                    "token_delta",
                    "credits_delta",
                    "top_session_id",
                    "top_session_title",
                    "top_session_tokens",
                    "confidence_counts",
                    "recommendation",
                }.issubset(projects["projects"][0])
            )
            self.assertTrue(
                {
                    "week_label",
                    "week_start",
                    "week_end",
                    "session_count",
                    "project_count",
                    "token_delta",
                    "credits_delta",
                    "top_project",
                    "top_session_id",
                    "top_session_title",
                    "top_session_tokens",
                    "confidence_counts",
                    "recommendation",
                }.issubset(weeks["weeks"][0])
            )
            self.assertTrue(
                {
                    "session_id",
                    "title",
                    "project",
                    "start_at",
                    "end_at",
                    "token_delta",
                    "stage_label",
                    "severity",
                    "confidence_level",
                    "recommendation",
                }.issubset(intervals["intervals"][0])
            )
            self.assertTrue(
                {
                    "scope",
                    "scope_id",
                    "name",
                    "token_delta",
                    "threshold",
                    "usage_percent",
                    "severity",
                    "confidence_level",
                    "reason",
                    "recommendation",
                }.issubset(alerts["alerts"][0])
            )
            self.assertTrue({"task_type", "session_count", "token_delta", "top_session_title"}.issubset(tasks["tasks"][0]))
            self.assertTrue(
                {
                    "source_type",
                    "enabled",
                    "confidence_ceiling",
                    "fields_present",
                    "missing_fields",
                    "diagnosis",
                }.issubset(confidence["sources"][0])
            )
            self.assertIn("不读取浏览器 cookie", privacy_payload["privacy_boundary"])

            self.run_probe("--db", str(db), "--json", "ledger-report", "--range", "30d", "--out", str(ledger_report))
            self.assertIn("严谨性说明", ledger_report.read_text(encoding="utf-8"))

            self.run_probe("--db", str(db), "--json", "dashboard", "--range", "30d", "--out", str(dashboard))
            html = dashboard.read_text(encoding="utf-8")
            for marker in [
                "projectFilter",
                "fromFilter",
                "toFilter",
                "confidenceFilter",
                "modelFilter",
                "本地预算预警",
                "数据源可信度",
                "任务类型归因",
                "高风险项目",
                "隐私边界",
                "credits 是来源提供的数值",
            ]:
                self.assertIn(marker, html)
            self.assertNotIn("sk-", html)
            self.assertNotIn("Bearer ", html)
            self.assertNotIn("cookie=", html)


if __name__ == "__main__":
    unittest.main()
