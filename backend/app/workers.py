from celery import Celery
from app.config import settings

celery = Celery("docintel", broker=settings.redis_url, backend=settings.redis_url)
celery.conf.update(task_track_started=True, task_serializer="json",
                   accept_content=["json"], result_serializer="json")

@celery.task(bind=True, max_retries=2, default_retry_delay=10)
def process_document(self, document_id: str):
    from app.database import SessionLocal
    from app.models import Document, Invoice
    from app.services.extractors import extract_document
    from app.services.validation import validate_invoice
    from app.schemas import InvoiceExtraction
    from app.config import settings
    import asyncio, os
    db = SessionLocal()
    try:
        doc = db.query(Document).filter(Document.id == document_id).first()
        if not doc:
            return
        doc.status = "processing"
        db.commit()
        text = extract_document(doc.stored_path)
        doc.extracted_text = text
        db.commit()
        from app.services.ai_extractor import extract_invoice
        extracted = asyncio.run(extract_invoice(text))
        data = extracted.model_dump()
        errors = validate_invoice(data, db, exclude_document_id=document_id)
        data["validation_errors"] = errors
        data["requires_review"] = bool(errors) or extracted.requires_review
        invoice = db.query(Invoice).filter(Invoice.document_id == document_id).first()
        if invoice is None:
            invoice = Invoice(document_id=document_id)
            db.add(invoice)
        for key in ("invoice_number", "invoice_date", "supplier_name", "customer_name",
                    "subtotal", "tax", "total", "currency", "line_items",
                    "confidence", "requires_review"):
            value = data.get(key)
            setattr(invoice, key, value)
        invoice.raw_json = extracted.model_dump(mode="json")
        invoice.validation_errors = errors
        doc.status = "completed"
        doc.error_message = None
        db.commit()
    except Exception as exc:
        db.rollback()
        doc = db.query(Document).filter(Document.id == document_id).first()
        if doc:
            doc.status = "failed"
            doc.error_message = str(exc)[:2000]
            db.commit()
        raise
    finally:
        db.close()
