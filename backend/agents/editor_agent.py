"""
Editor Agent — stitches video clips and audio into a final MP4.
"""
import os
import glob
import time

FINAL_VIDEO_DIR = os.path.join(os.path.dirname(__file__), "..", "storage", "videos", "final")
ASSETS_MUSIC_DIR = os.path.join(os.path.dirname(__file__), "..", "assets", "music")


class EditorAgent:
    async def run(self, job_id: str, context: dict) -> dict:
        from moviepy.editor import (
            VideoFileClip, AudioFileClip, concatenate_videoclips,
            CompositeVideoClip, TextClip, CompositeAudioClip
        )

        os.makedirs(FINAL_VIDEO_DIR, exist_ok=True)

        media = context.get("media", {})
        voice = context.get("voice", {})
        research = context.get("research", {})

        clip_paths = media.get("clip_paths", [])
        audio_path = voice.get("audio_path")
        title = research.get("title", "")

        # Load and concatenate video clips
        clips = []
        for cp in sorted(clip_paths, key=lambda x: x["scene"]):
            path = cp["path"]
            if os.path.exists(path):
                try:
                    c = VideoFileClip(path).resize((1280, 720))
                    clips.append(c)
                except Exception:
                    continue

        if not clips:
            # Fallback: create a black clip
            from moviepy.editor import ColorClip
            clips = [ColorClip(size=(1280, 720), color=(0, 0, 0), duration=5)]

        video = concatenate_videoclips(clips, method="compose")

        # Add voiceover
        if audio_path and os.path.exists(audio_path):
            voiceover = AudioFileClip(audio_path)
            # Loop or trim voiceover to match video duration
            if voiceover.duration < video.duration:
                from moviepy.audio.AudioClip import concatenate_audioclips
                repeats = int(video.duration // voiceover.duration) + 1
                voiceover = concatenate_audioclips([voiceover] * repeats)
            voiceover = voiceover.subclip(0, video.duration)

            # Optionally mix background music
            bg_music_files = glob.glob(os.path.join(ASSETS_MUSIC_DIR, "*.mp3"))
            if bg_music_files:
                bg = AudioFileClip(bg_music_files[0]).volumex(0.1)
                if bg.duration < video.duration:
                    from moviepy.audio.AudioClip import concatenate_audioclips
                    repeats = int(video.duration // bg.duration) + 1
                    bg = concatenate_audioclips([bg] * repeats)
                bg = bg.subclip(0, video.duration)
                final_audio = CompositeAudioClip([voiceover, bg])
            else:
                final_audio = voiceover

            video = video.set_audio(final_audio)

        # Add lower-third title text
        if title:
            try:
                txt = TextClip(title, fontsize=32, color="white", bg_color="black",
                               size=(1280, None), method="caption")
                txt = txt.set_position(("center", "bottom")).set_duration(min(5, video.duration))
                video = CompositeVideoClip([video, txt])
            except Exception:
                pass  # ImageMagick not available — skip text overlay

        output_path = os.path.join(FINAL_VIDEO_DIR, f"{job_id}_{int(time.time())}.mp4")
        video.write_videofile(output_path, fps=24, codec="libx264", audio_codec="aac", logger=None)
        video.close()

        return {
            "final_video_path": output_path,
            "duration": round(video.duration, 2),
        }
