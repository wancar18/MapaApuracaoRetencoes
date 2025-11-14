# pdf_processor.py
# Logic for PDF text extraction using PyPDF2 and OCR fallback.
import os
from typing import Optional

import PyPDF2
from pdf2image import convert_from_path
import pytesseract

from config import TESSERACT_CMD

# Set the Tesseract command path
pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD

def _extract_text_with_pypdf2(pdf_path: str) -> str:
    """Extracts text from a PDF using PyPDF2."""
    text = []
    try:
        with open(pdf_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text.append(page_text)
    except Exception as e:
        print(f"  [PyPDF2 Error] Falha ao ler o PDF: {e}")
        return ""
    return "\n".join(text)

def _extract_text_with_ocr(pdf_path: str) -> str:
    """Extracts text from a PDF using OCR (Tesseract)."""
    text = []
    try:
        print("  [OCR] Convertendo PDF para imagens...")
        images = convert_from_path(pdf_path, 300) # 300 DPI for better quality
        print(f"  [OCR] Extraindo texto de {len(images)} página(s)...")
        for i, image in enumerate(images):
            # lang='por' for Portuguese
            page_text = pytesseract.image_to_string(image, lang='por')
            text.append(page_text)
            print(f"    - Página {i+1} processada.")
    except Exception as e:
        print(f"  [OCR Error] Falha no processo de OCR: {e}")
        return ""
    return "\n".join(text)

def extrair_texto_inteligente(pdf_path: str) -> Optional[str]:
    """
    Intelligently extracts text from a PDF. It first tries to extract
    embedded text. If the result is insufficient, it falls back to OCR.

    Returns the extracted text, or None if both methods fail to produce
    meaningful content.
    """
    print(f"Iniciando extração de texto para: {os.path.basename(pdf_path)}")

    # 1. Try native text extraction first
    native_text = _extract_text_with_pypdf2(pdf_path)

    # Heuristic to check if the text is sufficient
    # We check for more than just a few characters.
    if native_text and len(native_text.strip()) > 100:
        print("  -> Extração de texto nativo bem-sucedida.")
        return native_text.strip()

    print("  -> Texto nativo insuficiente ou ausente. Iniciando fallback para OCR.")

    # 2. Fallback to OCR
    ocr_text = _extract_text_with_ocr(pdf_path)

    if ocr_text and len(ocr_text.strip()) > 100:
        print("  -> Extração via OCR bem-sucedida.")
        return ocr_text.strip()

    print("  [FALHA] Extração de texto falhou. O PDF pode estar vazio ou ilegível.")
    return None
