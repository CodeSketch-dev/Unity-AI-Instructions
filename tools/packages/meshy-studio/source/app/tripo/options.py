from __future__ import annotations

import json
from dataclasses import asdict, dataclass

MODEL_VERSIONS = ["v3.0-20250812", "v2.5-20250123", "v2.0-20240919"]  # editable in the UI: Tripo ships new ones often
DEFAULT_VERSION = MODEL_VERSIONS[0]
MIN_FACES, MAX_FACES, DEFAULT_FACES = 500, 60_000, 10_000


@dataclass(slots=True)
class TripoOptions:
    model_version: str = DEFAULT_VERSION
    face_limit: int = DEFAULT_FACES       # target triangles (quad=False) or quads
    texture: bool = True
    pbr: bool = False                     # PBR maps cost more credits and are not needed for the flat-lit mobile look
    texture_quality: str = "detailed"     # "standard" | "detailed"
    texture_alignment: str = "original_image"  # "original_image" keeps the concept's look | "geometry"
    smart_low_poly: bool = True           # clean hand-made-style low poly topology
    quad: bool = False
    auto_size: bool = True
    orientation: str = "default"          # "default" | "align_image"
    download: bool = False                # fetch GLB/FBX when done (Tripo free accounts cannot export; off = generate only)

    def normalized(self) -> "TripoOptions":
        quality = self.texture_quality if self.texture_quality in ("standard", "detailed") else "detailed"
        align = self.texture_alignment if self.texture_alignment in ("original_image", "geometry") else "original_image"
        orient = self.orientation if self.orientation in ("default", "align_image") else "default"
        return TripoOptions((self.model_version or DEFAULT_VERSION).strip(), max(MIN_FACES, min(MAX_FACES, int(self.face_limit))),
                            bool(self.texture), bool(self.pbr), quality, align, bool(self.smart_low_poly), bool(self.quad),
                            bool(self.auto_size), orient, bool(self.download))

    def to_json(self) -> str:
        return json.dumps(asdict(self.normalized()))

    @staticmethod
    def from_dict(data: dict | None) -> "TripoOptions":
        base = TripoOptions()
        data = data or {}
        values = {name: data.get(name, getattr(base, name)) for name in TripoOptions.__slots__}
        return TripoOptions(**values).normalized()

    def task_body(self, file_type: str, file_token: str) -> dict:
        o = self.normalized()
        body = {"type": "image_to_model", "file": {"type": file_type, "file_token": file_token},
                "model_version": o.model_version, "face_limit": o.face_limit, "texture": o.texture, "pbr": o.pbr,
                "texture_quality": o.texture_quality, "texture_alignment": o.texture_alignment, "quad": o.quad,
                "auto_size": o.auto_size, "orientation": o.orientation}
        if o.smart_low_poly:
            body["smart_low_poly"] = True
        return body
