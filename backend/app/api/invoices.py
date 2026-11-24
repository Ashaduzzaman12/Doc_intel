from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Invoice, Document
from app.schemas import CorrectionRequest
from app.services.validation import validate_invoice

router = APIRouter(tags=["invoices"])

@router.get("/documents/{document_id}/results")
def invoice_result(document_id: str, db: Session = Depends(get_db)):
    invoice = db.query(Invoice).filter(Invoice.document_id == document_id).first()
    if not invoice:
        raise HTTPException(404, "Invoice result not available")
    return {
        "id": invoice.id, "document_id": invoice.document_id,
        "invoice_number": invoice.invoice_number, "invoice_date": invoice.invoice_date,
        "supplier_name": invoice.supplier_name, "customer_name": invoice.customer_name,
        "subtotal": invoice.subtotal, "tax": invoice.tax, "total": invoice.total,
        "currency": invoice.currency, "line_items": invoice.line_items,
        "confidence": invoice.confidence, "validation_errors": invoice.validation_errors,
        "requires_review": invoice.requires_review
    }

@router.patch("/documents/{document_id}/correct")
def correct_invoice(document_id: str, body: CorrectionRequest, db: Session = Depends(get_db)):
    invoice = db.query(Invoice).filter(Invoice.document_id == document_id).first()
    if not invoice:
        raise HTTPException(404, "Invoice result not found")
    changes = body.model_dump(exclude_unset=True)
    for key, value in changes.items():
        setattr(invoice, key, value)
    current = {k: getattr(invoice, k) for k in (
        "invoice_number", "invoice_date", "supplier_name", "customer_name",
        "subtotal", "tax", "total", "currency", "line_items")}
    errors = validate_invoice(current, db, exclude_document_id=document_id)
    invoice.validation_errors = errors
    invoice.requires_review = bool(errors)
    db.commit()
    return {"message": "Correction saved", "updated_fields": list(changes), "validation_errors": errors}
