"""Call one tool of tools/meshy_mcp_server.py over stdio (for manual checks)."""
import json, os, subprocess, sys
name, args = sys.argv[1], json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}
req = [{"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": name, "arguments": args}}]
env = dict(os.environ, MESHY_NO_SPAWN="1")
out = subprocess.run([sys.executable, os.path.join(os.path.dirname(__file__), "meshy_mcp_server.py")],
                     input="\n".join(json.dumps(r) for r in req) + "\n", capture_output=True, text=True, env=env).stdout
print(out)
