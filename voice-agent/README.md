# Voice agent

LiveKit Agents worker using the Google realtime plugin. It provides one guest booking lookup tool that calls FastAPI; the worker never receives Mews credentials.

## Configure

Copy `.env.example` to `.env` and set LiveKit/Google values, `BACKEND_API_URL`, and `BACKEND_API_TOKEN`. The token must match backend `AGENT_API_TOKEN`. Mews settings stay in the backend environment.

The LiveKit job dispatcher must put the frontend-selected property in JSON job metadata:

```json
{"property":"nolita"}
```

The supported values are `nolita` and `nap_york`. The worker validates this metadata and captures it in the tool; the model cannot select or change the property. If metadata is absent or invalid, the lookup tool returns `unavailable` without calling the backend.

For each lookup, the agent gathers either a full name or reservation confirmation number, confirms the check-in date in `America/New_York`, and confirms name spelling before calling the backend. A booking match is not guest authentication and does not authorize check-in or other changes.

## Run and verify

```bash
source .venv/bin/activate
python worker.py
python worker.py readiness
python -m pytest
```
