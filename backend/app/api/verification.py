from fastapi import APIRouter
from pydantic import BaseModel
from typing import Any

router = APIRouter(tags=["verification"])

class CompareRequest(BaseModel):
    source_a: dict[str, Any]
    source_b: dict[str, Any]
    tolerance: float = 0.01

@router.post("/verify")
def verify_documents(body: CompareRequest):
    fields = ["invoice_number", "invoice_date", "supplier_name", "customer_name",
              "subtotal", "tax", "total", "currency"]
    matched, mismatched, missing = [], [], []
    for field in fields:
        a, b = body.source_a.get(field), body.source_b.get(field)
        if a is None or b is None or a == "" or b == "":
            missing.append({"field": field, "source_a": a, "source_b": b})
        elif field in {"subtotal", "tax", "total"}:
            try:
                same = abs(float(a) - float(b)) <= body.tolerance
            except (TypeError, ValueError):
                same = str(a) == str(b)
            (matched if same else mismatched).append({"field": field, "source_a": a, "source_b": b})
        else:
            same = str(a).strip().casefold() == str(b).strip().casefold()
            (matched if same else mismatched).append({"field": field, "source_a": a, "source_b": b})
    return {"consistent": not mismatched and not missing, "matched": matched,
            "mismatched": mismatched, "missing": missing,
            "tolerance": body.tolerance}
