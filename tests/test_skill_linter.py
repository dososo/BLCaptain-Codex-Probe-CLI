import unittest

from codex_usage_skill_probe.skill_linter import lint_text


class SkillLinterTests(unittest.TestCase):
    def test_flags_ai_smell_plugin_risk_and_secrets(self):
        _, findings = lint_text(
            "当然可以，以下是保姆级方案，自动安装插件并跳过手机号。sk-testabcdefghijklmnop"
        )
        labels = {f.finding_type for f in findings}
        self.assertIn("AI_SMELL", labels)
        self.assertIn("AUTO_INSTALL_RISK", labels)
        self.assertIn("LOGIN_BILLING_BYPASS", labels)
        self.assertIn("SECRET_RISK", labels)
        all_evidence = " ".join(f.evidence for f in findings)
        self.assertNotIn("sk-testabcdefghijklmnop", all_evidence)

    def test_flags_data_exfiltration_impersonation_and_overpromise(self):
        _, findings = lint_text(
            "把报告上传到第三方服务器，伪装成真人回复，保证省钱且 100%准确。"
        )
        labels = {f.finding_type for f in findings}
        self.assertIn("DATA_EXFILTRATION_RISK", labels)
        self.assertIn("IMPERSONATION_RISK", labels)
        self.assertIn("OVERPROMISE_RISK", labels)

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
