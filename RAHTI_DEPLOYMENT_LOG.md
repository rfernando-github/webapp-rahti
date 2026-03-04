# CardioRisk Predictor — Rahti Deployment Log

This document records the full deployment journey of the CardioRisk Predictor Flask app to CSC Rahti, including issues encountered and how they were resolved.

---

## Live URL

**https://webapp-rahti-git-cardiorisk2.2.rahtiapp.fi/**

---

## Timeline

### 1. GitHub Repository Setup

Pushed the Rahti-ready webapp to GitHub:

```bash
cd webapp-rahti
git init
git add .
git commit -m "CardioRisk Predictor for Rahti"
git branch -M main
git remote add origin https://github.com/rfernando-github/webapp-rahti.git
git push -u origin main
```

**Repository:** https://github.com/rfernando-github/webapp-rahti

---

### 2. CSC Account & Project Setup

1. Logged into https://my.csc.fi with University of Oulu Haka credentials
2. Created a new CSC project:
   - **Project number:** 2018066
   - **Title:** cardiorisk
   - **Type:** Academic
   - **Home organization:** University of Oulu
   - **Lifetime:** 25.02.2026 – 25.02.2027
3. Activated **Rahti Container Cloud** service under the project
4. Selected **Base** cloud resource package (3,000 BU)

---

### 3. Issue: "Could not find user" on Rahti Login

**Problem:** After activating Rahti, logging into https://rahti.csc.fi showed "Could not find user" (OKD error).

**Cause:** Two things needed to happen first:
- **MFA (Multi-Factor Authentication)** is required since November 2025
- Account propagation can take **a few hours** after service activation

**Solution:** Enabled MFA on the CSC account and waited. Login worked after a short delay.

---

### 4. Creating the Rahti OpenShift Project

**Problem:** Creating a project with a plain description failed:
```
admission webhook "project.admission.webhook" denied the request:
Please make sure that the project description conforms to the required format
(e.g., csc_project: 1000123)
```

**Solution:** Rahti requires the CSC project number in a specific format:
- **Name:** `cardiorisk` (later `cardiorisk2` for the successful deployment)
- **Display name:** `CardioRisk Predictor`
- **Description:** `csc_project: 2018066`

---

### 5. First Deployment — CrashLoopBackOff

Imported the app from Git:
- **Repo URL:** `https://github.com/rfernando-github/webapp-rahti.git`
- Rahti auto-detected Python and used the **S2I (Source-to-Image)** build process
- Build completed successfully

**Problem:** The app pod entered **CrashLoopBackOff** status (crashing and restarting repeatedly).

**Logs showed:**
```
Booting worker with pid: 24
Booting worker with pid: 25
Booting worker with pid: 26
... (12+ workers)
```

**Cause:** Gunicorn was auto-detecting the node's CPU count and spawning 12+ workers. Each worker loaded scikit-learn + the model into memory, exceeding the container's memory limit (~964 MiB) and causing an OOM (Out of Memory) kill.

---

### 6. Fix: Limit Gunicorn Workers

Updated `.s2i/environment` to limit concurrency:

```
APP_MODULE=wsgi:app
APP_PORT=8080
WEB_CONCURRENCY=2
```

Pushed the fix:
```bash
git add .s2i/environment
git commit -m "Limit Gunicorn to 2 workers to prevent OOM crash"
git push
```

Triggered a new build on Rahti. This time the pod started successfully with only 2 workers:
```
Booting worker with pid: 20
Booting worker with pid: 21
```

---

### 7. App Running Successfully

**Final logs confirmed the app is serving requests:**
```
---> Serving application with gunicorn (wsgi:app) with default settings ...
[2026-02-25 16:40:38 +0000] [1] [INFO] Starting gunicorn 25.1.0
[2026-02-25 16:40:38 +0000] [1] [INFO] Listening at: http://0.0.0.0:8080 (1)
[2026-02-25 16:40:38 +0000] [1] [INFO] Using worker: sync
[2026-02-25 16:40:38 +0000] [20] [INFO] Booting worker with pid: 20
[2026-02-25 16:40:38 +0000] [21] [INFO] Booting worker with pid: 21
10.129.0.2 - - [25/Feb/2026:16:48:35 +0000] "GET / HTTP/1.1" 200 8759
10.129.0.2 - - [25/Feb/2026:16:48:35 +0000] "GET /static/style.css HTTP/1.1" 200 0
```

All pages return HTTP 200:
- `GET /` — Input form
- `GET /about` — Model info page
- `POST /predict` — Prediction results

**Warning (harmless):** sklearn version mismatch warning — model was pickled with sklearn 1.7.2 (local machine), Rahti has sklearn 1.8.0. The model loads and works correctly despite this warning.

---

## Summary of Files Modified for Rahti

| File | Purpose |
|------|---------|
| `app.py` | Changed to `host='0.0.0.0'`, `port=8080` (Rahti requirement) |
| `wsgi.py` | New — Gunicorn WSGI entry point |
| `requirements.txt` | Added `gunicorn>=21.0` |
| `.s2i/environment` | S2I config: `APP_MODULE=wsgi:app`, `APP_PORT=8080`, `WEB_CONCURRENCY=2` |
| `.gitignore` | Excludes `__pycache__/`, `.env`, `venv/` |
| `Procfile` | Gunicorn command for Railway/Heroku compatibility |
| `model.pkl` | Pre-trained model committed to repo (Rahti has no dataset access) |
| `model_metadata.json` | Model metrics committed to repo |

---

## Rahti Infrastructure — Kubernetes / OpenShift Under the Hood

CSC Rahti is based on **Red Hat OpenShift (OKD)**, which is an enterprise **Kubernetes** distribution. Everything runs as containers orchestrated by Kubernetes.

### What Kubernetes Resources Were Created

When we imported from Git, Rahti automatically created these Kubernetes resources:

| Resource | Name | Purpose |
|----------|------|---------|
| **BuildConfig** | `webapp-rahti-git` | S2I build definition — how to build the container image from Git |
| **ImageStream** | `webapp-rahti-git` | Points to the built container image in Rahti's internal registry |
| **Deployment** | `webapp-rahti-git` | Defines how to run the app (image, ports, replicas) |
| **Service** | `webapp-rahti-git` | Internal network endpoint exposing port 8080 |
| **Route** | `webapp-rahti-git` | Maps public URL → Service → Pod |

### The Two Pods Explained

During deployment, Rahti created **2 pods**:

| Pod | Type | Status | Purpose |
|-----|------|--------|---------|
| `webapp-rahti-git-1-build` | Build pod | **Completed** | Temporary pod that cloned the Git repo, ran `pip install`, and built the container image. Stopped after build finished. |
| `webapp-rahti-git-598588b459-ngws6` | App pod | **Running** | The actual Flask application serving user requests via Gunicorn on port 8080. |

The build pod runs once and stops. Only the app pod stays running permanently.

### Request Flow Through Kubernetes

```
User Browser
    │
    ▼ HTTPS
Route (webapp-rahti-git-cardiorisk2.2.rahtiapp.fi)
    │
    ▼ HTTP (internal)
Service (webapp-rahti-git:8080)
    │
    ▼
App Pod (webapp-rahti-git-xxx)
    ├── Gunicorn master process (pid 1)
    ├── Worker 1 (pid 20) ── Flask app ── model.pkl
    └── Worker 2 (pid 21) ── Flask app ── model.pkl
```

### Build Process (S2I)

```
GitHub Repo
    │
    ▼
Build Pod (temporary)
    ├── git clone https://github.com/rfernando-github/webapp-rahti.git
    ├── pip install -r requirements.txt
    ├── Package everything into a container image
    └── Push image to internal registry → pod stops (Completed)
            │
            ▼
Container Image (stored in Rahti's internal registry)
            │
            ▼
App Pod (running permanently)
    ├── Reads .s2i/environment config
    ├── Runs: gunicorn wsgi:app --bind 0.0.0.0:8080 --workers 2
    └── Serves requests on port 8080
            │
            ▼
Route → public HTTPS URL
```

### CrashLoopBackOff — Kubernetes Self-Healing

During the first deployment, the app pod kept crashing due to OOM (too many Gunicorn workers). Kubernetes detected the crash and kept **automatically restarting** the pod — this is Kubernetes' **self-healing** mechanism. Each restart attempt is logged with increasing back-off delays:

```
Restart 1 → wait 10s → Restart 2 → wait 20s → Restart 3 → wait 40s → ...
```

This is why the status showed **CrashLoopBackOff** — Kubernetes was doing its job of trying to keep the pod running, but the underlying OOM issue needed to be fixed first (limiting workers to 2).

---

## How Rahti Builds & Runs the App (Summary)

```
1. Rahti clones the Git repository
2. Detects requirements.txt → Python S2I builder
3. Installs: flask, pandas, scikit-learn, numpy, gunicorn
4. Reads .s2i/environment:
   - APP_MODULE=wsgi:app
   - APP_PORT=8080
   - WEB_CONCURRENCY=2
5. Runs: gunicorn wsgi:app --bind 0.0.0.0:8080 --workers 2
6. Creates Route → public HTTPS URL
```

---

## Key Lessons Learned

1. **CSC Rahti requires MFA** — Enable it at my.csc.fi before attempting to log in
2. **Project description format** — Must be `csc_project: <number>`, not free text
3. **Account propagation delay** — May need to wait hours after activating Rahti
4. **Gunicorn workers** — Always set `WEB_CONCURRENCY` explicitly; auto-detection spawns too many workers on shared nodes, causing OOM crashes
5. **Model serialization** — Pickle files should be committed to the repo since the training dataset isn't available on Rahti
6. **sklearn version mismatch** — Minor version differences (1.7.2 vs 1.8.0) produce warnings but work fine
