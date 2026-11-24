from app.api.verification import verify_documents
from app.schemas import CompareRequest

def test_verification_detects_total_mismatch():
    result = verify_documents(CompareRequest(source_a={"total": 100}, source_b={"total": 120}))
    assert any(item["field"] == "total" for item in result["mismatched"])
