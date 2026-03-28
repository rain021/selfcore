"""
SelfCore Phase 4B-1 Self-Test -- TF-IDF + Communication Style (8 items)
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
# Test 1: TF-IDF with 25+ messages about programming
# ═══════════════════════════════════════════════════════════
try:
    from analysis_engine import extract_topics

    # Generate 30 programming-related test messages
    test_msgs = [
        "I need to refactor my React components to use hooks instead of class components",
        "The Python backend is handling API requests with FastAPI and it works great",
        "We should add TypeScript to the React project for better type safety",
        "Docker containers make deployment much easier on our Kubernetes cluster",
        "The database queries in PostgreSQL need optimization for better performance",
        "I wrote a Python script to automate the CI/CD pipeline using GitHub Actions",
        "React hooks like useState and useEffect simplified our component architecture",
        "The FastAPI endpoints need proper authentication with JWT tokens",
        "We deployed the Docker containers to AWS and configured load balancing",
        "TypeScript interfaces help catch bugs at compile time in our React app",
        "Python pandas library is great for data analysis and manipulation",
        "The React frontend communicates with the Python backend via REST API",
        "Kubernetes pods auto-scale based on CPU usage in our AWS cluster",
        "I prefer Python for backend development because of its clean syntax",
        "The React component tree is getting complex, we need state management",
        "Docker compose simplifies our local development environment setup",
        "FastAPI automatic documentation with Swagger is really helpful",
        "PostgreSQL full-text search is powerful for our search feature",
        "The Python test suite uses pytest with good coverage metrics",
        "React server components in Next.js reduce client-side JavaScript",
        "TypeScript generics are powerful but sometimes hard to understand",
        "We use Docker multi-stage builds to reduce image size",
        "The Python async features with FastAPI handle concurrent requests well",
        "React context API helped us avoid prop drilling in deep component trees",
        "Our Kubernetes deployment uses Helm charts for consistent configuration",
        "PostgreSQL JSON columns store flexible data alongside relational tables",
        "The Python logging module helps with debugging production issues",
        "React testing library makes writing component tests much easier",
        "Docker networking allows containers to communicate securely",
        "FastAPI dependency injection keeps our code clean and testable",
    ]

    topic_result = extract_topics(test_msgs, language="en")
    has_keywords = not topic_result.get("skipped", True) and len(topic_result.get("top_keywords", [])) > 0
    # Check that repeated terms like 'react', 'python', 'docker' appear
    kw_words = [kw["word"] for kw in topic_result.get("top_keywords", [])]
    has_repeat = any(kw.get("count", 0) >= 3 for kw in topic_result.get("top_keywords", []))

    test("1. TF-IDF 25+ msgs: valid top_keywords with count>=3",
         has_keywords and has_repeat,
         f"skipped={topic_result.get('skipped')}, keywords={kw_words[:5]}, counts={[kw.get('count') for kw in topic_result.get('top_keywords', [])[:5]]}")
except Exception as e:
    test("1. TF-IDF 25+ messages", False, str(e))

# ═══════════════════════════════════════════════════════════
# Test 2: TF-IDF with 5 messages -> skipped
# ═══════════════════════════════════════════════════════════
try:
    small_msgs = ["Hello world", "Python is great", "React hooks", "Testing code", "Final message"]
    result_small = extract_topics(small_msgs, language="en")
    test("2. TF-IDF 5 msgs: skipped=True",
         result_small.get("skipped") is True and result_small.get("reason") == "insufficient_data",
         f"Got: {result_small}")
except Exception as e:
    test("2. TF-IDF 5 messages skipped", False, str(e))

# ═══════════════════════════════════════════════════════════
# Test 3: TF-IDF with Korean messages (stopwords filtered)
# ═══════════════════════════════════════════════════════════
try:
    ko_msgs = [
        "React 컴포넌트를 리팩토링하고 있습니다",
        "Python으로 백엔드 API를 개발하고 있습니다",
        "TypeScript로 타입 안전성을 확보했습니다",
        "Docker 컨테이너로 배포합니다",
        "PostgreSQL 데이터베이스를 사용합니다",
        "React 훅을 사용해서 상태 관리를 합니다",
        "Python FastAPI로 REST API를 만들었습니다",
        "Kubernetes 클러스터에 배포했습니다",
        "React 컴포넌트 테스트를 작성합니다",
        "Python 스크립트로 자동화했습니다",
        "Docker 이미지를 빌드합니다",
        "TypeScript 인터페이스를 정의합니다",
        "React 성능을 최적화합니다",
        "Python 라이브러리를 설치합니다",
        "PostgreSQL 쿼리를 최적화합니다",
        "React Native로 모바일 앱을 만듭니다",
        "Python 비동기 프로그래밍을 합니다",
        "Docker Compose로 환경을 구성합니다",
        "React 상태 관리가 중요합니다",
        "Python 테스트 코드를 작성합니다",
        "TypeScript 제네릭을 사용합니다",
        "React 서버 컴포넌트를 구현합니다",
    ]

    ko_result = extract_topics(ko_msgs, language="ko")
    # Korean stopwords like "있습니다", "합니다" should be filtered out
    ko_words = [kw["word"] for kw in ko_result.get("top_keywords", [])]
    # "합니다" and "있습니다" should NOT be in top keywords
    stopword_leaked = any(w in ko_words for w in ["합니다", "있습니다", "됩니다"])
    has_tech = any(w.lower() in ["react", "python", "typescript", "docker"] for w in ko_words)

    test("3. TF-IDF Korean: stopwords filtered, tech terms found",
         not ko_result.get("skipped") and not stopword_leaked and has_tech,
         f"skipped={ko_result.get('skipped')}, stopword_leak={stopword_leaked}, words={ko_words[:8]}")
except Exception as e:
    test("3. TF-IDF Korean stopwords", False, str(e))

# ═══════════════════════════════════════════════════════════
# Test 4: Communication style with formal messages
# ═══════════════════════════════════════════════════════════
try:
    from analysis_engine import analyze_communication_style

    formal_msgs = [
        "이 코드를 리팩토링해 주시겠습니까",
        "데이터베이스 성능을 개선하고 싶습니다",
        "API 엔드포인트를 추가하겠습니다",
        "테스트 결과를 확인했습니다",
        "배포 과정에서 문제가 발생했습니다",
        "코드 리뷰를 요청드립니다",
        "성능 최적화가 필요합니다",
        "보안 취약점을 수정했습니다",
        "문서를 업데이트하겠습니다",
        "회의에서 논의된 내용을 반영했습니다",
    ]

    formal_result = analyze_communication_style(formal_msgs)
    test("4. Style formal messages: formality=formal",
         formal_result.get("formality") == "formal",
         f"Got formality={formal_result.get('formality')}, summary={formal_result.get('summary')}")
except Exception as e:
    test("4. Style formal messages", False, str(e))

# ═══════════════════════════════════════════════════════════
# Test 5: Communication style with casual messages
# ═══════════════════════════════════════════════════════════
try:
    casual_msgs = [
        "이거 버그인데 고쳐줘",
        "React 컴포넌트 좀 만들어줘",
        "이 코드 왜 안 되는 거야",
        "타입스크립트로 바꿔줄래",
        "이거 해봤는데 안 됐어",
        "빌드가 안 되는 건데 왜 그런 거야",
        "이 함수 리팩토링 해줘",
        "테스트 코드 좀 짜줘",
        "API 연결이 안 되는 건데",
        "도커 컨테이너 설정 좀 해줘",
    ]

    casual_result = analyze_communication_style(casual_msgs)
    test("5. Style casual messages: formality=casual",
         casual_result.get("formality") == "casual",
         f"Got formality={casual_result.get('formality')}, summary={casual_result.get('summary')}")
except Exception as e:
    test("5. Style casual messages", False, str(e))

# ═══════════════════════════════════════════════════════════
# Test 6: Communication style with code-heavy messages
# ═══════════════════════════════════════════════════════════
try:
    code_msgs = [
        "```python\ndef hello():\n    print('hello')\n```",
        "import React from 'react';\nconst App = () => { return <div>Hello</div>; }",
        "```javascript\nfunction test() { return true; }\n```",
        "const result = await fetch('/api/data').then(r => r.json())",
        "def parse_data(input):\n    return json.loads(input)",
        "```tsx\nimport { useState } from 'react';\n```",
        "from fastapi import FastAPI\napp = FastAPI()",
        "class UserService:\n    def get_user(self, id): pass",
        "let data = [1, 2, 3].map(x => x * 2).filter(x => x > 2)",
        "var config = require('./config')\nmodule.exports = config",
    ]

    code_result = analyze_communication_style(code_msgs)
    test("6. Style code-heavy: code_ratio > 0.3",
         code_result.get("code_ratio", 0) > 0.3,
         f"Got code_ratio={code_result.get('code_ratio')}")
except Exception as e:
    test("6. Style code-heavy", False, str(e))

# ═══════════════════════════════════════════════════════════
# Test 7: API endpoints return valid JSON (structural check)
# ═══════════════════════════════════════════════════════════
try:
    # Verify the functions return proper dicts
    topics_result = extract_topics(["test"] * 25, language="en")
    assert isinstance(topics_result, dict), "topics must return dict"
    assert "skipped" in topics_result or "top_keywords" in topics_result

    style_result = analyze_communication_style(["Hello world", "Testing code"])
    assert isinstance(style_result, dict), "style must return dict"
    required_keys = ["avg_message_length", "question_ratio", "code_ratio",
                     "formality", "language_mix", "verbosity", "summary"]
    missing = [k for k in required_keys if k not in style_result]
    assert not missing, f"Missing keys: {missing}"

    # Verify selfcore.py has the endpoints
    sc_path = os.path.join(PROJECT_ROOT, "selfcore.py")
    with open(sc_path, "r", encoding="utf-8") as f:
        sc = f.read()
    assert "/api/analyze/topics" in sc
    assert "/api/analyze/style" in sc

    test("7. API endpoints return valid JSON structure", True)
except Exception as e:
    test("7. API endpoints valid JSON", False, str(e))

# ═══════════════════════════════════════════════════════════
# Test 8: Phase 4A functionality preserved
# ═══════════════════════════════════════════════════════════
try:
    # Run existing Phase 4A tests inline (key checks)
    from analysis_engine import (
        parse_chatgpt_export, parse_claude_export, parse_text_paste,
        extract_entities, extract_preferences, detect_language,
        sanitize_profile_data, load_tech_dictionary
    )
    import zipfile, io

    # Entity extraction still works
    ents = extract_entities(["I love using React and Python for development"])
    tech_names = [t["name"] for t in ents.get("tech", [])]
    assert "React" in tech_names or "Python" in tech_names, f"Entity extraction broken: {tech_names}"

    # Language detection
    assert detect_language("했어") == "ko"
    assert detect_language("I refactored the code") == "en"

    # ChatGPT parser
    test_conv = [{"title": "t", "current_node": "n1", "mapping": {
        "r": {"id": "r", "parent": None, "message": None},
        "n1": {"id": "n1", "parent": "r", "message": {"author": {"role": "user"}, "content": {"parts": ["test"]}, "create_time": 1700000000}}
    }}]
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w') as zf:
        zf.writestr("conversations.json", json.dumps(test_conv))
    buf.seek(0)
    msgs = parse_chatgpt_export(buf.read())
    assert len(msgs) == 1

    # Sanitization
    s = sanitize_profile_data({"name": "test <|im_start|>hack"})
    assert "<|im_start|>" not in s["name"]

    # Tech dictionary
    td = load_tech_dictionary()
    assert len(td.get("patterns", [])) >= 200

    # selfcore.py still has all Phase 1-3 endpoints
    with open(sc_path, "r", encoding="utf-8") as f:
        sc = f.read()
    phase1_eps = ["/api/health", "/api/profile", "/api/context", "/api/settings",
                  "/api/activity", "/api/suggestions", "/api/weekly"]
    missing_eps = [ep for ep in phase1_eps if ep not in sc]
    assert not missing_eps, f"Missing endpoints: {missing_eps}"

    test("8. Phase 4A functionality preserved", True)
except Exception as e:
    test("8. Phase 4A preserved", False, str(e))

# ═══════════════════════════════════════════════════════════
# SUMMARY
# ═══════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("  SelfCore Phase 4B-1 Self-Test Results")
print("=" * 60)
for r in results:
    print(r)
print("=" * 60)
print(f"  TOTAL: {PASS + FAIL} | PASS: {PASS} | FAIL: {FAIL}")
print("=" * 60)
if FAIL > 0:
    sys.exit(1)
