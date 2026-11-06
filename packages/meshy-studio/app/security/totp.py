from __future__ import annotations

import base64
import hashlib
import hmac
import struct
import time


def totp_now(secret: str, *, at: float | None = None, digits: int = 6, step: int = 30) -> str:
    """RFC 6238 TOTP (SHA-1), stdlib only. Secret is base32, spaces allowed."""
    cleaned = secret.replace(" ", "").replace("-", "").upper()
    cleaned += "=" * (-len(cleaned) % 8)
    key = base64.b32decode(cleaned, casefold=True)
    counter = int((time.time() if at is None else at) // step)
    digest = hmac.new(key, struct.pack(">Q", counter), hashlib.sha1).digest()
    offset = digest[-1] & 0x0F
    code = (struct.unpack(">I", digest[offset:offset + 4])[0] & 0x7FFFFFFF) % (10 ** digits)
    return str(code).zfill(digits)
