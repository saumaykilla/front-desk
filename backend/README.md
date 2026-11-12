# Backend

FastAPI foundation; only `GET /health` is implemented. No hospitality workflows or external integrations are active.

```bash
cp .env.example .env
source .venv/bin/activate
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Settings: `APP_ENV`, `APP_NAME`, `LOG_LEVEL`, and comma-separated `CORS_ALLOWED_ORIGINS`. Verify with `python -m pytest` from this directory.
