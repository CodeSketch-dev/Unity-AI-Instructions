import re


# Anything that can unlock an account must never reach a log: passwords, tokens/API keys/TOTP secrets, cookies, OTP codes.
_PATTERNS = (
    re.compile(r"(?i)((?:otp|verification code|one[- ]time (?:code|password)|code)\s*(?:is|=|:)\s*)\d{4,8}"),
    re.compile(r"(?i)((?:set-)?cookie\s*[=:]\s*)[^\n]+"),
    re.compile(r"(?i)((?:token|secret|api[_-]?key|totp)\s*[=:]\s*)[^\s,;]+"),
    re.compile(r"(?i)(authorization\s*:\s*bearer\s+)[^\s,;]+"),
    re.compile(r"(?i)((?:password|passwd|pwd)\s*[=:]\s*)[^\s,;]+"),
    re.compile(r'(?i)(["\']?(?:totp_secret|api_key|password|token)["\']?\s*:\s*["\'])[^"\']+'),
)


def redact(value: object) -> str:
    text = str(value)
    for pattern in _PATTERNS:
        text = pattern.sub(r"\1[REDACTED]", text)
    return text
