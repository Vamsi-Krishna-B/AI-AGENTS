"""
Research Agent — discovers trending topics via YouTube + Gemini, decides video format.
"""
import os
from utils.llm import generate_json


def _get_youtube_trending_topics(max_results: int = 10) -> list[str]:
    """
    Fetch titles of currently trending YouTube videos (category: Science & Tech = 28,
    Entertainment = 24) using the YouTube Data API v3.
    Returns a list of video titles to feed into Gemini for topic selection.
    """
    try:
        from googleapiclient.discovery import build
        api_key = os.getenv("GEMINI_API_KEY", "")  # reuse or use a dedicated YT key
        yt_key = os.getenv("YOUTUBE_API_KEY", api_key)
        if not yt_key:
            return []
        youtube = build("youtube", "v3", developerKey=yt_key)
        response = youtube.videos().list(
            part="snippet",
            chart="mostPopular",
            regionCode="US",
            videoCategoryId="28",  # Science & Technology
            maxResults=max_results,
        ).execute()
        titles = [item["snippet"]["title"] for item in response.get("items", [])]
        # Also fetch entertainment
        response2 = youtube.videos().list(
            part="snippet",
            chart="mostPopular",
            regionCode="US",
            videoCategoryId="24",  # Entertainment
            maxResults=max_results,
        ).execute()
        titles += [item["snippet"]["title"] for item in response2.get("items", [])]
        return titles
    except Exception:
        return []


class ResearchAgent:
    async def run(self, job_id: str, context: dict) -> dict:
        generation = context.get("_generation", {})
        provider = generation.get("provider", "gemini")
        model = generation.get("model")
        api_key = generation.get("api_key")

        # Step 1: gather trending YouTube titles
        trending_titles = _get_youtube_trending_topics(max_results=10)
        trending_section = ""
        if trending_titles:
            joined = "\n".join(f"- {t}" for t in trending_titles[:15])
            trending_section = f"\n\nCurrently trending YouTube videos:\n{joined}\n\nUse the above trends to inform your topic selection."

        prompt = f"""
You are a YouTube research analyst specialising in AI, tech, and entertainment content.
Generate a trending video topic idea with the following JSON structure:

{{
  "topic": "short topic name",
  "title": "catchy YouTube video title (under 70 chars)",
  "description": "YouTube video description (150-300 chars)",
  "tags": ["tag1", "tag2", "tag3", "tag4", "tag5"],
  "format_type": "faceless",
  "research_summary": "2-3 sentence summary of why this topic is trending and what the video should cover"
}}

format_type must be one of: "avatar", "faceless", "animated"
Choose "faceless" for news/explainer, "avatar" for personal brand, "animated" for educational.
{trending_section}
"""
        data = generate_json(prompt, provider=provider, model=model, api_key=api_key)
        data["generation_provider"] = provider
        if model:
            data["generation_model"] = model

        return data
