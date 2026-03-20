"""
llm_parser.py
-------------
Handles all interaction with the Groq API.

Groq provides OpenAI-compatible Chat Completions endpoints with
ultra-fast inference via their custom LPU hardware.

Responsibilities:
  - Build a structured extraction prompt
  - Call the Groq Chat Completions API
  - Return the raw LLM response string for downstream parsing

Design principles:
  - Zero hallucination: prompt explicitly forbids guessing
  - JSON-only output: no markdown preamble allowed
  - Structured schema: every field is defined with type + instructions
"""

from groq import Groq, GroqError

from config import (
    GROQ_API_KEY,
    GROQ_MODEL,
    GROQ_MAX_TOKENS,
    GROQ_TEMPERATURE,
)
from utils import get_logger

logger = get_logger(__name__)

# Initialise the Groq client once (module-level singleton)
_client: Groq | None = None


def _get_client() -> Groq:
    """
    Return a module-level Groq client, creating it on first call.
    Raises RuntimeError if the API key is missing.
    """
    global _client
    if _client is None:
        if not GROQ_API_KEY:
            raise RuntimeError(
                "GROQ_API_KEY is not set. "
                "Add it to your .env file or set it as an environment variable. "
                "Get a free key at: https://console.groq.com/keys"
            )
        _client = Groq(api_key=GROQ_API_KEY)
    return _client



# ─────────────────────────────────────────
# Prompt Builder
# ─────────────────────────────────────────

def _build_prompt(resume_text: str) -> str:
    """
    Build a highly structured extraction prompt for the LLM.

    The prompt:
      - Gives the model an explicit role (expert resume parser)
      - Lists every field with its data type and allowed values
      - Forbids hallucination with an explicit instruction
      - Demands pure JSON output with no surrounding text

    Args:
        resume_text (str): Cleaned resume text.

    Returns:
        str: Fully formatted user prompt string.
    """
    return f"""You are an expert resume parser. Your only task is to extract structured information from the resume text provided below.

STRICT RULES:
1. Return ONLY a valid JSON object — no markdown, no code fences, no explanations.
2. Do NOT invent, assume, or hallucinate any information not present in the resume.
3. If a field is not found in the resume, use null for strings/objects or [] for arrays.
4. All string values must be properly escaped for JSON.

EXTRACT the following fields exactly:

{{
  "full_name": "<string> The candidate's full name. null if not found.",
  "role": "<string> The candidate's current or target job title/role. null if not found.",
  "skills": "<array of strings> All technical and soft skills mentioned. Normalize to title case. Remove duplicates.",
  "experience_level": "<string> One of exactly: 'Fresher', '0-1', '1-3', '3+'. Infer from years of experience or job titles. null if unclear.",
  "education": [
    {{
      "degree": "<string> Degree name e.g. B.Tech, MBA, B.Sc",
      "field": "<string> Field of study e.g. Computer Science",
      "institution": "<string> University or college name",
      "year": "<string> Graduation year or range e.g. 2020 or 2018-2022. null if not found."
    }}
  ],
  "projects": [
    {{
      "name": "<string> Project title",
      "description": "<string> Brief description of the project (1-2 sentences)",
      "technologies": "<array of strings> Technologies used in this project"
    }}
  ],
  "keywords": "<array of strings> Important keywords for job matching: tools, domain areas, certifications, methodologies. All lowercase."
}}

RESUME TEXT:
\"\"\"
{resume_text}
\"\"\"

Respond with the JSON object only. No other text."""


# ─────────────────────────────────────────
# LLM Call
# ─────────────────────────────────────────

def call_llm(resume_text: str) -> str:
    """
    Send the resume text to the Groq API and return the raw response string.

    Uses a two-message conversation:
      - system: Sets the model's role as a resume parser
      - user:   Contains the detailed prompt with the resume text

    Groq's API is fully compatible with the OpenAI Chat Completions
    interface, so the call structure is identical.

    Args:
        resume_text (str): Cleaned resume text to parse.

    Returns:
        str: Raw LLM response string (expected to be JSON).

    Raises:
        ValueError: If the input text is empty.
        RuntimeError: If the Groq API call fails for any reason.
    """
    if not resume_text or not resume_text.strip():
        raise ValueError("Resume text is empty. Cannot call LLM.")

    client = _get_client()
    prompt = _build_prompt(resume_text)

    logger.info(
        "Calling Groq API | model=%s | max_tokens=%d | temperature=%.1f",
        GROQ_MODEL,
        GROQ_MAX_TOKENS,
        GROQ_TEMPERATURE,
    )

    try:
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            max_tokens=GROQ_MAX_TOKENS,
            temperature=GROQ_TEMPERATURE,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a professional resume parsing assistant. "
                        "You extract structured data from resumes and output "
                        "valid JSON only. You never add extra commentary."
                    ),
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
        )

        raw_output = response.choices[0].message.content
        logger.info(
            "Groq API call successful. Response length: %d chars. "
            "Tokens used: prompt=%d, completion=%d, total=%d",
            len(raw_output) if raw_output else 0,
            response.usage.prompt_tokens,
            response.usage.completion_tokens,
            response.usage.total_tokens,
        )

        return raw_output or ""

    except GroqError as e:
        logger.error("Groq API error: %s", e)
        raise RuntimeError(f"Groq API call failed: {e}") from e
    except Exception as e:
        logger.error("Unexpected error during LLM call: %s", e)
        raise RuntimeError(f"Unexpected error calling LLM: {e}") from e