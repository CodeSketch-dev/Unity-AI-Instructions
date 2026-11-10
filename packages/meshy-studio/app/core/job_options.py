from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from enum import StrEnum


class GenMode(StrEnum):
    TOPOLOGY = "topology"    # Meshy 7 + Smart Topology with a chosen polygon count, then texture, then export (no remesh)
    AUTOMATIC = "automatic"  # Meshy decides the mesh (very dense), then texture, remesh 10K, export


class RigType(StrEnum):
    HUMANOID = "humanoid"
    QUADRUPED = "quadruped"
    AUTO = "auto"            # Meshy "Smart rigging" picks the skeleton


MIN_POLYCOUNT = 100
MAX_POLYCOUNT = 30_000
DEFAULT_POLYCOUNT = 3_000
MODEL_NAME = "Meshy 7"  # always; never switch to another model


@dataclass(slots=True)
class JobOptions:
    mode: GenMode = GenMode.TOPOLOGY
    polycount: int = DEFAULT_POLYCOUNT
    rig: bool = False
    rig_type: RigType = RigType.AUTO

    def normalized(self) -> "JobOptions":
        return JobOptions(GenMode(self.mode), max(MIN_POLYCOUNT, min(MAX_POLYCOUNT, int(self.polycount))),
                          bool(self.rig), RigType(self.rig_type))

    def to_json(self) -> str:
        return json.dumps(asdict(self.normalized()))

    @staticmethod
    def from_json(text: str | None) -> "JobOptions":
        """Old rows (no options) behave like the previous app: Automatic, no rig."""
        if not text:
            return JobOptions(mode=GenMode.AUTOMATIC)
        try:
            data = json.loads(text)
            return JobOptions(GenMode(data.get("mode", "automatic")), int(data.get("polycount", DEFAULT_POLYCOUNT)),
                              bool(data.get("rig", False)), RigType(data.get("rig_type", "auto"))).normalized()
        except (ValueError, TypeError):
            return JobOptions(mode=GenMode.AUTOMATIC)

    @property
    def remesh(self) -> bool:
        return self.mode == GenMode.AUTOMATIC

    @property
    def required_credits(self) -> int:
        """Generate 20 + Texture 10; rigging costs extra (amount unverified: only a pre-check estimate)."""
        return 30 + (5 if self.rig else 0)
