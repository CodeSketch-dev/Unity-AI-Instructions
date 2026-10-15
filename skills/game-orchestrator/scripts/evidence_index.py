"""Build a compact evidence index from a GDD folder without loading image bytes."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".gif"}


def build(root):
    root = Path(root).resolve()
    files, images = [], []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or "_generated" in path.parts:
            continue
        relative = path.relative_to(root).as_posix()
        files.append(relative)
        if path.suffix.lower() in IMAGE_EXTENSIONS:
            images.append(relative)
    return {"schema": 1, "root": str(root), "files": files, "images": images,
            "image_count": len(images),
            "unknowns": [] if images else ["no reference images found; visual fidelity is unverified"]}


def validate_for_mapspec(index, require_images=False):
    """Return blocking reasons before image-to-MapSpec inference."""
    reasons = []
    if not isinstance(index, dict) or index.get("schema") != 1:
        reasons.append("evidence index schema 1 is required")
    if not isinstance(index.get("files"), list):
        reasons.append("evidence index files are required")
    if require_images and not index.get("images"):
        reasons.append("at least one reference image is required for image-to-MapSpec inference")
    return reasons


def validate_mapspec_artifact(spec):
    """Check the MapSpec gate's required top-level contract without dependencies."""
    required = ("schema", "source", "materials", "surfaces", "parts", "chunks", "camera", "evidence")
    reasons = []
    if not isinstance(spec, dict) or spec.get("schema") != 1:
        reasons.append("MapSpec schema 1 is required")
    if isinstance(spec, dict):
        reasons.extend("MapSpec missing %s" % key for key in required if key not in spec)
        if not isinstance(spec.get("evidence"), list) or not spec["evidence"]:
            reasons.append("MapSpec evidence must be non-empty")
    return reasons


def write(root, out):
    data = build(root)
    destination = Path(out)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".tmp")
    temporary.write_text(json.dumps(data, indent=1), encoding="utf-8")
    temporary.replace(destination)
    return data


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("root")
    ap.add_argument("--out", required=True)
    ap.add_argument("--require-images", action="store_true",
                    help="fail the gate when no reference image is indexed")
    args = ap.parse_args(argv)
    data = write(args.root, args.out)
    reasons = validate_for_mapspec(data, require_images=args.require_images)
    print(json.dumps({"index": data, "validation": reasons}, indent=1))
    return 1 if reasons else 0


if __name__ == "__main__":
    raise SystemExit(main())
