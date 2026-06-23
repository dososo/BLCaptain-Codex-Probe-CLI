"""Safe local Codex rollout history reader."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .ledger_adapters import coerce_float, coerce_int, recommendation
from .ledger_storage import (
    add_delta_and_attribution,
    add_privacy_audit,
    add_snapshot,
    hash_label,
    upsert_project,
    upsert_session,
    upsert_source,
)


TOKEN_MARKERS = ("last_token_usage", "total_token_usage", "rate_limits")
SKIP_MARKERS = ("response_item", "assistant_message", "user_message", '"content"', '"arguments"')
UUID_RE = re.compile(r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}")


@dataclass(frozen=True)
class LocalHistoryDryRun:
    root_hash: str
    file_count: int
    token_record_count: int
    importable_record_count: int
    skipped_content_lines: int
    files: list[dict[str, object]]


def default_codex_root() -> Path:
    return Path.home() / ".codex"


def discover_rollout_files(root: Path) -> list[Path]:
    if not root.exists() or not root.is_dir():
        return []
    return sorted(root.glob("**/rollout-*.jsonl"), key=lambda item: item.stat().st_mtime)


def inspect_local_codex(root: Path | None = None, *, limit_files: int | None = None) -> LocalHistoryDryRun:
    safe_root = root or default_codex_root()
    files = discover_rollout_files(safe_root)
    if limit_files:
        files = files[-limit_files:]
    summaries = []
    token_records = 0
    importable_records = 0
    skipped_content = 0
    for path in files:
        summary = inspect_rollout_file(path)
        summaries.append(summary)
        token_records += int(summary["token_record_count"])
        importable_records += int(summary["importable_record_count"])
        skipped_content += int(summary["skipped_content_lines"])
    return LocalHistoryDryRun(
        root_hash=hash_label(str(safe_root.expanduser())),
        file_count=len(files),
        token_record_count=token_records,
        importable_record_count=importable_records,
        skipped_content_lines=skipped_content,
        files=summaries,
    )


def inspect_rollout_file(path: Path) -> dict[str, object]:
    token_records = 0
    importable = 0
    skipped_content = 0
    line_count = 0
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            line_count += 1
            if not any(marker in line for marker in TOKEN_MARKERS):
                continue
            if any(marker in line for marker in SKIP_MARKERS):
                skipped_content += 1
                continue
            token_records += 1
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            if extract_usage_record(record, path, line_count):
                importable += 1
    stat = path.stat()
    return {
        "file_hash": hash_label(str(path)),
        "name_prefix": path.name[:36],
        "size_bytes": stat.st_size,
        "mtime": datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat(),
        "line_count": line_count,
        "token_record_count": token_records,
        "importable_record_count": importable,
        "skipped_content_lines": skipped_content,
    }


def import_local_history(
    conn,
    root: Path | None = None,
    *,
    dry_run: bool = False,
    limit_files: int | None = None,
) -> dict[str, object]:
    safe_root = root or default_codex_root()
    dry = inspect_local_codex(safe_root, limit_files=limit_files)
    if dry_run:
        return dry_run_payload(dry, wrote=False)

    source_id = upsert_source(
        conn,
        "local_codex_rollout",
        "high",
        "只读取 Codex rollout JSONL 中的 token 用量白名单字段；跳过聊天正文、prompt、assistant 输出和工具参数。",
        metadata={"root_hash": dry.root_hash, "file_count": dry.file_count},
    )
    imported = 0
    skipped_duplicates = 0
    files = discover_rollout_files(safe_root)
    if limit_files:
        files = files[-limit_files:]
    for path in files:
        with path.open("r", encoding="utf-8", errors="replace") as handle:
            for line_number, line in enumerate(handle, 1):
                if not any(marker in line for marker in TOKEN_MARKERS):
                    continue
                if any(marker in line for marker in SKIP_MARKERS):
                    continue
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    continue
                record = extract_usage_record(event, path, line_number)
                if not record:
                    continue
                raw_ref = record["raw_ref"]
                exists = conn.execute(
                    "SELECT 1 FROM usage_snapshots WHERE raw_ref = ? LIMIT 1",
                    (raw_ref,),
                ).fetchone()
                if exists:
                    skipped_duplicates += 1
                    continue
                import_one_history_record(conn, record, source_id)
                imported += 1
    add_privacy_audit(
        conn,
        "local_codex_history_imported",
        {
            "root_hash": dry.root_hash,
            "files": dry.file_count,
            "token_records": dry.token_record_count,
            "imported": imported,
            "skipped_duplicates": skipped_duplicates,
        },
    )
    conn.commit()
    payload = dry_run_payload(dry, wrote=True)
    payload.update({"imported_snapshots": imported, "skipped_duplicates": skipped_duplicates, "source_id": source_id})
    return payload


def extract_usage_record(event: dict[str, Any], path: Path, line_number: int) -> dict[str, Any] | None:
    payload = event.get("payload") if isinstance(event.get("payload"), dict) else event
    info = payload.get("info") if isinstance(payload.get("info"), dict) else {}
    last_usage = first_dict(info.get("last_token_usage"), payload.get("last_token_usage"))
    total_usage = first_dict(info.get("total_token_usage"), payload.get("total_token_usage"))
    if not last_usage and not total_usage:
        return None
    session_id = extract_session_id(path, event, payload)
    captured_at = first_text(
        event.get("timestamp"),
        payload.get("timestamp"),
        payload.get("created_at"),
        payload.get("started_at"),
        timestamp_from_filename(path),
    )
    input_tokens = token_value(last_usage, "input_tokens", "prompt_tokens", "request_tokens")
    cached_tokens = token_value(last_usage, "cached_input_tokens", "cached_tokens", "cache_read_tokens")
    output_tokens = token_value(last_usage, "output_tokens", "completion_tokens", "response_tokens")
    last_total = token_value(last_usage, "total_tokens", "tokens")
    total_tokens = token_value(total_usage, "total_tokens", "tokens")
    if total_tokens is None:
        total_tokens = sum_tokens(input_tokens, cached_tokens, output_tokens) or last_total
    token_delta = last_total if last_total is not None else sum_tokens(input_tokens, cached_tokens, output_tokens)
    rate_limits = payload.get("rate_limits") if isinstance(payload.get("rate_limits"), dict) else {}
    credits = None
    if isinstance(rate_limits.get("credits"), dict):
        credits = coerce_float(rate_limits["credits"].get("remaining"))
    model = first_text(payload.get("model"), info.get("model"))
    cwd = first_text(payload.get("cwd"), info.get("cwd"))
    turn_id = first_text(payload.get("turn_id"), info.get("turn_id"))
    return {
        "session_id": session_id,
        "title": f"Codex 会话 {session_id[-8:]}",
        "project_name": f"本地项目 {hash_label(cwd or str(path.parent))}",
        "path_hash": hash_label(cwd or str(path.parent)),
        "captured_at": captured_at,
        "input_tokens": input_tokens,
        "cached_input_tokens": cached_tokens,
        "output_tokens": output_tokens,
        "total_tokens": total_tokens,
        "token_delta": token_delta or 0,
        "credits": credits,
        "context_limit_tokens": coerce_int(payload.get("model_context_window") or info.get("model_context_window")),
        "model": model,
        "turn_id": turn_id,
        "raw_ref": f"local:{hash_label(str(path))}:{line_number}",
    }


def import_one_history_record(conn, record: dict[str, Any], source_id: str) -> None:
    project_id = upsert_project(conn, record["project_name"], path_hint=record["path_hash"])
    session_id = upsert_session(
        conn,
        record["session_id"],
        record["title"],
        project_id,
        None,
        None,
        record["captured_at"],
        model=record.get("model") or "",
        source_id=source_id,
        metadata={"source": "local_codex_rollout", "path_hash": record["path_hash"], "turn_id": record.get("turn_id") or ""},
    )
    snapshot_id = add_snapshot(
        conn,
        session_id=session_id,
        captured_at=record["captured_at"],
        source_id=source_id,
        input_tokens=record.get("input_tokens"),
        cached_input_tokens=record.get("cached_input_tokens"),
        output_tokens=record.get("output_tokens"),
        total_tokens=record.get("total_tokens"),
        credits=record.get("credits"),
        context_limit_tokens=record.get("context_limit_tokens"),
        raw_ref=record["raw_ref"],
    )
    add_delta_and_attribution(
        conn,
        from_snapshot_id=None,
        to_snapshot_id=snapshot_id,
        session_id=session_id,
        token_delta=int(record.get("token_delta") or 0),
        credits_delta=None,
        confidence_level="high" if record.get("session_id") else "low",
        evidence_summary="本地 Codex rollout 结构化 token 用量字段；未读取聊天正文",
        recommendation=recommendation(int(record.get("token_delta") or 0)),
    )


def extract_session_id(path: Path, event: dict[str, Any], payload: dict[str, Any]) -> str:
    for value in [payload.get("session_id"), payload.get("conversation_id"), event.get("session_id")]:
        if isinstance(value, str) and value:
            return f"session_{hash_label(value)}"
    match = UUID_RE.search(path.name)
    if match:
        return f"session_{hash_label(match.group(0))}"
    return f"session_{hash_label(str(path))}"


def token_value(payload: dict[str, Any], *keys: str) -> int | None:
    for key in keys:
        value = coerce_int(payload.get(key))
        if value is not None:
            return value
    return None


def sum_tokens(*values: int | None) -> int | None:
    total = sum(value or 0 for value in values)
    return total if total else None


def first_dict(*values: Any) -> dict[str, Any]:
    for value in values:
        if isinstance(value, dict):
            return value
    return {}


def first_text(*values: Any) -> str:
    for value in values:
        if isinstance(value, str) and value:
            return value
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def timestamp_from_filename(path: Path) -> str:
    prefix = path.name.removeprefix("rollout-")[:19]
    try:
        return datetime.fromisoformat(prefix).replace(tzinfo=timezone.utc).isoformat()
    except ValueError:
        return datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat()


def dry_run_payload(dry_run: LocalHistoryDryRun, *, wrote: bool) -> dict[str, object]:
    return {
        "ok": True,
        "wrote": wrote,
        "source_type": "local_codex_rollout",
        "root_hash": dry_run.root_hash,
        "file_count": dry_run.file_count,
        "token_record_count": dry_run.token_record_count,
        "importable_record_count": dry_run.importable_record_count,
        "skipped_content_lines": dry_run.skipped_content_lines,
        "files": dry_run.files[:20],
        "privacy_boundary": "只读取 token 用量白名单字段；不读取浏览器 cookie、token、钥匙串、系统凭据、聊天正文、prompt 或 assistant 输出。",
    }


def collect_redacted_rollout_samples(
    root: Path | None,
    out: Path,
    *,
    limit_files: int | None = None,
    max_records: int = 80,
) -> dict[str, object]:
    safe_root = root or default_codex_root()
    files = discover_rollout_files(safe_root)
    if limit_files:
        files = files[-limit_files:]
    out.parent.mkdir(parents=True, exist_ok=True)
    written = 0
    source_files = 0
    with out.open("w", encoding="utf-8") as output:
        for path in files:
            file_written = 0
            with path.open("r", encoding="utf-8", errors="replace") as handle:
                for line_number, line in enumerate(handle, 1):
                    if written >= max_records:
                        break
                    if not any(marker in line for marker in TOKEN_MARKERS):
                        continue
                    if any(marker in line for marker in SKIP_MARKERS):
                        continue
                    try:
                        event = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    record = extract_usage_record(event, path, line_number)
                    if not record:
                        continue
                    redacted = {
                        "captured_at": record["captured_at"],
                        "session_id": record["session_id"],
                        "title": record["title"],
                        "project_name": record["project_name"],
                        "path_hash": record["path_hash"],
                        "model": record.get("model") or "",
                        "turn_id_hash": hash_label(record.get("turn_id") or ""),
                        "input_tokens": record.get("input_tokens"),
                        "cached_input_tokens": record.get("cached_input_tokens"),
                        "output_tokens": record.get("output_tokens"),
                        "total_tokens": record.get("total_tokens"),
                        "token_delta": record.get("token_delta"),
                        "credits_present": record.get("credits") is not None,
                        "context_limit_tokens": record.get("context_limit_tokens"),
                        "source_file_hash": hash_label(str(path)),
                    }
                    output.write(json.dumps(redacted, ensure_ascii=False, sort_keys=True) + "\n")
                    written += 1
                    file_written += 1
                if file_written:
                    source_files += 1
            if written >= max_records:
                break
    return {
        "ok": True,
        "out": str(out),
        "root_hash": hash_label(str(safe_root.expanduser())),
        "source_files": source_files,
        "records": written,
        "privacy_boundary": "样本只包含 token 用量白名单字段和哈希；不包含完整路径、聊天正文、prompt、assistant 输出、cookie、token 或系统凭据。",
    }
