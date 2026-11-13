# Google GenAI voice agent entrypoint

## 1. Objective

Make the repository's canonical LiveKit agent entrypoint run the existing front-desk booking assistant directly through Google's Gemini Live API using the LiveKit Google plugin and the configured `GOOGLE_API_KEY`. Remove the temporary LiveKit Inference override used for the audible test, and make the local run path clear and repeatable.

## 2. Scope

Included:

- Make `voice-agent/agent.py` the canonical LiveKit Agents CLI entrypoint, with a discoverable `AgentServer` and `@server.rtc_session` handler, usable by both `lk agent console agent.py` and `lk agent dev agent.py`.
- Keep booking behavior, New York check-in date handling, and trusted property metadata behavior unchanged.
- Construct the session with `livekit.plugins.google.realtime.RealtimeModel`, using Google credentials and an explicit configurable Gemini Live model.
- Keep readiness checks and the existing `worker.py` invocation compatible, either through a small delegation layer or an equally clear supported command.
- Update environment examples and voice-agent documentation with the Google GenAI model, credential, and terminal-console run instructions.
- Remove the temporary `console_entry_for_test.py` Inference shim.
- Add focused configuration/session tests for the direct Google plugin route and ensure no Inference model is selected by the normal agent.

Excluded:

- Backend, Mews, booking lookup, property dispatch, frontend, or prompt behavior changes.
- LiveKit Cloud deployment, project settings, API-key creation, or Google account/model-access changes.
- A fallback from Google GenAI to LiveKit Inference. Provider failures must be surfaced clearly.

## 3. Existing architecture

- `voice-agent/agent.py` defines `FrontDeskAgent` and its booking tool, but is not currently the CLI entrypoint.
- `voice-agent/worker.py` owns readiness reporting, `AgentServer`, the job entrypoint, and `cli.run_app`.
- `voice-agent/session.py` constructs a direct Google-plugin realtime model in the normal runtime.
- `voice-agent/console_entry_for_test.py` temporarily monkeypatches session creation to use `livekit.agents.inference.RealtimeModel`; this was used only for the approved audible test after direct Google API calls returned HTTP 404.
- `voice-agent/config/settings.py` has a Google API key, optional model ID, and voice setting. The `.env.local` files are local and must not be committed or exposed.
- The existing booking-reference implementation and associated uncommitted tracker/document changes are outside this plan and must be preserved.

## 4. Proposed implementation

Follow LiveKit's current Python agent structure: expose a module-level `AgentServer` and decorated job handler from `agent.py`, and make it usable with both `lk agent console agent.py` and `lk agent dev agent.py`. Keep `FrontDeskAgent` and booking tools modular; move the agent class to a small focused module if needed to avoid circular imports.

Use `livekit.plugins.google.realtime.RealtimeModel` for the live session. The model should be an explicit setting, defaulting to `gemini-3.8-live` to match the working `my-agent` Google setup, with `GOOGLE_REALTIME_MODEL` available for a supported alternative. Explicitly set the Google Live API version to `v1beta`; `google-genai` 3.x otherwise defaults to `v1`, which produced the observed 404. Set `vertexai=False` for the Google Gemini API path. Do not import or instantiate `livekit.agents.inference` in runtime code. Keep LiveKit credentials for room transport and `GOOGLE_API_KEY` for Google model access as separate responsibilities.

Retain `worker.py readiness` and the existing worker startup path for compatibility. Make it delegate to the canonical agent server instead of maintaining a second server definition. Do not silently retry with LiveKit Inference when Google rejects credentials, model access, or a connection.

## 5. Data and API contracts

- Required environment variables remain `LIVEKIT_URL`, `LIVEKIT_API_KEY`, `LIVEKIT_API_SECRET`, `GOOGLE_API_KEY`, `BACKEND_API_URL`, and `BACKEND_API_TOKEN`.
- `GOOGLE_REALTIME_MODEL` is optional; when absent, use `gemini-3.8-live`.
- The Google plugin uses API version `v1beta` and `vertexai=False` for the Gemini Developer API.
- `GOOGLE_REALTIME_VOICE` remains optional and defaults to the existing `Puck` voice.
- LiveKit job metadata continues to carry the trusted property as `{"property":"nolita"}` or `{"property":"nap_york"}`. Missing or invalid property context must continue to prevent booking lookup.
- The existing `find_guest_booking` backend request/response contract does not change.

## 6. Implementation steps

1. After approval, move this plan to `plans/approved/` and track it as a new voice-agent feature without changing `BOOKING-001` criteria.
2. Refactor the module structure so `agent.py` is the single CLI-discoverable server entrypoint while preserving readiness behavior and reusable agent class boundaries.
3. Set the direct Google-plugin model default and validate settings before session startup; retain the current fail-fast readiness behavior.
4. Remove the temporary inference test shim and update env examples, run instructions, and architecture/feature documentation as appropriate.
5. Add tests for model selection, required Google credential handling, CLI/server entrypoint registration, and preservation of property metadata handling.
6. Run voice-agent tests and import/readiness checks. If credentials are available, conduct a direct-Google console smoke test; record provider access failures without falling back to Inference. Verify a booking lookup separately through the frontend's trusted property dispatch, because local console sessions do not carry that frontend property metadata.
7. Update feature status, `progress.md`, and `session-handoff.md` with actual evidence and any credential-access blocker.

## 7. Failure handling

- Missing required settings should fail readiness before a job starts, without attempting a provider connection.
- Google authentication, model availability, quota, or network errors should be logged without exposing the API key or guest information and returned as a visible startup/session failure.
- The agent must not claim it can perform a booking lookup if model startup failed.
- No retry via LiveKit Inference is allowed. Any provider retry must be bounded by the SDK's documented behavior and must not switch providers.
- Backend lookup failures continue to follow the existing `unavailable` booking-tool response.

## 8. Security considerations

- Read Google and LiveKit credentials only from environment configuration; do not log or commit values.
- Keep Google API access in the voice agent and Mews credentials only in the backend.
- Keep property selection sourced from trusted LiveKit metadata, not model-generated tool arguments.
- Preserve current guest-data redaction and error handling.
- Avoid modifying local `.env.local` files; update only `.env.example`.

## 9. Testing strategy

- Unit tests: model factory selects `google.realtime.RealtimeModel`, passes the configured Google API key/model/voice, uses the documented default model when unset, and refuses missing Google credentials.
- Agent tests: `agent.py` exposes one canonical server/entrypoint; `worker.py readiness` remains compatible; property metadata continues to be validated before tool use.
- Existing booking-tool tests remain unchanged and should pass.
- Manual integration: run `lk agent console agent.py` with the real `GOOGLE_API_KEY` and verify a direct Google response. Verify a booking lookup separately through the normal frontend dispatch, which supplies trusted property metadata. A credential/model 404 is a failed integration check, not a passing test.

## 10. Acceptance criteria

- `agent.py` is a valid, discoverable LiveKit Agents entrypoint and the documented `lk agent console agent.py` command starts it.
- Runtime model construction uses the Google plugin and `GOOGLE_API_KEY`; no runtime code or default run command uses LiveKit Inference.
- Google provider errors are visible and do not trigger an automatic provider switch.
- Property metadata, booking tools, and readiness behavior remain intact.
- Automated tests and import/readiness checks pass, and the result of any real Google console attempt is documented accurately.
- Env examples and run documentation match the code; no secret values are present in tracked files.
- Feature tracking, progress, and handoff reflect the verified state, with any unavailable Google model access clearly marked.

## 11. Risks and open questions

- Direct Google Live API attempts returned HTTP 404 when the API version was omitted. The working `my-agent` project explicitly uses `api_version="v1beta"`; after matching that setting, a direct Gemini response was received in the console.
- The working `my-agent` project uses `gemini-3.8-live` with `api_version="v1beta"` and `vertexai=False`. LiveKit docs list Gemini 3.8 as supported through the direct Google plugin. Booking lookup still needs verification through the frontend's trusted property dispatch.
- Repository changes from the booking-reference work are uncommitted. Keep this work limited to files in this plan and do not commit without the user's authorization.
