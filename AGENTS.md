# AGENTS.md

## Cursor Cloud specific instructions

This repo is the **UpBain Research Platform v2** — a single Python (FastAPI + Uvicorn) web admin
backed by SQLite. The Telegram userbot/delivery bots are not implemented yet (`bot_manager.py` is a
stub), so the web admin is the only runnable service. Setup is just `pip install -r requirements.txt`
(handled by the startup update script) followed by running the server.

### Running the server
- Run with `python3 run.py` (NOT `python` — only `python3` exists on this image; `run.bat` is Windows-only).
- Serves on `0.0.0.0:8080` (port is `platform.web_port` in `data/auto_config.json`, default 8080). Open `http://127.0.0.1:8080`.
- Auth is open by default; if `platform.web_token` is set, send `Authorization: Bearer <token>`.

### Data / state
- SQLite DB (`data/platform.db`) and `data/auto_config.json` are auto-created on first startup and seeded
  with 4 default VIP plans. The whole `data/` dir is gitignored — delete it to reset to a clean state.

### Lint / test / build
- There is no test suite, no linter config, and no build step. As a sanity check you can byte-compile
  with `python3 -m compileall -q core research_platform web run.py`.

### Non-obvious gotchas
- `tgcrypto` (a `requirements.txt` dependency) compiles a C extension and needs the `python3-dev` system
  headers; these are pre-installed in the VM image, so `pip install` succeeds without extra steps.
- `days`/`day_items` rows are normally populated by the (not-yet-implemented) userbot archive hook, so the
  `/api/platform/days/*` endpoints have no data until you seed via `research_platform.archive_index`
  (`get_or_create_day` + `add_day_item`). The userbot (Pyrogram) and delivery bots (aiogram) need real
  Telegram credentials/tokens and cannot be exercised in this environment.
