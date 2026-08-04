import pytest

def test_health_endpoint(client):
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
