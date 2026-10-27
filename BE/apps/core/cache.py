import logging
import time

from django.core.cache.backends.base import DEFAULT_TIMEOUT
from django.core.cache.backends.redis import RedisCache
from redis.exceptions import RedisError

log = logging.getLogger(__name__)

RETRY_AFTER = 10  # seconds without trying Redis once it failed (a circuit breaker)


class ResilientRedisCache(RedisCache):
    """The Redis cache, except that Redis being unreachable is a cache miss instead of a 500.

    The cache holds the rate-limit counters, so with the plain backend a Redis restart took the whole API down
    (every request reads its counter). Without Redis the DRF limits are simply off for a moment (nginx still limits
    per IP) and the site keeps working. After a failure Redis is not tried again for RETRY_AFTER seconds, so
    requests do not each wait for a connection timeout; the error is logged once per outage.
    """

    _down_until = 0.0

    def _call(self, op, default, *args):
        if time.monotonic() < ResilientRedisCache._down_until:
            return default
        try:
            result = getattr(super(), op)(*args)
        except RedisError:
            if not ResilientRedisCache._down_until:
                log.error("Redis unreachable (%s): cache acts as empty, rate limits are off until it is back", op)
            ResilientRedisCache._down_until = time.monotonic() + RETRY_AFTER
            return default
        if ResilientRedisCache._down_until:
            ResilientRedisCache._down_until = 0.0
            log.warning("Redis is back")
        return result

    def get(self, key, default=None, version=None):
        return self._call("get", default, key, default, version)

    def get_many(self, keys, version=None):
        return self._call("get_many", {}, keys, version)

    def has_key(self, key, version=None):
        return self._call("has_key", False, key, version)

    def add(self, key, value, timeout=DEFAULT_TIMEOUT, version=None):
        return self._call("add", False, key, value, timeout, version)

    def set(self, key, value, timeout=DEFAULT_TIMEOUT, version=None):
        return self._call("set", None, key, value, timeout, version)

    def set_many(self, data, timeout=DEFAULT_TIMEOUT, version=None):
        return self._call("set_many", list(data), data, timeout, version)

    def touch(self, key, timeout=DEFAULT_TIMEOUT, version=None):
        return self._call("touch", False, key, timeout, version)

    def delete(self, key, version=None):
        return self._call("delete", False, key, version)

    def delete_many(self, keys, version=None):
        return self._call("delete_many", None, keys, version)

    def incr(self, key, delta=1, version=None):
        return self._call("incr", delta, key, delta, version)
