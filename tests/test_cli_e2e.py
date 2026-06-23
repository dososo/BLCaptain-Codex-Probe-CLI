import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class CliE2ETests(unittest.TestCase):
    def run_probe(self, *args, check=True):
        cmd = [sys.executable, "-m", "codex_usage_skill_probe", *args]
        result = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True)
        if check and result.returncode != 0:
            raise AssertionError(f"command failed: {cmd}\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}")
        return result

    def test_acceptance_flow(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            db = tmp_path / "probe.db"
            usage_report = tmp_path / "usage.md"
            skill_report = tmp_path / "skill.md"
            doctor_dir = tmp_path / "doctor"

            imported = self.run_probe(
                "--db",
                str(db),
                "--json",
                "import",
                "--status",
                "examples/status.txt",
                "--goal",
                "验收测试",
            )
            payload = json.loads(imported.stdout)
            self.assertTrue(payload["ok"])

            usage = self.run_probe(
                "--db",
                str(db),
                "--json",
                "usage-report",
                "--budget-tokens",
                "100000",
                "--out",
                str(usage_report),
            )
            usage_payload = json.loads(usage.stdout)
            labels = {f["finding_type"] for f in usage_payload["findings"]}
            self.assertIn("OVER_BUDGET", labels)
            self.assertTrue(usage_report.exists())
            self.assertIn("E-011", usage_report.read_text(encoding="utf-8"))

            linted = self.run_probe(
                "--db",
                str(db),
                "--json",
                "skill-lint",
                "examples/risky-skill.md",
                "--out",
                str(skill_report),
            )
            lint_payload = json.loads(linted.stdout)
            lint_labels = {f["finding_type"] for f in lint_payload["findings"]}
            self.assertIn("AI_SMELL", lint_labels)
            self.assertIn("PLUGIN_RISK", lint_labels)
            self.assertTrue(skill_report.exists())

            doctor = self.run_probe(
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
            )
            doctor_payload = json.loads(doctor.stdout)
            self.assertTrue(doctor_payload["ok"])
            self.assertIn(doctor_payload["decision"]["action"], {"停止", "降配", "继续"})
            self.assertTrue((doctor_dir / "doctor-report.md").exists())
            self.assertTrue((doctor_dir / "usage-report.md").exists())
            self.assertTrue((doctor_dir / "skill-lint-report.md").exists())
            self.assertIn("决策卡片", (doctor_dir / "usage-report.md").read_text(encoding="utf-8"))

            deleted = self.run_probe("--db", str(db), "--json", "delete", "--all", "--yes")
            self.assertTrue(json.loads(deleted.stdout)["ok"])

            after_delete = self.run_probe(
                "--db",
                str(db),
                "--json",
                "usage-report",
                "--out",
                str(tmp_path / "after-delete.md"),
                check=False,
            )
            self.assertNotEqual(after_delete.returncode, 0)
            self.assertIn("NO_USAGE_DATA", after_delete.stderr)

    def test_ledger_flow(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            db = tmp_path / "ledger.db"
            session_report = tmp_path / "session.md"
            ledger_report = tmp_path / "ledger.md"
            privacy_report = tmp_path / "privacy.md"
            dashboard = tmp_path / "dashboard.html"

            initialized = self.run_probe("--db", str(db), "--json", "ledger", "init")
            self.assertTrue(json.loads(initialized.stdout)["ok"])

            doctor = self.run_probe("--db", str(db), "--json", "sources", "doctor")
            doctor_payload = json.loads(doctor.stdout)
            self.assertEqual(doctor_payload["max_confidence"], "exact")

            inspected = self.run_probe(
                "--db",
                str(db),
                "--json",
                "ledger",
                "inspect-export",
                "examples/ledger-samples/official-export.jsonl",
            )
            self.assertEqual(json.loads(inspected.stdout)["format"], "jsonl")

            mapping = tmp_path / "mapping.json"
            mapped = self.run_probe(
                "--db",
                str(db),
                "--json",
                "ledger",
                "map-export",
                "examples/ledger-samples/official-export-alt.json",
                "--out",
                str(mapping),
            )
            self.assertTrue(json.loads(mapped.stdout)["ok"])
            self.assertTrue(mapping.exists())

            official = self.run_probe(
                "--db",
                str(db),
                "--json",
                "ledger",
                "import",
                "--official-export",
                "examples/ledger-samples/official-export.csv",
            )
            self.assertEqual(json.loads(official.stdout)["sessions"], 3)

            jsonl = self.run_probe(
                "--db",
                str(db),
                "--json",
                "ledger",
                "import",
                "--official-export",
                "examples/ledger-samples/official-export.jsonl",
            )
            self.assertEqual(json.loads(jsonl.stdout)["sessions"], 2)

            snapshots = self.run_probe(
                "--db",
                str(db),
                "--json",
                "ledger",
                "import",
                "--snapshot",
                "examples/ledger-samples/snapshot-delta.json",
            )
            self.assertEqual(json.loads(snapshots.stdout)["snapshots"], 5)

            history_preview = self.run_probe(
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
            )
            self.assertFalse(json.loads(history_preview.stdout)["wrote"])

            history_import = self.run_probe(
                "--db",
                str(db),
                "--json",
                "ledger",
                "import-history",
                "--source",
                "local-codex",
                "--root",
                "examples/ledger-samples/local-codex",
            )
            self.assertEqual(json.loads(history_import.stdout)["imported_snapshots"], 2)

            watch_once = self.run_probe(
                "--db",
                str(db),
                "--json",
                "watch",
                "once",
                "--root",
                "examples/ledger-samples/local-codex",
            )
            self.assertTrue(json.loads(watch_once.stdout)["ok"])

            try:
                watch_start = self.run_probe(
                    "--db",
                    str(db),
                    "--json",
                    "watch",
                    "start",
                    "--interval-seconds",
                    "1",
                    "--root",
                    "examples/ledger-samples/local-codex",
                )
                self.assertEqual(json.loads(watch_start.stdout)["status"], "running")
                watch_status = self.run_probe("--db", str(db), "--json", "watch", "status")
                self.assertIn(json.loads(watch_status.stdout)["status"], {"running", "stopped"})
                watch_logs = self.run_probe("--db", str(db), "--json", "watch", "logs")
                self.assertTrue(json.loads(watch_logs.stdout)["ok"])
            finally:
                self.run_probe("--db", str(db), "--json", "watch", "stop", check=False)

            ranked = self.run_probe("--db", str(db), "--json", "sessions", "--range", "7d")
            ranked_payload = json.loads(ranked.stdout)
            self.assertEqual(ranked_payload["sessions"][0]["session_id"], "session_readme_release")
            confidences = {item["confidence_level"] for item in ranked_payload["sessions"]}
            self.assertTrue({"exact", "high", "medium", "low"}.issubset(confidences))

            self.run_probe(
                "--db",
                str(db),
                "--json",
                "session-report",
                "session_readme_release",
                "--out",
                str(session_report),
            )
            self.assertIn("Codex 单会话用量详情", session_report.read_text(encoding="utf-8"))
            self.assertIn("高消耗区间", session_report.read_text(encoding="utf-8"))

            self.run_probe("--db", str(db), "--json", "ledger-report", "--range", "30d", "--out", str(ledger_report))
            self.assertIn("Codex 会话级 Token 总账报告", ledger_report.read_text(encoding="utf-8"))

            self.run_probe("--db", str(db), "--json", "privacy", "inspect", "--out", str(privacy_report))
            self.assertIn("不读取", privacy_report.read_text(encoding="utf-8"))

            self.run_probe("--db", str(db), "--json", "dashboard", "--range", "7d", "--out", str(dashboard))
            html = dashboard.read_text(encoding="utf-8")
            self.assertIn("Codex 会话级 Token 账本", html)
            self.assertNotIn("cookie=", html)

            deleted = self.run_probe("--db", str(db), "--json", "delete", "--ledger", "--yes")
            self.assertTrue(json.loads(deleted.stdout)["ok"])

            deleted_watcher = self.run_probe("--db", str(db), "--json", "delete", "--watcher", "--yes")
            self.assertTrue(json.loads(deleted_watcher.stdout)["ok"])


if __name__ == "__main__":
    unittest.main()
