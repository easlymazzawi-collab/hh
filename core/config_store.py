"""Lưu cấu hình platform trong data/auto_config.json."""

from __future__ import annotations

import json
import os
import threading
from copy import deepcopy
from typing import Any

DATA_DIR = "data"
AUTO_CONFIG_FILE = os.path.join(DATA_DIR, "auto_config.json")

_lock = threading.Lock()

DEFAULT_PLATFORM: dict[str, Any] = {
    "enabled": False,
    "publish_channels": True,
    "archive_index": True,
    "bot_delivery": True,
    "channel_first": True,
    "delivery_delay_sec": 1.0,
    "require_vip_for_archive": False,
    "admin_forum_id": None,
    "admin_zip_topic_id": None,
    "admin_contrib_topic_id": None,
    "admin_notify_group_id": None,
    "membership_channel_id": None,
    "membership_channel_username": "",
    "force_join_check_sec": 300,
    "force_join_message": (
        "Bạn cần tham gia kênh để dùng bot.\n"
        "Nhấn Join → bấm Đã join — kiểm tra."
    ),
    "backup_forum_id": None,
    "backup_to_telegram": True,
    "backup_interval_hours": 24,
    "backup_keep_days": 7,
    "share_event": {"enabled": False, "period_start": None, "period_end": None},
    "bots": [],
    "web_port": 8080,
    "web_token": "",
}


def _ensure_data_dir() -> None:
    os.makedirs(DATA_DIR, exist_ok=True)


def load_auto_config() -> dict[str, Any]:
    _ensure_data_dir()
    with _lock:
        if not os.path.isfile(AUTO_CONFIG_FILE):
            return {"platform": deepcopy(DEFAULT_PLATFORM)}
        with open(AUTO_CONFIG_FILE, encoding="utf-8") as f:
            return json.load(f)


def save_auto_config(cfg: dict[str, Any]) -> None:
    _ensure_data_dir()
    with _lock:
        with open(AUTO_CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
