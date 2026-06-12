import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()

VEO_API_KEY = os.getenv("VEO_API_KEY", "")
GCP_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT", "")

VEO_ENDPOINT = (
    "https://us-central1-aiplatform.googleapis.com/v1/projects/"
    f"{GCP_PROJECT}/locations/us-central1/publishers/google/models/veo-001:predict"
)


def generate_clip(prompt: str, output_path: str, duration_seconds: int = 5) -> str:
    """
    Call Google Veo API to generate a video clip from a text prompt.
    Saves the result to output_path and returns the path.
    Falls back to a black placeholder clip if Veo is unavailable.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    if not VEO_API_KEY or not GCP_PROJECT:
        return _create_placeholder_clip(output_path, duration_seconds)

    headers = {
        "Authorization": f"Bearer {VEO_API_KEY}",
        "Content-Type": "application/json",
    }
    body = {
        "instances": [{"prompt": prompt}],
        "parameters": {"sampleCount": 1, "durationSeconds": duration_seconds},
    }

    try:
        resp = requests.post(VEO_ENDPOINT, headers=headers, json=body, timeout=120)
        resp.raise_for_status()
        data = resp.json()
        video_b64 = data["predictions"][0]["bytesBase64Encoded"]
        import base64

        with open(output_path, "wb") as f:
            f.write(base64.b64decode(video_b64))
        return output_path
    except Exception:
        return _create_placeholder_clip(output_path, duration_seconds)


def _create_placeholder_clip(output_path: str, duration_seconds: int) -> str:
    """Create a black placeholder video clip using MoviePy."""
    from moviepy.editor import ColorClip

    clip = ColorClip(size=(1280, 720), color=(0, 0, 0), duration=duration_seconds)
    clip.write_videofile(output_path, fps=24, logger=None)
    clip.close()
    return output_path
