# CycleCare — Build Roadmap

Stack reference: **app/** (Capacitor-wrapped mobile frontend) · **backend/** (Django + DRF + PostgreSQL) · **ml-service/** (FastAPI)

Each phase is scoped to one cohesive slice of functionality, touches one existing frontend page (or adds a new one), and should end with that slice actually working end-to-end on a device — not just backend endpoints in isolation.

---

## Phase 0 — Foundation *(in progress)*
Get the three services able to talk to each other before any feature work starts.

- [x] Monorepo restructure: `app/`, `backend/`, `ml-service/`, `docs/`
- [x] Existing frontend moved into `app/www`, history preserved
- [x] Root `.gitignore` and `README.md`
- [ ] Django project scaffolded (`backend/`), PostgreSQL connected
- [ ] FastAPI project scaffolded (`ml-service/`)
- [ ] Capacitor initialized around `app/www`, builds and runs on a simulator unchanged
- [ ] `.env` config per service, local dev ports agreed
- [ ] End-to-end "hello world" check: app → backend → ml-service all reachable

---

## Phase 1 — Auth & Onboarding
*Touches: `login.html`, `onboarding.html`*

- User model with role (`patient` / `doctor`), JWT-based auth (access + refresh)
- Signup / login / token-refresh endpoints
- Patient profile: age, weight, height, dietary preference (veg / non-veg / mixed schedule)
- Doctor profile: specialization, years of experience
- Password hashing, basic input validation server-side (not just client-side like today)
- Wire `login.js` and `onboarding.js` to real endpoints, replacing the current fake `setTimeout` success states

**Done when:** a real account can be created, logged into, and routed to the correct onboarding flow by role — persisted in Postgres, not just local page state.

---

## Phase 2 — Cycle Tracking
*Touches: `cycle-tracker.html`*

- `CycleEntry` model: start date, end date, flow intensity, symptoms, patient reference
- CRUD endpoints; duration and gap-to-next-cycle computed server-side (not just in the browser)
- Simple rule-based next-cycle prediction to start (rolling average of past cycles) — real ML prediction comes later in Phase 7
- Wire `cycle-tracker.js` to persist entries and pull real history

**Done when:** a patient's cycle history survives app restarts and syncs across devices.

---

## Phase 3 — Doctor–Patient Consent System
*Touches: `consent.html`, `doctor-dashboard.html`*

- `ConsentGrant` model: patient, doctor, status (pending / active / revoked), timestamps
- Grant / revoke / request-by-code endpoints
- Access-control enforced **server-side** on every doctor-facing endpoint — a doctor querying a patient without an active grant gets a 403, regardless of what the UI shows
- Doctor dashboard: list of consented patients only, expandable detail view pulling real tracked data
- Audit log entry on every grant, revoke, and doctor data access (needed for health-data accountability)

**Done when:** access genuinely follows consent state — verified by trying to view a patient's data as a doctor *before* consent is granted and confirming it's blocked.

---

## Phase 4 — Wearable & Health Data Integration
*Touches: `dashboard.html`*

- Capacitor Health Connect plugin (Android) — sleep, exercise data
- Capacitor HealthKit plugin (iOS), noting boAt Wave device parity may lag on iOS
- `SleepData` / `ExerciseData` models + sync endpoint (background or on-open sync)
- Wire the dashboard's "Connect" buttons to real device permission flows and live data, replacing the current hardcoded "7h 20m" placeholder
- Alcohol tracking: stub the endpoint now, real vitals-based detection deferred to Phase 7 (needs a trained model)

**Done when:** real step/sleep/exercise data from a connected device shows up on the dashboard.

---

## Phase 5 — Suggestion Center (doctor-authored first)
*Touches: `suggestion-center.html`*

- `Suggestion` model: source (`ai` / `doctor`), status (pending / approved / dismissed), text, patient/doctor references
- Approve / dismiss / create-custom endpoints
- Wire `suggestion-center.js` so approved/custom suggestions actually reach the patient (not just a local DOM update)
- **Deliberately AI-suggestion-free in this phase** — ship the review/approval workflow with doctor-authored suggestions only, so it's usable before the ML side exists

**Done when:** a doctor can write a suggestion and the patient receives it as a real notification (ties into Phase 9).

---

## Phase 6 — Craving → Healthier Alternative (first ML integration)
*Touches: `craving.html`*

- First real `ml-service` endpoint — good low-risk phase to prove the backend ↔ ml-service call path
- Start by porting the existing rule-based matching (pizza/chocolate/fries/burger → alternative) into `ml-service`, called via `backend`
- `CravingLog` model to store requests/results — this log becomes training signal later if you want to move past rule-based matching
- Wire `craving.js` to the real pipeline

**Done when:** the craving feature works exactly as it does today, but the logic lives server-side and every request is logged.

---

## Phase 7 — Predictive & Generative Models
*No new frontend page — upgrades what Phases 2, 4, and 5 already shipped*

- Cycle-length prediction model replacing the Phase 2 rolling-average placeholder
- AI-suggestion generator: reads cycle + wearable trends, writes into the `Suggestion` model as `source: ai`, `status: pending` — flows straight into the Phase 5 doctor-review workflow, no new UI needed
- Food-image recognition model (photo → nutrition estimate) — new capability, will need a small upload UI addition in a later phase
- Alcohol-from-vitals classifier, completing the Phase 4 stub

**Done when:** the Suggestion Center starts showing AI-drafted suggestions alongside doctor-authored ones, and cycle predictions are noticeably better than a flat 28-day guess.

---

## Phase 8 — In-App AI Assistant
*New frontend page: a chat/assistant screen*

- LLM-backed assistant (e.g. Claude API) using tool-calling — tools map directly to existing backend endpoints (`get_cycle_history`, `log_symptom`, `suggest_recipe`, `get_wearable_summary`, `request_doctor_review`)
- Conversation history storage per patient
- Guardrails: wellness support only, no diagnostic claims, defers to doctor-reviewed suggestions for anything medical
- New chat screen added to the app

**Done when:** a patient can ask something like "what should I eat instead of the thing I'm craving" or "how's my cycle trending" in plain language and get an answer grounded in their real data.

---

## Phase 9 — Notifications & Reminders
*Cross-cutting — activates delivery for Phases 5, 7, and 8*

- Firebase Cloud Messaging wired into `app/`
- Reminder scheduling for approved suggestions
- Notification preferences (quiet hours, categories)

**Done when:** an approved suggestion or reminder actually reaches the device, not just the in-app suggestion list.

---

## Phase 10 — Security, Polish & Store Readiness
- Encryption at rest/in transit review, secrets audit
- Full audit-log review for doctor data access
- Mobile UX pass on the existing CSS: touch targets, safe-area insets, native-feeling transitions
- App icons, splash screens, store listing assets
- Manual QA pass across both patient and doctor roles
- Privacy policy / consent language finalized for health data
- App Store / Play Store submission

---

## Phase 11 — Scale & Ops *(post-launch)*
- CI/CD pipeline
- Containerization for consistent dev/deploy environments
- Production monitoring and logging
- Revisit architecture if patient/doctor volume grows meaningfully

---

### How to use this doc
Check off items as they land, and don't start a phase's frontend wiring until that phase's backend/ml-service endpoints exist — each phase is meant to leave the app in a genuinely working state, not a half-wired one.
