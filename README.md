# CycleCare

A health-tracking app for patients with PCOD/PCOS, recommended and used by doctors as part of patient care. CycleCare connects a **Patient** and a **Doctor**, enabling structured tracking of menstrual cycle, sleep, alcohol, and exercise data, alongside doctor-reviewed, AI-assisted suggestions and personalized nutrition guidance.

## Project Structure

This repo is a monorepo containing three services plus shared docs:

```
cyclecare/
├── app/          # Mobile app frontend (Capacitor)
├── backend/      # Core API (Django + DRF + PostgreSQL)
├── ml-service/   # AI/ML microservice (FastAPI)
└── docs/         # Product and feature specs
```

- **`app/`** — The CycleCare mobile app, wrapped natively via [Capacitor](https://capacitorjs.com/). The web UI (HTML/CSS/JS) lives in `app/www`, alongside the generated native Android and iOS project shells.
- **`backend/`** — Core API server built with **Django + Django REST Framework**, backed by **PostgreSQL**. Handles authentication, onboarding, cycle tracking, consent management, doctor dashboards, and the suggestion center.
- **`ml-service/`** — AI/ML microservice built with **FastAPI**. Hosts cycle-length prediction, the craving → healthier-alternative engine, and the AI-suggestion generator consumed by the backend's Suggestion Center.
- **`docs/`** — Product overview and feature specs for the platform.

## Prerequisites

| Service | Requires |
|---|---|
| `app/` | Node.js + npm, Capacitor CLI |
| `backend/` | Python 3.x, PostgreSQL |
| `ml-service/` | Python 3.x |

## Getting Started

For a complete local stack, run `docker compose up --build` from the repository root. The backend API is available at `http://localhost:8000`, the OpenAPI UI at `http://localhost:8000/api/docs/`, and the ML service health check at `http://localhost:8001/health/`.

Backend-specific setup, environment variables, tests, and API details are documented in [backend/README.md](backend/README.md).

## Manuals

- [User Manual](docs/USER_MANUAL.md) — patient and doctor workflows, consent, suggestions, and troubleshooting.
- [Operations Manual](docs/OPERATIONS_MANUAL.md) — local startup, Docker, database, tests, ML training, and Android setup.
- [Privacy and Data Architecture](docs/privacy-data-architecture.md) — storage boundaries and security requirements.

## Status

🚧 Actively under development — currently scaffolding project structure and core services.

## Team

- Backend / ML
- Frontend / Mobile (JS)