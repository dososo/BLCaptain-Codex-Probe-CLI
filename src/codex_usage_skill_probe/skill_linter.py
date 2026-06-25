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

RISK_RULES = [
    (
        "AUTO_INSTALL_RISK",
        "high",
        0.9,
        [r"自动安装", r"自动启用", r"未经(?:用户)?确认.*安装", r"默认安装.*插件"],
        "插件、连接器或外部工具必须由用户明确确认；改成列出用途、权限和替代方案后再请求确认。",
        "E-007,R-005",
    ),
    (
        "LOGIN_BILLING_BYPASS",
        "high",
        0.92,
        [r"绕过登录", r"跳过手机号", r"拼车", r"共享账号", r"规避计费", r"绕过额度", r"无限额度", r"免费额度"],
        "删除绕登录、共享账号、规避计费或绕额度表达；改为官方合规路径和成本治理建议。",
        "R-005",
    ),
    (
        "REQUEST_INTERCEPTION_RISK",
        "high",
        0.9,
        [r"代理(?:官方)?请求", r"拦截(?:Codex)?请求", r"抓包", r"中间人"],
        "不要代理、拦截或修改 Codex / OpenAI 请求；如需分析，只处理用户显式提供或本地白名单数据。",
        "R-005",
    ),
    (
        "DATA_EXFILTRATION_RISK",
        "high",
        0.88,
        [r"外传", r"上传(?:到|至)", r"发送(?:到|至).*(?:服务器|云端|第三方|webhook)", r"同步(?:到|至).*(?:云端|第三方)", r"requests\.post", r"curl\s+https?://"],
        "不要默认外传用户文件、报告或日志；如确需联网，必须说明字段、目的、保留时间并等待用户确认。",
        "R-005",
    ),
    (
        "IMPERSONATION_RISK",
        "medium",
        0.84,
        [r"伪装成真人", r"冒充", r"模拟(?:真实)?用户", r"隐藏 AI 身份", r"绕过风控"],
        "不要指导伪装真人、冒充身份或绕过平台风控；改成透明披露和合规自动化。",
        "E-008,R-005",
    ),
    (
        "OVERPROMISE_RISK",
        "medium",
        0.8,
        [r"100%[^\n]{0,12}(?:准确|无误|安全)", r"保证(?:省钱|降本|不出错)", r"绝对(?:安全|准确|不会)", r"永久(?:免费|无限)"],
        "删掉无法验证的绝对承诺；改成数据来源、置信度、适用边界和人工复核条件。",
        "E-008",
    ),
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

    for finding_type, severity, confidence, patterns, suggestion, evidence_ids in RISK_RULES:
        for pattern in patterns:
            match = re.search(pattern, redacted, flags=re.I)
            if match:
                findings.append(
                    make_finding(
                        batch,
                        finding_type,
                        severity,
                        confidence,
                        snippet(context(redacted, match.start(), match.end())),
                        suggestion,
                        evidence_ids,
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
    left = max(0, start - radius)
    right = min(len(text), end + radius)
    marker_start = text.rfind("[REDACTED:", 0, right)
    if marker_start >= left:
        marker_end = text.find("]", marker_start)
        if marker_end >= right:
            right = marker_end + 1
    return text[left:right]
