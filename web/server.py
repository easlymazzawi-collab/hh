"""FastAPI — Research Platform web admin (viết lại từ đầu)."""

from __future__ import annotations

import os
from typing import Any

from fastapi import Body, Depends, FastAPI, Header, HTTPException
from fastapi.responses import HTMLResponse, Response
from pydantic import BaseModel, Field

from core.config_store import load_auto_config, save_auto_config
from research_platform.db import init_db

WEB_DIR = os.path.join(os.path.dirname(__file__), "static")
app = FastAPI(title="UpBain Research Platform", version="2.0")


def _web_token() -> str:
    cfg = load_auto_config()
    return (cfg.get("platform") or {}).get("web_token") or ""


def _auth(
    authorization: str | None = Header(default=None),
    x_token: str | None = Header(default=None),
) -> bool:
    token = _web_token()
    if not token:
        return True
    got = (authorization or "").replace("Bearer ", "").strip() or (x_token or "").strip()
    if got != token:
        raise HTTPException(401, "Unauthorized")
    return True


class PlatformPatch(BaseModel):
    enabled: bool | None = None
    publish_channels: bool | None = None
    archive_index: bool | None = None
    bot_delivery: bool | None = None
    channel_first: bool | None = None
    delivery_delay_sec: float | None = None
    require_vip_for_archive: bool | None = None
    admin_forum_id: int | None = None
    admin_zip_topic_id: int | None = None
    admin_contrib_topic_id: int | None = None
    admin_notify_group_id: int | None = None
    membership_channel_id: int | None = None
    membership_channel_username: str | None = None
    force_join_check_sec: int | None = None
    force_join_message: str | None = None
    backup_forum_id: int | None = None
    backup_to_telegram: bool | None = None
    backup_interval_hours: int | None = None
    backup_keep_days: int | None = None
    share_event: dict | None = None
    bots: list[dict] | None = None
    web_token: str | None = None


class VipPlanIn(BaseModel):
    plan_type: str | None = None
    name: str | None = None
    stars_price: int | None = None
    duration_days: int | None = None
    enabled: int | None = None
    sort_order: int | None = None


class VipGrantIn(BaseModel):
    user_id: int
    plan_id: int


class GiftCodeIn(BaseModel):
    plan_id: int = 1
    count: int = 5
    prefix: str = "VIP"
    max_uses: int = 1
    expires_at: str | None = None
    code: str | None = None


class AdsContractIn(BaseModel):
    alias: str
    src_msg_ids: list[int] = Field(default_factory=list)
    src_chat_id: int | None = None
    active: bool = True


def _mask_platform(plat: dict) -> dict:
    from research_platform.config import list_bots_config, mask_bots_for_api

    out = dict(plat)
    out["bots"] = mask_bots_for_api(list_bots_config(out))
    if out.get("web_token"):
        out["has_web_token"] = True
        out["web_token"] = ""
    return out


@app.on_event("startup")
def _startup() -> None:
    init_db()


@app.get("/", response_class=HTMLResponse)
async def index_page():
    path = os.path.join(WEB_DIR, "index.html")
    with open(path, encoding="utf-8") as f:
        return HTMLResponse(f.read())


@app.get("/api/platform")
async def get_platform(_=Depends(_auth)):
    from research_platform.archive_index import list_days, sync_all_bots_from_config
    from research_platform.bot_manager import bot_status
    from research_platform.config import load_platform_config
    from research_platform.run_queue import queue_status

    plat = load_platform_config()
    days = []
    if plat.get("enabled"):
        try:
            sync_all_bots_from_config(plat)
            days = list_days(limit=60)
        except Exception:
            pass
    return {
        "platform": _mask_platform(plat),
        "days": days,
        "bot_status": bot_status(),
        "queue": queue_status(),
    }


@app.patch("/api/platform")
async def patch_platform(body: PlatformPatch, _=Depends(_auth)):
    from research_platform.archive_index import sync_all_bots_from_config
    from research_platform.config import load_platform_config, save_platform_config

    plat = load_platform_config()
    data = body.model_dump(exclude_unset=True)
    bots_patch = data.pop("bots", None)
    for k, v in data.items():
        plat[k] = v
    if bots_patch is not None:
        merged = []
        existing = plat.get("bots") or []
        for i, bp in enumerate(bots_patch[:10]):
            cur = dict(existing[i]) if i < len(existing) else {}
            token = bp.pop("token", None) if isinstance(bp, dict) else None
            if isinstance(bp, dict):
                cur.update(bp)
            if token:
                cur["token"] = token
            merged.append(cur)
        plat["bots"] = merged
    save_platform_config(plat)
    if plat.get("enabled"):
        sync_all_bots_from_config(plat)
    return {"ok": True, "platform": _mask_platform(plat)}


@app.post("/api/platform/bots/restart")
async def platform_restart_bots(username: str | None = None, _=Depends(_auth)):
    from research_platform.bot_manager import restart_bot

    return {"ok": True, **await restart_bot(username)}


@app.get("/api/platform/vip/plans")
async def platform_vip_plans(_=Depends(_auth)):
    from research_platform.vip import list_vip_plans
    return {"plans": list_vip_plans(enabled_only=False)}


@app.post("/api/platform/vip/plans")
async def platform_vip_plan_create(body: VipPlanIn, _=Depends(_auth)):
    from research_platform.vip import upsert_vip_plan
    return upsert_vip_plan(None, **body.model_dump(exclude_unset=True))


@app.patch("/api/platform/vip/plans/{plan_id}")
async def platform_vip_plan_patch(plan_id: int, body: VipPlanIn, _=Depends(_auth)):
    from research_platform.vip import upsert_vip_plan
    return upsert_vip_plan(plan_id, **body.model_dump(exclude_unset=True))


@app.post("/api/platform/vip/grant")
async def platform_vip_grant(body: VipGrantIn, _=Depends(_auth)):
    from research_platform.vip import grant_vip
    return grant_vip(body.user_id, body.plan_id, source="admin")


@app.get("/api/platform/giftcodes")
async def platform_giftcodes(_=Depends(_auth)):
    from research_platform.giftcode import list_gift_codes
    return {"codes": list_gift_codes()}


@app.post("/api/platform/giftcodes")
async def platform_giftcodes_create(body: GiftCodeIn, _=Depends(_auth)):
    from research_platform.giftcode import create_gift_codes
    codes = create_gift_codes(**body.model_dump())
    return {"ok": True, "codes": codes}


@app.get("/api/platform/ads")
async def platform_ads_list(_=Depends(_auth)):
    from research_platform.ads import list_ads_contracts
    return {"contracts": list_ads_contracts()}


@app.post("/api/platform/ads")
async def platform_ads_upsert(body: AdsContractIn, _=Depends(_auth)):
    from research_platform.ads import upsert_ads_contract
    return upsert_ads_contract(body.alias, src_msg_ids=body.src_msg_ids, src_chat_id=body.src_chat_id, active=body.active)


@app.post("/api/platform/ads/{alias}/terminate")
async def platform_ads_terminate(alias: str, _=Depends(_auth)):
    from research_platform.ads import terminate_ads_contract
    if not terminate_ads_contract(alias):
        raise HTTPException(404, "Alias không tồn tại")
    return {"ok": True}


@app.post("/api/platform/ads/recheck")
async def platform_ads_recheck(_=Depends(_auth)):
    from research_platform.ads import recheck_all_ads_aliases
    return recheck_all_ads_aliases()


@app.get("/api/platform/users")
async def platform_users(_=Depends(_auth)):
    from research_platform.archive_index import list_users
    from research_platform.vip import user_is_vip
    users = list_users()
    for u in users:
        u["is_vip"] = user_is_vip(u["telegram_id"])
    return {"users": users}


@app.get("/api/platform/share/leaderboard")
async def platform_share_lb(_=Depends(_auth)):
    from research_platform.share import leaderboard
    return {"leaderboard": leaderboard()}


@app.get("/api/platform/contributions")
async def platform_contributions(_=Depends(_auth)):
    from research_platform.catalog import list_pending_contributions
    return {"items": list_pending_contributions()}


@app.post("/api/platform/contributions/{cid}/approve")
async def platform_contrib_approve(cid: int, _=Depends(_auth)):
    from research_platform.catalog import approve_contribution
    r = approve_contribution(cid)
    if not r:
        raise HTTPException(404, "Not found")
    return r


@app.post("/api/platform/contributions/{cid}/reject")
async def platform_contrib_reject(cid: int, _=Depends(_auth)):
    from research_platform.catalog import reject_contribution
    if not reject_contribution(cid):
        raise HTTPException(404, "Not found")
    return {"ok": True}


@app.get("/api/platform/rollup")
async def platform_rollup_list(_=Depends(_auth)):
    from research_platform.rollup import list_rollups
    return {"rollups": list_rollups()}


@app.post("/api/platform/rollup")
async def platform_rollup_run(_=Depends(_auth)):
    from research_platform.rollup import run_rollup_all
    results = await run_rollup_all()
    return {"ok": True, "results": results}


@app.post("/api/platform/days/{day_id}/publish")
async def platform_publish_day(day_id: int, _=Depends(_auth)):
    from research_platform.archive_index import publish_day
    if not publish_day(day_id):
        raise HTTPException(404, "Không publish được")
    return {"ok": True}


@app.post("/api/platform/days/{day_id}/close")
async def platform_close_day(day_id: int, _=Depends(_auth)):
    from research_platform.archive_index import close_day
    if not close_day(day_id):
        raise HTTPException(404, "Không đóng được")
    return {"ok": True}


@app.get("/api/platform/days/{day_id}/items")
async def platform_day_items(day_id: int, _=Depends(_auth)):
    from research_platform.archive_index import get_day_items
    return {"items": get_day_items(day_id, active_ads_only=False)}


@app.get("/api/platform/backup")
async def platform_backup_status(_=Depends(_auth)):
    from research_platform.backup import get_backup_status
    return {"ok": True, "status": get_backup_status()}


@app.post("/api/platform/backup")
async def platform_backup_run(body: dict | None = Body(default=None), _=Depends(_auth)):
    from research_platform.backup import run_backup_now
    send_tg = (body or {}).get("telegram") if body else None
    result = run_backup_now(send_telegram=send_tg)
    if not result.get("ok"):
        raise HTTPException(500, "Backup thất bại")
    return result


@app.get("/api/platform/backup/download")
async def platform_backup_download(_=Depends(_auth)):
    from research_platform.backup import build_backup_zip
    data, filename = build_backup_zip()
    return Response(
        content=data,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


def run_server() -> None:
    import uvicorn
    cfg = load_auto_config()
    port = int((cfg.get("platform") or {}).get("web_port") or 8080)
    uvicorn.run(app, host="0.0.0.0", port=port)


if __name__ == "__main__":
    run_server()
