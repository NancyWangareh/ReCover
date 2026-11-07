import re
from pathlib import Path
from typing import List, Dict, Any
from pypdf import PdfReader
from google import genai
from .config import DOCS_DIR, OCR_DIR, GEMINI_MODEL, get_api_key

def extract_pdf_pages(pdf_path: Path) -> List[Dict[str, Any]]:
    pages = []
    reader = PdfReader(str(pdf_path))
    for idx, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        pages.append({"source": pdf_path.name, "page": idx + 1, "text": text})
    return pages

def run_gemini_ocr_if_needed(pdf_path: Path) -> Path:
    cached_path = OCR_DIR / f"{pdf_path.stem}_ocr.txt"
    if cached_path.exists():
        return cached_path

    # Check character density
    reader = PdfReader(str(pdf_path))
    total_chars = sum(len(page.extract_text() or "") for page in reader.pages)
    if total_chars > 200:
        return pdf_path  # Digital text exists; no OCR needed

    client = genai.Client(api_key=get_api_key())
    uploaded_file = client.files.upload(file=str(pdf_path))

    ocr_prompt = (
        "Transcribe ALL text in this PDF page-by-page exactly as printed. "
        "Do not summarize, translate, or alter numbers. "
        "Before the text of every page, write a clear marker on its own line: === PAGE n ==="
    )
    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=[uploaded_file, ocr_prompt]
    )
    cached_path.write_text(response.text, encoding="utf-8")
    return cached_path

def split_ocr_pages(ocr_file_path: Path, original_pdf_name: str) -> List[Dict[str, Any]]:
    content = ocr_file_path.read_text(encoding="utf-8")
    page_blocks = re.split(r"=== PAGE (\d+) ===", content)
    pages = []
    if len(page_blocks) > 1:
        for i in range(1, len(page_blocks), 2):
            page_num = int(page_blocks[i])
            text = page_blocks[i + 1].strip()
            pages.append({"source": original_pdf_name, "page": page_num, "text": text})
    else:
        pages.append({"source": original_pdf_name, "page": 1, "text": content.strip()})
    return pages