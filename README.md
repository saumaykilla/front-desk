# Front Desk Agent

Development foundation for a hospitality voice assistant. The repository contains three independently runnable applications; no reservation, check-in, check-out, or staff workflows are implemented yet.

## Architecture

- `backend/`: FastAPI health endpoint, environment-backed settings, CORS, and logging.
- `voice-agent/`: LiveKit Agents worker with Google's real-time plugin; external connectivity requires real credentials.
- `web/`: Next.js App Router, TypeScript, Tailwind CSS, shadcn/ui configuration, and typed backend client.

## Prerequisites

Python 3.12+, Node.js 22+, and npm. Registry access is required for initial dependency installation.

## Initialize

```bash
./init.sh
```

Copy each component's `.env.example` to `.env` and configure only the values required by that component. Never commit credentials.

## Run independently

```bash
cd backend && source .venv/bin/activate && uvicorn app.main:app --reload
cd voice-agent && source .venv/bin/activate && python worker.py
cd web && npm run dev
```

Backend health: `http://127.0.0.1:8000/health`. See each app README for details and verification commands.
