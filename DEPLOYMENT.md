# CardioRisk Predictor — CSC Rahti Deployment Guide

This document covers how to deploy the CardioRisk Predictor Flask web app on **CSC Rahti**, Finland's container cloud platform for academic use.

---

## Table of Contents

1. [What is CSC Rahti?](#1-what-is-csc-rahti)
2. [Prerequisites](#2-prerequisites)
3. [What Changed for Rahti](#3-what-changed-for-rahti)
4. [Project Structure](#4-project-structure)
5. [Step-by-Step Deployment](#5-step-by-step-deployment)
6. [How Rahti Builds the App](#6-how-rahti-builds-the-app)
7. [Enable HTTPS](#7-enable-https)
8. [Auto-Redeploy with Webhooks](#8-auto-redeploy-with-webhooks)
9. [Running Locally (Testing)](#9-running-locally-testing)
10. [Troubleshooting](#10-troubleshooting)
11. [Useful Links](#11-useful-links)

---

## 1. What is CSC Rahti?

**Rahti** is a container cloud service provided by [CSC — IT Center for Science](https://csc.fi), Finland's national research computing center. It is based on **Red Hat OpenShift** (Kubernetes).

Key facts:
- **Free** for Finnish academic users (universities, research institutes)
- Supports **Python, Node.js, Java, Go** and custom Docker images
- Uses **Source-to-Image (S2I)** to build apps directly from Git repositories
- Provides a **public URL** for each deployed app
- Supports **HTTPS**, **webhooks**, and **auto-scaling**

Rahti documentation: https://docs.csc.fi/cloud/rahti/

---

## 2. Prerequisites

Before deploying, you need:

### 2.1 CSC Account
- Log in or register at https://my.csc.fi using **Haka** (University of Oulu credentials)
- If you don't have a CSC project, create one at my.csc.fi and request **Rahti access**

### 2.2 GitHub Repository
- Push the `webapp-rahti/` folder contents to a **public GitHub repository**
- The repo must contain all files at the **root level** (not nested inside a subfolder), OR you specify the context directory during import

### 2.3 Pre-trained Model
- `model.pkl` and `model_metadata.json` **must be committed** to the repo
- The dataset (`Health Screening Data.csv`) is NOT needed on Rahti — the model is already trained
- If you need to retrain, run `python3 train_model.py` locally first, then commit the updated `.pkl` and `.json`

---

## 3. What Changed for Rahti

The `webapp-rahti/` folder is a modified copy of `webapp/`. Here are the differences:

| File | Change | Why |
|------|--------|-----|
| `app.py` | `app.run(host='0.0.0.0', port=8080)` | Rahti expects apps on port **8080** and bound to `0.0.0.0` (not localhost) |
| `wsgi.py` | **New file** | Gunicorn WSGI entry point — Rahti's S2I Python builder uses this |
| `requirements.txt` | Added `gunicorn>=21.0` | Production WSGI server (Flask's dev server is not suitable for production) |
| `.s2i/environment` | **New file** | Tells the S2I builder: `APP_MODULE=wsgi:app` and `APP_PORT=8080` |
| `.gitignore` | **New file** | Prevents `__pycache__/`, `.env`, `venv/` from being committed |
| `model.pkl` | **Included in repo** | Rahti has no access to the training dataset, so the model must be pre-built |
| `model_metadata.json` | **Included in repo** | Same reason — metrics are pre-computed |

All other files (templates, CSS, `validators.py`, `model_service.py`) are **identical** to `webapp/`.

---

## 4. Project Structure

```
webapp-rahti/
├── .s2i/
│   └── environment          # S2I build config (APP_MODULE, APP_PORT)
├── templates/
│   ├── base.html            # Base layout (Bootstrap 5, navbar, footer)
│   ├── index.html           # Patient input form
│   ├── result.html          # Prediction results + explainability
│   └── about.html           # Model metrics & architecture info
├── static/
│   └── style.css            # Custom CSS (risk colors)
├── app.py                   # Flask app (port 8080, host 0.0.0.0)
├── wsgi.py                  # Gunicorn WSGI entry point
├── model_service.py         # Model loading, prediction, explainability
├── validators.py            # Input validation
├── train_model.py           # Training script (run locally, not on Rahti)
├── model.pkl                # Pre-trained Decision Tree model
├── model_metadata.json      # Model metrics & feature importances
├── requirements.txt         # Python dependencies (includes gunicorn)
├── .gitignore               # Git ignore rules
└── DEPLOYMENT.md            # This file
```

---

## 5. Step-by-Step Deployment

### Step 1: Push to GitHub

```bash
cd webapp-rahti
git init
git add .
git commit -m "CardioRisk Predictor — Rahti deployment"
git remote add origin https://github.com/<your-username>/<your-repo>.git
git push -u origin master
```

> **Important:** Rahti webhook integration expects the default branch to be named `master`. If yours is `main`, it still works but you'll need to adjust the webhook branch filter.

### Step 2: Log in to Rahti

1. Go to https://rahti.csc.fi
2. Click **"Log in with CSC account"**
3. Authenticate via Haka (University of Oulu)

### Step 3: Create a Project

1. In the Rahti web console, click **"Create Project"**
2. Name it something like `cardiorisk-predictor`
3. Click **Create**

### Step 4: Import from Git

1. Click the **"+"** button (top-right) → **"Import from Git"**
2. Paste your GitHub repository URL (HTTPS format):
   ```
   https://github.com/<your-username>/<your-repo>.git
   ```
3. Rahti will auto-detect it as a **Python** application
4. Verify the settings:
   - **Builder Image:** Python
   - **Application name:** `cardiorisk-predictor`
   - **Name:** `cardiorisk-predictor`
5. Click **Create**

### Step 5: Wait for Build

- Rahti clones your repo, installs dependencies from `requirements.txt`, and starts the app via `wsgi.py`
- The build typically takes **2–5 minutes**
- You can watch the build logs in the console under **Builds**

### Step 6: Access Your App

- Once the build completes and the pod is running, click **Routes** in the sidebar
- Your app will have a public URL like:
  ```
  http://cardiorisk-predictor-<project>.rahtiapp.fi
  ```
- Open it in your browser — the input form should load

---

## 6. How Rahti Builds the App

Rahti uses **Source-to-Image (S2I)** with the Python builder image. Here's what happens:

```
1. Rahti clones your Git repo
2. Detects requirements.txt → installs dependencies with pip
3. Reads .s2i/environment:
   - APP_MODULE=wsgi:app  → imports 'app' from wsgi.py
   - APP_PORT=8080        → binds to port 8080
4. Starts Gunicorn:
   gunicorn wsgi:app --bind 0.0.0.0:8080
5. Creates a Route (public URL) pointing to port 8080
```

You do **not** need a Dockerfile — S2I handles everything.

---

## 7. Enable HTTPS

By default, Rahti creates an HTTP route. To enable HTTPS:

1. Go to **Networking → Routes** in the Rahti console
2. Click on your route name
3. Click **Actions → Edit**
4. Under **TLS Settings**, select **"Edge"** termination
5. Save

Your app will now be accessible via `https://` with a valid SSL certificate.

---

## 8. Auto-Redeploy with Webhooks

To automatically rebuild the app when you push to GitHub:

### Get the Webhook URL
1. In Rahti console, go to **Builds → cardiorisk-predictor → Configuration**
2. Copy the **GitHub Webhook URL**

### Add to GitHub
1. Go to your GitHub repo → **Settings → Webhooks → Add webhook**
2. **Payload URL:** Paste the Rahti webhook URL
3. **Content type:** `application/json`
4. **Events:** "Just the push event"
5. Click **Add webhook**

Now every `git push` triggers an automatic rebuild and redeploy.

---

## 9. Running Locally (Testing)

You can test the Rahti version locally before deploying:

```bash
cd webapp-rahti
pip install -r requirements.txt
python3 app.py
```

Open http://localhost:8080 in your browser.

To test with Gunicorn (same as Rahti will run it):

```bash
cd webapp-rahti
gunicorn wsgi:app --bind 0.0.0.0:8080
```

---

## 10. Troubleshooting

### Build fails with "No module named ..."
- Make sure all dependencies are listed in `requirements.txt`
- Check the build logs in **Builds → cardiorisk-predictor → Logs**

### App starts but shows "Application is not available"
- Check pod logs: **Workloads → Pods → cardiorisk-predictor-xxx → Logs**
- Verify the app listens on port **8080** (not 5000)
- Verify `host='0.0.0.0'` (not `127.0.0.1` or `localhost`)

### Model file not found
- Make sure `model.pkl` and `model_metadata.json` are committed to Git
- Check with: `git ls-files model.pkl model_metadata.json`

### "Permission denied" errors
- Rahti runs containers as a **non-root user**
- Don't write files to the container filesystem at runtime
- The app only reads `model.pkl` and `model_metadata.json` — this is fine

### Webhook not triggering
- Verify the webhook URL is correct in GitHub settings
- Check GitHub → Settings → Webhooks → Recent Deliveries for error codes
- Ensure content type is `application/json`

---

## 11. Useful Links

| Resource | URL |
|----------|-----|
| CSC Rahti Docs | https://docs.csc.fi/cloud/rahti/ |
| Rahti Console | https://rahti.csc.fi |
| My CSC (account/projects) | https://my.csc.fi |
| Deploy from Git tutorial | https://docs.csc.fi/cloud/rahti/tutorials/deploy_from_git/ |
| Flask Rahti boilerplate | https://github.com/arcada-uas/rahti-flask |
| CSC ML Rahti examples | https://github.com/CSCfi/rahti-ml-examples |
| S2I Python builder docs | https://github.com/sclorg/s2i-python-container |
