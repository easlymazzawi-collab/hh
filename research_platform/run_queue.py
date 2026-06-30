"""Queue tuần tự 10 bot."""

from __future__ import annotations

from research_platform.config import list_bots_config, load_platform_config


def queue_status() -> dict:
    bots = [b for b in list_bots_config() if b.get("enabled", True)]
    bots.sort(key=lambda x: int(x.get("queue_order") or 0))
    return {
        "total": len(bots),
        "max": 10,
        "order": [b.get("username") or f"#{b.get('queue_order',0)}" for b in bots],
        "current": None,
    }
