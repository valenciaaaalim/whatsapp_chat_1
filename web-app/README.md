# WhatsApp Risk Assessment Web App

This is a web application for user testing of the WhatsApp risk assessment system, converted from the native Android app.

## Architecture

- **Backend**: FastAPI (Python) with SQLite/PostgreSQL database
- **Frontend**: React with React Router
- **Services**: 
  - Gemini API integration for risk assessment
  - XML Extractor service (stubbed for now)
- **Deployment**: Docker containers, Google Cloud Run, Cloudflare

## Local Development

### Prerequisites

- Python 3.11+
- Node.js 16+ and npm
- Docker and Docker Compose (for full stack)

### Backend Setup

1. **Navigate to backend directory:**
   ```bash
   cd web-app/backend
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set environment variables:**
   Create a `.env` file:
   ```env
   GEMINI_API_KEY=your_gemini_api_key_here
   DATABASE_URL=sqlite:///./web_app.db
   FRONTEND_URL=http://localhost:3000
   ```

5. **Initialize database and seed data:**
   ```bash
   python seed_data.py
   ```
   
   This will load conversations from `../../annotated_test.json` (the root of the repository).

6. **Run the backend:**
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

### Frontend Setup

1. **Navigate to frontend directory:**
   ```bash
   cd web-app/frontend
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Set environment variables:**
   Create a `.env` file:
   ```env
   REACT_APP_API_URL=http://localhost:8000
   ```

4. **Run the frontend:**
   ```bash
   npm start
   ```

The frontend will be available at `http://localhost:3000`.

### Docker Compose Setup (Recommended)

1. **Set environment variables:**
   Create a `.env` file in the `web-app` directory:
   ```env
   GEMINI_API_KEY=your_gemini_api_key_here
   ```

2. **Build and start services:**
   ```bash
   cd web-app
   docker-compose up --build
   ```

3. **Seed the database:**
   ```bash
   docker-compose exec web-app-backend python seed_data.py
   ```

The backend will be available at `http://localhost:8000` and frontend at `http://localhost:3000` (if you run it separately).

## Database Seeding

The seed script loads conversations from `annotated_test.json` in the repository root:

```bash
cd web-app/backend
python seed_data.py
```

Or with Docker:
```bash
docker-compose exec web-app-backend python seed_data.py
```

## API Endpoints

### Participants
- `POST /api/participants` - Create participant (A/B assignment)
- `GET /api/participants/{id}` - Get participant

### Conversations
- `GET /api/conversations/seed` - Get all seed conversations
- `GET /api/conversations/seed/{id}` - Get specific conversation
- `POST /api/conversations/sessions/{participant_id}/{conversation_id}` - Create session
- `GET /api/conversations/sessions/{session_id}` - Get session

### Risk Assessment
- `POST /api/risk/assess` - Assess risk of draft message

### User Inputs
- `POST /api/user-inputs` - Capture user input
- `POST /api/user-inputs/with-warning` - Capture input with warning data

### Surveys
- `POST /api/surveys/responses` - Submit survey response
- `GET /api/surveys/responses/{participant_id}` - Get responses

### Completion
- `GET /api/completion/prolific` - Get Prolific completion URL
- `GET /api/completion/redirect` - Redirect to Prolific

## Security Features

- CORS configuration
- Environment-based secrets
- HTTPS-only cookies (in production)
- Input validation via Pydantic
- Security headers middleware

## Deployment

See [DEPLOYMENT.md](./DEPLOYMENT.md) for detailed deployment instructions.

## Testing Flow

1. User arrives at welcome screen
2. Participant is created and assigned to variant A or B
3. User goes through three conversation scenarios
4. After each conversation, user answers survey questions
5. User is redirected to Prolific completion URL

## Project Structure

```
web-app/
├── backend/              # FastAPI backend
│   ├── app/             # Application code
│   │   ├── routers/     # API route handlers
│   │   ├── services/    # Business logic
│   │   ├── models.py    # Database models
│   │   └── schemas.py   # Pydantic schemas
│   ├── Dockerfile
│   ├── requirements.txt
│   └── seed_data.py     # Database seeding script
├── frontend/             # React frontend
│   ├── src/
│   │   ├── components/  # React components
│   │   └── App.js       # Main app
│   └── package.json
├── xml-extractor/       # XML extractor stub service
├── docker-compose.yml   # Multi-service setup
├── README.md           # This file
└── DEPLOYMENT.md       # Deployment guide
```
