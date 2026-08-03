import json
import hashlib
import redis
from src.config.settings import settings

class EmbeddingCache:
    _client = None

    @classmethod
    def get_client(cls):
        if not settings.EMBEDDING_CACHE_ENABLED:
            return None
        if cls._client is None:
            try:
                cls._client = redis.from_url(settings.REDIS_URL, decode_responses=True, socket_connect_timeout=1.0)
            except Exception as e:
                print(f"Failed to initialize Redis embedding client: {str(e)}")
                cls._client = None
        return cls._client

    @classmethod
    def get_key(cls, text: str) -> str:
        text_hash = hashlib.sha256(text.encode('utf-8')).hexdigest()
        return f"embedding:sha256:{text_hash}"

    @classmethod
    def get(cls, text: str) -> list or None:
        """
        Retrieves cached embedding vector for a given text.
        Returns None if cache is disabled, cache miss, or Redis is down.
        """
        client = cls.get_client()
        if client is None:
            return None
        key = cls.get_key(text)
        try:
            val = client.get(key)
            if val:
                return json.loads(val)
        except Exception as e:
            print(f"Redis embedding get error (falling back to ST): {str(e)}")
        return None

    @classmethod
    def set(cls, text: str, vector: list) -> bool:
        """
        Caches the embedding vector in Redis with TTL.
        """
        client = cls.get_client()
        if client is None:
            return False
        key = cls.get_key(text)
        try:
            client.set(key, json.dumps(vector), ex=settings.EMBEDDING_CACHE_TTL)
            return True
        except Exception as e:
            print(f"Redis embedding set error: {str(e)}")
        return False
