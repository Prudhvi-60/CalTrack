from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
from pathlib import Path

import pdfplumber

from app.core.exceptions import AppError

_MIN_TEXT_CHARS = 80
_MAX_PAGES = 40
_OCR_MAX_PAGES = 20


@dataclass(frozen=True)
class ExtractedPage:
    page_number: int
    text: str
    image: bytes | None = None


@dataclass(frozen=True)
class ExtractedDocument:
    document_text: str
    pages: list[ExtractedPage]
    method: str


def sanitize_pdf_filename(filename: str | None) -> str:
    name = Path(filename or "upload.pdf").name
    if not name or name in {".", ".."} or ".." in name:
        raise AppError("INVALID_PDF", "Invalid file name", 400)
    if not name.lower().endswith(".pdf"):
        raise AppError("INVALID_PDF", "Upload a PDF file", 400)
    return name


def extract_pdf_document(data: bytes) -> ExtractedDocument:
    if not data:
        raise AppError("INVALID_PDF", "The uploaded file is empty", 400)
    if not data.startswith(b"%PDF"):
        raise AppError("INVALID_PDF", "File is not a valid PDF", 400)
    try:
        with pdfplumber.open(BytesIO(data)) as pdf:
            pages: list[ExtractedPage] = []
            texts: list[str] = []
            for index, page in enumerate(pdf.pages[:_MAX_PAGES], start=1):
                text = (page.extract_text() or "").strip()
                pages.append(ExtractedPage(page_number=index, text=text))
                if text:
                    texts.append(f"--- Page {index} ---\n{text}")
            document_text = "\n\n".join(texts).strip()
            if len(document_text) >= _MIN_TEXT_CHARS:
                return ExtractedDocument(document_text=document_text, pages=pages, method="text")
            ocr_pages = _render_page_images(pdf)
    except AppError:
        raise
    except Exception as exc:
        raise AppError("INVALID_PDF", "Could not read the PDF", 400) from exc
    if not ocr_pages:
        if not document_text:
            raise AppError("EMPTY_PDF", "The PDF did not contain readable text. Try a clearer scan.", 400)
        return ExtractedDocument(document_text=document_text, pages=pages, method="text")
    combined = document_text
    return ExtractedDocument(document_text=combined, pages=ocr_pages, method="ocr")


def _render_page_images(pdf) -> list[ExtractedPage]:
    rendered: list[ExtractedPage] = []
    for index, page in enumerate(pdf.pages[:_OCR_MAX_PAGES], start=1):
        try:
            image = page.to_image(resolution=140).original
            buffer = BytesIO()
            image.convert("RGB").save(buffer, format="JPEG", quality=72)
            rendered.append(
                ExtractedPage(
                    page_number=index,
                    text=(page.extract_text() or "").strip(),
                    image=buffer.getvalue(),
                )
            )
        except Exception:
            continue
    return rendered
