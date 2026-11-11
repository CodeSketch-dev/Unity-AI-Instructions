"""Built-in fallback Purelymail API key (obfuscated, NOT secure: anyone with the repo or exe can recover it).
Built-in fallbacks also cover the shared mailbox password. Values saved in the Windows credential store always win."""
from __future__ import annotations

import base64

_PAD = b"MeshyAIStudio-default-key-pad"
_BLOB = "PQheBBA3LH5AE1JZDhxXBEtVQV4RAF9cTR5dAwd0AF5fTnktYBJNBV5YSFA="


def default_token() -> str:
    raw = base64.b64decode(_BLOB)
    return bytes(b ^ _PAD[i % len(_PAD)] for i, b in enumerate(raw)).decode()


_PASSWORD_BLOB = "Dg0aDRcBeWBNRlJRWRxTXQ=="


def default_mail_password() -> str:
    raw = base64.b64decode(_PASSWORD_BLOB)
    return bytes(b ^ _PAD[i % len(_PAD)] for i, b in enumerate(raw)).decode()
