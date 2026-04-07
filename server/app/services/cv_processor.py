import re
from time import perf_counter

import fitz  # PyMuPDF
from fastapi import UploadFile
from app.services.embedding import embed_query
from app.database import vector_index
from app.logging_utils import log_event

async def extract_text_from_pdf(file: UploadFile) -> str:
    """
    Extracts text from an uploaded PDF file directly from memory.
    """
    try:
        # Read the uploaded file asynchronously into memory
        file_bytes = await file.read()
        
        # Open the PDF directly from the byte stream
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        text = ""
        
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            text += page.get_text()
            
        return text
    except Exception as e:
        raise Exception(f"Error reading PDF: {e}")

def chunk_cv_robust_headers(text: str, user_id: str) -> list[dict]:
    """
    Chunks CV text by looking for exact UPPERCASE headers.
    """
    headers = [
        'EDUCATION', 'EDUCATIONAL', 'EXPERIENCE', 'WORK EXPERIENCE', 'WORK', 
        'PROFESSIONAL EXPERIENCE', 'LEADERSHIP EXPERIENCE', 'RELEVANT EXPERIENCE',
        'PROJECTS', 'PERSONAL PROJECTS', 'ACADEMIC PROJECTS', 'NOTABLE', 
        'STUDENT ORGANIZATION', 'ORGANIZATION', 'ORGANIZATIONAL',
        'SKILLS', 'TECHNICAL SKILLS', 'CERTIFICATIONS', 'EXTRACURRICULAR',
        'SUMMARY', 'PROFESSIONAL SUMMARY', 'OBJECTIVE', 'PUBLICATIONS', 'INTERESTS', 'LANGUAGES'
    ]
    
    pattern = r'\b(' + '|'.join(headers) + r')\b(?=[ \t]*(?:\n|:|$))'
    parts = re.split(pattern, text)
    chunks = []
    
    if parts[0].strip():
        chunks.append({
            "metadata": {
                "user_id": user_id,
                "section": "Contact & Summary",
                "text": parts[0].strip()
            }
        })
        
    for i in range(1, len(parts), 2):
        header_name = parts[i].strip()
        content = parts[i+1].strip() if i+1 < len(parts) else ""
        
        if content:
            chunks.append({
                "metadata": {
                    "user_id": user_id,
                    "section": header_name,
                    "text": content
                }
            })
            
    return chunks

async def process_and_upsert_cv(
    file: UploadFile,
    user_id: str,
    operation_id: str | None = None,
) -> dict:
    """
    Main pipeline to be called by the FastAPI route.
    Extracts text, chunks it, embeds it, and upserts to Pinecone.
    """
    total_start = perf_counter()
    extract_start = perf_counter()
    raw_text = await extract_text_from_pdf(file)
    extract_ms = round((perf_counter() - extract_start) * 1000, 2)

    chunk_start = perf_counter()
    chunks_list = chunk_cv_robust_headers(raw_text, user_id)
    chunk_ms = round((perf_counter() - chunk_start) * 1000, 2)

    embed_start = perf_counter()
    vectors_to_upsert = []
    embed_failures = 0
    for idx, chunk in enumerate(chunks_list):
        text_content = chunk["metadata"]["text"]
        section_name = chunk["metadata"]["section"]

        if not text_content.strip():
            continue

        try:
            embedding_values = embed_query(text_content)

            chunk_id = f"{user_id}-chunk-{idx}"
            vector_data = {
                "id": chunk_id,
                "values": embedding_values,
                "metadata": {
                    "user_id": user_id,
                    "section": section_name,
                    "text": text_content,
                },
            }
            vectors_to_upsert.append(vector_data)
        except Exception as exc:
            embed_failures += 1
            log_event(
                "cv_chunk_embed_error",
                operation_id=operation_id,
                user_id=user_id,
                chunk_index=idx,
                section=section_name,
                error=str(exc),
            )
    embed_ms = round((perf_counter() - embed_start) * 1000, 2)

    upsert_ms = 0.0
    if vectors_to_upsert:
        upsert_start = perf_counter()
        vector_index.upsert(vectors=vectors_to_upsert)
        upsert_ms = round((perf_counter() - upsert_start) * 1000, 2)
        status = "success"
        message = f"Successfully processed and upserted {len(vectors_to_upsert)} chunks."
    else:
        status = "warning"
        message = "No valid text found to upsert."

    chunking_and_upsert_ms = round(chunk_ms + upsert_ms, 2)
    total_ms = round((perf_counter() - total_start) * 1000, 2)

    log_event(
        "cv_ingest_pipeline",
        operation_id=operation_id,
        user_id=user_id,
        filename=file.filename,
        status=status,
        extract_ms=extract_ms,
        chunk_ms=chunk_ms,
        embed_ms=embed_ms,
        upsert_ms=upsert_ms,
        chunking_and_upsert_ms=chunking_and_upsert_ms,
        total_ms=total_ms,
        raw_text_chars=len(raw_text),
        chunk_count=len(chunks_list),
        upserted_chunk_count=len(vectors_to_upsert),
        embed_failures=embed_failures,
    )

    return {"status": status, "message": message}
