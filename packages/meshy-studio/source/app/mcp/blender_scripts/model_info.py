import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from _common import args, result, reset, import_model, meshes, tri_count  # noqa: E402
import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402

cfg = args()
reset()
objects = import_model(cfg["input"])
parts = meshes(objects)
lo, hi = Vector((1e9,) * 3), Vector((-1e9,) * 3)
for obj in parts:
    for corner in obj.bound_box:
        world = obj.matrix_world @ Vector(corner)
        lo = Vector(min(a, b) for a, b in zip(lo, world))
        hi = Vector(max(a, b) for a, b in zip(hi, world))
images = {}
for image in bpy.data.images:
    if image.size[0] and image.name not in ("Render Result", "Viewer Node"):
        images[image.name] = [image.size[0], image.size[1]]
result({"meshes": len(parts), "triangles": sum(tri_count(o) for o in parts), "materials": len(bpy.data.materials),
        "images": images, "uv_layers": sorted({u.name for o in parts for u in o.data.uv_layers}),
        "size_xyz": [round(hi[i] - lo[i], 4) for i in range(3)] if parts else [0, 0, 0],
        "bones": sum(len(a.data.bones) for a in objects if a.type == "ARMATURE")})
