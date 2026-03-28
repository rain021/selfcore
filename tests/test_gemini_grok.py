"""
SelfCore — Gemini & Grok Platform Support Self-Test (12 Items)
═══════════════════════════════════════════════════════════════
Validates:
  1. Gemini JSON parser mock test
  2. Gemini HTML parser mock test
  3. Grok parser JSON test
  4. Grok parser unsupported format (PDF) test
  5. Chrome Extension manifest includes x.com/grok.com
  6. Chrome Extension content.js has Grok selectors
  7. API endpoints /api/analyze/gemini and /api/analyze/grok exist
  8. Analysis UI shows 4 import buttons + text paste
  9. Guide sections for all platforms (ChatGPT, Claude, Gemini, Grok)
  10. Multi-source merge handles 4 platforms
  11. All existing features still work (import integrity)
  12. Launcher script exists (setup_python.bat)
"""

import sys
import os
import json
import zipfile
import io

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
# Test 1: Gemini JSON parser mock test
# ═══════════════════════════════════════════════════════════════
try:
    from analysis_engine import parse_gemini_export

    # Create mock Google Takeout JSON (MyActivity format)
    mock_activities = [
        {
            "title": "Asked Gemini: What is machine learning?",
            "products": [{"name": "Gemini Apps"}],
            "time": "2025-01-15T10:00:00Z"
        },
        {
            "title": "Asked Gemini: Explain neural networks",
            "products": [{"name": "Gemini Apps"}],
            "time": "2025-01-15T11:00:00Z"
        },
        {
            "title": "Searched for cat videos",
            "products": [{"name": "YouTube"}],
            "time": "2025-01-15T12:00:00Z"
        }
    ]
    mock_json = json.dumps(mock_activities).encode("utf-8")

    # Create a ZIP with MyActivity.json
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("Takeout/My Activity/Gemini Apps/MyActivity.json", mock_json)
    zip_bytes = buf.getvalue()

    msgs = parse_gemini_export(zip_bytes)
    test("1. Gemini JSON parser — message count",
         len(msgs) == 2,
         f"Expected 2 messages, got {len(msgs)}")
    if len(msgs) >= 2:
        test("1b. Gemini JSON parser — prefix stripped",
             msgs[0]["text"] == "What is machine learning?",
             f"Got: {msgs[0]['text']}")
        test("1c. Gemini JSON parser — non-Gemini filtered out",
             all("cat videos" not in m["text"] for m in msgs),
             "YouTube entry should be filtered")
    else:
        test("1b. Gemini JSON parser — prefix stripped", False, "Not enough messages")
        test("1c. Gemini JSON parser — non-Gemini filtered", False, "Not enough messages")
except Exception as e:
    test("1. Gemini JSON parser", False, str(e))

# ═══════════════════════════════════════════════════════════════
# Test 2: Gemini HTML parser mock test
# ═══════════════════════════════════════════════════════════════
try:
    mock_html = b"""
    <html><body>
        <div class="content-cell mdl-cell">How to build a REST API</div>
        <div class="content-cell mdl-cell">Gemini Apps</div>
        <div class="content-cell mdl-cell">What are design patterns in Python</div>
        <div class="content-cell mdl-cell">ab</div>
    </body></html>
    """
    buf2 = io.BytesIO()
    with zipfile.ZipFile(buf2, "w") as zf:
        zf.writestr("Takeout/My Activity/Gemini Apps/MyActivity.html", mock_html)
    html_zip = buf2.getvalue()

    msgs_html = parse_gemini_export(html_zip)
    # Should get "How to build a REST API" and "What are design patterns in Python"
    # "Gemini Apps" is filtered, "ab" is too short (<3 chars)
    test("2. Gemini HTML parser — message count",
         len(msgs_html) == 2,
         f"Expected 2 messages, got {len(msgs_html)}")
    if len(msgs_html) >= 1:
        test("2b. Gemini HTML parser — content extracted",
             "REST API" in msgs_html[0]["text"],
             f"Got: {msgs_html[0]['text']}")
    else:
        test("2b. Gemini HTML parser — content extracted", False, "No messages parsed")
except Exception as e:
    test("2. Gemini HTML parser", False, str(e))

# ═══════════════════════════════════════════════════════════════
# Test 3: Grok parser JSON test
# ═══════════════════════════════════════════════════════════════
try:
    from analysis_engine import parse_grok_export

    mock_grok = [
        {
            "messages": [
                {"role": "user", "text": "What is quantum computing?", "timestamp": "2025-02-01T10:00:00Z"},
                {"role": "assistant", "text": "Quantum computing uses qubits...", "timestamp": "2025-02-01T10:00:05Z"},
                {"role": "user", "text": "How is it different from classical?", "timestamp": "2025-02-01T10:01:00Z"}
            ]
        }
    ]
    mock_grok_json = json.dumps(mock_grok).encode("utf-8")

    buf3 = io.BytesIO()
    with zipfile.ZipFile(buf3, "w") as zf:
        zf.writestr("data/grok_conversations.json", mock_grok_json)
    grok_zip = buf3.getvalue()

    msgs_grok = parse_grok_export(grok_zip)
    test("3. Grok JSON parser — user messages only",
         len(msgs_grok) == 2,
         f"Expected 2 user messages, got {len(msgs_grok)}")
    if len(msgs_grok) >= 1:
        test("3b. Grok JSON parser — text content",
             "quantum computing" in msgs_grok[0]["text"].lower(),
             f"Got: {msgs_grok[0]['text']}")
    else:
        test("3b. Grok JSON parser — text content", False, "No messages parsed")
except Exception as e:
    test("3. Grok JSON parser", False, str(e))

# ═══════════════════════════════════════════════════════════════
# Test 4: Grok parser unsupported format (PDF) test
# ═══════════════════════════════════════════════════════════════
try:
    pdf_bytes = b'%PDF-1.4 fake pdf content here'
    msgs_pdf = parse_grok_export(pdf_bytes)
    test("4. Grok PDF detection — returns empty",
         len(msgs_pdf) == 0,
         f"Expected 0 messages, got {len(msgs_pdf)}")
except Exception as e:
    test("4. Grok PDF detection", False, str(e))

# ═══════════════════════════════════════════════════════════════
# Test 5: Chrome Extension manifest includes x.com/grok.com
# ═══════════════════════════════════════════════════════════════
try:
    manifest_path = os.path.join(PROJECT_ROOT, "extension", "manifest.json")
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    matches = manifest.get("content_scripts", [{}])[0].get("matches", [])
    has_xcom = any("x.com" in m for m in matches)
    has_grok = any("grok.com" in m for m in matches)
    test("5a. Manifest includes x.com", has_xcom, f"matches: {matches}")
    test("5b. Manifest includes grok.com", has_grok, f"matches: {matches}")
except Exception as e:
    test("5. Chrome Extension manifest", False, str(e))

# ═══════════════════════════════════════════════════════════════
# Test 6: Chrome Extension content.js has Grok selectors
# ═══════════════════════════════════════════════════════════════
try:
    content_js_path = os.path.join(PROJECT_ROOT, "extension", "content.js")
    with open(content_js_path, "r", encoding="utf-8") as f:
        content_js = f.read()

    test("6a. content.js — Grok platform detection",
         'return "grok"' in content_js,
         "Missing grok platform return")
    test("6b. content.js — Grok input selectors",
         'case "grok"' in content_js,
         "Missing grok case in getInputField")
    test("6c. content.js — x.com hostname check",
         'x.com' in content_js,
         "Missing x.com hostname check")
except Exception as e:
    test("6. Chrome Extension content.js", False, str(e))

# ═══════════════════════════════════════════════════════════════
# Test 7: API endpoints exist in selfcore.py
# ═══════════════════════════════════════════════════════════════
try:
    selfcore_path = os.path.join(PROJECT_ROOT, "selfcore.py")
    with open(selfcore_path, "r", encoding="utf-8") as f:
        selfcore_code = f.read()

    test("7a. API endpoint /api/analyze/gemini",
         '/api/analyze/gemini' in selfcore_code,
         "Missing gemini endpoint")
    test("7b. API endpoint /api/analyze/grok",
         '/api/analyze/grok' in selfcore_code,
         "Missing grok endpoint")
    test("7c. Imports parse_gemini_export",
         'parse_gemini_export' in selfcore_code,
         "Missing import")
    test("7d. Imports parse_grok_export",
         'parse_grok_export' in selfcore_code,
         "Missing import")
except Exception as e:
    test("7. API endpoints", False, str(e))

# ═══════════════════════════════════════════════════════════════
# Test 8: Analysis UI shows 4 import buttons + text paste
# ═══════════════════════════════════════════════════════════════
try:
    page_path = os.path.join(PROJECT_ROOT, "app", "page.tsx")
    with open(page_path, "r", encoding="utf-8") as f:
        page_code = f.read()

    test("8a. UI — ChatGPT import button",
         'analysis.import.chatgpt' in page_code or 'chatgptAnalysisRef' in page_code,
         "Missing ChatGPT import")
    test("8b. UI — Claude import button",
         'analysis.import.claude' in page_code or 'claudeAnalysisRef' in page_code,
         "Missing Claude import")
    test("8c. UI — Gemini import button",
         'analysis.import.gemini' in page_code and 'geminiAnalysisRef' in page_code,
         "Missing Gemini import")
    test("8d. UI — Grok import button",
         'analysis.import.grok' in page_code and 'grokAnalysisRef' in page_code,
         "Missing Grok import")
    test("8e. UI — Text paste button",
         'analysis.import.text' in page_code or 'textPaste' in page_code.lower() or 'handleTextPaste' in page_code,
         "Missing text paste")
except Exception as e:
    test("8. Analysis UI buttons", False, str(e))

# ═══════════════════════════════════════════════════════════════
# Test 9: Guide sections for all platforms
# ═══════════════════════════════════════════════════════════════
try:
    i18n_path = os.path.join(PROJECT_ROOT, "lib", "i18n.ts")
    with open(i18n_path, "r", encoding="utf-8") as f:
        i18n_code = f.read()

    test("9a. i18n — ChatGPT guide keys",
         'analysis.guide.chatgpt.title' in i18n_code,
         "Missing ChatGPT guide")
    test("9b. i18n — Claude guide keys",
         'analysis.guide.claude.title' in i18n_code,
         "Missing Claude guide")
    test("9c. i18n — Gemini guide keys",
         'analysis.guide.gemini.title' in i18n_code,
         "Missing Gemini guide")
    test("9d. i18n — Grok guide keys",
         'analysis.guide.grok.title' in i18n_code,
         "Missing Grok guide")

    # Verify guide sections in page.tsx
    test("9e. UI — Gemini guide rendered",
         'analysis.guide.gemini.title' in page_code,
         "Missing Gemini guide in UI")
    test("9f. UI — Grok guide rendered",
         'analysis.guide.grok.title' in page_code,
         "Missing Grok guide in UI")
except Exception as e:
    test("9. Guide sections", False, str(e))

# ═══════════════════════════════════════════════════════════════
# Test 10: Multi-source merge handles 4 platforms
# ═══════════════════════════════════════════════════════════════
try:
    from analysis_engine import merge_analysis_results

    mock_results = [
        {
            "source": "chatgpt",
            "entities": {
                "tech": [{"name": "Python", "count": 5}],
                "people": [],
                "orgs": [{"name": "Google", "count": 2}]
            },
            "preferences": [{"target": "vim", "sentiment": "positive"}],
            "stats": {"total_messages": 100}
        },
        {
            "source": "claude",
            "entities": {
                "tech": [{"name": "Python", "count": 3}, {"name": "Rust", "count": 2}],
                "people": [],
                "orgs": []
            },
            "preferences": [],
            "stats": {"total_messages": 50}
        },
        {
            "source": "gemini",
            "entities": {
                "tech": [{"name": "JavaScript", "count": 4}],
                "people": [{"name": "Linus Torvalds", "count": 1}],
                "orgs": []
            },
            "preferences": [{"target": "tabs", "sentiment": "positive"}],
            "stats": {"total_messages": 30}
        },
        {
            "source": "grok",
            "entities": {
                "tech": [{"name": "python", "count": 2}],  # lowercase to test dedup
                "people": [],
                "orgs": [{"name": "Google", "count": 1}]
            },
            "preferences": [],
            "stats": {"total_messages": 20}
        }
    ]

    merged = merge_analysis_results(mock_results)

    # Python should be merged: 5+3+2 = 10
    tech_names = {t["name"].lower(): t["count"] for t in merged["entities"]["tech"]}
    test("10a. Merge — Python count aggregated",
         tech_names.get("python", 0) == 10,
         f"Expected 10, got {tech_names.get('python', 0)}")

    test("10b. Merge — Rust preserved",
         "rust" in tech_names,
         "Rust missing from merged tech")

    test("10c. Merge — JavaScript from Gemini",
         "javascript" in tech_names,
         "JavaScript missing from merged tech")

    test("10d. Merge — Google org deduped",
         len(merged["entities"]["orgs"]) == 1,
         f"Expected 1 org, got {len(merged['entities']['orgs'])}")

    test("10e. Merge — total messages",
         merged["stats"]["total_messages"] == 200,
         f"Expected 200, got {merged['stats']['total_messages']}")

    test("10f. Merge — preferences from multiple sources",
         len(merged["preferences"]) == 2,
         f"Expected 2 prefs, got {len(merged['preferences'])}")
except Exception as e:
    test("10. Multi-source merge", False, str(e))

# ═══════════════════════════════════════════════════════════════
# Test 11: All existing features still work (import integrity)
# ═══════════════════════════════════════════════════════════════
try:
    from analysis_engine import (
        parse_chatgpt_export,
        parse_claude_export,
        parse_text_paste,
        parse_gemini_export as _ge,
        parse_grok_export as _gk,
        merge_analysis_results as _mr,
        extract_entities,
        extract_preferences,
        extract_topics,
        detect_language,
    )
    test("11a. Import — all parsers importable", True)
    test("11b. Import — NLP functions importable", True)

    # Quick text paste parse test
    test_msgs = parse_text_paste("User: I love Python\nAssistant: Great choice!")
    test("11c. Text paste parser still works",
         len(test_msgs) >= 1,
         f"Got {len(test_msgs)} messages")

    # Quick language detection test
    lang = detect_language("Hello, how are you today?")
    test("11d. Language detection still works",
         lang in ("en", "unknown"),
         f"Got: {lang}")
except Exception as e:
    test("11. Import integrity", False, str(e))

# ═══════════════════════════════════════════════════════════════
# Test 12: Launcher script exists
# ═══════════════════════════════════════════════════════════════
try:
    bat_path = os.path.join(PROJECT_ROOT, "setup_python.bat")
    pkg_path = os.path.join(PROJECT_ROOT, "package.json")
    main_path = os.path.join(PROJECT_ROOT, "main.js")

    test("12a. setup_python.bat exists",
         os.path.isfile(bat_path),
         "Missing setup_python.bat")
    test("12b. package.json exists",
         os.path.isfile(pkg_path),
         "Missing package.json")
    test("12c. main.js exists",
         os.path.isfile(main_path),
         "Missing main.js")

    # Verify package.json has start script
    with open(pkg_path, "r", encoding="utf-8") as f:
        pkg = json.load(f)
    test("12d. package.json has dev script",
         "app:dev" in pkg.get("scripts", {}) or "dev" in pkg.get("scripts", {}),
         "Missing dev/app:dev script")
except Exception as e:
    test("12. Launcher files", False, str(e))


# ═══════════════════════════════════════════════════════════════
# Summary
# ═══════════════════════════════════════════════════════════════
import sys as _sys
_sys.stdout.reconfigure(encoding="utf-8", errors="replace")

print()
print("=" * 60)
print("  SelfCore -- Gemini & Grok Self-Test Results")
print("=" * 60)
for r in results:
    print(r)
print("-" * 60)
print(f"  Total: {PASS + FAIL}  |  PASS: {PASS}  |  FAIL: {FAIL}")
print("=" * 60)

if FAIL > 0:
    sys.exit(1)
