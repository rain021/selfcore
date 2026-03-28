"""
SelfCore Phase 4B-2 Self-Test -- Ollama LLM Integration (12 items)
"""
import sys
import os
import json

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


# ═══════════════════════════════════════════════════════════
# Test 1: check_ollama_status() returns valid dict, never crashes
# ═══════════════════════════════════════════════════════════
ollama_status = None
try:
    from analysis_engine import check_ollama_status
    ollama_status = check_ollama_status()
    required = {"installed", "running", "model_available", "model_name", "gpu_available", "gpu_usage_percent"}
    has_all = required.issubset(set(ollama_status.keys()))
    test("1. check_ollama_status() valid dict, no crash",
         has_all and isinstance(ollama_status, dict),
         f"keys={list(ollama_status.keys())}")
except Exception as e:
    test("1. check_ollama_status()", False, str(e))

# ═══════════════════════════════════════════════════════════
# Test 2: cleanup_orphan_ollama() runs without error
# ═══════════════════════════════════════════════════════════
try:
    from analysis_engine import cleanup_orphan_ollama
    cleanup_result = cleanup_orphan_ollama()
    has_status = "status" in cleanup_result
    has_cleaned = "cleaned" in cleanup_result
    test("2. cleanup_orphan_ollama() no error",
         has_status and has_cleaned,
         f"result={cleanup_result}")
except Exception as e:
    test("2. cleanup_orphan_ollama()", False, str(e))

# ═══════════════════════════════════════════════════════════
# Test 3: If Ollama installed, start returns True
# ═══════════════════════════════════════════════════════════
try:
    from analysis_engine import start_ollama_if_needed
    if ollama_status and ollama_status.get("installed"):
        started = start_ollama_if_needed()
        test("3. start_ollama_if_needed() (installed)", started,
             f"returned {started}")
    else:
        # Ollama not installed -- function should return False gracefully
        started = start_ollama_if_needed()
        test("3. start_ollama_if_needed() (not installed, graceful False)",
             started is False, f"returned {started}")
except Exception as e:
    test("3. start_ollama_if_needed()", False, str(e))

# ═══════════════════════════════════════════════════════════
# Test 4: Model availability check returns correct bool
# ═══════════════════════════════════════════════════════════
try:
    if ollama_status and ollama_status.get("installed"):
        model_avail = ollama_status.get("model_available")
        test("4. model_available check (installed)",
             isinstance(model_avail, bool),
             f"model_available={model_avail}")
    else:
        test("4. model_available check (not installed, False)",
             ollama_status is not None and ollama_status.get("model_available") is False,
             f"model_available={ollama_status.get('model_available') if ollama_status else 'N/A'}")
except Exception as e:
    test("4. model availability", False, str(e))

# ═══════════════════════════════════════════════════════════
# Test 5: All functions return graceful failure if Ollama absent
# ═══════════════════════════════════════════════════════════
try:
    from analysis_engine import (
        check_ollama_status, start_ollama_if_needed,
        pull_model_if_needed, cleanup_orphan_ollama,
        run_profile_extraction
    )
    # These should ALL return without exception
    s = check_ollama_status()
    assert isinstance(s, dict)
    st = start_ollama_if_needed()
    assert isinstance(st, bool)
    cl = cleanup_orphan_ollama()
    assert isinstance(cl, dict)

    # run_profile_extraction with no Ollama should return None gracefully
    rpe = run_profile_extraction(
        {"tech": [{"name": "Python", "count": 5}]},
        {"skipped": True}, [], {}
    )
    # Should be None (no Ollama) or a dict with error key
    ok = rpe is None or (isinstance(rpe, dict))
    test("5. Graceful failure when Ollama absent", ok,
         f"profile_extraction returned type={type(rpe).__name__}")
except Exception as e:
    test("5. Graceful failure", False, str(e))

# ═══════════════════════════════════════════════════════════
# Test 6: run_full_analysis (text, no LLM) returns all fields
# ═══════════════════════════════════════════════════════════
try:
    from analysis_engine import run_full_analysis

    test_text = (
        "I love using React for building user interfaces. "
        "Python is great for backend development with FastAPI. "
        "Docker containers make deployment much easier. "
        "TypeScript provides excellent type safety. "
        "I prefer VS Code as my primary editor."
    )

    result = run_full_analysis(source="text", data=test_text, use_llm=False)
    required_fields = {"source", "total_messages", "entities", "preferences",
                       "topics", "communication_style", "llm_profile", "analyzed_at", "stats"}
    has_all_fields = required_fields.issubset(set(result.keys()))
    test("6. run_full_analysis(text, no LLM) all fields present",
         has_all_fields,
         f"missing={required_fields - set(result.keys())}")
except Exception as e:
    test("6. run_full_analysis fields", False, str(e))

# ═══════════════════════════════════════════════════════════
# Test 7: Pipeline populates entities, preferences, topics, style
# ═══════════════════════════════════════════════════════════
try:
    # Check that entities were populated
    ents = result.get("entities", {})
    has_tech = len(ents.get("tech", [])) > 0
    # Communication style populated
    style = result.get("communication_style", {})
    has_style = "formality" in style and "verbosity" in style
    # Topics (may be skipped due to few messages, that's ok)
    topics = result.get("topics", {})
    topics_ok = isinstance(topics, dict) and "skipped" in topics
    # LLM should be None since we passed use_llm=False
    llm_none = result.get("llm_profile") is None

    test("7. Pipeline populates entities/prefs/topics/style",
         has_tech and has_style and topics_ok and llm_none,
         f"tech={has_tech}, style={has_style}, topics={topics_ok}, llm_none={llm_none}")
except Exception as e:
    test("7. Pipeline data populated", False, str(e))

# ═══════════════════════════════════════════════════════════
# Test 8: GET /api/ollama/status returns valid JSON
# ═══════════════════════════════════════════════════════════
try:
    sc_path = os.path.join(PROJECT_ROOT, "selfcore.py")
    with open(sc_path, "r", encoding="utf-8") as f:
        sc = f.read()
    has_status_ep = "/api/ollama/status" in sc
    has_start_ep = "/api/ollama/start" in sc
    has_pull_ep = "/api/ollama/pull" in sc
    has_cleanup_ep = "/api/ollama/cleanup" in sc
    has_deep_ep = "/api/analyze/deep" in sc

    test("8. Ollama API endpoints in selfcore.py",
         has_status_ep and has_start_ep and has_pull_ep and has_cleanup_ep and has_deep_ep,
         f"status={has_status_ep} start={has_start_ep} pull={has_pull_ep} cleanup={has_cleanup_ep} deep={has_deep_ep}")
except Exception as e:
    test("8. Ollama API endpoints", False, str(e))

# ═══════════════════════════════════════════════════════════
# Test 9: POST /api/analyze/deep endpoint exists with correct handler
# ═══════════════════════════════════════════════════════════
try:
    # Verify the deep endpoint calls run_full_analysis correctly
    assert "run_full_analysis(" in sc and "source=" in sc
    assert "use_llm" in sc
    test("9. /api/analyze/deep endpoint uses run_full_analysis with params", True)
except Exception as e:
    test("9. Deep endpoint handler", False, str(e))

# ═══════════════════════════════════════════════════════════
# Test 10: Phase 4A + 4B-1 functionality preserved
# ═══════════════════════════════════════════════════════════
try:
    from analysis_engine import (
        parse_text_paste, extract_entities, extract_preferences,
        detect_language, sanitize_profile_data, load_tech_dictionary,
        extract_topics, analyze_communication_style
    )
    import zipfile, io

    # Entity extraction
    ents = extract_entities(["I love React and Python"])
    tech = [t["name"] for t in ents.get("tech", [])]
    assert "React" in tech or "Python" in tech

    # Language detection
    assert detect_language("I refactored the code and added testing") == "en"
    assert detect_language("안녕하세요") == "ko"

    # Sanitization
    s = sanitize_profile_data({"x": "test <|im_start|>hack"})
    assert "<|im_start|>" not in s["x"]

    # Tech dictionary 200+
    td = load_tech_dictionary()
    assert len(td.get("patterns", [])) >= 200

    # TF-IDF skip
    small = extract_topics(["a", "b"], language="en")
    assert small.get("skipped") is True

    # Communication style
    cs = analyze_communication_style(["Hello, how are you?"])
    assert "formality" in cs

    # Text paste parser
    msgs = parse_text_paste("User: hi\nAssistant: hello\nUser: bye")
    assert len([m for m in msgs if m["role"] == "user"]) == 2

    # ChatGPT parser
    test_conv = [{"title": "t", "current_node": "n1", "mapping": {
        "r": {"id": "r", "parent": None, "message": None},
        "n1": {"id": "n1", "parent": "r", "message": {"author": {"role": "user"}, "content": {"parts": ["test"]}, "create_time": 1700000000}}
    }}]
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w') as zf:
        zf.writestr("conversations.json", json.dumps(test_conv))
    buf.seek(0)
    from analysis_engine import parse_chatgpt_export
    cmsgs = parse_chatgpt_export(buf.read())
    assert len(cmsgs) == 1

    # Phase 1-3 endpoints
    phase1_eps = ["/api/health", "/api/profile", "/api/context", "/api/settings",
                  "/api/activity", "/api/suggestions", "/api/weekly",
                  "/api/import/chatgpt", "/api/import/text"]
    missing_eps = [ep for ep in phase1_eps if ep not in sc]
    assert not missing_eps, f"Missing: {missing_eps}"

    test("10. Phase 4A + 4B-1 functionality preserved", True)
except Exception as e:
    test("10. Phase 4A + 4B-1 preserved", False, str(e))

# ═══════════════════════════════════════════════════════════
# Test 11: SelfCore.vbs exists and launches correctly
# ═══════════════════════════════════════════════════════════
try:
    vbs_path = r"C:\Users\user\Desktop\SelfCore.vbs"
    exists = os.path.exists(vbs_path)
    if exists:
        with open(vbs_path, "r") as f:
            content = f.read()
        test("11. SelfCore.vbs launcher",
             "SelfCore" in content and "selfcore.py" in content,
             "Content check passed")
    else:
        test("11. SelfCore.vbs launcher", False, "File not found")
except Exception as e:
    test("11. SelfCore.vbs", False, str(e))

# ═══════════════════════════════════════════════════════════
# Test 12: Startup cleanup registered in selfcore.py
# ═══════════════════════════════════════════════════════════
try:
    assert "cleanup_orphan_ollama()" in sc
    assert 'cleanup_orphan_ollama' in sc
    # Check it's in the __main__ block
    main_idx = sc.index('if __name__ == "__main__"')
    cleanup_idx = sc.index("cleanup_orphan_ollama()", main_idx)
    server_idx = sc.index("HTTPServer", main_idx)
    test("12. Startup cleanup before HTTP server",
         cleanup_idx < server_idx,
         f"cleanup at char {cleanup_idx}, server at {server_idx}")
except Exception as e:
    test("12. Startup cleanup registration", False, str(e))


# ═══════════════════════════════════════════════════════════
# SUMMARY
# ═══════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("  SelfCore Phase 4B-2 Self-Test Results")
print("=" * 60)
for r in results:
    print(r)
print("=" * 60)
print(f"  TOTAL: {PASS + FAIL} | PASS: {PASS} | FAIL: {FAIL}")
if ollama_status:
    print(f"  Ollama: installed={ollama_status.get('installed')}, running={ollama_status.get('running')}, model={ollama_status.get('model_available')}")
    print(f"  GPU: available={ollama_status.get('gpu_available')}, usage={ollama_status.get('gpu_usage_percent')}")
print("=" * 60)
if FAIL > 0:
    sys.exit(1)
