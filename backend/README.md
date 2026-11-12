# Backend

FastAPI owns Mews access and guest booking lookup. The current operational endpoint is `POST /guest-bookings/lookup`; `GET /health` reports process liveness.

## Configure

Copy `.env.example` to `.env` and set:

- `AGENT_API_TOKEN`: high-entropy shared bearer secret; set the same value as `BACKEND_API_TOKEN` in `voice-agent/.env`.
- `MEWS_NOLITA_API_URL`, `MEWS_NOLITA_CLIENT_TOKEN`, `MEWS_NOLITA_ACCESS_TOKEN`.
- `MEWS_NAP_YORK_API_URL`, `MEWS_NAP_YORK_CLIENT_TOKEN`, `MEWS_NAP_YORK_ACCESS_TOKEN`.

The Mews URL is the environment's platform base address (without a path). Use HTTPS except for local development. Mews credentials never belong in the voice-agent or web environment. Missing property configuration produces an `unavailable` lookup result. A missing backend agent token disables lookup with HTTP 503.

## Request behavior

The authenticated request contains a property slug (`nolita` or `nap_york`), exactly one of `full_name` / `confirmation_number`, and the guest-confirmed local `check_in_date` (`YYYY-MM-DD`). The backend uses `America/New_York` for both properties. Results distinguish `matched`, `no_match`, `ambiguous`, and `unavailable`; the response omits Mews reservation IDs and raw PMS data.

The backend uses the read-only Mews Connector API reservation, customer, and companionship operations. It does not authenticate the guest for check-in or authorize any reservation changes.

## Run and verify

```bash
source .venv/bin/activate
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
python -m pytest
```
