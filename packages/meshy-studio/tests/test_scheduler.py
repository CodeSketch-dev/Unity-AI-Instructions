from app.core.models import Account
from app.core.scheduler import SchedulePolicy, Scheduler


def account(account_id: int, priority: int, busy: int = 0, valid: bool = True):
    return Account(account_id, f"u{account_id}@e.com", None, priority, "", "Ready", valid, True, busy)


def test_priority_scheduler_selects_lowest_eligible_priority():
    selected = Scheduler().select([account(1, 2), account(2, 1), account(3, 0, valid=False)], SchedulePolicy.PRIORITY)
    assert selected.account.id == 2
    assert "priority" in selected.reason.lower()


def test_least_busy_and_manual_selection():
    scheduler = Scheduler()
    accounts = [account(1, 1, 3), account(2, 2, 0)]
    assert scheduler.select(accounts, SchedulePolicy.LEAST_BUSY).account.id == 2
    assert scheduler.select(accounts, SchedulePolicy.MANUAL, manual_account_id=1).account.id == 1


def test_scheduler_refuses_ineligible_accounts():
    try:
        Scheduler().select([account(1, 1, valid=False)], SchedulePolicy.PRIORITY)
    except LookupError as error:
        assert "eligible" in str(error).lower()
    else:
        raise AssertionError("ineligible account selected")

