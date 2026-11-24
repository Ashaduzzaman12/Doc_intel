from pathlib import Path
import pandas as pd
import fitz
from PIL import Image
import pytesseract

SUPPORTED = {".pdf", ".jpg", ".jpeg", ".png", ".tif", ".tiff", ".xlsx", ".xls", ".csv"}

def extract_pdf(path: str) -> str:
    chunks = []
    with fitz.open(path) as pdf:
        for page_no, page in enumerate(pdf, start=1):
            text = page.get_text("text").strip()
            if not text:
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
                image = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                text = pytesseract.image_to_string(image)
            chunks.append(f"\n[PAGE {page_no}]\n{text}")
    return "\n".join(chunks)

def extract_image(path: str) -> str:
    return pytesseract.image_to_string(Image.open(path))

def extract_spreadsheet(path: str) -> str:
    suffix = Path(path).suffix.lower()
    sections = []
    if suffix == ".csv":
        frames = {"CSV": pd.read_csv(path, dtype=str, keep_default_na=False)}
    else:
        frames = pd.read_excel(path, sheet_name=None, dtype=str, keep_default_na=False)
    for sheet, frame in frames.items():
        sections.append(f"[SHEET: {sheet}]\n{frame.fillna('').to_csv(index=False)}")
    return "\n\n".join(sections)

def extract_document(path: str) -> str:
    suffix = Path(path).suffix.lower()
    if suffix == ".pdf":
        return extract_pdf(path)
    if suffix in {".jpg", ".jpeg", ".png", ".tif", ".tiff"}:
        return extract_image(path)
    if suffix in {".xlsx", ".xls", ".csv"}:
        return extract_spreadsheet(path)
    raise ValueError(f"Unsupported file type: {suffix}")
