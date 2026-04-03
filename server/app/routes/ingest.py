from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

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
        result = await process_and_upsert_cv(file, normalized_user_id)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to ingest CV: {exc}") from exc

    return IngestResponse(
        status=result["status"],
        message=result["message"],
        user_id=normalized_user_id,
        filename=file.filename,
    )
