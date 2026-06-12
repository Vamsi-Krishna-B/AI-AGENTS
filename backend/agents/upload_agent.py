"""
Upload Agent — authenticates with YouTube and uploads the final video.
"""
from utils.youtube import upload_video


class UploadAgent:
    async def run(self, job_id: str, context: dict) -> dict:
        research = context.get("research", {})
        editor = context.get("editor", {})
        thumbnail = context.get("thumbnail", {})

        video_path = editor.get("final_video_path")
        thumbnail_path = thumbnail.get("thumbnail_path")

        if not video_path:
            raise ValueError("No final video path found in editor output")

        result = upload_video(
            video_path=video_path,
            title=research.get("title", "AI Video"),
            description=research.get("description", ""),
            tags=research.get("tags", []),
            thumbnail_path=thumbnail_path,
            publish_at=None,  # publish immediately; set a datetime string to schedule
        )
        return result
