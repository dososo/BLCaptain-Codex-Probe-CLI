import unittest

from codex_usage_skill_probe.models import TaskUsageRecord, new_id, now_iso
from codex_usage_skill_probe.usage_analyzer import analyze_usage


class UsageAnalyzerTests(unittest.TestCase):
    def test_budget_and_stop_findings(self):
        record = TaskUsageRecord(
            task_id=new_id("task"),
            import_id=new_id("import"),
            created_at=now_iso(),
            model="gpt-5.5",
            mode="fast",
            input_tokens=100000,
            output_tokens=50000,
            total_tokens=150000,
            credits=40,
            quota_remaining=10,
            quota_limit=100,
        )
        findings = analyze_usage(record, budget_tokens=100000, budget_credits=30)
        labels = {f.finding_type for f in findings}
        self.assertIn("OVER_BUDGET", labels)
        self.assertIn("CREDITS_OVER_BUDGET", labels)
        self.assertIn("FAST_MODE_RISK", labels)
        self.assertIn("STOP_RECOMMENDED", labels)


if __name__ == "__main__":
    unittest.main()

