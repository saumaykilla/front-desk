# Front Desk Agent

Voice-based hospitality assistant foundation with an implemented guest booking lookup. The repository contains three independently runnable applications; check-in, check-out, payment, access, and staff workflows are not implemented.

## Architecture

- `backend/`: FastAPI health and authenticated booking lookup endpoints, property-scoped Mews Connector API access, environment-backed settings, CORS, and logging.
- `voice-agent/`: LiveKit Agents worker with Google's real-time plugin and a tool that uses authenticated backend booking lookup; external connectivity requires real credentials.
- `web/`: Next.js App Router, TypeScript, Tailwind CSS, shadcn/ui configuration, and typed backend client.

## Prerequisites

Python 3.12+, Node.js 22+, and npm. Registry access is required for initial dependency installation.

## Initialize

```bash
./init.sh
```

Copy each component's `.env.example` to `.env` and configure only the values required by that component. Never commit credentials.

For booking lookup, configure backend `AGENT_API_TOKEN` and voice-agent `BACKEND_API_TOKEN` to the same high-entropy secret. Set separate Mews API URL, ClientToken, and AccessToken values for Nolita and Nap York in `backend/.env`. The LiveKit job metadata must include `{"property":"nolita"}` or `{"property":"nap_york"}` as selected by the frontend. Both properties use the `America/New_York` timezone.

## Run independently

```bash
cd backend && source .venv/bin/activate && uvicorn app.main:app --reload
cd voice-agent && source .venv/bin/activate && python worker.py
cd web && npm run dev
```

Backend health: `http://127.0.0.1:8000/health`. See each app README for booking lookup configuration and verification commands.
