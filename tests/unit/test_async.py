import pytest
from unittest.mock import MagicMock, patch

def test_async_process_endpoint(client):
    # Enqueue payload validation
    payload = {
        "message_id": "test_async_001",
        "user_id": "u_001",
        "conversation_type": "personal",
        "created_at": "2026-08-02 12:00:00",
        "message_text": "Hello this is an async test."
    }
    
    with patch("src.main.process_message_async.delay") as mock_delay:
        mock_task = MagicMock()
        mock_task.id = "mock_task_id_123"
        mock_delay.return_value = mock_task
        
        response = client.post("/api/v1/messages/process-async", json=payload)
        assert response.status_code == 202
        data = response.json()
        assert data["task_id"] == "mock_task_id_123"
        assert data["status"] == "PENDING"
        mock_delay.assert_called_once()

def test_get_task_status_pending(client):
    # Task enqueued but not completed
    with patch("src.main.AsyncResult") as mock_async_result:
        mock_res = MagicMock()
        mock_res.state = "PENDING"
        mock_async_result.return_value = mock_res
        
        response = client.get("/api/v1/messages/tasks/mock_task_id_123")
        assert response.status_code == 200
        data = response.json()
        assert data["task_id"] == "mock_task_id_123"
        assert data["status"] == "PENDING"

def test_get_task_status_success(client):
    # Successful task result extraction
    with patch("src.main.AsyncResult") as mock_async_result:
        mock_res = MagicMock()
        mock_res.state = "SUCCESS"
        mock_res.result = {
            "message_id": "test_async_001",
            "message_type": "personal",
            "action": "digest",
            "confidence": 0.85,
            "reason": "General message",
            "safety_result": {"detected": False, "risk_level": "low", "matched_indicators": [], "sanitized_text": ""},
            "urgency_result": {"is_urgent": False, "urgency_score": 0.0, "urgency_reasons": []},
            "personalization_result": {"priority_score": 2.0, "trust_score": 3.5, "relationship_score": 2.0, "reasons": []},
            "evidence_message_ids": "none",
            "processing_metadata": {}
        }
        mock_async_result.return_value = mock_res
        
        response = client.get("/api/v1/messages/tasks/mock_task_id_123")
        assert response.status_code == 200
        data = response.json()
        assert data["task_id"] == "mock_task_id_123"
        assert data["status"] == "SUCCESS"
        assert data["result"]["message_type"] == "personal"
        assert data["result"]["action"] == "digest"

def test_get_task_status_failure(client):
    # Task failed exception recovery
    with patch("src.main.AsyncResult") as mock_async_result:
        mock_res = MagicMock()
        mock_res.state = "FAILURE"
        mock_res.result = Exception("Task crashed")
        mock_async_result.return_value = mock_res
        
        response = client.get("/api/v1/messages/tasks/mock_task_id_123")
        assert response.status_code == 200
        data = response.json()
        assert data["task_id"] == "mock_task_id_123"
        assert data["status"] == "FAILURE"
        assert "error" in data
