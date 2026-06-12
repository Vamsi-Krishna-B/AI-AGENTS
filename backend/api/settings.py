"""
Settings API routes.
"""
from fastapi import APIRouter, Request
from pydantic import BaseModel
from typing import Optional
from db.mongo import settings_collection

router = APIRouter(prefix="/api/settings", tags=["settings"])

DEFAULT_SETTINGS = {
    "autonomous_mode": False,
    "schedule_time": "09:00",
    "channel_id": "",
    "default_format": "faceless",
    "generation_provider": "gemini",
    "generation_model": "",
}


class SettingsUpdate(BaseModel):
    autonomous_mode: Optional[bool] = None
    schedule_time: Optional[str] = None
    channel_id: Optional[str] = None
    default_format: Optional[str] = None
    generation_provider: Optional[str] = None
    generation_model: Optional[str] = None
    gemini_api_key: Optional[str] = None
    groq_api_key: Optional[str] = None
    youtube_client_id: Optional[str] = None
    youtube_client_secret: Optional[str] = None


@router.get("")
async def get_settings():
    doc = await settings_collection().find_one({}, {"_id": 0})
    if not doc:
        return DEFAULT_SETTINGS
    return {**DEFAULT_SETTINGS, **doc}


@router.put("")
async def update_settings(request: Request, body: SettingsUpdate):
    update = {k: v for k, v in body.model_dump().items() if v is not None}
    if "generation_provider" in update:
        update["generation_provider"] = str(update["generation_provider"]).lower()
    await settings_collection().update_one({}, {"$set": update}, upsert=True)
    doc = await settings_collection().find_one({}, {"_id": 0})

    # If schedule_time changed, update the cron job live
    if body.schedule_time:
        try:
            from main import _reschedule
            _reschedule(body.schedule_time)
        except Exception:
            pass  # scheduler not available (e.g. tests)

    return {**DEFAULT_SETTINGS, **(doc or {})}
