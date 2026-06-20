"""Markdown and JSON report rendering."""

from __future__ import annotations

import json
from pathlib import Path

from .models import RiskFinding, TaskUsageRecord


def render_usage_markdown(record: TaskUsageRecord, findings: list[RiskFinding]) -> str:
    lines = [
        "# Codex 任务级用量自查报告",
        "",
        "定位：Watch / 验证型探针。本报告只解释用户显式提供的本地数据，不替代官方 usage dashboard 或 `/status`。",
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


def escape(text: str) -> str:
    return str(text).replace("|", "\\|").replace("\n", " ")

