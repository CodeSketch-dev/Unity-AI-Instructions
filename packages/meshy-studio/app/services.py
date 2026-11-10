from __future__ import annotations

from typing import Any, Callable

from app.automation.google_login import GoogleOAuthLogin
from app.automation.meshy_worker import MeshyWebWorker
from app.core.pipeline import PipelineService
from app.mail.manager import MailboxManager
from app.security.credentials import CredentialStore, KeyringCredentialStore
from app.settings import Settings


def make_worker_factory(browser_manager: Any, settings: Settings,
                        credentials: CredentialStore | None = None) -> Callable[[], MeshyWebWorker]:
    """One new worker per pipeline thread (each thread owns its Playwright driver and browser windows)."""
    store = credentials or KeyringCredentialStore()

    def factory() -> MeshyWebWorker:
        return MeshyWebWorker(browser_manager, google_login=GoogleOAuthLogin(store), export_dir=lambda: settings.export_dir)
    return factory


def build_pipeline(database: Any, browser_manager: Any, settings: Settings,
                   credentials: CredentialStore | None = None) -> PipelineService:
    factory = make_worker_factory(browser_manager, settings, credentials)
    return PipelineService(database, factory(), concurrency=settings.concurrency, worker_factory=factory,
                           max_retries=settings.max_retries, job_timeout_seconds=settings.job_timeout_minutes * 60)


def build_mail_manager(database: Any, settings: Settings, credentials: CredentialStore | None = None) -> MailboxManager:
    return MailboxManager(database, credentials or KeyringCredentialStore(),
                          api_config=lambda: settings.get("purelymail_api"))
