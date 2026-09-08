# CycleCare User Manual

CycleCare is a health-tracking application connecting patients with consented doctors. Patients keep control of their health data, and AI-generated suggestions require doctor review before they become approved recommendations.

## Start the application

For local web use, ask the project operator to start the services, then open:

```text
http://127.0.0.1:5500/login.html
```

The web interface requires the Django API and ML service to be running. Do not open the HTML file directly from the filesystem because browser security rules can block API requests.

## Patient workflow

### Create an account

1. Open the login page.
2. Select **Sign Up**.
3. Choose **Patient**.
4. Enter your name, email, and password.
5. Submit the form.
6. Complete age, height, weight, and dietary preference during onboarding.

Passwords are sent over the API and stored on the server only as salted hashes. Never share your password or JWT token.

### Log a cycle

1. Open **Log Cycle Entry** from the patient dashboard.
2. Select start and end dates.
3. Choose flow intensity.
4. Select symptoms.
5. Save the entry.

The server validates the dates and calculates duration and summary statistics.

### Request a craving alternative

1. Open **Craving? Get an Alternative**.
2. Enter a craving such as pizza, chocolate, fries, or burger.
3. Submit the request.

The request is sent to the craving service and the result is saved to your craving history.

### Give a doctor access

1. Open **Manage Doctor Access**.
2. Select **Add Doctor**.
3. Enter the doctor's code.
4. Submit the request.
5. Use the toggle to revoke access later.

Only an active consent grant allows a doctor to view the permitted aggregate dashboard. Revoking consent blocks future doctor dashboard access.

### Wearable data

Health Connect support is prepared for the Android shell. The mobile integration sends daily aggregates rather than continuous sleep or workout sessions. The browser prototype cannot access Health Connect directly.

## Doctor workflow

### Create an account

1. Open the login page.
2. Select **Sign Up**.
3. Choose **Doctor**.
4. Enter your name, email, and password.
5. Complete specialization and years of experience.
6. Keep the generated doctor code available for patients who want to grant access.

### View consented patients

Open **Doctor Dashboard**. Only patients with active consent appear in the list.

### Review the patient summary

Select **View Dashboard** for a patient. The doctor receives aggregate statistics such as average cycle duration, average sleep, and activity totals. Raw cycle logs, raw wearable sessions, food records, body measurements, and dietary schedules are not shown.

### Review AI suggestions

1. Open **Suggestion Center**.
2. Select a consented patient.
3. Review pending AI suggestions.
4. Choose **Approve** or **Dismiss**.
5. Use **Add Custom Suggestion** for a doctor-authored recommendation.

AI suggestions remain pending until a consented doctor approves them. Patients should treat approved suggestions as wellness guidance and consult their doctor for medical decisions.

## Privacy rules

- Never share your password or access token.
- Grant consent only to a doctor you trust.
- Revoke consent when access is no longer needed.
- Raw health records are intended to remain on the phone in the encrypted mobile architecture.
- The current backend enforces consent and exposes only aggregate doctor statistics.
- Alcohol screening output is a non-diagnostic research signal and requires clinician review.

## Troubleshooting

**Login fails:** confirm the backend is running at `http://127.0.0.1:8000` and that the account already exists.

**The page shows a network error:** use the local web server URL instead of opening the HTML file directly.

**A doctor cannot see a patient:** confirm the patient granted consent and has not revoked it.

**Wearable connection does not open on the browser:** Health Connect requires the Android application shell and a configured Android device or emulator.
