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
                "停止当前任务；复盘是否使用了高成本模型、Fast mode 或过长上下文。",
                "E-011,E-012,R-002",
            )
        )

    if record.context_remaining_percent is not None:
        if record.context_remaining_percent < 15:
            findings.append(
                finding(
                    record,
                    "CONTEXT_STOP_LINE",
                    "high",
                    0.91,
                    f"context_remaining_percent={record.context_remaining_percent}",
                    "当前会话上下文余量很低；停止继续塞入文件和长日志，先保存结论或开新会话。",
                    "E-011,E-012,E-013",
                )
            )
        elif record.context_remaining_percent < 35:
            findings.append(
                finding(
                    record,
                    "CONTEXT_NEAR_LIMIT",
                    "medium",
                    0.84,
                    f"context_remaining_percent={record.context_remaining_percent}",
                    "继续前先删减输入；只带最终 README、目标仓库路径、最新 commit 和必要错误日志。",
                    "E-013",
                )
            )

    if record.five_hour_remaining_percent is not None and record.five_hour_remaining_percent < 20:
        findings.append(
            finding(
                record,
                "FIVE_HOUR_LIMIT_LOW",
                "medium",
                0.82,
                f"five_hour_remaining_percent={record.five_hour_remaining_percent}",
                "短窗口额度偏低；只做收尾验证，避免继续启动大范围探索。",
                "E-011,E-012",
            )
        )

    if record.seven_day_remaining_percent is not None and record.seven_day_remaining_percent < 20:
        findings.append(
            finding(
                record,
                "SEVEN_DAY_LIMIT_LOW",
                "high",
                0.88,
                f"seven_day_remaining_percent={record.seven_day_remaining_percent}",
                "7 天额度偏低；停止非必要任务，把后续工作拆到额度恢复后执行。",
                "E-011,E-012",
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
    if record.context_remaining_percent is not None:
        parts.append(f"context_remaining={record.context_remaining_percent}%")
    if record.five_hour_remaining_percent is not None:
        parts.append(f"5h_remaining={record.five_hour_remaining_percent}%")
    if record.seven_day_remaining_percent is not None:
        parts.append(f"7d_remaining={record.seven_day_remaining_percent}%")
    if record.credits is not None:
        parts.append(f"credits={record.credits}")
    if record.model:
        parts.append(f"model={record.model}")
    return ", ".join(parts) or "usage fields unavailable"


def build_decision_card(record: TaskUsageRecord, findings: list[RiskFinding]) -> dict[str, str]:
    labels = {item.finding_type for item in findings}
    if "LOW_CONFIDENCE_USAGE" in labels:
        action = "补充数据"
    elif labels & {"OVER_BUDGET", "CREDITS_OVER_BUDGET", "STOP_RECOMMENDED", "CONTEXT_STOP_LINE", "SEVEN_DAY_LIMIT_LOW"}:
        action = "停止"
    elif labels & {"BUDGET_NEAR_LIMIT", "CONTEXT_NEAR_LIMIT", "FIVE_HOUR_LIMIT_LOW", "FAST_MODE_RISK"}:
        action = "降配"
    else:
        action = "继续"

    return {
        "action": action,
        "why_expensive": explain_cost(record, labels),
        "downgrade": downgrade_advice(record, labels),
        "stop_when": stop_advice(record, labels),
    }


def explain_cost(record: TaskUsageRecord, labels: set[str]) -> str:
    reasons: list[str] = []
    if record.total_tokens is not None and record.total_tokens >= 100000:
        reasons.append(f"当前任务已累计 {record.total_tokens:,} tokens，上下文规模已经偏大")
    if record.context_remaining_percent is not None and record.context_remaining_percent < 50:
        reasons.append(f"会话上下文只剩 {record.context_remaining_percent:g}%")
    if "FAST_MODE_RISK" in labels:
        reasons.append("当前模式偏重，可能不适合继续做低风险文案或收尾任务")
    if record.output_tokens is not None and record.output_tokens >= 20000:
        reasons.append(f"输出 token 达到 {record.output_tokens:,}，报告、README、日志类任务会继续放大成本")
    return "；".join(reasons) if reasons else "未发现强成本风险；主要成本仍取决于后续输入长度、输出长度和模型模式。"


def downgrade_advice(record: TaskUsageRecord, labels: set[str]) -> str:
    advice = ["开新会话时只带最终 README、目标仓库路径、最新 commit 和必要错误日志"]
    if record.context_remaining_percent is not None and record.context_remaining_percent < 50:
        advice.append("不要默认重读全项目，先点名必要文件")
    if "FAST_MODE_RISK" in labels:
        advice.append("把探索、文案润色、README 微调放到普通模式或更小模型")
    if labels & {"BUDGET_NEAR_LIMIT", "OVER_BUDGET"}:
        advice.append("把发布准备、CI 修复、README 微调拆成独立小任务")
    return "；".join(advice) + "。"


def stop_advice(record: TaskUsageRecord, labels: set[str]) -> str:
    if labels & {"OVER_BUDGET", "CREDITS_OVER_BUDGET", "STOP_RECOMMENDED", "CONTEXT_STOP_LINE", "SEVEN_DAY_LIMIT_LOW"}:
        return "现在就停止扩展范围，只保留保存成果、提交、推送和必要验证。"
    if record.context_remaining_percent is not None and record.context_remaining_percent < 35:
        return "如果下一步还要读大量文件、跑 CI 或处理 GitHub 发布，建议先停在这里开新会话。"
    if record.five_hour_remaining_percent is not None and record.five_hour_remaining_percent < 20:
        return "5 小时额度低于 20% 时，停止非必要探索，只做收尾验证。"
    return "当上下文低于 35%、预算超过 80%、或任务开始要求反复读大文件时，就应该停下来拆分。"
