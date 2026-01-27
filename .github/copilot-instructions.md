# Project Context

This is the `fintech-data-clearinghouse` project, a Python-based backend service designed to ingest financial trade data via SFTP, validate it, store it in PostgreSQL, and expose it via a REST API.

The system emphasizes reliability ("boring technology"), strict data validation, and production-grade simulation using Docker.

# Technology Stack

- **Language:** Python 3.11+
- **Framework:** Flask 3.x (Blueprints for routing)
- **Database:** PostgreSQL 17+
- **ORM/Driver:** SQLAlchemy 2.0+ with `psycopg` (v3) driver. **Do not use `psycopg2`.**
- **Data Processing:** Pandas 3.x (for CSV parsing and validation).
- **Ingestion:** Paramiko (for active SFTP polling).
- **Infrastructure:** Docker & Docker Compose (PostgreSQL 17.7, SFTP service via atmoz/sftp).
- **Web Server:** Flask runs on `0.0.0.0:5000` in container (see `run.py`).

# Coding Guidelines

## 1. Code Style & Tone

- **No Emojis:** Do not include emojis in comments, git commits, or documentation.
- **Conciseness:** Write direct, imperative code. Avoid verbose boilerplate.
- **Type Hinting:** Use standard Python type hints (`from typing import ...`) for all function arguments and return values.

## 2. Database Interactions (SQLAlchemy 2.0 Style)

- Always use the `psycopg` (v3) dialect.
- When writing raw SQL, always wrap queries in `text()` from `sqlalchemy`.
- Use `db.session.execute()` for execution.
- Connection string format: `postgresql+psycopg://user:password@host:port/dbname`.
- The `db` singleton is initialized in `app/__init__.py` and imported as `from app import db`.
- **Preferred Pattern:**

  ```python
  from sqlalchemy import text
  from app import db

  # DO:
  result = db.session.execute(text("SELECT 1"))

  # DON'T:
  # result = db.engine.execute("SELECT 1")  <-- Deprecated in 2.0
  ```

## 3. Data Ingestion Architecture

**Status:** `app/ingest.py` is currently a scaffold (empty). Future implementations should follow this pattern.

- **No Local File Watching:** The application must NOT rely on local filesystem events (like `watchdog`).
- **Active Polling:** The app acts as a client. For local dev, connect to SFTP at `sftp://vest_user:pass@localhost:2222/upload` (docker-compose service).
- **Atomic Operations:**
  1. Download file to memory (or temp).
  2. Validate columns/types.
  3. Ingest to DB.
  4. **Move** file to `/processed` directory on the remote server on success.
- **Library:** Use `paramiko` for all SSH/SFTP operations.
- **Docker Compose SFTP Service:** Image `atmoz/sftp` exposes port `2222` with user `vest_user:pass`.

## 4. Error Handling

- **Operational Errors:** Database disconnects or SFTP failures should log an error but keep the main loop running (retry logic).
- **Data Errors:** Malformed CSVs or missing columns must be logged, skipped, and strictly NOT halt the ingestion process.
- **HTTP Responses:** Return clean JSON `{"status": "error", "message": "..."}` with appropriate HTTP 4xx/5xx codes.

## 5. Configuration

- All configuration must come from Environment Variables.
- Use `os.getenv('VAR_NAME', 'default')`.
- **Required Vars (docker-compose):** `DATABASE_URL`, `UPLOAD_FOLDER`.
- **Production Vars:** `SFTP_HOST`, `SFTP_USER`, `SFTP_PASS` (add as needed).

## 6. Shell & Environment

- Target the **Fish** shell for CLI commands where applicable, or standard POSIX `sh` for Docker scripts.
- Do not assume `bash` specific syntax (like arrays) unless necessary.

## 7. Docker & Local Development

- The application runs as a stateless container via `docker-compose up`.
- It should not write state to the local container filesystem (except `/tmp`).
- The Dockerfile uses `python:3.14-slim` with system deps (gcc, libpq-dev) for psycopg3.
- **Multi-service setup:**
  - `web`: Flask app (port 5000), depends on `db` health.
  - `db`: PostgreSQL 17.7, healthcheck via `pg_isready`.
  - `sftp`: atmoz/sftp (port 2222), volume-mounts `./sftp_data`.
- Commands: `docker-compose up`, `docker-compose logs -f web`.

## 8. Flask App Structure

- Entry point: `run.py` → `create_app()` runs Flask on `0.0.0.0:5000`.
- `app/__init__.py`: Defines `db = SQLAlchemy()` singleton and `create_app()` factory.
- `app/routes.py`: Contains Flask Blueprints (e.g., `/health` checks DB connectivity).
- `app/models.py`, `app/ingest.py`: Empty scaffolds; populate as features are implemented.

## 9. Testing

- `/tests` directory is empty. Use `pytest` or `unittest` for implementation.
- Focus on: CSV validation, DB operations, SFTP error handling.

# "Don't" List

- Do not use `psycopg2-binary`. Use `psycopg[binary]`.
- Do not suggest `watchdog` for file monitoring.
- Do not use complex class hierarchies where a simple function or module will suffice.
- Do not write to container filesystem outside `/tmp` (use DB for state).
