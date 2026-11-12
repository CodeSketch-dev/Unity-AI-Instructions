"""Compare ordered mesh/hierarchy JSON dumps; this tool does not export or import assets."""
import argparse
import copy
import json
import math
from pathlib import Path


def compare(source, target, epsilon=1e-6):
    if not math.isfinite(epsilon) or epsilon < 0:
        raise ValueError("Tolerance must be finite and nonnegative")
    for dump in (source, target):
        if not {"nodes", "meshes"} <= dump.keys():
            raise ValueError("Dump requires nodes and meshes")
        if not dump["meshes"] or not any(mesh.get("positions") for mesh in dump["meshes"]):
            raise ValueError("Empty geometry is not a verified export")
        for mesh in dump["meshes"]:
            if not {"name", "positions", "normals", "uvs", "colors", "submeshes", "bindposes", "boneWeights"} <= mesh.keys():
                raise ValueError("Mesh dump is missing required attributes")
    maximum = 0.0

    def walk(a, b, path):
        nonlocal maximum
        if isinstance(a, (int, float)) and not isinstance(a, bool) and isinstance(b, (int, float)) and not isinstance(b, bool):
            if not math.isfinite(a) or not math.isfinite(b):
                raise ValueError(path + ": non-finite value")
            difference = abs(a - b)
            exact = isinstance(a, int) or any("/" + name + "/" in path for name in ("normals", "uvs", "colors", "submeshes", "boneWeights"))
            if difference > (0 if exact else epsilon):
                raise ValueError(path + ": difference " + str(difference))
            maximum = max(maximum, difference)
        elif type(a) is not type(b):
            raise ValueError(path + ": type mismatch")
        elif isinstance(a, dict):
            if a.keys() != b.keys():
                raise ValueError(path + ": field mismatch")
            for key in a:
                walk(a[key], b[key], path + "/" + key)
        elif isinstance(a, list):
            if len(a) != len(b):
                raise ValueError(path + ": count mismatch")
            for index, (left, right) in enumerate(zip(a, b)):
                walk(left, right, path + "/" + str(index))
        elif a != b:
            raise ValueError(path + ": value mismatch")
    walk(source, target, "")
    return maximum


def self_test():
    source = {"nodes": [], "meshes": [{"name": "mesh", "positions": [[0.5, 0.0, 0.5]],
        "normals": [[0.0, 0.0, 1.0]], "uvs": [[0.0, 1.0]], "colors": [],
        "submeshes": [[0, 1, 2]], "bindposes": [], "boneWeights": []}]}
    target = copy.deepcopy(source)
    target["meshes"][0]["positions"][0][0] += 2.98e-8
    assert compare(source, target) < 1e-6
    for field, value in (("positions", [[-0.5, 0.0, -0.5]]), ("submeshes", [[0, 2, 1]]),
                         ("normals", [[0.0, 0.0, 1.00000001]]), ("uvs", [[0.0, .99]])):
        target = copy.deepcopy(source)
        target["meshes"][0][field] = value
        try:
            compare(source, target)
        except ValueError:
            continue
        raise AssertionError("Mismatch accepted: " + field)
    print("PASS: tolerated position error; rejected axis mirror, winding, normal and UV changes")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", nargs="?", type=Path)
    parser.add_argument("target", nargs="?", type=Path)
    parser.add_argument("--epsilon", type=float, default=1e-6)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
    elif args.source and args.target:
        error = compare(json.loads(args.source.read_text()), json.loads(args.target.read_text()), args.epsilon)
        print("PASS maximum numeric error=" + str(error))
    else:
        parser.error("Provide source and target dumps, or --self-test")
