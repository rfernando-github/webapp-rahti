# CardioRisk Predictor

A web application for cardiovascular disease (CVD) risk prediction, built with Flask and scikit-learn. Deployed on [CSC Rahti](https://docs.csc.fi/cloud/rahti/), Finland's academic container cloud platform.

**Live URL:** https://webapp-rahti-git-cardiorisk2.2.rahtiapp.fi/

**GitHub:** https://github.com/rfernando-github/webapp-rahti

## Overview

CardioRisk Predictor is a digital health screening tool that predicts whether a patient is at high or low risk for cardiovascular disease based on 10 health parameters. The app uses a pre-trained Decision Tree classifier and provides explainable predictions — showing the decision rules the model followed and feature importance scores.

### Features

- Patient health data input form (demographics, vitals, lab results, lifestyle)
- Real-time CVD risk prediction (HIGH / LOW risk)
- Confidence probabilities for each class
- Explainability: decision path rules and feature importance
- Model information and performance metrics page

## Architecture

The app is **stateless** with no database. It loads a pre-trained model at startup and computes predictions in-memory:

```
User Form Input --> Validation --> Feature Extraction --> Decision Tree Model --> Prediction Results
```

## Tech Stack

- **Backend:** Flask 3.x, Gunicorn
- **ML Model:** scikit-learn DecisionTreeClassifier
- **Frontend:** Bootstrap 5, Jinja2 templates
- **Deployment:** CSC Rahti (Red Hat OpenShift / Kubernetes)

## Model Details

| Metric | Value |
|--------|-------|
| Algorithm | Decision Tree (max_depth=5, Gini criterion) |
| Accuracy | 73.44% |
| Precision | 76.12% |
| Recall | 67.55% |
| F1 Score | 71.58% |
| ROC AUC | 0.7929 |

**Input features (10):** Age, Gender, BMI (calculated from height/weight), Systolic BP, Diastolic BP, Cholesterol, Glucose, Smoking, Alcohol, Physical Activity

**Training data:** Kaggle Health Screening Data — 68,560 records after cleaning (80/20 train/test split)

## Project Structure

```
webapp-rahti/
├── .s2i/
│   └── environment          # S2I build config (APP_MODULE, APP_PORT, WEB_CONCURRENCY)
├── templates/
│   ├── base.html            # Base layout (Bootstrap 5, navbar, footer)
│   ├── index.html           # Patient input form
│   ├── result.html          # Prediction results + explainability
│   └── about.html           # Model metrics & architecture info
├── static/
│   └── style.css            # Custom CSS (risk level colors)
├── app.py                   # Flask app — routes: /, /predict, /about
├── wsgi.py                  # Gunicorn WSGI entry point
├── model_service.py         # Model loading, prediction, feature extraction, explainability
├── validators.py            # Input validation (range & type checks)
├── train_model.py           # Training script (run locally, not on Rahti)
├── model.pkl                # Pre-trained Decision Tree model
├── model_metadata.json      # Model metrics & feature importances
├── requirements.txt         # Python dependencies
├── Procfile                 # Heroku/Railway compatibility
└── .gitignore               # Git ignore rules
```

## Running Locally

### Prerequisites

- Python 3.10+
- pip

### Setup

```bash
cd webapp-rahti
pip install -r requirements.txt
python3 app.py
```

Open http://localhost:8080 in your browser.

To run with Gunicorn (same as production):

```bash
gunicorn wsgi:app --bind 0.0.0.0:8080
```

### Retraining the Model

If you need to retrain the model with updated data:

```bash
python3 train_model.py
```

This generates new `model.pkl` and `model_metadata.json` files. Commit them to the repo.

## Deploying on CSC Rahti

### Prerequisites

1. A CSC account — register at https://my.csc.fi using **Haka** (university credentials)
2. **MFA enabled** on your CSC account (required since November 2025)
3. A CSC project with **Rahti Container Cloud** service activated
4. This repository pushed to a **public GitHub** repo

### Step 1: Push to GitHub

```bash
cd webapp-rahti
git init
git add .
git commit -m "CardioRisk Predictor — Rahti deployment"
git remote add origin https://github.com/<your-username>/<your-repo>.git
git push -u origin main
```

Make sure `model.pkl` and `model_metadata.json` are committed — Rahti has no access to the training dataset.

### Step 2: Log in to Rahti

1. Go to https://rahti.csc.fi
2. Click **"Log in with CSC account"**
3. Authenticate via Haka

### Step 3: Create a Project

1. In the Rahti web console, click **"Create Project"**
2. Fill in:
   - **Name:** `cardiorisk` (lowercase, no spaces)
   - **Display name:** `CardioRisk Predictor`
   - **Description:** `csc_project: <your-project-number>` (this exact format is required)
3. Click **Create**

> **Important:** The description **must** follow the format `csc_project: <number>`. You can find your project number at https://my.csc.fi. Using any other format will be rejected.

### Step 4: Import from Git

1. Click the **"+"** button (top-right) -> **"Import from Git"**
2. Paste your GitHub repository URL:
   ```
   https://github.com/<your-username>/<your-repo>.git
   ```
3. Rahti auto-detects Python and selects the S2I Python builder
4. Verify settings:
   - **Builder Image:** Python
   - **Application name:** `cardiorisk-predictor`
   - **Name:** `cardiorisk-predictor`
5. Click **Create**

### Step 5: Wait for Build

The build typically takes 2-5 minutes. Rahti will:

1. Clone the Git repository
2. Detect `requirements.txt` and install dependencies with pip
3. Read `.s2i/environment` for configuration:
   ```
   APP_MODULE=wsgi:app    # Gunicorn entry point
   APP_PORT=8080          # Listening port
   WEB_CONCURRENCY=2      # Limit Gunicorn workers (prevents OOM)
   ```
4. Start Gunicorn: `gunicorn wsgi:app --bind 0.0.0.0:8080 --workers 2`
5. Create a Route (public URL)

You can monitor the build under **Builds** in the console.

### Step 6: Access Your App

Once the pod is running, go to **Networking -> Routes** to find your public URL:

```
https://<app-name>-<project>.rahtiapp.fi
```

### Step 7: Enable HTTPS (Optional)

1. Go to **Networking -> Routes**
2. Click on your route -> **Actions -> Edit**
3. Under **TLS Settings**, select **"Edge"** termination
4. Save

### Step 8: Set Up Auto-Redeploy (Optional)

To automatically rebuild when you push to GitHub:

1. In Rahti: **Builds -> \<your-build\> -> Configuration** — copy the **GitHub Webhook URL**
2. In GitHub: **Settings -> Webhooks -> Add webhook**
   - **Payload URL:** paste the Rahti webhook URL
   - **Content type:** `application/json`
   - **Events:** "Just the push event"
3. Click **Add webhook**

Now every `git push` triggers an automatic rebuild and redeploy.

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "Could not find user" on Rahti login | Enable MFA on your CSC account and wait a few hours for propagation |
| Project creation rejected | Description must be `csc_project: <number>` format |
| CrashLoopBackOff / OOM | Set `WEB_CONCURRENCY=2` in `.s2i/environment` to limit Gunicorn workers |
| "Application is not available" | Check pod logs; verify app listens on port 8080 and host 0.0.0.0 |
| Model file not found | Ensure `model.pkl` and `model_metadata.json` are committed to Git |
| sklearn version warning | Minor version mismatches produce warnings but work fine |

## Team

- Roshan Fernando
- Antti Moilanen
- Ville Rytkonen
- Tuomas Rahkola

**Course:** Software for Intelligent Systems and Artificial Intelligence — University of Oulu (Group G)

## License

This project was developed as part of academic coursework at the University of Oulu.
