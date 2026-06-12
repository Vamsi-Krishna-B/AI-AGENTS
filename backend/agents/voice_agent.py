"""
Voice Agent — generates voiceover audio from script text.
"""
import os
import time
from utils.gemini import gemini_tts

AUDIO_DIR = os.path.join(os.path.dirname(__file__), "..", "storage", "audio")


class VoiceAgent:
    async def run(self, job_id: str, context: dict) -> dict:
        os.makedirs(AUDIO_DIR, exist_ok=True)
        script = context.get("script", {})
        voiceover_text = script.get("voiceover_text", script.get("full_script", ""))

        output_path = os.path.join(AUDIO_DIR, f"{job_id}_{int(time.time())}.mp3")
        await gemini_tts(voiceover_text, output_path)

        # Estimate duration from file size / bitrate (128 kbps MP3)
        size_bytes = os.path.getsize(output_path)
        estimated_duration = size_bytes / (128 * 1000 / 8)

        return {
            "audio_path": output_path,
            "duration": round(estimated_duration, 2),
        }
