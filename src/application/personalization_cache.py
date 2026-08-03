import json
import redis
from src.config.settings import settings

class PersonalizationCache:
    _client = None

    @classmethod
    def get_client(cls):
        if not settings.PERSONALIZATION_CACHE_ENABLED:
            return None
        if cls._client is None:
            try:
                cls._client = redis.from_url(settings.REDIS_URL, decode_responses=True, socket_connect_timeout=1.0)
            except Exception as e:
                print(f"Failed to initialize Redis client: {str(e)}")
                cls._client = None
        return cls._client

    @classmethod
    def get_key(cls, user_id: str, sender_id: str) -> str:
        return f"personalization:{user_id}:{sender_id}"

    @classmethod
    def get(cls, user_id: str, sender_id: str) -> dict or None:
        """
        Retrieves cached personalization statistics. Returns None if cache is disabled,
        cache miss occurs, or Redis is unavailable.
        """
        client = cls.get_client()
        if client is None:
            return None
        key = cls.get_key(user_id, sender_id)
        try:
            val = client.get(key)
            if val:
                return json.loads(val)
        except Exception as e:
            print(f"Redis get error (falling back to DB): {str(e)}")
        return None

    @classmethod
    def set(cls, user_id: str, sender_id: str, stats: dict) -> bool:
        """
        Caches personalization statistics with TTL. Returns False if operation fails or cache is disabled.
        """
        client = cls.get_client()
        if client is None:
            return False
        key = cls.get_key(user_id, sender_id)
        try:
            client.set(key, json.dumps(stats), ex=settings.PERSONALIZATION_CACHE_TTL)
            return True
        except Exception as e:
            print(f"Redis set error: {str(e)}")
        return False

    @classmethod
    def invalidate(cls, user_id: str, sender_id: str) -> bool:
        """
        Invalidates cached personalization statistics.
        """
        client = cls.get_client()
        if client is None:
            return False
        key = cls.get_key(user_id, sender_id)
        try:
            client.delete(key)
            return True
        except Exception as e:
            print(f"Redis delete error: {str(e)}")
        return False
