"""Report renderers for the session-level ledger."""

from __future__ import annotations

from html import escape as html_escape

from .ledger_models import SessionSummary, SnapshotSummary


def fmt(value: object) -> str:
    if value is None or value == "":
        return "未知"
    if isinstance(value, float):
        return f"{value:.2f}"
    return str(value)


def md_cell(value: object) -> str:
    return fmt(value).replace("\n", " ").replace("|", "\\|")


def render_sessions_markdown(sessions: list[SessionSummary], range_label: str) -> str:
    lines = [
        "# Codex 会话级 Token 账本",
        "",
        f"时间范围：{range_label}",
        "",
        "| 会话 | 项目 | token delta | credits delta | 上下文峰值 | 置信度 | 数据源 | 建议 |",
        "|---|---|---:|---:|---:|---|---|---|",
    ]
    for item in sessions:
        lines.append(
            f"| {md_cell(item.title)} | {md_cell(item.project)} | {item.token_delta} | {fmt(item.credits_delta)} | {fmt(item.context_peak_percent)} | {md_cell(item.confidence_level)} | {md_cell(item.source_type)} | {md_cell(item.recommendation)} |"
        )
    lines.extend(
        [
            "",
            "## 说明",
            "",
            "- `exact` 表示官方导出或等价结构化数据直接提供会话级用量。",
            "- `high` 表示同一会话快照可计算 delta。",
            "- `medium` 表示存在多会话或窗口重叠，只能按可见元信息归因。",
            "- `low` 只能作为估算，不能当作精确账单。",
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
        f"| 会话数 | {len(sessions)} |",
        f"| token delta | {total_tokens} |",
        f"| credits delta | {total_credits:.2f} |",
        f"| exact/high 置信会话 | {high_confidence} |",
        f"| 最耗会话 | {md_cell(top_session)} |",
        "",
        "## 会话排行",
        "",
        "| 排名 | 会话 | 项目 | token delta | credits delta | 置信度 | 数据源 | 建议 |",
        "|---:|---|---|---:|---:|---|---|---|",
    ]
    for index, item in enumerate(sessions, 1):
        lines.append(
            f"| {index} | {md_cell(item.title)} | {md_cell(item.project)} | {item.token_delta} | {fmt(item.credits_delta)} | {md_cell(item.confidence_level)} | {md_cell(item.source_type)} | {md_cell(item.recommendation)} |"
        )
    lines.extend(
        [
            "",
            "## 结论",
            "",
            ledger_conclusion(sessions),
            "",
            "## 隐私边界",
            "",
            "- 本报告不包含聊天正文。",
            "- 本报告不包含浏览器 cookie、OpenAI token、钥匙串、系统凭据或完整私密路径。",
            "- 低置信归因只能作为估算，不应作为精确账单。",
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
        f"| 开始时间 | {fmt(session.started_at)} |",
        f"| 结束时间 | {fmt(session.ended_at)} |",
        f"| token delta | {session.token_delta} |",
        f"| credits delta | {fmt(session.credits_delta)} |",
        f"| 上下文峰值 | {fmt(session.context_peak_percent)} |",
        f"| 数据源 | {md_cell(session.source_type)} |",
        f"| 置信度 | {session.confidence_level} ({session.confidence_score:.2f}) |",
        f"| 建议 | {md_cell(session.recommendation)} |",
        f"| 证据 | {md_cell(session.evidence_summary)} |",
        "",
        "## 时间线",
        "",
        "| 时间 | total_tokens | credits | context_used | context_limit | context_remaining | 数据源 |",
        "|---|---:|---:|---:|---:|---:|---|",
    ]
    for snap in snapshots:
        lines.append(
            f"| {md_cell(snap.captured_at)} | {fmt(snap.total_tokens)} | {fmt(snap.credits)} | {fmt(snap.context_used_tokens)} | {fmt(snap.context_limit_tokens)} | {fmt(snap.context_remaining_percent)} | {md_cell(snap.source_type)} |"
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
        "| 开始 | 结束 | token delta | credits delta | 判断 |",
        "|---|---|---:|---:|---|",
    ]
    for row in rows:
        lines.append(
            f"| {md_cell(row['start'])} | {md_cell(row['end'])} | {row['token_delta']} | {fmt(row['credits_delta'])} | {md_cell(row['label'])} |"
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
            if previous.credits is not None and current.credits is not None:
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


def render_dashboard_html(sessions: list[SessionSummary], range_label: str) -> str:
    total_tokens = sum(item.token_delta for item in sessions)
    total_credits = sum(item.credits_delta or 0 for item in sessions)
    row_blocks = []
    for item in sessions:
        row_blocks.append(
            "\n".join(
                [
                    "        <tr>",
                    f"          <td>{html_escape(item.title)}</td>",
                    f"          <td>{html_escape(item.project)}</td>",
                    f"          <td>{item.token_delta:,}</td>",
                    f"          <td>{fmt(item.credits_delta)}</td>",
                    f"          <td><span class=\"badge {item.confidence_level}\">{item.confidence_level}</span></td>",
                    f"          <td>{html_escape(item.recommendation)}</td>",
                    "        </tr>",
                ]
            )
        )
    rows = "\n".join(row_blocks)
    if not rows:
        rows = "<tr><td colspan=\"6\">暂无会话账本数据，请先导入官方导出或快照样本。</td></tr>"
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>BLCaptain Codex Ledger</title>
  <style>
    body {{ margin: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; color: #111827; background: #f4fbf7; }}
    main {{ max-width: 1180px; margin: 0 auto; padding: 42px 28px 64px; }}
    h1 {{ font-size: 44px; margin: 0 0 10px; letter-spacing: 0; }}
    p {{ color: #475569; font-size: 18px; }}
    .grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin: 28px 0; }}
    .stat, .panel {{ background: white; border: 1px solid #bbf7d0; border-radius: 8px; padding: 22px; }}
    .stat strong {{ display: block; font-size: 34px; margin-top: 8px; }}
    table {{ width: 100%; border-collapse: collapse; background: white; border: 1px solid #bbf7d0; border-radius: 8px; overflow: hidden; }}
    th, td {{ text-align: left; padding: 14px 16px; border-bottom: 1px solid #e2e8f0; font-size: 15px; }}
    th {{ background: #ecfdf5; color: #065f46; }}
    .badge {{ border-radius: 999px; padding: 4px 10px; font-weight: 700; }}
    .exact {{ background: #d9ff72; }}
    .high {{ background: #bbf7d0; }}
    .medium {{ background: #fde68a; }}
    .low {{ background: #fecaca; }}
  </style>
</head>
<body>
  <main>
    <h1>Codex 会话级 Token 账本</h1>
    <p>时间范围：{html_escape(range_label)}。所有数据来自本地账本，不上传云端，不读取聊天正文、cookie、token 或系统凭据。</p>
    <section class="grid">
      <div class="stat">会话数<strong>{len(sessions)}</strong></div>
      <div class="stat">token delta<strong>{total_tokens:,}</strong></div>
      <div class="stat">credits delta<strong>{total_credits:.2f}</strong></div>
    </section>
    <section class="panel">
      <h2>最耗 token 的会话</h2>
      <table>
        <thead>
          <tr><th>会话</th><th>项目</th><th>token delta</th><th>credits</th><th>置信度</th><th>建议</th></tr>
        </thead>
        <tbody>
          {rows}
        </tbody>
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


def ledger_conclusion(sessions: list[SessionSummary]) -> str:
    if not sessions:
        return "暂无会话账本数据。请先导入官方导出或本地快照。"
    top = sessions[0]
    if top.token_delta >= 100_000:
        return f"最耗会话是「{top.title}」，token delta 为 {top.token_delta:,}。建议先停止该长会话，保存成果后拆到新会话。"
    if top.token_delta >= 50_000:
        return f"最耗会话是「{top.title}」，token delta 为 {top.token_delta:,}。建议降配收尾或拆分后续任务。"
    return f"最耗会话是「{top.title}」，token delta 为 {top.token_delta:,}。当前可继续观察。"
