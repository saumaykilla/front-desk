# Voice agent

LiveKit Agents voice assistant using Google's Gemini Live API through the LiveKit Google plugin. The voice agent calls the FastAPI booking lookup tool and never receives Mews credentials. The Google plugin uses `GOOGLE_API_KEY` directly; the runtime does not use LiveKit Inference or switch providers on failure.

## Configure

Copy `.env.example` to `.env.local` and set LiveKit/Google values, `BACKEND_API_URL`, and `BACKEND_API_TOKEN`. The token must match backend `AGENT_API_TOKEN`. Mews settings stay in the backend environment. `GOOGLE_REALTIME_MODEL` defaults to `gemini-3.8-live`. The Google GenAI client defaults to API version `v1`, so the session explicitly uses `v1beta` for Gemini Live.

The LiveKit job dispatcher must put the frontend-selected property in JSON job metadata:

```json
{"property":"nolita"}
```

The supported values are `nolita` and `nap_york`. The worker validates this metadata and captures it in the tool; the model cannot select or change the property. If metadata is absent or invalid, the lookup tool returns `unavailable` without calling the backend.

For each lookup, the agent gathers either a full name or booking confirmation/reference number, confirms the check-in date in `America/New_York`, and confirms name spelling before calling the backend. The backend checks a supplied number against both Mews reservation confirmation numbers and channel booking references. A booking match is not guest authentication and does not authorize check-in or other changes.

## Run and verify

```bash
source .venv/bin/activate
# Talk to the agent locally using this computer's microphone and speakers:
lk agent console agent.py
# Run a development worker for the frontend/LiveKit app with hot reload:
lk agent dev agent.py
# Or start the worker directly without the LiveKit CLI:
python worker.py
# Check local configuration without connecting to LiveKit or Google:
python worker.py readiness
python -m pytest
```

Use one agent start mode at a time. `lk agent console agent.py` runs the agent locally against the microphone and speakers. The local console does not provide the frontend-selected property metadata, so use the normal frontend dispatch to verify a booking lookup. `lk agent dev agent.py` runs a development worker for the frontend and reloads on code changes. The module loads `.env.local` before creating its Google model session. Provider authentication or model-access errors are reported and never trigger a LiveKit Inference fallback.
