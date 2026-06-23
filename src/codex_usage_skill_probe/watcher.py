"""Small local watcher process for Codex ledger snapshots."""

from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .local_history import default_codex_root, import_local_history


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def watch_dir(db_path: Path) -> Path:
    return db_path.parent / "watch"


def watch_paths(db_path: Path) -> dict[str, Path]:
    base = watch_dir(db_path)
    return {
        "dir": base,
        "state": base / "status.json",
        "lock": base / "watch.lock",
        "stop": base / "stop.flag",
        "log": base / "watch.log",
    }


def read_state(db_path: Path) -> dict[str, Any]:
    paths = watch_paths(db_path)
    if not paths["state"].exists():
        return {"status": "stopped", "last_message": "watch 尚未启动", "pid": None}
    try:
        state = json.loads(paths["state"].read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"status": "error", "last_error": "watch status file is broken", "pid": None}
    pid = state.get("pid")
    if state.get("status") == "running" and pid and not is_pid_alive(int(pid)):
        state["status"] = "error"
        state["last_error"] = "watcher 进程已退出，但状态文件仍显示 running"
        state["stopped_at"] = now_iso()
        write_state(db_path, state)
    return state


def write_state(db_path: Path, state: dict[str, Any]) -> None:
    paths = watch_paths(db_path)
    paths["dir"].mkdir(parents=True, exist_ok=True)
    state.setdefault("log_path", str(paths["log"]))
    paths["state"].write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def append_log(db_path: Path, message: str) -> None:
    paths = watch_paths(db_path)
    paths["dir"].mkdir(parents=True, exist_ok=True)
    with paths["log"].open("a", encoding="utf-8") as handle:
        handle.write(f"{now_iso()} {message}\n")


def is_pid_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def collect_once(store, root: Path | None = None, *, limit_files: int | None = None) -> dict[str, object]:
    return import_local_history(store.conn, root or default_codex_root(), dry_run=False, limit_files=limit_files)


def start_watcher(db_path: Path, interval_seconds: int, root: Path | None = None, limit_files: int | None = None) -> dict[str, Any]:
    current = read_state(db_path)
    if current.get("status") == "running" and current.get("pid") and is_pid_alive(int(current["pid"])):
        current["already_running"] = True
        return current
    paths = watch_paths(db_path)
    paths["dir"].mkdir(parents=True, exist_ok=True)
    if paths["stop"].exists():
        paths["stop"].unlink()
    cmd = [
        sys.executable,
        "-m",
        "codex_usage_skill_probe",
        "--db",
        str(db_path),
        "--json",
        "watch",
        "_run",
        "--interval-seconds",
        str(interval_seconds),
    ]
    if root:
        cmd.extend(["--root", str(root)])
    if limit_files:
        cmd.extend(["--limit-files", str(limit_files)])
    with paths["log"].open("a", encoding="utf-8") as log_handle:
        process = subprocess.Popen(
            cmd,
            stdout=log_handle,
            stderr=log_handle,
            stdin=subprocess.DEVNULL,
            start_new_session=True,
        )
    state = {
        "status": "running",
        "pid": process.pid,
        "started_at": now_iso(),
        "stopped_at": None,
        "interval_seconds": interval_seconds,
        "collection_count": 0,
        "last_collected_at": None,
        "last_error": "",
        "root_hash": "",
        "lock_path": str(paths["lock"]),
        "log_path": str(paths["log"]),
        "last_message": "watcher 后台进程已启动",
    }
    write_state(db_path, state)
    append_log(db_path, f"started pid={process.pid} interval={interval_seconds}")
    return state


def stop_watcher(db_path: Path, timeout_seconds: float = 5.0) -> dict[str, Any]:
    paths = watch_paths(db_path)
    state = read_state(db_path)
    paths["dir"].mkdir(parents=True, exist_ok=True)
    paths["stop"].write_text(now_iso(), encoding="utf-8")
    pid = state.get("pid")
    if pid and is_pid_alive(int(pid)):
        deadline = time.time() + timeout_seconds
        while time.time() < deadline and is_pid_alive(int(pid)):
            time.sleep(0.1)
        if is_pid_alive(int(pid)):
            os.kill(int(pid), signal.SIGTERM)
    state.update(
        {
            "status": "stopped",
            "stopped_at": now_iso(),
            "last_message": "watcher 已停止",
        }
    )
    write_state(db_path, state)
    append_log(db_path, "stopped")
    return state


def watcher_logs(db_path: Path, limit: int = 80) -> dict[str, Any]:
    path = watch_paths(db_path)["log"]
    if not path.exists():
        return {"ok": True, "log_path": str(path), "lines": []}
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()[-limit:]
    return {"ok": True, "log_path": str(path), "lines": lines}


def delete_watcher_files(db_path: Path) -> int:
    stop_watcher(db_path, timeout_seconds=1.0)
    deleted = 0
    for path in [watch_paths(db_path)["state"], watch_paths(db_path)["lock"], watch_paths(db_path)["stop"], watch_paths(db_path)["log"]]:
        if path.exists():
            path.unlink()
            deleted += 1
    return deleted


def run_forever(store, interval_seconds: int, root: Path | None = None, limit_files: int | None = None) -> None:
    db_path = store.db_path
    paths = watch_paths(db_path)
    paths["dir"].mkdir(parents=True, exist_ok=True)
    paths["lock"].write_text(str(os.getpid()), encoding="utf-8")
    state = read_state(db_path)
    state.update({"status": "running", "pid": os.getpid(), "started_at": state.get("started_at") or now_iso()})
    write_state(db_path, state)
    append_log(db_path, "runner entered loop")
    try:
        while True:
            if paths["stop"].exists():
                break
            try:
                result = collect_once(store, root=root, limit_files=limit_files)
                state = read_state(db_path)
                state.update(
                    {
                        "status": "running",
                        "pid": os.getpid(),
                        "collection_count": int(state.get("collection_count") or 0) + 1,
                        "last_collected_at": now_iso(),
                        "last_error": "",
                        "root_hash": result.get("root_hash", ""),
                        "last_message": f"采集完成，新增 {result.get('imported_snapshots', 0)} 条快照",
                    }
                )
                write_state(db_path, state)
                append_log(db_path, state["last_message"])
            except Exception as exc:  # pragma: no cover - daemon resilience path
                state = read_state(db_path)
                state.update({"status": "running", "last_error": str(exc), "last_message": "采集失败，等待下一轮"})
                write_state(db_path, state)
                append_log(db_path, f"error {exc}")
            deadline = time.time() + max(1, interval_seconds)
            while time.time() < deadline:
                if paths["stop"].exists():
                    raise KeyboardInterrupt
                time.sleep(0.2)
    except KeyboardInterrupt:
        pass
    finally:
        if paths["lock"].exists():
            paths["lock"].unlink()
        state = read_state(db_path)
        state.update({"status": "stopped", "stopped_at": now_iso(), "pid": os.getpid(), "last_message": "watcher runner exited"})
        write_state(db_path, state)
        append_log(db_path, "runner exited")
