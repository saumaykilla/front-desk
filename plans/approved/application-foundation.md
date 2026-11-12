# Application Foundation Setup Plan

## 1. Objective

Complete the repository setup for three independently runnable applications: a FastAPI backend, a LiveKit Agents voice worker using the Google real-time plugin, and a Next.js App Router frontend using TypeScript, Tailwind CSS, and shadcn/ui. This is repository setup only; it does not implement hospitality workflows or product features.

## 2. Scope

### Included

- Audit and retain the existing backend, voice-agent, and web foundation where it meets the request.
- Complete missing configuration, reusable directory structure, starter content, environment examples, and per-app/root documentation.
- Validate the installed LiveKit Google plugin's supported real-time model defaults/parameters without inventing a model identifier.
- Make the root initializer usable and document its behavior.
- Run the requested per-app and root verification and record actual outcomes.
- Update `feature-list.json`, `progress.md`, and `session-handoff.md` with accurate setup status and evidence.

### Excluded

- Reservation, guest verification, check-in, check-out, escalation, staff dashboard, or other hospitality workflows.
- Calling Google, LiveKit, Mews, or other service APIs with placeholder credentials.
- Production deployment, authentication, database setup, or additional integrations.
- Unrelated refactors or modifications outside the setup requirements.

## 3. Existing Architecture

- `docs/architecture.md` describes a FastAPI backend, a LiveKit Agents Python worker with Google's real-time plugin, and a Next.js TypeScript frontend.
- `backend/` already contains FastAPI entrypoint, health route, Pydantic settings, logging, CORS, a pytest setup, and a health test.
- `voice-agent/` already contains agent/session/worker modules, settings/readiness checks, a placeholder prompt, empty tools package, and readiness tests.
- `web/` already contains a Next.js App Router scaffold, TypeScript, Tailwind CSS v4, ESLint configuration, package lockfile, and default Next.js landing content.
- The root currently has `init.sh`, `.gitignore`, progress/handoff/tracking files, and architecture docs, but no root README or root `.env.example`. The web scaffold still needs the requested application placeholder, shadcn/ui setup, API client structure, environment configuration, and app-specific scripts/docs.
- This workspace does not currently expose a `.git` directory; Git status/history cannot be used as a source of change provenance.

## 4. Proposed Implementation

Preserve and complete the existing components instead of regenerating them. Keep backend and voice-agent dependencies isolated in their own Python virtual environments and keep the frontend independently runnable from `web/`. Retain backend-owned health/readiness behavior and the voice worker's explicit missing-credential check. For Google real-time model selection, rely on the installed `livekit-plugins-google` default unless verified plugin documentation demonstrates a compatible configured override; do not add a guessed model ID.

Use the existing Next.js App Router and Tailwind v4 setup. Add shadcn/ui configuration and its minimal prerequisites using the component conventions supported by the installed package versions, plus empty/reserved shared, feature, hook, service, and type directories as appropriate. Add a simple neutral setup-status landing page and a typed API client that reads the public backend URL from environment configuration. Document that the browser client can only use `NEXT_PUBLIC_` values and keep secrets confined to server-side services.

Keep environment examples per component, with a root example documenting the local setup inputs or links to component examples. Include only variables requested for this stage; no credentials or speculative Mews settings.

## 5. Data and API Contracts

- Backend health: `GET /health` returns HTTP 200 and JSON `{"status":"ok","service":"front-desk-backend"}`.
- Backend configuration: `APP_ENV`, `LOG_LEVEL`, and comma-separated `CORS_ALLOWED_ORIGINS` are loaded through Pydantic settings and `.env` support.
- Voice-agent required variables: `LIVEKIT_URL`, `LIVEKIT_API_KEY`, `LIVEKIT_API_SECRET`, `GOOGLE_API_KEY`, and `BACKEND_API_URL`. Readiness reports missing configuration locally and must not claim external connectivity.
- Frontend configuration: `NEXT_PUBLIC_BACKEND_API_URL` is the browser-visible backend base URL. The API client should expose a typed health request and surface HTTP/network errors rather than fabricate success.
- No hospitality data schemas, operational API routes, or callable agent tools are introduced in this foundation task.

## 6. Implementation Steps

1. After plan approval, update the feature tracker to identify this as the active repository foundation task and link the approved plan.
2. Complete the backend setup only where audit/verification reveals gaps; retain the health-only API and existing architecture.
3. Complete voice-agent setup only where audit/verification reveals gaps; verify Google plugin compatibility from installed package metadata/docs, preserve credential preflight, and do not connect to external services.
4. Complete the web setup: configure shadcn/ui and app directories, replace the generated landing page with a setup placeholder, add typed API service and public environment configuration, and add explicit typecheck/lint/build scripts if missing.
5. Add/update backend, voice-agent, web, and root READMEs; add the root environment example and keep per-app examples secret-free.
6. Review `init.sh` for safe, reproducible initialization and make only changes required by this plan. Avoid destructive cleanup and preserve the lockfile.
7. Execute backend import, tests, and local health request; voice-agent dependency/import/readiness checks without credentials; frontend install, typecheck, lint, and production build; and root initialization. Record exact commands and outcomes.
8. Update progress and handoff, record verification evidence in the feature tracker, inspect final diffs/files for scope and secret issues, and report blockers honestly.

## 7. Failure Handling

- Dependency installation or verification failures are recorded with their exact command and relevant error; no check is described as passing unless it exits successfully.
- If network access or package availability prevents installation, retain existing manifests and report the blocked checks; do not silently skip required checks.
- Missing LiveKit/Google credentials should cause an explicit local readiness/startup message before a connection attempt. No synthetic success response is allowed.
- API client network and non-2xx failures should be surfaced to the caller as errors.
- If the installed plugin does not support the current session construction, stop and document the compatibility issue before changing the design beyond this plan.

## 8. Security Considerations

- Never add real secrets to tracked files or logs.
- Keep LiveKit secrets and Google API keys server-side in the voice-agent environment.
- Only expose the backend URL as a public frontend variable.
- CORS origins come from backend environment configuration and credentials are not enabled by default.
- The placeholder frontend and empty voice tools must not imply that any guest operation is implemented.

## 9. Testing Strategy

- Backend: run the health/settings pytest suite, import `app.main:app`, and exercise `/health` using FastAPI's test client or a local server.
- Voice agent: install declared dependencies, import agent/worker/session modules, exercise readiness output and missing-credential startup behavior, and inspect the installed plugin's model constructor/default. Do not attempt a real LiveKit or Google connection.
- Frontend: install from `package-lock.json`, run TypeScript checking, ESLint, and `next build`.
- Root: run `./init.sh` and confirm documented startup commands/paths. Capture every command's actual exit result.
- No external service integration tests are in scope.

## 10. Acceptance Criteria

1. Backend remains independently runnable with environment-based settings, CORS, logging, and a passing `/health` check.
2. Voice-agent modules import and worker readiness handles absent credentials clearly without claiming a connection; Google model selection is verified against the installed plugin and no guessed identifier is added.
3. Web app is a TypeScript App Router app with Tailwind and shadcn/ui configuration, a neutral placeholder landing page, reusable directory structure, and a typed backend API client configured through environment variables.
4. Each application has usable setup/run documentation and secret-free environment examples; the root README covers architecture, prerequisites, initialization, and independent startup.
5. `./init.sh` initializes all three local environments without removing user files.
6. Requested verification commands are executed and results, credentials limitations, and unresolved dependencies are recorded accurately.
7. No hospitality workflow or external service integration is implemented.
8. Progress, feature tracking, and session handoff reflect the verified repository state.

## 11. Risks and Open Questions

- Initializer dependency downloads require package registry network access; this environment's first attempt was blocked by sandbox DNS and required an approved network-enabled retry.
- LiveKit's Google plugin evolves; model compatibility must be checked against the installed version and its documented default behavior.
- The root is missing `.git`, so no clean/dirty working-tree claim, diff review, or commit can be made from this workspace snapshot.
- The architecture document includes future product workflow descriptions; these remain reference-only and outside the approved setup scope.
