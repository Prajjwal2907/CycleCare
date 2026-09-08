# PCOD/PCOS Tracker — Feature List

## 1. Overview
A health-tracking app for patients with PCOD/PCOS, recommended and used by doctors as part of patient care. The app connects a **Doctor** and a **Patient**, allowing structured tracking of menstrual, sleep, alcohol, and exercise data, with doctor-reviewed, AI-assisted suggestions.

---

## 2. Account Types

### 2.1 Doctor Account
- Doctor dashboard (no real-time updates by default)
- Dashboard becomes visible only **after patient consent** is given
- Access to Suggestion Center for reviewing/approving/adding suggestions

### 2.2 Patient Account
- Patient interface for daily/cycle-based tracking
- Option to grant/revoke doctor access to dashboard

---

## 3. Onboarding (Patient)
- Login / account creation
- Basic details: **age, weight, height**
- Dietary preference:
  - Vegetarian
  - Non-vegetarian
  - Non-vegetarian, but vegetarian on specific days (custom schedule)

---

## 4. Tracking Modules

### 4.1 Menstrual Cycle (Manual Entry)
- Cycle start date
- Cycle end date
- Flow intensity (e.g., light / normal / heavy)
- Symptom severity (e.g., cramps, other symptoms)
- Total cycle duration (auto-calculated)
- Gap until next cycle (auto-calculated from historical entries)

### 4.2 Sleep (Smartwatch / Health Connect)
- Synced via Health Connect or equivalent smartwatch integration
- Deep sleep duration
- Total sleep duration
- Sleep quality trends over time

### 4.3 Alcohol Consumption (Smartwatch — Vitals-Based)
- Detected/estimated via vitals monitoring (e.g., heart rate, other signals)
- Logged automatically based on vitals patterns

### 4.4 Exercise (Smartwatch)
- Activity/workout tracking via smartwatch
- Duration, intensity, and type of activity (as available from device)

---

## 5. Doctor Dashboard
- Consolidated view of patient's tracked data (cycle, sleep, alcohol, exercise)
- Visible only after patient approval
- Reviewed typically during in-person/follow-up visits

---

## 6. Suggestion Center
- **AI-generated suggestions** based on tracked data, reviewed by the doctor
- Doctor can:
  - Approve AI suggestions
  - Add custom suggestions/reminders (e.g., "drink water at specific times," dietary recommendations)
- Patient receives approved suggestions as reminders/notifications

---

## 7. Craving → Healthier Alternative Feature
- Patient enters a food they're craving (e.g., "pizza")
- App returns a **healthier recipe/alternative** that mimics the same craving in a better-for-you form
- Suggestions respect the patient's dietary preference (veg/non-veg/mixed)

---

## 8. Open Items / To Be Defined
- Consent flow details (how patient grants/revokes doctor access)
- Notification/reminder scheduling system
- AI suggestion generation logic/data sources
- Data privacy & sharing permissions between doctor and patient accounts
