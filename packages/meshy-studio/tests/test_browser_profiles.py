from pathlib import Path

from app.automation.browser_manager import BrowserManager


def test_profiles_are_isolated_and_stay_inside_profile_root(tmp_path: Path):
    manager = BrowserManager(tmp_path / "profiles")
    first = manager.profile_path(1)
    second = manager.profile_path(2)
    assert first != second
    assert first.parent == second.parent == (tmp_path / "profiles").resolve()
    assert first.name == "account_000001"

