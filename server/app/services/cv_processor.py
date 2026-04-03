import re
import fitz  # PyMuPDF
from fastapi import UploadFile
from app.services.embedding import embed_query
from app.database import vector_index

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

async def process_and_upsert_cv(file: UploadFile, user_id: str) -> dict:
    """
    Main pipeline to be called by the FastAPI route.
    Extracts text, chunks it, embeds it, and upserts to Pinecone.
    """
    # 1. Extract Text from Uploaded File
    raw_text = await extract_text_from_pdf(file)
    
    # 2. Chunk Text
    chunks_list = chunk_cv_robust_headers(raw_text, user_id)
    
    # 3. Embed and Prepare for Upsert
    vectors_to_upsert = []
    for idx, chunk in enumerate(chunks_list):
        text_content = chunk['metadata']['text']
        section_name = chunk['metadata']['section']
        
        if not text_content.strip():
            continue
            
        try:
            # Generate 768-dim embeddings
            embedding_values = embed_query(text_content)
            
            chunk_id = f"{user_id}-chunk-{idx}"
            vector_data = {
                "id": chunk_id,
                "values": embedding_values,
                "metadata": {
                    "user_id": user_id,
                    "section": section_name,
                    "text": text_content 
                }
            }
            vectors_to_upsert.append(vector_data)
        except Exception as e:
            print(f"❌ Error embedding Chunk {idx+1}: {e}")

    # 4. Upsert to Pinecone
    if vectors_to_upsert:
        vector_index.upsert(vectors=vectors_to_upsert)
        return {"status": "success", "message": f"Successfully processed and upserted {len(vectors_to_upsert)} chunks."}
    else:
        return {"status": "warning", "message": "No valid text found to upsert."}