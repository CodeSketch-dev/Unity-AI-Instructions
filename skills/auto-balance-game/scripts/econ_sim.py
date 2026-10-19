"""Simulate and bounded-tune an auto-balance-game plan without Unity dependencies."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def _positive(value: Any, fallback: float = 1.0) -> float:
    try:
        value = float(value)
    except (TypeError, ValueError):
        return fallback
    return value if value > 0 else fallback


def simulate(plan: dict[str, Any], knobs: dict[str, Any] | None = None) -> dict[str, Any]:
    """Estimate completion time from generated economy/combat values.

    This is a cheap pre-Unity model. It must not replace the fresh-save PlayMode
    verification required by the balance skill.
    """
    knobs = knobs or {}
    income_factor = _positive(knobs.get("income_factor"), 1.0)
    enemy_hp_factor = _positive(knobs.get("enemy_hp_factor"), 1.0)
    cooldown_factor = _positive(knobs.get("cooldown_factor"), 1.0)
    target = _positive((plan.get("target") or {}).get("total_play_minutes"), 0.0)
    rows = []
    for generated in plan.get("generated_values") or []:
        currency = generated.get("currency") or {}
        combat = generated.get("combat") or {}
        income = _positive(currency.get("income_per_minute"), 0.0) * income_factor
        unlock = _positive(currency.get("unlock_cost"), 0.0)
        economy_minutes = unlock / income if income else float("inf")
        power = _positive(combat.get("player_power"), 0.0)
        enemy_hp = _positive(combat.get("enemy_hp"), 0.0) * enemy_hp_factor
        cooldown = _positive(combat.get("action_cooldown_seconds"), 0.0) * cooldown_factor
        combat_minutes = (enemy_hp / power * cooldown / 60.0) if power else float("inf")
        rows.append({
            "path": generated.get("path"),
            "economy_minutes": round(economy_minutes, 6),
            "combat_minutes": round(combat_minutes, 6),
            "estimated_minutes": round(max(economy_minutes, combat_minutes), 6),
        })
    total = sum(row["estimated_minutes"] for row in rows)
    tolerance = _positive((plan.get("verification") or {}).get("completion_tolerance"), 0.05)
    error = (total - target) / target if target else None
    return {
        "simulated": bool(rows and target),
        "milestones": len(rows),
        "total_minutes": round(total, 6) if rows else 0.0,
        "target_minutes": round(target, 6),
        "relative_error": round(error, 6) if error is not None else None,
        "within_tolerance": bool(error is not None and abs(error) <= tolerance),
        "knobs": {"income_factor": income_factor, "enemy_hp_factor": enemy_hp_factor, "cooldown_factor": cooldown_factor},
        "rows": rows,
    }


def tune(plan: dict[str, Any], initial: dict[str, Any] | None = None, tolerance: float = 0.05, max_iterations: int = 12) -> dict[str, Any]:
    """Tune the cheapest global economy knob with a hard iteration cap."""
    if max_iterations < 1:
        raise ValueError("max_iterations must be positive")
    if not plan.get("generated_values"):
        return {"status": "inconclusive", "reason": "milestones are required for pre-Unity simulation", "iterations": 0}
    knobs = {"income_factor": _positive((initial or {}).get("income_factor"), 1.0)}
    history = []
    for iteration in range(1, max_iterations + 1):
        metrics = simulate(plan, knobs)
        history.append(metrics)
        if metrics["relative_error"] is not None and abs(metrics["relative_error"]) <= tolerance:
            return {"status": "converged", "iterations": iteration, "knobs": knobs, "metrics": metrics, "history": history}
        if not metrics["total_minutes"] or not metrics["target_minutes"]:
            break
        # Estimated time is inversely proportional to income in this cheap model.
        knobs["income_factor"] = min(4.0, max(0.25, knobs["income_factor"] * metrics["total_minutes"] / metrics["target_minutes"]))
    return {"status": "not-converged", "iterations": len(history), "knobs": knobs, "metrics": history[-1], "history": history}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("plan", type=Path)
    parser.add_argument("--mode", choices=("simulate", "tune"), default="simulate")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--tolerance", type=float, default=0.05)
    parser.add_argument("--max-iterations", type=int, default=12)
    args = parser.parse_args(argv)
    plan = json.loads(args.plan.read_text(encoding="utf-8"))
    report = simulate(plan) if args.mode == "simulate" else tune(plan, tolerance=args.tolerance, max_iterations=args.max_iterations)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print("%s: %s" % (args.mode, report.get("status", "ok")))
    return 0 if report.get("simulated", report.get("status") == "converged") else 1


if __name__ == "__main__":
    raise SystemExit(main())
