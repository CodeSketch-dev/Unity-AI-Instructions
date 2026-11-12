"""Write accounts.txt (email|password|recovery|totp) from the local DB + Windows credential store.

Usage: python tools/export_accounts.py <output.txt>
The file holds plaintext passwords: only for a team build you deliberately share.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.core.database import Database
from app.paths import app_root
from app.security.credentials import KeyringCredentialStore

root = app_root()
store = KeyringCredentialStore()
lines = []
for account in Database(root / "data" / "meshy.sqlite3").list_accounts():
    password = store.get(account.email, "password")
    if not password:
        print(f"skip {account.email}: no stored password", file=sys.stderr)
        continue
    fields = [account.email, password]
    totp = store.get(account.email, "totp")
    if account.recovery_email or totp:
        fields += [account.recovery_email or "", totp or ""]
    lines.append("|".join(fields))
Path(sys.argv[1]).write_text("\n".join(lines) + "\n", encoding="utf-8")
print(f"wrote {len(lines)} accounts")
