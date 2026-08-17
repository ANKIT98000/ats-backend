"""
utils/parse_extractor.py
-----------------------
Utility to read raw plaintext from uploaded PDF and DOCX files for parsing.
"""
import io
import logging
from pypdf import PdfReader
import docx

logger = logging.getLogger(__name__)

def extract_text_for_parsing(filename: str, content: bytes) -> str:
    print(f" [EXTRACTOR] Opening and reading file: {filename}...")
    filename_lower = filename.lower()
    text_content = []

    try:
        if filename_lower.endswith(".pdf"):
            pdf_reader = PdfReader(io.BytesIO(content))
            for page in pdf_reader.pages:
                extracted = page.extract_text()
                if extracted:
                    text_content.append(extracted)
        elif filename_lower.endswith((".docx", ".doc")):
            doc = docx.Document(io.BytesIO(content))
            for para in doc.paragraphs:
                if para.text:
                    text_content.append(para.text)
        else:
            raise ValueError("Unsupported file format.")

        full_text = "\n".join(text_content).strip()
        print(f"[EXTRACTOR] Successfully extracted {len(full_text)} characters.")
        return full_text
    except Exception as exc:
        print(f"[EXTRACTOR ERROR] Failed to read text: {str(exc)}")
        logger.error(f"Error extracting text: {str(exc)}")
        raise