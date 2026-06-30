"""Archive index — ngày + day_items (link + metadata)."""

from __future__ import annotations

from research_platform.dates import date_vn_str, topic_label_vn, today_vn
from research_platform.db import connect, init_db, json_dumps, json_loads, row_to_dict


def ensure_db() -> None:
    init_db()


def sync_bot_from_config(bot_cfg: dict) -> int:
    ensure_db()
    src_forum = bot_cfg.get("source_forum_id")
    src_topic = bot_cfg.get("source_topic_id")
    branch = bot_cfg.get("branch", "ads")
    with connect() as conn:
        row = conn.execute(
            "SELECT id FROM bots WHERE source_forum_id=? AND source_topic_id=? AND branch=?",
            (src_forum, src_topic, branch),
        ).fetchone()
        vals = (
            bot_cfg.get("username", ""),
            src_forum,
            src_topic,
            bot_cfg.get("catalog_topic_id"),
            branch,
            1 if bot_cfg.get("enabled", True) else 0,
            int(bot_cfg.get("queue_order") or 0),
        )
        if row:
            bot_id = row["id"]
            conn.execute(
                "UPDATE bots SET username=?,source_forum_id=?,source_topic_id=?,catalog_topic_id=?,branch=?,enabled=?,queue_order=? WHERE id=?",
                (*vals, bot_id),
            )
        else:
            cur = conn.execute(
                "INSERT INTO bots (username,source_forum_id,source_topic_id,catalog_topic_id,branch,enabled,queue_order) VALUES (?,?,?,?,?,?,?)",
                vals,
            )
            bot_id = cur.lastrowid
        return int(bot_id)


def sync_all_bots_from_config(plat: dict) -> None:
    for b in plat.get("bots") or []:
        if b.get("enabled", True):
            sync_bot_from_config(b)


def get_or_create_day(bot_id: int, d=None) -> dict:
    ensure_db()
    d = d or today_vn()
    dv, label = date_vn_str(d), topic_label_vn(d)
    with connect() as conn:
        row = conn.execute("SELECT * FROM days WHERE bot_id=? AND date_vn=?", (bot_id, dv)).fetchone()
        if row:
            return dict(row)
        cur = conn.execute(
            "INSERT INTO days (bot_id,date_vn,topic_label,status) VALUES (?,?,?,'draft')",
            (bot_id, dv, label),
        )
        return dict(conn.execute("SELECT * FROM days WHERE id=?", (cur.lastrowid,)).fetchone())


def add_day_item(
    day_id: int,
    seq: int,
    src_chat_id: int,
    src_msg_id: int,
    *,
    item_type: str = "content",
    ads_alias: str | None = None,
    album_msg_ids: list[int] | None = None,
) -> int:
    ensure_db()
    with connect() as conn:
        conn.execute(
            """INSERT OR REPLACE INTO day_items
               (day_id,seq,src_chat_id,src_msg_id,item_type,ads_alias,album_msg_ids,indexed)
               VALUES (?,?,?,?,?,?,?,1)""",
            (day_id, seq, src_chat_id, src_msg_id, item_type, ads_alias, json_dumps(album_msg_ids or [])),
        )
        row = conn.execute("SELECT id FROM day_items WHERE day_id=? AND seq=?", (day_id, seq)).fetchone()
        return int(row["id"])


def list_days(limit: int = 60) -> list[dict]:
    ensure_db()
    with connect() as conn:
        rows = conn.execute(
            """SELECT d.*, b.username AS bot_username
               FROM days d LEFT JOIN bots b ON b.id=d.bot_id
               ORDER BY d.date_vn DESC LIMIT ?""",
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]


def get_day_items(day_id: int, *, active_ads_only: bool = True) -> list[dict]:
    ensure_db()
    with connect() as conn:
        rows = conn.execute(
            "SELECT * FROM day_items WHERE day_id=? ORDER BY seq",
            (day_id,),
        ).fetchall()
        items = []
        for r in rows:
            item = dict(r)
            item["album_msg_ids"] = json_loads(item.get("album_msg_ids"))
            if active_ads_only and item.get("item_type") == "ads" and item.get("ads_alias"):
                ac = conn.execute(
                    "SELECT active FROM ads_contracts WHERE alias=?",
                    (item["ads_alias"],),
                ).fetchone()
                if ac and not ac["active"]:
                    continue
            items.append(item)
        return items


def publish_day(day_id: int) -> bool:
    ensure_db()
    with connect() as conn:
        cur = conn.execute(
            "UPDATE days SET status='published' WHERE id=? AND status IN ('draft','channel_done','indexed')",
            (day_id,),
        )
        return cur.rowcount > 0


def close_day(day_id: int) -> bool:
    ensure_db()
    with connect() as conn:
        cur = conn.execute("UPDATE days SET status='closed' WHERE id=?", (day_id,))
        return cur.rowcount > 0


def list_users(limit: int = 200) -> list[dict]:
    ensure_db()
    with connect() as conn:
        rows = conn.execute(
            "SELECT * FROM users ORDER BY joined_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]


def export_archive_json() -> list[dict]:
    ensure_db()
    out = []
    for day in list_days(limit=500):
        out.append({**day, "items": get_day_items(day["id"], active_ads_only=False)})
    return out
