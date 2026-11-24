from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.database import get_db
from app.models import Document, Invoice

router = APIRouter(tags=["search"])

@router.get("/search")
def search_documents(q: str = Query("", max_length=200), supplier: str | None = None,
                     invoice_number: str | None = None, status: str | None = None,
                     db: Session = Depends(get_db)):
    query = db.query(Document, Invoice).outerjoin(Invoice, Invoice.document_id == Document.id)
    if q:
        like = f"%{q}%"
        query = query.filter(or_(Document.filename.ilike(like),
                                 Document.extracted_text.ilike(like),
                                 Invoice.invoice_number.ilike(like),
                                 Invoice.supplier_name.ilike(like)))
    if supplier:
        query = query.filter(Invoice.supplier_name.ilike(f"%{supplier}%"))
    if invoice_number:
        query = query.filter(Invoice.invoice_number.ilike(f"%{invoice_number}%"))
    if status:
        query = query.filter(Document.status == status)
    rows = query.order_by(Document.created_at.desc()).limit(100).all()
    return [{"document_id": d.id, "filename": d.filename, "status": d.status,
             "invoice_number": i.invoice_number if i else None,
             "supplier_name": i.supplier_name if i else None,
             "total": float(i.total) if i and i.total is not None else None,
             "currency": i.currency if i else None} for d, i in rows]
