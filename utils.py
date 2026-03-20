"""
utils.py
--------
Utility / helper functions shared across the Resume Parser module.
Includes logging setup, JSON safety parsing, and skill/experience normalization.
"""

import json
import logging
import re

from config import LOG_FORMAT, LOG_DATE_FORMAT, LOG_LEVEL, EXPERIENCE_LEVELS


# ─────────────────────────────────────────
# Logging
# ─────────────────────────────────────────

def get_logger(name: str) -> logging.Logger:
    """
    Create and return a named logger with a consistent format.

    Args:
        name (str): Logger name, typically __name__ of the calling module.

    Returns:
        logging.Logger: Configured logger instance.
    """
    logger = logging.getLogger(name)

    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(fmt=LOG_FORMAT, datefmt=LOG_DATE_FORMAT)
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    logger.setLevel(getattr(logging, LOG_LEVEL.upper(), logging.INFO))
    return logger


# ─────────────────────────────────────────
# JSON Parsing
# ─────────────────────────────────────────

def safe_parse_json(raw_text: str) -> dict:
    """
    Safely parse a JSON string returned by the LLM.

    Handles cases where the LLM wraps the output in markdown code fences
    like ```json ... ``` or just ``` ... ```.

    Args:
        raw_text (str): Raw string output from the LLM.

    Returns:
        dict: Parsed JSON as a Python dictionary.

    Raises:
        ValueError: If the text cannot be parsed as valid JSON.
    """
    logger = get_logger(__name__)

    if not raw_text or not raw_text.strip():
        raise ValueError("LLM returned an empty response.")

    # Strip markdown code fences if present (```json ... ``` or ``` ... ```)
    cleaned = re.sub(r"^```(?:json)?\s*", "", raw_text.strip(), flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```$", "", cleaned.strip())

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        logger.error("JSON parse error: %s", e)
        logger.debug("Raw LLM output:\n%s", raw_text)
        raise ValueError(f"Failed to parse LLM output as JSON: {e}") from e


# ─────────────────────────────────────────
# Skill Normalization
# ─────────────────────────────────────────

def normalize_skills(skills: list) -> list:
    """
    Normalize a list of skill strings:
      - Strip whitespace
      - Convert to title case
      - Remove duplicates (case-insensitive)
      - Remove empty strings

    Args:
        skills (list): Raw list of skill strings from LLM.

    Returns:
        list: Cleaned, deduplicated list of skill strings.
    """
    if not isinstance(skills, list):
        return []

    seen = set()
    normalized = []

    for skill in skills:
        if not isinstance(skill, str):
            continue
        cleaned = skill.strip().title()
        lower = cleaned.lower()
        if cleaned and lower not in seen:
            seen.add(lower)
            normalized.append(cleaned)

    return normalized


# ─────────────────────────────────────────
# Experience Level Normalization
# ─────────────────────────────────────────

def normalize_experience_level(raw_level: str) -> str:
    """
    Map an experience level string (from LLM) to one of the standard labels:
      Fresher | 0-1 | 1-3 | 3+

    Matching is case-insensitive and uses keyword detection.

    Args:
        raw_level (str): Raw experience level string from LLM output.

    Returns:
        str: Standardized experience level label, or "Unknown" if unrecognized.
    """
    if not isinstance(raw_level, str):
        return "Unknown"

    lower = raw_level.lower().strip()

    # Direct lookup
    if lower in EXPERIENCE_LEVELS:
        return EXPERIENCE_LEVELS[lower]

    # Keyword scan
    for keyword, label in EXPERIENCE_LEVELS.items():
        if keyword in lower:
            return label

    return "Unknown"


# ─────────────────────────────────────────
# Keyword Normalization
# ─────────────────────────────────────────

def normalize_keywords(keywords: list) -> list:
    """
    Normalize a list of keyword strings:
      - Strip whitespace
      - Lowercase
      - Remove duplicates and empty strings

    Args:
        keywords (list): Raw keyword list from LLM.

    Returns:
        list: Cleaned, deduplicated lowercase keywords.
    """
    if not isinstance(keywords, list):
        return []

    seen = set()
    result = []

    for kw in keywords:
        if not isinstance(kw, str):
            continue
        cleaned = kw.strip().lower()
        if cleaned and cleaned not in seen:
            seen.add(cleaned)
            result.append(cleaned)

    return result


# ─────────────────────────────────────────
# General List Deduplication
# ─────────────────────────────────────────

def deduplicate_list(items: list) -> list:
    """
    Remove duplicate strings from a list while preserving order.

    Args:
        items (list): List of strings (possibly with duplicates).

    Returns:
        list: Deduplicated list in original order.
    """
    if not isinstance(items, list):
        return []

    seen = set()
    result = []

    for item in items:
        key = str(item).strip().lower()
        if key and key not in seen:
            seen.add(key)
            result.append(item)

    return result
