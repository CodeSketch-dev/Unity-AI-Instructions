from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from app.core.models import Account


class SchedulePolicy(StrEnum):
    MANUAL = "Manual Account Selection"
    PRIORITY = "Priority Scheduling"
    ROUND_ROBIN = "Round Robin"
    LEAST_BUSY = "Least Busy Account"


@dataclass(frozen=True, slots=True)
class Selection:
    account: Account
    reason: str


class Scheduler:
    def __init__(self):
        self._round_robin_index = 0

    def select(self, accounts: list[Account], policy: SchedulePolicy, manual_account_id: int | None = None, *, allow_unvalidated: bool = False) -> Selection:
        # A profile without a validated session is still eligible: the worker
        # can authenticate it via Playwright. Only disabled/quota accounts are
        # excluded from automatic rotation.
        eligible = [a for a in accounts if a.authorized and (allow_unvalidated or a.session_valid) and a.status.lower() not in {"busy", "quota limited", "needs verification", "login failed"}]
        if not eligible:
            raise LookupError("No eligible account has a valid session and authorization")
        if policy == SchedulePolicy.MANUAL:
            selected = next((a for a in eligible if a.id == manual_account_id), None)
            if not selected:
                raise LookupError("Selected account is not eligible")
            return Selection(selected, "Manually selected by the user")
        if policy == SchedulePolicy.PRIORITY:
            selected = min(eligible, key=lambda a: (a.priority, a.active_jobs, a.id))
            return Selection(selected, f"Lowest eligible priority ({selected.priority})")
        if policy == SchedulePolicy.LEAST_BUSY:
            selected = min(eligible, key=lambda a: (a.active_jobs, a.priority, a.id))
            return Selection(selected, f"Least busy ({selected.active_jobs} active jobs)")
        ordered = sorted(eligible, key=lambda a: (a.priority, a.id))
        selected = ordered[self._round_robin_index % len(ordered)]
        self._round_robin_index += 1
        return Selection(selected, "Next eligible account in round-robin order")

