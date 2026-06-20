import unittest

from codex_usage_skill_probe.privacy import redact, snippet


class PrivacyTests(unittest.TestCase):
    def test_redacts_common_secrets(self):
        text = "key sk-abcdefghijklmnop123456 token=secret123456789 email a@b.com phone 13800138000"
        redacted = redact(text)
        self.assertNotIn("sk-abcdefghijklmnop123456", redacted)
        self.assertNotIn("secret123456789", redacted)
        self.assertNotIn("a@b.com", redacted)
        self.assertNotIn("13800138000", redacted)
        self.assertIn("[REDACTED:OPENAI_KEY]", redacted)

    def test_snippet_does_not_cut_redaction_marker(self):
        text = "x" * 140 + " sk-abcdefghijklmnop1234567890"
        preview = snippet(text, limit=160)
        self.assertIn("[REDACTED:OPENAI_KEY]", preview)
        self.assertNotIn("[REDACTED:OPEN", preview.replace("[REDACTED:OPENAI_KEY]", ""))


if __name__ == "__main__":
    unittest.main()
