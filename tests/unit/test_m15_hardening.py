import pytest
from slowapi import Limiter
from slowapi.util import get_remote_address
from limits.storage.redis import RedisStorage
from src.config.settings import settings

def test_rate_limiter_uses_redis():
    limiter = Limiter(key_func=get_remote_address, storage_uri=settings.REDIS_URL)
    assert isinstance(limiter._storage, RedisStorage)
