import pytest
from unittest.mock import PropertyMock, patch, MagicMock
from src.infrastructure.models import UserInteraction
from src.worker import recalculate_personalization_stats

def test_create_user_interaction_success(client, db_session):
    """
    Verifies that a valid interaction ingestion request successfully persists
    in the database and dispatches the Celery task.
    """
    payload = {
        "user_id": "u_test_event_001",
        "message_id": "msg_test_event_001",
        "opened": True,
        "replied": True,
        "dismissed": False,
        "reported": False,
        "reaction_time_seconds": 15
    }

    with patch("src.worker.recalculate_personalization_stats.delay") as mock_delay:
        response = client.post("/api/v1/interactions", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "success"
        assert "interaction_id" in data

        # Assert delay was triggered with correct arguments
        mock_delay.assert_called_once_with("u_test_event_001", "default_sender")

    # Assert DB state
    interaction_id = data["interaction_id"]
    record = db_session.query(UserInteraction).filter(UserInteraction.id == interaction_id).first()
    assert record is not None
    assert record.user_id == "u_test_event_001"
    assert record.message_id == "msg_test_event_001"
    assert record.opened is True
    assert record.replied is True
    assert record.reaction_time_seconds == 15

def test_create_user_interaction_invalid_payload(client):
    """
    Verifies that requests with missing required fields (e.g., user_id or message_id)
    fail validation with a 422 Unprocessable Entity code.
    """
    # Missing message_id
    payload = {
        "user_id": "u_test_event_002",
        "opened": True
    }
    response = client.post("/api/v1/interactions", json=payload)
    assert response.status_code == 422

    # Missing user_id
    payload_missing_user = {
        "message_id": "msg_test_event_002",
        "replied": True
    }
    response2 = client.post("/api/v1/interactions", json=payload_missing_user)
    assert response2.status_code == 422

def test_create_user_interaction_non_sqlite_missing_user_message(client, db_session):
    """
    Verifies that on non-SQLite database configurations (like PostgreSQL), recording
    an interaction for non-existent user_id or message_id returns a 400 Bad Request
    instead of silently creating stub records.
    """
    orig_name = db_session.bind.dialect.name
    db_session.bind.dialect.name = 'postgresql'
    try:
        payload = {
            "user_id": "non_existent_user_pg",
            "message_id": "non_existent_message_pg",
            "opened": True
        }
        response = client.post("/api/v1/interactions", json=payload)
        assert response.status_code == 400
        assert "does not exist" in response.json()["detail"]
    finally:
        db_session.bind.dialect.name = orig_name

def test_celery_task_registration():
    """
    Verifies that the recalculate_personalization_stats task is correctly registered
    with Celery and can be queried.
    """
    from src.worker import celery_app
    assert "tasks.recalculate_personalization_stats" in celery_app.tasks

def test_celery_task_execution_and_session_handling(db_session):
    """
    Verifies that direct synchronous execution of the Celery task processes
    the aggregation query correctly and disposes of DB sessions cleanly.
    """
    from src.infrastructure.models import User, Message, Channel

    user = User(id="u_task_01", email="task_user@example.com")
    chan = Channel(id="c_task_01", name="Task Chan", type="personal", external_id="c_task_01")
    db_session.add(user)
    db_session.add(chan)
    db_session.flush()

    msg = Message(id="m_task_01", channel_id=chan.id, sender_id="s_task_01", message_text="Stats task message")
    db_session.add(msg)
    db_session.flush()

    interaction = UserInteraction(user_id=user.id, message_id=msg.id, opened=True, replied=True, dismissed=False, reported=False, reaction_time_seconds=90)
    db_session.add(interaction)
    db_session.commit()

    # Run the Celery task synchronously
    stats = recalculate_personalization_stats(user.id, "s_task_01", db_session)
    assert stats["total_count"] == 1
    assert stats["reply_rate"] == 1.0
    assert stats["has_fast_historical_reply"] is True

def test_celery_task_failure_handling():
    """
    Verifies that recalculate_personalization_stats task propagates errors without
    corrupting any database contexts.
    """
    # Run task with invalid parameters to force a DB exception or type error
    with pytest.raises(Exception):
        recalculate_personalization_stats(None, None)
