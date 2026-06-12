"""
Media Agent — generates video clips for each scene.
"""
import os
import time
from utils.veo import generate_clip

RAW_VIDEO_DIR = os.path.join(os.path.dirname(__file__), "..", "storage", "videos", "raw")


class MediaAgent:
    async def run(self, job_id: str, context: dict) -> dict:
        research = context.get("research", {})
        script = context.get("script", {})
        format_type = research.get("format_type", "faceless")
        scenes = script.get("scenes", [])

        clip_paths = []

        for scene in scenes:
            scene_num = scene.get("scene_number", 0)
            duration = scene.get("duration_seconds", 10)
            query = scene.get("b_roll_query", research.get("topic", "technology"))

            if format_type == "faceless":
                out = os.path.join(RAW_VIDEO_DIR, f"{job_id}_scene{scene_num}_{int(time.time())}.mp4")
                path = generate_clip(query, out, duration_seconds=duration)
                clip_paths.append({"scene": scene_num, "path": path, "source": "veo"})

            elif format_type in ("avatar", "animated"):
                out = os.path.join(RAW_VIDEO_DIR, f"{job_id}_scene{scene_num}_{int(time.time())}.mp4")
                veo_prompt = scene.get("visual_description", query)
                if format_type == "animated":
                    veo_prompt = f"animation style, {veo_prompt}"
                path = generate_clip(veo_prompt, out, duration_seconds=duration)
                clip_paths.append({"scene": scene_num, "path": path, "source": "veo"})

        return {"clip_paths": clip_paths, "format_type": format_type}
