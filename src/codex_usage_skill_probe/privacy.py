"""Local redaction helpers.

The probe never needs secrets. Reports store redacted evidence snippets only.
"""

from __future__ import annotations

import re


REDACTION_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("OPENAI_KEY", re.compile(r"\bsk-[A-Za-z0-9_\-]{16,}\b")),
    ("API_KEY", re.compile(r"(?i)\b(api[_-]?key|secret|access[_-]?token|token)\s*[:=]\s*['\"]?[^'\"\s,;]{8,}")),
    ("COOKIE", re.compile(r"(?i)\b(cookie|set-cookie)\s*[:=]\s*[^;\n]{8,}")),
    ("BEARER_TOKEN", re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._\-]{12,}")),
    ("EMAIL", re.compile(r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b")),
    ("PHONE", re.compile(r"(?<!\d)(?:\+?86[- ]?)?1[3-9]\d{9}(?!\d)")),
]


def redact(text: str) -> str:
    result = text
    for label, pattern in REDACTION_PATTERNS:
        result = pattern.sub(f"[REDACTED:{label}]", result)
    return result


def snippet(text: str, limit: int = 180) -> str:
    compact = " ".join(redact(text).split())
    if len(compact) <= limit:
        return compact
    cut = limit - 3
    marker_start = compact.rfind("[REDACTED:", 0, cut)
    if marker_start != -1:
        marker_end = compact.find("]", marker_start)
        if marker_end >= cut:
            cut = marker_end + 1
    return compact[:cut] + "..."
