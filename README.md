# Autonomous YouTube Channel Manager

A full-stack multi-agent AI system that autonomously manages a YouTube channel — from idea generation to video upload.

---

## Quick Start

### Prerequisites
- Docker Desktop (running)
- Local MongoDB on port 27017 (the app connects to your host MongoDB from inside containers)
- Node.js 18+ *(only needed for local dev, not Docker)*
- Python 3.11+ *(only needed for local dev, not Docker)*

### 1. Fill in API keys
Edit `.env` in the project root:
```
GEMINI_API_KEY=your_gemini_api_key
YOUTUBE_API_KEY=your_youtube_data_api_key    # public API key for trending search
YOUTUBE_CLIENT_ID=...
YOUTUBE_CLIENT_SECRET=...
GOOGLE_CLOUD_PROJECT=...   # for Veo
```

### 2. Run the full app with Docker

```bash
# Build and start all containers (backend, celery, redis, frontend)
docker compose up --build

# Or run in the background
docker compose up --build -d
```

| Service | URL |
|---------|-----|
| Frontend (nginx) | http://localhost:5174 |
| Backend API | http://localhost:8000 |
| Redis | localhost:6379 (internal) |
| MongoDB | your local machine :27017 |

> **Note:** Containers reach your local MongoDB via `host.docker.internal:27017`.
> Make sure MongoDB is running locally before starting Docker Compose.

### 3. Run the dev stack without rebuilding on every code change

```bash
# First run, or after dependency/Dockerfile changes
docker compose -f docker-compose.dev.yml up --build

# Normal development runs
docker compose -f docker-compose.dev.yml up
```

The dev stack bind-mounts `backend/` and `frontend/`, runs FastAPI with `--reload`, runs Celery through `watchfiles`, and runs the Vite dev server.
The frontend is exposed on http://localhost:5174 by default to avoid clashing with a local Vite server on port 5173. To use a different host port, run `FRONTEND_PORT=5180 docker compose -f docker-compose.dev.yml up`.

VS Code users can also run **Dev Containers: Reopen in Container**. The config lives in `.devcontainer/devcontainer.json`.

### 4. Project tooling

This repo uses:

- `uv` for backend Python dependency management (`backend/pyproject.toml` and `backend/uv.lock`)
- `mise` as a root-level task runner (`mise.toml`)
- `npm` for the frontend

Useful commands:

```bash
mise run dev          # start hot-reload dev stack
mise run dev-build    # rebuild and start hot-reload dev stack
mise run dev-down     # stop dev stack
```

Rebuild the backend/celery containers only after dependency or Dockerfile changes.

### 5. YouTube OAuth (first time)
Open http://localhost:8000/auth/youtube in your browser and complete the Google OAuth flow. The token is saved inside the backend container volume.

### Stop everything
```bash
# If you started the production stack
docker compose down

# If you started the dev stack
docker compose -f docker-compose.dev.yml down
```

---

## Local Development (without Docker)

```bash
# Start Redis only via Docker
docker compose up redis -d

# Backend
cd backend
uv sync
uv run uvicorn main:app --reload --port 8000

# Celery (separate terminal)
uv run celery -A tasks.celery_app worker --loglevel=info

# Frontend
cd frontend && npm run dev   # → http://localhost:5173
```

---

## Architecture

| Agent | Responsibility |
|-------|---------------|
| Orchestrator | Coordinates all agents, tracks pipeline state |
| Research | Finds trending topics via Gemini Pro |
| Script | Generates full video script with scenes |
| Media | Generates clips with Veo |
| Voice | Generates voiceover via Gemini TTS |
| Editor | Stitches clips + audio with MoviePy |
| Thumbnail | Generates thumbnail with Pillow |
| Upload | Uploads to YouTube via Data API v3 |

---

## Project Structure

```
backend/
  main.py               FastAPI entry point + WebSocket
  agents/               8 AI agents
  api/                  REST route handlers
  db/mongo.py           Motor async MongoDB client
  tasks/                Celery workers
  utils/                API wrappers (Gemini, Veo, YouTube)
  storage/              Generated files (videos, audio, thumbnails)

frontend/
  src/
    pages/              Dashboard, Pipeline, Script, Thumbnail, Calendar, Analytics, Settings
    components/         AgentStatusCard, LiveLogStream, AutonomousToggle, StageApproval
    hooks/              useWebSocket
    api/client.ts       Axios API client
```
# AI-AGENTS
