"""
SelfCore Phase 4A Self-Test — 18 Test Items
"""
import sys
import os
import json
import zipfile
import io
import tempfile

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
# Test 1: spaCy en_core_web_sm loads
# ═══════════════════════════════════════════════════════════
try:
    import spacy
    nlp_en = spacy.load("en_core_web_sm")
    test("1. spaCy en_core_web_sm loads", nlp_en is not None)
except Exception as e:
    test("1. spaCy en_core_web_sm loads", False, str(e))

# ═══════════════════════════════════════════════════════════
# Test 2: spaCy ko_core_news_sm loads
# ═══════════════════════════════════════════════════════════
try:
    nlp_ko = spacy.load("ko_core_news_sm")
    test("2. spaCy ko_core_news_sm loads", nlp_ko is not None)
except Exception as e:
    test("2. spaCy ko_core_news_sm loads", False, str(e))

# ═══════════════════════════════════════════════════════════
# Test 3: tech_dictionary.json loads with 200+ patterns
# ═══════════════════════════════════════════════════════════
try:
    from analysis_engine import load_tech_dictionary
    td = load_tech_dictionary()
    pattern_count = len(td.get("patterns", []))
    test("3. tech_dictionary.json 200+ patterns", pattern_count >= 200,
         f"Only {pattern_count} patterns found")
except Exception as e:
    test("3. tech_dictionary.json 200+ patterns", False, str(e))

# ═══════════════════════════════════════════════════════════
# Test 4: korean_stopwords.json loads
# ═══════════════════════════════════════════════════════════
try:
    from analysis_engine import load_korean_stopwords
    ksw = load_korean_stopwords()
    test("4. korean_stopwords.json loads", isinstance(ksw, list) and len(ksw) > 30,
         f"Got {len(ksw)} stopwords")
except Exception as e:
    test("4. korean_stopwords.json loads", False, str(e))

# ═══════════════════════════════════════════════════════════
# Test 5: injection_blacklist.json loads
# ═══════════════════════════════════════════════════════════
try:
    from analysis_engine import load_injection_blacklist
    bl = load_injection_blacklist()
    test("5. injection_blacklist.json loads", isinstance(bl, list) and len(bl) > 10,
         f"Got {len(bl)} patterns")
except Exception as e:
    test("5. injection_blacklist.json loads", False, str(e))

# ═══════════════════════════════════════════════════════════
# Test 6: ChatGPT parser DAG backward traversal
# ═══════════════════════════════════════════════════════════
try:
    from analysis_engine import parse_chatgpt_export

    # Create test conversations.json with DAG structure
    test_conversations = [{
        "title": "Test conversation",
        "current_node": "node3",
        "mapping": {
            "root": {
                "id": "root",
                "parent": None,
                "message": None
            },
            "node1": {
                "id": "node1",
                "parent": "root",
                "message": {
                    "author": {"role": "user"},
                    "content": {"parts": ["Hello, I love Python programming"]},
                    "create_time": 1700000000
                }
            },
            "node2": {
                "id": "node2",
                "parent": "node1",
                "message": {
                    "author": {"role": "assistant"},
                    "content": {"parts": ["Hello! Python is great."]}
                }
            },
            "node3": {
                "id": "node3",
                "parent": "node2",
                "message": {
                    "author": {"role": "user"},
                    "content": {"parts": ["Tell me about React", {"type": "image"}]},
                    "create_time": 1700001000
                }
            }
        }
    }]

    # Create zip in memory
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("conversations.json", json.dumps(test_conversations))
    buf.seek(0)

    msgs = parse_chatgpt_export(buf.read())
    user_msgs = [m for m in msgs if m["role"] == "user"]
    test("6. ChatGPT DAG parser extracts user messages only",
         len(user_msgs) == 2 and "Python" in user_msgs[0]["text"] and "React" in user_msgs[1]["text"],
         f"Got {len(user_msgs)} messages: {[m['text'][:30] for m in user_msgs]}")
except Exception as e:
    test("6. ChatGPT DAG parser", False, str(e))

# ═══════════════════════════════════════════════════════════
# Test 7: Claude parser
# ═══════════════════════════════════════════════════════════
try:
    from analysis_engine import parse_claude_export

    test_claude_data = [
        {
            "uuid": "test-conv",
            "name": "Test",
            "chat_messages": [
                {"sender": "human", "text": "I prefer TypeScript for web dev", "created_at": "2024-01-01T10:00:00"},
                {"sender": "assistant", "text": "TypeScript is popular!", "created_at": "2024-01-01T10:01:00"},
                {"sender": "human", "text": "How about FastAPI?", "created_at": "2024-01-01T10:02:00"}
            ]
        }
    ]

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("conversations.json", json.dumps(test_claude_data))
    buf.seek(0)

    msgs = parse_claude_export(buf.read())
    human_msgs = [m for m in msgs if m["role"] == "user"]
    test("7. Claude parser extracts human messages only",
         len(human_msgs) == 2 and "TypeScript" in human_msgs[0]["text"],
         f"Got {len(human_msgs)} messages")
except Exception as e:
    test("7. Claude parser", False, str(e))

# ═══════════════════════════════════════════════════════════
# Test 8: Text paste parser (conversation mode)
# ═══════════════════════════════════════════════════════════
try:
    from analysis_engine import parse_text_paste

    conv_text = "User: hello\nAssistant: hi\nUser: how are you"
    msgs = parse_text_paste(conv_text)
    user_msgs = [m for m in msgs if m["role"] == "user"]
    test("8. Text paste parser conversation mode",
         len(user_msgs) == 2 and "hello" in user_msgs[0]["text"],
         f"Got {len(user_msgs)} user messages: {[m['text'] for m in user_msgs]}")
except Exception as e:
    test("8. Text paste parser conversation mode", False, str(e))

# ═══════════════════════════════════════════════════════════
# Test 9: Text paste parser (free text mode)
# ═══════════════════════════════════════════════════════════
try:
    plain_text = "I have been working on a React project with TypeScript for the last few months."
    msgs = parse_text_paste(plain_text)
    test("9. Text paste parser free text mode",
         len(msgs) == 1 and msgs[0]["text"] == plain_text.strip(),
         f"Got {len(msgs)} messages")
except Exception as e:
    test("9. Text paste parser free text mode", False, str(e))

# ═══════════════════════════════════════════════════════════
# Test 10: Entity extraction (React + TypeScript detection)
# ═══════════════════════════════════════════════════════════
try:
    from analysis_engine import extract_entities

    test_texts = ["React 컴포넌트를 리팩토링하고 TypeScript로 마이그레이션했어"]
    entities = extract_entities(test_texts)
    tech_names = [t["name"] for t in entities.get("tech", [])]
    has_react = any("React" in n for n in tech_names)
    has_ts = any("TypeScript" in n for n in tech_names)
    test("10. Entity extraction: React + TypeScript detected",
         has_react and has_ts,
         f"Found tech: {tech_names}")
except Exception as e:
    test("10. Entity extraction", False, str(e))

# ═══════════════════════════════════════════════════════════
# Test 11: Short term context check (Go)
# ═══════════════════════════════════════════════════════════
try:
    # "Go language" should detect Go
    texts_good = ["Go language is great for concurrent programming"]
    ents_good = extract_entities(texts_good)
    tech_good = [t["name"] for t in ents_good.get("tech", [])]
    has_go_good = "Go" in tech_good

    # "I want to go home" should NOT detect Go
    texts_bad = ["I want to go home and rest"]
    ents_bad = extract_entities(texts_bad)
    tech_bad = [t["name"] for t in ents_bad.get("tech", [])]
    has_go_bad = "Go" in tech_bad

    test("11. Short term context: Go detection",
         has_go_good and not has_go_bad,
         f"'Go language': {tech_good}, 'go home': {tech_bad}")
except Exception as e:
    test("11. Short term context: Go detection", False, str(e))

# ═══════════════════════════════════════════════════════════
# Test 12: Preference extraction
# ═══════════════════════════════════════════════════════════
try:
    from analysis_engine import extract_preferences

    pref_texts = [
        "Python 정말 좋아해. Python is my favorite language.",
        "Java는 별로야. Java is terrible for quick prototyping."
    ]
    pref_entities = extract_entities(pref_texts)
    prefs = extract_preferences(pref_texts, pref_entities)
    pref_dict = {p["target"]: p["sentiment"] for p in prefs}

    python_like = pref_dict.get("Python") == "Like"
    java_dislike = pref_dict.get("Java") == "Dislike"

    test("12. Preference extraction: Python=Like, Java=Dislike",
         python_like and java_dislike,
         f"Got preferences: {pref_dict}")
except Exception as e:
    test("12. Preference extraction", False, str(e))

# ═══════════════════════════════════════════════════════════
# Test 13: Language detection
# ═══════════════════════════════════════════════════════════
try:
    from analysis_engine import detect_language

    ko_result = detect_language("리팩토링했어")
    en_result = detect_language("I refactored the code")
    test("13. Language detection: ko/en",
         ko_result == "ko" and en_result == "en",
         f"'리팩토링했어'={ko_result}, 'I refactored'={en_result}")
except Exception as e:
    test("13. Language detection", False, str(e))

# ═══════════════════════════════════════════════════════════
# Test 14: Sanitization
# ═══════════════════════════════════════════════════════════
try:
    from analysis_engine import sanitize_profile_data

    test_profile = {
        "identity": {"name": "Test <|im_start|>User"},
        "tags": ["normal <div>tag</div>", "inject <system>hack</system>"]
    }
    sanitized = sanitize_profile_data(test_profile)
    name_clean = "<|im_start|>" not in sanitized["identity"]["name"]
    div_preserved = "<div>" in sanitized["tags"][0]
    system_removed = "<system>" not in sanitized["tags"][1]

    test("14. Sanitization: blacklist removed, HTML preserved",
         name_clean and div_preserved and system_removed,
         f"name_clean={name_clean}, div_preserved={div_preserved}, system_removed={system_removed}")
except Exception as e:
    test("14. Sanitization", False, str(e))

# ═══════════════════════════════════════════════════════════
# Test 15: API endpoints return valid JSON (structural check)
# ═══════════════════════════════════════════════════════════
try:
    # We can't actually hit the server, but verify the imports work
    from analysis_engine import run_full_analysis, merge_analysis_results, get_progress
    result = run_full_analysis([])
    assert "entities" in result
    assert "preferences" in result
    assert "stats" in result
    merged = merge_analysis_results([])
    assert "entities" in merged
    progress = get_progress()
    assert "status" in progress
    test("15. API endpoint functions return valid structure", True)
except Exception as e:
    test("15. API endpoint functions", False, str(e))

# ═══════════════════════════════════════════════════════════
# Test 16: i18n keys exist for Analysis tab
# ═══════════════════════════════════════════════════════════
try:
    i18n_path = os.path.join(PROJECT_ROOT, "lib", "i18n.ts")
    with open(i18n_path, "r", encoding="utf-8") as f:
        i18n_content = f.read()
    required_keys = [
        "analysis.title", "analysis.import.chatgpt", "analysis.import.claude",
        "analysis.import.text", "analysis.results.techStack", "analysis.results.preferences",
        "analysis.apply", "analysis.rerun", "analysis.guide.chatgpt.title",
        "analysis.guide.claude.title"
    ]
    all_found = all(k in i18n_content for k in required_keys)
    missing = [k for k in required_keys if k not in i18n_content]
    test("16. i18n keys for Analysis tab (KO+EN)",
         all_found,
         f"Missing: {missing}" if missing else "")
except Exception as e:
    test("16. i18n keys", False, str(e))

# ═══════════════════════════════════════════════════════════
# Test 17: Existing Phase 1-3 features (structural check)
# ═══════════════════════════════════════════════════════════
try:
    # Check selfcore.py still has all original endpoints
    sc_path = os.path.join(PROJECT_ROOT, "selfcore.py")
    with open(sc_path, "r", encoding="utf-8") as f:
        sc_content = f.read()
    required_endpoints = [
        "/api/health", "/api/profile", "/api/profiles", "/api/context",
        "/api/settings", "/api/activity", "/api/patterns", "/api/analyze",
        "/api/suggestions", "/api/weekly", "/api/injections",
        "/api/export", "/api/import", "/api/import/chatgpt", "/api/import/text",
        "/api/injection/log", "/api/suggestions/apply", "/api/activity/purge"
    ]
    all_present = all(ep in sc_content for ep in required_endpoints)
    missing_ep = [ep for ep in required_endpoints if ep not in sc_content]
    test("17. Phase 1-3 endpoints preserved",
         all_present,
         f"Missing: {missing_ep}" if missing_ep else "")
except Exception as e:
    test("17. Phase 1-3 features", False, str(e))

# ═══════════════════════════════════════════════════════════
# Test 18: SelfCore.vbs exists and is correct
# ═══════════════════════════════════════════════════════════
try:
    vbs_path = r"C:\Users\user\Desktop\SelfCore.vbs"
    exists = os.path.exists(vbs_path)
    if exists:
        with open(vbs_path, "r") as f:
            content = f.read()
        has_selfcore = "SelfCore" in content
        has_py = "selfcore.py" in content
        test("18. SelfCore.vbs launcher works",
             has_selfcore and has_py,
             f"Content check: SelfCore={has_selfcore}, py={has_py}")
    else:
        test("18. SelfCore.vbs launcher works", False, "File not found")
except Exception as e:
    test("18. SelfCore.vbs launcher", False, str(e))

# ═══════════════════════════════════════════════════════════
# SUMMARY
# ═══════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("  SelfCore Phase 4A Self-Test Results")
print("=" * 60)
for r in results:
    print(r)
print("=" * 60)
print(f"  TOTAL: {PASS + FAIL} | PASS: {PASS} | FAIL: {FAIL}")
print("=" * 60)
if FAIL > 0:
    sys.exit(1)
