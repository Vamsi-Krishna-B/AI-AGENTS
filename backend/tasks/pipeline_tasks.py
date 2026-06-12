import asyncio
from tasks.celery_app import celery_app
from agents.orchestrator import OrchestratorAgent
from db.mongo import close_db, connect_db


async def _run_pipeline(job_id: str):
    await connect_db()
    try:
        orchestrator = OrchestratorAgent()
        await orchestrator.run(job_id)
    finally:
        await close_db()


async def _run_single_stage(job_id: str, stage: str):
    await connect_db()
    try:
        orchestrator = OrchestratorAgent()
        await orchestrator.run_stage(job_id, stage)
    finally:
        await close_db()


@celery_app.task(bind=True, name="tasks.pipeline_tasks.run_pipeline")
def run_pipeline(self, job_id: str):
    """Run the full agent pipeline for a given job."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(_run_pipeline(job_id))
    finally:
        loop.close()


@celery_app.task(bind=True, name="tasks.pipeline_tasks.run_single_stage")
def run_single_stage(self, job_id: str, stage: str):
    """Run a single stage after manual approval."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(_run_single_stage(job_id, stage))
    finally:
        loop.close()
