"""ML model training and reload Celery tasks."""
from __future__ import annotations

from typing import Any

import structlog

from app.workers.celery_app import celery_app

logger = structlog.get_logger(__name__)


@celery_app.task(name="app.workers.ml_tasks.retrain_model")
def retrain_model(exam_type: str = "all") -> dict:
    """Trigger model retraining. Returns job summary."""
    logger.info("ml_retrain_started", exam_type=exam_type)
    # Training script runs as a subprocess to keep Celery worker clean
    import subprocess
    import sys

    result = subprocess.run(
        [sys.executable, "scripts/run_training.py", "--exam-type", exam_type],
        capture_output=True,
        text=True,
        timeout=3600,
    )
    if result.returncode != 0:
        logger.error("ml_retrain_failed", stderr=result.stderr[:500])
        return {"status": "failed", "error": result.stderr[:500]}

    logger.info("ml_retrain_completed", exam_type=exam_type)
    return {"status": "completed", "output": result.stdout[:500]}
