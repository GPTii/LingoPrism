import pytest


@pytest.fixture(autouse=True)
def _fresh_rate_limits():
    """Rate-limit counters live in the cache: every test starts from zero."""
    from django.core.cache import cache

    cache.clear()
    yield
