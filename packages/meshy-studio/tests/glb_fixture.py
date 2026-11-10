"""Builds small but valid GLB files for tests (a real mesh with N triangles and an optional PNG texture)."""
import io
import json
import struct
from pathlib import Path


def make_mesh_glb(path: Path, triangles: int = 12, texture: bool = True) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    indices = struct.pack(f"<{triangles * 3}H", *[i % (triangles * 3) for i in range(triangles * 3)])
    positions = struct.pack("<9f", 0, 0, 0, 1, 0, 0, 0, 1, 0)
    blob = indices + b"\0" * (-len(indices) % 4)
    pos_offset = len(blob)
    blob += positions
    views = [{"buffer": 0, "byteOffset": 0, "byteLength": len(indices)},
             {"buffer": 0, "byteOffset": pos_offset, "byteLength": len(positions)}]
    document = {
        "asset": {"version": "2.0"},
        "meshes": [{"primitives": [{"attributes": {"POSITION": 1}, "indices": 0, "material": 0}]}],
        "accessors": [{"bufferView": 0, "componentType": 5123, "count": triangles * 3, "type": "SCALAR"},
                      {"bufferView": 1, "componentType": 5126, "count": 3, "type": "VEC3"}],
        "materials": [{}],
    }
    if texture:
        from PIL import Image
        buffer = io.BytesIO()
        Image.new("RGB", (4, 4), (200, 30, 30)).save(buffer, format="PNG")
        png = buffer.getvalue()
        while len(blob) % 4:
            blob += b"\0"
        views.append({"buffer": 0, "byteOffset": len(blob), "byteLength": len(png)})
        blob += png
        document["images"] = [{"bufferView": 2, "mimeType": "image/png"}]
        document["textures"] = [{"source": 0}]
        document["materials"] = [{"pbrMetallicRoughness": {"baseColorTexture": {"index": 0}}}]
    document["bufferViews"] = views
    blob += b"\0" * (-len(blob) % 4)
    document["buffers"] = [{"byteLength": len(blob)}]
    text = json.dumps(document).encode()
    text += b" " * (-len(text) % 4)
    body = struct.pack("<II", len(text), 0x4E4F534A) + text + struct.pack("<II", len(blob), 0x004E4942) + blob
    path.write_bytes(b"glTF" + struct.pack("<II", 2, 12 + len(body)) + body)
    return path
