# AGENTS.md

## Project Overview

Apache Airflow 3.2.0 (CeleryExecutor) pipeline that processes price monitoring Excel/CSV files for food products (meat, fish, milk, egg, fruit). Files are picked up hourly, processed through an ML pipeline, and saved to a MySQL database.

## Commands

```
make docker_init           # First-time setup (creates .env with AIRFLOW_UID, runs DB migration)
make docker_up             # Build and start all services
make docker_stop           # Stop services
make docker_clean_up_all_data  # Tear down + delete all volumes
```

Airflow UI: http://localhost:8080 | Flower: http://localhost:5555

## Setup

1. Copy `.env.local` to `.env` and fill in real values (DB credentials, Fernet key, JWT secret, Redis password, monitoring folder paths)
2. Run `make docker_init` then `make docker_up`
3. `.env` is gitignored — never commit secrets

## Architecture

```
dags/              → Airflow DAG definitions (schedule: hourly)
app/               → Python application built into app-worker Docker image
app/docker_commands/  → CLI entrypoints invoked by DAGs via CustomDockerOperator
plugins/           → CustomDockerOperator plugin (runs app-worker containers per task, passes XCom)
data/              → Temp data (gitignored except .gitkeep)
logs/, config/     → Auto-created by airflow-init (gitignored)
```

### Pipeline flow (per file)

`wait_file_appear` → `collect_files` → `extract_excel/csv` → [`classify` (meat only)] → [`outliers` (meat only)] → `save_db`

Each task step spins up a separate `app-worker` container via `CustomDockerOperator`. Containers share bind-mounted folders for monitoring files and temp data.

### Key design details

- **DAGs run inside Airflow containers**, but processing happens in **ephemeral app-worker containers** spawned per task
- `CustomDockerOperator` uses `xcom_all=True` to pass file paths between tasks via XCom
- Host monitoring folders (`MONITORING_NEW_FOLDER/{type}/`) are bind-mounted into containers at `/opt/airflow/monitoring/new/{type}/`
- On success, files move to `MONITORING_PROCESSED_FOLDER/{type}/`; on failure to `MONITORING_ERRORS_FOLDER/{type}/`
- Only **meat** pipeline has ML classification (`make_classification`) and outlier detection (`make_outliers_detection`)
- Other types (fish, milk, egg, fruit) go: extract → save_db directly
- The Dockerfile copies `.env` into the app-worker image (contains DB connection settings used by the app)

## Testing

No test suite exists. Verify changes by:
1. `make docker_up --build` to rebuild app-worker
2. Drop a test file into the configured `MONITORING_NEW_FOLDER/{type}/`
3. Watch execution in Airflow UI or Flower

## Conventions

- Python 3.11, no virtualenv needed (everything runs in Docker)
- CLI commands use `click` — invoked as `python -m app.docker_commands.<module>`
- DAG constants live in `dags/constants.py` (paths, timeouts, extensions)
- Each product type has its own subdirectory under `app/` with processors
