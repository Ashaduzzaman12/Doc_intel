import os, uuid, mimetypes
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.config import settings
from app.models import Document
from app.services.extractors import SUPPORTED
from app.workers import process_document

router = APIRouter(tags=["documents"])
os.makedirs(settings.upload_dir, exist_ok=True)

@router.post("/documents/upload")
async def upload_documents(files: list[UploadFile] = File(...), db: Session = Depends(get_db)):
    results = []
    for file in files:
        suffix = Path(file.filename or "").suffix.lower()
        if suffix not in SUPPORTED:
            raise HTTPException(400, f"Unsupported file type: {suffix}")
        content = await file.read(settings.max_upload_mb * 1024 * 1024 + 1)
        if len(content) > settings.max_upload_mb * 1024 * 1024:
            raise HTTPException(413, f"{file.filename} exceeds upload limit")
        doc_id = str(uuid.uuid4())
        safe_name = Path(file.filename).name
        stored = os.path.join(settings.upload_dir, f"{doc_id}{suffix}")
        with open(stored, "wb") as f:
            f.write(content)
        doc = Document(id=doc_id, filename=safe_name, stored_path=stored,
                       mime_type=file.content_type or mimetypes.guess_type(safe_name)[0] or "application/octet-stream",
                       size_bytes=len(content), status="queued")
        db.add(doc)
        db.commit()
        task = process_document.delay(doc_id)
        results.append({"document_id": doc_id, "filename": safe_name, "task_id": task.id, "status": "queued"})
    return {"uploaded": len(results), "documents": results}

@router.get("/documents")
def list_documents(status: str | None = None, limit: int = 50, offset: int = 0, db: Session = Depends(get_db)):
    query = db.query(Document)
    if status:
        query = query.filter(Document.status == status)
    items = query.order_by(Document.created_at.desc()).offset(offset).limit(min(limit, 200)).all()
    return [{"id": d.id, "filename": d.filename, "status": d.status,
             "error_message": d.error_message, "created_at": d.created_at} for d in items]

@router.get("/documents/{document_id}")
def get_document(document_id: str, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(404, "Document not found")
    return {"id": doc.id, "filename": doc.filename, "status": doc.status,
            "error_message": doc.error_message, "extracted_text": doc.extracted_text,
            "created_at": doc.created_at}

@router.get("/documents/{document_id}/status")
def document_status(document_id: str, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(404, "Document not found")
    return {"document_id": doc.id, "status": doc.status, "error": doc.error_message}

@router.post("/documents/{document_id}/reprocess")
def reprocess(document_id: str, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(404, "Document not found")
    doc.status, doc.error_message = "queued", None
    db.commit()
    task = process_document.delay(document_id)
    return {"document_id": document_id, "task_id": task.id, "status": "queued"}
