import pytest
from prometheus_client import REGISTRY

def test_dlq_metric_exists():
    """
    Verify that the DLQ counter metric is successfully registered in the Prometheus registry.
    """
    metrics = [metric.name for metric in REGISTRY.collect()]
    assert "smartinbox_dlq_entries" in metrics or "smartinbox_dlq_entries_total" in metrics, "DLQ entries metric must be exposed"

def test_fastapi_instrumentation_active(client):
    """
    Verify that the /metrics endpoint exists and exposes default FastAPI metrics.
    """
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "http_requests_total" in response.text
    assert "smartinbox_dlq_entries_total" in response.text
