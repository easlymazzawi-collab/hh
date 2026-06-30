"""VIP plans và grant."""

from __future__ import annotations

from datetime import timedelta

from research_platform.dates import now_vn
from research_platform.db import connect, init_db, row_to_dict


def list_vip_plans(*, enabled_only: bool = True) -> list[dict]:
    init_db()
    with connect() as conn:
        q = "SELECT * FROM vip_plans"
        if enabled_only:
            q += " WHERE enabled=1"
        q += " ORDER BY sort_order, id"
        return [dict(r) for r in conn.execute(q).fetchall()]


def upsert_vip_plan(plan_id: int | None, **fields) -> dict:
    init_db()
    with connect() as conn:
        if plan_id:
            cols = ", ".join(f"{k}=?" for k in fields)
            conn.execute(f"UPDATE vip_plans SET {cols} WHERE id=?", (*fields.values(), plan_id))
            row = conn.execute("SELECT * FROM vip_plans WHERE id=?", (plan_id,)).fetchone()
        else:
            keys = list(fields.keys())
            cur = conn.execute(
                f"INSERT INTO vip_plans ({','.join(keys)}) VALUES ({','.join('?'*len(keys))})",
                list(fields.values()),
            )
            row = conn.execute("SELECT * FROM vip_plans WHERE id=?", (cur.lastrowid,)).fetchone()
        return dict(row)


def grant_vip(user_id: int, plan_id: int, *, source: str = "admin") -> dict:
    init_db()
    with connect() as conn:
        plan = conn.execute("SELECT * FROM vip_plans WHERE id=?", (plan_id,)).fetchone()
        if not plan:
            raise ValueError("Plan không tồn tại")
        conn.execute(
            "INSERT OR IGNORE INTO users (telegram_id) VALUES (?)",
            (user_id,),
        )
        until = None
        if plan["duration_days"]:
            until = (now_vn() + timedelta(days=plan["duration_days"])).isoformat()
        conn.execute(
            "UPDATE users SET vip_until=? WHERE telegram_id=?",
            (until, user_id),
        )
        return {"ok": True, "user_id": user_id, "vip_until": until, "source": source}


def user_is_vip(user_id: int) -> bool:
    init_db()
    with connect() as conn:
        row = conn.execute("SELECT vip_until FROM users WHERE telegram_id=?", (user_id,)).fetchone()
        if not row:
            return False
        until = row["vip_until"]
        if until is None:
            return True  # lifetime
        if until == "":
            return False
        from datetime import datetime
        try:
            expires = datetime.fromisoformat(until)
        except ValueError:
            return False
        now = now_vn()
        if expires.tzinfo is None:
            now = now.replace(tzinfo=None)
        return expires > now
