# Azure App Service Deployment Guide

Deploy the **Soft Skill Check** (AI English Assessment) full stack to Azure with scaling support.

---

## Architecture Overview

| Component | Recommended | Alternative | Scale-ability |
|-----------|-------------|-------------|----------------|
| **Backend** (FastAPI) | Azure App Service (Linux, Python) | Web App for Containers | Scale out (instances) + scale up (size) |
| **Frontend** (React/Vite) | Azure Static Web Apps | App Service static files | CDN, unlimited scale |
| **Database** | Supabase PostgreSQL (existing) | — | Managed |
| **Sessions** (scale-out) | Azure Cache for Redis | In-memory (single instance only) | Required for multi-instance |

---

## Option 1: Recommended — App Service + Static Web Apps (Best for scaling)

**Why:** Backend and frontend scale independently. Static Web Apps gives global CDN, free tier, and GitHub Actions integration. Lowest cost and simplest ops.

```
[Users] → [Azure Static Web Apps] (frontend, CDN)
                ↓
         [App Service] (backend, scale-out) → [Supabase] [Azure OpenAI/Speech/Blob]
```

### 1.1 Backend — Azure App Service

#### Prerequisites
- Azure CLI (`az`) installed and logged in: `az login`
- Resource group and region (e.g. `eastus`)

#### Create and deploy backend

```bash
# Variables
RESOURCE_GROUP="soft-skill-check-rg"
LOCATION="eastus"
APP_NAME="soft-skill-check-api"    # Must be globally unique
PLAN_NAME="soft-skill-check-plan"

# Create resource group
az group create --name $RESOURCE_GROUP --location $LOCATION

# Create App Service plan (Linux, Python)
# Use B2 or S2+ for production; B1 for dev
az appservice plan create \
  --name $PLAN_NAME \
  --resource-group $RESOURCE_GROUP \
  --is-linux \
  --sku B2

# Create web app (Python 3.11)
az webapp create \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --plan $PLAN_NAME \
  --runtime "PYTHON:3.11"

# Configure startup command (use startup.sh or inline)
# Option A: Use startup.sh (respects PORT env var)
az webapp config set \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --startup-file "startup.sh"

# Option B: Inline (Azure default PORT is 8000)
# az webapp config set --name $APP_NAME --resource-group $RESOURCE_GROUP \
#   --startup-file "gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app --bind 0.0.0.0:8000"

# Enable HTTPS only
az webapp update --name $APP_NAME --resource-group $RESOURCE_GROUP --https-only true
```

#### Deploy code (local build)

```bash
cd backend
pip install -r requirements.txt
az webapp up \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --runtime "PYTHON:3.11" \
  --sku B2
```

Or **deploy from ZIP**:

```bash
cd backend
pip install -r requirements.txt -t .python_packages/lib/site-packages
zip -r deploy.zip . -x "*.git*" -x "venv/*" -x "__pycache__/*" -x "*.pyc"
az webapp deploy \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --src-path deploy.zip \
  --type zip
```

#### Application settings (environment variables)

Set these in **Configuration → Application settings** (or via CLI). **Do not** commit secrets to git.

```bash
az webapp config appsettings set \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --settings \
    APP_ENV=production \
    DEBUG=False \
    PORT=8000 \
    CORS_ORIGINS="https://<YOUR-STATIC-WEB-APP-URL>.azurestaticapps.net,https://<YOUR-CUSTOM-DOMAIN>" \
    SUPABASE_URL="<YOUR_SUPABASE_URL>" \
    SUPABASE_ANON_KEY="<YOUR_SUPABASE_ANON_KEY>" \
    SUPABASE_SERVICE_ROLE_KEY="<YOUR_SERVICE_ROLE_KEY>" \
    SUPABASE_DB_URL="<YOUR_SUPABASE_DB_URL>" \
    AZURE_OPENAI_ENDPOINT="<YOUR_AZURE_OPENAI_ENDPOINT>" \
    AZURE_OPENAI_API_KEY="<YOUR_AZURE_OPENAI_KEY>" \
    AZURE_OPENAI_DEPLOYMENT_NAME="gpt-4o" \
    AZURE_SPEECH_KEY="<YOUR_AZURE_SPEECH_KEY>" \
    AZURE_SPEECH_REGION="<YOUR_AZURE_SPEECH_REGION>" \
    AZURE_STORAGE_CONNECTION_STRING="<YOUR_AZURE_STORAGE_CONNECTION_STRING>" \
    SECRET_KEY="<GENERATE_STRONG_SECRET_KEY>" \
    GOOGLE_API_KEY="<YOUR_GOOGLE_API_KEY>"
```

Use **Azure Key Vault references** in production instead of plain values where possible.

#### Scaling (backend)

- **Scale up (size):** App Service plan → **Scale up (App Service plan)**. Use **P1v2** or **P2v2** for more CPU/memory under load.
- **Scale out (instances):** **Scale out (App Service plan)** → set instance count (e.g. 2–10).
- **Autoscale:** **Scale out** → **Custom autoscale**:
  - Scale out: e.g. CPU > 70% or HTTP queue length > 10
  - Scale in: CPU < 30%

**Important:** If you scale to **multiple instances**, move in-memory **sessions** to **Azure Cache for Redis** (see [Production notes](#production-notes-before-scaling-out)).

---

### 1.2 Frontend — Azure Static Web Apps

#### Create Static Web App (Azure CLI)

```bash
# Create Static Web App
az staticwebapp create \
  --name "soft-skill-check-web" \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION \
  --source https://github.com/<YOUR_ORG>/<YOUR_REPO> \
  --branch main \
  --app-location "frontend" \
  --output-location "dist" \
  --login-with-github
```

Or use **Azure Portal**: Static Web Apps → Create → Connect GitHub → set **App location** `frontend`, **Output location** `dist`.

#### Build-time environment variables

Configure in **Configuration → Application settings** for the Static Web App:

| Name | Value |
|------|--------|
| `VITE_API_BASE_URL` | `https://<YOUR-BACKEND-APP-NAME>.azurewebsites.net` |
| `VITE_SUPABASE_URL` | Your Supabase project URL |
| `VITE_SUPABASE_ANON_KEY` | Your Supabase anon key |
| `VITE_API_TIMEOUT` | `30000` |

**Build command:** `npm run build` (default when app location is `frontend`).

#### Custom domain and CORS

- Add custom domain in Static Web Apps and optionally in App Service.
- Ensure backend **CORS_ORIGINS** includes:
  - `https://<static-web-app>.azurestaticapps.net`
  - Your custom domain(s)

---

## Option 2: Single App Service (Backend + static frontend)

One App Service serves both API and the SPA. Simpler to operate, but frontend and backend scale together.

### Setup

1. **Build frontend** with API base URL:
   ```bash
   cd frontend
   echo "VITE_API_BASE_URL=https://<YOUR-APP-NAME>.azurewebsites.net" > .env.production
   npm run build
   ```
2. **Backend** serves static files from `frontend/dist`:
   - Mount `frontend/dist` as static (e.g. via `FastAPI StaticFiles` at `/`) and reserve `/api`, `/health`, etc. for the API.
3. **Deploy** the monorepo (backend + `frontend/dist`) to one App Service.

Scaling: **Scale out** and **Scale up** the single plan. Same Redis-for-sessions requirement if you use multiple instances.

---

## Option 3: Docker (Web App for Containers / Container Apps)

Best if you prefer containers and already use Docker.

### Backend Dockerfile

Use the provided `backend/Dockerfile` (includes `ffmpeg` and `libsndfile1` for audio). Build and push to Azure Container Registry:

```bash
cd backend
docker build -t <YOUR_ACR>.azurecr.io/soft-skill-check-api:latest .
docker push <YOUR_ACR>.azurecr.io/soft-skill-check-api:latest
```

### Deploy to Web App for Containers

```bash
az webapp create \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --plan $PLAN_NAME \
  --deployment-container-image-name <YOUR_ACR>.azurecr.io/soft-skill-check-api:latest
```

Build and push image to **Azure Container Registry**, then deploy. Use **Azure Container Apps** if you want event-driven scaling and microservices-style ops.

---

## Production Notes (before scaling out)

1. **Sessions (multi-instance):** The app uses in-memory session storage. With **multiple App Service instances**, use **Azure Cache for Redis** (or similar) and switch the session store to Redis. See `PRODUCTION_ANALYSIS.md`.
2. **Health checks:** App Service **Health check** → Path: `/health`. Use for load balancer probes.
3. **Logging:** Enable **App Service Logging** (Application Logging, HTTP logs). Consider **Application Insights**.
4. **Secrets:** Prefer **Key Vault references** in App Service application settings over plain env vars.
5. **Security:** Enforce **HTTPS only**, restrict **CORS**, fix **JWT verification** (see `PRODUCTION_ANALYSIS.md`), add **rate limiting** on expensive endpoints.

6. **Audio (FFmpeg):** The app uses `imageio-ffmpeg` and audio libs. The default Python App Service image may lack system libraries. If you hit audio conversion errors, use **Option 3 (Docker)** with a Dockerfile that installs `ffmpeg` and `libsndfile1` (see example in Option 3).

---

## Scaling Cheat Sheet

| Goal | Action |
|------|--------|
| More traffic, same latency | **Scale out** (more instances) |
| Heavier per-request work | **Scale up** (larger SKU) |
| Traffic spikes | **Autoscale** on CPU / custom metrics |
| Multiple instances | **Redis** (or DB) for sessions |
| Global users | **Static Web Apps** (frontend) + **Azure Front Door** (optional) |

---

## CI/CD with GitHub Actions

A workflow deploys the **backend** to Azure App Service on push to `main` (when `backend/**` or the workflow file changes).

### Setup

1. **Create a service principal** (one-time):
   ```bash
   az ad sp create-for-rbac --name "soft-skill-check-deploy" --role contributor \
     --scopes /subscriptions/<SUBSCRIPTION_ID>/resourceGroups/<RESOURCE_GROUP> \
     --sdk-auth
   ```
   Copy the JSON output.

2. **Add GitHub secrets**:
   - `AZURE_CREDENTIALS`: paste the full JSON from step 1.

3. **Set workflow app name**: Edit `.github/workflows/deploy-azure.yml` and set `AZURE_WEBAPP_NAME` to your backend App Service name.

4. **Optional:** Create a `production` environment in GitHub (Settings → Environments) and add approval rules. The workflow uses `environment: production`; remove that line if you don’t use environments.

### Frontend (Static Web Apps)

Connect your repo to Azure Static Web Apps in the portal. Azure adds its own workflow to build and deploy the frontend on push. Set `VITE_API_BASE_URL` and other `VITE_*` vars in the Static Web App **Configuration** so they’re available at build time.

---

## Quick Start Checklist

- [ ] Create resource group and App Service plan (B2 or higher for prod).
- [ ] Create App Service (Python 3.11), set startup command, deploy backend.
- [ ] Configure all backend env vars (including CORS with frontend URL).
- [ ] Create Static Web App, connect repo, set `app-location` / `output-location`.
- [ ] Set `VITE_API_BASE_URL` and Supabase vars for frontend build.
- [ ] Add frontend URL to backend CORS.
- [ ] Test end-to-end (login → assessment → results).
- [ ] Enable Autoscale and Health check; plan Redis when going multi-instance.

---

## Cost (rough, monthly)

- **App Service** B2: ~\$55; P1v2: ~\$85.
- **Static Web Apps** Free: \$0; Standard: ~\$9.
- **Supabase / Azure OpenAI / Speech / Blob:** per your usage.

Use **Azure Pricing Calculator** for your region and SKUs.
