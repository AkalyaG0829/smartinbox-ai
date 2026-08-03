import pytest
import json
from unittest.mock import patch, MagicMock, PropertyMock
from src.application.personalization_cache import PersonalizationCache
from src.config.settings import settings

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
def reset_cache_client():
    PersonalizationCache._client = None
    yield
    PersonalizationCache._client = None

def test_cache_key_generation():
    key = PersonalizationCache.get_key("u123", "s456")
    assert key == "personalization:u123:s456"

def test_cache_miss_hit_population_and_ttl():
    mock_client = MockRedisClient()
    PersonalizationCache._client = mock_client

    # Cache miss
    assert PersonalizationCache.get("u123", "s456") is None

    # Cache population
    stats = {"total_count": 5, "open_rate": 0.8}
    success = PersonalizationCache.set("u123", "s456", stats)
    assert success is True

    # TTL verification
    key = PersonalizationCache.get_key("u123", "s456")
    assert mock_client.ttls[key] == settings.PERSONALIZATION_CACHE_TTL

    # Cache hit
    cached = PersonalizationCache.get("u123", "s456")
    assert cached is not None
    assert cached["total_count"] == 5
    assert cached["open_rate"] == 0.8

def test_cache_invalidation():
    mock_client = MockRedisClient()
    PersonalizationCache._client = mock_client

    stats = {"total_count": 5, "open_rate": 0.8}
    PersonalizationCache.set("u123", "s456", stats)

    # Invalidate
    success = PersonalizationCache.invalidate("u123", "s456")
    assert success is True
    assert PersonalizationCache.get("u123", "s456") is None

def test_redis_failure_graceful_fallback():
    # Make get/set raise exceptions
    mock_client = MagicMock()
    mock_client.get.side_effect = Exception("Redis error")
    mock_client.set.side_effect = Exception("Redis error")
    PersonalizationCache._client = mock_client

    # Graceful fallback to return None / False
    assert PersonalizationCache.get("u123", "s456") is None
    assert PersonalizationCache.set("u123", "s456", {"ok": True}) is False

def test_celery_recalculation_updates_cache(db_session):
    from src.infrastructure.models import User, Message, Channel, UserInteraction
    from src.worker import recalculate_personalization_stats

    mock_client = MockRedisClient()
    PersonalizationCache._client = mock_client

    user = User(id="u_rec_01", email="rec_user@example.com")
    chan = Channel(id="c_rec_01", name="Rec Chan", type="personal", external_id="c_rec_01")
    db_session.add(user)
    db_session.add(chan)
    db_session.flush()

    msg = Message(id="m_rec_01", channel_id=chan.id, sender_id="s_rec_01", message_text="Test message")
    db_session.add(msg)
    db_session.flush()

    interaction = UserInteraction(user_id=user.id, message_id=msg.id, opened=True, replied=True)
    db_session.add(interaction)
    db_session.commit()

    # Executing the task updates the cache
    recalculate_personalization_stats(user.id, "s_rec_01", db_session)

    cached = PersonalizationCache.get(user.id, "s_rec_01")
    assert cached is not None
    assert cached["total_count"] == 1
    assert cached["reply_rate"] == 1.0

def test_interaction_endpoint_invalidates_cache(client, db_session):
    mock_client = MockRedisClient()
    PersonalizationCache._client = mock_client

    # Populate cache first
    stats = {"total_count": 1}
    PersonalizationCache.set("u_test_event_001", "default_sender", stats)
    assert PersonalizationCache.get("u_test_event_001", "default_sender") is not None

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

    # Verify cache is invalidated (removed) after post
    assert PersonalizationCache.get("u_test_event_001", "default_sender") is None
