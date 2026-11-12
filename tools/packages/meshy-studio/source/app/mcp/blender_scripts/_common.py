"""Shared helpers for the headless Blender scripts (run with: blender --background --python <script> -- <json args>)."""
import json
import sys

import bpy


def args():
    return json.loads(sys.argv[sys.argv.index("--") + 1])


def result(payload):
    print("MESHY_RESULT " + json.dumps(payload), flush=True)


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def import_model(path):
    before = set(bpy.data.objects)
    lower = path.lower()
    if lower.endswith((".glb", ".gltf")):
        bpy.ops.import_scene.gltf(filepath=path)
    elif lower.endswith(".fbx"):
        bpy.ops.import_scene.fbx(filepath=path)
    elif lower.endswith(".obj"):
        bpy.ops.wm.obj_import(filepath=path)
    else:
        raise RuntimeError("unsupported input: " + path)
    return [o for o in bpy.data.objects if o not in before]


def meshes(objects):
    return [o for o in objects if o.type == "MESH"]


def tri_count(obj):
    mesh = obj.data
    mesh.calc_loop_triangles()
    return len(mesh.loop_triangles)


def total_tris(objects):
    return sum(tri_count(o) for o in meshes(objects))


def select_only(objects):
    bpy.ops.object.select_all(action="DESELECT")
    for o in objects:
        o.select_set(True)
    if objects:
        bpy.context.view_layer.objects.active = objects[0]


def export(path, objects):
    select_only(objects)
    lower = path.lower()
    if lower.endswith(".glb"):
        bpy.ops.export_scene.gltf(filepath=path, export_format="GLB", use_selection=True)
    elif lower.endswith(".fbx"):
        bpy.ops.export_scene.fbx(filepath=path, use_selection=True, path_mode="COPY", embed_textures=True,
                                 axis_forward="-Z", axis_up="Y", apply_scale_options="FBX_SCALE_ALL", bake_space_transform=True)
    else:
        raise RuntimeError("unsupported output: " + path)
