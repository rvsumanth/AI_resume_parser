"""
resume_parser
-------------
A production-ready resume parsing module for AI job recommendation systems.

Public API:
    from resume_parser.parser import parse_resume

    result = parse_resume("path/to/resume.pdf")
"""

from parser import parse_resume

__all__ = ["parse_resume"]
__version__ = "1.0.0"
