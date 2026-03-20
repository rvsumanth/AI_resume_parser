"""
cleaner.py
----------
Text cleaning and preprocessing for resume content.

Transforms raw extracted text into clean, normalized input
suitable for the LLM prompt — removing noise without losing
semantically meaningful content.
"""

import re
import unicodedata

from utils import get_logger

logger = get_logger(__name__)


# ─────────────────────────────────────────
# Public Entry Point
# ─────────────────────────────────────────

def clean_text(raw_text: str) -> str:
    """
    Full preprocessing pipeline for raw resume text.

    Steps:
      1. Decode/normalize unicode characters
      2. Remove non-printable / control characters
      3. Standardize line endings
      4. Collapse excessive blank lines
      5. Remove noisy symbols and special characters
      6. Collapse multiple spaces into one
      7. Strip leading/trailing whitespace

    Args:
        raw_text (str): Raw text extracted from the resume file.

    Returns:
        str: Cleaned, normalized text ready for LLM input.

    Raises:
        ValueError: If the input is empty or None.
    """
    if not raw_text or not raw_text.strip():
        raise ValueError("Cannot clean empty text. Extraction may have failed.")

    logger.info("Starting text cleaning. Input length: %d chars.", len(raw_text))

    text = raw_text

    text = _normalize_unicode(text)
    text = _remove_control_characters(text)
    text = _normalize_line_endings(text)
    text = _collapse_blank_lines(text)
    text = _remove_noisy_symbols(text)
    text = _collapse_whitespace(text)
    text = text.strip()

    logger.info("Text cleaning complete. Output length: %d chars.", len(text))
    return text


# ─────────────────────────────────────────
# Step 1: Unicode Normalization
# ─────────────────────────────────────────

def _normalize_unicode(text: str) -> str:
    """
    Normalize unicode characters to their closest ASCII equivalents.

    For example:
      - "café"  → "cafe"
      - "\u2019" (curly apostrophe) → "'"
      - Ligatures like "ﬁ" → "fi"

    Uses NFKD normalization + ASCII encoding/decoding to strip diacritics.

    Args:
        text (str): Raw unicode text.

    Returns:
        str: ASCII-safe normalized text.
    """
    # NFKD decomposes combined characters (é → e + ◌́)
    normalized = unicodedata.normalize("NFKD", text)
    # Encode to ASCII, ignoring characters that can't be converted
    ascii_bytes = normalized.encode("ascii", errors="ignore")
    return ascii_bytes.decode("ascii")


# ─────────────────────────────────────────
# Step 2: Remove Control Characters
# ─────────────────────────────────────────

def _remove_control_characters(text: str) -> str:
    """
    Remove non-printable control characters (e.g., \\x00, \\x01).
    Preserves newlines (\\n) and tabs (\\t) as they carry structural info.

    Args:
        text (str): Text possibly containing control characters.

    Returns:
        str: Cleaned text without control characters.
    """
    # Keep \n (newline) and \t (tab); remove all other control chars
    cleaned = re.sub(r"[^\S\n\t]+", " ", text)          # collapse inline whitespace
    cleaned = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", cleaned)
    return cleaned


# ─────────────────────────────────────────
# Step 3: Normalize Line Endings
# ─────────────────────────────────────────

def _normalize_line_endings(text: str) -> str:
    """
    Convert Windows (\\r\\n) and old Mac (\\r) line endings to Unix (\\n).

    Args:
        text (str): Text with mixed line endings.

    Returns:
        str: Text with unified \\n line endings.
    """
    text = text.replace("\r\n", "\n")
    text = text.replace("\r", "\n")
    return text


# ─────────────────────────────────────────
# Step 4: Collapse Excessive Blank Lines
# ─────────────────────────────────────────

def _collapse_blank_lines(text: str) -> str:
    """
    Reduce 3 or more consecutive blank lines to a maximum of 2.
    This preserves section separation without wasting tokens.

    Args:
        text (str): Text with possible excessive blank lines.

    Returns:
        str: Text with normalized blank line spacing.
    """
    # Replace 3+ consecutive newlines with exactly 2
    return re.sub(r"\n{3,}", "\n\n", text)


# ─────────────────────────────────────────
# Step 5: Remove Noisy Symbols
# ─────────────────────────────────────────

def _remove_noisy_symbols(text: str) -> str:
    """
    Remove symbols that add visual formatting in documents but are
    meaningless as text (e.g., decorative bullets, box-drawing chars,
    repeated dashes used as dividers).

    Preserves:
      - Alphanumeric characters
      - Common punctuation (. , : ; / @ + # & ( ) [ ] ' " - _)
      - Newlines

    Args:
        text (str): Text with possible noisy symbols.

    Returns:
        str: Cleaned text with only meaningful characters.
    """
    # Remove decorative repeated characters like ===, ---, •••, ***
    text = re.sub(r"[-=*_~]{3,}", " ", text)

    # Remove bullet-like unicode symbols commonly found in PDFs
    text = re.sub(r"[●•◦▪▸►▶→⇒✓✔✗✘◆◇■□]", " ", text)

    # Remove characters that are clearly not part of resume content
    # Keep: letters, digits, common punctuation, newlines
    text = re.sub(r"[^\w\s.,;:/@#+&()\[\]'\"\-\n]", " ", text)

    return text


# ─────────────────────────────────────────
# Step 6: Collapse Multiple Spaces
# ─────────────────────────────────────────

def _collapse_whitespace(text: str) -> str:
    """
    Collapse multiple consecutive spaces (or tabs) on a single line
    into a single space.

    Does NOT affect newlines — those are handled separately.

    Args:
        text (str): Text with possible multiple spaces.

    Returns:
        str: Text with single-space separated words per line.
    """
    # Replace multiple horizontal whitespace chars with a single space
    lines = text.split("\n")
    collapsed = [re.sub(r"[ \t]+", " ", line).strip() for line in lines]
    return "\n".join(collapsed)
