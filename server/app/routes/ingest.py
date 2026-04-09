from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel
from uuid import uuid4

from app.logging_utils import log_event
from app.services.cv_processor import process_and_upsert_cv

router = APIRouter()


class IngestResponse(BaseModel):
    status: str
    message: str
    user_id: str
    filename: str


@router.post("/ingest", response_model=IngestResponse)
async def ingest_cv(
    file: UploadFile = File(...),
    user_id: str = Form(...),
):
    operation_id = uuid4().hex
    normalized_user_id = user_id.strip()
    if not normalized_user_id:
        raise HTTPException(status_code=400, detail="user_id is required")

    if not file.filename:
        raise HTTPException(status_code=400, detail="A CV file is required")

    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Only PDF CV uploads are supported",
        )

    try:
        result = await process_and_upsert_cv(file, normalized_user_id, operation_id)
    except Exception as exc:
        log_event(
            "cv_ingest_error",
            operation_id=operation_id,
            user_id=normalized_user_id,
            filename=file.filename,
            error=str(exc),
        )
        raise HTTPException(status_code=500, detail=f"Failed to ingest CV: {exc}") from exc

    return IngestResponse(
        status=result["status"],
        message=result["message"],
        user_id=normalized_user_id,
        filename=file.filename,
    )
