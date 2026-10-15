"""Validate a compact RobloxShaderKit mesh/material bake report."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


REQUIRED_CHANNELS = ("vertex_color", "uv0", "uv1", "uv2")
KNOWN_FLAGS = 0b1_1111


@dataclass(frozen=True)
class Finding:
    level: str
    code: str
    message: str


def _number(value: Any, default: int = -1) -> int:
    return value if isinstance(value, int) and not isinstance(value, bool) else default


def validate(report: dict[str, Any]) -> list[Finding]:
    findings: list[Finding] = []
    vertex_count = _number(report.get("vertex_count"))
    channels = report.get("channels")
    if vertex_count < 0 or not isinstance(channels, dict):
        findings.append(Finding("ERROR", "channel-length", "vertex_count and channels are required"))
    else:
        for channel in REQUIRED_CHANNELS:
            if _number(channels.get(channel)) != vertex_count:
                findings.append(Finding("ERROR", "channel-length", f"{channel} length must equal vertex_count"))

    if str(report.get("color_space", "")).lower() == "linear" and report.get("colors_linear") is not True:
        findings.append(Finding("ERROR", "color-space", "Linear projects require linear vertex colors"))

    surfaces = report.get("surfaces", [])
    if not isinstance(surfaces, list):
        findings.append(Finding("ERROR", "surface-list", "surfaces must be a list"))
    else:
        for index, surface in enumerate(surfaces):
            if not isinstance(surface, dict):
                findings.append(Finding("ERROR", "surface-flags", f"surface {index} must be an object"))
                continue
            flags = _number(surface.get("flags"))
            slot = _number(surface.get("slot"))
            if flags < 0 or flags & ~KNOWN_FLAGS or (flags & 0b110 and not flags & 0b001):
                findings.append(Finding("ERROR", "surface-flags", f"surface {index} has invalid flags"))
            if slot < 0 or slot > 4:
                findings.append(Finding("ERROR", "surface-slot", f"surface {index} slot must be 0..4"))
            if flags & 0b100 and _number(surface.get("checker_tiling"), 0) < 1:
                findings.append(Finding("ERROR", "surface-flags", f"surface {index} checker tiling must be positive"))

    materials = report.get("materials")
    families = report.get("families")
    if not isinstance(materials, dict) or not isinstance(families, list):
        findings.append(Finding("ERROR", "material-report", "materials and families are required"))
    else:
        material_count = _number(materials.get("count"))
        family_count = sum(_number(family.get("count")) for family in families if isinstance(family, dict))
        if material_count < 1 or family_count != material_count:
            findings.append(Finding("ERROR", "material-count", "family counts must equal materials.count"))
        if materials.get("shared") is True and material_count != 1:
            findings.append(Finding("ERROR", "material-count", "shared material reports must contain one material"))
        if _number(materials.get("static_object_variants"), 0) > 0:
            findings.append(Finding("ERROR", "static-material-variants", "static objects must not use per-object material variants"))
        if len(families) > 1 or material_count > 1:
            missing = [family.get("name", "unnamed") for family in families if not isinstance(family, dict) or not str(family.get("justification", "")).strip()]
            if missing:
                findings.append(Finding("ERROR", "unjustified-material-families", f"material separation needs a reason: {', '.join(map(str, missing))}"))
            else:
                findings.append(Finding("WARN", "material-families", "material families are allowed only with documented constraints"))

    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path)
    args = parser.parse_args(argv)
    report = json.loads(args.report.read_text(encoding="utf-8"))
    findings = validate(report)
    for finding in findings:
        print(f"{finding.level} {finding.code}: {finding.message}")
    return 1 if any(finding.level == "ERROR" for finding in findings) else 0


if __name__ == "__main__":
    raise SystemExit(main())
