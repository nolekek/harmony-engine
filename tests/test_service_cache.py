"""
Tests for the bounded LRU+TTL request cache in backend.service (audit M2):
eviction at capacity, TTL expiry (monkeypatched clock), hit/miss semantics,
and preserved cache-hit behaviour for identical harmonize requests.
"""

import copy
import time as real_time

import pytest

from backend import service as service_mod
from backend.service import (
    CACHE_MAX_ENTRIES,
    CACHE_TTL_SEC,
    HarmonizationService,
    _cache_lookup,
    _cache_store,
    clear_service_cache,
)


class FakeClock:
    """Drop-in replacement for the `time` module inside backend.service."""

    def __init__(self) -> None:
        self.now = 1000.0

    def monotonic(self) -> float:
        return self.now

    def perf_counter(self) -> float:
        return real_time.perf_counter()

    def advance(self, seconds: float) -> None:
        self.now += seconds


@pytest.fixture(autouse=True)
def _flush_cache():
    clear_service_cache()
    yield
    clear_service_cache()


def test_cache_miss_returns_none():
    assert _cache_lookup(("never-stored",)) is None


def test_cache_hit_returns_independent_copy():
    payload = {"is_success": True, "candidates": [{"cost": 1.0}]}
    _cache_store(("k1",), payload)
    hit = _cache_lookup(("k1",))
    assert hit == payload
    assert hit is not payload
    # Mutating the returned copy must not poison the cache
    hit["candidates"][0]["cost"] = 999.0
    assert _cache_lookup(("k1",))["candidates"][0]["cost"] == 1.0


def test_cache_ttl_expiry(monkeypatch):
    clock = FakeClock()
    monkeypatch.setattr(service_mod, "time", clock)
    _cache_store(("k1",), {"v": 1})

    clock.advance(CACHE_TTL_SEC - 1)
    assert _cache_lookup(("k1",)) == {"v": 1}

    clock.advance(2.0)  # now beyond TTL
    assert _cache_lookup(("k1",)) is None
    assert len(service_mod._SERVICE_REQUEST_CACHE) == 0


def test_cache_lru_eviction_at_capacity():
    for i in range(CACHE_MAX_ENTRIES + 1):
        _cache_store((f"key{i}",), {"i": i})
    assert len(service_mod._SERVICE_REQUEST_CACHE) == CACHE_MAX_ENTRIES
    assert _cache_lookup(("key0",)) is None  # oldest evicted
    assert _cache_lookup((f"key{CACHE_MAX_ENTRIES}",)) == {"i": CACHE_MAX_ENTRIES}


def test_cache_lru_refresh_on_hit():
    for i in range(CACHE_MAX_ENTRIES):
        _cache_store((f"key{i}",), {"i": i})
    # Touch key0 so key1 becomes the LRU tail
    assert _cache_lookup(("key0",)) is not None
    _cache_store(("overflow",), {"i": -1})
    assert _cache_lookup(("key0",)) == {"i": 0}
    assert _cache_lookup(("key1",)) is None


def test_clear_service_cache_empties_store():
    _cache_store(("k",), {"v": 1})
    clear_service_cache()
    assert len(service_mod._SERVICE_REQUEST_CACHE) == 0
    assert _cache_lookup(("k",)) is None


def test_harmonize_identical_request_served_from_cache():
    """Cache-hit behaviour for identical requests is preserved end-to-end."""
    svc = HarmonizationService()
    req = {
        "melody": [
            {"pitch": 64, "duration": "half", "is_downbeat": True},
            {"pitch": 65, "duration": "half", "is_downbeat": False},
            {"pitch": 67, "duration": "half", "is_downbeat": True},
            {"pitch": 62, "duration": "half", "is_downbeat": False},
            {"pitch": 60, "duration": "half", "is_downbeat": True},
        ],
        "key": {"tonic": "C", "mode": "Major"},
        "time_signature": "4/4",
    }
    first = svc.harmonize(copy.deepcopy(req))
    assert first["is_success"] is True
    assert len(service_mod._SERVICE_REQUEST_CACHE) == 1

    second = svc.harmonize(copy.deepcopy(req))
    assert second["is_success"] is True
    assert [c["chords"] for c in second["candidates"]] == [c["chords"] for c in first["candidates"]]
    assert len(service_mod._SERVICE_REQUEST_CACHE) == 1
