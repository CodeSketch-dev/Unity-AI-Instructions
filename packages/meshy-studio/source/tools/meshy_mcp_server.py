"""Entry point of the Meshy AI Studio MCP server (stdio). Register it with Claude Code / Codex: see docs/mcp-setup.md.

Account import is kept here (it needs the credential store): it takes a file path, never inline passwords."""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.mcp import context  # noqa: E402
from app.mcp.registry import STR, schema, tool  # noqa: E402
from app.mcp.server import main  # noqa: E402


@tool("import_accounts", "Import a .txt file of lines: email (Purelymail OTP login), or email|password[|recovery_email|totp_secret].",
      schema(["file_path"], file_path=STR))
def import_accounts(args: dict) -> dict:
    from app.core.account_manager import AccountManager
    from app.security.credentials import KeyringCredentialStore, MemoryCredentialStore
    store = MemoryCredentialStore() if os.environ.get("MESHY_CREDENTIALS") == "memory" else KeyringCredentialStore()
    database = context.db()
    try:
        result = AccountManager(database, store, context.DATA / "profiles").import_file(args["file_path"])
        return {"imported": result.imported, "duplicates": result.duplicates, "invalid": result.invalid}
    finally:
        database.close()


if __name__ == "__main__":
    main()
