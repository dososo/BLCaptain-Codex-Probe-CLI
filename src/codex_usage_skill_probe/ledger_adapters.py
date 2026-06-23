"""User-provided ledger data adapters."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from .ledger_storage import (
    add_delta_and_attribution,
    add_privacy_audit,
    add_snapshot,
    upsert_project,
    upsert_session,
    upsert_source,
)


def coerce_int(value: Any) -> int | None:
    if value is None or value == "":
        return None
    if isinstance(value, int):
        return value
    try:
        return int(str(value).replace(",", "").replace("_", "").strip())
    except ValueError:
        return None


def coerce_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    if isinstance(value, float | int):
        return float(value)
    try:
        return float(str(value).replace(",", "").replace("_", "").strip())
    except ValueError:
        return None


def load_records(path: Path) -> dict[str, list[dict[str, Any]]]:
    suffix = path.suffix.lower()
    if suffix == ".json":
        payload = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(payload, list):
            return {"sessions": payload}
        if "sessions" in payload or "snapshots" in payload:
            return {
                "sessions": list(payload.get("sessions", [])),
                "snapshots": list(payload.get("snapshots", [])),
            }
        return {"sessions": [payload]}
    if suffix == ".csv":
        with path.open("r", encoding="utf-8", newline="") as handle:
            return {"sessions": list(csv.DictReader(handle))}
    raise ValueError(f"Unsupported ledger data file: {path}")


def import_official_export(conn, path: Path) -> dict[str, object]:
    payload = load_records(path)
    source_id = upsert_source(
        conn,
        "official_export",
        "exact",
        "用户显式提供的官方导出 CSV/JSON；不读取浏览器、cookie、token 或聊天正文。",
        metadata={"filename": path.name},
    )
    imported_sessions = 0
    imported_snapshots = 0

    for record in payload.get("sessions", []):
        session_id = str(record.get("session_id") or record.get("id") or "").strip()
        title = str(record.get("title") or record.get("session_title") or session_id or "未命名会话")
        project_name = str(record.get("project") or record.get("project_name") or "未归属项目")
        project_id = upsert_project(conn, project_name)
        started_at = str(record.get("started_at") or record.get("start_time") or record.get("created_at") or "")
        ended_at = str(record.get("ended_at") or record.get("end_time") or record.get("last_seen_at") or started_at)
        safe_session_id = upsert_session(
            conn,
            session_id or f"session_{imported_sessions + 1}",
            title,
            project_id,
            started_at or None,
            ended_at or None,
            ended_at or started_at,
            model=str(record.get("model") or ""),
            source_id=source_id,
            metadata={"source": "official_export"},
        )
        total_tokens = coerce_int(record.get("total_tokens"))
        input_tokens = coerce_int(record.get("input_tokens"))
        cached_tokens = coerce_int(record.get("cached_input_tokens"))
        output_tokens = coerce_int(record.get("output_tokens"))
        if total_tokens is None:
            total_tokens = sum(v or 0 for v in [input_tokens, cached_tokens, output_tokens]) or None
        credits = coerce_float(record.get("credits"))
        snapshot_id = add_snapshot(
            conn,
            session_id=safe_session_id,
            captured_at=ended_at or started_at,
            source_id=source_id,
            input_tokens=input_tokens,
            cached_input_tokens=cached_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            credits=credits,
            context_remaining_percent=coerce_float(record.get("context_remaining_percent")),
            context_used_tokens=coerce_int(record.get("context_used_tokens")),
            context_limit_tokens=coerce_int(record.get("context_limit_tokens")),
            raw_ref=f"{path.name}:sessions",
        )
        add_delta_and_attribution(
            conn,
            from_snapshot_id=None,
            to_snapshot_id=snapshot_id,
            session_id=safe_session_id,
            token_delta=total_tokens or 0,
            credits_delta=credits,
            confidence_level="exact",
            evidence_summary="官方导出直接提供会话级用量字段",
            recommendation=recommendation(total_tokens or 0),
        )
        imported_sessions += 1
        imported_snapshots += 1

    for record in payload.get("snapshots", []):
        imported_snapshots += import_snapshot_record(conn, record, source_id, path.name, confidence="high")

    add_privacy_audit(
        conn,
        "official_export_imported",
        {"filename": path.name, "sessions": imported_sessions, "snapshots": imported_snapshots},
    )
    conn.commit()
    return {"sessions": imported_sessions, "snapshots": imported_snapshots, "source_id": source_id}


def import_snapshot_delta(conn, path: Path) -> dict[str, object]:
    payload = load_records(path)
    source_id = upsert_source(
        conn,
        "snapshot_delta",
        "high",
        "用户显式提供的本地快照文件；只读取会话元信息和 token 数字。",
        metadata={"filename": path.name},
    )
    snapshots = payload.get("snapshots") or payload.get("sessions") or []
    imported = 0
    for record in snapshots:
        imported += import_snapshot_record(conn, record, source_id, path.name, confidence=record_confidence(record))
    add_privacy_audit(conn, "snapshot_delta_imported", {"filename": path.name, "snapshots": imported})
    conn.commit()
    return {"sessions": count_distinct_sessions(snapshots), "snapshots": imported, "source_id": source_id}


def import_snapshot_record(conn, record: dict[str, Any], source_id: str, filename: str, confidence: str) -> int:
    session_id = str(record.get("session_id") or record.get("active_session_id") or "").strip()
    title = str(record.get("title") or session_id or "未知会话")
    project_name = str(record.get("project") or "未归属项目")
    project_id = upsert_project(conn, project_name)
    captured_at = str(record.get("captured_at") or record.get("created_at") or record.get("last_seen_at") or "")
    if not captured_at:
        raise ValueError("snapshot record missing captured_at")
    safe_session_id = upsert_session(
        conn,
        session_id or f"session_unknown_{captured_at}",
        title,
        project_id,
        str(record.get("started_at") or "") or None,
        str(record.get("ended_at") or "") or None,
        captured_at,
        model=str(record.get("model") or ""),
        source_id=source_id,
        metadata={"source": "snapshot_delta"},
    )
    snapshot_id = add_snapshot(
        conn,
        session_id=safe_session_id,
        captured_at=captured_at,
        source_id=source_id,
        input_tokens=coerce_int(record.get("input_tokens")),
        cached_input_tokens=coerce_int(record.get("cached_input_tokens")),
        output_tokens=coerce_int(record.get("output_tokens")),
        total_tokens=coerce_int(record.get("total_tokens")),
        credits=coerce_float(record.get("credits")),
        context_remaining_percent=coerce_float(record.get("context_remaining_percent")),
        context_used_tokens=coerce_int(record.get("context_used_tokens")),
        context_limit_tokens=coerce_int(record.get("context_limit_tokens")),
        raw_ref=f"{filename}:snapshots",
    )
    previous = conn.execute(
        """
        SELECT id, total_tokens, credits
        FROM usage_snapshots
        WHERE session_id = ? AND captured_at < ? AND id != ?
        ORDER BY captured_at DESC
        LIMIT 1
        """,
        (safe_session_id, captured_at, snapshot_id),
    ).fetchone()
    current_total = coerce_int(record.get("total_tokens")) or 0
    current_credits = coerce_float(record.get("credits"))
    if previous:
        token_delta = max(0, current_total - (previous["total_tokens"] or 0))
        credits_delta = None
        if current_credits is not None and previous["credits"] is not None:
            credits_delta = max(0.0, current_credits - previous["credits"])
        from_snapshot_id = previous["id"]
    else:
        token_delta = coerce_int(record.get("token_delta")) or 0
        credits_delta = coerce_float(record.get("credits_delta")) or 0.0
        from_snapshot_id = None
    add_delta_and_attribution(
        conn,
        from_snapshot_id=from_snapshot_id,
        to_snapshot_id=snapshot_id,
        session_id=safe_session_id,
        token_delta=token_delta,
        credits_delta=credits_delta,
        confidence_level=confidence,
        evidence_summary=confidence_evidence(confidence),
        recommendation=recommendation(token_delta),
    )
    return 1


def record_confidence(record: dict[str, Any]) -> str:
    if not record.get("session_id") and not record.get("active_session_id"):
        return "low"
    active_count = coerce_int(record.get("active_session_count"))
    if active_count and active_count > 1:
        return "medium"
    if record.get("source_type") == "local_status":
        return "high"
    return "high"


def confidence_evidence(confidence: str) -> str:
    return {
        "high": "同一会话快照提供 token delta，可高置信归因",
        "medium": "快照区间存在多会话或窗口重叠，按可见元信息归因",
        "low": "缺少稳定会话标识，仅作为估算",
    }.get(confidence, "快照提供会话用量字段")


def recommendation(token_delta: int) -> str:
    if token_delta >= 100_000:
        return "停止当前长会话，保存成果后拆到新会话"
    if token_delta >= 50_000:
        return "降配或拆分后续任务，避免继续放大上下文"
    return "可以继续，但保留停止线"


def count_distinct_sessions(records: list[dict[str, Any]]) -> int:
    ids = {str(item.get("session_id") or item.get("active_session_id") or "") for item in records}
    return len({item for item in ids if item})
