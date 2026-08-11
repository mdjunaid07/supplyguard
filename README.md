 # 🔐 SupplyGuard — AI Supply Chain Attack Intelligence Engine

> **Detect risky npm dependencies in Pull Requests *before* vulnerabilities are publicly known.**
> Uses behavioral ML analysis, graph-based trust scoring, and multi-source data collection to automatically comment risk reports on GitHub PRs.

---

## 📋 Table of Contents

1. [What This System Does](#-what-this-system-does)
2. [System Architecture](#-system-architecture)
3. [Project Structure](#-project-structure)
4. [Prerequisites — What You Need to Install](#-prerequisites--what-you-need-to-install)
5. [Step-by-Step Setup](#-step-by-step-setup)
   - [Step 1: Clone & Install Dependencies](#step-1-clone--install-dependencies)
   - [Step 2: Configure Your GitHub App](#step-2-configure-your-github-app-)
   - [Step 3: Set Up Environment Variables (.env)](#step-3-set-up-environment-variables-env)
   - [Step 4: Set Up MongoDB](#step-4-set-up-mongodb)
   - [Step 5: Train the ML Model](#step-5-train-the-ml-model)
   - [Step 6: Run the Backend](#step-6-run-the-backend)
   - [Step 7: Run the Frontend](#step-7-run-the-frontend)
6. [How to Test the Application](#-how-to-test-the-application)
7. [Where to See the Output](#-where-to-see-the-output)
8. [Running with Docker (Easiest)](#-running-with-docker-easiest)
9. [Deployment](#-deployment)
10. [Troubleshooting](#-troubleshooting)

---

## 🎯 What This System Does

When a developer opens a Pull Request that changes `package.json`:

```
Developer opens PR
      ↓
GitHub sends webhook → SupplyGuard Backend
      ↓
Extracts changed dependencies
      ↓
Collects data from: npm + GitHub API + NVD CVE Database
      ↓
Builds 14-feature ML vector per package
      ↓
ML model predicts risk probability (0–100%)
      ↓
Graph trust scoring (PageRank on dependency graph)
      ↓
Generates risk report Markdown
      ↓
Posts automated comment on the PR ← YOU SEE THIS
      ↓
Stores results in MongoDB → visible on React Dashboard ← YOU SEE THIS TOO
```

---

## 🏗️ System Architecture

```
┌────────────────────────────────────────────────────────┐
│                    GitHub App                          │
│   PR opened → sends webhook to your backend           │
└────────────────────────┬───────────────────────────────┘
                         │  POST /webhook
              ┌──────────▼──────────┐
              │   FastAPI Backend   │  ← Python, port 8000
              │   (backend/)        │
              └──┬───────────┬──────┘
                 │           │
        ┌────────▼──┐  ┌─────▼──────────┐
        │  ML Model │  │  Graph Engine  │
        │ scikit-   │  │  NetworkX      │
        │ learn     │  │  PageRank      │
        └────────┬──┘  └─────┬──────────┘
                 └─────┬─────┘
              ┌────────▼────────┐
              │    MongoDB      │  ← Stores all scan results
              └────────┬────────┘
                       │
              ┌────────▼────────┐
              │ React Dashboard │  ← port 5173
              │ (frontend/)     │
              └─────────────────┘
```

---

## 📁 Project Structure

```
supplyguard/
│
├── .env                          ← YOUR SECRETS GO HERE (you create this)
├── .env.example                  ← Template showing all required variables
├── docker-compose.yml            ← Run everything with one command
│
├── backend/                      ← Python FastAPI server
│   ├── main.py                   ← App entry point
│   ├── config.py                 ← Reads .env variables
│   ├── requirements.txt          ← Python packages to install
│   ├── webhook/
│   │   ├── router.py             ← POST /webhook handler
│   │   └── validator.py          ← GitHub signature verification
│   ├── services/
│   │   ├── dependency_extractor.py  ← Reads package.json diff from PR
│   │   ├── npm_collector.py         ← Fetches npm registry data
│   │   ├── github_collector.py      ← Fetches GitHub repo stats
│   │   ├── cve_collector.py         ← Fetches CVEs from NVD
│   │   ├── feature_engineer.py      ← Builds ML feature vector
│   │   └── report_generator.py      ← Creates PR comment Markdown
│   ├── ml/
│   │   ├── predictor.py          ← Loads model, returns risk score
│   │   ├── preprocessor.py       ← StandardScaler / imputer
│   │   └── explainer.py          ← SHAP explanations
│   ├── graph/
│   │   ├── trust_graph.py        ← NetworkX graph of packages
│   │   └── trust_scorer.py       ← PageRank trust scores
│   ├── db/
│   │   ├── mongo.py              ← MongoDB connection
│   │   └── models.py             ← Data schemas (Pydantic)
│   ├── api/
│   │   └── router.py             ← REST endpoints for dashboard
│   └── utils/
│       ├── github_client.py      ← Posts PR comments
│       └── logger.py             ← Logging setup
│
├── ml-model/                     ← ML training scripts
│   ├── train.py                  ← Train LogReg + RF + GBM, save best model
│   ├── predict.py                ← CLI: analyse a single package
│   ├── requirements.txt          ← ML-only Python packages
│   ├── data/
│   │   └── sample_dataset.csv    ← 140-row synthetic training data
│   └── models/                   ← Saved model files (generated by train.py)
│       ├── model.pkl             ← Best trained model
│       ├── preprocessor.pkl      ← Fitted scaler
│       └── feature_importances.csv
│
└── frontend/                     ← React dashboard
    ├── package.json              ← Node packages to install
    ├── vite.config.js
    ├── tailwind.config.js
    ├── index.html
    └── src/
        ├── App.jsx               ← Routes
        ├── main.jsx              ← Entry point
        ├── index.css             ← Global styles + Tailwind
        ├── api/client.js         ← Axios API calls
        ├── components/
        │   ├── Navbar.jsx
        │   ├── RiskCard.jsx
        │   ├── RiskTrend.jsx     ← Recharts area chart
        │   ├── TrustGraph.jsx    ← Force-directed graph
        │   └── PackageDetail.jsx
        └── pages/
            ├── Dashboard.jsx     ← Main overview page
            ├── ScanHistory.jsx   ← All PR scans table
            └── PackageDetailPage.jsx
```

---

## 💻 Prerequisites — What You Need to Install

### Required Software

| Software | Version | Download |
|----------|---------|---------|
| **Python** | 3.11+ | https://www.python.org/downloads/ |
| **Node.js** | 18+ | https://nodejs.org/ |
| **MongoDB** | 7+ | https://www.mongodb.com/try/download/community OR use MongoDB Atlas (free cloud) |
| **Git** | Any recent | https://git-scm.com/ |

### Required Accounts / Services

| Account | Why needed | Cost |
|---------|-----------|------|
| **GitHub Account** | You already have one (GitHub App created) | Free |
| **MongoDB Atlas** | Free cloud database (alternative to local MongoDB) | Free tier |
| **ngrok** | Expose your local backend to GitHub for webhooks during testing | Free |
| **NVD API Key** | CVE database (optional, works without, but rate-limited) | Free — https://nvd.nist.gov/developers/request-an-api-key |

---

## 🔧 Step-by-Step Setup

### Step 1: Clone & Install Dependencies

#### 1A. Backend Python Dependencies

Open a terminal in the `supplyguard/` root folder:

```bash
# Create a virtual environment (recommended)
python -m venv venv

# Activate it:
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# Install backend dependencies
pip install -r backend/requirements.txt
```

**What gets installed:**
- `fastapi` + `uvicorn` — web server
- `motor` + `pymongo` — MongoDB async driver
- `PyGithub` — GitHub API client
- `httpx` — async HTTP client (for npm/NVD API calls)
- `scikit-learn` + `pandas` + `numpy` — ML pipeline
- `shap` — ML explainability
- `networkx` — dependency graph / trust scoring
- `pydantic-settings` — environment variable management
- `cryptography` — GitHub App JWT signing

#### 1B. ML Model Dependencies

```bash
pip install -r ml-model/requirements.txt
```

**What gets installed:**
- `scikit-learn`, `pandas`, `numpy` — model training
- `joblib` — saving/loading models
- `shap` — SHAP values
- `matplotlib`, `seaborn` — training charts

#### 1C. Frontend Node Dependencies

```bash
cd frontend
npm install
cd ..
```

**What gets installed:**
- `react` + `react-dom` + `react-router-dom` — UI framework
- `recharts` — risk trend charts
- `react-force-graph-2d` — interactive dependency graph
- `lucide-react` — icons
- `axios` — API calls
- `tailwindcss` — styling
- `vite` — dev server + bundler

---

### Step 2: Configure Your GitHub App 🔑

You said you already created your GitHub App. Here's exactly what to do:

#### 2A. Find Your GitHub App Settings

1. Go to: **https://github.com/settings/apps**
2. Click your app name
3. You'll see the **App ID** at the top — copy it

#### 2B. Generate a Private Key

1. On your GitHub App settings page, scroll down to **"Private keys"**
2. Click **"Generate a private key"**
3. A `.pem` file downloads (e.g., `supplyguard.2024-01-01.private-key.pem`)
4. **Move this file into your project root:**
   ```
   supplyguard/
   ├── private-key.pem    ← put the .pem file here
   ├── .env
   └── ...
   ```

#### 2C. Set Up the Webhook URL

During development you need **ngrok** to expose your local machine:

```bash
# Install ngrok: https://ngrok.com/download
# Then run:
ngrok http 8000
```

ngrok gives you a URL like: `https://abc123.ngrok-free.app`

1. On your GitHub App settings page, find **"Webhook URL"**
2. Set it to: `https://abc123.ngrok-free.app/webhook`
3. Set a **Webhook Secret** — any random string, e.g., `mysecretkey123`
4. Under **Permissions**, make sure you have:
   - Pull requests → **Read & Write** ✅
   - Contents → **Read** ✅
   - Metadata → **Read** ✅
5. Under **Subscribe to events**, check:
   - **Pull request** ✅
6. Click **Save changes**

#### 2D. Install the App on Your Repository

1. On your GitHub App settings page, click **"Install App"** in the left sidebar
2. Select your GitHub account
3. Choose **"Only select repositories"** → pick the repo you want to monitor
4. Click **Install**

---

### Step 3: Set Up Environment Variables (.env)

Create a `.env` file in the **project root** (`supplyguard/`):

```bash
# Windows:
copy .env.example .env

# Mac/Linux:
cp .env.example .env
```

Now open `.env` and fill in your values:

```env
# ─── GitHub App ───────────────────────────────────────────────
# From: github.com/settings/apps → your app → "App ID" at the top
GITHUB_APP_ID=123456

# Path to the .pem private key file you downloaded
GITHUB_PRIVATE_KEY_PATH=./private-key.pem

# The webhook secret you set on the GitHub App settings page
GITHUB_WEBHOOK_SECRET=mysecretkey123

# A Personal Access Token (PAT) for GitHub API calls
# Create at: github.com/settings/tokens → Generate new token (classic)
# Scopes needed: repo, read:org
GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# ─── MongoDB ──────────────────────────────────────────────────
# Option A: Local MongoDB (if installed locally)
MONGO_URI=mongodb://localhost:27017

# Option B: MongoDB Atlas (free cloud database)
# Get from: cloud.mongodb.com → your cluster → Connect → Drivers
# MONGO_URI=mongodb+srv://username:password@cluster0.xxxxx.mongodb.net/

MONGO_DB_NAME=supplyguard

# ─── Backend ──────────────────────────────────────────────────
BACKEND_PORT=8000
ENVIRONMENT=development
SECRET_KEY=change-this-to-any-random-string-you-want

# ─── ML Model paths (don't change unless you move files) ──────
MODEL_PATH=./ml-model/models/model.pkl
PREPROCESSOR_PATH=./ml-model/models/preprocessor.pkl

# ─── NVD CVE API (optional but recommended) ───────────────────
# Get free key at: https://nvd.nist.gov/developers/request-an-api-key
# Without this key, CVE lookups still work but are rate-limited to 5/30sec
NVD_API_KEY=your-nvd-api-key-here
```

### Where each value comes from:

| Variable | Where to get it |
|----------|----------------|
| `GITHUB_APP_ID` | github.com/settings/apps → your app → top of page labeled "App ID" |
| `GITHUB_PRIVATE_KEY_PATH` | Path to the `.pem` file you downloaded from GitHub App settings |
| `GITHUB_WEBHOOK_SECRET` | Whatever string you typed in the GitHub App "Webhook secret" field |
| `GITHUB_TOKEN` | github.com/settings/tokens → "Generate new token (classic)" → check `repo` scope |
| `MONGO_URI` | Local: `mongodb://localhost:27017` OR MongoDB Atlas connection string |
| `NVD_API_KEY` | nvd.nist.gov/developers/request-an-api-key (free, email registration) |

---

### Step 4: Set Up MongoDB

#### Option A: Local MongoDB (easiest for dev)

1. Download from: https://www.mongodb.com/try/download/community
2. Install and start:
   ```bash
   # Windows (as service, auto-starts)
   # Just install MongoDB Community Edition

   # Verify it's running:
   mongosh
   # Should show "Connected to: mongodb://127.0.0.1:27017/"
   ```
3. In `.env` set: `MONGO_URI=mongodb://localhost:27017`

#### Option B: MongoDB Atlas (free cloud, no install needed)

1. Go to https://cloud.mongodb.com and sign up free
2. Create a free **M0 cluster**
3. Click **Connect** → **Drivers** → copy the connection string
4. Replace `<password>` with your DB password
5. In `.env` set: `MONGO_URI=mongodb+srv://user:pass@cluster0.xxxxx.mongodb.net/`

> SupplyGuard automatically creates the `supplyguard` database and all collections on first run. **No manual setup needed.**

---

### Step 5: Train the ML Model

This creates the `model.pkl` file that the backend uses for predictions.

```bash
# Make sure your virtualenv is active
# From the project root:
python ml-model/train.py
```

**Expected output:**
```
✅ Loaded 140 samples | Malicious: 40 | Benign: 100

🔧 Training Logistic Regression...
  CV AUC: 0.9234 ± 0.0312

🔧 Training Random Forest...
  CV AUC: 0.9687 ± 0.0218

🔧 Training Gradient Boosting...
  CV AUC: 0.9545 ± 0.0189

🏆 Best model: Random Forest (AUC=0.9812)
✅ Best model saved → ml-model/models/model.pkl
✅ Preprocessor saved → ml-model/models/preprocessor.pkl
```

**Custom training data:** If you want to add more training samples, edit `ml-model/data/sample_dataset.csv` and re-run `train.py`. The CSV columns must match the feature names (see the file for reference).

---

### Step 6: Run the Backend

```bash
# From project root, with virtualenv active:
uvicorn backend.main:app --reload --port 8000
```

**Expected output:**
```
INFO  | supplyguard | 🚀 SupplyGuard backend started
INFO  | db.mongo    | Connected to MongoDB: supplyguard
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

The backend is now running at: **http://localhost:8000**

**Verify it works:**
```bash
curl http://localhost:8000/health
# → {"status":"ok","service":"supplyguard"}
```

---

### Step 7: Run the Frontend

Open a **second terminal**:

```bash
cd frontend
npm run dev
```

**Expected output:**
```
  VITE v5.x.x  ready in 512 ms
  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose
```

Open your browser at: **http://localhost:5173**

---

## 🧪 How to Test the Application

### Test 1: Health Check

```bash
curl http://localhost:8000/health
```
Expected: `{"status":"ok","service":"supplyguard"}`

### Test 2: Test the ML Predictor CLI

```bash
# Analyse a specific package using the CLI tool
python ml-model/predict.py --package lodash
python ml-model/predict.py --package event-stream
python ml-model/predict.py --package express --version 4.18.2
```

You'll see a formatted risk report printed in the terminal.

### Test 3: Send a Fake Webhook (Simulate a PR)

Create a test file `test_webhook.py` in the project root:

```python
import httpx
import json
import hmac
import hashlib

WEBHOOK_SECRET = "mysecretkey123"   # same as in .env

payload = {
    "action": "opened",
    "number": 42,
    "pull_request": {
        "number": 42,
        "base": {"sha": "abc123def456abc123def456abc123def456abc1"},
        "head": {"sha": "def456abc123def456abc123def456abc123def4"},
    },
    "repository": {
        "full_name": "your-username/your-repo"
    },
    "installation": {"id": 12345678}
}

body = json.dumps(payload).encode()
sig = "sha256=" + hmac.new(
    WEBHOOK_SECRET.encode(), body, hashlib.sha256
).hexdigest()

response = httpx.post(
    "http://localhost:8000/webhook",
    content=body,
    headers={
        "X-GitHub-Event": "pull_request",
        "X-Hub-Signature-256": sig,
        "Content-Type": "application/json",
    }
)
print(response.status_code, response.json())
```

```bash
python test_webhook.py
# → 200 {'status': 'accepted', 'pr': 42, 'repo': 'your-username/your-repo'}
```

### Test 4: Real GitHub PR Test

1. Start ngrok: `ngrok http 8000`
2. Copy the ngrok URL (e.g. `https://abc123.ngrok-free.app`)
3. Go to your GitHub App settings → set Webhook URL to `https://abc123.ngrok-free.app/webhook`
4. Open a PR in your monitored repo that changes `package.json`
5. Add or change any npm package, e.g.:
   ```json
   "dependencies": {
     "lodash": "^4.17.21",
     "some-new-package": "^1.0.0"
   }
   ```
6. Push the branch and open the PR
7. Within ~30 seconds, SupplyGuard posts a comment on the PR

### Test 5: Browse the API Directly

```bash
# List all scans
curl http://localhost:8000/api/scans

# Overview stats
curl http://localhost:8000/api/stats/overview

# Interactive API docs (Swagger UI)
# Open in browser:
http://localhost:8000/docs
```

---

## 👀 Where to See the Output

### Output Location 1: GitHub PR Comment ← Main Output

When SupplyGuard analyses a PR, it **automatically posts a comment** on the Pull Request that looks like:

```
## 🔐 SupplyGuard — AI Supply Chain Risk Report

> Repository: your-org/your-repo | PR: #42 | Scanned: 2024-01-15 10:30 UTC

---

### 📊 Summary

| Packages Scanned | 🔴 HIGH | 🟡 MEDIUM | 🟢 LOW |
|:-:|:-:|:-:|:-:|
| 3 | 1 | 1 | 1 |

---

### 🔴 High Risk Packages

#### 🔴 `some-package` @ `1.0.0`

| Risk Score | Risk Level | Trust Score |
|:-:|:-:|:-:|
| **87.3%** | **HIGH** | 23.1% |

**⚠️ Risk Factors:**
- Very new package (< 90 days old)
- Single maintainer — high bus-factor risk
- Sudden surge in release activity
- 2 known CVE(s) found
```

**When does this appear?**
- Every time a PR is **opened**, **updated**, or **reopened**
- Appears within **10–60 seconds** of the PR event (depends on API response times)

---

### Output Location 2: React Dashboard → http://localhost:5173

Open your browser at **http://localhost:5173** to see:

| Page | URL | What you see |
|------|-----|-------------|
| **Dashboard** | `/` | Summary cards, risk trend chart, recent scans, dependency graph |
| **Scan History** | `/scans` | Table of all PR scans with risk levels and package counts |
| **Packages** | `/packages` | All tracked packages sorted by risk score |

---

### Output Location 3: Backend Logs (Terminal)

Watch the backend terminal while a PR is processed:

```
2024-01-15 10:30:01 | INFO | webhook.router | Processing PR #42 in your-org/your-repo
2024-01-15 10:30:02 | INFO | dependency_extractor | added=2 removed=0 changed=1
2024-01-15 10:30:04 | INFO | npm_collector | Fetched metadata for lodash
2024-01-15 10:30:05 | INFO | github_collector | Fetched GitHub data for lodash/lodash
2024-01-15 10:30:06 | INFO | cve_collector | CVEs found for lodash: 3
2024-01-15 10:30:07 | INFO | webhook.router | HIGH=1 MEDIUM=1 LOW=1
2024-01-15 10:30:08 | INFO | github_client | Posted comment on your-org/your-repo#42
```

---

### Output Location 4: MongoDB Collections

Connect with MongoDB Compass or `mongosh` to inspect raw data:

```bash
mongosh
use supplyguard
db.scans.find().sort({scanned_at: -1}).limit(3).pretty()
db.packages.find().sort({avg_risk_score: -1}).limit(10).pretty()
```

Collections:
- `scans` — one document per PR scan, contains all package risk details
- `packages` — running history per package for continuous learning

---

### Output Location 5: Interactive API Docs

FastAPI auto-generates Swagger UI at:
**http://localhost:8000/docs**

You can test every endpoint directly in the browser.

---

## 🐳 Running with Docker (Easiest)

If you have Docker installed, run everything with one command:

```bash
# Build and start all services (backend + frontend + mongodb)
docker-compose up --build

# Run in background
docker-compose up -d --build

# Stop
docker-compose down
```

Services started:
| Service | URL |
|---------|-----|
| Backend | http://localhost:8000 |
| Frontend | http://localhost:5173 |
| MongoDB | localhost:27017 |

> ⚠️ **Before running Docker**, make sure your `.env` file has `MONGO_URI=mongodb://mongodb:27017` (uses the Docker service name, not `localhost`)

---

## 🚀 Deployment

### Deploy Backend to Render (Free)

1. Push your code to GitHub
2. Go to https://render.com → "New Web Service"
3. Connect your repository
4. Settings:
   - **Build Command:** `pip install -r backend/requirements.txt`
   - **Start Command:** `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
   - **Environment:** Python 3.11
5. Add all environment variables from your `.env` file
6. Under "Files", upload your `private-key.pem` as a secret file
7. Update your GitHub App's Webhook URL to the Render URL: `https://your-app.onrender.com/webhook`

### Deploy Frontend to Netlify (Free)

1. Go to https://app.netlify.com → "Add new site" → "Import from Git"
2. Connect your repository
3. Settings:
   - **Base directory:** `frontend`
   - **Build command:** `npm run build`
   - **Publish directory:** `frontend/dist`
4. Add environment variable:
   - `VITE_API_BASE_URL` = `https://your-backend.onrender.com`

---

## 🔧 Troubleshooting

### "No module named 'backend'"
```bash
# Run uvicorn from the project ROOT, not from backend/
# Correct:
cd supplyguard
uvicorn backend.main:app --reload
```

### "Model not found" warning
```bash
# Train the model first:
python ml-model/train.py
```

### Webhook not receiving events
```bash
# Make sure ngrok is running:
ngrok http 8000
# Update GitHub App webhook URL with the new ngrok URL each time you restart ngrok
```

### MongoDB connection refused
```bash
# Start MongoDB service (Windows):
net start MongoDB
# Or start manually:
mongod --dbpath C:\data\db
```

### GitHub App "Invalid signature" (401 error)
- Check that `GITHUB_WEBHOOK_SECRET` in `.env` **exactly matches** the secret you typed in GitHub App settings (no extra spaces)

### Port 8000 already in use
```bash
uvicorn backend.main:app --reload --port 8001
# Also update VITE_API_BASE_URL to http://localhost:8001
```

---

## 🧠 ML Model Details

| Feature | Description |
|---------|-------------|
| `package_age_days` | How old the package is |
| `maintainer_count` | Number of maintainers |
| `maintainer_account_age` | Age of maintainer accounts |
| `commits_per_month` | Development activity |
| `release_frequency` | How often new versions are published |
| `version_spike_ratio` | Sudden release activity surge |
| `contributor_growth_rate` | Change in contributor count |
| `repo_popularity_score` | Stars + forks + watchers score |
| `ownership_change_flag` | Heuristic for ownership transfer |
| `download_trend_score` | Download growth/decline rate |
| `cve_count` | Number of known CVEs |
| `cve_severity_score` | Weighted CVSS severity |
| `dependency_depth` | How deep in the dependency tree |
| `historical_risk_score` | Past risk score from previous scans |

**Risk Classification:**
- 🟢 **LOW**: 0 – 35%
- 🟡 **MEDIUM**: 35 – 70%
- 🔴 **HIGH**: 70 – 100%

---

## 🔄 Continuous Learning Loop

As SupplyGuard scans more PRs, it stores feature vectors in MongoDB. To retrain with real data:

```bash
# Export collected data from MongoDB
# (use MongoDB Compass or mongosh to export packages collection to CSV)

# Retrain with new data
python ml-model/train.py --data path/to/real_data.csv
```

---

## 📊 Tech Stack Summary

| Layer | Technology | Version |
|-------|-----------|---------|
| Backend | Python FastAPI | 0.111 |
| ML | scikit-learn | 1.4.2 |
| ML Explainers | SHAP | 0.45.1 |
| Graph | NetworkX | 3.3 |
| Database Driver | Motor (async MongoDB) | 3.4 |
| Frontend | React | 18.3 |
| Charts | Recharts | 2.12 |
| Styling | Tailwind CSS | 3.4 |
| HTTP Client | httpx (async) | 0.27 |
| Bundler | Vite | 5.2 |

---

## 📄 License

MIT License — use freely for commercial and personal projects.

---

*Built with ❤️ by SupplyGuard — protecting the open-source supply chain one PR at a time.*
