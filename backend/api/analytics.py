"""
Analytics API routes.
"""
from datetime import datetime
from fastapi import APIRouter, HTTPException
from db.mongo import analytics_collection, settings_collection
from utils.youtube import get_channel_analytics

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("")
async def get_analytics(refresh: bool = False):
    settings = await settings_collection().find_one({}, {"_id": 0}) or {}
    channel_id = settings.get("channel_id", "")

    if refresh and channel_id:
        try:
            fresh_data = get_channel_analytics(channel_id)
            for item in fresh_data:
                await analytics_collection().update_one(
                    {"video_id": item["video_id"]},
                    {"$set": {**item, "fetched_at": datetime.utcnow().isoformat()}},
                    upsert=True,
                )
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"YouTube API error: {e}")

    results = []
    async for doc in analytics_collection().find({}, {"_id": 0}).sort("fetched_at", -1):
        results.append(doc)
    return results
