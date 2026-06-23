"""Safe source discovery for the local ledger."""

from __future__ import annotations

from pathlib import Path

from .ledger_models import SourceDoctorResult
from .ledger_storage import upsert_source


def run_source_doctor(conn, root: Path | None = None) -> list[SourceDoctorResult]:
    root = root or Path.cwd()
    sample_dir = root / "examples" / "ledger-samples"
    results = [
        SourceDoctorResult(
            source_type="official_export",
            available=True,
            confidence_ceiling="exact",
            permission_scope="仅导入用户显式提供的官方 CSV/JSON 文件",
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
            metadata={"available": result.available, "privacy_note": result.privacy_note},
        )
    conn.commit()
    return results


def source_doctor_payload(results: list[SourceDoctorResult]) -> dict[str, object]:
    order = {"low": 1, "medium": 2, "high": 3, "exact": 4}
    available = [item for item in results if item.available]
    max_confidence = "low"
    if available:
        max_confidence = max(available, key=lambda item: order.get(item.confidence_ceiling, 0)).confidence_ceiling
    return {
        "ok": True,
        "max_confidence": max_confidence,
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
