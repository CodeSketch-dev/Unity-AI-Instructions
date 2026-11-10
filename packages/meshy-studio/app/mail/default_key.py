"""Built-in fallback Purelymail API key (obfuscated, NOT secure: anyone with the repo or exe can recover it).
A key saved on the Purelymail page (Windows credential store) always wins over this default."""
from __future__ import annotations

import base64

_PAD = b"MeshyAIStudio-default-key-pad"
_BLOB = "PQheBBA3LH5AE1JZDhxXBEtVQV4RAF9cTR5dAwd0AF5fTnktYBJNBV5YSFA="


def default_token() -> str:
    raw = base64.b64decode(_BLOB)
    return bytes(b ^ _PAD[i % len(_PAD)] for i, b in enumerate(raw)).decode()
