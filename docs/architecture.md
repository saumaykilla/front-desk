# Front Desk Agent — Architecture

## 1. Overview

Front Desk Agent is an AI-powered voice assistant for hospitality front-desk operations.

Guests interact with the agent through real-time voice conversations. The initial version focuses on:

- Reservation lookup and guest verification.
- Guest check-in.
- Guest check-out.
- Answering property-related questions.
- Escalating unresolved requests to front-desk staff.

The application consists of three primary components:

1. **Backend:** Python and FastAPI.
2. **Voice Agent:** LiveKit Agents with Google's Gemini Live API through the LiveKit Google plugin, `GOOGLE_API_KEY`, and explicit `v1beta` API version.
3. **Web Application:** Next.js, TypeScript, and shadcn/ui.

Mews is the initial PMS integration and source of truth for reservation and check-in/check-out information.

Payments and access-control integrations such as Seam are explicitly outside the initial scope.

## 2. Technology Stack

| Component             | Technology                            |
| --------------------- | ------------------------------------- |
| Backend               | Python, FastAPI                       |
| Voice infrastructure  | LiveKit                               |
| Voice agent           | LiveKit Agents for Python             |
| AI model              | Google Gemini Live API via `livekit-plugins-google` |
| Frontend              | Next.js, TypeScript                   |
| UI components         | shadcn/ui                             |
| Backend communication | REST APIs                             |
| Voice communication   | LiveKit WebRTC                        |
| PMS                   | Mews                                  |
| Backend testing       | Pytest                                |
| Frontend testing      | To be selected during implementation  |

Exact model identifiers, LiveKit compatibility, and Mews API capabilities must be validated before implementation.

## 3. Repository Structure

```text
front-desk-agent/
│
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── api/
│   │   │   ├── routes/
│   │   │   └── dependencies.py
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   ├── security.py
│   │   │   └── logging.py
│   │   ├── services/
│   │   │   ├── reservation_service.py
│   │   │   ├── guest_verification_service.py
│   │   │   ├── checkin_service.py
│   │   │   ├── checkout_service.py
│   │   │   └── escalation_service.py
│   │   ├── integrations/
│   │   │   └── mews/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── repositories/
│   │   └── utils/
│   ├── tests/
│   ├── requirements.txt
│   └── README.md
│
├── voice-agent/
│   ├── agent.py
│   ├── worker.py
│   ├── session.py
│   ├── tools/
│   │   ├── reservation_tools.py
│   │   ├── checkin_tools.py
│   │   ├── checkout_tools.py
│   │   ├── knowledge_tools.py
│   │   └── escalation_tools.py
│   ├── prompts/
│   │   ├── system.md
│   │   ├── greeting.md
│   │   ├── reservation.md
│   │   ├── checkin.md
│   │   ├── checkout.md
│   │   ├── support.md
│   │   └── escalation.md
│   ├── config/
│   ├── tests/
│   ├── requirements.txt
│   └── README.md
│
├── web/
│   ├── src/
│   │   ├── app/
│   │   ├── components/
│   │   │   ├── ui/
│   │   │   └── shared/
│   │   ├── features/
│   │   ├── hooks/
│   │   ├── lib/
│   │   ├── services/
│   │   └── types/
│   ├── public/
│   ├── tests/
│   └── package.json
│
├── docs/
│   └── architecture.md
│
├── plans/
│   ├── pending/
│   └── approved/
│
├── scripts/
│
├── AGENTS.md
├── feature_list.json
├── progress.md
├── session-handoff.md
├── init.sh
├── .env.example
└── README.md
```

## 4. Component Responsibilities

### 4.1 Backend — FastAPI

The backend owns application business logic and external integrations. It currently exposes process health and an authenticated guest-booking lookup operation; later hospitality workflows remain unimplemented.

Responsibilities:

- Expose REST APIs to the web application.
- Expose authenticated APIs for the voice agent.
- Retrieve and manage reservation information through Mews.
- Verify guest identity.
- Manage check-in and check-out workflows.
- Validate whether a guest can perform a requested operation.
- Retrieve property and operational information.
- Handle exceptions and escalation workflows.
- Maintain operational logs and audit records.

The backend is responsible for enforcing business rules. The LLM must never be the authority for whether a guest is allowed to perform an operation.

### 4.2 Voice Agent — LiveKit

The voice agent handles real-time guest interactions.

Responsibilities:

- Join and manage LiveKit rooms.
- Process incoming and outgoing audio.
- Connect to Google's Gemini Live API directly through the LiveKit Google plugin with `GOOGLE_API_KEY`; the runtime does not fall back to LiveKit Inference.
- Maintain active conversation context.
- Load prompts from `voice-agent/prompts/`.
- Expose callable tools from `voice-agent/tools/`.
- Call backend APIs to perform operational actions.
- Handle interruptions, unclear speech, and confirmation requests.
- Recover gracefully from tool failures.
- Escalate unresolved requests to front-desk staff.

The voice agent coordinates conversations. It does not directly own PMS integrations or critical business logic. Its guest-booking lookup tool receives the selected `nolita` / `nap_york` property from LiveKit job metadata and calls the authenticated backend; Mews credentials remain backend-only.

### 4.3 Web Application — Next.js

The web application provides the staff-facing interface.

Responsibilities:

- Display active and historical guest interactions.
- Allow staff to inspect reservation information and check-in/check-out status.
- Display escalations requiring human attention.
- Provide access to property knowledge and operational information.
- Provide agent configuration and property settings where authorized.
- Display relevant operational errors and activity.

Use shadcn/ui for reusable interface components. Organize application-specific UI inside `web/src/features/`.

## 5. Backend Organization

The backend should separate API handling, business logic, and external integrations.

**API routes**

Handle HTTP requests, authentication dependencies, request validation, and response serialization.

**Services**

Implement business workflows, including reservation lookup, guest verification, check-in, and check-out.

**Integrations**

Contain provider-specific API clients and adapters. The initial integration is Mews.

**Schemas**

Define typed request and response contracts using Pydantic.

**Repositories**

Abstract persistent application data access if and when a database is introduced.

The backend must expose reusable service interfaces rather than duplicating business logic across the web application and voice agent.

## 6. Voice Agent Organization

### Tools

All callable voice-agent tools must live in:

`voice-agent/tools/`

Each tool should have one focused responsibility and a typed input/output contract.

Initial proposed tools (only `find_guest_booking` is currently implemented):

| Tool                    | Responsibility                                  |
| ----------------------- | ----------------------------------------------- |
| `find_guest_booking`   | Locate a current reservation using a confirmed name or booking confirmation/reference number and check-in date |
| `get_guest_reservation` | Retrieve reservation information                |
| `verify_guest`          | Verify the guest's identity                     |
| `get_checkin_status`    | Retrieve check-in status                        |
| `start_checkin`         | Initiate or guide the check-in workflow         |
| `complete_checkin`      | Complete check-in when permitted                |
| `get_checkout_status`   | Retrieve check-out status                       |
| `process_checkout`      | Execute an authorized check-out                 |
| `answer_guest_question` | Answer property-related questions               |
| `escalate_to_frontdesk` | Escalate unresolved requests                    |

These are proposed agent-facing contracts. The actual operations must be mapped to supported Mews capabilities before implementation.

Tools should call the FastAPI backend rather than independently integrating with Mews.

### Prompts

All voice-agent prompts must live in:

`voice-agent/prompts/`

Prompts should be separated by conversational responsibility.

The system prompt defines:

- Agent identity and role.
- Conversation behavior.
- Tool usage expectations.
- Guest verification requirements.
- Privacy requirements.
- Escalation rules.
- Prohibited assumptions and disclosures.

Workflow-specific prompts provide additional context for reservation lookup, check-in, check-out, and guest support.

Prompts guide model behavior. They do not replace backend validation or authorization.

## 7. Communication Architecture

```text
                      Guest
                        |
                        v
                  LiveKit Room
                        |
                        v
                   Voice Agent
                        |
                        v
              Google Real-time Model
                        |
                        v
                   Agent Tools
                        |
                        v
                  FastAPI Backend
                        |
                        v
                  Mews Integration
                        |
                        v
                 Mews PMS


                   Staff / Admin
                        |
                        v
                  Next.js Web
                        |
                        v
                  FastAPI Backend
```

Communication rules:

- Guest audio is handled through LiveKit.
- The voice agent communicates with Google's real-time model.
- Agent tools communicate with FastAPI.
- The web application communicates with FastAPI.
- FastAPI handles Mews operations.
- Sensitive operations must be validated and authorized by the backend.

## 8. Conversation and Business State

The architecture separates temporary conversation state from persistent operational state.

**Voice agent state**

Owns the active conversation context, including:

- Current conversation stage.
- Guest-provided information.
- Pending confirmations.
- Recent tool results.
- Conversation history required by the model.

**Backend state**

Owns authoritative operational information, including:

- Reservation details retrieved from Mews.
- Guest verification results.
- Check-in/check-out operation status.
- Authorization decisions.
- Operation outcomes and audit records.

The voice agent must not treat its conversation history as proof that an operation succeeded.

## 9. Core Business Rules

1. Never disclose reservation details before guest verification.
2. Confirm ambiguous guest names and reservation matches rather than guessing.
3. Verify reservation information against Mews.
4. Never assume check-in or check-out is complete because a guest says it is.
5. Verify operation status through Mews.
6. Do not report success until the backend confirms the operation.
7. Do not repeat potentially non-idempotent operations without checking their status.
8. Handle Mews errors and unavailable services without fabricating results.
9. Escalate when an operation cannot be safely completed.
10. Keep internal operational notes separate from guest-facing information.

## 10. Configuration and Secrets

Each application component should have its own environment configuration.

Backend configuration may include:

- Per-property Mews API URLs, ClientTokens, and AccessTokens for Nolita and Nap York.
- `AGENT_API_TOKEN`, shared with the voice agent as `BACKEND_API_TOKEN`.
- The lookup date timezone, currently `America/New_York` for both properties.
- Database configuration, if introduced.
- Authentication and security settings.

Voice-agent configuration may include:

- LiveKit credentials.
- Google API credentials.
- Backend API URL.
- `BACKEND_API_TOKEN` matching the backend agent token.

Web configuration may include:

- Backend API URL.
- Public application configuration.

Secrets must never be committed to the repository.

The root `.env.example` should document required configuration without containing actual credentials.

## 11. Initial Scope and Exclusions

### Included

- Reservation lookup.
- Guest verification.
- Check-in.
- Check-out.
- Property-related guest questions.
- Front-desk escalation.
- Staff-facing operational interface.

### Excluded from initial scope

- Payment processing or deposit verification.
- Seam integration and digital access credentials.
- Automated room-access code delivery.
- Other PMS integrations.
- Advanced multi-property administration unless required by the initial implementation.

New capabilities must be added through the planning and approval workflow.

## 12. Implementation Principles

- Keep business logic in the FastAPI backend.
- Keep provider-specific code inside integration modules.
- Keep voice-agent tools small and focused.
- Keep prompts separate from application code.
- Use typed request and response schemas.
- Avoid duplicating business logic.
- Do not fabricate results when an integration fails.
- Keep logs useful without unnecessarily storing sensitive guest information.
- Test business rules independently of the LLM.
- Verify Mews capabilities before implementing operations.

## 13. Implementation Sequence

Implementation proceeds one approved feature at a time.

Proposed high-level sequence:

1. Repository and development environment foundation.
2. FastAPI application foundation.
3. LiveKit agent foundation and Google real-time model connection.
4. Voice-agent to backend communication.
5. Mews reservation lookup and guest verification.
6. Check-in workflow.
7. Check-out workflow.
8. Property knowledge and guest support.
9. Next.js staff dashboard.
10. Testing, monitoring, and production readiness.

Each feature requires an approved plan, implementation, verification evidence, and an updated feature tracker before being marked `passing`.
