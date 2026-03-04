# WhatsApp Risk Assessment Web App

Web study application for risk-assessment experiments.

## Current Deployment Shape

- Frontend: React app on Vercel (no frontend Cloud Run service)
- Backend: FastAPI on Google Cloud Run
- Database: Cloud SQL PostgreSQL via `DATABASE_URL`
- CI/CD: Cloud Build trigger builds from `web-app/backend`

## Repository Layout

```text
web-app/
├── backend/
│   ├── app/
│   │   ├── routers/
│   │   ├── services/
│   │   ├── models.py
│   │   ├── schemas.py
│   │   ├── database.py
│   │   └── main.py
│   ├── requirements.txt
│   ├── Dockerfile
│   └── gliner_service.py
├── frontend/
│   ├── src/
│   └── package.json
├── README.md
└── DEPLOYMENT.md
```

## Local Development

### Prerequisites

- Python 3.11+
- Node.js 18+ and npm

### Backend

1. Go to backend:

```bash
cd web-app/backend
```

2. Create and activate venv:

```bash
python -m venv venv
source venv/bin/activate
```

3. Install deps:

```bash
pip install -r requirements.txt
```

4. Set env vars (example):

```env
# API key
GEMINI_API_KEY=your_key

# Model routing
GEMINI_FIRST_MODEL=gemini-3-flash-preview
FIRST_MODEL_THINKING_POWER=medium
FIRST_MODEL_TIMEOUT_SECONDS=20
FIRST_MODEL_MAX_ATTEMPTS=1

GEMINI_SECOND_MODEL=gemini-2.5-flash
SECOND_MODEL_THINKING_POWER=-1
SECOND_MODEL_TIMEOUT_SECONDS=20
SECOND_MODEL_MAX_ATTEMPTS=1

# LLM budget
LLM_SCENARIO_MAX_CALLS=10

# CORS
FRONTEND_URL=http://localhost:3000

# Optional for local DB-backed flows
# If omitted, app still starts; DB-backed endpoints return 503.
DATABASE_URL=postgresql+psycopg2://user:password@localhost:5432/whatsapp_1
```

5. Start backend:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8080
```

Health check:

```bash
curl http://localhost:8080/healthz
```

### Frontend

1. Go to frontend:

```bash
cd web-app/frontend
```

2. Install deps:

```bash
npm install
```

3. Set frontend env var:

```env
REACT_APP_BACKEND_BASE_URL=http://localhost:8080
```

4. Start frontend:

```bash
npm start
```

Frontend runs on `http://localhost:3000`.

## Seed Conversations

Conversation scenarios are loaded from:

- `web-app/backend/app/assets/annotated_test.json`

At runtime they are exposed by:

- `GET /api/conversations/seed`

## Key API Endpoints

Participants and progress:

- `POST /api/participants`
- `GET /api/participants/{participant_id}`
- `GET /api/participants/by-prolific/{prolific_id}`
- `GET /api/participants/{participant_id}/progress`
- `GET /api/participants/{participant_id}/data`

Risk and PII:

- `POST /api/risk/assess`
- `POST /pii/detect`
- `GET /pii/status`

Conversation seed:

- `GET /api/conversations/seed`
- `POST /api/conversations/reload` (dev use)

Study responses:

- `POST /api/participants/{participant_id}/baseline-assessment`
- `POST /api/participants/message`
- `POST /api/participants/{participant_id}/post-scenario-survey`
- `POST /api/participants/{participant_id}/pii-disclosure`
- `POST /api/participants/{participant_id}/sus-responses`
- `POST /api/participants/{participant_id}/end-of-study-survey`

Completion:

- `GET /api/completion/prolific`

## Deployment

See [DEPLOYMENT.md](./DEPLOYMENT.md) for Cloud Run + Vercel deployment instructions.
