from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import os

from core.database import get_db
from core.security import get_current_user, require_role
from services.rag import stream_answer, retrieve

router = APIRouter()

DOCS_DIR = "/app/data/docs"


class ChatRequest(BaseModel):
    question:     str
    zone_context: str = ""


@router.post("/")
async def chat(
    body: ChatRequest,
    _=   Depends(require_role("RESCUE", "ADMIN")),
):
    """Stream a RAG-powered answer — RESCUE and ADMIN only."""
    if not body.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    async def generate():
        async for token in stream_answer(body.question, body.zone_context):
            yield token

    return StreamingResponse(generate(), media_type="text/plain")


@router.get("/sources")
async def get_sources(question: str, _=Depends(get_current_user)):
    """Return the retrieved chunks for a question — useful for debugging."""
    chunks = retrieve(question)
    return chunks


@router.post("/documents/upload")
async def upload_pdf(
    file: UploadFile = File(...),
    _=    Depends(require_role("ADMIN")),
):
    """Upload a PDF to /app/data/docs/ — then run the ingest scripts."""
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files accepted")

    os.makedirs(DOCS_DIR, exist_ok=True)
    path = os.path.join(DOCS_DIR, file.filename)
    with open(path, "wb") as f:
        f.write(await file.read())

    return {
        "message": f"Uploaded {file.filename}. Now run the ingest pipeline:",
        "steps": [
            "docker exec climarisk_backend python services/pdf_to_markdown.py",
            "docker exec climarisk_backend python services/ingest.py",
        ]
    }