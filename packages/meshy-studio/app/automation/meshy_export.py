from __future__ import annotations

import base64
import json
import struct
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from app.paths import app_root

EXTENSION_DIR = app_root() / "docs" / "vendor" / "meshy-ai-to-stl" / "chrome-extension"
CONVERT_PAGE = "convert_auto.html"
# Posts the raw .meshy bytes to the extension's sandboxed decoder and returns the GLB as base64.
_CONVERT_HTML = """<!doctype html><iframe id="f" src="sandbox.html"></iframe><script>
const f=document.getElementById("f");
window.convertMeshy=(buffer,format)=>new Promise((resolve,reject)=>{
  const id=Date.now()+Math.random();
  const handler=e=>{if(!e.data||e.data.id!==id)return;window.removeEventListener("message",handler);
    if(!e.data.ok){reject(new Error(e.data.error||"decode failed"));return;}
    const r=new FileReader();r.onload=()=>resolve(r.result.split(",")[1]);
    r.readAsDataURL(new Blob([e.data.output]));};
  window.addEventListener("message",handler);
  f.contentWindow.postMessage({type:"convert",id,format:format||"glb",buffer},"*");
});
</script>"""


class MeshyExportError(RuntimeError):
    pass


def inspect_glb(path: str | Path) -> dict[str, int]:
    """Triangle and texture counts of a GLB, read from its JSON chunk."""
    data = Path(path).read_bytes()
    if data[:4] != b"glTF":
        raise MeshyExportError("Not a GLB file")
    length, kind = struct.unpack_from("<II", data, 12)
    document = json.loads(data[20:20 + length].decode("utf-8"))
    accessors = document.get("accessors", [])
    triangles = 0
    for mesh in document.get("meshes", []):
        for primitive in mesh.get("primitives", []):
            index = primitive.get("indices")
            if index is not None:
                triangles += accessors[index]["count"] // 3
            else:
                triangles += accessors[primitive["attributes"]["POSITION"]]["count"] // 3
    return {"triangles": triangles, "images": len(document.get("images", [])), "materials": len(document.get("materials", []))}


class MeshyExporter:
    """Downloads the selected Meshy asset as GLB via the bundled meshy-ai-to-stl decoder."""

    def __init__(self, extension_dir: Path = EXTENSION_DIR):
        self.extension_dir = Path(extension_dir)

    def decoder_ready(self) -> bool:
        vendor = self.extension_dir / "vendor"
        return (vendor / "mesh_loader.js").exists() and (vendor / "mesh_loader.wasm").exists()

    def export_latest(self, context: Any, page: Any, out_path: str | Path, *, max_triangles: int = 15_000) -> dict[str, Any]:
        """Download the newest finished low-poly (remeshed) task as GLB and verify it."""
        if not self.decoder_ready():
            raise MeshyExportError("Decoder files missing; run setup-vendor.ps1 in docs/vendor/meshy-ai-to-stl")
        task = self.latest_task(page, max_triangles=max_triangles)
        response = context.request.get(task["result"]["texture"]["modelUrl"])
        if not response.ok:
            raise MeshyExportError(f"Model download failed: HTTP {response.status}")
        out = Path(out_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(self._decode(context, list(response.body())))
        info = inspect_glb(out)
        return {"path": out, "task_id": task["id"], **info}

    @staticmethod
    def latest_task(page: Any, *, max_triangles: int = 15_000) -> dict[str, Any]:
        """Capture the app's own task-list response on reload (the API needs the page's auth).

        The body is read inside the response handler: Playwright drops it once the page navigates again.
        """
        tasks: list[dict[str, Any]] = []

        def on_response(response: Any) -> None:
            if "/meshyd-api/web/v2/tasks?" in response.url and not tasks:
                try:
                    tasks.extend(response.json().get("result") or [])
                except Exception:
                    pass

        page.on("response", on_response)
        try:
            for _ in range(3):
                page.reload(wait_until="domcontentloaded")
                for _ in range(24):
                    if tasks:
                        break
                    page.wait_for_timeout(500)
                if tasks:
                    break
        finally:
            page.remove_listener("response", on_response)
        if not tasks:
            raise MeshyExportError("Meshy task list was not loaded")
        for task in tasks:  # newest first
            result = task.get("result") or {}
            url = (result.get("texture") or {}).get("modelUrl")
            if task.get("status") == "SUCCEEDED" and url and 0 < task.get("triangleCount", 0) <= max_triangles:
                return task
        raise MeshyExportError("No finished low-poly textured task found")

    def _decode(self, context: Any, raw: list[int]) -> bytes:
        page_file = self.extension_dir / CONVERT_PAGE
        if not page_file.exists() or page_file.read_text(encoding="utf-8") != _CONVERT_HTML:
            page_file.write_text(_CONVERT_HTML, encoding="utf-8")
        handler = partial(_QuietHandler, directory=str(self.extension_dir))
        server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        decoder = context.new_page()
        try:
            decoder.goto(f"http://127.0.0.1:{server.server_address[1]}/{CONVERT_PAGE}")
            decoder.wait_for_timeout(1000)
            encoded = decoder.evaluate(
                "async b => await window.convertMeshy(new Uint8Array(b).buffer, 'glb')", raw)
            return base64.b64decode(encoded)
        finally:
            decoder.close()
            server.shutdown()
            server.server_close()


class _QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args: Any) -> None:
        pass
