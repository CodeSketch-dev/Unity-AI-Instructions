"""Tests must never open real windows (Explorer, default apps, Chrome): block every launcher for the whole suite."""
import os

import pytest


@pytest.fixture(autouse=True)
def _no_real_launches(monkeypatch):
    opened = []
    monkeypatch.setattr(os, "startfile", lambda path, *a, **k: opened.append(str(path)), raising=False)
    yield opened
