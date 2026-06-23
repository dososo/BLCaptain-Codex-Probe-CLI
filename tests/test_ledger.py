import tempfile
import unittest
from pathlib import Path

from codex_usage_skill_probe.ledger_adapters import import_official_export, import_snapshot_delta
from codex_usage_skill_probe.ledger_storage import delete_ledger_data, ledger_summary, privacy_audit_rows
from codex_usage_skill_probe.source_doctor import run_source_doctor, source_doctor_payload
from codex_usage_skill_probe.storage import Store


ROOT = Path(__file__).resolve().parents[1]


class LedgerTests(unittest.TestCase):
    def test_source_doctor_declares_privacy_boundary(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = Store(Path(tmp) / "ledger.db")
            try:
                results = run_source_doctor(store.conn, ROOT)
                payload = source_doctor_payload(results)
            finally:
                store.close()

        self.assertEqual(payload["max_confidence"], "exact")
        self.assertIn("不读取浏览器 cookie", payload["privacy_boundary"])
        source_types = {item["source_type"] for item in payload["sources"]}
        self.assertIn("official_export", source_types)
        self.assertIn("snapshot_delta", source_types)

    def test_official_and_snapshot_import_build_session_ledger(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = Store(Path(tmp) / "ledger.db")
            try:
                import_official_export(store.conn, ROOT / "examples" / "ledger-samples" / "official-export.csv")
                import_snapshot_delta(store.conn, ROOT / "examples" / "ledger-samples" / "snapshot-delta.json")
                sessions = ledger_summary(store.conn)
                high_or_better = ledger_summary(store.conn, min_confidence="high")
            finally:
                store.close()

        by_id = {item.session_id: item for item in sessions}
        self.assertEqual(by_id["session_readme_release"].token_delta, 142047)
        self.assertEqual(by_id["session_readme_release"].confidence_level, "exact")
        self.assertEqual(by_id["session_ci_fix"].token_delta, 22400)
        self.assertEqual(by_id["session_ci_fix"].confidence_level, "high")
        self.assertEqual(by_id["session_research"].token_delta, 18200)
        self.assertEqual(by_id["session_research"].confidence_level, "medium")
        low = [item for item in sessions if item.confidence_level == "low"]
        self.assertEqual(len(low), 1)
        self.assertEqual(low[0].token_delta, 6400)
        self.assertEqual({item.confidence_level for item in high_or_better}, {"exact", "high"})

    def test_delete_ledger_keeps_privacy_audit(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = Store(Path(tmp) / "ledger.db")
            try:
                import_official_export(store.conn, ROOT / "examples" / "ledger-samples" / "official-export.csv")
                deleted = delete_ledger_data(store.conn)
                remaining = ledger_summary(store.conn)
                audits = privacy_audit_rows(store.conn)
            finally:
                store.close()

        self.assertGreater(deleted, 0)
        self.assertEqual(remaining, [])
        self.assertTrue(any(item["action"] == "delete_ledger_business_data" for item in audits))


if __name__ == "__main__":
    unittest.main()
