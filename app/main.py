from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from celery.result import AsyncResult
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse

from app.config import settings
from app.schemas import CreateJobResponse, JobStatus, JobStatusResponse
from app.tasks import make_piano_backing

app = FastAPI(title=settings.app_name)


def _ensure_dirs() -> None:
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    settings.output_dir.mkdir(parents=True, exist_ok=True)


@app.on_event("startup")
def on_startup() -> None:
    _ensure_dirs()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/jobs", response_model=CreateJobResponse)
async def create_job(
    file: UploadFile = File(...),
    rights_confirmed: bool = Form(...),
    dramatic_level: int = Form(7),
    target_bpm: int | None = Form(None),
) -> CreateJobResponse:
    if not rights_confirmed:
        raise HTTPException(status_code=400, detail="rights_confirmed must be true")

    contents = await file.read()
    size_mb = len(contents) / (1024 * 1024)
    if size_mb > settings.max_upload_mb:
        raise HTTPException(status_code=413, detail="File is too large")

    source_ext = Path(file.filename or "upload.mp3").suffix or ".mp3"
    input_name = f"{uuid4().hex}{source_ext}"
    job_id = uuid4().hex
    output_name = f"{job_id}.mp3"

    input_path = settings.upload_dir / input_name
    input_path.write_bytes(contents)

    task = make_piano_backing.delay(
        input_filename=input_name,
        output_filename=output_name,
        dramatic_level=dramatic_level,
        target_bpm=target_bpm,
    )

    return CreateJobResponse(
        job_id=task.id,
        status=JobStatus.queued,
        detail="Job accepted",
    )


@app.get("/jobs/{job_id}", response_model=JobStatusResponse)
def get_job_status(job_id: str) -> JobStatusResponse:
    result = AsyncResult(job_id)
    created_at = datetime.now(timezone.utc)

    if result.state in {"PENDING", "RECEIVED", "RETRY"}:
        status = JobStatus.queued
        updated_at = datetime.now(timezone.utc)
        return JobStatusResponse(
            job_id=job_id,
            status=status,
            created_at=created_at,
            updated_at=updated_at,
        )

    if result.state in {"STARTED"}:
        return JobStatusResponse(
            job_id=job_id,
            status=JobStatus.processing,
            created_at=created_at,
            updated_at=datetime.now(timezone.utc),
        )

    if result.state == "SUCCESS":
        payload = result.result or {}
        output_name = payload.get("output_file")
        return JobStatusResponse(
            job_id=job_id,
            status=JobStatus.done,
            created_at=created_at,
            updated_at=datetime.now(timezone.utc),
            output_file=output_name,
        )

    return JobStatusResponse(
        job_id=job_id,
        status=JobStatus.failed,
        created_at=created_at,
        updated_at=datetime.now(timezone.utc),
        error_message=str(result.result),
    )


@app.get("/outputs/{filename}")
def download_output(filename: str) -> FileResponse:
    file_path = settings.output_dir / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(file_path, media_type="audio/mpeg", filename=filename)
