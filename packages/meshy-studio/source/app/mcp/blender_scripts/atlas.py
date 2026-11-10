"""Pack several textured models into ONE shared texture atlas (one material, one texture for all of them).

Method: copy each UV map to an 'AtlasUV' layer, pack every island of every model together, bake the original materials'
base colour into the shared image through the packed UVs (Cycles, diffuse colour only), then give every mesh the same
material and export each model on its own. Meshes must be static (no armature)."""
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from _common import args, result, reset, import_model, meshes, tri_count, export  # noqa: E402
import bpy  # noqa: E402

cfg = args()
SIZE = int(cfg.get("atlas_size", 2048))
MARGIN_PX = int(cfg.get("margin_px", 8))
OUT = cfg["output_dir"]
FORMATS = cfg.get("formats", ["fbx"])
UNWRAP = cfg.get("unwrap", "smart")
ANGLE = float(cfg.get("angle_limit", 66))
os.makedirs(OUT, exist_ok=True)
reset()

groups = []  # (name, [mesh objects])
for item in cfg["inputs"]:
    objs = meshes(import_model(item["path"]))
    if not objs:
        raise RuntimeError("no mesh in " + item["path"])
    groups.append((item["name"], objs))
allm = [o for _, objs in groups for o in objs]

# ---- prepare: apply scale (so island density follows real size), make sure every mesh has UVs -----------------------
bpy.ops.object.select_all(action="DESELECT")
for o in allm:
    o.select_set(True)
    bpy.context.view_layer.objects.active = o
bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
for o in allm:
    if not o.data.uv_layers:
        bpy.context.view_layer.objects.active = o
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_all(action="SELECT")
        bpy.ops.uv.smart_project(island_margin=0.02)
        bpy.ops.object.mode_set(mode="OBJECT")


def uv_attr(mesh, name):
    return mesh.attributes[name]


original_uv = {}
for o in allm:
    mesh = o.data
    src = mesh.uv_layers.active.name
    original_uv[o.name] = src
    buf = [0.0] * (len(mesh.loops) * 2)
    mesh.attributes[src].data.foreach_get("vector", buf)
    mesh.uv_layers.new(name="AtlasUV")
    mesh.attributes["AtlasUV"].data.foreach_set("vector", buf)
    if UNWRAP == "smart":
        # Meshy's own unwrap is shredded into hundreds of tiny islands; a fresh angle-based unwrap gives large clean islands.
        # The bake below still reads colours through the ORIGINAL UVs, so the look is kept.
        mesh.uv_layers.active = mesh.uv_layers["AtlasUV"]
        bpy.ops.object.select_all(action="DESELECT")
        o.select_set(True)
        bpy.context.view_layer.objects.active = o
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_all(action="SELECT")
        bpy.ops.uv.smart_project(angle_limit=math.radians(ANGLE), island_margin=0.0, correct_aspect=True, scale_to_bounds=False)
        bpy.ops.object.mode_set(mode="OBJECT")

# ---- pack all islands together on temporary duplicates ------------------------------------------------------------
dups = []
for index, o in enumerate(allm):
    d = o.copy()
    d.data = o.data.copy()
    bpy.context.collection.objects.link(d)
    mesh = d.data
    mesh.attributes.new("src_obj", "INT", "FACE")
    mesh.attributes.new("src_poly", "INT", "FACE")
    mesh.attributes["src_obj"].data.foreach_set("value", [index] * len(mesh.polygons))
    mesh.attributes["src_poly"].data.foreach_set("value", list(range(len(mesh.polygons))))
    for layer in [u for u in mesh.uv_layers if u.name != "AtlasUV"]:
        mesh.uv_layers.remove(layer)
    mesh.uv_layers.active = mesh.uv_layers["AtlasUV"]
    d.modifiers.clear()
    dups.append(d)
bpy.ops.object.select_all(action="DESELECT")
for d in dups:
    d.select_set(True)
bpy.context.view_layer.objects.active = dups[0]
bpy.ops.object.join()
joined = bpy.context.view_layer.objects.active
bpy.context.scene.tool_settings.use_uv_select_sync = True
bpy.ops.object.mode_set(mode="EDIT")
bpy.ops.mesh.select_all(action="SELECT")
if cfg.get("density", "equalize") == "equalize":
    bpy.ops.uv.average_islands_scale()
bpy.ops.uv.pack_islands(rotate=bool(cfg.get("rotate", True)), rotate_method="ANY", shape_method="CONCAVE", margin=MARGIN_PX / SIZE)
bpy.ops.object.mode_set(mode="OBJECT")

jm = joined.data
packed = [0.0] * (len(jm.loops) * 2)
jm.attributes["AtlasUV"].data.foreach_get("vector", packed)
src_obj = [0] * len(jm.polygons)
src_poly = [0] * len(jm.polygons)
jm.attributes["src_obj"].data.foreach_get("value", src_obj)
jm.attributes["src_poly"].data.foreach_get("value", src_poly)
buffers = {i: [0.0] * (len(o.data.loops) * 2) for i, o in enumerate(allm)}
for poly in jm.polygons:
    target = allm[src_obj[poly.index]].data
    tpoly = target.polygons[src_poly[poly.index]]
    for k in range(poly.loop_total):
        ju, tl = poly.loop_start + k, tpoly.loop_start + k
        buffers[src_obj[poly.index]][tl * 2] = packed[ju * 2]
        buffers[src_obj[poly.index]][tl * 2 + 1] = packed[ju * 2 + 1]
for i, o in enumerate(allm):
    o.data.attributes["AtlasUV"].data.foreach_set("vector", buffers[i])
bpy.data.objects.remove(joined, do_unlink=True)

# ---- bake the original colours into the shared atlas ----------------------------------------------------------------
scene = bpy.context.scene
scene.render.engine = "CYCLES"
scene.cycles.device = "CPU"
scene.cycles.samples = 1
scene.render.bake.margin = MARGIN_PX
scene.render.bake.use_pass_direct = False
scene.render.bake.use_pass_indirect = False
scene.render.bake.use_pass_color = True
atlas = bpy.data.images.new("atlas", SIZE, SIZE, alpha=False)
atlas.generated_color = (0.5, 0.5, 0.5, 1.0)
for o in allm:
    mesh = o.data
    mesh.uv_layers[original_uv[o.name]].active_render = True  # materials keep sampling their own textures
    mesh.uv_layers.active = mesh.uv_layers["AtlasUV"]         # the bake writes through the packed layout
    if not o.material_slots:
        mat = bpy.data.materials.new(o.name + "_flat")
        mat.diffuse_color = (0.8, 0.8, 0.8, 1)
        o.data.materials.append(mat)
    for slot in o.material_slots:
        mat = slot.material
        mat.use_nodes = True
        node = mat.node_tree.nodes.new("ShaderNodeTexImage")
        node.image = atlas
        node.select = True
        mat.node_tree.nodes.active = node
bpy.ops.object.select_all(action="DESELECT")
for o in allm:
    o.select_set(True)
bpy.context.view_layer.objects.active = allm[0]
bpy.ops.object.bake(type="DIFFUSE", pass_filter={"COLOR"}, margin=MARGIN_PX)
atlas_path = os.path.join(OUT, "atlas.png")
atlas.filepath_raw = atlas_path
atlas.file_format = "PNG"
atlas.save()

# ---- one shared material for every mesh, packed UVs only ------------------------------------------------------------
shared = bpy.data.materials.new("Atlas")
shared.use_nodes = True
nodes = shared.node_tree.nodes
tex = nodes.new("ShaderNodeTexImage")
tex.image = atlas
bsdf = nodes["Principled BSDF"]
bsdf.inputs["Roughness"].default_value = 1.0
bsdf.inputs["Metallic"].default_value = 0.0
shared.node_tree.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
for o in allm:
    mesh = o.data
    mesh.materials.clear()
    mesh.materials.append(shared)
    for layer in [u for u in mesh.uv_layers if u.name != "AtlasUV"]:
        mesh.uv_layers.remove(layer)
    mesh.uv_layers["AtlasUV"].name = "UVMap"

# ---- export each model alone ------------------------------------------------------------------------------------------
report = []
for name, objs in groups:
    files = []
    for fmt in FORMATS:
        path = os.path.join(OUT, f"{name}.{fmt}")
        export(path, objs)
        files.append(path)
    report.append({"name": name, "triangles": sum(tri_count(o) for o in objs), "files": files})
manifest = {"atlas": atlas_path, "atlas_size": SIZE, "models": report, "materials": 1, "textures": 1}
with open(os.path.join(OUT, "atlas_manifest.json"), "w", encoding="utf-8") as handle:
    json.dump(manifest, handle, indent=2)
result(manifest)
