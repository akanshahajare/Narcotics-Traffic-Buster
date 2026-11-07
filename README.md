# Narcotics Traffic Buster — AI-Powered Monitoring Application

A responsive, installable web application and Android-wrapper starter for authorized incident reporting, evidence integrity checks, GPS-tagged submissions, geospatial visualization and administrator case review.

> **Important scope and safety note:** This repository is a functional reporting/case-management prototype. It does not continuously track people, identify suspects, infer criminality, or automatically make law-enforcement decisions. GPS is collected only when a signed-in reporter explicitly presses **Capture GPS**. Reports and map pins are based on user-submitted information. No trained narcotics-recognition model is bundled; do not describe AI detection as implemented until a validated model is separately integrated and evaluated.

## Features implemented

- Responsive interface for desktop, laptop, tablet and mobile.
- Customer registration, sign-in and personal report history.
- Separate administrator role and admin-only case review dashboard.
- Incident report submission with category and narrative.
- Optional camera/photo upload (`capture="environment"` on supported phones).
- Explicit, permission-based GPS capture with latitude, longitude and accuracy.
- Leaflet/OpenStreetMap location preview and Google Maps directions link.
- Evidence SHA-256 digest generated server-side and stored with the report.
- Admin status workflow: Submitted, Under review, Verified, Closed, Rejected.
- SQLite database for local development; persistent disk recommended for deployment.
- PWA manifest and service worker for installable mobile/desktop web experience.
- Capacitor Android wrapper source to package the deployed web application.

## Stack

- Backend: Python 3, Flask, SQLite, Werkzeug password hashing, Gunicorn.
- Frontend: HTML, CSS, JavaScript, Leaflet maps.
- Mobile delivery: Progressive Web App + Capacitor Android wrapper.

## Run locally (Windows)

1. Install Python 3.10 or newer.
2. Extract this repository and open a terminal in the project folder.
3. Create a virtual environment:

   ```powershell
   py -m venv .venv
   .venv\Scripts\Activate.ps1
   ```

4. Install dependencies:

   ```powershell
   pip install -r requirements.txt
   ```

5. Copy `.env.example` to `.env`. Set a strong `SECRET_KEY`, `ADMIN_EMAIL` and `ADMIN_PASSWORD` (at least 12 characters) before starting. Startup will stop if the admin credentials are missing or too short. Example PowerShell commands:

   ```powershell
   Copy-Item .env.example .env
   ```

   Edit `.env` with your own values. The administrator account is created on first database initialization. If the database already exists, changing `ADMIN_PASSWORD` does not reset an existing account password.

6. Start the server:

   ```powershell
   python app.py
   ```

7. Open `http://127.0.0.1:5000`.
   - Register a normal customer account through **Create reporter account**.
   - Sign in as the administrator using the credentials configured in `.env`.

For phone testing on the same Wi-Fi, run the server on `0.0.0.0` (already configured) and open `http://YOUR-COMPUTER-LAN-IP:5000` on the phone. Browser geolocation generally requires HTTPS or localhost; use a trusted HTTPS deployment to test GPS on other devices.

## Deploy to Render

1. Create a GitHub repository and push the project (see GitHub steps below).
2. In Render, choose **New → Blueprint** and connect the GitHub repository. Render reads `render.yaml`.
3. Set `ADMIN_EMAIL` and `ADMIN_PASSWORD` in the Render service environment. Set a strong `SECRET_KEY` if overriding the generated value.
4. Deploy and wait for the service to become live.
5. Open the HTTPS Render URL and test registration, admin login, report submission and photo viewing.
6. The included Render configuration mounts a persistent disk at `instance/`; keep this disk for SQLite and uploaded evidence. A persistent disk may require a paid Render plan. Do not deploy a database-backed production system on an ephemeral filesystem.

## Install as an app (PWA)

1. Deploy the app to an HTTPS domain.
2. Open the URL in Chrome on Android, or a supported browser on desktop.
3. Use the browser menu → **Install app** / **Add to Home screen**.
4. Open the installed app from its icon. PWA support depends on browser/platform.

## Build a native Android APK (Capacitor)

An APK is **not included in this source archive**. APK compilation requires the Android SDK, Android Studio/Gradle and a deployed HTTPS backend; those build prerequisites are not present in this build environment. The Android wrapper source is provided below so you can build it on a computer with Android Studio.

1. Deploy the Flask application and copy its HTTPS URL.
2. Install Node.js 20+ and Android Studio (including Android SDK + platform tools).
3. Open a terminal in `android-wrapper/`.
4. Edit `capacitor.config.ts`: replace `https://REPLACE-WITH-YOUR-DEPLOYED-DOMAIN` with your real HTTPS URL. Also replace the URL in `www/index.html`.
5. Run:

   ```bash
   npm install
   npx cap add android
   npx cap sync android
   npx cap open android
   ```

6. In Android Studio, allow Gradle sync and install any requested SDK components.
7. For a test APK, use **Build → Build Bundle(s) / APK(s) → Build APK(s)**. Android Studio displays the generated APK location, normally `android/app/build/outputs/apk/debug/app-debug.apk`.
8. For release distribution, create a signed APK/AAB using **Build → Generate Signed Bundle / APK**. Protect your signing key and do not commit it to GitHub.

The native wrapper loads the deployed HTTPS app, so the backend must remain reachable for login, reports and evidence. The PWA remains the primary cross-platform app experience.

## GitHub upload — step by step

1. Sign in to GitHub and click **New repository**.
2. Name it `narcotics-traffic-buster` and choose Public or Private. Do not initialize it with a README (this folder already contains one).
3. Extract this ZIP on your computer.
4. Open a terminal in the extracted `narcotics-traffic-buster` folder.
5. Run the following commands, replacing the URL with your repository URL:

   ```bash
   git init
   git add .
   git commit -m "Build Narcotics Traffic Buster monitoring application"
   git branch -M main
   git remote add origin https://github.com/YOUR-USERNAME/narcotics-traffic-buster.git
   git push -u origin main
   ```

6. Refresh the GitHub repository page and confirm the files are present.
7. Never upload `.env`, real evidence photos, `instance/`, database files, passwords or Android signing keys. `.gitignore` excludes the local data directory and secrets file.

## API overview

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/health` | Service health |
| POST | `/api/register` | Customer registration |
| POST | `/api/login` | Sign in |
| POST | `/api/logout` | Sign out |
| GET | `/api/me` | Current session |
| POST | `/api/reports` | Submit report (multipart form) |
| GET | `/api/reports` | Own reports; all reports for admin |
| PATCH | `/api/reports/<id>` | Admin status/note update |
| GET | `/api/evidence/<id>` | Authorized evidence access |
| GET | `/api/stats` | Admin dashboard counts |

## Evidence integrity and limitations

The server computes a SHA-256 digest of each uploaded image and stores it alongside the report. This can help detect whether the stored file later changes. It does **not** prove when, where, by whom or under what circumstances a photo was taken; browser-provided GPS/time can be inaccurate or manipulated. A production evidentiary chain requires authenticated capture, trusted time, access audit logs, retention controls, encryption, backups and legal/policy review.

## Production hardening checklist

- Use HTTPS and a strong randomly generated `SECRET_KEY`.
- Change the seeded admin credentials immediately and restrict admin account creation.
- Add CSRF protection, rate limiting, account recovery and MFA before public production use.
- Use managed PostgreSQL/object storage for multi-instance deployments; SQLite/local uploads are suitable only for a small single-instance prototype with persistent disk.
- Add audit logging, retention/deletion policies, encryption at rest and backups.
- Validate file contents/MIME signatures, malware-scan uploads and set stricter upload limits.
- Add a validated, independently evaluated computer-vision model only for bounded assistance (for example, image-quality triage); keep human review and never use model output alone to identify people or determine guilt.
- Obtain legal, privacy, security and operational approval before collecting real-world reports.

## Project structure

```text
narcotics-traffic-buster/
├── app.py
├── requirements.txt
├── .env.example
├── Procfile
├── render.yaml
├── README.md
├── manifest.json
├── sw.js
├── templates/index.html
├── static/app.js
├── static/style.css
├── static/icon.svg
└── android-wrapper/
    ├── package.json
    ├── capacitor.config.ts
    └── www/index.html
```
