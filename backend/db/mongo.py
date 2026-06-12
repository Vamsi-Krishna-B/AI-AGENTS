import os
from typing import Optional

from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
MONGODB_DB = os.getenv("MONGODB_DB", "youtube_manager")

client: Optional[AsyncIOMotorClient] = None


async def connect_db():
    global client
    if client is None:
        client = AsyncIOMotorClient(MONGODB_URI)


async def close_db():
    global client
    if client:
        client.close()
        client = None


def get_db():
    global client
    if client is None:
        client = AsyncIOMotorClient(MONGODB_URI)
    return client[MONGODB_DB]


def jobs_collection():
    return get_db()["jobs"]


def logs_collection():
    return get_db()["pipeline_logs"]


def settings_collection():
    return get_db()["settings"]


def analytics_collection():
    return get_db()["analytics"]
