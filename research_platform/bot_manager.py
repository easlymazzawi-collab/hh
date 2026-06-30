"""Multi-bot manager — stub trạng thái cho web."""

from __future__ import annotations

from research_platform.config import list_bots_config, load_platform_config

_running: dict[str, bool] = {}


def bot_status() -> list[dict]:
    plat = load_platform_config()
    out = []
    for b in list_bots_config(plat):
        un = b.get("username") or f"bot_{b.get('queue_order', 0)}"
        out.append({
            "username": un,
            "enabled": b.get("enabled", True),
            "running": _running.get(un, False),
            "queue_order": b.get("queue_order", 0),
        })
    return out


async def restart_bot(username: str | None = None) -> dict:
    plat = load_platform_config()
    restarted = []
    for b in list_bots_config(plat):
        un = b.get("username") or ""
        if username and un != username:
            continue
        _running[un or f"bot_{b.get('queue_order',0)}"] = bool(b.get("enabled"))
        restarted.append(un or "(unnamed)")
    return {"restarted": restarted or ["all"]}
