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


def parse_context_status(text: str) -> tuple[float | None, int | None, int | None]:
    patterns = [
        r"剩余\s*([\d,_.]+)\s*%\s*[（(]\s*已使用\s*([\d,_.]+[KkMm]?)\s*/\s*共\s*([\d,_.]+[KkMm]?)\s*[）)]",
        r"\bcontext(?:\s+remaining)?\s*[:=]\s*([\d,_.]+)\s*%\s*[（(]\s*used\s*([\d,_.]+[KkMm]?)\s*/\s*(?:limit\s*)?([\d,_.]+[KkMm]?)\s*[）)]",
        r"\bcontext\s*[:=]\s*([\d,_.]+)\s*%\s*remaining\s*[（(]\s*([\d,_.]+[KkMm]?)\s*used\s*/\s*([\d,_.]+[KkMm]?)\s*limit\s*[）)]",
    ]
    match = None
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.I)
        if match:
            break
    if not match:
        return None, None, None
    return (
        float(match.group(1).replace(",", "").replace("_", "")),
        parse_human_int(match.group(2)),
        parse_human_int(match.group(3)),
    )


def parse_labeled_percent(text: str, label_pattern: str) -> float | None:
    match = re.search(label_pattern + r"[\s\S]{0,160}?剩余\s*([\d,_.]+)\s*%", text, flags=re.I)
    if not match:
        match = re.search(label_pattern + r"[\s\S]{0,160}?\bremaining\s*[:=]?\s*([\d,_.]+)\s*%", text, flags=re.I)
    if not match:
        match = re.search(label_pattern + r"[\s\S]{0,160}?([\d,_.]+)\s*%\s*remaining\b", text, flags=re.I)
    return float(match.group(1).replace(",", "").replace("_", "")) if match else None


def parse_labeled_reset(text: str, label_pattern: str) -> str:
    match = re.search(
        label_pattern + r"[\s\S]{0,180}?(?:重置时间|reset(?:s)?(?:\s*time|\s*at)?|resets\s+at)\s*[：:=]\s*([^\n）)]+)",
        text,
        flags=re.I,
    )
    return match.group(1).strip() if match else ""


def parse_status_text(text: str, goal: str = "", model_hint: str = "") -> tuple[ImportBatch, TaskUsageRecord]:
    stripped = text.strip()
    if stripped.startswith("{"):
        return parse_manual_json(stripped, source_type="status_text", goal=goal, model_hint=model_hint)

    context_remaining, context_used, context_limit = parse_context_status(stripped)
    five_hour_label = r"(?:5\s*(?:小时|h|hour)|5-hour)[^\n]*"
    seven_day_label = r"(?:7\s*(?:天|d|day)|7-day)[^\n]*"
    five_hour_remaining = parse_labeled_percent(stripped, five_hour_label)
    seven_day_remaining = parse_labeled_percent(stripped, seven_day_label)

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
        total_tokens = context_used
    if total_tokens is None:
        known = [v for v in [input_tokens, output_tokens] if v is not None]
        total_tokens = sum(known) if known else None

    credits = parse_float(stripped, r"\bcredits?\s*[:=]\s*([\d,_.]+)")
    quota_remaining = parse_float(
        stripped,
        r"\b(?:remaining|quota_remaining)\s*[:=]\s*([\d,_.]+)",
    )
    if quota_remaining is None:
        quota_remaining = context_remaining
    quota_limit = parse_float(stripped, r"\b(?:limit|quota_limit)\s*[:=]\s*([\d,_.]+)")
    if quota_remaining is not None and quota_limit is None and (context_remaining is not None or "%" in stripped):
        quota_limit = 100.0

    batch = ImportBatch(
        id=new_id("import"),
        source_type="status_text",
        created_at=now_iso(),
        metadata={"parser": "status_text", "limits_detected": bool(five_hour_remaining or seven_day_remaining)},
        raw_hash=raw_hash(stripped),
        parsed_count=1 if any([input_tokens, output_tokens, total_tokens, credits, context_remaining, five_hour_remaining, seven_day_remaining]) else 0,
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
        context_remaining_percent=context_remaining,
        context_used_tokens=context_used,
        context_limit_tokens=context_limit,
        five_hour_remaining_percent=five_hour_remaining,
        five_hour_reset=parse_labeled_reset(stripped, five_hour_label),
        seven_day_remaining_percent=seven_day_remaining,
        seven_day_reset=parse_labeled_reset(stripped, seven_day_label),
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
        metadata={"parser": "manual_json", "file_schema": "v0.3"},
        raw_hash=raw_hash(text),
        parsed_count=1
        if any(
            [
                input_tokens,
                output_tokens,
                total_tokens,
                data.get("credits"),
                data.get("context_remaining_percent"),
                data.get("five_hour_remaining_percent"),
                data.get("seven_day_remaining_percent"),
            ]
        )
        else 0,
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
        context_remaining_percent=coerce_float(data.get("context_remaining_percent")),
        context_used_tokens=coerce_int(data.get("context_used_tokens")),
        context_limit_tokens=coerce_int(data.get("context_limit_tokens")),
        five_hour_remaining_percent=coerce_float(data.get("five_hour_remaining_percent")),
        five_hour_reset=str(data.get("five_hour_reset") or ""),
        seven_day_remaining_percent=coerce_float(data.get("seven_day_remaining_percent")),
        seven_day_reset=str(data.get("seven_day_reset") or ""),
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
    compact = value.replace(",", "").replace("_", "").replace(" ", "").strip()
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
