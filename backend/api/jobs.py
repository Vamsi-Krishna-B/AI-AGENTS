"""
Jobs API routes.
"""
from datetime import datetime
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from db.mongo import jobs_collection, logs_collection, settings_collection
from agents.orchestrator import OrchestratorAgent
from tasks.pipeline_tasks import run_pipeline

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


class StartJobRequest(BaseModel):
    autonomous: bool = False
    format_type: str = "faceless"
    generation_provider: str | None = None
    generation_model: str | None = None


def _clean_provider(provider: str | None, fallback: str = "gemini") -> str:
    return (provider or fallback).lower()


@router.post("/start")
async def start_job(req: StartJobRequest):
    settings = await settings_collection().find_one({}) or {}
    orchestrator = OrchestratorAgent()
    job_id = await orchestrator.create_job(
        autonomous=req.autonomous,
        format_type=req.format_type,
        generation_provider=_clean_provider(req.generation_provider, settings.get("generation_provider", "gemini")),
        generation_model=req.generation_model or settings.get("generation_model"),
    )
    # Dispatch to Celery
    run_pipeline.delay(job_id)
    return {"job_id": job_id, "status": "started"}


@router.get("")
async def list_jobs():
    jobs = []
    async for job in jobs_collection().find({}, {"_id": 0}).sort("created_at", -1).limit(50):
        jobs.append(job)
    return jobs


@router.get("/{job_id}")
async def get_job(job_id: str):
    job = await jobs_collection().find_one({"job_id": job_id}, {"_id": 0})
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    logs = []
    async for log in logs_collection().find({"job_id": job_id}, {"_id": 0}).sort("timestamp", 1):
        logs.append(log)
    job["logs"] = logs
    return job


@router.put("/{job_id}/approve/{stage}")
async def approve_stage(job_id: str, stage: str):
    result = await jobs_collection().update_one(
        {"job_id": job_id},
        {"$set": {f"stages.{stage}.status": "approved", f"stages.{stage}.updated_at": datetime.utcnow().isoformat()}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Job not found")
    await logs_collection().insert_one(
        {
            "job_id": job_id,
            "agent": "orchestrator",
            "timestamp": datetime.utcnow().isoformat(),
            "level": "INFO",
            "message": f"Approval received for stage '{stage}'",
        }
    )
    return {"job_id": job_id, "stage": stage, "status": "approved"}


@router.put("/{job_id}/cancel")
async def cancel_job(job_id: str):
    result = await jobs_collection().update_one(
        {"job_id": job_id},
        {"$set": {"status": "cancelled"}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Job not found")
    return {"job_id": job_id, "status": "cancelled"}


@router.delete("/{job_id}")
async def delete_job(job_id: str):
    job = await jobs_collection().find_one({"job_id": job_id}, {"_id": 0, "status": 1})
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    await jobs_collection().delete_one({"job_id": job_id})
    await logs_collection().delete_many({"job_id": job_id})
    return {"job_id": job_id, "status": "deleted"}


@router.post("/{job_id}/retry")
async def retry_job(job_id: str):
    original = await jobs_collection().find_one({"job_id": job_id}, {"_id": 0})
    if not original:
        raise HTTPException(status_code=404, detail="Job not found")
    if original.get("status") not in {"failed", "cancelled"}:
        raise HTTPException(status_code=400, detail="Only failed or cancelled jobs can be retried")

    orchestrator = OrchestratorAgent()
    retry_job_id = await orchestrator.create_job(
        autonomous=original.get("autonomous", False),
        format_type=original.get("format_type", "faceless"),
        generation_provider=_clean_provider(original.get("generation_provider")),
        generation_model=original.get("generation_model"),
        retry_of=job_id,
    )
    await logs_collection().insert_one(
        {
            "job_id": retry_job_id,
            "agent": "orchestrator",
            "timestamp": datetime.utcnow().isoformat(),
            "level": "INFO",
            "message": f"Retry created from job {job_id}",
        }
    )
    run_pipeline.delay(retry_job_id)
    return {"job_id": retry_job_id, "retry_of": job_id, "status": "started"}
