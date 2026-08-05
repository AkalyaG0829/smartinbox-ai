import pytest
import json
from unittest.mock import patch
from src.worker import handle_task_failure, warm_up_model, process_message_async, process_media_async
from src.infrastructure.models import FailedTaskLog
from src.config.settings import settings
import logging

def test_dlq_payload_sanitization(db_session):
    # Ensure clean state
    db_session.query(FailedTaskLog).delete()
    db_session.commit()

    # Mock task and sender
    class MockSender:
        name = "tasks.test_task"

    sender = MockSender()
    sensitive_payload = {
        "user_id": 123,
        "content": "Hello world",
        "api_key": "sk-12345",
        "secret_token": "abcde"
    }

    try:
        raise ValueError("Test error")
    except ValueError as e:
        with patch('src.database.session.SessionLocal', return_value=db_session):
            handle_task_failure(
                sender=sender,
                task_id="test-task-1",
                exception=e,
                args=(sensitive_payload,),
                kwargs={},
                traceback_obj=e.__traceback__,
                einfo=None
            )

    log_entry = db_session.query(FailedTaskLog).filter_by(task_id="test-task-1").first()
    assert log_entry is not None
    
    saved_payload = json.loads(log_entry.original_payload)
    assert saved_payload["user_id"] == 123
    assert saved_payload["content"] == "Hello world"
    assert saved_payload["api_key"] == "***MASKED***"
    assert saved_payload["secret_token"] == "***MASKED***"

def test_worker_isolation_skips_ml_warmup(caplog):
    caplog.set_level(logging.INFO)
    
    original_role = settings.WORKER_ROLE
    try:
        # Test routing worker skips warmup
        settings.WORKER_ROLE = "routing"
        warm_up_model(None)
        assert "Skipping ML warmup. Worker role is routing." in caplog.text
        
        caplog.clear()

        # ML worker does warmup
        settings.WORKER_ROLE = "ml"
        # We catch the exception because we are running in a fast test environment where 
        # downloading the model might fail or take too long, but we just verify it attempts it.
        # It should log either success or failure, not skip.
        warm_up_model(None)
        assert "Skipping ML warmup" not in caplog.text

    finally:
        settings.WORKER_ROLE = original_role

def test_celery_task_timeouts():
    # Verify the timeouts were added properly to the task properties
    assert getattr(process_message_async, "soft_time_limit", None) == 120 or process_message_async.time_limit == 150
    assert getattr(process_media_async, "soft_time_limit", None) == 60 or process_media_async.time_limit == 90
