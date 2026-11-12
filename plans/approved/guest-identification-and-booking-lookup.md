# Guest Identification and Booking Lookup Plan

## 1. Objective

Give the voice agent a reliable way to identify a guest's current Mews reservation at the property selected for the conversation. The agent gathers and confirms the minimum lookup details, calls the backend only when those details are complete, and handles no-match or ambiguous results without guessing.

## 2. Scope

### Included

- Use the property selected by the frontend/session context: `nolita` or `nap_york`.
- Gather either the guest's full name or Mews reservation confirmation number.
- When using a name, read it back and ask the guest to confirm the spelling; if the agent is uncertain, ask the guest to spell it.
- Ask whether check-in is today or on an earlier date, and obtain/confirm the actual check-in date needed to disambiguate the reservation.
- Call a focused voice-agent tool and backend lookup operation only after required information is present and confirmed.
- Select and retrieve the matching current reservation from the property's Mews account.
- Return a minimal, typed result to the agent, with explicit no-match, ambiguous-match, and integration-error outcomes.
- Configure both properties' Mews credentials and platform settings in backend environment variables; keep them server-side.

### Excluded

- Check-in, check-out, payment/deposit, room-access, or reservation-update operations.
- Broader identity authentication or authorization. A name/confirmation number and arrival date locate a booking; they do not alone prove the caller is authorized to receive sensitive reservation details.
- Exposing unrelated reservation fields, guest contact details, payment data, internal notes, or room-access credentials to the voice agent.
- Staff dashboard or frontend changes beyond the already-provided property context.

## 3. Existing Architecture

- `voice-agent/agent.py` loads the system prompt and tools; `voice-agent/tools/` currently registers no tools.
- `voice-agent/prompts/system.md` is currently a placeholder and must be updated only for this approved lookup flow.
- `voice-agent/config/settings.py` holds voice-worker settings, but should not hold Mews credentials.
- `backend/app/main.py` registers only `/health`; backend settings are in `backend/app/core/config.py`.
- `backend/app/integrations/mews/` is an empty adapter package. Backend service, schema, and API route packages are available.
- `backend/app/core/security.py` explicitly has no authentication/authorization implementation. The caller identity/authentication boundary for the agent-to-backend request therefore needs resolution before exposing a guest lookup route.
- The frontend supplies property context to the LiveKit job; the worker will consume the property from trusted LiveKit job metadata rather than asking the model to choose it.
- `docs/architecture.md` assigns PMS integrations and business rules to FastAPI and says voice tools call the backend.

## 4. Proposed Implementation

1. Keep conversation behavior in the voice agent: obtain the property context from trusted job/session metadata, collect one lookup key (full name or confirmation number), confirm the name spelling where applicable, and confirm the check-in date. The model must not choose or change the property itself.
2. Use a typed voice tool such as `find_guest_booking` that accepts exactly one lookup key and the confirmed check-in date. The tool obtains the selected property from trusted LiveKit job metadata, calls FastAPI, and never calls Mews directly.
3. Validate the property against the fixed `nolita` / `nap_york` allowlist in the backend and map it to that property's configured Mews endpoint and credentials. Do not accept a URL, token, service ID, or enterprise ID from the model.
4. Implement a small Mews Connector API client and a reservation lookup service. The current Mews documentation describes POST JSON requests and `reservations/getAll/2023-06-06`; its `Numbers` filter supports a Mews reservation confirmation number, and its scheduled-start interval can scope candidate arrivals. For a name lookup, use a date-scoped reservation set and resolve the associated customer profiles for exact normalized-name comparison. Do not rely on `customers/search` alone: Mews documents it as searching customers active at the moment, which does not cover all future arrivals.
5. Interpret the supplied date in `America/New_York` and convert its start/end boundaries to UTC for Mews. Select a current relevant reservation whose scheduled check-in falls on that date, preferring `Started` or `Confirmed` and excluding cancelled/processed records. If multiple plausible reservations remain, return an ambiguity outcome for the agent to clarify; never select by fuzzy similarity alone.
6. Return only the candidate's guest display name, local scheduled check-in date, reservation state, and an opaque internal reservation identifier if needed for subsequent approved workflows. The agent confirms the match using only information the guest supplied or a minimal name/date confirmation. Do not disclose further reservation information in this feature.

Mews' currently published Connector API authentication guide requires `ClientToken`, `AccessToken`, and `Client` in each request. The user confirmed that the supplied `ClientToken` is the Mews `ClientToken`. Configure per-property `MEWS_NOLITA_CLIENT_TOKEN`, `MEWS_NOLITA_ACCESS_TOKEN`, `MEWS_NAP_YORK_CLIENT_TOKEN`, and `MEWS_NAP_YORK_ACCESS_TOKEN` values so either property's credentials can be independent; never pass credentials through voice-tool arguments. Use the fixed client identifier `Front Desk Agent 0.1.0`.

The voice worker authenticates backend requests using an `Authorization: Bearer` token from `BACKEND_API_TOKEN`; the backend expects the matching `AGENT_API_TOKEN` and rejects lookup requests when it is unset. The property is read from trusted JSON LiveKit job metadata and is not part of the model-visible tool schema. Configure the Mews API base URL independently for each property. New York property-local dates use the IANA timezone `America/New_York` (including daylight-saving transitions).

## 5. Data and API Contracts

### Voice tool input

```json
{
  "full_name": "Jordan Lee",
  "confirmation_number": null,
  "check_in_date": "2026-11-12"
}
```

- Exactly one of `full_name` or `confirmation_number` is required.
- `full_name`: non-empty, guest-confirmed spelling; preserve the original and normalize only for matching.
- `confirmation_number`: non-empty string; preserve leading zeroes and punctuation.
- `check_in_date`: ISO local calendar date confirmed with the guest.

The backend request contract contains the trusted `property` enum (`nolita | nap_york`) plus these lookup fields, but does not accept credentials or endpoint configuration. The worker adds the property from validated job metadata; the backend derives Mews configuration from the enum.

### Backend result

Use a discriminated outcome, for example:

- `matched`: minimal reservation match fields.
- `no_match`: no relevant reservation found for the property and details.
- `ambiguous`: multiple candidates; include only safe name/date choices needed to ask a clarifying question.
- `unavailable`: Mews timed out, rejected credentials, rate-limited, or returned an invalid/unexpected response.

Do not collapse `unavailable` into `no_match`. Validate the Mews response structure before using it. Keep internal Mews IDs and raw payloads out of spoken output and routine logs.

### Mews request shape

The currently published Connector API uses `ClientToken`, `AccessToken`, and `Client` in a JSON POST body. Reservation confirmation numbers are exposed as `Number`; guest names require matching reservations to customer records because the reservation endpoint has no name filter. Use `customers/getAll` filtered by the reservation's `AccountId` and companion customer IDs from `companionships/getAll` filtered by reservation IDs. Request only customer name fields through the smallest supported `Extent`.

## 6. Implementation Steps

1. Configure Mews credentials and API base URLs per property, the agent bearer secret, and property metadata at runtime; validate the enabled Mews operations and exact response shapes against each property's Connector API before a live smoke test.
2. Verify the documented reservation, customer, companionship, and pagination contracts; use reservations filtered by the confirmed `Numbers` value or a one-day `ScheduledStartUtc` interval. For name searches, resolve the reservation owner and linked companions, then fetch only those customer profiles with minimal extents.
3. Add backend settings for per-property Mews credentials and endpoint/configuration, validating required settings without logging secret values.
4. Add typed backend schemas and the allowlisted property-to-configuration mapping.
5. Implement the Mews client with request timeout, response validation, safe error translation, and narrowly scoped reservation/customer requests.
6. Implement deterministic lookup for confirmation number and date-scoped full-name candidate resolution, including property-local date conversion, pagination, state filtering, and ambiguity detection.
7. Add an authenticated backend lookup route using the shared bearer secret; ensure only the selected property's configuration can be used.
8. Add a voice-agent backend client and focused tool; thread trusted property context from LiveKit job metadata into the tool without giving the LLM authority to change it.
9. Update the system/workflow prompt with the required collection sequence, spelling readback/clarification, date confirmation, tool-call preconditions, and safe failure responses.
10. Add tests for service/schema behavior, mocked Mews payloads, API authorization/property scoping, tool input handling, and conversation/tool failure outcomes. Do not make real Mews calls in unit tests.
11. Update secret-free environment examples and integration documentation, then run the relevant backend and voice-agent checks and update progress, feature tracking, and handoff with actual evidence.

## 7. Failure Handling

- Missing/invalid property context: do not call the backend; ask for staff/session recovery or escalate.
- Missing lookup key, unconfirmed name spelling, or missing check-in date: ask one concise follow-up and do not call Mews yet.
- No matches: tell the guest no matching booking was found for the details and invite them to restate the name/number/date; do not suggest another guest's booking.
- Multiple candidates: ask a minimal clarifying question; do not disclose sensitive candidate details or select the first result.
- Timeout/network error/429/5xx: apply bounded retries only where safe, honor `Retry-After` for 429, and return `unavailable` if still failing. Do not report that no booking exists.
- Authentication/authorization failure or malformed response: stop lookup, log a redacted diagnostic, return `unavailable`, and route to staff assistance where available.
- Never retry with the other property's credentials or silently fall back to a different property.

## 8. Security Considerations

- Keep Mews credentials only in backend environment/secrets configuration; separate values for Nolita and Nap York.
- Validate property identifiers server-side and bind each to exactly one configured property. Never let model-generated input choose credentials, an endpoint, or an enterprise.
- Authenticate and authorize the voice-agent-to-backend request with a shared bearer secret before exposing the lookup endpoint; fail closed if it is not configured.
- Treat guest names, confirmation numbers, dates, and Mews payloads as untrusted input/data. Bound input lengths and validate dates.
- Do not log tokens, raw Mews payloads, confirmation numbers, or unnecessary guest personal data. Avoid putting credentials in URLs.
- Treat lookup as candidate location rather than identity proof. A later approved flow must define the verification step before revealing sensitive booking details or performing operations.
- Minimize the response to the voice model and never speak internal IDs or operational notes.

## 9. Testing Strategy

- Unit tests for property allowlisting, exactly-one-lookup-key validation, date/timezone boundaries, name normalization, candidate selection, state filtering, and ambiguous/no-match outcomes.
- Mews-client tests with mocked HTTP responses for success, malformed JSON/schema, timeout, network errors, 401/403, 408, 429 with `Retry-After`, and 5xx.
- Backend route tests for agent authentication, invalid property rejection, per-property credential isolation, request validation, and response minimization.
- Voice-tool tests for missing inputs, spelling confirmation before invocation (where represented in testable workflow state), trusted property propagation, and backend error handling.
- No live Mews calls are required for automated tests. A credentialed sandbox smoke test may be run separately only after the connector configuration is supplied and approved for that environment.
- Run `./init.sh`, backend pytest, voice-agent pytest, and available lint/type/build checks affected by implementation; record exact outcomes.

## 10. Acceptance Criteria

1. The agent does not call lookup until it has the trusted property, one confirmed lookup key, and confirmed check-in date.
2. For name lookup, the agent reads back the name spelling and gets confirmation, or asks the guest to spell it when uncertain.
3. The agent distinguishes check-in today from a prior check-in date and confirms the date used for lookup.
4. The backend rejects invalid property values and selects only that property's configured Mews credentials.
5. Confirmation-number lookup and full-name lookup retrieve only matching current/relevant reservation candidates from the selected property's Mews data.
6. Zero, one, and multiple matches are handled explicitly; no candidate is silently chosen when ambiguous.
7. Mews authentication, timeout, rate-limit, and malformed-response failures are reported as service unavailability, not as no booking found.
8. No Mews credential or raw booking payload is exposed to the voice agent, frontend, or logs.
9. The result contains only minimal lookup/match information and does not claim that the guest has been authenticated for sensitive actions.
10. Tests, documentation, feature tracking, progress, and handoff are updated with actual verification evidence.

## 11. Risks and Open Questions

1. **Credential availability:** Real per-property tokens, Connector API base URLs, and the shared backend/agent secret must be supplied through runtime environment configuration before live calls can be made.
2. **Name-match behavior:** Exact normalized full-name matching includes the reservation owner and Mews-linked companions. A booker who is not linked to the reservation is not treated as a guest match; ambiguous cases are clarified instead of fuzzily selected.
3. Mews access is not available locally; implementation can validate schemas with mocks, but a live smoke test remains dependent on runtime secrets and property permissions.
