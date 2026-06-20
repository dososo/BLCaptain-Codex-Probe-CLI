import unittest

from codex_usage_skill_probe.skill_linter import lint_text


class SkillLinterTests(unittest.TestCase):
    def test_flags_ai_smell_plugin_risk_and_secrets(self):
        _, findings = lint_text(
            "当然可以，以下是保姆级方案，自动安装插件并跳过手机号。sk-testabcdefghijklmnop"
        )
        labels = {f.finding_type for f in findings}
        self.assertIn("AI_SMELL", labels)
        self.assertIn("PLUGIN_RISK", labels)
        self.assertIn("SECRET_RISK", labels)
        all_evidence = " ".join(f.evidence for f in findings)
        self.assertNotIn("sk-testabcdefghijklmnop", all_evidence)


if __name__ == "__main__":
    unittest.main()

