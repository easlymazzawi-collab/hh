# UpBain Research Platform v2

Hệ thống research archive theo ngày — **viết lại từ đầu** theo `PROJECT_PROMPT.txt`.

## Chạy web admin

```bash
pip install -r requirements.txt
python run.py
```

Mở http://127.0.0.1:8080

## Cấu trúc

```
web/static/index.html   # UI admin (sidebar) — viết mới
web/server.py           # FastAPI /api/platform/*
research_platform/      # SQLite, archive index, VIP, ads, backup...
core/config_store.py    # auto_config.json
run.py                  # Entry point
```

## Kiến trúc 3 lớp

| Lớp | Config key | Mô tả |
|-----|------------|--------|
| Up kênh | `publish_channels` | Userbot forward RR |
| Archive index | `archive_index` | Ghi link + metadata SQLite |
| Bot delivery | `bot_delivery` | Bot copy/forward cho user |

## Ghi chú

- Repo nguồn (upbain, clender) chỉ dùng **tham chiếu pattern**, không copy nguyên xi.
- Userbot + aiogram delivery sẽ gắn ở phase tiếp theo.
