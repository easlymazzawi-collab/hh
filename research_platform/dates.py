"""Ngày theo múi giờ Việt Nam."""

from __future__ import annotations

from datetime import date, datetime
from zoneinfo import ZoneInfo

VN = ZoneInfo("Asia/Ho_Chi_Minh")


def now_vn() -> datetime:
    return datetime.now(VN)


def today_vn() -> date:
    return now_vn().date()


def date_vn_str(d: date | None = None) -> str:
    d = d or today_vn()
    return d.strftime("%Y-%m-%d")


def topic_label_vn(d: date | None = None) -> str:
    d = d or today_vn()
    return d.strftime("%d-%m-%Y")


def parse_day_input(text: str) -> date | None:
    text = (text or "").strip()
    for fmt in ("%d-%m-%Y", "%d/%m/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    return None
