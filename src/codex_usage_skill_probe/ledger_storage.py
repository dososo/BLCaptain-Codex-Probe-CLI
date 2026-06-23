"""SQLite helpers for the local Codex session token ledger."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from .ledger_models import SessionSummary, SnapshotSummary, confidence_score
from .models import new_id, now_iso


LEDGER_SCHEMA = """
CREATE TABLE IF NOT EXISTS sources (
  id TEXT PRIMARY KEY,
  type TEXT NOT NULL,
  enabled INTEGER NOT NULL,
  confidence_ceiling TEXT NOT NULL,
  permission_scope TEXT NOT NULL,
  created_at TEXT NOT NULL,
  last_seen_at TEXT,
  metadata_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS projects (
  id TEXT PRIMARY KEY,
  name_hash TEXT NOT NULL,
  name_display TEXT,
  path_hash TEXT,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS sessions (
  id TEXT PRIMARY KEY,
  title_hash TEXT NOT NULL,
  title_display TEXT,
  project_id TEXT,
  started_at TEXT,
  ended_at TEXT,
  last_seen_at TEXT NOT NULL,
  model TEXT,
  source_id TEXT,
  metadata_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS usage_snapshots (
  id TEXT PRIMARY KEY,
  session_id TEXT,
  captured_at TEXT NOT NULL,
  source_id TEXT NOT NULL,
  input_tokens INTEGER,
  cached_input_tokens INTEGER,
  output_tokens INTEGER,
  total_tokens INTEGER,
  credits REAL,
  context_remaining_percent REAL,
  context_used_tokens INTEGER,
  context_limit_tokens INTEGER,
  raw_ref TEXT
);

CREATE TABLE IF NOT EXISTS usage_deltas (
  id TEXT PRIMARY KEY,
  from_snapshot_id TEXT,
  to_snapshot_id TEXT,
  session_id TEXT,
  token_delta INTEGER,
  credits_delta REAL,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS session_attributions (
  id TEXT PRIMARY KEY,
  session_id TEXT NOT NULL,
  delta_id TEXT NOT NULL,
  confidence_level TEXT NOT NULL,
  confidence_score REAL NOT NULL,
  evidence_summary TEXT NOT NULL,
  recommendation TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS privacy_audit_logs (
  id TEXT PRIMARY KEY,
  created_at TEXT NOT NULL,
  action TEXT NOT NULL,
  details_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS ledger_watch_state (
  id TEXT PRIMARY KEY,
  status TEXT NOT NULL,
  started_at TEXT,
  stopped_at TEXT,
  interval_seconds INTEGER,
  source_ids_json TEXT NOT NULL,
  last_message TEXT NOT NULL
);
"""


def ensure_ledger_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(LEDGER_SCHEMA)


def json_dumps(payload: dict[str, Any] | list[Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)


def hash_label(value: str) -> str:
    import hashlib

    clean = value.strip()
    if not clean:
        clean = "unknown"
    return hashlib.sha256(clean.encode("utf-8")).hexdigest()[:16]


def add_privacy_audit(conn: sqlite3.Connection, action: str, details: dict[str, Any]) -> None:
    conn.execute(
        """
        INSERT INTO privacy_audit_logs (id, created_at, action, details_json)
        VALUES (?, ?, ?, ?)
        """,
        (new_id("privacy"), now_iso(), action, json_dumps(details)),
    )


def upsert_source(
    conn: sqlite3.Connection,
    source_type: str,
    confidence_ceiling: str,
    permission_scope: str,
    *,
    enabled: bool = True,
    metadata: dict[str, Any] | None = None,
) -> str:
    source_id = f"source_{source_type}"
    now = now_iso()
    conn.execute(
        """
        INSERT INTO sources
          (id, type, enabled, confidence_ceiling, permission_scope, created_at, last_seen_at, metadata_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
          enabled=excluded.enabled,
          confidence_ceiling=excluded.confidence_ceiling,
          permission_scope=excluded.permission_scope,
          last_seen_at=excluded.last_seen_at,
          metadata_json=excluded.metadata_json
        """,
        (
            source_id,
            source_type,
            1 if enabled else 0,
            confidence_ceiling,
            permission_scope,
            now,
            now,
            json_dumps(metadata or {}),
        ),
    )
    add_privacy_audit(
        conn,
        "source_upserted",
        {"source_type": source_type, "confidence_ceiling": confidence_ceiling, "enabled": enabled},
    )
    return source_id


def upsert_project(conn: sqlite3.Connection, name: str, path_hint: str = "") -> str:
    project_id = f"project_{hash_label(name or path_hint or 'unknown')}"
    conn.execute(
        """
        INSERT INTO projects (id, name_hash, name_display, path_hash, created_at)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
          name_display=excluded.name_display,
          path_hash=excluded.path_hash
        """,
        (
            project_id,
            hash_label(name),
            name or "未命名项目",
            hash_label(path_hint) if path_hint else None,
            now_iso(),
        ),
    )
    return project_id


def upsert_session(
    conn: sqlite3.Connection,
    session_id: str,
    title: str,
    project_id: str | None,
    started_at: str | None,
    ended_at: str | None,
    last_seen_at: str,
    model: str = "",
    source_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> str:
    safe_id = session_id or f"session_{hash_label(title + last_seen_at)}"
    conn.execute(
        """
        INSERT INTO sessions
          (id, title_hash, title_display, project_id, started_at, ended_at, last_seen_at, model, source_id, metadata_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
          title_display=excluded.title_display,
          project_id=COALESCE(excluded.project_id, sessions.project_id),
          started_at=COALESCE(sessions.started_at, excluded.started_at),
          ended_at=COALESCE(excluded.ended_at, sessions.ended_at),
          last_seen_at=excluded.last_seen_at,
          model=COALESCE(NULLIF(excluded.model, ''), sessions.model),
          source_id=COALESCE(excluded.source_id, sessions.source_id),
          metadata_json=excluded.metadata_json
        """,
        (
            safe_id,
            hash_label(title),
            title or safe_id,
            project_id,
            started_at,
            ended_at,
            last_seen_at,
            model,
            source_id,
            json_dumps(metadata or {}),
        ),
    )
    return safe_id


def add_snapshot(
    conn: sqlite3.Connection,
    *,
    session_id: str | None,
    captured_at: str,
    source_id: str,
    input_tokens: int | None = None,
    cached_input_tokens: int | None = None,
    output_tokens: int | None = None,
    total_tokens: int | None = None,
    credits: float | None = None,
    context_remaining_percent: float | None = None,
    context_used_tokens: int | None = None,
    context_limit_tokens: int | None = None,
    raw_ref: str = "",
) -> str:
    snapshot_id = new_id("snap")
    conn.execute(
        """
        INSERT INTO usage_snapshots
          (id, session_id, captured_at, source_id, input_tokens, cached_input_tokens,
           output_tokens, total_tokens, credits, context_remaining_percent,
           context_used_tokens, context_limit_tokens, raw_ref)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            snapshot_id,
            session_id,
            captured_at,
            source_id,
            input_tokens,
            cached_input_tokens,
            output_tokens,
            total_tokens,
            credits,
            context_remaining_percent,
            context_used_tokens,
            context_limit_tokens,
            raw_ref,
        ),
    )
    return snapshot_id


def add_delta_and_attribution(
    conn: sqlite3.Connection,
    *,
    from_snapshot_id: str | None,
    to_snapshot_id: str,
    session_id: str,
    token_delta: int,
    credits_delta: float | None,
    confidence_level: str,
    evidence_summary: str,
    recommendation: str,
) -> str:
    delta_id = new_id("delta")
    conn.execute(
        """
        INSERT INTO usage_deltas
          (id, from_snapshot_id, to_snapshot_id, session_id, token_delta, credits_delta, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            delta_id,
            from_snapshot_id,
            to_snapshot_id,
            session_id,
            token_delta,
            credits_delta,
            now_iso(),
        ),
    )
    conn.execute(
        """
        INSERT INTO session_attributions
          (id, session_id, delta_id, confidence_level, confidence_score, evidence_summary, recommendation, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            new_id("attr"),
            session_id,
            delta_id,
            confidence_level,
            confidence_score(confidence_level),
            evidence_summary,
            recommendation,
            now_iso(),
        ),
    )
    return delta_id


def ledger_summary(
    conn: sqlite3.Connection,
    start: str | None = None,
    end: str | None = None,
    min_confidence: str | None = None,
) -> list[SessionSummary]:
    params: list[Any] = []
    where = ["1=1"]
    if start:
        where.append("COALESCE(s.ended_at, s.last_seen_at) >= ?")
        params.append(start)
    if end:
        where.append("COALESCE(s.started_at, s.last_seen_at) <= ?")
        params.append(end)
    if min_confidence:
        min_order = {"low": 1, "medium": 2, "high": 3, "exact": 4}.get(min_confidence, 1)
        where.append("COALESCE(dt.confidence_rank, 1) >= ?")
        params.append(min_order)

    rows = conn.execute(
        f"""
        WITH delta_totals AS (
          SELECT
            d.session_id,
            COALESCE(SUM(d.token_delta), 0) AS token_delta,
            SUM(d.credits_delta) AS credits_delta,
            COALESCE(MAX(CASE a.confidence_level WHEN 'exact' THEN 4 WHEN 'high' THEN 3 WHEN 'medium' THEN 2 ELSE 1 END), 1) AS confidence_rank,
            COALESCE(MAX(a.confidence_score), 0.0) AS confidence_score,
            COALESCE(MAX(a.recommendation), '继续观察') AS recommendation,
            COALESCE(MAX(a.evidence_summary), '暂无归因证据') AS evidence_summary
          FROM usage_deltas d
          LEFT JOIN session_attributions a ON a.delta_id = d.id
          GROUP BY d.session_id
        ),
        snapshot_context AS (
          SELECT
            session_id,
            MIN(captured_at) AS first_snapshot_at,
            MAX(captured_at) AS last_snapshot_at,
            MAX(
              CASE
                WHEN context_used_tokens IS NOT NULL AND context_limit_tokens IS NOT NULL AND context_limit_tokens > 0
                  THEN CAST(context_used_tokens AS REAL) * 100.0 / context_limit_tokens
                WHEN context_remaining_percent IS NOT NULL
                  THEN 100.0 - context_remaining_percent
                ELSE NULL
              END
            ) AS context_peak_percent
          FROM usage_snapshots
          GROUP BY session_id
        )
        SELECT
          s.id AS session_id,
          COALESCE(s.title_display, s.id) AS title,
          COALESCE(p.name_display, '未归属项目') AS project,
          COALESCE(s.model, '') AS model,
          COALESCE(s.started_at, sc.first_snapshot_at, '') AS started_at,
          COALESCE(s.ended_at, sc.last_snapshot_at, s.last_seen_at) AS ended_at,
          COALESCE(dt.token_delta, 0) AS token_delta,
          dt.credits_delta AS credits_delta,
          sc.context_peak_percent AS context_peak_percent,
          COALESCE(dt.confidence_rank, 1) AS confidence_rank,
          COALESCE(dt.confidence_score, 0.0) AS confidence_score,
          COALESCE(src.type, 'unknown') AS source_type,
          COALESCE(dt.recommendation, '继续观察') AS recommendation,
          COALESCE(dt.evidence_summary, '暂无归因证据') AS evidence_summary
        FROM sessions s
        LEFT JOIN projects p ON p.id = s.project_id
        LEFT JOIN delta_totals dt ON dt.session_id = s.id
        LEFT JOIN snapshot_context sc ON sc.session_id = s.id
        LEFT JOIN sources src ON src.id = s.source_id
        WHERE {' AND '.join(where)}
        ORDER BY token_delta DESC, ended_at DESC
        """,
        params,
    ).fetchall()
    return [
        SessionSummary(
            session_id=row["session_id"],
            title=row["title"],
            project=row["project"],
            model=row["model"] or "",
            started_at=row["started_at"] or "",
            ended_at=row["ended_at"] or "",
            token_delta=int(row["token_delta"] or 0),
            credits_delta=row["credits_delta"],
            context_peak_percent=row["context_peak_percent"],
            confidence_level={4: "exact", 3: "high", 2: "medium"}.get(row["confidence_rank"], "low"),
            confidence_score=float(row["confidence_score"] or 0),
            source_type=row["source_type"],
            recommendation=summary_recommendation(int(row["token_delta"] or 0), row["recommendation"]),
            evidence_summary=row["evidence_summary"],
        )
        for row in rows
    ]


def summary_recommendation(token_delta: int, fallback: str) -> str:
    if token_delta >= 100_000:
        return "停止当前长会话，保存成果后拆到新会话"
    if token_delta >= 50_000:
        return "降配或拆分后续任务，避免继续放大上下文"
    return fallback or "可以继续，但保留停止线"


def session_snapshots(conn: sqlite3.Connection, session_id: str) -> list[SnapshotSummary]:
    rows = conn.execute(
        """
        SELECT us.*, src.type AS source_type
        FROM usage_snapshots us
        LEFT JOIN sources src ON src.id = us.source_id
        WHERE us.session_id = ?
        ORDER BY us.captured_at
        """,
        (session_id,),
    ).fetchall()
    return [
        SnapshotSummary(
            snapshot_id=row["id"],
            captured_at=row["captured_at"],
            total_tokens=row["total_tokens"],
            credits=row["credits"],
            context_used_tokens=row["context_used_tokens"],
            context_limit_tokens=row["context_limit_tokens"],
            context_remaining_percent=row["context_remaining_percent"],
            source_type=row["source_type"] or "unknown",
        )
        for row in rows
    ]


def source_rows(conn: sqlite3.Connection) -> list[dict[str, object]]:
    rows = conn.execute(
        """
        SELECT id, type, enabled, confidence_ceiling, permission_scope, created_at, last_seen_at
        FROM sources
        ORDER BY type
        """
    ).fetchall()
    return [dict(row) for row in rows]


def privacy_audit_rows(conn: sqlite3.Connection, limit: int = 30) -> list[dict[str, object]]:
    rows = conn.execute(
        """
        SELECT created_at, action, details_json
        FROM privacy_audit_logs
        ORDER BY created_at DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()
    return [dict(row) for row in rows]


def delete_ledger_data(conn: sqlite3.Connection) -> int:
    tables = [
        "sources",
        "projects",
        "sessions",
        "usage_snapshots",
        "usage_deltas",
        "session_attributions",
        "ledger_watch_state",
    ]
    total = 0
    for table in tables:
        cur = conn.execute(f"DELETE FROM {table}")
        total += cur.rowcount if cur.rowcount != -1 else 0
    add_privacy_audit(conn, "delete_ledger_business_data", {"deleted_count": total})
    conn.commit()
    return total


def write_watch_state(
    conn: sqlite3.Connection,
    *,
    status: str,
    interval_seconds: int = 60,
    source_ids: list[str] | None = None,
    message: str = "",
) -> None:
    conn.execute("DELETE FROM ledger_watch_state")
    now = now_iso()
    conn.execute(
        """
        INSERT INTO ledger_watch_state
          (id, status, started_at, stopped_at, interval_seconds, source_ids_json, last_message)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "watch_default",
            status,
            now if status == "running" else None,
            now if status == "stopped" else None,
            interval_seconds,
            json_dumps(source_ids or []),
            message,
        ),
    )
    add_privacy_audit(conn, f"watch_{status}", {"interval_seconds": interval_seconds, "source_count": len(source_ids or [])})


def read_watch_state(conn: sqlite3.Connection) -> dict[str, Any]:
    row = conn.execute("SELECT * FROM ledger_watch_state WHERE id = 'watch_default'").fetchone()
    if not row:
        return {"status": "stopped", "last_message": "watch 尚未启动"}
    return {
        "status": row["status"],
        "started_at": row["started_at"],
        "stopped_at": row["stopped_at"],
        "interval_seconds": row["interval_seconds"],
        "source_ids": json.loads(row["source_ids_json"] or "[]"),
        "last_message": row["last_message"],
    }


def write_static_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
