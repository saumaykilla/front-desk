# Booking Reference Number Lookup

## 1. Objective

Extend the guest booking lookup so a guest can provide either the Mews reservation confirmation number or a channel/booking reference number. The guest should not need to know which kind of number they have.

## 2. Scope

Included:

- Keep one guest-facing booking-number input.
- Search Mews reservations by both the Mews reservation number and the channel number.
- Scope both searches to the selected property, requested New York local check-in date, and eligible reservation states.
- Merge duplicate reservation results and preserve the existing `matched`, `no_match`, `ambiguous`, and `unavailable` outcomes.
- Update tool instructions, API contract, tests, docs, feature tracking, progress, and handoff.

Excluded:

- Fuzzy matching or guessing other identifiers.
- Searching every reservation at a property when neither number filter matches.
- Exposing channel/booking reference values or internal reservation identifiers in logs or voice output.
- Reservation changes or identity verification.

## 3. Existing architecture

- `voice-agent/tools/__init__.py` exposes `find_guest_booking` with an optional `confirmation_number` argument.
- `voice-agent/tools/booking_client.py` sends that value to the authenticated backend as `confirmation_number`.
- `backend/app/schemas/guest_booking.py` enforces exactly one of `full_name` and `confirmation_number`.
- `backend/app/integrations/mews/client.py` currently sends a number only through Mews `reservations/getAll` `Numbers`.
- `backend/app/services/guest_booking_service.py` performs date/state/name filtering and de-duplicates reservation candidates.
- The feature is tracked as `BOOKING-001`; its original plan remains approved at `plans/approved/guest-identification-and-booking-lookup.md`.

## 4. Proposed implementation

Retain a single, neutral backend/tool field named `booking_reference` for the guest-supplied number. The voice agent will refer to it as “booking confirmation or reference number.” The backend Mews adapter will issue two separately filtered `reservations/getAll/2023-06-06` requests using the same property credentials, New York arrival interval, and eligible states: one with `Numbers: [booking_reference]` and one with `ChannelNumbers: [booking_reference]`. Separate calls avoid depending on undocumented AND/OR behavior when multiple filters are combined. The service will merge results by Mews reservation ID before customer resolution and outcome selection.

Mews documents `Numbers` as reservation confirmation numbers and `ChannelNumbers` as channel numbers or references, with Booking.com confirmation numbers as an example. [Mews Reservations API](https://docs.mews.com/connector-api/operations/reservations)

## 5. Data and API contracts

The tool and backend request will contain exactly one of:

- `full_name`: guest-confirmed full name; or
- `booking_reference`: non-empty string containing either a Mews reservation confirmation number or a channel/booking reference number.

The request continues to include the trusted `property` and guest-confirmed `check_in_date`. Mews calls use the same property’s `ClientToken`, `AccessToken`, and `Client` body fields. Number lookup sends the value in `Numbers` for one request and `ChannelNumbers` for a second request. Results are de-duplicated on reservation ID and mapped to the existing response outcome contract.

## 6. Implementation steps

1. Replace the guest-facing/tool/backend request field `confirmation_number` with the neutral `booking_reference`; update strict exactly-one-key validation.
2. Update the voice-agent tool description and system prompt to invite either a Mews confirmation number or booking reference number.
3. Extend the Mews adapter to make separately filtered `Numbers` and `ChannelNumbers` searches, using shared date/state/property filters and existing pagination/error handling.
4. Merge results by reservation ID before resolving account and companion names; preserve existing ambiguity and privacy behavior.
5. Update unit tests for each Mews filter, duplicate matches across filters, a reference-only match, no match, ambiguity, and API failures.
6. Update README, architecture documentation, approved-plan linkage/feature tracking as required by the approval workflow.
7. Run backend and voice-agent tests, applicable web checks, and update progress/handoff with evidence.

## 7. Failure handling

- If either Mews search fails, return `unavailable`; do not treat a partial result from only one search as a complete lookup.
- Preserve bounded 429 retry behavior independently for each request.
- If both searches return no results, return `no_match`.
- If both find the same reservation, de-duplicate it and return a single match.
- If the combined result has multiple reservations, return `ambiguous`; never choose the first result.
- Invalid, malformed, unauthorized, timed-out, or unavailable Mews responses remain `unavailable`.

## 8. Security considerations

- Keep using trusted property context and property-specific backend Mews credentials.
- Treat booking references as sensitive guest-provided data; do not log the value, raw Mews payloads, or internal reservation IDs.
- Keep the agent-to-backend bearer authentication unchanged.
- Do not expose reservation details beyond the existing minimal response.

## 9. Testing strategy

- Schema/tool tests verify exactly one of full name and booking reference, trimming/empty rejection, and preserving leading zeroes and punctuation.
- Mocked Mews client tests verify `Numbers` and `ChannelNumbers` are each sent in their own request, with identical property/date/state scoping.
- Service/client tests verify de-duplication when both filters return the same reservation, a match on either filter, combined ambiguity, no match, and unavailable when either request fails.
- Voice-agent tests verify that the neutral booking reference reaches the backend unchanged.
- No live Mews calls are required for unit tests.

## 10. Acceptance criteria

1. A guest can supply either a Mews confirmation number or a channel/booking reference using the same input.
2. The backend searches the `Numbers` and `ChannelNumbers` filters independently for the selected property and confirmed date.
3. Duplicate reservations returned by both filters count as one match.
4. A unique match from either filter returns `matched`; no result from both returns `no_match`; multiple distinct results return `ambiguous`.
5. If either required Mews search fails, the result is `unavailable`, not a partial `matched` or `no_match`.
6. Booking numbers, raw Mews responses, and internal IDs are not logged or spoken.
7. Automated tests and applicable documentation are updated and pass.

## 11. Risks and open questions

- A channel reference may identify more than one reservation within a property/date scope. Existing ambiguity behavior must remain intact.
- Some channel booking references may not be populated in `ChannelNumber`; this feature only supports identifiers that Mews returns through the documented filter.
- This plan assumes “booking reference number” means the Mews reservation `ChannelNumber` value (such as a channel/OTA reference). If the user means a different Mews field, confirm it before implementation.
- A live positive reference-number case is not yet available. Automated tests will prove each filter contract; a live smoke test should be added when a known reference number is supplied.
- This plan intentionally calls both filters on every number lookup. This adds one read-only API request and may increase latency or rate-limit exposure; the existing timeout and retry policy applies to both.
