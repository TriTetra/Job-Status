"""PDF text extraction using PyMuPDF."""

import logging
import fitz  # PyMuPDF

logger = logging.getLogger(__name__)


class PDFParser:
    @staticmethod
    def extract_text(pdf_path: str) -> str:
        """Extract all text from PDF, page by page."""
        doc = fitz.open(pdf_path)
        pages = []
        for page in doc:
            pages.append(page.get_text())
        doc.close()
        text = "\n".join(pages).strip()
        logger.info("Extracted %d chars from %s", len(text), pdf_path)
        return text
