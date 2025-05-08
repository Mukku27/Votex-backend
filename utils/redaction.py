"""
Regex utilities for PII detection and redaction.
"""
import re

PII_PATTERNS = [
    r"\b\d{6,}\b",                                 # long numeric sequences
    r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",  # email addresses
]

def redact_pii(text: str) -> str:
    """
    Replace detected PII patterns with “[REDACTED]”.
    """
    for pattern in PII_PATTERNS:
        text = re.sub(pattern, "[REDACTED]", text)
    return text
