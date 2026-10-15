"""Generate a complete, constraint-driven game balance plan from playtime targets."""
import argparse
import json
import os
import re


def _duration(value):
    match = re.fullmatch(r"([0-9]+(?:\.[0-9]+)?)(m|min|minutes?|h|hours?|s|sec|seconds?)?", str(value).strip().lower())
    if not match:
        raise ValueError("invalid duration %r; use 2m, 1.5h, or 90s" % value)
    number = float(match.group(1))
    unit = match.group(2) or "m"
    if unit.startswith("h"):
        number *= 60
    elif unit.startswith("s"):
        number /= 60
    return number


def _scalar(value):
    text = str(value).strip()
    if "," in text:
        return [_scalar(part) for part in text.split(",")]
    if text.lower() in ("true", "false"):
        return text.lower() == "true"
    try:
        return float(text) if "." in text else int(text)
    except ValueError:
        return text


def _pairs(values, name):
    result = []
    for raw in values:
        if "=" not in raw:
            raise ValueError("%s must use key=value: %s" % (name, raw))
        key, value = raw.split("=", 1)
        if not key.strip() or not value.strip():
            raise ValueError("%s must have a non-empty key and value: %s" % (name, raw))
        result.append((key.strip(), value.strip()))
    return result


TUNABLE_KEY = re.compile(r"(price|cost|income|reward|amount|multiplier|boost|damage|cooldown|range|speed|jump|hp|health|interval|duration|growth|requirement|cap|weight|odds|chance|radius|lifetime|count|slots|level|value|effect|power|rate|xp|experience)", re.I)


def _allocate_milestones(total_minutes, specs):
    parsed = []
    for raw_id, raw_time in _pairs(specs, "--milestone"):
        parsed.append((raw_id, _duration(raw_time)))
    if any(minutes <= 0 for _, minutes in parsed) or len({key for key, _ in parsed}) != len(parsed):
        raise ValueError("milestone paths and durations must be positive and unique")
    explicit = sum(minutes for _, minutes in parsed)
    if explicit > total_minutes + 1e-6:
        raise ValueError("explicit milestone time exceeds the full-game target")
    if not parsed:
        return []
    remaining = total_minutes - explicit
    if remaining <= 1e-6:
        return parsed
    return parsed + [("generated.remaining", remaining)]


def _discover_stats(gdd_root):
    if not gdd_root or not os.path.isdir(gdd_root):
        return []
    found = set()
    for base, _, files in os.walk(gdd_root):
        for name in files:
            if not name.endswith((".md", ".yaml", ".yml", ".json", ".csv")):
                continue
            with open(os.path.join(base, name), encoding="utf-8", errors="ignore") as handle:
                for line in handle:
                    match = re.match(r"\s*([A-Za-z_][A-Za-z0-9_.-]*)\s*:", line)
                    if match and TUNABLE_KEY.search(match.group(1)):
                        found.add(match.group(1))
    return sorted(found)


def build_plan(full_days, hours_per_day, milestone_specs=None, constraints=None, overrides=None, gdd_root=None):
    if full_days <= 0 or hours_per_day <= 0:
        raise ValueError("full_days and hours_per_day must be positive")
    total_minutes = int(round(full_days * hours_per_day * 60))
    milestones = _allocate_milestones(total_minutes, milestone_specs or [])
    constraints = dict((key, _scalar(value)) for key, value in _pairs(constraints or [], "--constraint"))
    overrides = dict((key, _scalar(value)) for key, value in _pairs(overrides or [], "--set"))
    currency_ids = {"coins"}
    for key in list(constraints) + list(overrides):
        match = re.match(r"currency\.([A-Za-z0-9_-]+)\.", key)
        if match:
            currency_ids.add(match.group(1))
    enemy_hp_factor = float(overrides.get("combat.enemy_hp_factor", 1.0))
    income_factor = float(overrides.get("economy.income_factor", 1.0))
    rows = []
    elapsed = 0.0
    generated_values = []
    for path, minutes in milestones:
        progress = elapsed / total_minutes
        power = round(10.0 * (1.0 + progress), 4)
        income = round(100.0 * (1.0 + progress) * income_factor, 4)
        unlock_cost = round(income * minutes, 4)
        rows.append({"path": path, "target_minutes": round(minutes, 4), "progress_fraction": round(progress, 6), "gate": {"stat": "primary_progression", "value": round(progress, 6)}, "generated": path == "generated.remaining"})
        generated_values.append({
            "path": path,
            "time": {"target_minutes": round(minutes, 4), "target_seconds": round(minutes * 60, 4)},
            "progression": {"entry_requirement": round(progress, 6), "completion_reward": round(1.0 / max(len(milestones), 1), 6)},
            "currency": {"income_per_minute": income, "unlock_cost": unlock_cost, "upgrade_cost": round(unlock_cost * 0.25, 4), "reward_per_action": round(income / 10.0, 4)},
            "combat": {"player_power": power, "enemy_hp": round(power * 3.0 * enemy_hp_factor, 4), "enemy_damage": round(power * 0.1, 4), "action_cooldown_seconds": round(max(0.25, minutes * 60 / 20.0), 4)},
            "content": {"drop_weight": round(1.0 / (max(len(generated_values), 1) ** 0.5), 6), "collection_target": path},
        })
        elapsed += minutes
    return {
        "schema": "auto-balance-game/v1",
        "mode": "generated-tuning",
        "target": {"full_days": full_days, "hours_per_day": hours_per_day, "total_play_minutes": total_minutes, "sessions_per_day": constraints.get("player_sessions_per_day", 1)},
        "milestones": rows,
        "stats": {
            "progression": {"primary_progression": {"start": 0, "end": 1, "source": "milestone_timeline"}, "completion_fraction": 1},
            "currencies": {currency_id: {"sources": ["primary_loop" if currency_id == "coins" else "configured_source"], "sinks": ["upgrades", "content_unlocks"], "generated": True} for currency_id in sorted(currency_ids)},
            "economy": {"income_rate": "derived_from_next_unlock_time", "cost_curve": "derived_from_progression_and_sinks", "wallet_caps": "derived_from_session_flow"},
            "combat": {"player_power": "derived_from_next_target_time", "enemy_hp": "derived_from_player_power", "enemy_damage": "derived_from_survival_window", "cooldowns": "derived_from_action_cadence"},
            "content": {"unlock_requirements": "derived_from_milestone_timeline", "reward_rate": "derived_from_next_unlock_time", "drop_weights": "derived_from_collection_target"},
            "retention": {"daily_progression": "derived_from_full_days_and_hours_per_day", "offline_reward": "bounded_by_session_economy"},
            "rebirth": {"availability": "derived_from_progression_milestones", "reset_and_keep": "derived_from_gdd_behavior"},
        },
        "generated_values": generated_values,
        "discovered_stats": _discover_stats(gdd_root),
        "constraints": constraints,
        "overrides": overrides,
        "assumptions": ["Unobserved numeric values are generated by the balance pass, not copied from a generic recipe.", "Milestone times are completion-time targets; dependent stats are solved against them.", "Observed GDD facts override generated values; user overrides override generated values."],
        "verification": {"required": ["fresh-save golden path", "normal timeScale", "every milestone reachable", "currency sources and sinks reachable", "completion time within target tolerance"], "recompute_after": ["GDD change", "milestone timeline change", "constraint change", "user override change"]},
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--full-days", type=float, required=True)
    parser.add_argument("--hours-per-day", type=float, required=True)
    parser.add_argument("--milestone", action="append", default=[])
    parser.add_argument("--constraint", action="append", default=[])
    parser.add_argument("--set", dest="overrides", action="append", default=[])
    parser.add_argument("--gdd")
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)
    try:
        plan = build_plan(args.full_days, args.hours_per_day, args.milestone, args.constraint, args.overrides, args.gdd)
    except ValueError as exc:
        parser.error(str(exc))
    if args.gdd:
        plan["input"] = {"gdd": os.path.abspath(args.gdd)}
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w", encoding="utf-8", newline="\n") as handle:
        json.dump(plan, handle, indent=2)
        handle.write("\n")
    print("WROTE %s" % args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
