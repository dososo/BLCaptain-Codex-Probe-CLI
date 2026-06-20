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


if __name__ == "__main__":
    unittest.main()

