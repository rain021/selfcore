"""
SelfCore Ollama Status Speed Fix -- Self-Test (4 items)
"""
import sys
import os
import time

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

PASS = 0
FAIL = 0
results = []

def test(name, condition, detail=""):
    global PASS, FAIL
    if condition:
        PASS += 1
        results.append(f"  [PASS] {name}")
    else:
        FAIL += 1
        results.append(f"  [FAIL] {name} -- {detail}")


# ═══════════════════════════════════════════════════════════════
# Test 1: check_ollama_status() completes in under 1 second
#         when Ollama is not installed
# ═══════════════════════════════════════════════════════════════
try:
    from analysis_engine import check_ollama_status, _ollama_status_cache

    # Clear cache to force a fresh check
    _ollama_status_cache["time"] = 0
    _ollama_status_cache["result"] = None

    t0 = time.time()
    status = check_ollama_status(force=True)
    t1 = time.time()
    elapsed = t1 - t0

    assert isinstance(status, dict)
    assert "installed" in status and "running" in status

    test("1. check_ollama_status() completes in {:.2f}s (< 1s)".format(elapsed),
         elapsed < 1.0,
         f"Took {elapsed:.2f}s")
except Exception as e:
    test("1. Status check speed", False, str(e))


# ═══════════════════════════════════════════════════════════════
# Test 2: Cached result returns instantly (< 0.01s) on second call
# ═══════════════════════════════════════════════════════════════
try:
    # First call already happened in test 1, cache should be warm
    t0 = time.time()
    status2 = check_ollama_status()  # Should hit cache
    t1 = time.time()
    cached_elapsed = t1 - t0

    # Result should be identical
    assert status2 == status, "Cached result differs from original"

    test("2. Cached result returns in {:.4f}s (< 0.01s)".format(cached_elapsed),
         cached_elapsed < 0.01,
         f"Took {cached_elapsed:.4f}s")
except Exception as e:
    test("2. Cache speed", False, str(e))


# ═══════════════════════════════════════════════════════════════
# Test 3: force=True bypasses cache (makes a real check)
# ═══════════════════════════════════════════════════════════════
try:
    # Record cache time before force call
    cache_time_before = _ollama_status_cache["time"]

    t0 = time.time()
    status3 = check_ollama_status(force=True)
    t1 = time.time()

    # Cache time should have been updated
    cache_time_after = _ollama_status_cache["time"]
    cache_updated = cache_time_after > cache_time_before or cache_time_after >= t0

    assert isinstance(status3, dict)
    test("3. force=True bypasses cache (cache updated: {})".format(cache_updated),
         cache_updated,
         f"before={cache_time_before:.2f}, after={cache_time_after:.2f}")
except Exception as e:
    test("3. Force bypass", False, str(e))


# ═══════════════════════════════════════════════════════════════
# Test 4: selfcore.py /api/ollama/status supports force parameter
# ═══════════════════════════════════════════════════════════════
try:
    sc_path = os.path.join(PROJECT_ROOT, "selfcore.py")
    with open(sc_path, "r", encoding="utf-8") as f:
        sc = f.read()

    # Find the /api/ollama/status handler
    idx = sc.index("/api/ollama/status")
    section = sc[idx:idx+300]

    assert "force" in section, "force parameter not handled in endpoint"
    assert "check_ollama_status(force=" in section, "force not passed to check_ollama_status"

    # Verify no start_ollama_if_needed in status handler
    status_handler_end = sc.index("elif", idx + 1)
    status_section = sc[idx:status_handler_end]
    has_start = "start_ollama_if_needed" in status_section
    assert not has_start, "Status endpoint should NOT call start_ollama_if_needed"

    test("4. /api/ollama/status supports force param, no auto-start", True)
except Exception as e:
    test("4. Endpoint force parameter", False, str(e))


# ═══════════════════════════════════════════════════════════════
# SUMMARY
# ═══════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("  SelfCore Ollama Speed Fix Self-Test Results")
print("=" * 60)
for r in results:
    print(r)
print("=" * 60)
print(f"  TOTAL: {PASS + FAIL} | PASS: {PASS} | FAIL: {FAIL}")
print("=" * 60)
if FAIL > 0:
    sys.exit(1)
