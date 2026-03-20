"""
config.py
---------
Central configuration file for the Resume Parser module.
Loads environment variables and defines constants used across the project.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# ─────────────────────────────────────────
# Groq Configuration
# ─────────────────────────────────────────

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
GROQ_MAX_TOKENS = int(os.getenv("GROQ_MAX_TOKENS", "2000"))
GROQ_TEMPERATURE = float(os.getenv("GROQ_TEMPERATURE", "0.0"))  # 0 = deterministic

# ─────────────────────────────────────────
# Supported File Types
# ─────────────────────────────────────────

SUPPORTED_EXTENSIONS = {".pdf", ".docx"}

# ─────────────────────────────────────────
# Experience Level Mapping
# Used to normalize LLM output to standard labels
# ─────────────────────────────────────────

EXPERIENCE_LEVELS = {
    "fresher": "Fresher",
    "entry": "0-1",
    "junior": "0-1",
    "0-1": "0-1",
    "mid": "1-3",
    "intermediate": "1-3",
    "1-3": "1-3",
    "senior": "3+",
    "lead": "3+",
    "expert": "3+",
    "3+": "3+",
}

# ─────────────────────────────────────────
# Logging Configuration
# ─────────────────────────────────────────

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"