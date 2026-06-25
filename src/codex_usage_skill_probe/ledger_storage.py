"""SQLite helpers for the local Codex session token ledger."""

from __future__ import annotations

import json
import sqlite3
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from .ledger_models import (
    BudgetAlert,
    ProjectSummary,
    SessionIntervalSummary,
    SessionSummary,
    SnapshotSummary,
    SourceConfidenceSummary,
    TaskTypeSummary,
    WeeklySummary,
    confidence_score,
)
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


def project_summary(
    conn: sqlite3.Connection,
    start: str | None = None,
    end: str | None = None,
    min_confidence: str | None = None,
) -> list[ProjectSummary]:
    sessions = ledger_summary(conn, start=start, end=end, min_confidence=min_confidence)
    grouped: dict[str, list[SessionSummary]] = defaultdict(list)
    for session in sessions:
        grouped[session.project].append(session)
    summaries = [build_project_summary(project, items) for project, items in grouped.items()]
    return sorted(summaries, key=lambda item: (item.token_delta, item.session_count), reverse=True)


def build_project_summary(project: str, sessions: list[SessionSummary]) -> ProjectSummary:
    top = max(sessions, key=lambda item: item.token_delta)
    token_total = sum(item.token_delta for item in sessions)
    credits = sum_known_credits(sessions)
    return ProjectSummary(
        project=project,
        session_count=len(sessions),
        token_delta=token_total,
        credits_delta=credits,
        top_session_id=top.session_id,
        top_session_title=top.title,
        top_session_tokens=top.token_delta,
        confidence_counts=confidence_counts(sessions),
        recommendation=summary_recommendation(token_total, "可以继续，但保留停止线"),
    )


def weekly_summary(
    conn: sqlite3.Connection,
    start: str | None = None,
    end: str | None = None,
    min_confidence: str | None = None,
) -> list[WeeklySummary]:
    sessions = ledger_summary(conn, start=start, end=end, min_confidence=min_confidence)
    grouped: dict[tuple[int, int], list[SessionSummary]] = defaultdict(list)
    for session in sessions:
        grouped[local_week_key(session.ended_at or session.started_at)].append(session)

    summaries = []
    for (year, week), items in grouped.items():
        week_start = datetime.fromisocalendar(year, week, 1).date()
        week_end = week_start + timedelta(days=6)
        project_totals: dict[str, int] = defaultdict(int)
        for item in items:
            project_totals[item.project] += item.token_delta
        top_project = max(project_totals.items(), key=lambda item: item[1])[0]
        top_session = max(items, key=lambda item: item.token_delta)
        token_total = sum(item.token_delta for item in items)
        summaries.append(
            WeeklySummary(
                week_label=f"{year}-W{week:02d}",
                week_start=week_start.isoformat(),
                week_end=week_end.isoformat(),
                session_count=len(items),
                project_count=len(project_totals),
                token_delta=token_total,
                credits_delta=sum_known_credits(items),
                top_project=top_project,
                top_session_id=top_session.session_id,
                top_session_title=top_session.title,
                top_session_tokens=top_session.token_delta,
                confidence_counts=confidence_counts(items),
                recommendation=summary_recommendation(token_total, "可以继续，但保留停止线"),
            )
        )
    return sorted(summaries, key=lambda item: item.week_start, reverse=True)


def session_intervals(
    conn: sqlite3.Connection,
    start: str | None = None,
    end: str | None = None,
    *,
    session_id: str | None = None,
) -> list[SessionIntervalSummary]:
    sessions = ledger_summary(conn, start=start, end=end)
    if session_id:
        sessions = [item for item in sessions if item.session_id == session_id]
    intervals: list[SessionIntervalSummary] = []
    for session in sessions:
        snapshots = session_snapshots(conn, session.session_id)
        if len(snapshots) >= 2:
            previous = snapshots[0]
            for current in snapshots[1:]:
                token_delta = max(0, int(current.total_tokens or 0) - int(previous.total_tokens or 0))
                credits_delta = interval_credits_delta(previous, current)
                intervals.append(build_interval_summary(session, previous, current, token_delta, credits_delta))
                previous = current
        elif session.token_delta > 0:
            intervals.append(
                SessionIntervalSummary(
                    session_id=session.session_id,
                    title=session.title,
                    project=session.project,
                    model=session.model,
                    start_at=session.started_at,
                    end_at=session.ended_at,
                    token_delta=session.token_delta,
                    credits_delta=session.credits_delta,
                    context_used_percent=session.context_peak_percent,
                    stage_label=infer_task_type(session),
                    severity=usage_severity(session.token_delta),
                    confidence_level=session.confidence_level,
                    source_type=session.source_type,
                    recommendation=interval_recommendation(session.token_delta, session.context_peak_percent),
                    evidence_summary=session.evidence_summary,
                )
            )
    return sorted(intervals, key=lambda item: (item.token_delta, item.end_at), reverse=True)


def build_interval_summary(
    session: SessionSummary,
    previous: SnapshotSummary,
    current: SnapshotSummary,
    token_delta: int,
    credits_delta: float | None,
) -> SessionIntervalSummary:
    context_used = context_used_percent(current)
    return SessionIntervalSummary(
        session_id=session.session_id,
        title=session.title,
        project=session.project,
        model=session.model,
        start_at=previous.captured_at,
        end_at=current.captured_at,
        token_delta=token_delta,
        credits_delta=credits_delta,
        context_used_percent=context_used,
        stage_label=infer_task_type(session),
        severity=usage_severity(token_delta),
        confidence_level=session.confidence_level,
        source_type=current.source_type or session.source_type,
        recommendation=interval_recommendation(token_delta, context_used),
        evidence_summary=session.evidence_summary,
    )


def budget_alerts(
    conn: sqlite3.Connection,
    start: str | None = None,
    end: str | None = None,
    *,
    session_threshold: int = 100_000,
    project_threshold: int = 250_000,
    ledger_threshold: int = 500_000,
    context_remaining_threshold: float = 20.0,
) -> list[BudgetAlert]:
    sessions = ledger_summary(conn, start=start, end=end)
    projects = project_summary(conn, start=start, end=end)
    alerts: list[BudgetAlert] = []
    for session in sessions:
        if session.token_delta >= session_threshold:
            alerts.append(
                build_alert(
                    "session",
                    session.session_id,
                    session.title,
                    session.token_delta,
                    session_threshold,
                    session.confidence_level,
                    "单会话 token delta 超过本地预算阈值",
                    summary_recommendation(session.token_delta, session.recommendation),
                )
            )
        if session.context_peak_percent is not None:
            remaining = max(0.0, 100.0 - float(session.context_peak_percent))
            if remaining <= context_remaining_threshold:
                alerts.append(
                    build_alert(
                        "context",
                        session.session_id,
                        session.title,
                        int(round(session.context_peak_percent)),
                        max(1.0, 100.0 - context_remaining_threshold),
                        session.confidence_level,
                        f"上下文剩余约 {remaining:.1f}%，低于本地阈值 {context_remaining_threshold:.1f}%",
                        "停止继续堆上下文，保存结论后开新会话",
                    )
                )
    for project in projects:
        if project.token_delta >= project_threshold:
            alerts.append(
                build_alert(
                    "project",
                    project.project,
                    project.project,
                    project.token_delta,
                    project_threshold,
                    strongest_confidence(project.confidence_counts),
                    "项目周期 token delta 超过本地预算阈值",
                    project.recommendation,
                )
            )
    ledger_total = sum(item.token_delta for item in sessions)
    if ledger_total >= ledger_threshold:
        alerts.append(
            build_alert(
                "ledger",
                "current_range",
                "当前时间范围总账",
                ledger_total,
                ledger_threshold,
                strongest_confidence(confidence_counts(sessions)),
                "当前时间范围总账超过本地预算阈值",
                summary_recommendation(ledger_total, "暂停大任务，拆分会话和项目再继续"),
            )
        )
    return sorted(alerts, key=lambda item: (severity_rank(item.severity), item.usage_percent), reverse=True)


def build_alert(
    scope: str,
    scope_id: str,
    name: str,
    token_delta: int,
    threshold: float,
    confidence_level: str,
    reason: str,
    recommendation: str,
) -> BudgetAlert:
    usage_percent = float(token_delta) * 100.0 / threshold if threshold else 0.0
    return BudgetAlert(
        scope=scope,
        scope_id=scope_id,
        name=name,
        token_delta=token_delta,
        threshold=threshold,
        usage_percent=usage_percent,
        severity=alert_severity(usage_percent),
        confidence_level=confidence_level,
        reason=reason,
        recommendation=recommendation,
    )


def task_type_summary(
    conn: sqlite3.Connection,
    start: str | None = None,
    end: str | None = None,
) -> list[TaskTypeSummary]:
    sessions = ledger_summary(conn, start=start, end=end)
    grouped: dict[str, list[SessionSummary]] = defaultdict(list)
    for session in sessions:
        grouped[infer_task_type(session)].append(session)
    results = []
    for task_type, items in grouped.items():
        top = max(items, key=lambda item: item.token_delta)
        token_total = sum(item.token_delta for item in items)
        results.append(
            TaskTypeSummary(
                task_type=task_type,
                session_count=len(items),
                token_delta=token_total,
                credits_delta=sum_known_credits(items),
                top_session_id=top.session_id,
                top_session_title=top.title,
                top_session_tokens=top.token_delta,
                confidence_counts=confidence_counts(items),
                recommendation=summary_recommendation(token_total, "继续观察"),
            )
        )
    return sorted(results, key=lambda item: (item.token_delta, item.session_count), reverse=True)


def source_confidence_summary(conn: sqlite3.Connection) -> list[SourceConfidenceSummary]:
    rows = conn.execute(
        """
        SELECT
          src.type AS source_type,
          src.enabled AS enabled,
          src.confidence_ceiling AS confidence_ceiling,
          src.permission_scope AS permission_scope,
          COUNT(DISTINCT s.id) AS session_count,
          COUNT(DISTINCT us.id) AS snapshot_count,
          SUM(CASE WHEN us.session_id IS NOT NULL THEN 1 ELSE 0 END) AS session_field_count,
          SUM(CASE WHEN us.total_tokens IS NOT NULL THEN 1 ELSE 0 END) AS total_tokens_count,
          SUM(CASE WHEN us.credits IS NOT NULL THEN 1 ELSE 0 END) AS credits_count,
          SUM(CASE WHEN us.context_limit_tokens IS NOT NULL THEN 1 ELSE 0 END) AS context_limit_count,
          SUM(CASE WHEN us.context_remaining_percent IS NOT NULL OR us.context_used_tokens IS NOT NULL THEN 1 ELSE 0 END) AS context_state_count,
          SUM(CASE WHEN s.model IS NOT NULL AND s.model != '' THEN 1 ELSE 0 END) AS model_count,
          SUM(CASE WHEN s.project_id IS NOT NULL THEN 1 ELSE 0 END) AS project_count
        FROM sources src
        LEFT JOIN usage_snapshots us ON us.source_id = src.id
        LEFT JOIN sessions s ON s.id = us.session_id OR s.source_id = src.id
        GROUP BY src.id
        ORDER BY src.type
        """
    ).fetchall()
    summaries: list[SourceConfidenceSummary] = []
    for row in rows:
        snapshot_count = int(row["snapshot_count"] or 0)
        fields_present, missing_fields = source_fields(row, snapshot_count)
        summaries.append(
            SourceConfidenceSummary(
                source_type=row["source_type"],
                enabled=bool(row["enabled"]),
                confidence_ceiling=row["confidence_ceiling"],
                session_count=int(row["session_count"] or 0),
                snapshot_count=snapshot_count,
                fields_present=fields_present,
                missing_fields=missing_fields,
                diagnosis=source_diagnosis(row["source_type"], row["confidence_ceiling"], missing_fields, snapshot_count),
                privacy_note=row["permission_scope"],
            )
        )
    return summaries


def local_week_key(value: str) -> tuple[int, int]:
    try:
        parsed = datetime.fromisoformat((value or "").replace("Z", "+00:00"))
    except ValueError:
        parsed = datetime.now().astimezone()
    parsed = parsed.astimezone() if parsed.tzinfo else parsed
    year, week, _ = parsed.date().isocalendar()
    return year, week


def sum_known_credits(sessions: list[SessionSummary]) -> float | None:
    values = [item.credits_delta for item in sessions if item.credits_delta is not None]
    if not values:
        return None
    return sum(values)


def confidence_counts(sessions: list[SessionSummary]) -> dict[str, int]:
    counts = {"exact": 0, "high": 0, "medium": 0, "low": 0}
    for session in sessions:
        counts[session.confidence_level if session.confidence_level in counts else "low"] += 1
    return counts


def interval_credits_delta(previous: SnapshotSummary, current: SnapshotSummary) -> float | None:
    if previous.credits is None or current.credits is None:
        return None
    if previous.source_type != current.source_type or current.source_type == "local_codex_rollout":
        return None
    return max(0.0, float(current.credits) - float(previous.credits))


def context_used_percent(snapshot: SnapshotSummary) -> float | None:
    if snapshot.context_used_tokens is not None and snapshot.context_limit_tokens:
        return float(snapshot.context_used_tokens) * 100.0 / float(snapshot.context_limit_tokens)
    if snapshot.context_remaining_percent is not None:
        return max(0.0, 100.0 - float(snapshot.context_remaining_percent))
    return None


def usage_severity(token_delta: int) -> str:
    if token_delta >= 80_000:
        return "critical"
    if token_delta >= 50_000:
        return "high"
    if token_delta >= 20_000:
        return "medium"
    return "low"


def severity_rank(severity: str) -> int:
    return {"critical": 4, "high": 3, "medium": 2, "low": 1}.get(severity, 0)


def alert_severity(usage_percent: float) -> str:
    if usage_percent >= 130:
        return "critical"
    if usage_percent >= 100:
        return "high"
    if usage_percent >= 80:
        return "medium"
    return "low"


def interval_recommendation(token_delta: int, context_used_percent_value: float | None) -> str:
    if context_used_percent_value is not None and context_used_percent_value >= 80:
        return "停止继续堆上下文，保存结论后开新会话"
    if token_delta >= 80_000:
        return "停止当前阶段，沉淀结果后拆到新会话"
    if token_delta >= 50_000:
        return "降配收尾，避免继续放大上下文"
    if token_delta >= 20_000:
        return "观察该阶段，后续只带必要文件和结论"
    return "可以继续，但保留停止线"


def infer_task_type(session: SessionSummary) -> str:
    text = " ".join([session.title, session.project, session.evidence_summary, session.recommendation]).lower()
    rules = [
        ("发布交付", ["release", "github", "push", "commit", "tag", "发布", "提交", "推送"]),
        ("验证测试", ["test", "ci", "compile", "acceptance", "verify", "验收", "验证", "测试"]),
        ("调试修复", ["debug", "fix", "bug", "error", "failure", "修复", "报错"]),
        ("文档报告", ["readme", "doc", "docs", "report", "markdown", "文档", "报告", "周报"]),
        ("素材生成", ["image", "screenshot", "cover", "poster", "xiaohongshu", "截图", "封面", "小红书"]),
        ("调研分析", ["prd", "research", "analysis", "opportunity", "调研", "分析", "机会"]),
        ("开发实现", ["code", "cli", "feature", "storage", "dashboard", "开发", "实现"]),
    ]
    for label, keywords in rules:
        if any(keyword in text for keyword in keywords):
            return label
    return "未知任务"


def strongest_confidence(counts: dict[str, int]) -> str:
    for level in ["exact", "high", "medium", "low"]:
        if counts.get(level, 0):
            return level
    return "low"


def source_fields(row: sqlite3.Row, snapshot_count: int) -> tuple[list[str], list[str]]:
    checks = {
        "session_id": row["session_field_count"],
        "total_tokens": row["total_tokens_count"],
        "credits": row["credits_count"],
        "context_window": row["context_limit_count"],
        "context_state": row["context_state_count"],
        "model": row["model_count"],
        "project": row["project_count"],
    }
    present: list[str] = []
    missing: list[str] = []
    for field, count in checks.items():
        if int(count or 0) > 0:
            present.append(field)
        elif snapshot_count > 0:
            missing.append(field)
        else:
            missing.append(field)
    return present, missing


def source_diagnosis(source_type: str, confidence_ceiling: str, missing_fields: list[str], snapshot_count: int) -> str:
    if snapshot_count == 0:
        return "已登记数据源，但当前账本没有该来源快照；无法做会话级归因。"
    if not missing_fields:
        return "字段覆盖完整，可用于当前来源口径下的高质量归因。"
    if "total_tokens" in missing_fields:
        return "缺少 total_tokens，无法精确计算会话级 token delta。"
    if confidence_ceiling == "exact":
        return "官方或等价导出字段可用，但仍需注意 credits 口径不等同于账单金额。"
    if source_type == "local_codex_rollout":
        return "本地 rollout 只读取 token 白名单字段；schema 变动时可能出现缺字段。"
    return "可用于治理参考，但缺字段会降低精细度。"


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
