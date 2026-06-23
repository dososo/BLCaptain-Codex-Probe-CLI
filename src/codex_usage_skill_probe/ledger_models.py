"""Ledger domain helpers for session-level Codex usage attribution."""

from __future__ import annotations

from dataclasses import dataclass


CONFIDENCE_ORDER = {
    "low": 1,
    "medium": 2,
    "high": 3,
    "exact": 4,
}


@dataclass(frozen=True)
class LedgerRange:
    label: str
    start: str | None
    end: str | None


@dataclass(frozen=True)
class SourceDoctorResult:
    source_type: str
    available: bool
    confidence_ceiling: str
    permission_scope: str
    privacy_note: str
    next_step: str


@dataclass(frozen=True)
class SessionSummary:
    session_id: str
    title: str
    project: str
    started_at: str
    ended_at: str
    token_delta: int
    credits_delta: float | None
    context_peak_percent: float | None
    confidence_level: str
    confidence_score: float
    source_type: str
    recommendation: str
    evidence_summary: str


@dataclass(frozen=True)
class SnapshotSummary:
    snapshot_id: str
    captured_at: str
    total_tokens: int | None
    credits: float | None
    context_used_tokens: int | None
    context_limit_tokens: int | None
    context_remaining_percent: float | None
    source_type: str


def confidence_score(level: str) -> float:
    return {
        "exact": 0.99,
        "high": 0.88,
        "medium": 0.68,
        "low": 0.42,
    }.get(level, 0.3)


def min_confidence_level(levels: list[str]) -> str:
    if not levels:
        return "low"
    return min(levels, key=lambda item: CONFIDENCE_ORDER.get(item, 0))
