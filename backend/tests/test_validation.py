from app.services.validation import validate_invoice

class EmptyQuery:
    def filter(self, *args, **kwargs): return self
    def first(self): return None

class FakeDB:
    def query(self, model): return EmptyQuery()

def test_balanced_invoice_has_no_calculation_error():
    invoice = {
        "invoice_number": "INV-1", "invoice_date": "2026-01-01",
        "supplier_name": "ACME", "subtotal": 100, "tax": 15, "total": 115,
        "line_items": [{"amount": 100}]
    }
    errors = validate_invoice(invoice, FakeDB())
    assert not [e for e in errors if e["code"] in {"total_mismatch", "line_items_mismatch"}]

def test_total_mismatch_is_flagged():
    invoice = {"invoice_number": "INV-2", "invoice_date": "2026-01-01",
               "supplier_name": "ACME", "subtotal": 100, "tax": 15, "total": 120,
               "line_items": []}
    errors = validate_invoice(invoice, FakeDB())
    assert any(e["code"] == "total_mismatch" for e in errors)

def test_missing_invoice_number_is_flagged():
    invoice = {"invoice_number": None, "invoice_date": "2026-01-01",
               "supplier_name": "ACME", "subtotal": 10, "tax": 1, "total": 11,
               "line_items": []}
    errors = validate_invoice(invoice, FakeDB())
    assert any(e["field"] == "invoice_number" for e in errors)
