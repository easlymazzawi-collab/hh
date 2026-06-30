"""Share ref + leaderboard."""

from __future__ import annotations

from research_platform.db import connect, init_db


def leaderboard(limit: int = 10) -> list[dict]:
    init_db()
    with connect() as conn:
        rows = conn.execute(
            """SELECT ref_code, day_id, creator_user_id, click_count
               FROM share_refs ORDER BY click_count DESC LIMIT ?""",
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]
