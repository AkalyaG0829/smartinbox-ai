import pytest
from sqlalchemy import text
from src.database.session import engine

def test_metrics_endpoint_public_access(client):
    # Should be accessible without API key
    response = client.get("/metrics")
    assert response.status_code == 200
    # Content-Type should be text/plain (Prometheus format uses this with version info)
    assert "text/plain" in response.headers.get("content-type", "").lower()

def test_metrics_endpoint_content(client):
    response = client.get("/metrics")
    assert response.status_code == 200
    
    content = response.text
    # Check for some basic Prometheus metrics
    assert "http_requests_total" in content
    assert "http_request_size_bytes" in content

def test_alembic_configuration():
    from alembic.config import Config
    from alembic import command
    
    alembic_cfg = Config("alembic.ini")
    
    # Just checking that the config can be parsed and we have a valid environment
    assert "alembic" in alembic_cfg.get_main_option("script_location")
    
    # We shouldn't run a full migration in unit tests because the tests use an in-memory SQLite setup 
    # created by Base.metadata.create_all(), but we can ensure Alembic environment loads properly.
    # We will just verify it does not crash when getting current heads.
    # Note: command.heads() returns the head revisions but prints them.
    # We'll just capture or run it.
    command.heads(alembic_cfg)
