"""Task-level usage analysis."""

from __future__ import annotations

from .models import RiskFinding, TaskUsageRecord, new_id, now_iso


def analyze_usage(
    record: TaskUsageRecord,
    budget_tokens: int | None = None,
    budget_credits: float | None = None,
) -> list[RiskFinding]:
    findings: list[RiskFinding] = []

    if record.total_tokens is None and record.credits is None:
        findings.append(
            finding(
                record,
                "LOW_CONFIDENCE_USAGE",
                "high",
                0.95,
                "没有发现 token 或 credits 字段",
                "请粘贴 Codex `/status` 输出，或使用手工 JSON 提供 input_tokens/output_tokens/credits。",
                "R-001,R-002",
            )
        )
        return findings

    if budget_tokens is not None and record.total_tokens is not None:
        ratio = record.total_tokens / budget_tokens if budget_tokens > 0 else 0
        if ratio >= 1:
            findings.append(
                finding(
                    record,
                    "OVER_BUDGET",
                    "high",
                    0.94,
                    f"total_tokens={record.total_tokens} 超过 budget_tokens={budget_tokens}",
                    "停止继续扩大上下文；拆分任务；优先复用缓存输入；下一轮改用更小模型或降低推理强度。",
                    "E-011,E-012,E-013",
                )
            )
        elif ratio >= 0.8:
            findings.append(
                finding(
                    record,
                    "BUDGET_NEAR_LIMIT",
                    "medium",
                    0.86,
                    f"total_tokens={record.total_tokens} 已达到预算的 {ratio:.0%}",
                    "继续前先收敛目标；把探索和修改拆成两次任务；保留停止线。",
                    "E-013",
                )
            )

    if budget_credits is not None and record.credits is not None and record.credits > budget_credits:
        findings.append(
            finding(
                record,
                "CREDITS_OVER_BUDGET",
                "high",
                0.9,
                f"credits={record.credits} 超过 budget_credits={budget_credits}",
                "停止本轮；复盘是否使用了高成本模型、Fast mode 或过长上下文。",
                "E-011,E-012,R-002",
            )
        )

    mode_text = (record.mode or "").lower()
    if "fast" in mode_text or "xhigh" in mode_text or "high" in mode_text:
        findings.append(
            finding(
                record,
                "FAST_MODE_RISK",
                "medium",
                0.78,
                f"mode={record.mode}",
                "除非任务确实需要速度或高推理，否则优先用普通模式或更小模型做初筛。",
                "E-013,R-002",
            )
        )

    if record.quota_remaining is not None and record.quota_limit:
        remaining_ratio = record.quota_remaining / record.quota_limit
        if remaining_ratio < 0.15:
            findings.append(
                finding(
                    record,
                    "STOP_RECOMMENDED",
                    "high",
                    0.9,
                    f"quota_remaining={record.quota_remaining}，低于 quota_limit={record.quota_limit} 的 15%",
                    "建议停止非必要任务；只保留验证和保存成果动作。",
                    "E-011,E-012",
                )
            )

    if not findings:
        findings.append(
            finding(
                record,
                "USAGE_BASELINE",
                "info",
                0.76,
                usage_summary(record),
                "当前没有触发强风险；仍建议记录任务目标、模型和输出质量，避免只看总量。",
                "R-001,R-002",
            )
        )

    return findings


def finding(
    record: TaskUsageRecord,
    finding_type: str,
    severity: str,
    confidence: float,
    evidence: str,
    suggestion: str,
    evidence_ids: str,
) -> RiskFinding:
    return RiskFinding(
        id=new_id("finding"),
        import_id=record.import_id,
        conversation_id=record.task_id,
        finding_type=finding_type,
        severity=severity,
        confidence=confidence,
        evidence=evidence,
        suggestion=suggestion,
        evidence_ids=evidence_ids,
        created_at=now_iso(),
    )


def usage_summary(record: TaskUsageRecord) -> str:
    parts = []
    if record.total_tokens is not None:
        parts.append(f"total_tokens={record.total_tokens}")
    if record.credits is not None:
        parts.append(f"credits={record.credits}")
    if record.model:
        parts.append(f"model={record.model}")
    return ", ".join(parts) or "usage fields unavailable"

