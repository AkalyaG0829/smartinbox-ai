import pytest
from src.config.settings import settings
from src.main import app, get_api_key
from src.database.session import get_db

@pytest.fixture(autouse=True)
def remove_api_key_override(client):
    app.dependency_overrides.pop(get_api_key, None)
    yield
    # No need to restore, fixture clears it for the test scope

def test_missing_api_key_returns_401(client):
    # Make a request without the API key header
    res = client.get("/api/v1/analytics/alignment")
    assert res.status_code == 401
    assert res.json()["detail"] == "Invalid or missing API Key"

def test_invalid_api_key_returns_401(client):
    # Make a request with wrong API key
    res = client.get("/api/v1/analytics/alignment", headers={"X-API-Key": "wrong-key"})
    assert res.status_code == 401
    assert res.json()["detail"] == "Invalid or missing API Key"

def test_valid_api_key_returns_success(client):
    # Make a request with valid API key
    res = client.get("/api/v1/analytics/alignment", headers={"X-API-Key": settings.API_KEY})
    assert res.status_code == 200

def test_rate_limiting_429(client):
    # We test on analytics which is 60/minute
    for i in range(60):
        client.get("/api/v1/analytics/alignment", headers={"X-API-Key": settings.API_KEY})
        
    res = client.get("/api/v1/analytics/alignment", headers={"X-API-Key": settings.API_KEY})
    assert res.status_code == 429
    assert "Rate limit exceeded" in res.text

def test_health_check_public(client):
    # Should not require API key
    res = client.get("/health")
    assert res.status_code in (200, 503) # might be 503 if redis is down in test env, but not 401
