# AGENTS.md

## Quick start

```bash
# 1. Create venv (Makefile uses venv/bin/python, not system Python)
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# 2. Copy .env from example and fill in real values (copied into Docker image at build time)
cp .env.example .env

# 3. Download TimesFM model (~1GB, needs HF_TOKEN in .env)
make download_hf_models

# 4. Ensure external MySQL is reachable (host/port from .env) and caddy-network exists
docker network create caddy-network 2>/dev/null || true

# 5. Start stack
docker compose up -d --build
```

## Commands

| Command | Description | Notes |
|---------|-------------|-------|
| `make unit-tests` | `python -W ignore -m pytest tests/unit/models/ tests/unit/data/ -v` | No external deps |
| `make api-tests` | `python -W ignore -m pytest tests/api/api_tests.py -v` | Requires `docker compose up` |
| `make e2e-tests` | `python -W ignore -m pytest tests/e2e -v` | Requires external services |
| `make download_hf_models` | Downloads TimesFM to `storage/.cache/huggingface` | Needs `HF_TOKEN` in `.env` |

All test commands run with `-W ignore` via the Makefile. The Makefile `include .env` and exports it. Tests use `tests/configs.py:get_test_config()` (in-code Config object) or `tests/test_config.yaml`.

## Architecture

- **FastAPI** on port 81, HTTP Basic Auth (credentials from `.env`). Entry point: `main.py` with APScheduler.
- **APScheduler** runs two cron jobs: weekly forecast (Saturday 21:00, 13-step) and monthly forecast (1st-7th Sunday 21:00, 12-step), plus Grafana dashboard updates.
- **RQ (Redis Queue)** for distributed async task processing. Redis is the single broker.
- **MySQL** is **external** (not in docker-compose). Connection via `.env` (`db_host`, `db_port`, etc.). Tables: `raw_monitorings_meat`, `raw_monitorings_seafood/*`, `forecasting_history`, `predicted_prices`, indicator tables, Grafana dashboard metrics.
- 5 worker types, each in its own Docker image with isolated dependencies:
  - `worker-rapids` (conda env, ARIMA — temporarily disabled in pipeline; builds from `workers/rapids/` context)
  - `worker-general` (Prophet, Exponential Smoothing, ThetaModel)
  - `worker-neuralprophet` (NeuralProphet, GPU)
  - `worker-timesfm` (TimesFM, GPU, needs HF token; `HF_HOME=/app/storage/.cache/huggingface`)
  - `worker-common-tasks` (DB persistence, lightweight)
- **Grafana** dashboard auto-updated via `dashboards/grafana_dashboard.py`.
- **Caddy** reverse proxy via external `caddy-network` label (`forecasting.3090.a505.ru`).
- `storage/` volume: mounted for model cache, uploaded files, and config overrides. Gitignored except `.gitkeep`.

## Config

- Two YAML config profiles: `config/config.yaml` (weekly, 13-step forecast) and `config/month_config.yaml` (monthly, 12-step).
- Config override: `storage/config.yaml` or `storage/month_config.yaml` takes precedence if it exists.
- Loaded via OmegaConf → Pydantic (`config/configs.py:Config`).
- `config/update_utils.py` patches config at runtime for API-predict requests.
- `.env` loaded via `pydantic-settings` in `app/common/settings.py`.

## Workers

Each worker is a standalone container running `python -m worker`. Workers share no code at runtime — each copies its own `app/` subdirectory at build time. The common entrypoint is `app.predict.predict_with_hyperparameter_tuning(df_json, cfg_dict, forecasting_date, model_name?)`.

## Forecasting pipeline

1. `predict_pipline()` (scheduled) or `/predict` API endpoint
2. Data: MySQL query or uploaded Excel → DataFrame with columns `ds`, `y`, `ID`
3. Jobs dispatched to RQ queues per model type
4. Each model: Optuna hyperparameter tuning → train → predict → serialize result as JSON
5. `save_predictions()` (common-tasks worker) collects results and saves to DB
6. Best model per time-series selected later via SQL by lowest `mape_at_test`

Models: Exponential Smoothing, Prophet, ThetaModel, NeuralProphet, TimesFM. ARIMA queue exists but disabled in predictor.

`use_only_light_models=True` skips NeuralProphet and TimesFM. `use_only_light_models=False` also adds macroeconomic/agro indicators for NeuralProphet.

## API endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/predict` | Submit forecast task (multipart: Excel file + params). Returns `{"task_id": "..."}` |
| GET | `/status/{task_id}` | Check task status: `PENDING`, `SUCCESS`, or `FAILURE` |
| GET | `/result/{task_id}` | Get forecast results after `SUCCESS`: `{"result": {"values": [...]}}` |

All endpoints require HTTP Basic Auth (`api_user:api_password` from `.env`).

## Repo layout

```
forecasting/
├── app/           FastAPI app (api, common, data, database, predictor, redis_queue)
├── config/        YAML configs + Config pydantic model
├── dashboards/    Grafana dashboard auto-updater
├── storage/       Runtime data, model cache, config overrides (.gitkeep only)
├── tests/         unit/, api/, e2e + test_data/ fixtures
├── workers/       One subdir per worker type (rapids, general, neuralprophet, timesfm, common_tasks)
├── main.py        FastAPI entrypoint with APScheduler
├── Makefile       Test + download commands (uses venv/bin/python)
├── Dockerfile     Backend image (Python 3.11-slim, copies .env into image)
└── docker-compose.yaml   Full stack definition
```

## Notable quirks

- **MySQL is external** — must be running and reachable before `docker compose up`. Not managed by compose.
- **`caddy-network` is external** — must be created before compose starts (`docker network create caddy-network`).
- **`.env` must exist before build** — the backend Dockerfile does `COPY .env .`, so build fails without it.
- **Makefile uses `venv/`** — not system Python. Create venv and install deps first.
- Redis port: FastAPI app hardcodes 6379 (`app/redis_queue/connect.py`), workers use env `$REDIS_PORT` (all set to 6379 in compose).
- Config priority: `storage/config.yaml` > `config/config.yaml` (same for `month_config`).
- ARIMA is "temporarily disabled" — queue task exists but not dispatched from `predict_pipline()`. Re-enabling means uncommenting in `predictor.py`.
- Tests in `tests/unit/models/` and `tests/unit/data/` run independently. API and e2e tests require external services (DB, Redis).
- Makefile includes `.env` directly — secrets leak into Makefile namespace.
- Python 3.11 (Dockerfile base image).
- Each worker has its own `requirements.txt` — no shared dependency file across workers.
