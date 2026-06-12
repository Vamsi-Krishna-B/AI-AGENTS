"""
Provider-aware helpers for JSON/text generation.
"""
import json
import os
from typing import Any

import requests

from utils.gemini import gemini_generate_text


DEFAULT_GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")


def _strip_json_fences(raw: str) -> str:
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    if raw.endswith("```"):
        raw = raw[:-3]
    return raw.strip()


def _extract_json(raw: str) -> str:
    raw = _strip_json_fences(raw)
    start = raw.find("{")
    end = raw.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return raw
    return raw[start : end + 1]


def _groq_generate_text(
    prompt: str,
    model: str | None = None,
    temperature: float = 0.7,
    api_key: str | None = None,
    json_mode: bool = False,
) -> str:
    api_key = api_key or os.getenv("GROQ_API_KEY", "")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY is required when using the GROQ provider")

    payload = {
        "model": model or DEFAULT_GROQ_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": temperature,
    }
    if json_mode:
        payload["response_format"] = {"type": "json_object"}

    response = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "ai-agents-backend/1.0",
        },
        json=payload,
        timeout=90,
    )
    response.raise_for_status()
    data = response.json()
    return data["choices"][0]["message"]["content"]


def generate_text(
    prompt: str,
    provider: str = "gemini",
    model: str | None = None,
    temperature: float = 0.7,
    api_key: str | None = None,
    json_mode: bool = False,
) -> str:
    if provider == "groq":
        return _groq_generate_text(
            prompt,
            model=model,
            temperature=temperature,
            api_key=api_key,
            json_mode=json_mode,
        )
    return gemini_generate_text(prompt, temperature=temperature, model=model, api_key=api_key)


def generate_json(
    prompt: str,
    provider: str = "gemini",
    model: str | None = None,
    temperature: float = 0.5,
    api_key: str | None = None,
) -> dict[str, Any]:
    json_prompt = (
        prompt
        + "\n\nRespond ONLY with valid JSON, no markdown code fences, no extra text."
    )
    raw = generate_text(
        json_prompt,
        provider=provider,
        model=model,
        temperature=temperature,
        api_key=api_key,
        json_mode=True,
    )
    candidate = _extract_json(raw)
    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        repair_prompt = f"""
Repair the following malformed JSON into valid JSON.
Do not change the data model, do not add commentary, and return only JSON.

Malformed JSON:
{candidate}
"""
        repaired = generate_text(
            repair_prompt,
            provider=provider,
            model=model,
            temperature=0,
            api_key=api_key,
            json_mode=True,
        )
        repaired_candidate = _extract_json(repaired)
        try:
            return json.loads(repaired_candidate)
        except json.JSONDecodeError as exc:
            snippet = candidate[:1000]
            raise ValueError(f"Model returned invalid JSON after repair: {exc}. Raw response starts: {snippet}") from exc
