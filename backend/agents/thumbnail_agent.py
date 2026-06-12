"""
Thumbnail Agent — generates a thumbnail image with title text overlay.
"""
import os
import time
import base64
import io
from utils.gemini import gemini_generate_text

THUMBNAIL_DIR = os.path.join(os.path.dirname(__file__), "..", "storage", "thumbnails")


class ThumbnailAgent:
    async def run(self, job_id: str, context: dict) -> dict:
        from PIL import Image, ImageDraw, ImageFont

        os.makedirs(THUMBNAIL_DIR, exist_ok=True)

        research = context.get("research", {})
        title = research.get("title", "AI Video")
        topic = research.get("topic", "AI")

        # Try Gemini image generation
        thumbnail_path = os.path.join(THUMBNAIL_DIR, f"{job_id}_{int(time.time())}.jpg")
        background = self._generate_background(topic, title, thumbnail_path)

        # Add title text overlay using Pillow
        img = Image.open(background).convert("RGB")
        img = img.resize((1280, 720))
        draw = ImageDraw.Draw(img)

        # Draw semi-transparent banner at bottom
        overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
        overlay_draw = ImageDraw.Draw(overlay)
        overlay_draw.rectangle([(0, 560), (1280, 720)], fill=(0, 0, 0, 180))
        img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
        draw = ImageDraw.Draw(img)

        # Draw title text
        try:
            font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", size=52)
        except Exception:
            font = ImageFont.load_default()

        # Word wrap
        words = title.split()
        lines = []
        current = ""
        for word in words:
            test = f"{current} {word}".strip()
            bbox = draw.textbbox((0, 0), test, font=font)
            if bbox[2] > 1200:
                lines.append(current)
                current = word
            else:
                current = test
        if current:
            lines.append(current)

        y = 580
        for line in lines[:2]:
            draw.text((40, y), line, fill="white", font=font)
            y += 60

        img.save(thumbnail_path, "JPEG", quality=95)
        return {"thumbnail_path": thumbnail_path}

    def _generate_background(self, topic: str, title: str, output_path: str) -> str:
        """Attempt Gemini image generation; fall back to gradient background."""
        try:
            import google.generativeai as genai
            from utils.gemini import GEMINI_MODEL

            model = genai.GenerativeModel(GEMINI_MODEL)
            prompt = (
                f"Create a vibrant YouTube thumbnail background image for a video about '{topic}'. "
                "Cinematic, high-contrast, eye-catching. No text. 16:9 aspect ratio."
            )
            response = model.generate_content(prompt)
            # If image parts are returned
            for part in response.parts:
                if hasattr(part, "inline_data"):
                    img_data = base64.b64decode(part.inline_data.data)
                    with open(output_path, "wb") as f:
                        f.write(img_data)
                    return output_path
        except Exception:
            pass

        # Fallback: gradient image
        return self._create_gradient_background(topic, output_path)

    def _create_gradient_background(self, topic: str, output_path: str) -> str:
        from PIL import Image
        import numpy as np

        width, height = 1280, 720
        # Simple top-to-bottom gradient (dark blue to purple)
        img_array = np.zeros((height, width, 3), dtype=np.uint8)
        for y in range(height):
            r = int(10 + (80 - 10) * y / height)
            g = int(10 + (0 - 10) * y / height)
            b = int(80 + (120 - 80) * y / height)
            img_array[y, :] = [r, g, b]

        img = Image.fromarray(img_array)
        img.save(output_path, "JPEG", quality=95)
        return output_path
