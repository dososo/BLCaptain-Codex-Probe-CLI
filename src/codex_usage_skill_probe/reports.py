"""Markdown and JSON report rendering."""

from __future__ import annotations

import json
from pathlib import Path

from .models import RiskFinding, TaskUsageRecord
from .usage_analyzer import build_decision_card


def render_usage_markdown(record: TaskUsageRecord, findings: list[RiskFinding]) -> str:
    decision = build_decision_card(record, findings)
    lines = [
        "# Codex 任务级用量自查报告",
        "",
        "定位：Watch / 验证型探针。本报告只解释用户显式提供的本地数据，不替代官方 usage dashboard 或 `/status`。",
        "",
        "## 决策卡片",
        "",
        "| 问题 | 结论 |",
        "|---|---|",
        f"| 建议动作 | **{decision['action']}** |",
        f"| 为什么贵 | {escape(decision['why_expensive'])} |",
        f"| 怎么降配 | {escape(decision['downgrade'])} |",
        f"| 什么时候该停 | {escape(decision['stop_when'])} |",
        "",
        "## 任务摘要",
        "",
        "| 字段 | 值 |",
        "|---|---|",
        f"| task_id | `{record.task_id}` |",
        f"| model | {record.model or '未知'} |",
        f"| mode | {record.mode or '未知'} |",
        f"| input_tokens | {value(record.input_tokens)} |",
        f"| output_tokens | {value(record.output_tokens)} |",
        f"| cached_input_tokens | {value(record.cached_input_tokens)} |",
        f"| total_tokens | {value(record.total_tokens)} |",
        f"| credits | {value(record.credits)} |",
        f"| context_remaining_percent | {value(record.context_remaining_percent)} |",
        f"| context_used_tokens | {value(record.context_used_tokens)} |",
        f"| context_limit_tokens | {value(record.context_limit_tokens)} |",
        f"| five_hour_remaining_percent | {value(record.five_hour_remaining_percent)} |",
        f"| five_hour_reset | {value(record.five_hour_reset)} |",
        f"| seven_day_remaining_percent | {value(record.seven_day_remaining_percent)} |",
        f"| seven_day_reset | {value(record.seven_day_reset)} |",
        f"| quota_remaining | {value(record.quota_remaining)} |",
        f"| quota_limit | {value(record.quota_limit)} |",
        "",
        "## 风险与建议",
        "",
        "| 标签 | 严重度 | 置信度 | 证据 | 建议 | 证据来源 |",
        "|---|---|---:|---|---|---|",
    ]
    for finding in findings:
        lines.append(
            f"| `{finding.finding_type}` | {finding.severity} | {finding.confidence:.2f} | {escape(finding.evidence)} | {escape(finding.suggestion)} | {finding.evidence_ids} |"
        )

    lines.extend(
        [
            "",
            "## 停止线",
            "",
            "- 如果报告只出现 `LOW_CONFIDENCE_USAGE`，不要据此做强决策，先补充更完整的 `/status` 或手工数据。",
            "- 如果出现 `OVER_BUDGET`、`CREDITS_OVER_BUDGET` 或 `STOP_RECOMMENDED`，先停止扩展任务，保存成果，再决定是否拆分、降配或继续。",
            "- 本工具不承诺省钱、额度翻倍、绕过限制或替代官方用量系统。",
        ]
    )
    return "\n".join(lines) + "\n"


def render_skill_markdown(findings: list[RiskFinding]) -> str:
    lines = [
        "# Codex Skill / 输出体检报告",
        "",
        "定位：本地只读体检。报告只给人工复核建议，不自动安装插件、不自动伪装真人、不保证平台过审。",
        "",
        "| 标签 | 严重度 | 置信度 | 证据片段 | 建议 | 证据来源 |",
        "|---|---|---:|---|---|---|",
    ]
    for finding in findings:
        lines.append(
            f"| `{finding.finding_type}` | {finding.severity} | {finding.confidence:.2f} | {escape(finding.evidence)} | {escape(finding.suggestion)} | {finding.evidence_ids} |"
        )
    lines.extend(
        [
            "",
            "## 人工复核清单",
            "",
            "- 高严重度条目必须人工确认后再发布或交付。",
            "- 所有命中的敏感信息都应从源文件中移除，而不仅是依赖报告脱敏。",
            "- 涉及绕登录、拼车、规避计费、代理官方请求的能力不进入 P0。",
        ]
    )
    return "\n".join(lines) + "\n"


def render_doctor_markdown(
    record: TaskUsageRecord | None,
    usage_findings: list[RiskFinding],
    skill_findings: list[RiskFinding],
    usage_report_path: Path | None,
    skill_report_path: Path | None,
) -> str:
    decision = build_decision_card(record, usage_findings) if record else None
    lines = [
        "# BLCaptain Codex Probe Doctor 报告",
        "",
        "定位：本地一键体检。本报告只处理用户显式提供的文件，不登录、不读取浏览器 cookie、不上传。",
        "",
        "## 总览",
        "",
        "| 项目 | 结果 |",
        "|---|---|",
        f"| 用量报告 | {link_or_missing(usage_report_path)} |",
        f"| Skill / 输出体检 | {link_or_missing(skill_report_path)} |",
        f"| 用量风险数 | {len(usage_findings)} |",
        f"| Skill 风险数 | {len(skill_findings)} |",
    ]
    if decision:
        lines.extend(
            [
                f"| 建议动作 | **{decision['action']}** |",
                f"| 为什么贵 | {escape(decision['why_expensive'])} |",
                f"| 怎么降配 | {escape(decision['downgrade'])} |",
                f"| 什么时候该停 | {escape(decision['stop_when'])} |",
            ]
        )

    lines.extend(
        [
            "",
            "## 隐私边界",
            "",
            "- 只读取命令行显式传入的 `--status`、`--manual-json` 或 `--skill` 文件。",
            "- 不读取浏览器、登录态、cookie、token、钥匙串、系统凭据或私密目录。",
            "- 报告写入本地 `--out-dir`，不会上传云端。",
            "- 命中的敏感信息会以 `[REDACTED:...]` 形式进入证据片段。",
            "",
            "## 下一步",
            "",
            "- 若建议动作是 **停止**，先保存成果并开新会话，不要继续扩大上下文。",
            "- 若建议动作是 **降配**，拆小任务、降低推理强度，并只带必要文件。",
            "- 若建议动作是 **继续**，仍建议保留停止线，避免长会话无意识膨胀。",
        ]
    )
    return "\n".join(lines) + "\n"


def findings_to_json(findings: list[RiskFinding]) -> list[dict[str, object]]:
    return [
        {
            "id": f.id,
            "finding_type": f.finding_type,
            "severity": f.severity,
            "confidence": f.confidence,
            "evidence": f.evidence,
            "suggestion": f.suggestion,
            "evidence_ids": f.evidence_ids,
        }
        for f in findings
    ]


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def value(item: object) -> str:
    return "未知" if item is None or item == "" else str(item)


def link_or_missing(path: Path | None) -> str:
    return f"[{path.name}]({path.name})" if path else "未生成"


def escape(text: str) -> str:
    return str(text).replace("|", "\\|").replace("\n", " ")
