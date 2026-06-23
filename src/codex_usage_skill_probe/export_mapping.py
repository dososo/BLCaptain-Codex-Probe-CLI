"""Official export inspection and field mapping helpers."""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


CANONICAL_FIELDS = [
    "session_id",
    "title",
    "project",
    "started_at",
    "ended_at",
    "model",
    "input_tokens",
    "cached_input_tokens",
    "output_tokens",
    "total_tokens",
    "credits",
    "context_remaining_percent",
    "context_used_tokens",
    "context_limit_tokens",
]

FIELD_ALIASES = {
    "session_id": ["session_id", "id", "conversation_id", "thread_id", "chat_id", "session"],
    "title": ["title", "session_title", "chat_title", "name"],
    "project": ["project", "project_name", "workspace", "repo", "repository"],
    "started_at": ["started_at", "start_time", "created_at", "created", "first_seen_at"],
    "ended_at": ["ended_at", "end_time", "last_seen_at", "updated_at", "finished_at"],
    "model": ["model", "model_name"],
    "input_tokens": ["input_tokens", "prompt_tokens", "request_tokens", "input"],
    "cached_input_tokens": ["cached_input_tokens", "cached_tokens", "cache_read_tokens"],
    "output_tokens": ["output_tokens", "completion_tokens", "response_tokens", "output"],
    "total_tokens": ["total_tokens", "tokens", "token_count", "total"],
    "credits": ["credits", "credit_delta", "cost", "cost_credits"],
    "context_remaining_percent": ["context_remaining_percent", "context_remaining", "remaining_context_percent"],
    "context_used_tokens": ["context_used_tokens", "context_used", "context_tokens"],
    "context_limit_tokens": ["context_limit_tokens", "context_limit", "context_window"],
}


@dataclass(frozen=True)
class ExportInspection:
    path: str
    format: str
    row_count: int
    fields: list[str]
    mapping: dict[str, str]
    missing_recommended: list[str]


def read_export_rows(path: Path) -> tuple[str, list[dict[str, Any]]]:
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    suffix = path.suffix.lower()
    if suffix == ".csv":
        with path.open("r", encoding="utf-8", newline="") as handle:
            return "csv", list(csv.DictReader(handle))
    if suffix == ".jsonl":
        rows = []
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                text = line.strip()
                if text:
                    rows.append(json.loads(text))
        return "jsonl", rows
    if suffix == ".json":
        payload = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(payload, list):
            return "json", payload
        if isinstance(payload, dict):
            if isinstance(payload.get("sessions"), list):
                return "json", list(payload["sessions"])
            if isinstance(payload.get("snapshots"), list):
                return "json", list(payload["snapshots"])
            return "json", [payload]
    raise ValueError(f"Unsupported export file: {path}")


def inspect_export(path: Path, mapping_path: Path | None = None) -> ExportInspection:
    file_format, rows = read_export_rows(path)
    fields = sorted({key for row in rows if isinstance(row, dict) for key in row.keys()})
    mapping = load_mapping(mapping_path) if mapping_path else build_mapping(fields)
    missing = [field for field in ["session_id", "total_tokens"] if not mapping.get(field)]
    return ExportInspection(
        path=path.name,
        format=file_format,
        row_count=len(rows),
        fields=fields,
        mapping={key: value for key, value in mapping.items() if value},
        missing_recommended=missing,
    )


def build_mapping(fields: list[str]) -> dict[str, str]:
    lowered = {field.lower(): field for field in fields}
    mapping: dict[str, str] = {}
    for canonical, aliases in FIELD_ALIASES.items():
        matched = ""
        for alias in aliases:
            if alias.lower() in lowered:
                matched = lowered[alias.lower()]
                break
        mapping[canonical] = matched
    return mapping


def load_mapping(path: Path | None) -> dict[str, str]:
    if not path:
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("mapping JSON must be an object")
    if "fields" in payload and isinstance(payload["fields"], dict):
        payload = payload["fields"]
    return {key: str(value) for key, value in payload.items() if key in CANONICAL_FIELDS and value}


def write_mapping_template(path: Path, inspection: ExportInspection) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "source_file": inspection.path,
        "format": inspection.format,
        "row_count": inspection.row_count,
        "fields": inspection.mapping,
        "notes": "Edit fields when your export uses custom column names. Values are source field names.",
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def normalize_rows(rows: list[dict[str, Any]], mapping: dict[str, str] | None = None) -> list[dict[str, Any]]:
    fields = sorted({key for row in rows if isinstance(row, dict) for key in row.keys()})
    active_mapping = mapping or build_mapping(fields)
    normalized = []
    for index, row in enumerate(rows, 1):
        item: dict[str, Any] = {"_row_number": index}
        for canonical in CANONICAL_FIELDS:
            source_key = active_mapping.get(canonical)
            if source_key:
                item[canonical] = row.get(source_key)
            else:
                item[canonical] = row.get(canonical)
        normalized.append(item)
    return normalized


def inspection_payload(inspection: ExportInspection) -> dict[str, object]:
    return {
        "ok": True,
        "path": inspection.path,
        "format": inspection.format,
        "row_count": inspection.row_count,
        "fields": inspection.fields,
        "mapping": inspection.mapping,
        "missing_recommended": inspection.missing_recommended,
        "privacy_boundary": "只检查字段名和行数，不读取浏览器 cookie、token、钥匙串、系统凭据或聊天正文。",
    }
