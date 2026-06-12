# AGENTS.md — axe-tg-bots

## Project overview

FastAPI service that dynamically launches and manages multiple Telegram bots (aiogram 3.x). Each bot's behavior (prompts, buttons, tools) is generated from Google Sheets data. LLM responses use an OpenAI-compatible proxy (VSEGPT). Bot configs are stored in MySQL.

## Entrypoints

| Purpose | File | Command |
|---|---|---|
| API server | `main.py` | `uvicorn main:app --host 0.0.0.0 --port 81` |
| Docker | `Dockerfile` + `docker-compose.yaml` | `docker compose up -d` (host `8181` → container `81`) |
| Standalone single bot | `bot.py` | `python bot.py` (hardcoded token) |

FastAPI lifecycle in `main.py` auto-loads all active bots from DB on startup and stops them on shutdown.

## Environment (`.env`)

```env
openai_key=<api-key>
openai_proxy=https://api.vsegpt.ru/v1
db_user=<mysql-user>
db_password=<mysql-password>
db_host=<mysql-host>
db_name=<mysql-db>
```

Required files (both gitignored):
- `.env` — secrets
- `google_credentials.json` — Google service account key for Sheets API

## Key directory structure

```
app/                  # FastAPI layer
  bot_manager.py      # BotManager — lifecycle (start/stop polling)
  router.py           # FastAPI routes (POST/DELETE/GET /clients/, POST /shutdown)
  schemas.py          # Pydantic models; ClientData auto-generates aiogram Router in __init__
conversator/          # Bot intelligence
  router_generator.py # generate_router(client_data) -> aiogram Router (dynamic)
  conversator.py      # LLM chat, tool calls, summarization
  file_loader.py      # Google Sheets → prompt/buttons/tools/price_list
  gpt_tools.py        # Tool definitions (get_prices, call_manager, etc.)
  chat_history.py     # JSON Lines chat log per user
utils/
  client.py           # AsyncOpenAI client (SSL verify=False)
  settings.py         # pydantic-settings from .env
  get_clients_from_db.py  # MySQL connection with retry (5 attempts, 30s base backoff)
  middleware.py        # 2-second per-user throttling
  errors.py           # Error reporting to @m16_tg_errors_channel
  decorators.py       # Exponential backoff (5 retries) + 403 → 2-hour wait
```

## Database (MySQL)

Table: `axe_bot` (filtered by `deleted = 0`)

Columns: `client_name`, `table_id`, `sheet_id`, `price_id`, `price_sheet`, `channel_id`, `token`, `manager_ids` (comma-separated), `deleted`

DB retry at startup: 5 attempts, exponential backoff (30s, 60s, 120s... + jitter).

## Google Sheets → prompt pipeline

1. Load sheet data → filter columns A:B
2. Extract `buttons`, `placeholder` rows by keyword
3. Extract `[tool][name]` patterns for tools
4. Send remaining rows to `google/gemini-2.5-flash-pre-05-20` via OpenAI-compatible proxy to auto-generate the system prompt
5. Optionally load `price_id`/`price_sheet` for price list

## LLM quirks

- Model: `openai/gpt-4o-mini` (routed through VSEGPT proxy)
- `extra_headers={"X-title": "axe-tg-bots"}` on all API calls
- AsyncOpenAI client created with `httpx.AsyncClient(verify=False)` — SSL verification disabled
- Exponential backoff decorator wraps `chat.completions.create` (5 retries, handles RateLimitError, InternalServerError, APIConnectionError, and 403 with 2-hour wait)

## Bot lifecycle

- `schemas.py:ClientData.__init__` calls `generate_router(self)` during construction
- `BotManager.add_and_start_client` creates Bot + Dispatcher + middlewares + polling task
- `BotManager.remove_client` closes session, stops polling, cancels task
- All bots share a single `MemoryStorage` and `FSMStrategy.CHAT`

## Chat history

- Stored as JSON Lines files: `logs/{client_name}/{user_id}.json`
- Only `user` and `assistant` role messages are loaded (last 10)
- `chat_history_transformer.py` converts old JSON array format → JSON Lines

## API endpoints

| Method | Path | Description |
|---|---|---|
| POST | `/clients/` | Start a new bot |
| DELETE | `/clients/{name}` | Stop and remove a bot |
| GET | `/clients/` | List active bots |
| POST | `/shutdown` | Stop all bots |

Client schema: `client_name`, `table_id`, `sheet_id`, `price_id` (opt), `price_sheet` (opt), `channel_id` (@name or -100...), `manager_ids` ([int]), `token`.

## No tests, no linter/formatter config

There is no test suite, CI, pre-commit, ruff, black, or mypy config. No `pyproject.toml`.
