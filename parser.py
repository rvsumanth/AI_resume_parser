"""
parser.py
---------
Main pipeline for the Resume Parser module.

Orchestrates the full parsing flow:
  1. Extract raw text from the file       (extractor.py)
  2. Clean and preprocess the text        (cleaner.py)
  3. Send to OpenAI LLM for extraction    (llm_parser.py)
  4. Parse and validate the JSON response (utils.py)
  5. Normalize and deduplicate fields     (utils.py)
  6. Return final structured JSON dict    ← this module

Public API:
  parse_resume(file_path: str) -> dict
"""

import json
from pathlib import Path

from extractor import extract_text
from cleaner import clean_text
from llm_parser import call_llm
from utils import (
    get_logger,
    safe_parse_json,
    normalize_skills,
    normalize_experience_level,
    normalize_keywords,
    deduplicate_list,
)

logger = get_logger(__name__)


# ─────────────────────────────────────────
# Public Entry Point
# ─────────────────────────────────────────

def parse_resume(file_path: str) -> dict:
    """
    Parse a resume file and return structured JSON data.

    This is the single public function of the module. It ties together
    all sub-modules into a clean, linear pipeline.

    Args:
        file_path (str): Path to the resume file (.pdf or .docx).

    Returns:
        dict: Structured resume data with the following keys:
          - full_name       (str | None)
          - role            (str | None)
          - skills          (list[str])
          - experience_level (str)
          - education       (list[dict])
          - projects        (list[dict])
          - keywords        (list[str])
          - _meta           (dict)  ← parsing metadata

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file format is unsupported or content is empty.
        RuntimeError: If extraction, LLM call, or JSON parsing fails.
    """
    file_name = Path(file_path).name
    logger.info("=" * 60)
    logger.info("Starting resume parsing for: %s", file_name)
    logger.info("=" * 60)

    # ── Step 1: Extract raw text ─────────────────────────────────────────────
    logger.info("[Step 1/5] Extracting text from file...")
    raw_text = extract_text(file_path)
    logger.info("[Step 1/5] Done. Raw text length: %d chars.", len(raw_text))

    # ── Step 2: Clean and preprocess text ────────────────────────────────────
    logger.info("[Step 2/5] Cleaning and preprocessing text...")
    clean = clean_text(raw_text)
    logger.info("[Step 2/5] Done. Cleaned text length: %d chars.", len(clean))

    # ── Step 3: Call LLM for structured extraction ───────────────────────────
    logger.info("[Step 3/5] Sending text to LLM for extraction...")
    raw_llm_response = call_llm(clean)
    logger.info("[Step 3/5] Done. LLM response length: %d chars.", len(raw_llm_response))

    # ── Step 4: Parse and validate JSON ──────────────────────────────────────
    logger.info("[Step 4/5] Parsing LLM JSON response...")
    parsed_data = safe_parse_json(raw_llm_response)
    logger.info("[Step 4/5] Done. JSON parsed successfully.")

    # ── Step 5: Normalize and structure the output ───────────────────────────
    logger.info("[Step 5/5] Normalizing and structuring output...")
    result = _normalize_output(parsed_data, file_name, len(raw_text), len(clean))
    logger.info("[Step 5/5] Done.")

    logger.info("Resume parsing complete for: %s", file_name)
    logger.info("=" * 60)

    logger.info("Data stored in JSON file data.json")
    with open(r"json_data/data.json", "w") as file:
        json.dump(result, file, indent =4)
    # return result


# ─────────────────────────────────────────
# Output Normalizer
# ─────────────────────────────────────────

def _normalize_output(
    data: dict,
    file_name: str,
    raw_length: int,
    clean_length: int,
) -> dict:
    """
    Normalize and sanitize every field in the parsed LLM output.

    This function:
      - Applies type checks and safe defaults for every field
      - Normalizes skills (title case, deduplicated)
      - Normalizes experience level to standard labels
      - Normalizes keywords (lowercase, deduplicated)
      - Sanitizes education and project entries
      - Adds _meta block with parsing diagnostics

    Args:
        data (dict):        Raw parsed dict from LLM JSON response.
        file_name (str):    Source file name for metadata.
        raw_length (int):   Character count of raw extracted text.
        clean_length (int): Character count after cleaning.

    Returns:
        dict: Fully normalized structured resume data.
    """
    return {
        "full_name": _safe_str(data.get("full_name")),
        "role": _safe_str(data.get("role")),
        "skills": normalize_skills(data.get("skills", [])),
        "experience_level": normalize_experience_level(
            data.get("experience_level", "")
        ),
        "education": _normalize_education(data.get("education", [])),
        "projects": _normalize_projects(data.get("projects", [])),
        "keywords": normalize_keywords(data.get("keywords", [])),
        "_meta": {
            "source_file": file_name,
            "raw_text_length": raw_length,
            "clean_text_length": clean_length,
            "fields_found": _count_non_null_fields(data),
        },
    }


def _normalize_education(education: list) -> list:
    """
    Normalize the education array.

    Each entry is expected to have: degree, field, institution, year.
    Missing string fields default to None; duplicate entries are removed.

    Args:
        education (list): Raw education list from LLM.

    Returns:
        list[dict]: Cleaned education entries.
    """
    if not isinstance(education, list):
        return []

    seen = set()
    result = []

    for entry in education:
        if not isinstance(entry, dict):
            continue

        cleaned = {
            "degree": _safe_str(entry.get("degree")),
            "field": _safe_str(entry.get("field")),
            "institution": _safe_str(entry.get("institution")),
            "year": _safe_str(entry.get("year")),
        }

        # Deduplicate by institution + degree combination
        key = f"{cleaned['institution']}|{cleaned['degree']}".lower()
        if key not in seen:
            seen.add(key)
            result.append(cleaned)

    return result


def _normalize_projects(projects: list) -> list:
    """
    Normalize the projects array.

    Each entry is expected to have: name, description, technologies.
    Technologies are normalized the same way as skills.

    Args:
        projects (list): Raw projects list from LLM.

    Returns:
        list[dict]: Cleaned project entries.
    """
    if not isinstance(projects, list):
        return []

    seen = set()
    result = []

    for entry in projects:
        if not isinstance(entry, dict):
            continue

        name = _safe_str(entry.get("name"))
        description = _safe_str(entry.get("description"))
        technologies = normalize_skills(entry.get("technologies", []))

        cleaned = {
            "name": name,
            "description": description,
            "technologies": technologies,
        }

        # Deduplicate by project name
        key = (name or "").lower().strip()
        if key not in seen:
            if key:
                seen.add(key)
            result.append(cleaned)

    return result


def _safe_str(value) -> str | None:
    """
    Safely convert a value to a stripped string, or return None.

    Returns None for null, empty strings, and the literal string "null".

    Args:
        value: Any value from parsed JSON.

    Returns:
        str | None: Cleaned string or None.
    """
    if value is None:
        return None
    text = str(value).strip()
    if not text or text.lower() in ("null", "none", "n/a", "na", "unknown"):
        return None
    return text


def _count_non_null_fields(data: dict) -> int:
    """
    Count how many top-level fields were successfully extracted (non-null / non-empty).

    Useful for diagnostics and quality scoring.

    Args:
        data (dict): Raw parsed LLM output dict.

    Returns:
        int: Number of non-empty fields found.
    """
    count = 0
    for key in ("full_name", "role", "skills", "experience_level", "education", "projects", "keywords"):
        val = data.get(key)
        if val is not None and val != "" and val != [] and val != {}:
            count += 1
    return count
