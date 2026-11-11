import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from _common import args, result, reset, import_model, meshes, tri_count, total_tris, export, select_only  # noqa: E402
import bpy  # noqa: E402

cfg = args()
reset()
objects = import_model(cfg["input"])
parts = meshes(objects)
before = total_tris(parts)
target = int(cfg["target_tris"])
if before > target > 0:
    for obj in parts:
        share = tri_count(obj) / max(1, before)
        want = max(4, int(target * share))
        have = tri_count(obj)
        if have <= want:
            continue
        select_only([obj])
        mod = obj.modifiers.new("Decimate", "DECIMATE")
        mod.decimate_type = "COLLAPSE"
        mod.ratio = max(0.001, min(1.0, want / have))
        mod.use_collapse_triangulate = True
        bpy.ops.object.modifier_apply(modifier=mod.name)
export(cfg["output"], objects)
result({"triangles_before": before, "triangles_after": total_tris(parts), "target": target, "output": cfg["output"]})
