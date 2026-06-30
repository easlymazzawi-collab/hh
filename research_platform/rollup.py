"""Rollup 30 ngày — catalog text."""

from __future__ import annotations

from research_platform.db import connect, init_db, json_dumps


def list_rollups() -> list[dict]:
    init_db()
    with connect() as conn:
        return [dict(r) for r in conn.execute("SELECT * FROM rollup_indexes ORDER BY month_label DESC").fetchall()]


async def run_rollup_all() -> list[dict]:
    """Tạo rollup placeholder — logic đầy đủ gắn khi có dữ liệu archive."""
    init_db()
    return []
