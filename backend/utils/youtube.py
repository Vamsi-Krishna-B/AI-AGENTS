import os
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from dotenv import load_dotenv

load_dotenv()

SCOPES = ["https://www.googleapis.com/auth/youtube.upload",
          "https://www.googleapis.com/auth/youtube.readonly",
          "https://www.googleapis.com/auth/yt-analytics.readonly"]

TOKEN_PATH = os.path.join(os.path.dirname(__file__), "..", "storage", "youtube_token.pickle")
CLIENT_SECRETS = {
    "installed": {
        "client_id": os.getenv("YOUTUBE_CLIENT_ID", ""),
        "client_secret": os.getenv("YOUTUBE_CLIENT_SECRET", ""),
        "redirect_uris": [os.getenv("YOUTUBE_REDIRECT_URI", "http://localhost:8000/auth/youtube/callback")],
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://accounts.google.com/o/oauth2/token",
    }
}


def _get_credentials():
    creds = None
    if os.path.exists(TOKEN_PATH):
        with open(TOKEN_PATH, "rb") as f:
            creds = pickle.load(f)
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        with open(TOKEN_PATH, "wb") as f:
            pickle.dump(creds, f)
    return creds


def get_youtube_client():
    creds = _get_credentials()
    if not creds or not creds.valid:
        raise RuntimeError(
            "YouTube credentials not found or invalid. "
            "Complete OAuth flow at /auth/youtube first."
        )
    return build("youtube", "v3", credentials=creds)


def upload_video(
    video_path: str,
    title: str,
    description: str,
    tags: list[str],
    thumbnail_path: str | None = None,
    category_id: str = "28",
    publish_at: str | None = None,
) -> dict:
    """Upload a video to YouTube and optionally set a thumbnail."""
    youtube = get_youtube_client()

    status = "private" if publish_at else "public"
    body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": tags,
            "categoryId": category_id,
        },
        "status": {
            "privacyStatus": status,
        },
    }
    if publish_at:
        body["status"]["publishAt"] = publish_at

    media = MediaFileUpload(video_path, chunksize=-1, resumable=True, mimetype="video/mp4")
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)

    response = None
    while response is None:
        _, response = request.next_chunk()

    video_id = response["id"]

    if thumbnail_path and os.path.exists(thumbnail_path):
        youtube.thumbnails().set(
            videoId=video_id,
            media_body=MediaFileUpload(thumbnail_path),
        ).execute()

    return {
        "youtube_video_id": video_id,
        "youtube_url": f"https://www.youtube.com/watch?v={video_id}",
        "scheduled_publish_time": publish_at,
    }


def get_channel_analytics(channel_id: str) -> list[dict]:
    """Fetch basic video stats for a channel."""
    youtube = get_youtube_client()
    res = youtube.channels().list(
        part="statistics", id=channel_id
    ).execute()
    stats = res.get("items", [{}])[0].get("statistics", {})

    videos_res = youtube.search().list(
        part="snippet", channelId=channel_id, order="date", maxResults=10, type="video"
    ).execute()

    results = []
    for item in videos_res.get("items", []):
        vid_id = item["id"]["videoId"]
        vid_res = youtube.videos().list(part="statistics", id=vid_id).execute()
        vid_stats = vid_res.get("items", [{}])[0].get("statistics", {})
        results.append({
            "video_id": vid_id,
            "title": item["snippet"]["title"],
            "youtube_url": f"https://www.youtube.com/watch?v={vid_id}",
            "views": int(vid_stats.get("viewCount", 0)),
            "likes": int(vid_stats.get("likeCount", 0)),
            "comments": int(vid_stats.get("commentCount", 0)),
        })
    return results
