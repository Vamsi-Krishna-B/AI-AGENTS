"""
FastAPI application entry point.
"""
import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from dotenv import load_dotenv

from db.mongo import connect_db, close_db, settings_collection
from api.jobs import router as jobs_router
from api.settings import router as settings_router
from api.analytics import router as analytics_router
from agents.orchestrator import OrchestratorAgent
from tasks.pipeline_tasks import run_pipeline

load_dotenv()

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")
logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


# ---------------------------------------------------------------------------
# WebSocket connection manager
# ---------------------------------------------------------------------------

class WebSocketManager:
    def __init__(self):
        self.active: list[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active.append(ws)

    def disconnect(self, ws: WebSocket):
        self.active.remove(ws)

    async def broadcast(self, data: dict):
        dead = []
        for ws in self.active:
            try:
                await ws.send_json(data)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.active.remove(ws)


ws_manager = WebSocketManager()


# ---------------------------------------------------------------------------
# Cron scheduler helpers
# ---------------------------------------------------------------------------

async def _scheduled_pipeline_job():
    """Triggered by APScheduler — starts an autonomous pipeline job."""
    settings = await settings_collection().find_one({}) or {}
    if not settings.get("autonomous_mode", False):
        return
    orchestrator = OrchestratorAgent()
    format_type = settings.get("default_format", "faceless")
    job_id = await orchestrator.create_job(
        autonomous=True,
        format_type=format_type,
        generation_provider=settings.get("generation_provider", "gemini"),
        generation_model=settings.get("generation_model"),
    )
    logger.info("Cron: starting autonomous pipeline job %s", job_id)
    run_pipeline.delay(job_id)


def _reschedule(schedule_time: str):
    """Remove old cron job and add a new one at the given HH:MM (UTC)."""
    scheduler.remove_all_jobs()
    try:
        hour, minute = schedule_time.split(":")
        scheduler.add_job(
            _scheduled_pipeline_job,
            CronTrigger(hour=int(hour), minute=int(minute), timezone="UTC"),
            id="daily_pipeline",
            replace_existing=True,
        )
        logger.info("Scheduled autonomous pipeline at %s UTC", schedule_time)
    except Exception as exc:
        logger.warning("Failed to schedule cron job: %s", exc)


# ---------------------------------------------------------------------------
# App lifecycle
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_db()
    # Inject WebSocket manager into OrchestratorAgent class
    OrchestratorAgent.ws_manager = ws_manager  # type: ignore[attr-defined]

    # Start the scheduler and load saved schedule time
    scheduler.start()
    settings = await settings_collection().find_one({}) or {}
    schedule_time = settings.get("schedule_time", "09:00")
    _reschedule(schedule_time)

    yield

    scheduler.shutdown(wait=False)
    await close_db()


app = FastAPI(title="YouTube Channel Manager", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL, "http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(jobs_router)
app.include_router(settings_router)
app.include_router(analytics_router)


# ---------------------------------------------------------------------------
# WebSocket endpoint
# ---------------------------------------------------------------------------

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws_manager.connect(ws)
    try:
        while True:
            # Keep the connection alive; clients can send pings
            await ws.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(ws)


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

@app.get("/health")
async def health():
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# YouTube OAuth flow (for initial token setup)
# ---------------------------------------------------------------------------

@app.get("/auth/youtube")
async def youtube_auth():
    from google_auth_oauthlib.flow import Flow
    import json, os

    client_config = {
        "installed": {
            "client_id": os.getenv("YOUTUBE_CLIENT_ID", ""),
            "client_secret": os.getenv("YOUTUBE_CLIENT_SECRET", ""),
            "redirect_uris": [os.getenv("YOUTUBE_REDIRECT_URI", "http://localhost:8000/auth/youtube/callback")],
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://accounts.google.com/o/oauth2/token",
        }
    }
    flow = Flow.from_client_config(
        client_config,
        scopes=[
            "https://www.googleapis.com/auth/youtube.upload",
            "https://www.googleapis.com/auth/youtube.readonly",
        ],
        redirect_uri=os.getenv("YOUTUBE_REDIRECT_URI", "http://localhost:8000/auth/youtube/callback"),
    )
    auth_url, _ = flow.authorization_url(prompt="consent")
    return {"auth_url": auth_url}


@app.get("/auth/youtube/callback")
async def youtube_callback(code: str):
    import pickle, os
    from google_auth_oauthlib.flow import Flow

    client_config = {
        "installed": {
            "client_id": os.getenv("YOUTUBE_CLIENT_ID", ""),
            "client_secret": os.getenv("YOUTUBE_CLIENT_SECRET", ""),
            "redirect_uris": [os.getenv("YOUTUBE_REDIRECT_URI", "http://localhost:8000/auth/youtube/callback")],
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://accounts.google.com/o/oauth2/token",
        }
    }
    flow = Flow.from_client_config(
        client_config,
        scopes=[
            "https://www.googleapis.com/auth/youtube.upload",
            "https://www.googleapis.com/auth/youtube.readonly",
        ],
        redirect_uri=os.getenv("YOUTUBE_REDIRECT_URI", "http://localhost:8000/auth/youtube/callback"),
    )
    flow.fetch_token(code=code)
    creds = flow.credentials

    token_path = os.path.join(os.path.dirname(__file__), "storage", "youtube_token.pickle")
    os.makedirs(os.path.dirname(token_path), exist_ok=True)
    with open(token_path, "wb") as f:
        pickle.dump(creds, f)

    return {"message": "YouTube authentication successful. You can close this window."}
