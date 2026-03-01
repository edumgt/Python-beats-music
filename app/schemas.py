from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class JobStatus(str, Enum):
    queued = "queued"
    processing = "processing"
    done = "done"
    failed = "failed"


class CreateJobResponse(BaseModel):
    job_id: str
    status: JobStatus
    detail: str


class JobStatusResponse(BaseModel):
    job_id: str
    status: JobStatus
    created_at: datetime
    updated_at: datetime
    output_file: str | None = None
    error_message: str | None = None


class UploadOptions(BaseModel):
    rights_confirmed: bool = Field(
        ...,
        description="업로더가 저작권/이용권리를 보유하고 있음을 확인",
    )
    dramatic_level: int = Field(default=7, ge=1, le=10)
    target_bpm: int | None = Field(default=None, ge=40, le=220)
