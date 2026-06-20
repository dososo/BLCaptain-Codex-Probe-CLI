"""Offline Skill/output inspection rules."""

from __future__ import annotations

import re
from pathlib import Path

from .models import ImportBatch, RiskFinding, new_id, now_iso
from .privacy import redact, snippet
from .usage_parser import raw_hash


AI_SMELL_PATTERNS = [
    r"(?i)\bas an ai\b",
    r"作为(?:一个)?AI",
    r"当然可以",
    r"以下是",
    r"一站式",
    r"赋能",
    r"闭环",
    r"降维打击",
    r"神器",
    r"保姆级",
    r"开挂",
    r"只需(?:一|1)",
    r"效率(?:直接)?拉满",
]

PLUGIN_RISK_PATTERNS = [
    r"绕过登录",
    r"跳过手机号",
    r"拼车",
    r"共享账号",
    r"规避计费",
    r"无限额度",
    r"免费额度",
    r"代理(?:官方)?请求",
    r"拦截(?:Codex)?请求",
    r"自动安装",
    r"自动启用",
]

SECRET_HINT_PATTERNS = [
    r"\[REDACTED:OPENAI_KEY\]",
    r"\[REDACTED:API_KEY\]",
    r"\[REDACTED:COOKIE\]",
    r"\[REDACTED:BEARER_TOKEN\]",
]


def lint_file(path: Path) -> tuple[ImportBatch, list[RiskFinding]]:
    text = path.read_text(encoding="utf-8")
    return lint_text(text, metadata={"path_name": path.name})


def lint_text(text: str, metadata: dict[str, str] | None = None) -> tuple[ImportBatch, list[RiskFinding]]:
    metadata = metadata or {}
    redacted = redact(text)
    batch = ImportBatch(
        id=new_id("import"),
        source_type="text_file",
        created_at=now_iso(),
        metadata={"parser": "skill_linter", **metadata},
        raw_hash=raw_hash(redacted),
        parsed_count=1 if redacted.strip() else 0,
    )
    findings: list[RiskFinding] = []

    if not redacted.strip():
        findings.append(make_finding(batch, "EMPTY_CONTENT", "high", 0.99, "", "请提供 Skill、提示词或输出文本。", "E-007,E-008"))
        return batch, findings

    for pattern in AI_SMELL_PATTERNS:
        match = re.search(pattern, redacted)
        if match:
            findings.append(
                make_finding(
                    batch,
                    "AI_SMELL",
                    "medium",
                    0.74,
                    snippet(context(redacted, match.start(), match.end())),
                    "人工复核这段表达是否模板化；优先改成具体事实、对象、动作和验收结果。",
                    "E-008",
                )
            )
            break

    for pattern in PLUGIN_RISK_PATTERNS:
        match = re.search(pattern, redacted)
        if match:
            findings.append(
                make_finding(
                    batch,
                    "PLUGIN_RISK",
                    "high",
                    0.9,
                    snippet(context(redacted, match.start(), match.end())),
                    "不要自动安装、启用或推荐可能绕登录、拼车、规避计费的能力；改为人工确认和合规替代路径。",
                    "E-007,R-005",
                )
            )
            break

    if any(re.search(pattern, redacted) for pattern in SECRET_HINT_PATTERNS):
        findings.append(
            make_finding(
                batch,
                "SECRET_RISK",
                "high",
                0.95,
                "输入中包含已脱敏的敏感信息",
                "报告不会输出原始秘密；建议从源文件移除密钥、cookie 或 token。",
                "R-005",
            )
        )

    if not re.search(r"验收|测试|验证|DoD|完成条件|Stop when|Acceptance", redacted, flags=re.I):
        findings.append(
            make_finding(
                batch,
                "MISSING_ACCEPTANCE",
                "medium",
                0.82,
                snippet(redacted),
                "补充可执行验收标准，避免 Skill 只描述能力、不证明结果。",
                "E-007,E-008",
            )
        )

    if not re.search(r"隐私|脱敏|删除|安全|secret|privacy|delete", redacted, flags=re.I):
        findings.append(
            make_finding(
                batch,
                "MISSING_PRIVACY_BOUNDARY",
                "medium",
                0.78,
                snippet(redacted),
                "补充隐私、安全和删除边界，尤其是本地文件、密钥和用户数据处理规则。",
                "R-005",
            )
        )

    if not findings:
        findings.append(
            make_finding(
                batch,
                "SKILL_BASELINE",
                "info",
                0.72,
                snippet(redacted),
                "未发现 P0 规则命中的强风险；建议仍由人工复核上下文和最终用途。",
                "E-007,E-008",
            )
        )

    return batch, findings


def make_finding(
    batch: ImportBatch,
    finding_type: str,
    severity: str,
    confidence: float,
    evidence: str,
    suggestion: str,
    evidence_ids: str,
) -> RiskFinding:
    return RiskFinding(
        id=new_id("finding"),
        import_id=batch.id,
        conversation_id=None,
        finding_type=finding_type,
        severity=severity,
        confidence=confidence,
        evidence=evidence,
        suggestion=suggestion,
        evidence_ids=evidence_ids,
        created_at=now_iso(),
    )


def context(text: str, start: int, end: int, radius: int = 90) -> str:
    return text[max(0, start - radius) : min(len(text), end + radius)]

