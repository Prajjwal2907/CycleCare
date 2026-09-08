# CycleCare Privacy and Data Architecture

## Current deployment

Local development uses SQLite at `backend/db.sqlite3` when `DATABASE_URL` is not set. Docker uses PostgreSQL in the `db` container, persisted in the `postgres_data` Docker volume. Production is configured for PostgreSQL through `DATABASE_URL`; a hosted production database still needs to be provisioned.

Django stores passwords using salted password hashes. Passwords are never stored in plaintext.

## Intended data split

The server stores only what is required for identity, authorization, consent, and doctor review:

- Account email, role, display name, and hashed password
- JWT authentication state and refresh-token handling
- Patient-doctor consent grants and revocation history
- Doctor-authored suggestions and AI drafts awaiting doctor review
- Privacy-safe aggregate statistics explicitly approved for sharing

The phone should retain raw personal health data locally:

- Individual cycle logs and symptoms
- Detailed sleep and exercise records
- Alcohol-related device signals
- Local craving history and unsent health data
- Local assistant history and unsent data

Raw health records must be stored in an encrypted mobile database. Android implementations should use Room with SQLCipher or an equivalent encrypted database, with encryption keys held by Android Keystore. Authentication tokens should use encrypted preferences or secure native storage, never browser `localStorage` in a production mobile build.

## Doctor access contract

1. A patient explicitly grants a doctor access.
2. The backend verifies an active consent grant on every doctor-facing request.
3. The phone computes the minimum statistics needed for care.
4. Only those aggregate statistics are uploaded.
5. The doctor receives aggregate cycle, sleep, exercise, and alcohol statistics.
6. Raw records, continuous sessions, body measurements, and dietary schedules are not returned to doctors.
7. AI-generated suggestions remain pending until the consented doctor approves or rejects them.

The current backend doctor dashboard implements the aggregate-only response contract. Wearable ingestion collapses same-day sleep and exercise sessions before persistence. The Android Health Connect fetcher also aggregates records before upload.

## ML privacy rules

ML services must receive aggregate statistics rather than raw health records. The current suggestion-generation path sends cycle, sleep, exercise, nutrition-count, and alcohol-count/confidence summaries only.

The repository's CSV can train an alcohol-use classification prototype, but it is a general health-screening dataset and is not a CycleCare clinical dataset. It must not be presented as a diagnosis, alcohol-use-disorder assessment, or PCOS model. A production model requires representative, consented, clinically governed CycleCare data and validation.

## Retention and security checklist

Before production release:

- Use PostgreSQL over TLS with encrypted backups.
- Replace localStorage tokens with secure native storage in the Capacitor Android shell.
- Add server-side retention and deletion policies.
- Log consent changes and doctor access without logging raw health payloads.
- Use HTTPS only, rotate secrets, and configure strict CORS and CSRF settings.
- Test that revoked consent returns `403` and that doctor responses contain no raw-record fields.
