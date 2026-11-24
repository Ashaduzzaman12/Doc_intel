# DocIntel — AI-Powered Document Intelligence

Local-first full-stack MVP for business document ingestion, OCR/text extraction, Ollama invoice extraction, financial validation, manual review, keyword search and source-to-source reconciliation.

## Stack
- Next.js 14, React, TypeScript, Tailwind CSS
- FastAPI, Pydantic, SQLAlchemy 2
- Celery + Redis background jobs
- PostgreSQL 16 (pgvector-enabled image)
- Ollama (`qwen2.5:3b` default)
- PyMuPDF, Tesseract OCR, Pillow, Pandas, OpenPyXL

## Run with Docker
Prerequisites: Docker Desktop; 8 GB RAM minimum suggested, 16 GB recommended for local model inference.

```bash
docker compose up --build -d
docker compose exec ollama ollama pull qwen2.5:3b
```
First model download can take several minutes. Then open:
- Frontend: http://localhost:3000
- Swagger API: http://localhost:8000/docs
- Health: http://localhost:8000/health

Logs: `docker compose logs -f backend worker ollama frontend`

## Upload via API
```bash
curl -X POST http://localhost:8000/api/documents/upload \\
  -F 'files=@sample_invoice.pdf' \\
  -F 'files=@ledger.xlsx'
```
Check `GET /api/documents`, then `GET /api/documents/{id}/status` and `GET /api/documents/{id}/results`.

## API endpoints
- `POST /api/documents/upload` — multi-file upload
- `GET /api/documents` — list/status filter
- `GET /api/documents/{id}` — metadata and extracted text
- `GET /api/documents/{id}/status` — job status
- `GET /api/documents/{id}/results` — structured invoice
- `PATCH /api/documents/{id}/correct` — manual correction
- `POST /api/documents/{id}/reprocess` — retry processing
- `GET /api/search?q=...&supplier=...&invoice_number=...` — keyword search
- `POST /api/verify` — compare two extracted/source JSON records
- `GET /health` — health check

## Supported files
PDF, JPG, JPEG, PNG, TIFF, XLSX, XLS and CSV. Digital PDFs use PyMuPDF text extraction, scanned pages fall back to Tesseract OCR, images use OCR, and spreadsheets are parsed sheet-by-sheet.

## Tests
```bash
docker compose run --rm backend pytest
```

## Architecture
Browser → FastAPI upload → shared storage + Celery/Redis queue → PDF/OCR/spreadsheet extraction → Ollama JSON extraction → Pydantic schema validation → deterministic Decimal financial validation → PostgreSQL → Next.js review/search UI.

## Database
The initial schema contains `documents` (file metadata/status/text), `invoices` (normalized invoice fields, line items, raw model JSON and validation findings). pgvector is available in the chosen PostgreSQL image, but semantic embeddings and vector search are not yet wired into this MVP. Current search is keyword-based.

## Known limitations / production hardening
This is a development MVP, not a production-certified accounting system. Add authentication and role-based access, per-user data isolation, file signature validation, malware scanning, encrypted object storage, secrets management, retention controls, backups, rate limiting, audit history, Alembic migrations, observability and comprehensive integration tests before production. Large PDFs are iterated page-by-page in one worker task; for 1,000-page workloads, split page ranges into separate queue tasks and aggregate results. OCR uses Tesseract for simpler local setup; PaddleOCR can replace it for difficult scans. Always require human review before accounting-system posting.

## Evaluation
Use a manually labeled dataset and report field-level accuracy, invoice exact-match accuracy, OCR success, p50/p95 processing time, document success/failure rates, and validation precision/recall. Segment by file type and scan quality. No metrics are fabricated or prefilled.

## AI-assisted development disclosure
AI assistance was used to scaffold parts of the source code and documentation. Review, test, and adapt generated code before operational use.
