from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import Base, engine
from app import models  # register tables before create_all
from app.api.documents import router as documents_router
from app.api.invoices import router as invoices_router
from app.api.search import router as search_router
from app.api.verification import router as verification_router

Base.metadata.create_all(bind=engine)
app = FastAPI(title="AI Document Intelligence API", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:3000"], allow_credentials=True,
                   allow_methods=["*"], allow_headers=["*"])
for router in (documents_router, invoices_router, search_router, verification_router):
    app.include_router(router, prefix="/api")

@app.get("/health")
def health():
    return {"status": "ok", "service": "document-intelligence-api"}
