"""Simulate an upgrade chain and print a pacing table.

Model: the player owns `level` purchases. Income/s = base_income + income_step * level.
Next cost = base_cost * cost_growth ** level. The player waits until they can afford it.
Prints per-level cost, income, wait and cumulative time, and flags waits above the target.
"""
import argparse


def fmt_time(seconds):
    if seconds < 90:
        return f"{seconds:.0f}s"
    if seconds < 5400:
        return f"{seconds / 60:.1f}m"
    return f"{seconds / 3600:.1f}h"


def fmt_num(value):
    for suffix, scale in (("Qa", 1e15), ("T", 1e12), ("B", 1e9), ("M", 1e6), ("K", 1e3)):
        if value >= scale:
            return f"{value / scale:.2f}{suffix}"
    return f"{value:.1f}"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-cost", type=float, default=10)
    parser.add_argument("--cost-growth", type=float, default=1.15)
    parser.add_argument("--base-income", type=float, default=1)
    parser.add_argument("--income-step", type=float, default=0.3,
                        help="income/s added per level (linear); use --income-growth for exponential")
    parser.add_argument("--income-growth", type=float, default=None,
                        help="if set, income = base_income * growth ** level")
    parser.add_argument("--levels", type=int, default=40)
    parser.add_argument("--target-wait", type=float, default=120, help="seconds; waits above are flagged")
    args = parser.parse_args()

    total = 0.0
    print("| lvl | cost | income/s | wait | total | flag |")
    print("|---|---|---|---|---|---|")
    for level in range(args.levels):
        if args.income_growth is not None:
            income = args.base_income * args.income_growth ** level
        else:
            income = args.base_income + args.income_step * level
        cost = args.base_cost * args.cost_growth ** level
        wait = cost / income
        total += wait
        flag = "SLOW" if wait > args.target_wait else ""
        print(f"| {level + 1} | {fmt_num(cost)} | {fmt_num(income)} | {fmt_time(wait)} | {fmt_time(total)} | {flag} |")


if __name__ == "__main__":
    main()
