"""
Script Agent — generates a full video script with scenes from research output.
"""
from utils.llm import generate_json


class ScriptAgent:
    async def run(self, job_id: str, context: dict) -> dict:
        generation = context.get("_generation", {})
        provider = generation.get("provider", "gemini")
        model = generation.get("model")
        api_key = generation.get("api_key")
        research = context.get("research", {})
        topic = research.get("topic", "AI trends")
        summary = research.get("research_summary", "")
        format_type = research.get("format_type", "faceless")

        prompt = f"""
You are a professional YouTube scriptwriter.
Write a complete video script for the following topic:

Topic: {topic}
Research Summary: {summary}
Format: {format_type}

Return JSON with this exact structure:
{{
  "full_script": "complete script text",
  "scenes": [
    {{
      "scene_number": 1,
      "type": "hook",
      "duration_seconds": 15,
      "script_text": "scene script text",
      "visual_description": "what should appear on screen",
      "b_roll_query": "search query for stock footage or veo prompt"
    }}
  ],
  "estimated_duration": 180,
  "voiceover_text": "clean voiceover text without stage directions"
}}

Include 3 scene types in order: hook (15s), main_content (split into 3-5 scenes), cta (15-20s).
Total video should be 2-4 minutes (120-240 seconds).
"""
        data = generate_json(prompt, provider=provider, model=model, api_key=api_key)
        data["generation_provider"] = provider
        if model:
            data["generation_model"] = model
        return data
