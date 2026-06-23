"""Safe source discovery for the local ledger."""

from __future__ import annotations

from pathlib import Path

from .local_history import default_codex_root, inspect_local_codex
from .ledger_models import SourceDoctorResult
from .ledger_storage import upsert_source


def run_source_doctor(conn, root: Path | None = None, *, deep: bool = False, local_codex=None) -> list[SourceDoctorResult]:
    root = root or Path.cwd()
    sample_dir = root / "examples" / "ledger-samples"
    local_codex = local_codex if local_codex is not None else inspect_local_codex(default_codex_root(), limit_files=40) if deep else None
    results = [
        SourceDoctorResult(
            source_type="official_export",
            available=True,
            confidence_ceiling="exact",
            permission_scope="仅导入用户显式提供的官方 CSV/JSON/JSONL 文件",
            privacy_note="不读取浏览器、cookie、token、钥匙串或聊天正文",
            next_step="使用 codex-probe ledger import --official-export <file>",
        ),
        SourceDoctorResult(
            source_type="snapshot_delta",
            available=True,
            confidence_ceiling="high",
            permission_scope="仅导入用户显式提供的本地快照 JSON/CSV",
            privacy_note="只处理会话元信息和 token 数字",
            next_step="使用 codex-probe ledger import --snapshot <file>",
        ),
        SourceDoctorResult(
            source_type="local_status",
            available=(sample_dir / "local-status-snapshots.json").exists(),
            confidence_ceiling="high",
            permission_scope="预留 allowlist 字段读取，不扫描私密目录",
            privacy_note="P0 只做安全探测和样本导入，不读取真实聊天正文",
            next_step="使用显式快照文件验证后再启用",
        ),
        SourceDoctorResult(
            source_type="local_codex_rollout",
            available=bool(local_codex and local_codex.importable_record_count),
            confidence_ceiling="high",
            permission_scope="只读取本机 Codex rollout JSONL token 用量白名单字段",
            privacy_note="跳过聊天正文、prompt、assistant 输出、cookie、token 和完整私密路径",
            next_step="使用 codex-probe ledger import-history --dry-run --source local-codex 预览",
        ),
        SourceDoctorResult(
            source_type="desktop_visible",
            available=False,
            confidence_ceiling="medium",
            permission_scope="需要用户显式授予系统可访问性权限",
            privacy_note="P0 不读取窗口正文，只保留接口预留和风险提示",
            next_step="暂不启用；等待 beta 用户授权验证",
        ),
    ]
    for result in results:
        upsert_source(
            conn,
            result.source_type,
            result.confidence_ceiling,
            result.permission_scope,
            enabled=False,
            metadata={
                "available": result.available,
                "privacy_note": result.privacy_note,
                "deep": deep,
                "local_codex": deep_local_payload(local_codex) if result.source_type == "local_codex_rollout" else None,
            },
        )
    conn.commit()
    return results


def source_doctor_payload(results: list[SourceDoctorResult], *, deep: bool = False) -> dict[str, object]:
    order = {"low": 1, "medium": 2, "high": 3, "exact": 4}
    available = [item for item in results if item.available]
    max_confidence = "low"
    if available:
        max_confidence = max(available, key=lambda item: order.get(item.confidence_ceiling, 0)).confidence_ceiling
    return {
        "ok": True,
        "max_confidence": max_confidence,
        "deep": deep,
        "privacy_boundary": "不读取浏览器 cookie、OpenAI token、钥匙串、系统凭据或聊天正文。",
        "sources": [
            {
                "source_type": item.source_type,
                "available": item.available,
                "confidence_ceiling": item.confidence_ceiling,
                "permission_scope": item.permission_scope,
                "privacy_note": item.privacy_note,
                "next_step": item.next_step,
            }
            for item in results
        ],
    }


def deep_local_payload(local_codex) -> dict[str, object] | None:
    if local_codex is None:
        return None
    return {
        "root_hash": local_codex.root_hash,
        "file_count": local_codex.file_count,
        "token_record_count": local_codex.token_record_count,
        "importable_record_count": local_codex.importable_record_count,
        "skipped_content_lines": local_codex.skipped_content_lines,
        "files": local_codex.files[:10],
    }
