import pytest
import json
from src.infrastructure.models import FailedTaskLog

def test_task_failure_handler_persistence(db_session, monkeypatch):
    from src.worker import handle_task_failure
    import src.database.session
    
    monkeypatch.setattr(src.database.session, "SessionLocal", lambda: db_session)
    
    import types
    class DummySender:
        name = "tasks.process_message_async"
    
    sender = DummySender()
    task_id = "test_fail_123"
    exception = ValueError("Simulated permanent failure")
    args = ({"message_id": "m1", "user_id": "u1"},)
    kwargs = {}
    
    try:
        raise exception
    except ValueError as e:
        import sys
        exc_type, exc_value, traceback_obj = sys.exc_info()
    
    # Manually invoke the failure signal handler
    handle_task_failure(
        sender=sender, 
        task_id=task_id, 
        exception=exception, 
        args=args, 
        kwargs=kwargs, 
        traceback_obj=traceback_obj, 
        einfo=None
    )
    
    # Check persistence
    logs = db_session.query(FailedTaskLog).all()
    assert len(logs) == 1
    assert logs[0].task_id == task_id
    assert logs[0].task_name == "tasks.process_message_async"
    assert logs[0].is_replayed is False
    assert "Simulated permanent failure" in logs[0].exception_details
    assert json.loads(logs[0].original_payload) == {"message_id": "m1", "user_id": "u1"}

def test_dlq_api_endpoints(client, db_session, monkeypatch):
    # Setup test data
    failed_log = FailedTaskLog(
        task_id="api_fail_123",
        task_name="tasks.recalculate_personalization_stats",
        original_payload=json.dumps({"user_id": "u1", "sender_id": "s1"}),
        exception_details="Redis timeout",
        is_replayed=False
    )
    db_session.add(failed_log)
    db_session.commit()
    
    log_id = failed_log.id
    
    # Test GET /api/v1/tasks/dlq
    get_res = client.get("/api/v1/tasks/dlq")
    assert get_res.status_code == 200
    data = get_res.json()
    assert data["status"] == "success"
    assert len(data["failed_tasks"]) == 1
    assert data["failed_tasks"][0]["task_id"] == "api_fail_123"
    
    # Mock the celery task delay
    called_with = None
    class MockTask:
        @staticmethod
        def delay(**kwargs):
            nonlocal called_with
            called_with = kwargs
            
    import src.worker as worker
    monkeypatch.setattr(worker, "recalculate_personalization_stats", MockTask)
    
    # Test POST /api/v1/tasks/dlq/{log_id}/replay
    replay_res = client.post(f"/api/v1/tasks/dlq/{log_id}/replay")
    assert replay_res.status_code == 200
    assert replay_res.json()["status"] == "success"
    
    # Verify mock was called with correct payload
    assert called_with == {"user_id": "u1", "sender_id": "s1"}
    
    # Verify it was marked as replayed
    db_session.refresh(failed_log)
    assert failed_log.is_replayed is True
    
    # Test double replay prevention
    replay_res_2 = client.post(f"/api/v1/tasks/dlq/{log_id}/replay")
    assert replay_res_2.status_code == 400
    assert "already been replayed" in replay_res_2.json()["detail"]
    
def test_replay_invalid_payload(client, db_session):
    failed_log = FailedTaskLog(
        task_id="bad_payload",
        task_name="tasks.process_message_async",
        original_payload="not valid json",
        is_replayed=False
    )
    db_session.add(failed_log)
    db_session.commit()
    
    replay_res = client.post(f"/api/v1/tasks/dlq/{failed_log.id}/replay")
    assert replay_res.status_code == 400
    assert "not valid JSON" in replay_res.json()["detail"]

def test_replay_unsupported_task(client, db_session):
    failed_log = FailedTaskLog(
        task_id="unsupported",
        task_name="tasks.unknown_task",
        original_payload='{"foo": "bar"}',
        is_replayed=False
    )
    db_session.add(failed_log)
    db_session.commit()
    
    replay_res = client.post(f"/api/v1/tasks/dlq/{failed_log.id}/replay")
    assert replay_res.status_code == 400
    assert "Unsupported task type" in replay_res.json()["detail"]
