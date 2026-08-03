import pytest
import json
from unittest.mock import PropertyMock, patch, MagicMock
from sqlalchemy.exc import OperationalError
from redis.exceptions import ConnectionError
from src.infrastructure.providers.sentence_transformer_provider import SentenceTransformersEmbeddingProvider
from src.application.embedding_cache import EmbeddingCache
from src.config.settings import settings
from src.worker import process_message_async, recalculate_personalization_stats

class MockRedisClient:
    def __init__(self):
        self.store = {}
        self.ttls = {}

    def get(self, key):
        return self.store.get(key)

    def set(self, key, value, ex=None):
        self.store[key] = value
        if ex:
            self.ttls[key] = ex
        return True

    def delete(self, key):
        if key in self.store:
            del self.store[key]
            if key in self.ttls:
                del self.ttls[key]
            return True
        return False

@pytest.fixture(autouse=True)
def reset_embedding_cache_client():
    EmbeddingCache._client = None
    yield
    EmbeddingCache._client = None

def test_embedding_cache_key_generation():
    key = EmbeddingCache.get_key("hello world")
    assert key.startswith("embedding:sha256:")
    assert len(key.split(":")[-1]) == 64  # SHA256 hex digest length

def test_embedding_cache_miss_hit_population_and_ttl():
    mock_client = MockRedisClient()
    EmbeddingCache._client = mock_client

    # Cache miss
    assert EmbeddingCache.get("hello world") is None

    # Populate cache
    vector = [0.1] * 384
    success = EmbeddingCache.set("hello world", vector)
    assert success is True

    # Cache hit
    cached = EmbeddingCache.get("hello world")
    assert cached is not None
    assert len(cached) == 384
    assert cached[0] == 0.1

    # TTL validation
    key = EmbeddingCache.get_key("hello world")
    assert mock_client.ttls[key] == settings.EMBEDDING_CACHE_TTL

def test_model_warmup_and_caching():
    mock_client = MockRedisClient()
    EmbeddingCache._client = mock_client

    provider = SentenceTransformersEmbeddingProvider()
    assert provider._model is None

    # Warmup eager loading
    provider.warmup()
    assert provider._model is not None

    # Generate embedding (first call causes cache miss -> ST execution -> cache population)
    import asyncio
    vector = asyncio.run(provider.get_embedding("warmup text"))

    # Verify that it is stored in the cache
    cached = EmbeddingCache.get("warmup text")
    assert cached is not None
    assert len(cached) == 384

def test_redis_failure_graceful_fallback():
    # Force client to throw exceptions on get/set to simulate Redis downtime
    mock_client = MagicMock()
    mock_client.get.side_effect = ConnectionError("Redis server is down")
    mock_client.set.side_effect = ConnectionError("Redis server is down")
    EmbeddingCache._client = mock_client

    provider = SentenceTransformersEmbeddingProvider()
    provider.warmup()

    # Should fall back to SentenceTransformers directly and succeed
    import asyncio
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        vector = loop.run_until_complete(provider.get_embedding("hello fallback"))
        assert len(vector) == 384
    finally:
        loop.close()

def test_celery_task_resiliency_retry_configuration():
    # Verify task process_message_async has correct retry configuration
    assert process_message_async.autoretry_for is not None
    assert ConnectionError in process_message_async.autoretry_for
    assert OperationalError in process_message_async.autoretry_for
    assert process_message_async.retry_backoff is True
    assert process_message_async.max_retries == 5

    # Verify task recalculate_personalization_stats has correct retry configuration
    assert recalculate_personalization_stats.autoretry_for is not None
    assert ConnectionError in recalculate_personalization_stats.autoretry_for
    assert OperationalError in recalculate_personalization_stats.autoretry_for
    assert recalculate_personalization_stats.retry_backoff is True
    assert recalculate_personalization_stats.max_retries == 5
