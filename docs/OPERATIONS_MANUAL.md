# CycleCare Operations Manual

This manual is for developers and operators running CycleCare locally or preparing a deployment.

## Repository services

- `app/www`: static web frontend
- `backend`: Django REST API
- `ml-service`: FastAPI craving, cycle, suggestion, and alcohol-screening service
- PostgreSQL: Docker database for the containerized stack

## Local prerequisites

- Windows PowerShell, macOS shell, or Linux shell
- Python 3.11 recommended for the ML training pipeline
- Python 3.x for Django
- Node.js and npm for the Capacitor wrapper
- Docker Desktop for the full container stack

## Fastest local start

From the repository root:

```powershell
.\backend\venv\Scripts\python.exe .\start_cyclecare.py
```

The launcher starts:

- Frontend: `http://127.0.0.1:5500/login.html`
- Backend API: `http://127.0.0.1:8000`
- Swagger UI: `http://127.0.0.1:8000/api/docs/`
- ML health endpoint: `http://127.0.0.1:8001/health/`

Press `Ctrl+C` in the launcher terminal to stop all three services.

If the repository virtual environment does not exist, create one and install backend dependencies:

```powershell
py -3.11 -m venv backend\venv
.\backend\venv\Scripts\python.exe -m pip install -r backend\requirements.txt
```

## Start services separately

```powershell
python -m http.server 5500 --directory app/www

.\backend\venv\Scripts\python.exe backend\manage.py runserver 127.0.0.1:8000

py -3.11 -m uvicorn main:app --app-dir ml-service --host 127.0.0.1 --port 8001
```

Use the Python interpreter that has the ML service dependencies installed for the ML command.

## Environment configuration

For Docker, create a local environment file:

```powershell
Copy-Item .env.example .env
```

Replace the placeholder values in `.env`, especially `SECRET_KEY` and `POSTGRES_PASSWORD`. The `.env` file is ignored by Git and must never be committed.

For local non-Docker development, Django uses SQLite when `DATABASE_URL` is absent. The local development secret is generated ephemerally when `SECRET_KEY` is absent. Production requires an explicit `SECRET_KEY` and PostgreSQL URL.

## Docker start

After creating `.env`:

```powershell
docker compose up --build
```

The services are exposed at the same URLs as the local launcher. Stop them with:

```powershell
docker compose down
```

To remove the development database volume as well:

```powershell
docker compose down -v
```

The volume removal permanently deletes the local Docker database.

## Database operations

Run Django commands from the repository root:

```powershell
.\backend\venv\Scripts\python.exe backend\manage.py migrate
.\backend\venv\Scripts\python.exe backend\manage.py check
.\backend\venv\Scripts\python.exe backend\manage.py makemigrations --check --dry-run
```

Local SQLite is stored at `backend/db.sqlite3` and is ignored by Git. Docker PostgreSQL is stored in the `postgres_data` Docker volume.

## Tests

```powershell
.\backend\venv\Scripts\python.exe backend\manage.py test accounts cycles wearables nutrition suggestions doctors
```

The suite covers authentication, consent, cycle tracking, wearable aggregation, suggestions, and doctor privacy boundaries.

## Train the research alcohol model

The available CSV has 991,346 general health-screening rows with a `DRK_YN` label. It does not represent a clinical CycleCare cohort.

Use Python 3.11 or newer with binary wheels:

```powershell
py -3.11 -m pip install -r ml-service\requirements.txt
py -3.11 ml-service\train_alcohol_model.py
```

The model and metrics are written to `ml-service/artifacts/`, which is ignored by Git. The endpoint is:

```text
POST http://127.0.0.1:8001/api/v1/predict-alcohol/
```

Its output is a non-diagnostic screening signal. Do not use it as a diagnosis or clinical decision system.

## Android and Health Connect

The Kotlin integration is at:

```text
app/android/src/main/java/com/cyclecare/healthconnect/HealthConnectFetcher.kt
```

Setup requirements and permissions are documented in [app/android/README.md](../app/android/README.md). Health Connect requires an initialized Android/Capacitor project, Android SDK, and a device or emulator with Health Connect available.

The fetcher aggregates sleep and workout sessions by day before sending them to `/api/wearables/sync/`. It does not upload continuous session timelines.

## Capacitor web compatibility

The web frontend remains in `app/www` and can still be served with Python. Capacitor uses the same directory as its `webDir`, so web testing and Android packaging share the same HTML, CSS, and JavaScript files.

From `app/`:

```powershell
npm install
npx cap sync
npx cap open android
```

Android Studio and the Android SDK are required to build or run the native shell.

## Security checklist before deployment

- Set a strong unique `SECRET_KEY`.
- Set a strong unique PostgreSQL password.
- Use HTTPS for the API and ML service.
- Set `DJANGO_ENV=prod` and `DEBUG=False`.
- Configure strict `ALLOWED_HOSTS` and `CORS_ALLOWED_ORIGINS`.
- Use encrypted PostgreSQL storage and encrypted backups.
- Use secure native token storage in Android instead of browser `localStorage`.
- Rotate credentials if they ever appeared in shared Git history.
- Confirm revoked consent returns `403`.
- Confirm doctor responses contain aggregate fields only.
