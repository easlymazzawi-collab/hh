"""Contribution queue — duyệt tên bộ."""

from __future__ import annotations

from research_platform.db import connect, init_db


def list_pending_contributions() -> list[dict]:
    init_db()
    with connect() as conn:
        rows = conn.execute(
            "SELECT * FROM contribution_queue WHERE status='pending' ORDER BY created_at",
        ).fetchall()
        return [dict(r) for r in rows]


def approve_contribution(cid: int) -> dict | None:
    init_db()
    with connect() as conn:
        row = conn.execute("SELECT * FROM contribution_queue WHERE id=?", (cid,)).fetchone()
        if not row:
            return None
        conn.execute("UPDATE contribution_queue SET status='approved' WHERE id=?", (cid,))
        return dict(row)


def reject_contribution(cid: int) -> bool:
    init_db()
    with connect() as conn:
        cur = conn.execute("UPDATE contribution_queue SET status='rejected' WHERE id=?", (cid,))
        return cur.rowcount > 0
