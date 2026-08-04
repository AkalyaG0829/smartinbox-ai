import pytest

from unittest.mock import patch

@patch("redis.Redis.from_url")
def test_health_endpoint(mock_redis, client):
    # Mock Redis ping to return true
    mock_redis.return_value.ping.return_value = True

    # We also need to mock the pgvector execution
    # Since testing uses SQLite which doesn't have vector by default,
    # we mock the Session's execute just for the vector check if we can,
    # or just accept that pgvector might be 'unreachable' but status should not be 503 if we allow partial health.
    # Wait, in get_health, if any is unreachable, does it return 503?
    # Ah, in main.py:
    # try: res = db.execute(text("SELECT '[1,2,3]'::vector;")).fetchone()
    # except Exception: health_status["status"] = "unhealthy"

    with patch("sqlalchemy.orm.Session.execute") as mock_exec:
        # DB will be healthy
        mock_exec.return_value.fetchone.return_value = [True]
        response = client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "database" in data

def test_route_message_endpoint(client):
    # Pass a basic payload matching expected message route contract
    payload = {
        "message_id": "test_msg_001",
        "user_id": "u_001",
        "conversation_type": "personal",
        "sender_user_id": "u_002",
        "created_at": "2026-07-30 22:19:00",
        "message_text": "Good morning my friend, how are you?",
        "media_type": "none",
        "forwarded_count": 0
    }
    response = client.post("/api/v1/messages/route", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "action" in data
    assert "message_type" in data
    assert "reason" in data
    assert "confidence" in data
    assert "evidence_message_ids" in data

def test_get_routing_alignment_analytics_endpoint(client):
    response = client.get("/api/v1/analytics/alignment")
    assert response.status_code == 200
    data = response.json()
    assert "alignment_rate" in data
    assert "total_actions" in data
    assert "aligned_count" in data
    assert "misaligned_count" in data
    assert "mismatches" in data
