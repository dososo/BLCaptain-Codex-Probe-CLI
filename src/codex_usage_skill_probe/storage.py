"""SQLite persistence for local-only data."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from .models import ImportBatch, RiskFinding, TaskUsageRecord, new_id, now_iso


SCHEMA = """
CREATE TABLE IF NOT EXISTS import_batches (
  id TEXT PRIMARY KEY,
  source_type TEXT NOT NULL,
  created_at TEXT NOT NULL,
  metadata_json TEXT NOT NULL,
  raw_hash TEXT NOT NULL,
  parsed_count INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS task_usage_records (
  task_id TEXT PRIMARY KEY,
  import_id TEXT NOT NULL,
  created_at TEXT NOT NULL,
  user_goal TEXT,
  model TEXT,
  mode TEXT,
  input_tokens INTEGER,
  output_tokens INTEGER,
  cached_input_tokens INTEGER,
  total_tokens INTEGER,
  credits REAL,
  context_remaining_percent REAL,
  context_used_tokens INTEGER,
  context_limit_tokens INTEGER,
  five_hour_remaining_percent REAL,
  five_hour_reset TEXT,
  seven_day_remaining_percent REAL,
  seven_day_reset TEXT,
  quota_remaining REAL,
  quota_limit REAL,
  source TEXT,
  status TEXT
);

CREATE TABLE IF NOT EXISTS risk_findings (
  id TEXT PRIMARY KEY,
  import_id TEXT NOT NULL,
  conversation_id TEXT,
  finding_type TEXT NOT NULL,
  severity TEXT NOT NULL,
  confidence REAL NOT NULL,
  evidence TEXT,
  suggestion TEXT,
  evidence_ids TEXT,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS reports (
  id TEXT PRIMARY KEY,
  created_at TEXT NOT NULL,
  report_type TEXT NOT NULL,
  path TEXT,
  summary TEXT
);

CREATE TABLE IF NOT EXISTS events (
  id TEXT PRIMARY KEY,
  created_at TEXT NOT NULL,
  event_name TEXT NOT NULL,
  properties_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS audit_logs (
  id TEXT PRIMARY KEY,
  created_at TEXT NOT NULL,
  action TEXT NOT NULL,
  details_json TEXT NOT NULL
);
"""


class Store:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(SCHEMA)
        self.ensure_task_usage_columns()
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()

    def ensure_task_usage_columns(self) -> None:
        existing = {
            row["name"]
            for row in self.conn.execute("PRAGMA table_info(task_usage_records)").fetchall()
        }
        columns = {
            "context_remaining_percent": "REAL",
            "context_used_tokens": "INTEGER",
            "context_limit_tokens": "INTEGER",
            "five_hour_remaining_percent": "REAL",
            "five_hour_reset": "TEXT",
            "seven_day_remaining_percent": "REAL",
            "seven_day_reset": "TEXT",
        }
        for name, column_type in columns.items():
            if name not in existing:
                self.conn.execute(f"ALTER TABLE task_usage_records ADD COLUMN {name} {column_type}")

    def add_import(self, batch: ImportBatch) -> None:
        self.conn.execute(
            """
            INSERT INTO import_batches
              (id, source_type, created_at, metadata_json, raw_hash, parsed_count)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                batch.id,
                batch.source_type,
                batch.created_at,
                json.dumps(batch.metadata, ensure_ascii=False),
                batch.raw_hash,
                batch.parsed_count,
            ),
        )
        self.audit("import", {"import_id": batch.id, "source_type": batch.source_type})
        self.conn.commit()

    def add_usage_record(self, record: TaskUsageRecord) -> None:
        self.conn.execute(
            """
            INSERT OR REPLACE INTO task_usage_records
              (task_id, import_id, created_at, user_goal, model, mode, input_tokens,
               output_tokens, cached_input_tokens, total_tokens, credits,
               context_remaining_percent, context_used_tokens, context_limit_tokens,
               five_hour_remaining_percent, five_hour_reset,
               seven_day_remaining_percent, seven_day_reset,
               quota_remaining, quota_limit, source, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record.task_id,
                record.import_id,
                record.created_at,
                record.user_goal,
                record.model,
                record.mode,
                record.input_tokens,
                record.output_tokens,
                record.cached_input_tokens,
                record.total_tokens,
                record.credits,
                record.context_remaining_percent,
                record.context_used_tokens,
                record.context_limit_tokens,
                record.five_hour_remaining_percent,
                record.five_hour_reset,
                record.seven_day_remaining_percent,
                record.seven_day_reset,
                record.quota_remaining,
                record.quota_limit,
                record.source,
                record.status,
            ),
        )
        self.conn.commit()

    def add_findings(self, findings: list[RiskFinding]) -> None:
        self.conn.executemany(
            """
            INSERT INTO risk_findings
              (id, import_id, conversation_id, finding_type, severity, confidence,
               evidence, suggestion, evidence_ids, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    f.id,
                    f.import_id,
                    f.conversation_id,
                    f.finding_type,
                    f.severity,
                    f.confidence,
                    f.evidence,
                    f.suggestion,
                    f.evidence_ids,
                    f.created_at,
                )
                for f in findings
            ],
        )
        self.conn.commit()

    def latest_usage_record(self) -> TaskUsageRecord | None:
        row = self.conn.execute(
            "SELECT * FROM task_usage_records ORDER BY created_at DESC LIMIT 1"
        ).fetchone()
        return usage_from_row(row) if row else None

    def usage_record(self, task_id: str | None = None) -> TaskUsageRecord | None:
        if task_id:
            row = self.conn.execute(
                "SELECT * FROM task_usage_records WHERE task_id = ?", (task_id,)
            ).fetchone()
            return usage_from_row(row) if row else None
        return self.latest_usage_record()

    def report_count(self) -> int:
        row = self.conn.execute("SELECT COUNT(*) AS n FROM task_usage_records").fetchone()
        return int(row["n"])

    def add_report(self, report_type: str, path: str, summary: str) -> str:
        report_id = new_id("report")
        self.conn.execute(
            "INSERT INTO reports (id, created_at, report_type, path, summary) VALUES (?, ?, ?, ?, ?)",
            (report_id, now_iso(), report_type, path, summary),
        )
        self.event(f"{report_type}_generated", {"report_id": report_id, "path": path})
        self.conn.commit()
        return report_id

    def event(self, event_name: str, properties: dict[str, Any]) -> None:
        self.conn.execute(
            "INSERT INTO events (id, created_at, event_name, properties_json) VALUES (?, ?, ?, ?)",
            (new_id("evt"), now_iso(), event_name, json.dumps(properties, ensure_ascii=False)),
        )

    def audit(self, action: str, details: dict[str, Any]) -> None:
        self.conn.execute(
            "INSERT INTO audit_logs (id, created_at, action, details_json) VALUES (?, ?, ?, ?)",
            (new_id("audit"), now_iso(), action, json.dumps(details, ensure_ascii=False)),
        )

    def delete_business_data(self) -> int:
        tables = ["import_batches", "task_usage_records", "risk_findings", "reports", "events"]
        total = 0
        for table in tables:
            cur = self.conn.execute(f"DELETE FROM {table}")
            total += cur.rowcount if cur.rowcount != -1 else 0
        self.audit("delete_all_business_data", {"deleted_count": total})
        self.conn.commit()
        self.conn.execute("VACUUM")
        return total


def usage_from_row(row: sqlite3.Row) -> TaskUsageRecord:
    return TaskUsageRecord(
        task_id=row["task_id"],
        import_id=row["import_id"],
        created_at=row["created_at"],
        user_goal=row["user_goal"] or "",
        model=row["model"] or "",
        mode=row["mode"] or "",
        input_tokens=row["input_tokens"],
        output_tokens=row["output_tokens"],
        cached_input_tokens=row["cached_input_tokens"],
        total_tokens=row["total_tokens"],
        credits=row["credits"],
        context_remaining_percent=row["context_remaining_percent"],
        context_used_tokens=row["context_used_tokens"],
        context_limit_tokens=row["context_limit_tokens"],
        five_hour_remaining_percent=row["five_hour_remaining_percent"],
        five_hour_reset=row["five_hour_reset"] or "",
        seven_day_remaining_percent=row["seven_day_remaining_percent"],
        seven_day_reset=row["seven_day_reset"] or "",
        quota_remaining=row["quota_remaining"],
        quota_limit=row["quota_limit"],
        source=row["source"] or "manual",
        status=row["status"] or "ok",
    )
