import pytest
import asyncio
from prometheus_client import REGISTRY

def test_pipeline_increments_custom_metrics(db_session):
    from src.application.pipeline import MessageRoutingPipeline
    from src.infrastructure.providers.mock_providers import MockSpeechToTextProvider, MockOCRProvider, LocalPromptInjectionShield
    from src.infrastructure.providers.sentence_transformer_provider import SentenceTransformersEmbeddingProvider
    
    stt_prov = MockSpeechToTextProvider()
    ocr_prov = MockOCRProvider()
    emb_prov = SentenceTransformersEmbeddingProvider(model_name="all-MiniLM-L6-v2")
    inj_shld = LocalPromptInjectionShield()

    pipeline = MessageRoutingPipeline(
        db=db_session,
        stt_provider=stt_prov,
        ocr_provider=ocr_prov,
        embedding_provider=emb_prov,
        injection_shield=inj_shld
    )
    
    # Get baseline values from Prometheus registry
    def get_metric_value(name, labels):
        val = REGISTRY.get_sample_value(name, labels)
        return val if val is not None else 0.0

    baseline_digest = get_metric_value("smartinbox_routing_decisions_total", {"action": "digest"})
    baseline_high_conf = get_metric_value("smartinbox_confidence_bands_total", {"band": "high"})
    baseline_embedding_count = get_metric_value("smartinbox_embedding_duration_seconds_count", {})
    
    request_data = {
        "message_id": "metric_test_msg_1",
        "user_id": "test_user_metrics@example.com",
        "message_text": "Hey, let's meet tomorrow!",
        "conversation_type": "personal",
        "sender_user_id": "friend_1",
        "created_at": "2026-08-04T12:00:00Z",
        "evidence_message_ids": "none"
    }
    
    from src.application.schemas import MessageProcessingRequest
    req = MessageProcessingRequest(**request_data)
    
    result = asyncio.run(pipeline.process_incoming_message(req))
    
    assert result.action == "digest"
    
    new_digest = get_metric_value("smartinbox_routing_decisions_total", {"action": "digest"})
    
    conf_score = float(result.confidence)
    band = "high" if conf_score >= 0.8 else ("medium" if conf_score >= 0.5 else "low")
    new_conf = get_metric_value("smartinbox_confidence_bands_total", {"band": band})
    baseline_conf = get_metric_value("smartinbox_confidence_bands_total", {"band": band}) - 1 # Since we incremented it
    
    new_embedding_count = get_metric_value("smartinbox_embedding_duration_seconds_count", {})
    
    assert new_digest > baseline_digest
    assert new_conf > baseline_conf
    assert new_embedding_count > baseline_embedding_count

def test_metrics_endpoint_exposes_custom_metrics(client):
    response = client.get("/metrics")
    assert response.status_code == 200
    
    content = response.text
    assert "smartinbox_routing_decisions_total" in content
    assert "smartinbox_confidence_bands_total" in content
    assert "smartinbox_embedding_duration_seconds" in content
