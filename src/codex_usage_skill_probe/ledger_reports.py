"""Report renderers for the session-level ledger."""

from __future__ import annotations

from datetime import datetime
from html import escape as html_escape

from .ledger_models import (
    BudgetAlert,
    ProjectSummary,
    SessionIntervalSummary,
    SessionSummary,
    SnapshotSummary,
    SourceConfidenceSummary,
    TaskTypeSummary,
    WeeklySummary,
)


def fmt(value: object) -> str:
    if value is None or value == "":
        return "未知"
    if isinstance(value, float):
        return f"{value:.2f}"
    return str(value)


def md_cell(value: object) -> str:
    return fmt(value).replace("\n", " ").replace("|", "\\|")


def local_time(value: str | None) -> str:
    if not value:
        return "未知"
    text = str(value)
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return text
    if parsed.tzinfo is None:
        parsed = parsed.astimezone()
    else:
        parsed = parsed.astimezone()
    offset = parsed.strftime("%z")
    if offset:
        offset_label = f"UTC{offset[:3]}:{offset[3:]}"
    else:
        offset_label = parsed.tzname() or "local"
    return f"{parsed:%Y-%m-%d %H:%M:%S} {offset_label}"


def timezone_note() -> str:
    return f"时间显示使用当前系统时区：{local_timezone_label()}。"


def local_timezone_label() -> str:
    return local_time(datetime.now().astimezone().isoformat()).split()[-1]


def local_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed.astimezone() if parsed.tzinfo else parsed.astimezone()


def render_sessions_markdown(sessions: list[SessionSummary], range_label: str) -> str:
    lines = [
        "# Codex 会话级 Token 账本",
        "",
        f"时间范围：{range_label}",
        timezone_note(),
        "",
        "| 会话 | 项目 | 开始时间 | 结束时间 | token delta | credits delta（来源值） | 上下文峰值 | 置信度 | 数据源 | 建议 |",
        "|---|---|---|---|---:|---:|---:|---|---|---|",
    ]
    for item in sessions:
        lines.append(
            f"| {md_cell(item.title)} | {md_cell(item.project)} | {md_cell(local_time(item.started_at))} | {md_cell(local_time(item.ended_at))} | {item.token_delta} | {fmt(item.credits_delta)} | {fmt(item.context_peak_percent)} | {md_cell(item.confidence_level)} | {md_cell(item.source_type)} | {md_cell(item.recommendation)} |"
        )
    lines.extend(
        [
            "",
            "## 严谨性说明",
            "",
            *precision_notes(),
        ]
    )
    return "\n".join(lines) + "\n"


def render_ledger_report_markdown(sessions: list[SessionSummary], range_label: str) -> str:
    total_tokens = sum(item.token_delta for item in sessions)
    total_credits = sum(item.credits_delta or 0 for item in sessions)
    high_confidence = len([item for item in sessions if item.confidence_level in {"exact", "high"}])
    top_session = sessions[0].title if sessions else "暂无"
    lines = [
        "# Codex 会话级 Token 总账报告",
        "",
        "定位：本地会话级账本。本报告只解释本地结构化账本数据，不替代官方 usage dashboard 或账单。",
        "",
        "## 总览",
        "",
        "| 字段 | 值 |",
        "|---|---|",
        f"| 时间范围 | {range_label} |",
        f"| 时间显示 | {timezone_note()} |",
        f"| 会话数 | {len(sessions)} |",
        f"| token delta | {total_tokens} |",
        f"| credits delta（来源值） | {total_credits:.2f} |",
        f"| exact/high 置信会话 | {high_confidence} |",
        f"| 最耗会话 | {md_cell(top_session)} |",
        "",
        "## 会话排行",
        "",
        "| 排名 | 会话 | 项目 | 开始时间 | 结束时间 | token delta | credits delta（来源值） | 置信度 | 数据源 | 建议 |",
        "|---:|---|---|---|---|---:|---:|---|---|---|",
    ]
    for index, item in enumerate(sessions, 1):
        lines.append(
            f"| {index} | {md_cell(item.title)} | {md_cell(item.project)} | {md_cell(local_time(item.started_at))} | {md_cell(local_time(item.ended_at))} | {item.token_delta} | {fmt(item.credits_delta)} | {md_cell(item.confidence_level)} | {md_cell(item.source_type)} | {md_cell(item.recommendation)} |"
        )
    lines.extend(
        [
            "",
            "## 结论",
            "",
            ledger_conclusion(sessions),
            "",
            "## 严谨性说明",
            "",
            *precision_notes(),
            "",
            "## 隐私边界",
            "",
            "- 本报告不包含聊天正文。",
            "- 本报告不包含浏览器 cookie、OpenAI token、钥匙串、系统凭据或完整私密路径。",
            "- 低置信归因只能作为估算，不应作为精确账单。",
        ]
    )
    return "\n".join(lines) + "\n"


def render_project_summary_markdown(projects: list[ProjectSummary], range_label: str) -> str:
    total_tokens = sum(item.token_delta for item in projects)
    total_credits = sum(item.credits_delta or 0 for item in projects)
    lines = [
        "# Codex 项目级用量汇总",
        "",
        "定位：按项目聚合本地会话级账本，帮助判断哪个项目最消耗上下文。本报告不替代官方 usage dashboard 或账单。",
        "",
        "## 总览",
        "",
        "| 字段 | 值 |",
        "|---|---|",
        f"| 时间范围 | {range_label} |",
        f"| 时间显示 | {timezone_note()} |",
        f"| 项目数 | {len(projects)} |",
        f"| token delta | {total_tokens} |",
        f"| credits delta（来源值） | {total_credits:.2f} |",
        "",
        "## 项目排行",
        "",
        "| 排名 | 项目 | 会话数 | token delta | credits delta（来源值） | 最高消耗会话 | 最高会话 token | 置信度分布 | 建议 |",
        "|---:|---|---:|---:|---:|---|---:|---|---|",
    ]
    for index, item in enumerate(projects, 1):
        lines.append(
            f"| {index} | {md_cell(item.project)} | {item.session_count} | {item.token_delta} | {fmt(item.credits_delta)} | {md_cell(item.top_session_title)} | {item.top_session_tokens} | {md_cell(format_confidence_counts(item.confidence_counts))} | {md_cell(item.recommendation)} |"
        )
    lines.extend(
        [
            "",
            "## 项目治理建议",
            "",
            project_conclusion(projects),
            "",
            "## 严谨性说明",
            "",
            *precision_notes(),
        ]
    )
    return "\n".join(lines) + "\n"


def render_weekly_report_markdown(weeks: list[WeeklySummary], range_label: str) -> str:
    total_tokens = sum(item.token_delta for item in weeks)
    total_credits = sum(item.credits_delta or 0 for item in weeks)
    lines = [
        "# Codex 周报",
        "",
        "定位：按本地系统时区的 ISO 周汇总 Codex 会话级账本，适合复盘一周内哪个项目和会话最消耗上下文。",
        "",
        "## 总览",
        "",
        "| 字段 | 值 |",
        "|---|---|",
        f"| 时间范围 | {range_label} |",
        f"| 时间显示 | {timezone_note()} |",
        f"| 周数 | {len(weeks)} |",
        f"| token delta | {total_tokens} |",
        f"| credits delta（来源值） | {total_credits:.2f} |",
        "",
        "## 周排行",
        "",
        "| 周 | 本地日期范围 | 会话数 | 项目数 | token delta | credits delta（来源值） | 最耗项目 | 最耗会话 | 最高会话 token | 置信度分布 | 建议 |",
        "|---|---|---:|---:|---:|---:|---|---|---:|---|---|",
    ]
    for item in weeks:
        lines.append(
            f"| {md_cell(item.week_label)} | {md_cell(item.week_start + ' 至 ' + item.week_end)} | {item.session_count} | {item.project_count} | {item.token_delta} | {fmt(item.credits_delta)} | {md_cell(item.top_project)} | {md_cell(item.top_session_title)} | {item.top_session_tokens} | {md_cell(format_confidence_counts(item.confidence_counts))} | {md_cell(item.recommendation)} |"
        )
    lines.extend(
        [
            "",
            "## 周报结论",
            "",
            weekly_conclusion(weeks),
            "",
            "## 严谨性说明",
            "",
            *precision_notes(),
        ]
    )
    return "\n".join(lines) + "\n"


def render_timeline_markdown(intervals: list[SessionIntervalSummary], range_label: str) -> str:
    lines = [
        "# Codex 阶段级高消耗时间线",
        "",
        "定位：把本地账本中的会话快照拆成阶段区间，帮助判断 token delta 是在哪一段时间增长的。本报告不读取聊天正文，也不替代官方账单。",
        "",
        f"时间范围：{range_label}",
        timezone_note(),
        "",
        "## 高消耗区间",
        "",
        "| 排名 | 会话 | 项目 | 阶段 | 开始 | 结束 | token delta | credits delta（来源值） | 上下文使用 | 风险 | 置信度 | 建议 |",
        "|---:|---|---|---|---|---|---:|---:|---:|---|---|---|",
    ]
    for index, item in enumerate(intervals, 1):
        lines.append(
            f"| {index} | {md_cell(item.title)} | {md_cell(item.project)} | {md_cell(item.stage_label)} | {md_cell(local_time(item.start_at))} | {md_cell(local_time(item.end_at))} | {item.token_delta} | {fmt(item.credits_delta)} | {fmt(item.context_used_percent)} | {md_cell(item.severity)} | {md_cell(item.confidence_level)} | {md_cell(item.recommendation)} |"
        )
    if not intervals:
        lines.append("|  | 暂无可计算区间 |  |  |  |  | 0 | 未知 | 未知 | low | low | 请先导入含 token 快照的数据源 |")
    lines.extend(
        [
            "",
            "## 阶段标签说明",
            "",
            "- 阶段标签来自会话标题、项目名、来源证据和建议文本的保守关键词推断。",
            "- 如果标题和来源字段不足，阶段会显示为 `未知任务`，不会硬猜。",
            "- 本报告只展示 token/credits 元信息，不展示 prompt、assistant 输出或工具参数。",
            "",
            "## 严谨性说明",
            "",
            *precision_notes(),
        ]
    )
    return "\n".join(lines) + "\n"


def render_alerts_markdown(alerts: list[BudgetAlert], range_label: str) -> str:
    lines = [
        "# Codex 本地预算与停止线预警",
        "",
        "定位：基于本地阈值判断单会话、项目、总账和上下文健康度风险。它不是官方账单，也不承诺省钱。",
        "",
        f"时间范围：{range_label}",
        timezone_note(),
        "",
        "## 预警列表",
        "",
        "| 范围 | 名称 | token/指标 | 阈值 | 使用率 | 风险 | 置信度 | 原因 | 建议 |",
        "|---|---|---:|---:|---:|---|---|---|---|",
    ]
    for item in alerts:
        lines.append(
            f"| {md_cell(item.scope)} | {md_cell(item.name)} | {item.token_delta} | {fmt(item.threshold)} | {item.usage_percent:.1f}% | {md_cell(item.severity)} | {md_cell(item.confidence_level)} | {md_cell(item.reason)} | {md_cell(item.recommendation)} |"
        )
    if not alerts:
        lines.append("| 当前范围 | 暂无预警 | 0 | 未触发 | 0.0% | low | low | 未超过本地阈值 | 可以继续观察 |")
    lines.extend(
        [
            "",
            "## 停止线口径",
            "",
            "- 单会话达到本地阈值：建议停止或拆到新会话。",
            "- 项目周期达到本地阈值：建议先做项目级总结，再拆分后续目标。",
            "- 当前时间范围总账达到本地阈值：建议暂停大任务，分批执行。",
            "- 上下文剩余低于阈值：建议停止继续堆上下文，避免后续每步都变贵。",
            "",
            "## 严谨性说明",
            "",
            *precision_notes(),
        ]
    )
    return "\n".join(lines) + "\n"


def render_task_report_markdown(tasks: list[TaskTypeSummary], range_label: str) -> str:
    lines = [
        "# Codex 任务类型归因报告",
        "",
        "定位：按保守任务类型聚合本地会话级账本，帮助判断 token 主要消耗在开发、测试、文档、发布还是调研阶段。",
        "",
        f"时间范围：{range_label}",
        timezone_note(),
        "",
        "| 排名 | 任务类型 | 会话数 | token delta | credits delta（来源值） | 最高消耗会话 | 最高会话 token | 置信度分布 | 建议 |",
        "|---:|---|---:|---:|---:|---|---:|---|---|",
    ]
    for index, item in enumerate(tasks, 1):
        lines.append(
            f"| {index} | {md_cell(item.task_type)} | {item.session_count} | {item.token_delta} | {fmt(item.credits_delta)} | {md_cell(item.top_session_title)} | {item.top_session_tokens} | {md_cell(format_confidence_counts(item.confidence_counts))} | {md_cell(item.recommendation)} |"
        )
    if not tasks:
        lines.append("|  | 暂无任务归因 | 0 | 0 | 未知 | 暂无 | 0 | 未知 | 请先导入会话级账本数据 |")
    lines.extend(
        [
            "",
            "## 归因边界",
            "",
            "- 任务类型来自标题、项目名和来源证据的关键词推断，不读取聊天正文。",
            "- 证据不足时使用 `未知任务`，不伪造阶段。",
            "- 建议用于工作流治理，不用于财务结算。",
        ]
    )
    return "\n".join(lines) + "\n"


def render_confidence_markdown(sources: list[SourceConfidenceSummary]) -> str:
    lines = [
        "# Codex 数据源可信度报告",
        "",
        "定位：解释每个数据源能支持多精细的 token 归因，以及为什么有些字段不能更精确。",
        "",
        "| 数据源 | 启用 | 置信上限 | 会话数 | 快照数 | 已有字段 | 缺失字段 | 诊断 |",
        "|---|---|---|---:|---:|---|---|---|",
    ]
    for item in sources:
        lines.append(
            f"| {md_cell(item.source_type)} | {item.enabled} | {md_cell(item.confidence_ceiling)} | {item.session_count} | {item.snapshot_count} | {md_cell(', '.join(item.fields_present) or '无')} | {md_cell(', '.join(item.missing_fields) or '无')} | {md_cell(item.diagnosis)} |"
        )
    if not sources:
        lines.append("| 暂无数据源 | False | low | 0 | 0 | 无 | 全部 | 请先初始化或导入数据源 |")
    lines.extend(
        [
            "",
            "## 口径说明",
            "",
            "- `official_export`：用户显式提供的官方或等价结构化导出，若含会话级 token 字段，置信上限可到 `exact`。",
            "- `local_codex_rollout`：本地结构化 rollout token 字段，置信上限通常为 `high`，不是官方账单。",
            "- `snapshot_delta`：用户显式提供或本地快照推导的 delta，置信度取决于是否能稳定关联会话和时间窗口。",
            "- 如果缺少 `total_tokens`、模型、项目或上下文窗口，本工具会显示缺失，不会补造。",
            "",
            "## 隐私边界",
            "",
            "- 不登录 OpenAI，不读取浏览器 cookie、OpenAI token、钥匙串或系统凭据。",
            "- 不抓包、不代理、不拦截请求、不读取聊天正文。",
            "- 所有报告均基于本地用户显式提供或本机可见的结构化用量字段。",
        ]
    )
    return "\n".join(lines) + "\n"


def render_session_detail_markdown(session: SessionSummary, snapshots: list[SnapshotSummary]) -> str:
    lines = [
        "# Codex 单会话用量详情",
        "",
        "| 字段 | 值 |",
        "|---|---|",
        f"| 会话 | {md_cell(session.title)} |",
        f"| session_id | `{md_cell(session.session_id)}` |",
        f"| 项目 | {md_cell(session.project)} |",
        f"| 开始时间 | {md_cell(local_time(session.started_at))} |",
        f"| 结束时间 | {md_cell(local_time(session.ended_at))} |",
        f"| token delta | {session.token_delta} |",
        f"| credits delta（来源值） | {fmt(session.credits_delta)} |",
        f"| 上下文峰值 | {fmt(session.context_peak_percent)} |",
        f"| 数据源 | {md_cell(session.source_type)} |",
        f"| 置信度 | {session.confidence_level} ({session.confidence_score:.2f}) |",
        f"| 建议 | {md_cell(session.recommendation)} |",
        f"| 证据 | {md_cell(session.evidence_summary)} |",
        "",
        "## 时间线",
        "",
        f"{timezone_note()}",
        "",
        "| 时间 | total_tokens | credits（来源值） | context_used | context_limit | context_remaining | 数据源 |",
        "|---|---:|---:|---:|---:|---:|---|",
    ]
    for snap in snapshots:
        lines.append(
            f"| {md_cell(local_time(snap.captured_at))} | {fmt(snap.total_tokens)} | {fmt(snap.credits)} | {fmt(snap.context_used_tokens)} | {fmt(snap.context_limit_tokens)} | {fmt(snap.context_remaining_percent)} | {md_cell(snap.source_type)} |"
        )
    lines.extend(
        [
            "",
            "## 高消耗区间",
            "",
            render_interval_table(session, snapshots),
            "",
            "## 高消耗判断",
            "",
            high_usage_note(session),
            "",
            "## 严谨性说明",
            "",
            *precision_notes(),
            "",
            "## 隐私边界",
            "",
            "- 本报告只展示会话元信息和 token/credits 数字。",
            "- 不包含聊天正文、浏览器 cookie、OpenAI token、系统凭据或完整私密路径。",
        ]
    )
    return "\n".join(lines) + "\n"


def render_interval_table(session: SessionSummary, snapshots: list[SnapshotSummary]) -> str:
    rows = interval_rows(session, snapshots)
    if not rows:
        return "暂无可计算区间。"
    lines = [
        "| 开始 | 结束 | token delta | credits delta（来源值） | 判断 |",
        "|---|---|---:|---:|---|",
    ]
    for row in rows:
        lines.append(
            f"| {md_cell(local_time(str(row['start'])))} | {md_cell(local_time(str(row['end'])))} | {row['token_delta']} | {fmt(row['credits_delta'])} | {md_cell(row['label'])} |"
        )
    return "\n".join(lines)


def interval_rows(session: SessionSummary, snapshots: list[SnapshotSummary]) -> list[dict[str, object]]:
    if len(snapshots) >= 2:
        rows = []
        previous = snapshots[0]
        for current in snapshots[1:]:
            prev_tokens = previous.total_tokens or 0
            current_tokens = current.total_tokens or 0
            token_delta = max(0, current_tokens - prev_tokens)
            credits_delta = None
            if (
                previous.credits is not None
                and current.credits is not None
                and previous.source_type != "local_codex_rollout"
                and current.source_type != "local_codex_rollout"
            ):
                credits_delta = max(0.0, current.credits - previous.credits)
            rows.append(
                {
                    "start": previous.captured_at,
                    "end": current.captured_at,
                    "token_delta": token_delta,
                    "credits_delta": credits_delta,
                    "label": interval_label(token_delta),
                }
            )
            previous = current
        return rows
    if session.token_delta > 0:
        return [
            {
                "start": session.started_at or "未知",
                "end": session.ended_at or "未知",
                "token_delta": session.token_delta,
                "credits_delta": session.credits_delta,
                "label": interval_label(session.token_delta),
            }
        ]
    return []


def interval_label(token_delta: int) -> str:
    if token_delta >= 50_000:
        return "高消耗区间"
    if token_delta >= 20_000:
        return "需要观察"
    return "正常"


def render_privacy_markdown(sources: list[dict[str, object]], audits: list[dict[str, object]]) -> str:
    lines = [
        "# Codex Ledger 隐私审计报告",
        "",
        "## 数据源",
        "",
        "| 类型 | 是否启用 | 置信度上限 | 授权范围 |",
        "|---|---|---|---|",
    ]
    for source in sources:
        lines.append(
            f"| {md_cell(source['type'])} | {bool(source['enabled'])} | {md_cell(source['confidence_ceiling'])} | {md_cell(source['permission_scope'])} |"
        )
    lines.extend(
        [
            "",
            "## 审计日志",
            "",
            "| 时间 | 动作 | 摘要 |",
            "|---|---|---|",
        ]
    )
    for audit in audits:
        lines.append(f"| {md_cell(audit['created_at'])} | {md_cell(audit['action'])} | {md_cell(audit['details_json'])} |")
    lines.extend(
        [
            "",
            "## 明确不读取",
            "",
            "- 浏览器 cookie",
            "- OpenAI token",
            "- 钥匙串和系统凭据",
            "- 聊天正文",
            "- 完整私密路径",
        ]
    )
    return "\n".join(lines) + "\n"


def render_dashboard_html(
    sessions: list[SessionSummary],
    range_label: str,
    *,
    alerts: list[BudgetAlert] | None = None,
    sources: list[SourceConfidenceSummary] | None = None,
    tasks: list[TaskTypeSummary] | None = None,
) -> str:
    total_tokens = sum(item.token_delta for item in sessions)
    total_credits = sum(item.credits_delta or 0 for item in sessions)
    exact_high = len([item for item in sessions if item.confidence_level in {"exact", "high"}])
    top = sessions[0] if sessions else None
    alert_items = alerts or []
    source_items = sources or []
    task_items = tasks or []
    now = datetime.now().astimezone()
    today_tokens = sum(item.token_delta for item in sessions if (local_datetime(item.ended_at) or local_datetime(item.started_at) or now).date() == now.date())
    current_year, current_week, _ = now.date().isocalendar()
    week_tokens = 0
    for item in sessions:
        dt = local_datetime(item.ended_at) or local_datetime(item.started_at)
        if dt and dt.date().isocalendar()[:2] == (current_year, current_week):
            week_tokens += item.token_delta
    stop_sessions = [item for item in sessions if item.token_delta >= 100_000 or (item.context_peak_percent or 0) >= 80]
    high_risk_sessions = [item for item in sessions if item.token_delta >= 50_000 or (item.context_peak_percent or 0) >= 70]
    project_totals: dict[str, int] = {}
    for item in sessions:
        project_totals[item.project] = project_totals.get(item.project, 0) + item.token_delta
    high_risk_projects = [name for name, value in project_totals.items() if value >= 250_000]
    model_options = sorted({item.model for item in sessions if item.model})
    row_blocks = []
    for item in sessions:
        row_blocks.append(
            "\n".join(
                [
                    f"        <tr data-project=\"{html_escape(item.project.lower())}\" data-confidence=\"{html_escape(item.confidence_level)}\" data-model=\"{html_escape((item.model or '').lower())}\" data-start=\"{html_escape(item.started_at[:10])}\">",
                    f"          <td>{html_escape(item.title)}</td>",
                    f"          <td>{html_escape(item.project)}</td>",
                    f"          <td>{html_escape(item.model or '未知')}</td>",
                    f"          <td>{html_escape(local_time(item.started_at))}</td>",
                    f"          <td>{html_escape(local_time(item.ended_at))}</td>",
                    f"          <td>{item.token_delta:,}</td>",
                    f"          <td>{fmt(item.credits_delta)}</td>",
                    f"          <td>{fmt(item.context_peak_percent)}</td>",
                    f"          <td><span class=\"badge {item.confidence_level}\">{item.confidence_level}</span></td>",
                    f"          <td>{html_escape(item.recommendation)}</td>",
                    "        </tr>",
                ]
            )
        )
    rows = "\n".join(row_blocks)
    if not rows:
        rows = "<tr><td colspan=\"10\">暂无会话账本数据，请先导入官方导出、local history 或快照样本。</td></tr>"
    detail_blocks = []
    for item in sessions[:6]:
        detail_blocks.append(
            "\n".join(
                [
                    "<article class=\"detail\">",
                    f"  <h3>{html_escape(item.title)}</h3>",
                    f"  <p>{html_escape(item.project)} · {html_escape(local_time(item.started_at))} → {html_escape(local_time(item.ended_at))}</p>",
                    "  <dl>",
                    f"    <div><dt>token delta</dt><dd>{item.token_delta:,}</dd></div>",
                    f"    <div><dt>置信度</dt><dd>{html_escape(item.confidence_level)} / {item.confidence_score:.2f}</dd></div>",
                    f"    <div><dt>数据源</dt><dd>{html_escape(item.source_type)}</dd></div>",
                    f"    <div><dt>建议</dt><dd>{html_escape(item.recommendation)}</dd></div>",
                    "  </dl>",
                    f"  <p class=\"evidence\">{html_escape(item.evidence_summary)}</p>",
                    "</article>",
                ]
            )
        )
    details = "\n".join(detail_blocks) or "<p>暂无单会话详情。</p>"
    decision = html_escape(ledger_conclusion(sessions))
    alert_rows = "\n".join(
        f"<tr><td>{html_escape(item.scope)}</td><td>{html_escape(item.name)}</td><td>{item.token_delta:,}</td><td>{item.usage_percent:.1f}%</td><td><span class=\"risk {html_escape(item.severity)}\">{html_escape(item.severity)}</span></td><td>{html_escape(item.recommendation)}</td></tr>"
        for item in alert_items[:8]
    ) or "<tr><td colspan=\"6\">暂无本地预算预警</td></tr>"
    source_rows = "\n".join(
        f"<tr><td>{html_escape(item.source_type)}</td><td>{html_escape(item.confidence_ceiling)}</td><td>{item.snapshot_count}</td><td>{html_escape(', '.join(item.missing_fields) or '无')}</td><td>{html_escape(item.diagnosis)}</td></tr>"
        for item in source_items
    ) or "<tr><td colspan=\"5\">暂无数据源可信度记录</td></tr>"
    task_rows = "\n".join(
        f"<tr><td>{html_escape(item.task_type)}</td><td>{item.session_count}</td><td>{item.token_delta:,}</td><td>{html_escape(item.recommendation)}</td></tr>"
        for item in task_items[:8]
    ) or "<tr><td colspan=\"4\">暂无任务归因</td></tr>"
    model_select_options = "\n".join(
        f"<option value=\"{html_escape(model.lower())}\">{html_escape(model)}</option>" for model in model_options
    )
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>BLCaptain Codex Ledger</title>
  <style>
    body {{ margin: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; color: #111827; background: #f8fafc; }}
    main {{ max-width: 1240px; margin: 0 auto; padding: 34px 28px 56px; }}
    h1 {{ font-size: 34px; margin: 0 0 8px; letter-spacing: 0; }}
    h2 {{ margin: 0 0 14px; font-size: 22px; }}
    h3 {{ margin: 0 0 8px; font-size: 18px; }}
    p {{ color: #475569; font-size: 16px; line-height: 1.6; }}
    .topline {{ display: flex; justify-content: space-between; gap: 16px; align-items: flex-start; border-bottom: 1px solid #cbd5e1; padding-bottom: 20px; }}
    .topline p {{ margin: 0; max-width: 760px; }}
    .grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin: 22px 0; }}
    .stat, .panel, .detail {{ background: white; border: 1px solid #cbd5e1; border-radius: 8px; padding: 18px; }}
    .stat span {{ color: #64748b; font-size: 13px; }}
    .stat strong {{ display: block; font-size: 28px; margin-top: 8px; }}
    .decision {{ border-left: 4px solid #0f766e; background: #f0fdfa; padding: 14px 16px; margin: 18px 0 24px; }}
    .panel {{ margin-top: 18px; overflow-x: auto; }}
    .filters {{ display: grid; grid-template-columns: 1.3fr repeat(4, 1fr); gap: 10px; align-items: end; margin-bottom: 14px; }}
    label {{ display: grid; gap: 6px; color: #475569; font-size: 13px; font-weight: 600; }}
    input, select {{ height: 38px; border: 1px solid #cbd5e1; border-radius: 6px; padding: 0 10px; font: inherit; background: white; }}
    .filter-count {{ color: #64748b; font-size: 13px; margin: 0 0 10px; }}
    table {{ width: 100%; min-width: 900px; border-collapse: collapse; background: white; }}
    th, td {{ text-align: left; padding: 12px 14px; border-bottom: 1px solid #e2e8f0; font-size: 14px; vertical-align: top; }}
    th {{ background: #f1f5f9; color: #334155; }}
    th:nth-child(3), td:nth-child(3) {{ min-width: 76px; white-space: nowrap; }}
    .details {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; }}
    dl {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; margin: 12px 0; }}
    dt {{ color: #64748b; font-size: 12px; }}
    dd {{ margin: 3px 0 0; font-weight: 700; }}
    .evidence {{ font-size: 14px; margin-bottom: 0; }}
    .privacy ul {{ margin: 0; padding-left: 20px; color: #334155; line-height: 1.8; }}
    .badge {{ border-radius: 999px; padding: 4px 10px; font-weight: 700; }}
    .risk {{ border-radius: 6px; padding: 4px 8px; font-weight: 700; }}
    .critical {{ background: #fee2e2; color: #991b1b; }}
    .exact {{ background: #d9ff72; }}
    .high {{ background: #bbf7d0; }}
    .medium {{ background: #fde68a; }}
    .low {{ background: #fecaca; }}
    @media (max-width: 820px) {{
      main {{ padding: 24px 16px 40px; }}
      .topline {{ display: block; }}
      .grid, .details, .filters {{ grid-template-columns: 1fr; }}
      h1 {{ font-size: 28px; }}
    }}
  </style>
</head>
<body>
  <main>
    <section class="topline">
      <div>
        <h1>Codex 会话级 Token 账本</h1>
        <p>时间范围：{html_escape(range_label)}。所有数据来自本地账本，不上传云端，不读取聊天正文、cookie、token 或系统凭据。</p>
      </div>
      <p>最高消耗会话：{html_escape(top.title if top else "暂无")}</p>
    </section>
    <section class="grid">
      <div class="stat"><span>会话数</span><strong>{len(sessions)}</strong></div>
      <div class="stat"><span>token delta</span><strong>{total_tokens:,}</strong></div>
      <div class="stat"><span>credits delta（来源值）</span><strong>{total_credits:.2f}</strong></div>
      <div class="stat"><span>exact/high 会话</span><strong>{exact_high}</strong></div>
    </section>
    <section class="grid" aria-label="风险摘要">
      <div class="stat"><span>今日 token</span><strong>{today_tokens:,}</strong></div>
      <div class="stat"><span>本周 token</span><strong>{week_tokens:,}</strong></div>
      <div class="stat"><span>高风险会话</span><strong>{len(high_risk_sessions)}</strong></div>
      <div class="stat"><span>高风险项目</span><strong>{len(high_risk_projects)}</strong></div>
      <div class="stat"><span>该停会话</span><strong>{len(stop_sessions)}</strong></div>
    </section>
    <section class="decision">{decision}</section>
    <section class="panel">
      <h2>本地预算预警</h2>
      <table>
        <thead><tr><th>范围</th><th>名称</th><th>token/指标</th><th>使用率</th><th>风险</th><th>建议</th></tr></thead>
        <tbody>{alert_rows}</tbody>
      </table>
    </section>
    <section class="panel">
      <h2>数据源可信度</h2>
      <table>
        <thead><tr><th>数据源</th><th>置信上限</th><th>快照数</th><th>缺失字段</th><th>诊断</th></tr></thead>
        <tbody>{source_rows}</tbody>
      </table>
    </section>
    <section class="panel">
      <h2>任务类型归因</h2>
      <table>
        <thead><tr><th>任务类型</th><th>会话数</th><th>token delta</th><th>建议</th></tr></thead>
        <tbody>{task_rows}</tbody>
      </table>
    </section>
    <section class="panel">
      <h2>会话排行</h2>
      <div class="filters" aria-label="会话筛选">
        <label>项目
          <input id="projectFilter" type="search" placeholder="输入项目关键词">
        </label>
        <label>开始日期
          <input id="fromFilter" type="date">
        </label>
        <label>结束日期
          <input id="toFilter" type="date">
        </label>
        <label>置信度
          <select id="confidenceFilter">
            <option value="">全部</option>
            <option value="exact">exact</option>
            <option value="high">high</option>
            <option value="medium">medium</option>
            <option value="low">low</option>
          </select>
        </label>
        <label>模型
          <select id="modelFilter">
            <option value="">全部</option>
            {model_select_options}
          </select>
        </label>
      </div>
      <p class="filter-count" id="filterCount">显示 {len(sessions)} / {len(sessions)} 个会话</p>
      <table>
        <thead>
          <tr><th>会话</th><th>项目</th><th>模型</th><th>开始</th><th>结束</th><th>token delta</th><th>credits</th><th>上下文峰值</th><th>置信度</th><th>建议</th></tr>
        </thead>
        <tbody>
          {rows}
        </tbody>
      </table>
    </section>
    <section class="panel">
      <h2>单会话详情摘要</h2>
      <div class="details">
        {details}
      </div>
    </section>
    <section class="panel privacy">
      <h2>隐私边界</h2>
      <ul>
        <li>{html_escape(timezone_note())}</li>
        <li>本页面只展示本地账本中的会话元信息和 token/credits 数字。</li>
        <li>credits 是来源提供的数值或同口径 delta，不等同于美元、人民币或官方账单金额。</li>
        <li>不包含聊天正文、prompt、assistant 输出、浏览器 cookie、OpenAI token、钥匙串或系统凭据。</li>
        <li>local Codex 历史导入默认隐藏完整路径，只保留哈希和短会话标识。</li>
        <li>低置信归因只能作为估算，不应当作精确账单。</li>
      </ul>
    </section>
  </main>
  <script>
    const rows = Array.from(document.querySelectorAll("tbody tr[data-project]"));
    const totalRows = rows.length;
    const projectFilter = document.getElementById("projectFilter");
    const fromFilter = document.getElementById("fromFilter");
    const toFilter = document.getElementById("toFilter");
    const confidenceFilter = document.getElementById("confidenceFilter");
    const modelFilter = document.getElementById("modelFilter");
    const filterCount = document.getElementById("filterCount");

    function applyFilters() {{
      const project = projectFilter.value.trim().toLowerCase();
      const from = fromFilter.value;
      const to = toFilter.value;
      const confidence = confidenceFilter.value;
      const model = modelFilter.value;
      let visible = 0;
      rows.forEach((row) => {{
        const start = row.dataset.start || "";
        const ok =
          (!project || row.dataset.project.includes(project)) &&
          (!from || start >= from) &&
          (!to || start <= to) &&
          (!confidence || row.dataset.confidence === confidence) &&
          (!model || row.dataset.model === model);
        row.hidden = !ok;
        if (ok) visible += 1;
      }});
      filterCount.textContent = `显示 ${{visible}} / ${{totalRows}} 个会话`;
    }}

    [projectFilter, fromFilter, toFilter, confidenceFilter, modelFilter].forEach((item) => {{
      item.addEventListener("input", applyFilters);
      item.addEventListener("change", applyFilters);
    }});
  </script>
</body>
</html>
"""


def render_watch_status_html(
    state: dict[str, object],
    logs: list[str],
    sessions: list[SessionSummary],
    *,
    alerts: list[BudgetAlert] | None = None,
) -> str:
    status = str(state.get("status") or "unknown")
    status_class = "running" if status == "running" else "error" if status == "error" else "stopped"
    rows = "\n".join(
        [
            f"<tr><th>{html_escape(str(key))}</th><td>{html_escape(fmt(value))}</td></tr>"
            for key, value in state.items()
            if key not in {"ok"}
        ]
    )
    log_items = "\n".join(f"<li>{html_escape(line)}</li>" for line in logs[-30:]) or "<li>暂无日志</li>"
    top_sessions = "\n".join(
        f"<tr><td>{html_escape(item.title)}</td><td>{item.token_delta:,}</td><td>{html_escape(item.confidence_level)}</td><td>{html_escape(item.recommendation)}</td></tr>"
        for item in sessions[:8]
    ) or "<tr><td colspan=\"4\">暂无会话数据</td></tr>"
    alert_rows = "\n".join(
        f"<tr><td>{html_escape(item.scope)}</td><td>{html_escape(item.name)}</td><td>{item.token_delta:,}</td><td>{html_escape(item.severity)}</td><td>{html_escape(item.recommendation)}</td></tr>"
        for item in (alerts or [])[:8]
    ) or "<tr><td colspan=\"5\">暂无本地预算预警</td></tr>"
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Codex Probe Watcher 状态</title>
  <style>
    body {{ margin: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; color: #111827; background: #f8fafc; }}
    main {{ max-width: 1040px; margin: 0 auto; padding: 34px 24px 56px; }}
    h1 {{ margin: 0 0 8px; font-size: 32px; }}
    h2 {{ font-size: 20px; margin: 0 0 12px; }}
    p {{ color: #475569; line-height: 1.6; }}
    .badge {{ display: inline-block; border-radius: 999px; padding: 5px 12px; font-weight: 700; }}
    .running {{ background: #bbf7d0; }}
    .stopped {{ background: #e2e8f0; }}
    .error {{ background: #fecaca; }}
    .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 14px; margin-top: 20px; }}
    section {{ background: white; border: 1px solid #cbd5e1; border-radius: 8px; padding: 18px; }}
    table {{ width: 100%; border-collapse: collapse; }}
    th, td {{ text-align: left; border-bottom: 1px solid #e2e8f0; padding: 10px 8px; vertical-align: top; }}
    th {{ color: #475569; width: 210px; }}
    ul {{ margin: 0; padding-left: 18px; line-height: 1.8; }}
    @media (max-width: 760px) {{ .grid {{ grid-template-columns: 1fr; }} }}
  </style>
</head>
<body>
  <main>
    <h1>Codex Probe Watcher 状态</h1>
    <p><span class="badge {status_class}">{html_escape(status)}</span> 本页面只读取本地 watcher 状态、日志和账本摘要，不读取聊天正文、cookie、token 或系统凭据。</p>
    <div class="grid">
      <section>
        <h2>运行状态</h2>
        <table>{rows}</table>
      </section>
      <section>
        <h2>最近日志</h2>
        <ul>{log_items}</ul>
      </section>
    </div>
    <section style="margin-top:14px">
      <h2>最近预警</h2>
      <table>
        <thead><tr><th>范围</th><th>名称</th><th>token/指标</th><th>风险</th><th>建议</th></tr></thead>
        <tbody>{alert_rows}</tbody>
      </table>
    </section>
    <section style="margin-top:14px">
      <h2>最近会话排行</h2>
      <table>
        <thead><tr><th>会话</th><th>token delta</th><th>置信度</th><th>建议</th></tr></thead>
        <tbody>{top_sessions}</tbody>
      </table>
    </section>
  </main>
</body>
</html>
"""


def high_usage_note(session: SessionSummary) -> str:
    if session.token_delta >= 100_000:
        return "- 该会话 token delta 超过 100,000，属于高消耗会话；建议停止当前长会话，开新会话只带必要上下文。"
    if session.token_delta >= 50_000:
        return "- 该会话 token delta 超过 50,000，建议降配收尾或拆分后续任务。"
    return "- 当前会话未达到高消耗阈值，可以继续观察。"


def precision_notes() -> list[str]:
    return [
        "- `credits` 表示数据源提供的 credits / cost / quota 数值；不同来源口径可能不同，本工具不换算成美元、人民币或官方账单金额。",
        "- `credits delta` 只在同一来源同一口径可解释为消耗差值时展示；无法确认口径时显示为 `未知`。",
        "- `exact` 表示用户显式提供的官方导出或等价结构化数据直接给出会话级 token 字段。",
        "- `high` 表示本地结构化记录能稳定关联到会话和 token 字段，但仍不是官方账单。",
        "- `medium` 表示存在多会话或时间窗口重叠，只能按可见元信息归因。",
        "- `low` 只能作为估算，不能当作精确账单。",
        "- `建议` 是基于 token delta 阈值的治理动作：>=100,000 建议停止；>=50,000 建议降配或拆分；低于阈值建议继续观察。",
    ]


def ledger_conclusion(sessions: list[SessionSummary]) -> str:
    if not sessions:
        return "暂无会话账本数据。请先导入官方导出或本地快照。"
    top = sessions[0]
    if top.token_delta >= 100_000:
        return f"最耗会话是「{top.title}」，token delta 为 {top.token_delta:,}。建议先停止该长会话，保存成果后拆到新会话。"
    if top.token_delta >= 50_000:
        return f"最耗会话是「{top.title}」，token delta 为 {top.token_delta:,}。建议降配收尾或拆分后续任务。"
    return f"最耗会话是「{top.title}」，token delta 为 {top.token_delta:,}。当前可继续观察。"


def project_conclusion(projects: list[ProjectSummary]) -> str:
    if not projects:
        return "暂无项目级账本数据。请先导入官方导出、本地历史或快照样本。"
    top = projects[0]
    return (
        f"最耗项目是「{top.project}」，token delta 为 {top.token_delta:,}，"
        f"最高消耗会话是「{top.top_session_title}」。{top.recommendation}。"
    )


def weekly_conclusion(weeks: list[WeeklySummary]) -> str:
    if not weeks:
        return "暂无周报数据。请先导入会话级账本数据。"
    top = max(weeks, key=lambda item: item.token_delta)
    return (
        f"最高消耗周是 {top.week_label}（{top.week_start} 至 {top.week_end}），"
        f"token delta 为 {top.token_delta:,}，最耗项目是「{top.top_project}」。{top.recommendation}。"
    )


def format_confidence_counts(counts: dict[str, int]) -> str:
    parts = []
    for level in ["exact", "high", "medium", "low"]:
        count = counts.get(level, 0)
        if count:
            parts.append(f"{level}:{count}")
    return " / ".join(parts) if parts else "未知"
