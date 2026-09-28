import logging
import threading
import time

import redis

from app.config import REDIS_URL

logger = logging.getLogger(__name__)


class InMemoryRedis:
    """Tiny single-process stand-in for the Redis calls this app uses.

    Only used when Redis is unreachable so the app still runs for a demo;
    locking is then atomic per process but not distributed.
    """

    def __init__(self):
        self._data: dict[str, tuple[str, float | None]] = {}
        self._lock = threading.Lock()

    def _alive(self, key):
        item = self._data.get(key)
        if item is None:
            return None
        value, expires = item
        if expires is not None and expires <= time.monotonic():
            del self._data[key]
            return None
        return value

    def ping(self):
        return True

    def set(self, key, value, nx=False, ex=None):
        with self._lock:
            if nx and self._alive(key) is not None:
                return None
            expires = time.monotonic() + ex if ex else None
            self._data[key] = (str(value), expires)
            return True

    def get(self, key):
        with self._lock:
            return self._alive(key)

    def mget(self, keys):
        with self._lock:
            return [self._alive(k) for k in keys]

    def delete(self, *keys):
        with self._lock:
            removed = 0
            for key in keys:
                if self._alive(key) is not None:
                    del self._data[key]
                    removed += 1
            return removed

    def expire(self, key, seconds):
        with self._lock:
            value = self._alive(key)
            if value is None:
                return False
            self._data[key] = (value, time.monotonic() + seconds)
            return True

    def ttl(self, key):
        with self._lock:
            if self._alive(key) is None:
                return -2
            expires = self._data[key][1]
            return -1 if expires is None else max(int(expires - time.monotonic()), 0)


def _connect():
    try:
        client = redis.Redis.from_url(REDIS_URL, decode_responses=True, socket_connect_timeout=2)
        client.ping()
        logger.info("Connected to Redis")
        return client, "redis"
    except Exception as e:
        logger.warning("Redis unavailable (%s) - falling back to in-memory locks", e)
        return InMemoryRedis(), "in-memory"


redis_client, REDIS_MODE = _connect()
