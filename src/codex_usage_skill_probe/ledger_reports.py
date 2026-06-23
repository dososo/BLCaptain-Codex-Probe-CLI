"""Report renderers for the session-level ledger."""

from __future__ import annotations

from datetime import datetime
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


def render_dashboard_html(sessions: list[SessionSummary], range_label: str) -> str:
    total_tokens = sum(item.token_delta for item in sessions)
    total_credits = sum(item.credits_delta or 0 for item in sessions)
    exact_high = len([item for item in sessions if item.confidence_level in {"exact", "high"}])
    top = sessions[0] if sessions else None
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
    .details {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; }}
    dl {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; margin: 12px 0; }}
    dt {{ color: #64748b; font-size: 12px; }}
    dd {{ margin: 3px 0 0; font-weight: 700; }}
    .evidence {{ font-size: 14px; margin-bottom: 0; }}
    .privacy ul {{ margin: 0; padding-left: 20px; color: #334155; line-height: 1.8; }}
    .badge {{ border-radius: 999px; padding: 4px 10px; font-weight: 700; }}
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
    <section class="decision">{decision}</section>
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


def render_watch_status_html(state: dict[str, object], logs: list[str], sessions: list[SessionSummary]) -> str:
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
