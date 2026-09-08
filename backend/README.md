# CycleCare Backend API

The core REST API service for **CycleCare**, a health-tracking platform for patients with PCOD/PCOS managed under doctor supervision.

Built with **Django 6.1**, **Django REST Framework (DRF)**, **PostgreSQL**, and documented with **OpenAPI 3.0 / drf-spectacular**.

---

## 🏛 Architecture & Domain Apps

The backend follows an app-per-domain modular architecture:

- **`core/`**: Abstract base models (`TimeStampedModel`), reusable permission classes (`IsPatient`, `IsDoctor`, `HasActiveConsent`), standard pagination, custom exception handling, and the `MLServiceClient` for interacting with the external FastAPI `ml-service`.
- **`accounts/`**: Unified `User` model (`patient` / `doctor`), `PatientProfile` (age, height, weight, dietary preferences schedule), `DoctorProfile` (specialization, unique doctor code), and auditable `ConsentGrant` records.
- **`cycles/`**: Menstrual cycle tracking (`CycleEntry`) with server-computed cycle duration, rolling average predictions, symptom tracking, and historical summary endpoint.
- **`wearables/`**: Smartwatch data ingestion (sleep duration/stages, vitals-based alcohol consumption signals, workout sessions). Features a provider-agnostic adapter layer (boAt Wave, Google Health Connect, Apple HealthKit) and idempotent upserts.
- **`nutrition/`**: Healthy craving alternatives (`CravingRequest`) respecting patient dietary preferences (veg, non-veg, mixed schedule). Food-image recognition is intentionally out of scope.
- **`suggestions/`**: Suggestion Center supporting AI-generated recommendations (pending doctor review), doctor approval/editing workflows, and doctor-authored custom reminders.
- **`doctors/`**: Doctor dashboard endpoints returning only active consented patients and consolidated medical views.
- **`ml-service/`**: FastAPI service exposing craving alternatives, cycle prediction, suggestion generation, and a research alcohol-screening model. The alcohol model is not diagnostic.

---

## 🚀 Getting Started

### 1. Prerequisites

- Python 3.10+ (tested up through Python 3.14)
- PostgreSQL 14+ (or SQLite automatically in local dev mode)
- `pip` or virtual environment manager

### 2. Environment Setup

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

Key environment variables:

| Variable | Description | Default |
| :--- | :--- | :--- |
| `DJANGO_ENV` | Environment mode (`dev` or `prod`) | `dev` |
| `DEBUG` | Enable debug mode | `True` |
| `SECRET_KEY` | Django secret key | Required in Docker/production; generated ephemerally for local dev |
| `DATABASE_URL` | PostgreSQL connection URL | If unset, falls back to SQLite `db.sqlite3` in dev |
| `ML_SERVICE_URL` | Internal URL for `ml-service` | `http://localhost:8001` |
| `ALLOWED_HOSTS` | Comma-separated allowed hostnames | `127.0.0.1,localhost,testserver` |
| `CORS_ALLOWED_ORIGINS`| Allowed origins for web & mobile | `http://localhost:3000,http://localhost:8100,capacitor://localhost` |

### 3. Install Dependencies

```bash
# In backend/ directory:
python -m venv venv

# Windows:
.\venv\Scripts\activate
# Linux / macOS:
source venv/bin/activate

pip install -r requirements.txt
```

In a second terminal, start the local ML service:

```bash
cd ml-service
pip install -r requirements.txt
uvicorn main:app --reload --port 8001
```

The ML health check is available at `http://localhost:8001/health/`.

### 4. Database Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### 5. Run the Local Development Server

```bash
python manage.py runserver 0.0.0.0:8000
```

The API will be live at `http://localhost:8000`.

### Train the research alcohol model

The repository includes a general health-screening CSV with the `DRK_YN` label. Use Python 3.11 or newer with binary wheels available:

```bash
py -3.11 -m pip install -r ml-service/requirements.txt
py -3.11 ml-service/train_alcohol_model.py
```

This writes an ignored artifact to `ml-service/artifacts/` and metrics beside it. The model is exposed at `POST /api/v1/predict-alcohol/` and returns a non-diagnostic screening signal. It must not be used to diagnose alcohol-use disorder or make clinical decisions without clinician validation.

---

## 📖 API Documentation & Swagger UI

Interactive OpenAPI 3.0 documentation is auto-generated via `drf-spectacular`:

- **Swagger UI**: [http://localhost:8000/api/docs/](http://localhost:8000/api/docs/)
- **ReDoc**: [http://localhost:8000/api/redoc/](http://localhost:8000/api/redoc/)
- **OpenAPI Schema (YAML/JSON)**: [http://localhost:8000/api/schema/](http://localhost:8000/api/schema/)

---

## 🧪 Running Automated Tests

Run the complete test suite across all apps:

```bash
python manage.py test accounts cycles wearables nutrition suggestions doctors
```

Or run individual apps:

```bash
python manage.py test accounts
python manage.py test cycles
python manage.py test wearables
python manage.py test nutrition
python manage.py test suggestions
python manage.py test doctors
```

---

## 🐳 Docker Deployment

To launch the full backend stack (Django API + PostgreSQL 16 + FastAPI ML-Service) using Docker Compose:

```bash
# From project root:
docker compose up --build
```

- **Backend API**: `http://localhost:8000`
- **Postgres Database**: `localhost:5432`
- **ML Service**: `http://localhost:8001`

---

## 🔒 Security & Consent Architecture

- **Append-Only Consent Grants**: Revoking consent timestamps `revoked_at` and marks `is_active=False` without destroying historical audit logs.
- **`HasActiveConsent` Permission**: Checked on every doctor access endpoint to protect patient health records.
- **Git Security**: `.gitignore` strictly rejects secrets (`.env*`), private keys (`*.pem`, `*.key`), and SQLite files.
