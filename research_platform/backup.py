"""Backup ZIP — pattern clender, viết lại cho platform."""

from __future__ import annotations

import hashlib
import io
import json
import os
import sqlite3
import threading
import zipfile
from datetime import datetime, timedelta

from core.config_store import AUTO_CONFIG_FILE, DATA_DIR
from research_platform.archive_index import export_archive_json
from research_platform.config import list_bots_config, load_platform_config, mask_bots_for_api
from research_platform.db import DB_PATH, init_db

BACKUP_DIR = os.path.join(DATA_DIR, "backups")
_scheduler_thread: threading.Thread | None = None
_scheduler_stop = threading.Event()


def _safe_copy_db(src: str, dst: str) -> bool:
    if not os.path.isfile(src):
        return False
    try:
        s = sqlite3.connect(src)
        d = sqlite3.connect(dst)
        with d:
            s.backup(d)
        s.close()
        d.close()
        return True
    except Exception:
        return False


def _mask_config_for_export() -> dict:
    cfg = {}
    if os.path.isfile(AUTO_CONFIG_FILE):
        with open(AUTO_CONFIG_FILE, encoding="utf-8") as f:
            cfg = json.load(f)
    plat = cfg.get("platform") or {}
    for b in plat.get("bots") or []:
        if b.get("token"):
            b["token"] = "***"
    return cfg


def build_backup_zip() -> tuple[bytes, str]:
    init_db()
    os.makedirs(BACKUP_DIR, exist_ok=True)
    ts = datetime.now().strftime("%Y-%m-%d_%H%M")
    filename = f"backup_{ts}.zip"
    tmp_db = os.path.join(BACKUP_DIR, "_tmp_platform.db")
    has_db = _safe_copy_db(DB_PATH, tmp_db)
    plat = load_platform_config()
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        if has_db:
            z.write(tmp_db, "platform.db")
        z.writestr("auto_config.json", json.dumps(_mask_config_for_export(), ensure_ascii=False, indent=2))
        z.writestr("archive_index.json", json.dumps(export_archive_json(), ensure_ascii=False, indent=2))
        z.writestr("bots.json", json.dumps(mask_bots_for_api(list_bots_config(plat)), ensure_ascii=False, indent=2))
        manifest = {
            "version": "2.0",
            "created_at": datetime.now().isoformat(),
            "checksum": "",
        }
        z.writestr("MANIFEST.json", json.dumps(manifest, ensure_ascii=False, indent=2))
    if os.path.isfile(tmp_db):
        os.remove(tmp_db)
    data = buf.getvalue()
    manifest["checksum"] = hashlib.sha256(data).hexdigest()
    return data, filename


def _rotate_old_backups(keep_days: int) -> None:
    if not os.path.isdir(BACKUP_DIR):
        return
    cutoff = datetime.now() - timedelta(days=keep_days)
    for name in os.listdir(BACKUP_DIR):
        if not name.endswith(".zip"):
            continue
        path = os.path.join(BACKUP_DIR, name)
        if datetime.fromtimestamp(os.path.getmtime(path)) < cutoff:
            try:
                os.remove(path)
            except OSError:
                pass


def get_backup_status() -> dict:
    plat = load_platform_config()
    init_db()
    files = []
    if os.path.isdir(BACKUP_DIR):
        files = sorted(
            [f for f in os.listdir(BACKUP_DIR) if f.endswith(".zip")],
            reverse=True,
        )
    skip = []
    bots = list_bots_config(plat)
    if not any(b.get("token") or b.get("has_token") for b in bots):
        skip.append("Thiếu bot token")
    if not plat.get("backup_forum_id") and not plat.get("admin_forum_id"):
        skip.append("Thiếu backup_forum_id hoặc admin_forum_id")
    return {
        "scheduler_on": _scheduler_thread is not None and _scheduler_thread.is_alive(),
        "interval_hours": plat.get("backup_interval_hours", 24),
        "keep_days": plat.get("backup_keep_days", 7),
        "backup_dir": BACKUP_DIR,
        "telegram_enabled": bool(plat.get("backup_to_telegram")),
        "telegram_ready": len(skip) == 0,
        "local_file_count": len(files),
        "last_backup_file": files[0] if files else None,
        "last_backup_at": None,
        "db_exists": os.path.isfile(DB_PATH),
        "skip_reasons": skip,
    }


def run_backup_now(*, send_telegram: bool | None = None) -> dict:
    plat = load_platform_config()
    data, filename = build_backup_zip()
    path = os.path.join(BACKUP_DIR, filename)
    with open(path, "wb") as f:
        f.write(data)
    _rotate_old_backups(int(plat.get("backup_keep_days") or 7))
    sent = False
    if send_telegram if send_telegram is not None else plat.get("backup_to_telegram"):
        # Upload Telegram gắn khi bot delivery chạy live
        sent = False
    return {"ok": True, "file": filename, "path": path, "sent_telegram": sent}


def start_backup_scheduler() -> None:
    global _scheduler_thread
    if _scheduler_thread and _scheduler_thread.is_alive():
        return

    def _loop() -> None:
        while not _scheduler_stop.is_set():
            plat = load_platform_config()
            hours = max(1, int(plat.get("backup_interval_hours") or 24))
            if _scheduler_stop.wait(hours * 3600):
                break
            try:
                run_backup_now()
            except Exception:
                pass

    _scheduler_stop.clear()
    _scheduler_thread = threading.Thread(target=_loop, daemon=True, name="backup-scheduler")
    _scheduler_thread.start()
