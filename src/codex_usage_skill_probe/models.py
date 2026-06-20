"""Domain records for the probe."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:12]}"


@dataclass
class ImportBatch:
    id: str
    source_type: str
    created_at: str
    metadata: dict[str, Any] = field(default_factory=dict)
    raw_hash: str = ""
    parsed_count: int = 0


@dataclass
class TaskUsageRecord:
    task_id: str
    import_id: str
    created_at: str
    user_goal: str = ""
    model: str = ""
    mode: str = ""
    input_tokens: int | None = None
    output_tokens: int | None = None
    cached_input_tokens: int | None = None
    total_tokens: int | None = None
    credits: float | None = None
    quota_remaining: float | None = None
    quota_limit: float | None = None
    source: str = "manual"
    status: str = "ok"


@dataclass
class RiskFinding:
    id: str
    import_id: str
    conversation_id: str | None
    finding_type: str
    severity: str
    confidence: float
    evidence: str
    suggestion: str
    evidence_ids: str
    created_at: str

