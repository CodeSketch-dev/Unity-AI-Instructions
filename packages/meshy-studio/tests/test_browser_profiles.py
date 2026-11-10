from pathlib import Path
import threading

from app.automation.browser_manager import BrowserManager


def test_profiles_are_isolated_and_stay_inside_profile_root(tmp_path: Path):
    manager = BrowserManager(tmp_path / "profiles")
    first = manager.profile_path(1)
    second = manager.profile_path(2)
    assert first != second
    assert first.parent == second.parent == (tmp_path / "profiles").resolve()
    assert first.name == "account_000001"


def test_thread_driver_is_stopped_and_removed(tmp_path: Path):
    manager = BrowserManager(tmp_path / "profiles")

    class Driver:
        stopped = False
        def stop(self): self.stopped = True

    driver = Driver()
    manager._playwrights[threading.get_ident()] = driver
    assert manager.close_thread_driver() is True
    assert driver.stopped is True and manager._playwrights == {}

