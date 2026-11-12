"""Validate an auto-balance-game JSON plan without Unity or third-party packages."""
import json
import sys


REQUIRED_DOMAINS = ("progression", "currencies", "economy", "combat", "content", "retention", "rebirth")
REQUIRED_VALUE_GROUPS = ("progression", "currency", "combat", "content")


def validate(plan):
    errors = []
    if plan.get("schema") != "auto-balance-game/v1":
        errors.append("schema must be auto-balance-game/v1")
    target = plan.get("target") or {}
    total = float(target.get("total_play_minutes", 0) or 0)
    if total <= 0:
        errors.append("target.total_play_minutes must be positive")
    milestones = plan.get("milestones") or []
    values = plan.get("generated_values") or []
    if len(milestones) != len(values):
        errors.append("milestones and generated_values must have equal length")
    paths = [row.get("path") for row in milestones]
    if any(not path for path in paths) or len(paths) != len(set(paths)):
        errors.append("milestone paths must be present and unique")
    minutes = sum(float(row.get("target_minutes", 0) or 0) for row in milestones)
    if milestones and abs(minutes - total) > 0.01:
        errors.append("milestone time does not equal target total")
    for row in values:
        missing = [key for key in REQUIRED_VALUE_GROUPS if not isinstance(row.get(key), dict)]
        if missing:
            errors.append("%s missing generated groups: %s" % (row.get("path"), ", ".join(missing)))
    stats = plan.get("stats") or {}
    for domain in REQUIRED_DOMAINS:
        if domain not in stats:
            errors.append("stats missing domain: %s" % domain)
    if not isinstance(plan.get("discovered_stats"), list):
        errors.append("discovered_stats must be a list")
    return errors


def main(argv=None):
    if len(sys.argv if argv is None else argv) != 2:
        print("usage: validate_balance_plan.py PLAN.json", file=sys.stderr)
        return 2
    try:
        with open((argv or sys.argv)[1], encoding="utf-8") as handle:
            plan = json.load(handle)
    except (OSError, ValueError) as exc:
        print("INVALID: %s" % exc)
        return 1
    errors = validate(plan)
    if errors:
        print("INVALID")
        for error in errors:
            print("- %s" % error)
        return 1
    print("VALID: %s milestones, %s discovered stats" % (len(plan.get("milestones", [])), len(plan.get("discovered_stats", []))))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
