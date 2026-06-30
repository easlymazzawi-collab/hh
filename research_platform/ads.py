"""Ads alias contracts."""

from __future__ import annotations

from research_platform.db import connect, init_db, json_dumps, json_loads


def list_ads_contracts() -> list[dict]:
    init_db()
    with connect() as conn:
        out = []
        for r in conn.execute("SELECT * FROM ads_contracts ORDER BY alias").fetchall():
            d = dict(r)
            d["src_msg_ids"] = json_loads(d.get("src_msg_ids"))
            out.append(d)
        return out


def upsert_ads_contract(
    alias: str,
    *,
    src_msg_ids: list[int] | None = None,
    src_chat_id: int | None = None,
    active: bool = True,
) -> dict:
    init_db()
    with connect() as conn:
        conn.execute(
            """INSERT INTO ads_contracts (alias,src_msg_ids,src_chat_id,active,updated_at)
               VALUES (?,?,?,?,datetime('now'))
               ON CONFLICT(alias) DO UPDATE SET
                 src_msg_ids=excluded.src_msg_ids,
                 src_chat_id=excluded.src_chat_id,
                 active=excluded.active,
                 updated_at=datetime('now')""",
            (alias, json_dumps(src_msg_ids or []), src_chat_id, 1 if active else 0),
        )
        row = conn.execute("SELECT * FROM ads_contracts WHERE alias=?", (alias,)).fetchone()
        d = dict(row)
        d["src_msg_ids"] = json_loads(d.get("src_msg_ids"))
        return d


def terminate_ads_contract(alias: str) -> bool:
    init_db()
    with connect() as conn:
        cur = conn.execute(
            "UPDATE ads_contracts SET active=0, terminated_at=datetime('now') WHERE alias=?",
            (alias,),
        )
        return cur.rowcount > 0


def recheck_all_ads_aliases() -> dict:
    """Placeholder — recheck sẽ gắn với userbot khi chạy live."""
    contracts = list_ads_contracts()
    return {"ok": True, "checked": len(contracts), "updated": 0}
