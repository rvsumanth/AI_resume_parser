"""
extractor.py
------------
Handles raw text extraction from PDF and DOCX resume files.

Supported formats:
  - PDF  → pdfplumber (primary), with PyPDF2 as fallback
  - DOCX → docx2txt

Raises clear errors for unsupported formats or empty files.
"""

import os
from pathlib import Path

import pdfplumber
import docx2txt

from config import SUPPORTED_EXTENSIONS
from utils import get_logger

logger = get_logger(__name__)


# ─────────────────────────────────────────
# Public Entry Point
# ─────────────────────────────────────────

def extract_text(file_path: str) -> str:
    """
    Extract raw text from a PDF or DOCX file.

    This is the main function called by the pipeline. It:
      1. Validates the file exists and has a supported extension.
      2. Dispatches to the correct extractor based on file type.
      3. Validates that the extracted text is non-empty.

    Args:
        file_path (str): Absolute or relative path to the resume file.

    Returns:
        str: Raw text extracted from the file.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the format is unsupported or the file yields no text.
        RuntimeError: If extraction fails unexpectedly.
    """
    path = Path(file_path)

    # ── Existence check ──────────────────────────────────────────────────────
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    ext = path.suffix.lower()

    # ── Format check ─────────────────────────────────────────────────────────
    if ext not in SUPPORTED_EXTENSIONS:
        raise ValueError(
            f"Unsupported file format: '{ext}'. "
            f"Supported formats: {', '.join(SUPPORTED_EXTENSIONS)}"
        )

    logger.info("Extracting text from: %s (format: %s)", path.name, ext)

    # ── Dispatch ─────────────────────────────────────────────────────────────
    if ext == ".pdf":
        text = _extract_from_pdf(str(path))
    elif ext == ".docx":
        text = _extract_from_docx(str(path))
    else:
        # Defensive — already caught above, but keeps linters happy
        raise ValueError(f"Unsupported format: {ext}")

    # ── Empty file check ─────────────────────────────────────────────────────
    if not text or not text.strip():
        raise ValueError(
            f"No text could be extracted from '{path.name}'. "
            "The file may be empty, image-based (scanned), or corrupted."
        )

    logger.info("Extraction successful. Characters extracted: %d", len(text))
    return text


# ─────────────────────────────────────────
# PDF Extraction
# ─────────────────────────────────────────

def _extract_from_pdf(file_path: str) -> str:
    """
    Extract text from a PDF file using pdfplumber.
    Falls back to PyPDF2 if pdfplumber returns no usable text.

    Args:
        file_path (str): Path to the PDF file.

    Returns:
        str: Extracted text.

    Raises:
        RuntimeError: If both primary and fallback extraction fail.
    """
    text = _pdf_pdfplumber(file_path)

    # Fallback if pdfplumber yields nothing meaningful
    if not text or len(text.strip()) < 20:
        logger.warning(
            "pdfplumber returned little/no text. Trying PyPDF2 fallback..."
        )
        text = _pdf_pypdf2_fallback(file_path)

    return text


def _pdf_pdfplumber(file_path: str) -> str:
    """
    Primary PDF extractor using pdfplumber.
    Iterates over every page and joins text with newlines.

    Args:
        file_path (str): Path to the PDF file.

    Returns:
        str: Concatenated text from all pages.
    """
    pages_text = []

    try:
        with pdfplumber.open(file_path) as pdf:
            total_pages = len(pdf.pages)
            logger.debug("PDF has %d page(s).", total_pages)

            for i, page in enumerate(pdf.pages, start=1):
                page_text = page.extract_text()
                if page_text:
                    pages_text.append(page_text)
                    logger.debug("Page %d: %d chars extracted.", i, len(page_text))
                else:
                    logger.debug("Page %d: no text found.", i)

    except Exception as e:
        logger.error("pdfplumber failed: %s", e)
        return ""

    return "\n".join(pages_text)


def _pdf_pypdf2_fallback(file_path: str) -> str:
    """
    Fallback PDF extractor using PyPDF2.
    Used when pdfplumber cannot extract meaningful text.

    Args:
        file_path (str): Path to the PDF file.

    Returns:
        str: Extracted text, or empty string on failure.
    """
    try:
        import PyPDF2  # Optional dependency — only imported if needed

        pages_text = []
        with open(file_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            for i, page in enumerate(reader.pages, start=1):
                page_text = page.extract_text()
                if page_text:
                    pages_text.append(page_text)
                    logger.debug("PyPDF2 page %d: %d chars.", i, len(page_text))

        return "\n".join(pages_text)

    except ImportError:
        logger.warning("PyPDF2 is not installed. Skipping fallback.")
        return ""
    except Exception as e:
        logger.error("PyPDF2 fallback also failed: %s", e)
        return ""


# ─────────────────────────────────────────
# DOCX Extraction
# ─────────────────────────────────────────

def _extract_from_docx(file_path: str) -> str:
    """
    Extract text from a DOCX file using docx2txt.

    Args:
        file_path (str): Path to the DOCX file.

    Returns:
        str: Raw text extracted from the document.

    Raises:
        RuntimeError: If docx2txt fails to process the file.
    """
    try:
        text = docx2txt.process(file_path)
        logger.debug("docx2txt extracted %d characters.", len(text) if text else 0)
        return text or ""
    except Exception as e:
        raise RuntimeError(f"Failed to extract text from DOCX file: {e}") from e
