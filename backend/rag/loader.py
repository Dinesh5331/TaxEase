import re
from pathlib import Path

import pymupdf
import pytesseract
from PIL import Image
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from rag.config import CHUNK_SIZE, CHUNK_OVERLAP


def clean_text(text):
    return " ".join(text.split())


def _ocr_page(page) -> str:
    """
    Render a pymupdf page to a high-DPI image and extract text via Tesseract OCR.
    Used as a fallback when get_text() returns nothing (scanned/image-based PDFs).
    """
    # 300 DPI gives good OCR accuracy; matrix scales from 72 DPI base
    mat = pymupdf.Matrix(300 / 72, 300 / 72)
    pix = page.get_pixmap(matrix=mat, colorspace=pymupdf.csRGB)
    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    text = pytesseract.image_to_string(img, lang="eng")
    return clean_text(text)


def normalize_document_key(value):
    normalized = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    normalized = re.sub(r"-+", "-", normalized)
    return normalized


def _extract_form_name(filename: str) -> str:
    """
    Extract normalized ITR form name from a filename stem.

    Examples:
        "ITR-1.pdf"            → "ITR-1"
        "itr_1-guidelines.pdf" → "ITR-1"
        "ITR-V.pdf"            → "ITR-V"
        "ITR-B.pdf"            → "ITR-B"
        "Finance_Bill.pdf"     → "unknown"
    """
    stem = Path(filename).stem  # strip extension before matching
    match = re.search(r"\bitr[\s\-_]*([a-z0-9]+)\b", stem, re.IGNORECASE)
    if not match:
        return "unknown"
    number_or_letter = match.group(1).upper()
    return f"ITR-{number_or_letter}"


def load_documents(folder_path, source_type, source_label=None):
    documents = []
    folder = Path(folder_path)

    if not folder.exists():
        return documents

    # ---- PDF files ----
    for pdf_path in sorted(folder.rglob("*.pdf")):
        pdf = pymupdf.open(pdf_path)
        file_name = pdf_path.name
        document_name = pdf_path.stem
        document_key = normalize_document_key(document_name)
        form_name = _extract_form_name(file_name)

        for page_num in range(len(pdf)):
            page = pdf[page_num]
            native_text = clean_text(page.get_text())
            was_ocr = False

            if native_text:
                text = native_text
            else:
                try:
                    text = _ocr_page(page)
                    was_ocr = bool(text)
                except Exception as ocr_err:
                    print(f"  ⚠️  OCR failed for {file_name} page {page_num + 1}: {ocr_err}")
                    text = ""

            if text:
                documents.append(
                    Document(
                        page_content=text,
                        metadata={
                            "source": source_type,
                            "source_label": source_label or source_type,
                            "file": file_name,
                            "path": str(pdf_path),
                            "folder": folder.name,
                            "document_name": document_name,
                            "document_key": document_key,
                            "form_name": form_name,
                            "itr_number": form_name.replace("ITR-", "") if form_name != "unknown" else None,
                            "page": page_num + 1,
                            "ocr": was_ocr,
                        }
                    )
                )

    # ---- Plain text files (.txt) ----
    for txt_path in sorted(folder.rglob("*.txt")):
        file_name = txt_path.name
        document_name = txt_path.stem
        document_key = normalize_document_key(document_name)
        form_name = _extract_form_name(file_name)  # "unknown" for general reference files

        try:
            text = clean_text(txt_path.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"  ⚠️  Failed to read {file_name}: {e}")
            continue

        if text:
            documents.append(
                Document(
                    page_content=text,
                    metadata={
                        "source": source_type,
                        "source_label": source_label or source_type,
                        "file": file_name,
                        "path": str(txt_path),
                        "folder": folder.name,
                        "document_name": document_name,
                        "document_key": document_key,
                        "form_name": form_name,
                        "itr_number": None,
                        "page": 1,
                        "ocr": False,
                    }
                )
            )

    return documents


def load_all_documents(document_sources):
    documents = []

    for source in document_sources:
        documents.extend(
            load_documents(
                source["path"],
                source["source"],
                source.get("label"),
            )
        )

    return documents


def split_documents(documents):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP
    )
    return splitter.split_documents(documents)
