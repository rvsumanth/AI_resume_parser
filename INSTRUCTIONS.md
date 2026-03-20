# Resume Parser Module

A production-ready Python module that parses PDF and DOCX resumes
and returns clean structured JSON using OpenAI's LLM.

---

## Project Structure

```
resume_parser/
├── parser.py         # Main pipeline — start here
├── extractor.py      # PDF / DOCX text extraction
├── cleaner.py        # Text cleaning & preprocessing
├── llm_parser.py     # OpenAI API integration
├── utils.py          # Shared helper functions
├── config.py         # Settings & environment variables
├── __init__.py       # Package init
├── requirements.txt  # Python dependencies
├── .env.example      # Environment variable template
└── INSTRUCTIONS.md   # This file
```

---

## Setup Instructions

### 1. Prerequisites

- Python 3.10 or higher
- An OpenAI API key (https://platform.openai.com/api-keys)

### 2. Install Dependencies

```bash
cd resume_parser
pip install -r requirements.txt
```

### 3. Configure Environment Variables

```bash
cp .env.example .env
```

Open `.env` and fill in your OpenAI API key:

```
OPENAI_API_KEY=sk-your-actual-api-key-here
```

---

## Usage

### As a Python module

```python
import sys
sys.path.insert(0, "path/to/resume_parser")

from parser import parse_resume

result = parse_resume("path/to/resume.pdf")   # or .docx
print(result)
```

### Quick test from the command line

```bash
cd resume_parser
python -c "
from parser import parse_resume
import json
result = parse_resume('../sample_resume.pdf')
print(json.dumps(result, indent=2))
"
```

---

## Output Format

```json
{
  "full_name": "Jane Doe",
  "role": "Backend Engineer",
  "skills": ["Python", "Django", "PostgreSQL", "Docker"],
  "experience_level": "1-3",
  "education": [
    {
      "degree": "B.Tech",
      "field": "Computer Science",
      "institution": "IIT Hyderabad",
      "year": "2022"
    }
  ],
  "projects": [
    {
      "name": "Inventory Management System",
      "description": "A REST API built with FastAPI and PostgreSQL.",
      "technologies": ["Fastapi", "Postgresql", "Redis"]
    }
  ],
  "keywords": ["backend", "api", "microservices", "agile"],
  "_meta": {
    "source_file": "jane_doe_resume.pdf",
    "raw_text_length": 3200,
    "clean_text_length": 2870,
    "fields_found": 7
  }
}
```

### Experience Level Values

| Label    | Meaning                              |
|----------|--------------------------------------|
| Fresher  | No experience / fresh graduate       |
| 0-1      | Less than 1 year of experience       |
| 1-3      | 1 to 3 years of experience           |
| 3+       | More than 3 years of experience      |
| Unknown  | Could not be determined from resume  |

---

## Error Handling

The module raises clear exceptions for common failure cases:

| Exception           | Cause                                      |
|---------------------|--------------------------------------------|
| `FileNotFoundError` | Resume file does not exist                 |
| `ValueError`        | Unsupported format, empty file, bad JSON   |
| `RuntimeError`      | Extraction failure, OpenAI API error       |

Wrap calls in try/except for production use:

```python
try:
    result = parse_resume("resume.pdf")
except FileNotFoundError as e:
    print(f"File not found: {e}")
except ValueError as e:
    print(f"Validation error: {e}")
except RuntimeError as e:
    print(f"Processing error: {e}")
```

---

## Configuration Options (.env)

| Variable            | Default       | Description                          |
|---------------------|---------------|--------------------------------------|
| OPENAI_API_KEY      | (required)    | Your OpenAI API key                  |
| OPENAI_MODEL        | gpt-4o-mini   | Model for extraction                 |
| OPENAI_MAX_TOKENS   | 2000          | Max tokens in LLM response           |
| OPENAI_TEMPERATURE  | 0.0           | 0 = deterministic (recommended)      |
| LOG_LEVEL           | INFO          | Logging verbosity                    |

---

## Supported File Formats

| Format | Library         | Fallback  |
|--------|-----------------|-----------|
| PDF    | pdfplumber      | PyPDF2    |
| DOCX   | docx2txt        | —         |

> **Note:** Scanned/image-based PDFs are not supported as they require OCR.
> Consider adding `pytesseract` + `pdf2image` for OCR support.
