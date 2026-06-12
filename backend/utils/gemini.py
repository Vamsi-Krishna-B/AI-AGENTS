import os
import json
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY", ""))

GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-pro")

def gemini_generate_text(
    prompt: str,
    temperature: float = 0.7,
    model: str | None = None,
    api_key: str | None = None,
) -> str:
    """Generate text from Gemini Pro."""
    if api_key:
        genai.configure(api_key=api_key)
    active_model = genai.GenerativeModel(model or GEMINI_MODEL)
    response = active_model.generate_content(
        prompt,
        generation_config=genai.types.GenerationConfig(
            temperature=temperature,
        ),
    )
    return response.text


def gemini_generate_json(prompt: str, temperature: float = 0.5) -> dict:
    """Generate and parse JSON from Gemini Pro."""
    json_prompt = (
        prompt
        + "\n\nRespond ONLY with valid JSON, no markdown code fences, no extra text."
    )
    raw = gemini_generate_text(json_prompt, temperature=temperature)
    # Strip potential code fences just in case
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    if raw.endswith("```"):
        raw = raw[:-3]
    return json.loads(raw.strip())


async def gemini_tts(text: str, output_path: str) -> str:
    """
    Generate voiceover using Gemini TTS.
    Falls back to a placeholder if TTS is not available.
    Returns the output file path.
    """
    try:
        import google.cloud.texttospeech as tts

        tts_client = tts.TextToSpeechClient()
        synthesis_input = tts.SynthesisInput(text=text)
        voice = tts.VoiceSelectionParams(
            language_code="en-US",
            ssml_gender=tts.SsmlVoiceGender.NEUTRAL,
        )
        audio_config = tts.AudioConfig(
            audio_encoding=tts.AudioEncoding.MP3,
        )
        response = tts_client.synthesize_speech(
            input=synthesis_input, voice=voice, audio_config=audio_config
        )
        with open(output_path, "wb") as f:
            f.write(response.audio_content)
        return output_path
    except Exception:
        # Placeholder: create a silent audio file using moviepy
        from moviepy.audio.AudioClip import AudioClip
        import numpy as np

        duration = max(5, len(text) // 15)  # rough estimate ~15 chars/sec
        silence = AudioClip(lambda t: np.zeros((2,)), duration=duration, fps=44100)
        silence.write_audiofile(output_path, logger=None)
        return output_path
