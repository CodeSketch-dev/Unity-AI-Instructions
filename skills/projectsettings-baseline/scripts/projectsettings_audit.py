"""Read-only audit of Unity ProjectSettings and URP assets against the mobile baseline.

Usage: py -I projectsettings_audit.py <unity-project>
Exit 1 if any FAIL. WARN and INFO never fail. Text-serialized YAML only.
"""
import glob
import os
import re
import sys
from collections import namedtuple

Finding = namedtuple("Finding", "level code message")
LAYERS = 32
TOTAL_PAIRS = LAYERS * (LAYERS + 1) // 2  # triangular layout, INFERRED


def read(project, rel):
    path = os.path.join(project, rel)
    if not os.path.isfile(path):
        return None
    with open(path, encoding="utf-8", errors="replace") as f:
        return f.read()


def values(text, key):
    return re.findall(r"^\s*%s:\s*(\S+)" % re.escape(key), text or "", re.M)


def num(text, key):
    vals = values(text, key)
    try:
        return float(vals[0]) if vals else None
    except ValueError:
        return None


def matrix_enabled_pairs(hexstr):
    """Count set bits in the triangular layer matrix. Returns (enabled, total). Layout INFERRED."""
    hexstr = hexstr.strip()
    enabled = 0
    for i in range(LAYERS):
        chunk = hexstr[i * 8:(i + 1) * 8]
        if len(chunk) < 8:
            break
        mask = int.from_bytes(bytes.fromhex(chunk), "little")
        valid = (1 << (LAYERS - i)) - 1
        enabled += bin(mask & valid).count("1")
    return enabled, TOTAL_PAIRS


def audit(project):
    out = []
    dyn = read(project, "ProjectSettings/DynamicsManager.asset")
    if dyn is None:
        out.append(Finding("INFO", "no-dynamics", "DynamicsManager.asset not found"))
    else:
        if num(dyn, "m_AutoSyncTransforms") == 1:
            out.append(Finding("FAIL", "auto-sync-transforms", "Physics.autoSyncTransforms is on; disable it"))
        if num(dyn, "m_ReuseCollisionCallbacks") == 0:
            out.append(Finding("FAIL", "reuse-collision-callbacks", "reuseCollisionCallbacks is off; enable it"))
        it = num(dyn, "m_DefaultSolverIterations")
        if it is not None and it > 6:
            out.append(Finding("WARN", "solver-iterations", "solver iterations %d > default 6" % it))
        m = values(dyn, "m_LayerCollisionMatrix")
        if m:
            enabled, total = matrix_enabled_pairs(m[0])
            level = "WARN" if enabled > 0.8 * total else "INFO"
            out.append(Finding(level, "layer-matrix", "%d of %d layer pairs enabled (layout INFERRED); disable pairs that never touch" % (enabled, total)))
    tm = read(project, "ProjectSettings/TimeManager.asset")
    if tm is not None:
        ts = num(tm, "m_TimeScale")
        if ts is not None and ts != 1:
            out.append(Finding("FAIL", "time-scale", "Time.timeScale is %g (QA leftover?)" % ts))
        mdt = num(tm, "Maximum Allowed Timestep")
        if mdt is not None and mdt > 0.15:
            out.append(Finding("WARN", "max-delta-time", "maximumDeltaTime %g > 0.1 (death-spiral risk)" % mdt))
    q = read(project, "ProjectSettings/QualitySettings.asset")
    if q is not None:
        if any(v != "0" for v in values(q, "vSyncCount")):
            out.append(Finding("WARN", "vsync", "a quality level has vSyncCount != 0; set 0 and cap frame rate in code"))
        if any(v != "0" for v in values(q, "globalTextureMipmapLimit")):
            out.append(Finding("WARN", "texture-mip-limit", "globalTextureMipmapLimit > 0 halves textures globally; make sure it is deliberate"))
    for path in sorted(glob.glob(os.path.join(project, "Assets", "**", "*.asset"), recursive=True)):
        if "RPAsset" not in os.path.basename(path):
            continue
        with open(path, encoding="utf-8", errors="replace") as f:
            t = f.read()
        if "m_UseSRPBatcher" not in t:
            continue
        name = os.path.basename(path)
        if num(t, "m_UseSRPBatcher") == 0:
            out.append(Finding("FAIL", "urp-srp-batcher", "%s: SRP Batcher off" % name))
        if num(t, "m_SupportsHDR") == 1:
            out.append(Finding("WARN", "urp-hdr", "%s: HDR on (baseline: off unless required)" % name))
        if num(t, "m_SoftShadowsSupported") == 1:
            out.append(Finding("WARN", "urp-soft-shadows", "%s: soft shadows supported" % name))
        res = num(t, "m_MainLightShadowmapResolution")
        if res is not None and res > 1024:
            out.append(Finding("WARN", "urp-shadowmap", "%s: shadow map %d > 1024" % (name, res)))
        dist = num(t, "m_ShadowDistance")
        if dist is not None and dist > 60:
            out.append(Finding("WARN", "urp-shadow-distance", "%s: shadow distance %g > 60" % (name, dist)))
    return out


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or not os.path.isdir(argv[0]):
        print("usage: projectsettings_audit.py <unity-project>", file=sys.stderr)
        return 2
    findings = audit(argv[0])
    for f in findings:
        print("%s %s: %s" % (f.level, f.code, f.message))
    fails = sum(1 for f in findings if f.level == "FAIL")
    print("%d fail, %d warn" % (fails, sum(1 for f in findings if f.level == "WARN")))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
