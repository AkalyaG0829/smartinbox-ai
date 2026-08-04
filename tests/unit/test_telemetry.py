import pytest
from src.main import app

def test_correlation_id_injected_in_response(client):
    res = client.get("/health")
    assert "X-Correlation-ID" in res.headers
    assert len(res.headers["X-Correlation-ID"]) > 0

def test_correlation_id_preserved_when_provided(client):
    custom_id = "test-custom-id-1234"
    res = client.get("/health", headers={"X-Correlation-ID": custom_id})
    assert res.headers.get("X-Correlation-ID") == custom_id

def test_health_check_returns_full_status(client):
    res = client.get("/health")
    data = res.json().get("detail", res.json())
    assert "status" in data
    assert "database" in data
    assert "redis" in data
    assert "pgvector" in data
