# Deployment Guide (Vercel + Cloud Run)

This guide matches the current production target:

- Frontend: Vercel (`web-app/frontend`)
- Backend: FastAPI on Cloud Run (built from `web-app/backend`)
- Database: Cloud SQL PostgreSQL (`DATABASE_URL`)
- CI/CD: Cloud Build trigger on `main`

## 1) Prerequisites

- GCP project with billing
- `gcloud` CLI authenticated
- Cloud Run, Cloud Build, Artifact Registry, Cloud SQL APIs enabled
- Vercel project connected to this repository

Set common variables:

```bash
export PROJECT_ID=your-project-id
export REGION=us-central1
export SERVICE_NAME=whatsapp-chat-1

gcloud config set project "$PROJECT_ID"
```

Enable APIs:

```bash
gcloud services enable run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com sqladmin.googleapis.com secretmanager.googleapis.com
```

## 2) Backend Continuous Deployment (Cloud Build -> Cloud Run)

Your trigger should build from:

- Directory: `web-app/backend`
- Dockerfile: `Dockerfile`
- Branch: `main`

If this trigger already exists, verify it still points to `web-app/backend`.

After each push to `main`, Cloud Build should:

1. Build backend image
2. Deploy a new Cloud Run revision

## 3) Cloud Run Environment Variables

Set/update backend env vars on the Cloud Run service:

```bash
gcloud run services update "$SERVICE_NAME" \
  --region "$REGION" \
  --update-env-vars "FRONTEND_URL=https://your-vercel-domain.vercel.app,DATABASE_URL=postgresql+psycopg2://USER:PASSWORD@HOST:5432/DBNAME,LLM_SCENARIO_MAX_CALLS=10,GEMINI_FIRST_MODEL=gemini-3-flash-preview,FIRST_MODEL_THINKING_POWER=medium,FIRST_MODEL_TIMEOUT_SECONDS=20,FIRST_MODEL_MAX_ATTEMPTS=1,GEMINI_SECOND_MODEL=gemini-2.5-flash,SECOND_MODEL_THINKING_POWER=-1,SECOND_MODEL_TIMEOUT_SECONDS=20,SECOND_MODEL_MAX_ATTEMPTS=1"
```

Required/important variables:

- `DATABASE_URL`
- `FRONTEND_URL` (must include protocol, for example `https://...vercel.app`)
- `GEMINI_FIRST_MODEL`
- `FIRST_MODEL_THINKING_POWER`
- `FIRST_MODEL_TIMEOUT_SECONDS`
- `FIRST_MODEL_MAX_ATTEMPTS`
- `GEMINI_SECOND_MODEL`
- `SECOND_MODEL_THINKING_POWER`
- `SECOND_MODEL_TIMEOUT_SECONDS`
- `SECOND_MODEL_MAX_ATTEMPTS`
- `LLM_SCENARIO_MAX_CALLS`
- API key: `GEMINI_API_KEY`

### Secret Manager (recommended)

```bash
# Create secret once
echo -n "your-gemini-api-key" | gcloud secrets create gemini-api-key --data-file=-

# Grant Cloud Run service account access
gcloud secrets add-iam-policy-binding gemini-api-key \
  --member="serviceAccount:PROJECT_NUMBER-compute@developer.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"

# Attach secret to service env
gcloud run services update "$SERVICE_NAME" \
  --region "$REGION" \
  --update-secrets "GEMINI_API_KEY=gemini-api-key:latest"
```

## 4) Cloud SQL PostgreSQL

Use a PostgreSQL URL in `DATABASE_URL`.

Example format:

```text
postgresql+psycopg2://USER:PASSWORD@HOST:5432/DBNAME
```

If using Cloud SQL Unix socket, use the corresponding socket-based SQLAlchemy URL supported by your environment.

## 5) Frontend Deployment (Vercel)

In Vercel project settings:

1. Root Directory: `web-app/frontend`
2. Build command: `npm run build`
3. Output directory: `build` (CRA)
4. Environment variables:

```env
REACT_APP_BACKEND_BASE_URL=https://YOUR_CLOUD_RUN_URL
```

Then redeploy from Vercel Deployments.

## 6) Verification

Get backend URL:

```bash
gcloud run services describe "$SERVICE_NAME" --region "$REGION" --format='value(status.url)'
```

Health check:

```bash
curl "https://YOUR_CLOUD_RUN_URL/healthz"
```

Read logs:

```bash
gcloud run services logs read "$SERVICE_NAME" --region "$REGION" --limit 100
```

## 7) Common Issues

1. CORS blocked from Vercel
- Ensure `FRONTEND_URL` exactly matches deployed Vercel origin.

2. Backend tries localhost from frontend
- Ensure Vercel env var `REACT_APP_BACKEND_BASE_URL` is set.
- Redeploy frontend after env var changes.

3. DB errors on startup
- Check `DATABASE_URL` value and Cloud SQL connectivity.

4. Cloud Build path failures
- Ensure trigger build context is `web-app/backend`.

## 8) Local Notes

- Backend listens on Cloud Run injected `PORT` (normally `8080`).
- Local run command remains:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8080
```
