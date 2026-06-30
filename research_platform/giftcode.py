"""Giftcode tạo và redeem."""

from __future__ import annotations

import secrets
import string

from research_platform.db import connect, init_db


def list_gift_codes() -> list[dict]:
    init_db()
    with connect() as conn:
        return [dict(r) for r in conn.execute("SELECT * FROM gift_codes ORDER BY created_at DESC").fetchall()]


def create_gift_codes(
    *,
    plan_id: int,
    count: int = 1,
    prefix: str = "VIP",
    max_uses: int = 1,
    expires_at: str | None = None,
    custom_code: str | None = None,
) -> list[str]:
    init_db()
    codes = []
    alphabet = string.ascii_uppercase + string.digits
    with connect() as conn:
        for _ in range(max(1, count)):
            code = custom_code or f"{prefix}{secrets.token_hex(4).upper()}"
            conn.execute(
                "INSERT OR REPLACE INTO gift_codes (code,plan_id,max_uses,expires_at) VALUES (?,?,?,?)",
                (code, plan_id, max_uses, expires_at),
            )
            codes.append(code)
    return codes
