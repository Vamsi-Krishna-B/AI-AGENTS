Build a full-stack Autonomous YouTube Channel Manager with a multi-agent architecture. Here are the complete specifications:

---

## PROJECT OVERVIEW
An AI-powered system that autonomously manages a YouTube channel (AI/entertainment niche) — from idea generation to video upload — with a web dashboard for monitoring and control.

---

## TECH STACK
- Frontend: React + Vite (TypeScript)
- Backend: Python FastAPI
- Database: Local MongoDB (via PyMongo / Motor for async)
- AI Brain: Google Gemini Pro API (gemini-1.5-pro)
- Video Generation: Google Veo API
- Voice: Gemini TTS
- Video Stitching: MoviePy
- Video Generation: Veo
- Publishing: YouTube Data API v3
- Task Queue: Celery + Redis (for parallel agent execution)
- Agent Orchestration: Custom async task runner using FastAPI background tasks + Celery workers

---

## MULTI-AGENT ARCHITECTURE

Build 8 agents, each as a separate Python module under `/agents/`:

### 1. Orchestrator Agent (`agents/orchestrator.py`)
- Master controller that coordinates all other agents
- Reads the "autonomous mode" toggle from MongoDB
- In autonomous mode: runs the full pipeline daily on a cron schedule
- In manual mode: waits for user approval at each stage
- Tracks pipeline state per job in MongoDB
- Sends status updates to dashboard via WebSocket

### 2. Research Agent (`agents/research_agent.py`)
- Uses Gemini Pro to discover trending AI/tech/entertainment topics
- Searches YouTube trending via YouTube Data API
- Veo API for generated video clips
- Decides video format: "avatar" | "faceless" | "animated" based on topic type
- Outputs: topic, title, description, tags, format_type, research_summary

### 3. Script Agent (`agents/script_agent.py`)
- Takes research output, generates full video script using Gemini Pro
- Script includes: hook (0-15s), main content, CTA
- Splits script into scenes with timing
- Outputs: full_script, scenes[], estimated_duration, voiceover_text

### 4. Media Agent (`agents/media_agent.py`)
- Based on format_type:
  - "avatar": Generates Veo video clips from scene prompts, saves to /storage/videos/raw/
  - "faceless": Generates topic-matched video clips with Veo
  - "animated": Generates animated clips via Veo with animation-style prompts
- Outputs: list of local video clip file paths per scene

### 5. Voice Agent (`agents/voice_agent.py`)
- Uses Gemini TTS to generate voiceover from voiceover_text
- Saves audio to /storage/audio/
- Returns: audio file path, duration

### 6. Editor Agent (`agents/editor_agent.py`)
- Uses MoviePy to stitch video clips + voiceover audio
- Adds: background music (from /assets/music/), lower thirds text, transitions
- Exports final MP4 to /storage/videos/final/
- Returns: final_video_path, duration

### 7. Thumbnail Agent (`agents/thumbnail_agent.py`)
- Uses Gemini Pro image generation to create thumbnail
- Adds title text overlay using Pillow
- Saves to /storage/thumbnails/
- Returns: thumbnail_path

### 8. Upload Agent (`agents/upload_agent.py`)
- Authenticates with YouTube Data API v3 using OAuth2
- Uploads final video + thumbnail
- Sets title, description, tags, category, schedule time
- Returns: youtube_video_id, youtube_url, scheduled_publish_time

---

## MONGODB SCHEMA

Collections:
- `jobs`: { job_id, status, created_at, format_type, autonomous, stages: { research, script, media, voice, editor, thumbnail, upload }, video_metadata, youtube_url }
- `pipeline_logs`: { job_id, agent, timestamp, level, message }
- `settings`: { autonomous_mode: bool, schedule_time: string, channel_id, default_format }
- `analytics`: { video_id, youtube_url, views, likes, comments, fetched_at }

---

## FASTAPI BACKEND

Routes under `/api/`:

- `POST /jobs/start` — Start a new pipeline job
- `GET /jobs` — List all jobs with status
- `GET /jobs/{job_id}` — Get full job detail + logs
- `PUT /jobs/{job_id}/approve/{stage}` — Approve a stage in manual mode
- `PUT /jobs/{job_id}/cancel` — Cancel a running job
- `GET /settings` — Get current settings
- `PUT /settings` — Update settings (autonomous toggle, schedule, etc.)
- `GET /analytics` — Get channel analytics
- `WebSocket /ws` — Real-time pipeline status updates to dashboard

---

## REACT + VITE FRONTEND

Pages/sections:

### Dashboard (home)
- Live pipeline status for current/recent jobs
- Autonomous mode toggle (big, prominent)
- Quick stats: total videos, last upload, next scheduled

### Pipeline Monitor
- Real-time log stream per job via WebSocket
- Stage-by-stage status: pending → running → done → failed
- Each stage shows: agent name, time taken, output preview
- Approve/reject buttons per stage (manual mode only)

### Content Calendar
- Calendar view showing scheduled uploads
- Ability to drag/reschedule

### Script Editor
- Full script display with scene breakdown
- Editable text fields per scene
- "Regenerate" button per scene (calls Gemini)

### Thumbnail Preview
- Shows generated thumbnail
- Option to regenerate or upload custom

### Settings
- Autonomous mode toggle
- Daily schedule time picker
- Channel ID input
- Default video format selector
- API key management (Gemini, YouTube)

### Analytics
- Views, likes, comments per video
- Simple recharts graphs

---

## PROJECT STRUCTURE
/
├── backend/
│   ├── main.py                  # FastAPI app entry
│   ├── agents/
│   │   ├── orchestrator.py
│   │   ├── research_agent.py
│   │   ├── script_agent.py
│   │   ├── media_agent.py
│   │   ├── voice_agent.py
│   │   ├── editor_agent.py
│   │   ├── thumbnail_agent.py
│   │   └── upload_agent.py
│   ├── api/
│   │   ├── jobs.py
│   │   ├── settings.py
│   │   └── analytics.py
│   ├── db/
│   │   └── mongo.py             # Motor async MongoDB client
│   ├── tasks/
│   │   └── celery_app.py        # Celery config for parallel agents
│   ├── utils/
│   │   ├── gemini.py            # Gemini API wrapper
│   │   ├── veo.py               # Veo API wrapper
│   │   ├── youtube.py           # YouTube Data API wrapper
│   └── storage/
│       ├── videos/raw/
│       ├── videos/final/
│       ├── audio/
│       └── thumbnails/
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── Dashboard.tsx
│   │   │   ├── PipelineMonitor.tsx
│   │   │   ├── ScriptEditor.tsx
│   │   │   ├── Thumbnail.tsx
│   │   │   ├── Calendar.tsx
│   │   │   ├── Analytics.tsx
│   │   │   └── Settings.tsx
│   │   ├── components/
│   │   │   ├── AgentStatusCard.tsx
│   │   │   ├── LiveLogStream.tsx
│   │   │   ├── AutonomousToggle.tsx
│   │   │   └── StageApproval.tsx
│   │   ├── hooks/
│   │   │   └── useWebSocket.ts
│   │   └── api/
│   │       └── client.ts
│   └── vite.config.ts
├── .env                         # All API keys
└── docker-compose.yml           # MongoDB + Redis

---

## KEY BEHAVIOURS

1. Autonomous Mode ON: Orchestrator runs full pipeline daily at scheduled time with no human input
2. Autonomous Mode OFF: Each stage pauses and waits for dashboard approval before proceeding
3. Agents run in parallel where possible (Media + Voice can run simultaneously after Script)
4. All agent logs stream live to dashboard via WebSocket
5. All generated files saved locally before upload
6. Job state persisted in MongoDB so pipeline survives server restarts
7. Failed stages can be retried individually without restarting the whole pipeline

---

## ENVIRONMENT VARIABLES (.env)
GEMINI_API_KEY=
VEO_API_KEY=
YOUTUBE_CLIENT_ID=
YOUTUBE_CLIENT_SECRET=
MONGODB_URI=mongodb://localhost:27017
REDIS_URL=redis://localhost:6379
STORAGE_BASE_PATH=./backend/storage

---

Start by scaffolding the full project structure, then implement each agent module, then the FastAPI routes, then the React frontend. Prioritize the Orchestrator, Research, and Script agents first as they are the core pipeline entry points.

quit
