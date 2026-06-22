"""Parse user-provided Codex usage data.

Supported inputs are intentionally user-provided files/text only. The probe does
not authenticate, scrape, proxy, or call Codex services.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

from .models import ImportBatch, TaskUsageRecord, new_id, now_iso


def raw_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def parse_int(text: str, *patterns: str) -> int | None:
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.I)
        if match:
            return parse_human_int(match.group(1))
    return None


def parse_float(text: str, *patterns: str) -> float | None:
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.I)
        if match:
            return float(match.group(1).replace(",", "").replace("_", ""))
    return None


def parse_status_text(text: str, goal: str = "", model_hint: str = "") -> tuple[ImportBatch, TaskUsageRecord]:
    stripped = text.strip()
    if stripped.startswith("{"):
        return parse_manual_json(stripped, source_type="status_text", goal=goal, model_hint=model_hint)

    model = model_hint or parse_text_field(stripped, r"\bmodel\s*[:=]\s*([A-Za-z0-9_.:\-/]+)")
    mode = parse_text_field(stripped, r"\b(?:mode|speed)\s*[:=]\s*([A-Za-z0-9_.:\-/]+)")
    input_tokens = parse_int(
        stripped,
        r"\binput[_\s-]*tokens?\s*[:=]\s*([\d,_]+)",
        r"\bin\s*[:=]\s*([\d,_]+)",
    )
    output_tokens = parse_int(
        stripped,
        r"\boutput[_\s-]*tokens?\s*[:=]\s*([\d,_]+)",
        r"\bout\s*[:=]\s*([\d,_]+)",
    )
    cached_tokens = parse_int(
        stripped,
        r"\bcached[_\s-]*(?:input[_\s-]*)?tokens?\s*[:=]\s*([\d,_]+)",
        r"\bcache\s*[:=]\s*([\d,_]+)",
    )
    total_tokens = parse_int(
        stripped,
        r"\btotal[_\s-]*tokens?\s*[:=]\s*([\d,_]+)",
        r"已使用\s*([\d,_.]+[KkMm]?)\s*/\s*共\s*[\d,_.]+[KkMm]?",
    )
    if total_tokens is None:
        known = [v for v in [input_tokens, output_tokens] if v is not None]
        total_tokens = sum(known) if known else None

    credits = parse_float(stripped, r"\bcredits?\s*[:=]\s*([\d,_.]+)")
    quota_remaining = parse_float(
        stripped,
        r"\b(?:remaining|quota_remaining)\s*[:=]\s*([\d,_.]+)",
        r"剩余\s*([\d,_.]+)\s*%",
    )
    quota_limit = parse_float(stripped, r"\b(?:limit|quota_limit)\s*[:=]\s*([\d,_.]+)")
    if quota_remaining is not None and quota_limit is None and "%" in stripped:
        quota_limit = 100.0

    batch = ImportBatch(
        id=new_id("import"),
        source_type="status_text",
        created_at=now_iso(),
        metadata={"parser": "status_text"},
        raw_hash=raw_hash(stripped),
        parsed_count=1 if any([input_tokens, output_tokens, total_tokens, credits]) else 0,
    )
    record = TaskUsageRecord(
        task_id=new_id("task"),
        import_id=batch.id,
        created_at=now_iso(),
        user_goal=goal,
        model=model,
        mode=mode,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cached_input_tokens=cached_tokens,
        total_tokens=total_tokens,
        credits=credits,
        quota_remaining=quota_remaining,
        quota_limit=quota_limit,
        source="status",
        status="ok" if batch.parsed_count else "failed",
    )
    return batch, record


def parse_manual_json(text: str, source_type: str = "manual_json", goal: str = "", model_hint: str = "") -> tuple[ImportBatch, TaskUsageRecord]:
    data = json.loads(text)
    if "usage" in data and isinstance(data["usage"], dict):
        data = {**data, **data["usage"]}

    input_tokens = coerce_int(data.get("input_tokens"))
    output_tokens = coerce_int(data.get("output_tokens"))
    total_tokens = coerce_int(data.get("total_tokens"))
    if total_tokens is None:
        known = [v for v in [input_tokens, output_tokens] if v is not None]
        total_tokens = sum(known) if known else None

    batch = ImportBatch(
        id=new_id("import"),
        source_type=source_type,
        created_at=now_iso(),
        metadata={"parser": "manual_json", "file_schema": "v0.1"},
        raw_hash=raw_hash(text),
        parsed_count=1 if any([input_tokens, output_tokens, total_tokens, data.get("credits")]) else 0,
    )
    record = TaskUsageRecord(
        task_id=str(data.get("task_id") or new_id("task")),
        import_id=batch.id,
        created_at=now_iso(),
        user_goal=str(data.get("user_goal") or goal or ""),
        model=str(data.get("model") or model_hint or ""),
        mode=str(data.get("mode") or ""),
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cached_input_tokens=coerce_int(data.get("cached_input_tokens")),
        total_tokens=total_tokens,
        credits=coerce_float(data.get("credits")),
        quota_remaining=coerce_float(data.get("quota_remaining")),
        quota_limit=coerce_float(data.get("quota_limit")),
        source=source_type,
        status="ok" if batch.parsed_count else "failed",
    )
    return batch, record


def load_status_file(path: Path, goal: str = "", model_hint: str = "") -> tuple[ImportBatch, TaskUsageRecord]:
    return parse_status_text(path.read_text(encoding="utf-8"), goal=goal, model_hint=model_hint)


def load_manual_json(path: Path, goal: str = "", model_hint: str = "") -> tuple[ImportBatch, TaskUsageRecord]:
    return parse_manual_json(path.read_text(encoding="utf-8"), goal=goal, model_hint=model_hint)


def parse_text_field(text: str, pattern: str) -> str:
    match = re.search(pattern, text, flags=re.I)
    return match.group(1).strip() if match else ""


def parse_human_int(value: str) -> int:
    compact = value.replace(",", "").replace("_", "").strip()
    suffix = compact[-1:].lower()
    if suffix == "k":
        return int(float(compact[:-1]) * 1000)
    if suffix == "m":
        return int(float(compact[:-1]) * 1000000)
    return int(compact)


def coerce_int(value: Any) -> int | None:
    if value is None or value == "":
        return None
    return parse_human_int(str(value))


def coerce_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    return float(str(value).replace(",", "").replace("_", ""))
