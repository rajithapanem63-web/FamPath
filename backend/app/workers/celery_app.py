"""
Celery application — with graceful fallback when Celery is not installed.
In local dev without Redis, tasks run synchronously in a thread pool.
"""
from __future__ import annotations

try:
    from celery import Celery  # type: ignore[import-untyped]
    from app.core.config import get_settings

    settings = get_settings()

    celery_app = Celery(
        "fampath",
        broker=str(settings.REDIS_URL),
        backend=str(settings.REDIS_URL),
        include=[
            "app.workers.email_tasks",
            "app.workers.import_tasks",
            "app.workers.report_tasks",
            "app.workers.ml_tasks",
            "app.workers.embed_tasks",
            "app.workers.reminder_tasks",
        ],
    )

    celery_app.conf.update(
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        timezone="Asia/Kolkata",
        enable_utc=True,
        task_track_started=True,
        task_acks_late=True,
        worker_prefetch_multiplier=1,
        beat_schedule={
            "daily-deadline-reminders": {
                "task": "app.workers.reminder_tasks.send_deadline_reminders",
                "schedule": 86400,
            },
        },
    )
    CELERY_AVAILABLE = True

except ImportError:
    import structlog
    import threading
    import uuid as _uuid
    from concurrent.futures import ThreadPoolExecutor

    _logger = structlog.get_logger(__name__)
    _executor = ThreadPoolExecutor(max_workers=2)
    CELERY_AVAILABLE = False

    class _FakeTask:
        """Synchronous task stub that runs in a background thread."""

        def __init__(self, fn: object) -> None:
            self._fn = fn
            self.__name__ = getattr(fn, "__name__", "task")

        def delay(self, *args: object, **kwargs: object) -> None:
            """Run the task in a background thread (fire-and-forget)."""
            _logger.info("celery_stub_running_task", task=self.__name__)
            _executor.submit(self._fn, *args, **kwargs)  # type: ignore[operator]

        def __call__(self, *args: object, **kwargs: object) -> object:
            return self._fn(*args, **kwargs)  # type: ignore[operator]

    class _FakeCelery:
        def task(self, *args: object, **kwargs: object):  # type: ignore[return]
            def decorator(fn: object) -> _FakeTask:
                return _FakeTask(fn)
            if args and callable(args[0]):
                return _FakeTask(args[0])
            return decorator

    celery_app = _FakeCelery()  # type: ignore[assignment]
    _logger.warning("celery_not_installed_using_thread_fallback")
