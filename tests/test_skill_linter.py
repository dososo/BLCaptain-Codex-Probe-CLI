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

    def test_evidence_does_not_cut_redaction_marker(self):
        _, findings = lint_text(
            "# 示例 Skill\n\n当然可以，以下是一个一站式保姆级 Skill。\n\n"
            "它会自动安装插件，并尝试跳过手机号验证。用户只需一键开挂。\n\n"
            "输出时需要减少 AI 味。\n\n"
            "API key: sk-example000000000000000000000000\n"
        )
        all_evidence = " ".join(f.evidence for f in findings)
        self.assertIn("[REDACTED:OPENAI_KEY]", all_evidence)
        self.assertNotIn("[REDACTED:OPEN ", all_evidence)


if __name__ == "__main__":
    unittest.main()
