import unittest

from codex_usage_skill_probe.privacy import redact


class PrivacyTests(unittest.TestCase):
    def test_redacts_common_secrets(self):
        text = "key sk-abcdefghijklmnop123456 token=secret123456789 email a@b.com phone 13800138000"
        redacted = redact(text)
        self.assertNotIn("sk-abcdefghijklmnop123456", redacted)
        self.assertNotIn("secret123456789", redacted)
        self.assertNotIn("a@b.com", redacted)
        self.assertNotIn("13800138000", redacted)
        self.assertIn("[REDACTED:OPENAI_KEY]", redacted)


if __name__ == "__main__":
    unittest.main()

