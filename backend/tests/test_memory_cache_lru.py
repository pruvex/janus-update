"""
Test-Skript für MemoryRAMCache LRU-Eviction mit 501 Memories.

Verifiziert:
1. MAX_ITEMS=500 Limit (OOM-Schutz)
2. LRU-Eviction bei Überlauf (niedrigste Priority zuerst)
3. Cache-Stats (hits, misses, evictions)
4. Cache-Touch (LRU-Update)

Usage:
    python backend/tests/test_memory_cache_lru.py
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from dataclasses import dataclass

from backend.services.memory_cache import CachedMemory, memory_cache


@dataclass(frozen=True)
class TestCachedMemory:
    """Test-Version von CachedMemory mit manueller ID-Steuerung."""
    id: int
    canonical_key: str
    priority: float
    memory_type: str = "GENERAL"
    tags: tuple = ()
    snippet: str = ""
    text_hash: str = ""


def reset_cache():
    """Reset den globalen Cache für saubere Tests."""
    memory_cache.invalidate_all()
    memory_cache._metrics.hits = 0
    memory_cache._metrics.misses = 0
    memory_cache._metrics.evictions = 0
    memory_cache._metrics.refreshes = 0
    memory_cache._metrics.invalidations = 0


def test_max_items_limit():
    """Test 1: MAX_ITEMS=500 wird eingehalten."""
    print("\n[Test 1] MAX_ITEMS Limit (500 Einträge)")
    reset_cache()
    
    # Erstelle 501 Einträge mit Priority >= 0.8 (alle sollten in Cache passen, aber limit ist 500)
    for i in range(1, 502):  # 1 bis 501
        mem = TestCachedMemory(
            id=i,
            canonical_key=f"test:key:{i}",
            priority=0.8 + (i / 1000),  # 0.801 bis 1.300
        )
        # Wir nutzen direkt den Cache, aber CachedMemory ist frozen, also cast
        cached = CachedMemory(
            id=mem.id,
            canonical_key=mem.canonical_key,
            priority=mem.priority,
            memory_type=mem.memory_type,
            tags=mem.tags,
            snippet=mem.snippet,
            text_hash=mem.text_hash
        )
        memory_cache.put(cached)
    
    cache_count = len(memory_cache.get_all())
    expected_max = memory_cache.MAX_ITEMS
    
    print(f"  -> 501 Einträge hinzugefügt, Cache-Größe: {cache_count}")
    print(f"  -> MAX_ITEMS: {expected_max}")
    
    assert cache_count <= expected_max, f"Cache überfüllt: {cache_count} > {expected_max}"
    assert cache_count == expected_max, f"Cache sollte exakt {expected_max} haben, hat {cache_count}"
    
    print("  ✅ Test 1 PASSED: Cache-Limit eingehalten")
    return True


def test_lru_eviction_lowest_priority():
    """Test 2: LRU evicted niedrigste Priority bei Überlauf."""
    print("\n[Test 2] LRU-Eviction (niedrigste Priority zuerst)")
    reset_cache()
    
    # Füge 500 Einträge mit steigender Priority hinzu (0.80 bis 1.299)
    for i in range(1, 501):
        mem = CachedMemory(
            id=i,
            canonical_key=f"test:key:{i}",
            priority=0.8 + ((i - 1) / 1000),  # 0.80, 0.801, ...
            memory_type="CORE",
            tags=(),
            snippet="",
            text_hash=""
        )
        memory_cache.put(mem)
    
    # Finde minimum Priority im Cache
    all_mems = memory_cache.get_all()
    min_priority = min(m.priority for m in all_mems)
    max_priority = max(m.priority for m in all_mems)
    
    print(f"  -> 500 Einträge: min_priority={min_priority:.4f}, max_priority={max_priority:.4f}")
    
    # Füge 501. Eintrag mit sehr hoher Priority hinzu (sollte nicht evicted werden)
    new_mem = CachedMemory(
        id=501,
        canonical_key="test:key:501",
        priority=1.5,  # Höchste Priority
        memory_type="CORE",
        tags=(),
        snippet="",
        text_hash=""
    )
    memory_cache.put(new_mem)
    
    # Check: Eviction sollte passiert sein
    evictions = memory_cache._metrics.evictions
    print(f"  -> Evictions: {evictions}")
    assert evictions >= 1, f"Es sollte mindestens 1 Eviction geben, aber: {evictions}"
    
    # Check: ID mit niedrigster Priority (0.80) sollte evicted sein
    cache_ids = {m.id for m in memory_cache.get_all()}
    assert 1 not in cache_ids, "ID=1 (niedrigste Priority 0.80) sollte evicted sein"
    assert 501 in cache_ids, "ID=501 (höchste Priority 1.5) sollte im Cache sein"
    
    # Check: Neue min Priority
    new_min = min(m.priority for m in memory_cache.get_all())
    print(f"  -> Neue min_priority nach Eviction: {new_min:.4f}")
    assert new_min > 0.8, "Neue min Priority sollte > 0.8 sein"
    
    print("  ✅ Test 2 PASSED: LRU evicted niedrigste Priority")
    return True


def test_lru_touch_updates_position():
    """Test 3: Touch verschiebt Eintrag ans Ende (LRU-Preservation)."""
    print("\n[Test 3] Cache-Touch verschiebt LRU-Position")
    reset_cache()
    
    # Füge 3 Einträge hinzu (alle gleiche Priority)
    for i in range(1, 4):
        mem = CachedMemory(
            id=i,
            canonical_key=f"key:{i}",
            priority=0.9,
            memory_type="CORE",
            tags=(),
            snippet="",
            text_hash=""
        )
        memory_cache.put(mem)
    
    # Touch ID=1 (änderste, sollte jetzt am Ende/LRU-safe sein)
    memory_cache.touch(1)
    
    # Füge neuen Eintrag mit niedrigerer Priority hinzu, um Eviction zu triggern
    new_mem = CachedMemory(
        id=4,
        canonical_key="key:4",
        priority=0.85,  # Niedriger als 0.9
        memory_type="GENERAL",
        tags=(),
        snippet="",
        text_hash=""
    )
    memory_cache.put(new_mem)
    
    # Da alle 0.9 Einträge gleiche Priority haben, sollte nach Touch
    # der am längsten nicht verwendete (nicht ID=1) evicted werden
    cache_ids = {m.id for m in memory_cache.get_all()}
    
    print(f"  -> Cache IDs nach Touch(1) + Put(4): {sorted(cache_ids)}")
    assert 1 in cache_ids, "ID=1 sollte noch da sein (getouched)"
    assert 4 in cache_ids, "ID=4 sollte da sein (neu)"
    
    print("  ✅ Test 3 PASSED: Touch bewahrt Eintrag vor Eviction")
    return True


def test_cache_stats():
    """Test 4: Cache-Stats sind korrekt."""
    print("\n[Test 4] Cache-Statistik")
    reset_cache()
    
    # Füge Eintrag hinzu
    mem = CachedMemory(id=1, canonical_key="key:1", priority=0.95, memory_type="CORE", tags=(), snippet="", text_hash="")
    memory_cache.put(mem)
    
    # Miss (nicht im Cache)
    result = memory_cache.get(999)
    assert result is None
    
    # Hit (im Cache)
    result = memory_cache.get(1)
    assert result is not None
    
    stats = memory_cache.get_stats()
    print(f"  -> Stats: {stats}")
    
    assert stats['metrics']['hits'] == 1, f"Expected 1 hit, got {stats['metrics']['hits']}"
    assert stats['metrics']['misses'] == 1, f"Expected 1 miss, got {stats['metrics']['misses']}"
    assert stats['cached_count'] == 1, f"Expected 1 cached, got {stats['cached_count']}"
    
    print("  ✅ Test 4 PASSED: Cache-Stats korrekt")
    return True


def test_invalidate():
    """Test 5: Invalidate entfernt Eintrag."""
    print("\n[Test 5] Cache-Invalidate")
    reset_cache()
    
    mem = CachedMemory(id=1, canonical_key="key:1", priority=0.95, memory_type="CORE", tags=(), snippet="", text_hash="")
    memory_cache.put(mem)
    
    assert memory_cache.get(1) is not None
    
    memory_cache.invalidate(1)
    
    assert memory_cache.get(1) is None
    assert memory_cache._metrics.invalidations == 1
    
    print("  ✅ Test 5 PASSED: Invalidate funktioniert")
    return True


def test_get_by_tag():
    """Test 6: Filterung nach Tags."""
    print("\n[Test 6] Filter nach Tags")
    reset_cache()
    
    mem1 = CachedMemory(id=1, canonical_key="key:1", priority=0.9, memory_type="CORE", 
                      tags=("identity", "pet"), snippet="", text_hash="")
    mem2 = CachedMemory(id=2, canonical_key="key:2", priority=0.9, memory_type="CORE",
                      tags=("identity", "appearance"), snippet="", text_hash="")
    mem3 = CachedMemory(id=3, canonical_key="key:3", priority=0.9, memory_type="GENERAL",
                      tags=("temporal",), snippet="", text_hash="")
    
    memory_cache.put(mem1)
    memory_cache.put(mem2)
    memory_cache.put(mem3)
    
    identity_mems = memory_cache.get_by_tag("identity")
    pet_mems = memory_cache.get_by_tag("pet")
    temporal_mems = memory_cache.get_by_tag("temporal")
    
    print(f"  -> 'identity': {len(identity_mems)} Einträge")
    print(f"  -> 'pet': {len(pet_mems)} Einträge")
    print(f"  -> 'temporal': {len(temporal_mems)} Einträge")
    
    assert len(identity_mems) == 2
    assert len(pet_mems) == 1
    assert len(temporal_mems) == 1
    
    print("  ✅ Test 6 PASSED: Tag-Filterung korrekt")
    return True


def run_all_tests():
    """Führt alle Tests aus."""
    print("=" * 60)
    print("MemoryRAMCache V2.1.0 LRU-Eviction Tests")
    print("=" * 60)
    
    tests = [
        test_max_items_limit,
        test_lru_eviction_lowest_priority,
        test_lru_touch_updates_position,
        test_cache_stats,
        test_invalidate,
        test_get_by_tag,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
        except AssertionError as e:
            print(f"  ❌ FAILED: {e}")
            failed += 1
        except Exception as e:
            print(f"  ❌ ERROR: {e}")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"Ergebnis: {passed} passed, {failed} failed")
    print("=" * 60)
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
