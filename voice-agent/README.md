# Voice agent

LiveKit Agents worker using the Google realtime plugin. The installed plugin default model is used unless a compatible `GOOGLE_REALTIME_MODEL` is explicitly configured. No external connection is attempted until startup with real credentials.

```bash
cp .env.example .env
source .venv/bin/activate
python worker.py
```

Required values: LiveKit URL/key/secret, Google API key, and backend URL. For local config-only readiness run `python worker.py readiness`; this does not prove service connectivity. Verify with `python -m pytest` from this directory.
