from decimal import Decimal, InvalidOperation

CENT = Decimal("0.01")

def dec(value):
    if value is None:
        return None
    return Decimal(str(value)).quantize(CENT)

def validate_invoice(invoice: dict, db, exclude_document_id=None):
    errors = []
    for field in ("invoice_number", "invoice_date", "supplier_name", "total"):
        if invoice.get(field) in (None, ""):
            errors.append({"code": "missing_field", "field": field, "message": f"Missing {field}"})

    subtotal, tax, total = (dec(invoice.get(k)) for k in ("subtotal", "tax", "total"))
    if None not in (subtotal, tax, total) and abs(subtotal + tax - total) > CENT:
        errors.append({"code": "total_mismatch", "field": "total",
                       "message": "Subtotal plus tax does not equal total"})
    amounts = [dec(item.get("amount")) for item in invoice.get("line_items", [])]
    if subtotal is not None and amounts and all(x is not None for x in amounts):
        if abs(sum(amounts, Decimal("0.00")) - subtotal) > CENT:
            errors.append({"code": "line_items_mismatch", "field": "subtotal",
                           "message": "Line item amounts do not equal subtotal"})

    number = invoice.get("invoice_number")
    supplier = invoice.get("supplier_name")
    if number and supplier:
        from app.models import Invoice
        query = db.query(Invoice).filter(
            Invoice.invoice_number == number,
            Invoice.supplier_name == supplier
        )
        if exclude_document_id:
            query = query.filter(Invoice.document_id != exclude_document_id)
        if query.first():
            errors.append({"code": "possible_duplicate", "field": "invoice_number",
                           "message": "Invoice number already exists for this supplier"})
    return errors
