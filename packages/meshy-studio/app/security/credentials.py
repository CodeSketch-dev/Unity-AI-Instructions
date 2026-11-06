from __future__ import annotations

from typing import Protocol


SERVICE = "MeshyAIStudio"


class CredentialStore(Protocol):
    def set(self, account_key: str, kind: str, value: str) -> None: ...
    def get(self, account_key: str, kind: str) -> str | None: ...
    def delete(self, account_key: str, kind: str) -> None: ...


class KeyringCredentialStore:
    def _username(self, account_key: str, kind: str) -> str:
        return f"{account_key}:{kind}"

    def set(self, account_key: str, kind: str, value: str) -> None:
        import keyring
        keyring.set_password(SERVICE, self._username(account_key, kind), value)

    def get(self, account_key: str, kind: str) -> str | None:
        import keyring
        return keyring.get_password(SERVICE, self._username(account_key, kind))

    def delete(self, account_key: str, kind: str) -> None:
        import keyring
        try:
            keyring.delete_password(SERVICE, self._username(account_key, kind))
        except keyring.errors.PasswordDeleteError:
            pass


class MemoryCredentialStore:
    def __init__(self):
        self.values: dict[tuple[str, str], str] = {}

    def set(self, account_key: str, kind: str, value: str) -> None:
        self.values[(account_key, kind)] = value

    def get(self, account_key: str, kind: str) -> str | None:
        return self.values.get((account_key, kind))

    def delete(self, account_key: str, kind: str) -> None:
        self.values.pop((account_key, kind), None)

