import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def rpc(tmp_path, calls):
    env = dict(os.environ, MESHY_DATA_DIR=str(tmp_path), MESHY_NO_SPAWN="1", MESHY_CREDENTIALS="memory")
    lines = "\n".join(json.dumps({"jsonrpc": "2.0", "id": i, "method": m, "params": p}) for i, (m, p) in enumerate(calls, 1))
    out = subprocess.run([sys.executable, str(ROOT / "tools" / "meshy_mcp_server.py")], input=lines + "\n",
                         capture_output=True, text=True, env=env, timeout=60, cwd=str(ROOT)).stdout
    return [json.loads(x) for x in out.splitlines()]


def call(name, **args):
    return ("tools/call", {"name": name, "arguments": args})


def test_tools_list_and_generate_flow(tmp_path):
    img = tmp_path / "a.png"
    img.write_bytes(b"x")
    accounts = tmp_path / "acc.txt"
    accounts.write_text("buyer@example.com|supersecret|rec@example.com|GEZDGNBVGY3TQOJQ\n")
    res = rpc(tmp_path, [
        ("tools/list", {}),
        call("generate_model", image_path=str(img)),
        call("generate_model", image_path=str(tmp_path / "bad.txt")),
        call("job_status", job_id=1),
        call("import_accounts", file_path=str(accounts)),
        call("list_accounts"),
    ])
    names = {t["name"] for t in res[0]["result"]["tools"]}
    assert {"generate_model", "job_status", "list_jobs", "list_accounts", "import_accounts"} <= names
    assert json.loads(res[1]["result"]["content"][0]["text"])["job_id"] == 1
    assert res[2]["result"]["isError"] is True
    assert json.loads(res[3]["result"]["content"][0]["text"])["status"] == "Pending"
    assert json.loads(res[4]["result"]["content"][0]["text"])["imported"] == 1
    listing = res[5]["result"]["content"][0]["text"]
    assert "buyer@example.com" in listing and "supersecret" not in listing and "GEZD" not in listing
