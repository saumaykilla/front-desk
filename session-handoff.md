# Session Handoff

## Verified Now

- Initial harness engineering principles have been established.
- Mandatory planning and explicit approval workflows have been defined.
- Backend health/settings checks pass: 2 pytest tests and the FastAPI app import.
- Voice-agent readiness tests pass: 6 pytest tests; worker/session/agent imports pass with the installed Google plugin.
- Web lint, TypeScript check, and production build pass.
- `./init.sh` completed successfully after a network-enabled retry installed the voice-agent and web dependencies.
- A plan for the requested setup work is pending explicit user approval at `plans/pending/application-foundation.md`.
- No hospitality workflows or product features are implemented.

## Changed This Session

### Engineering Harness

- Prepared initial AGENTS.md instructions.
- Established a mandatory planning → review → approval → tracking → implementation → verification workflow.
- Defined feature status conventions.
- Established repository-local progress tracking and session handoff requirements.
- Prepared initial feature_list.json.
- Prepared initial progress.md.

### Application

- Existing backend and voice-agent scaffolds were inspected and verified; no application files were changed this session.
- The web app remains the generated Next.js starter and has not been customized.
- No external service connections were attempted; no credentials were supplied.
- The installed `livekit-plugins-google` version is 1.8.11. Its realtime model constructor accepts an unspecified `model`, consistent with relying on the plugin default.
- `plans/pending/application-foundation.md` captures the proposed remaining setup scope; implementation has not started pending approval.

## Broken Or Unverified

- The requested landing page, shadcn/ui initialization, frontend API client structure, and root/app documentation still need implementation after plan approval.
- The voice-agent worker has not been started with real credentials; LiveKit and Google connectivity remain unverified by design.
- npm reported 8 moderate audit findings during dependency installation; no automatic dependency changes were applied.
- Running pytest from the repository root incorrectly combines the two isolated Python projects; run checks from each app directory.
- The workspace snapshot does not include `.git`, preventing status/history/diff/commit checks.
- Root README and root `.env.example` are not present yet.

## Next Best Step

- Await explicit approval or requested edits for `plans/pending/application-foundation.md`.
- After approval, move the plan to `plans/approved/`, update `feature_list.json` to track the approved setup scope, then implement one setup task at a time.

## Baseline Commands and Results

- `./init.sh` — passed after approved network-enabled rerun; installs declared dependencies.
- `cd backend && ./.venv/bin/python -m pytest` — 2 passed (one Starlette/httpx deprecation warning).
- `cd backend && ./.venv/bin/python -c 'from app.main import app; print(app.title)'` — passed.
- `cd voice-agent && ./.venv/bin/python -m pytest` — 6 passed.
- `cd voice-agent && ./.venv/bin/python -c 'from livekit.plugins import google; import agent, session, worker, inspect; print(inspect.signature(google.realtime.RealtimeModel))'` — passed; plugin version 1.8.11 allows an unspecified model.
- `cd web && npm run lint` — passed.
- `cd web && npx tsc --noEmit` — passed.
- `cd web && npm run build` — passed.
- No real LiveKit or Google API request was made.

## Commands

- Startup: `./init.sh` (pending implementation).
- Verification: To be determined after repository inspection.
- Focused debug command: To be determined based on the repository's existing stack.

## Instructions For The Next Session

Start by reading AGENTS.md, progress.md, feature_list.json, and this handoff. First obtain explicit user approval for `plans/pending/application-foundation.md` (or revise it as requested). Do not begin implementation until approval is explicit. After approval, move the plan into `plans/approved/`, update feature tracking, and complete only the setup scope in that plan.

## Latest Session Handoff — 2026-11-12

- Approved plan: `plans/approved/application-foundation.md`.
- Implemented root and component setup documentation, frontend placeholder, shadcn configuration, typed backend health client, frontend environment example, and typecheck script.
- Backend: 2 tests pass. Voice agent: 6 tests pass. Web typecheck and lint pass. Production build is blocked by sandbox process/port permission (Turbopack); retry `cd web && npm run build` with appropriate permissions.
- `feature-list.json` status is `implemented`; do not mark verified until the production build passes.
- No external service calls or guest workflows were implemented.

### Follow-up verification — 2026-11-12

- Turbopack build is incompatible with this execution environment because it cannot create/bind its worker process. Switched the web `build` script to Next.js's supported Webpack builder.
- `cd web && npm run build` now passes. Backend tests (2), voice-agent tests (6), web typecheck, and lint also pass as recorded above.
- Feature status is now `passing`; there are no remaining implementation tasks for the approved foundation plan.

### Current Handoff — 2026-11-12 (implementation)

#### Current state

- Current feature: `BOOKING-001`, guest identification and current Mews booking lookup for Nolita and Nap York.
- Status: implementation complete; automated checks pass. Nap York live access is verified for name lookup. The feature remains `in_progress` until Nolita access and a positive confirmation-number case are verified.
- Approved plan: `plans/approved/guest-identification-and-booking-lookup.md`.
- Last completed task: final backend, voice-agent, web, and repository diff checks; feature evidence and this handoff updated.

#### Changes made

- Backend: added the bearer-authenticated `POST /guest-bookings/lookup` route, strict schemas, separate per-property Mews config, and read-only Mews Connector client with New York local-date filtering, pagination, bounded 429 retry, customer/companion name matching, and safe error mapping.
- Voice agent: added the `find_guest_booking` tool, persistent authenticated backend client, allowlisted property context from LiveKit JSON job metadata, New York current-date prompt context, and spelling/date confirmation instructions.
- Documentation and secret-free env examples now cover `ClientToken`, `AccessToken`, property-specific settings, shared agent/backend bearer auth, and required job metadata.
- No real credentials were added.

#### Verification

- `backend/.venv/bin/python -m pytest -q` — 27 passed, with one Starlette/httpx deprecation warning.
- `voice-agent/.venv/bin/python -m pytest -q` — 11 passed.
- `cd web && npm run lint` — passed.
- `cd web && npm run typecheck` — passed.
- `cd web && npm run build` — passed with Webpack.
- `./init.sh` — completed successfully earlier in the implementation session.
- Credentialed, read-only Nap York Mews smoke tests: name lookup matched one `Confirmed` reservation on 2026-11-12; confirmation-number lookup returned `no_match` for that date.
- No guest name, confirmation number, response body, or credential was recorded in repository artifacts.

#### Outstanding work

- Configure Nolita credentials if they are not present in the runtime environment; the local Nap York configuration was sufficient for the live name lookup.
- Run a credentialed smoke test for Nolita and obtain a positive confirmation-number lookup case for Nap York; verify the deployed Connector API response contracts and enabled operation permissions.
- Keep `BOOKING-001` `in_progress` until that check passes; then record evidence and update status according to `feature_list.json` rules.

#### Next session instruction

With the remaining runtime credentials and a known confirmation number available, run a read-only lookup against Nolita and a positive confirmation-number lookup against Nap York. Also check a previous-day in-house reservation and an unavailable/authentication failure. Record sanitized outcomes without guest details or tokens, then update `feature_list.json`, `progress.md`, and this handoff.

### Current Handoff — 2026-11-12 (booking-reference extension plan)

#### Current state

- Active feature: `BOOKING-001`, with current name/number lookup implemented in commit `aa8503f`.
- New requested extension: allow one supplied value to match either Mews reservation confirmation `Number` or channel/booking reference `ChannelNumber`.
- Plan status: pending explicit approval at `plans/pending/booking-reference-number-lookup.md`; no code for this extension has been written.
- Existing uncommitted changes from the previous live lookup session remain in `feature-list.json`, `progress.md`, and this handoff. Preserve them.

#### Findings and proposed approach

- Current code sends a number only as Mews `Numbers`.
- Current Mews docs describe `Numbers` for Mews reservation confirmation numbers and `ChannelNumbers` for channel references, including OTA examples: https://docs.mews.com/connector-api/operations/reservations
- The pending plan proposes two separately filtered read-only searches with the same date, state, and property constraints, then merges/de-duplicates by reservation ID. If either query fails, return `unavailable`.
- Assumption to confirm: “booking reference number” means Mews reservation `ChannelNumber` (channel/OTA reference), not another identifier field.

#### Verification

- Backend `.venv` pytest: 27 passed.
- Voice-agent `.venv` pytest: 11 passed.
- Web lint could not run: local `eslint` executable is missing. The `./init.sh` attempt showed PyPI DNS retry warnings and did not yield a confirmed successful completion in this session.
- No Mews API calls were made for this extension.

#### Next step

Ask the user to confirm the `ChannelNumber` meaning and explicitly approve the pending plan. After approval, implement only that scope, update `feature_list.json`, run focused backend/voice tests, and refresh documentation and handoff.

### Current Handoff — 2026-11-13 (Google GenAI entrypoint implementation)

#### Current state

- The user reports that the audible Nap York booking-reference test succeeded using the temporary LiveKit Inference console shim.
- Normal runtime `session.py` already uses the Google provider plugin (`google.realtime.RealtimeModel`) and configured `GOOGLE_API_KEY`.
- The temporary `voice-agent/console_entry_for_test.py` overrides the normal path with LiveKit Inference. It was used because direct Google Live API requests returned HTTP 404; the successful Inference test does not prove direct Google access works.
- Approved plan: `plans/approved/google-genai-agent-entrypoint.md`.
- Feature: `VOICE-001`, currently `in_progress`; direct Google Gemini Live now responds, while booking lookup through trusted frontend dispatch remains unverified.
- Existing uncommitted booking-reference changes are present. Preserve them and do not commit without authorization.

#### Docs and proposed approach

- Current LiveKit docs describe the Google plugin as the direct Gemini Live path using `GOOGLE_API_KEY`; Inference instead uses LiveKit Cloud credentials and bills through LiveKit.
- Docs currently list `gemini-2.5-flash-native-audio-preview-12-2025` as the Google Gemini API plugin default.
- `voice-agent/agent.py` now exposes the canonical `AgentServer` and `@server.rtc_session` entrypoint. The reusable `FrontDeskAgent` class is in `front_desk_agent.py`; `worker.py` reuses the server and still supports `readiness`.
- `session.py` builds `google.realtime.RealtimeModel` with `GOOGLE_API_KEY`, the configured model and voice, `api_version="v1beta"`, and `vertexai=False`. There is no runtime Inference path or provider fallback. `.env.local` is loaded by the settings module.
- The temporary `console_entry_for_test.py` shim was removed. Env example, README, and architecture docs describe direct Google setup. Use `lk agent console agent.py` for local mic/speaker testing and `lk agent dev agent.py` for the frontend-connected development worker.
- The installed Google plugin is 1.8.11 and `google-genai` is 3.3.0. The working `my-agent` uses `gemini-3.8-live` with `api_version="v1beta"`; the Google GenAI SDK otherwise defaults to `v1`, which produced the 404.

#### Verification

- `./init.sh` completed before implementation; existing Python dependencies were satisfied despite network retry warnings, and web dependencies installed.
- `voice-agent/.venv/bin/python -m pytest -q` — 16 passed.
- `backend/.venv/bin/python -m pytest -q` — 29 passed, one Starlette/httpx deprecation warning.
- Agent import check — `AgentServer` and entrypoint callable.
- `worker.py readiness` — ready, no missing variables; it does not test external connectivity.
- Initial direct `lk agent console --text agent.py` attempt with API version unset returned HTTP 404. After explicitly setting `v1beta`, the console returned a direct Google response to a text turn. The process was stopped; no fallback occurred.
- Local console sessions do not carry frontend-selected property metadata. The approved plan now calls for verifying a booking lookup separately through normal frontend dispatch.
- LiveKit docs consulted: [Gemini Live API](https://docs.livekit.io/agents/models/realtime/gemini/), [Google AI and LiveKit](https://docs.livekit.io/agents/integrations/google/), and [Agent job lifecycle](https://docs.livekit.io/agents/server/job/).

#### Next step

Verify booking lookup through normal frontend dispatch with trusted property metadata. If that passes, update `VOICE-001` status and evidence; preserve existing booking-reference changes and do not commit without authorization.
