import re


_PATTERNS = (
    re.compile(r"(?i)(authorization\s*:\s*bearer\s+)[^\s,;]+"),
    re.compile(r"(?i)((?:password|cookie)\s*[=:]\s*)[^\s,;]+"),
    re.compile(r'(?i)(["\']?(?:totp_secret|api_key)["\']?\s*:\s*["\'])[^"\']+'),
)


def redact(value: object) -> str:
    text = str(value)
    for pattern in _PATTERNS:
        text = pattern.sub(r"\1[REDACTED]", text)
    return text

