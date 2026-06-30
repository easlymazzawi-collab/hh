"""Cấu hình platform.* trong auto_config.json."""

from __future__ import annotations

import threading
from copy import deepcopy
from typing import Any

from core.config_store import DEFAULT_PLATFORM, load_auto_config, save_auto_config

_lock = threading.Lock()

_DEFAULT_BOT: dict[str, Any] = {
    "token": "",
    "username": "",
    "source_forum_id": None,
    "source_topic_id": None,
    "catalog_topic_id": None,
    "branch": "ads",
    "enabled": True,
    "queue_order": 0,
}


def load_platform_config() -> dict[str, Any]:
    with _lock:
        cfg = load_auto_config()
        plat = cfg.setdefault("platform", deepcopy(DEFAULT_PLATFORM))
        for k, v in DEFAULT_PLATFORM.items():
            if k not in plat:
                plat[k] = deepcopy(v) if isinstance(v, (dict, list)) else v
        plat.setdefault("bots", [])
        return plat


def save_platform_config(plat: dict[str, Any]) -> None:
    with _lock:
        cfg = load_auto_config()
        cfg["platform"] = plat
        save_auto_config(cfg)


def list_bots_config(plat: dict | None = None) -> list[dict]:
    plat = plat or load_platform_config()
    bots = plat.get("bots") or []
    return [{**_DEFAULT_BOT, **b} for b in bots]


def mask_bots_for_api(bots: list[dict]) -> list[dict]:
    out = []
    for b in bots:
        m = {**_DEFAULT_BOT, **b}
        if m.get("token"):
            m["has_token"] = True
            m["token"] = ""
        else:
            m["has_token"] = False
        out.append(m)
    return out
