import unittest

from codex_usage_skill_probe.usage_parser import parse_status_text


class UsageParserTests(unittest.TestCase):
    def test_parse_status_text(self):
        batch, record = parse_status_text(
            """
            Model: gpt-5.5
            Mode: fast
            Input tokens: 1,200
            Output tokens: 300
            Credits: 12.5
            Remaining: 8
            Limit: 100
            """
        )
        self.assertEqual(batch.parsed_count, 1)
        self.assertEqual(record.model, "gpt-5.5")
        self.assertEqual(record.mode, "fast")
        self.assertEqual(record.input_tokens, 1200)
        self.assertEqual(record.output_tokens, 300)
        self.assertEqual(record.total_tokens, 1500)
        self.assertEqual(record.credits, 12.5)
        self.assertEqual(record.quota_remaining, 8)


if __name__ == "__main__":
    unittest.main()

