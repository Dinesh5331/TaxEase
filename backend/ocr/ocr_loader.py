import fitz  # PyMuPDF
import pytesseract
from PIL import Image


def extract_text(file_path):
    text = ""

    # 📄 PDF handling (NO poppler needed)
    if file_path.lower().endswith(".pdf"):
        doc = fitz.open(file_path)

        for i, page in enumerate(doc):
            page_text = page.get_text()

            # If text exists → use it
            if page_text.strip():
                text += f"\n--- Page {i+1} ---\n"
                text += page_text
            else:
                # Fallback → OCR if scanned PDF
                pix = page.get_pixmap()
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                text += pytesseract.image_to_string(img)

    # 🖼️ Image handling
    else:
        img = Image.open(file_path)
        text = pytesseract.image_to_string(img)

    return text.strip()