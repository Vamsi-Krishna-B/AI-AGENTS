"""
Orchestrator Agent — master controller that coordinates all other agents.
"""
import asyncio
import uuid
from datetime import datetime
from typing import Any

from db.mongo import jobs_collection, logs_collection, settings_collection
from agents.research_agent import ResearchAgent
from agents.script_agent import ScriptAgent
from agents.media_agent import MediaAgent
from agents.voice_agent import VoiceAgent
from agents.editor_agent import EditorAgent
from agents.thumbnail_agent import ThumbnailAgent
from agents.upload_agent import UploadAgent

STAGES = ["research", "script", "media", "voice", "editor", "thumbnail", "upload"]
AI_STAGES = {"research", "script"}


class OrchestratorAgent:
    def __init__(self):
        self.ws_manager = None  # injected by main.py at runtime

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    async def _log(self, job_id: str, agent: str, level: str, message: str):
        doc = {
            "job_id": job_id,
            "agent": agent,
            "timestamp": datetime.utcnow().isoformat(),
            "level": level,
            "message": message,
        }
        await logs_collection().insert_one(doc)
        if self.ws_manager:
            await self.ws_manager.broadcast({"type": "log", "job_id": job_id, **doc})

    async def _set_stage_status(self, job_id: str, stage: str, status: str, output: Any = None):
        update: dict = {f"stages.{stage}.status": status}
        if output is not None:
            update[f"stages.{stage}.output"] = output
        update[f"stages.{stage}.updated_at"] = datetime.utcnow().isoformat()
        await jobs_collection().update_one({"job_id": job_id}, {"$set": update})
        if self.ws_manager:
            await self.ws_manager.broadcast(
                {"type": "stage_update", "job_id": job_id, "stage": stage, "status": status}
            )

    async def _get_job(self, job_id: str) -> dict:
        return await jobs_collection().find_one({"job_id": job_id})

    async def _get_settings(self) -> dict:
        doc = await settings_collection().find_one({})
        return doc or {}

    # ------------------------------------------------------------------
    # Job creation
    # ------------------------------------------------------------------

    async def create_job(
        self,
        autonomous: bool = False,
        format_type: str = "faceless",
        generation_provider: str = "gemini",
        generation_model: str | None = None,
        retry_of: str | None = None,
    ) -> str:
        job_id = str(uuid.uuid4())
        generation_provider = (generation_provider or "gemini").lower()
        stages_init = {s: {"status": "pending", "output": None, "updated_at": None} for s in STAGES}
        doc = {
            "job_id": job_id,
            "status": "created",
            "created_at": datetime.utcnow().isoformat(),
            "format_type": format_type,
            "autonomous": autonomous,
            "generation_provider": generation_provider,
            "generation_model": generation_model,
            "retry_of": retry_of,
            "stages": stages_init,
            "video_metadata": {},
            "youtube_url": None,
        }
        await jobs_collection().insert_one(doc)
        return job_id

    # ------------------------------------------------------------------
    # Full pipeline run
    # ------------------------------------------------------------------

    async def run(self, job_id: str):
        job = await self._get_job(job_id)
        if not job:
            return

        settings = await self._get_settings()
        autonomous = job.get("autonomous", settings.get("autonomous_mode", False))

        await jobs_collection().update_one(
            {"job_id": job_id}, {"$set": {"status": "running"}}
        )
        await self._log(job_id, "orchestrator", "INFO", "Pipeline started")

        generation_provider = (job.get("generation_provider") or settings.get("generation_provider", "gemini")).lower()
        generation_model = job.get("generation_model") or settings.get("generation_model")
        await jobs_collection().update_one(
            {"job_id": job_id},
            {"$set": {"generation_provider": generation_provider, "generation_model": generation_model}},
        )
        context: dict = {
            "_generation": {
                "provider": generation_provider,
                "model": generation_model,
                "api_key": settings.get("groq_api_key") if generation_provider == "groq" else settings.get("gemini_api_key"),
            },
        }
        model_label = generation_model or ("llama-3.3-70b-versatile" if generation_provider == "groq" else "default")
        await self._log(job_id, "orchestrator", "INFO", f"Generation provider: {generation_provider} ({model_label})")

        for stage in STAGES:
            current = await self._get_job(job_id)
            if current and current.get("status") == "cancelled":
                await self._log(job_id, "orchestrator", "INFO", "Pipeline cancelled")
                return

            # In manual mode, wait for approval
            if not autonomous:
                await self._set_stage_status(job_id, stage, "awaiting_approval")
                await self._log(job_id, "orchestrator", "INFO", f"Stage '{stage}' awaiting approval")
                # Wait until approved or cancelled
                for _ in range(3600):  # max 1 hour wait
                    await asyncio.sleep(1)
                    current = await self._get_job(job_id)
                    stage_status = current["stages"][stage]["status"]
                    if stage_status == "approved":
                        await self._log(job_id, "orchestrator", "INFO", f"Stage '{stage}' approved; starting next step")
                        break
                    if current["status"] == "cancelled":
                        await self._log(job_id, "orchestrator", "INFO", "Pipeline cancelled")
                        return
                else:
                    await self._log(job_id, "orchestrator", "WARNING", f"Timeout waiting for approval of '{stage}'")
                    await jobs_collection().update_one({"job_id": job_id}, {"$set": {"status": "failed"}})
                    return

            output = await self.run_stage(job_id, stage, context)
            current = await self._get_job(job_id)
            if current and current.get("status") == "cancelled":
                await self._log(job_id, "orchestrator", "INFO", "Pipeline cancelled")
                return
            if output is None:
                await jobs_collection().update_one({"job_id": job_id}, {"$set": {"status": "failed"}})
                return
            context[stage] = output

        await jobs_collection().update_one({"job_id": job_id}, {"$set": {"status": "completed"}})
        await self._log(job_id, "orchestrator", "INFO", "Pipeline completed successfully")

    # ------------------------------------------------------------------
    # Single stage runner
    # ------------------------------------------------------------------

    async def run_stage(self, job_id: str, stage: str, context: dict | None = None) -> Any:
        if context is None:
            # Rebuild context from stored outputs
            job = await self._get_job(job_id)
            settings = await self._get_settings()
            context = {s: job["stages"][s].get("output") for s in STAGES if job["stages"][s].get("output")}
            generation_provider = (job.get("generation_provider") or settings.get("generation_provider", "gemini")).lower()
            context["_generation"] = {
                "provider": generation_provider,
                "model": job.get("generation_model") or settings.get("generation_model"),
                "api_key": settings.get("groq_api_key") if generation_provider == "groq" else settings.get("gemini_api_key"),
            }

        agent_map = {
            "research": ResearchAgent,
            "script": ScriptAgent,
            "media": MediaAgent,
            "voice": VoiceAgent,
            "editor": EditorAgent,
            "thumbnail": ThumbnailAgent,
            "upload": UploadAgent,
        }

        await self._set_stage_status(job_id, stage, "running")
        await self._log(job_id, stage, "INFO", f"Starting {stage} stage")

        try:
            agent_cls = agent_map[stage]
            agent = agent_cls()
            generation = context.get("_generation", {})
            provider = generation.get("provider", "gemini")
            model = generation.get("model") or ("llama-3.3-70b-versatile" if provider == "groq" else "default")
            if stage in AI_STAGES:
                await self._log(job_id, stage, "INFO", f"Calling {provider} model for {stage}: {model}")
                await self._log(job_id, stage, "INFO", "Waiting for AI model response")
            output = await agent.run(job_id, context)
            if stage in AI_STAGES:
                await self._log(job_id, stage, "INFO", "AI model response received")
            await self._set_stage_status(job_id, stage, "done", output)
            await self._log(job_id, stage, "INFO", f"{stage} stage completed")
            return output
        except Exception as exc:
            await self._set_stage_status(job_id, stage, "failed")
            await self._log(job_id, stage, "ERROR", str(exc))
            return None
