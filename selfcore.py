# PRIVACY: This server binds to 127.0.0.1 ONLY. No external network access.
# All data stays on the user's PC. Nothing is sent to any external server.
"""
SelfCore — Personal AI Identity Engine Backend v4.0
Phase 4: Hardened error handling, port retry, SQLite retry, batch observer writes.
"""

import json
import os
import hashlib
import base64
import re
import sqlite3
import threading
import time
import zipfile
import io
import ctypes
import ctypes.wintypes
from datetime import datetime, timedelta
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from collections import Counter

import psutil
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

# Phase 4A: Analysis Engine
try:
    from analysis_engine import (
        parse_chatgpt_export, parse_claude_export, parse_text_paste,
        merge_analysis_results, run_full_analysis, sanitize_profile_data,
        get_progress, set_progress, extract_topics, analyze_communication_style,
        check_ollama_status, start_ollama_if_needed, pull_model_if_needed,
        cleanup_orphan_ollama, run_profile_extraction,
        generate_profile_updates, apply_suggestions
    )
    ANALYSIS_ENGINE_AVAILABLE = True
except ImportError:
    ANALYSIS_ENGINE_AVAILABLE = False

# ─── Paths ────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROFILES_DIR = os.path.join(BASE_DIR, "profiles")
DB_PATH = os.path.join(BASE_DIR, "selfcore.db")
os.makedirs(PROFILES_DIR, exist_ok=True)

# ─── Default .self schema ────────────────────────────────────────
DEFAULT_SCHEMA = {
    "version": "1.0",
    "identity": {"name": "", "language": [], "timezone": "", "occupation": ""},
    "cognition": {"decision_style": "", "communication_preference": "", "thinking_patterns": [], "risk_tolerance": ""},
    "projects": [],
    "preferences": {"ai_interaction": "", "output_format": "", "design_taste": "", "tools_primary": []},
    "context_tags": {"tech": [], "interests": [], "current_focus": ""}
}

# ─── SQLite (with retry on lock) ─────────────────────────────────
def sqlite_connect(retries=3, delay=1):
    """Connect to SQLite with retry on database lock."""
    for attempt in range(retries):
        try:
            conn = sqlite3.connect(DB_PATH, timeout=5)
            return conn
        except sqlite3.OperationalError as e:
            if "locked" in str(e) and attempt < retries - 1:
                time.sleep(delay)
            else:
                raise
    return sqlite3.connect(DB_PATH, timeout=5)

def init_db():
    conn = sqlite_connect()
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS activity_log (id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp TEXT, window_title TEXT, process_name TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS injection_log (id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp TEXT, platform TEXT, context_injected TEXT, profile_used TEXT, route_rule TEXT)")
    conn.commit()
    conn.close()

def get_setting(key):
    conn = sqlite_connect()
    c = conn.cursor()
    c.execute("SELECT value FROM settings WHERE key = ?", (key,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else None

def set_setting(key, value):
    conn = sqlite_connect()
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))
    conn.commit()
    conn.close()

init_db()

# ─── Multi-Profile ───────────────────────────────────────────────
def get_active_profile_name():
    return get_setting("active_profile") or "default"

def set_active_profile_name(name):
    set_setting("active_profile", name)

def profile_path(name):
    safe = re.sub(r'[^\w\-]', '_', name)
    return os.path.join(PROFILES_DIR, f"{safe}.self")

def list_profiles():
    return sorted([f[:-5] for f in os.listdir(PROFILES_DIR) if f.endswith(".self")])

def load_profile(name=None):
    if name is None:
        name = get_active_profile_name()
    path = profile_path(name)
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            # Validate required keys exist
            for k in ("identity", "cognition", "projects", "preferences", "context_tags"):
                if k not in data:
                    raise ValueError(f"Missing key: {k}")
            return data
        except (json.JSONDecodeError, ValueError, KeyError) as e:
            print(f"[SelfCore] WARNING: Corrupted profile '{name}': {e}. Resetting to default.")
            fresh = json.loads(json.dumps(DEFAULT_SCHEMA))
            save_profile(fresh, name)
            return fresh
    return json.loads(json.dumps(DEFAULT_SCHEMA))

def save_profile(data, name=None):
    if name is None:
        name = get_active_profile_name()
    with open(profile_path(name), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def delete_profile(name):
    path = profile_path(name)
    if os.path.exists(path):
        os.remove(path)
        return True
    return False

# ─── Encryption ──────────────────────────────────────────────────
DEFAULT_PASSWORD = "selfcore-default-key-2026"

def derive_key(pw):
    return hashlib.sha256(pw.encode("utf-8")).digest()

def encrypt_data(data, pw=None):
    pw = pw or get_setting("export_password") or DEFAULT_PASSWORD
    aesgcm = AESGCM(derive_key(pw))
    nonce = os.urandom(12)
    ct = aesgcm.encrypt(nonce, data.encode("utf-8"), None)
    return base64.b64encode(nonce + ct).decode("utf-8")

def decrypt_data(payload, pw=None):
    pw = pw or get_setting("export_password") or DEFAULT_PASSWORD
    raw = base64.b64decode(payload)
    return AESGCM(derive_key(pw)).decrypt(raw[:12], raw[12:], None).decode("utf-8")

# ─── Tokenizer ───────────────────────────────────────────────────
STOPWORDS = {"the","a","an","is","are","was","were","be","been","being","have",
    "has","had","do","does","did","will","would","could","should","may","might",
    "shall","can","to","of","in","for","on","with","at","by","from","as","into",
    "through","during","before","after","and","but","or","nor","not","so","yet",
    "both","either","neither","each","every","all","any","few","more","most",
    "other","some","such","no","only","own","same","than","too","very","just",
    "about","what","which","who","whom","this","that","these","those","i","me",
    "my","myself","we","our","you","your","he","him","she","her","it","its",
    "they","them","their","how","when","where","why","make","help","want","need",
    "write","create","build","please","could","would","like","using","use"}

def tokenize(text):
    words = re.findall(r'[a-zA-Z0-9\u3131-\uD79D]+', text.lower())
    return [w for w in words if w not in STOPWORDS and len(w) > 1]

def flatten_values(obj, prefix=""):
    pairs = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            pairs.extend(flatten_values(v, f"{prefix}.{k}" if prefix else k))
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            if isinstance(item, dict):
                pairs.extend(flatten_values(item, f"{prefix}[{i}]"))
            else:
                pairs.append((prefix, str(item)))
    elif obj:
        pairs.append((prefix, str(obj)))
    return pairs

def score_block(block_texts, query_tokens):
    if not query_tokens:
        return 0
    bw = []
    for t in block_texts:
        bw.extend(tokenize(t))
    if not bw:
        return 0
    bc = Counter(bw)
    return sum(bc[qt] / len(bw) for qt in query_tokens if qt in bc)

# ─── Dynamic Context Router v3 ─────────────────────────────────
CODE_KW = {"code","coding","programming","function","bug","error","debug","api",
    "script","class","method","variable","algorithm","database","sql","deploy",
    "compile","syntax","runtime","refactor","test","unittest","server","backend",
    "frontend","framework","library","package","module","import","export",
    "python","javascript","typescript","react","rust","java","go","cpp","html","css",
    "git","docker","kubernetes","aws","node","django","flask","fastapi","electron","next",
    "fix","build"}

WRITING_KW = {"write","email","letter","essay","article","blog","message","draft",
    "tone","formal","informal","grammar","proofread","translate","summarize",
    "document","report","proposal","presentation","memo","copywriting","content",
    "summary"}

PLANNING_KW = {"plan","strategy","roadmap","milestone","deadline","goal","objective",
    "prioritize","schedule","timeline","sprint","backlog","architecture",
    "decision","tradeoff","risk","budget","resource","scope","task","project",
    "workflow","process","pipeline","phase"}

CREATIVE_KW = {"design","creative","art","color","layout","ui","ux","brand",
    "aesthetic","visual","illustration","logo","typography","animation","figma",
    "photoshop","blender","sketch","wireframe","prototype","style","mood","theme",
    "font"}

# Korean keyword sets for v3
CODE_KW_KO = {"코드","에러","버그","함수","빌드","컴파일","디버그","서버","배포","테스트","구현","개발","클래스","변수","알고리즘"}
WRITING_KW_KO = {"문서","이메일","작성","보고서","편지","번역","요약","초안","메일","글"}
PLANNING_KW_KO = {"목표","계획","전략","로드맵","일정","마일스톤","타임라인","우선순위","프로젝트"}
CREATIVE_KW_KO = {"디자인","레이아웃","색상","폰트","로고","브랜드","스타일","와이어프레임"}

def classify_query_v3(query):
    """v3: classify using both tokenized words and Korean substrings."""
    tokens = set(tokenize(query))
    text_lower = query.lower()

    scores = {
        "code":     len(tokens & CODE_KW),
        "writing":  len(tokens & WRITING_KW),
        "planning": len(tokens & PLANNING_KW),
        "creative": len(tokens & CREATIVE_KW),
    }
    # Korean keyword matching (substring)
    for kw in CODE_KW_KO:
        if kw in text_lower: scores["code"] += 1
    for kw in WRITING_KW_KO:
        if kw in text_lower: scores["writing"] += 1
    for kw in PLANNING_KW_KO:
        if kw in text_lower: scores["planning"] += 1
    for kw in CREATIVE_KW_KO:
        if kw in text_lower: scores["creative"] += 1

    best = max(scores, key=scores.get)
    if scores[best] == 0:
        return "general"
    return best

def get_recent_activity_boost():
    """Check last 2 hours of activity for context boost."""
    since = (datetime.now() - timedelta(hours=2)).isoformat()
    try:
        conn = sqlite_connect()
        c = conn.cursor()
        c.execute("SELECT window_title, process_name FROM activity_log WHERE timestamp >= ?", (since,))
        rows = c.fetchall()
        conn.close()
    except Exception:
        return {}
    if not rows:
        return {}
    proc_counts = Counter()
    for title, proc in rows:
        pn = (proc or "").replace(".exe", "").lower()
        proc_counts[pn] += 1
    boosts = {}
    for pn, cnt in proc_counts.most_common(3):
        if pn in ("code", "devenv", "pycharm", "idea64", "webstorm64"):
            boosts["projects"] = boosts.get("projects", 0) + 0.3
            boosts["context_tags"] = boosts.get("context_tags", 0) + 0.2
        elif "chrome" in pn or "firefox" in pn or "edge" in pn:
            boosts["identity"] = boosts.get("identity", 0) + 0.1
            boosts["cognition"] = boosts.get("cognition", 0) + 0.1
        elif "figma" in pn or "photoshop" in pn or "illustrator" in pn:
            boosts["preferences"] = boosts.get("preferences", 0) + 0.2
    return boosts

def _est_tokens(text):
    """Estimate token count: word_count * 1.3"""
    return int(len(text.split()) * 1.3)

def get_context_v3(query, profile_name=None, max_tokens=200):
    """Dynamic Router v3: structured output with token budget."""
    profile = load_profile(profile_name)
    identity = profile.get("identity", {})
    name = identity.get("name", "User") or "User"
    occ = identity.get("occupation", "") or ""

    category = classify_query_v3(query) if query.strip() else "general"
    boosts = get_recent_activity_boost()

    # Step 2: select blocks by category
    BLOCK_MAP = {
        "code":     ["projects", "context_tags", "cognition"],
        "writing":  ["cognition", "preferences", "identity"],
        "planning": ["cognition", "projects", "context_tags"],
        "creative": ["preferences", "identity"],
        "general":  ["identity", "context_tags"],
    }
    selected_keys = BLOCK_MAP.get(category, BLOCK_MAP["general"])

    # Step 5: Build structured output
    lines = ["The following is verified context about the user you are talking to:"]
    lines.append(f"- Name: {name}")
    if occ:
        lines.append(f"- Role: {occ}")
    token_count = sum(_est_tokens(l) for l in lines)

    # Active projects
    if "projects" in selected_keys:
        projects = profile.get("projects", [])
        for p in projects:
            pname = p.get("name", "")
            pstack = p.get("stack", "")
            pstatus = p.get("status", "")
            if pname:
                line = f"- Current project: {pname}"
                if pstack: line += f" ({pstack})"
                if pstatus and pstatus != "active": line += f" [{pstatus}]"
                est = _est_tokens(line)
                if token_count + est <= max_tokens:
                    lines.append(line)
                    token_count += est

    # Cognition
    cognition = profile.get("cognition", {})
    if "cognition" in selected_keys:
        comm = cognition.get("communication_preference", "")
        if comm:
            line = f"- Communication: {comm}"
            est = _est_tokens(line)
            if token_count + est <= max_tokens:
                lines.append(line)
                token_count += est
        dec = cognition.get("decision_style", "")
        if dec:
            line = f"- Decision style: {dec}"
            est = _est_tokens(line)
            if token_count + est <= max_tokens:
                lines.append(line)
                token_count += est

    # Context tags
    ctx_tags = profile.get("context_tags", {})
    if "context_tags" in selected_keys:
        tech = ctx_tags.get("tech", [])
        if tech:
            line = f"- Tech stack: {', '.join(tech[:10])}"
            est = _est_tokens(line)
            if token_count + est <= max_tokens:
                lines.append(line)
                token_count += est
        focus = ctx_tags.get("current_focus", "")
        if focus:
            line = f"- Current focus: {focus}"
            est = _est_tokens(line)
            if token_count + est <= max_tokens:
                lines.append(line)
                token_count += est
        interests = ctx_tags.get("interests", [])
        if interests:
            line = f"- Interests: {', '.join(interests[:5])}"
            est = _est_tokens(line)
            if token_count + est <= max_tokens:
                lines.append(line)
                token_count += est

    # Preferences
    prefs = profile.get("preferences", {})
    if "preferences" in selected_keys:
        if category == "creative" and prefs.get("design_taste"):
            line = f"- Design taste: {prefs['design_taste']}"
            est = _est_tokens(line)
            if token_count + est <= max_tokens:
                lines.append(line)
                token_count += est
        if prefs.get("output_format"):
            line = f"- Output format: {prefs['output_format']}"
            est = _est_tokens(line)
            if token_count + est <= max_tokens:
                lines.append(line)
                token_count += est
        tools = prefs.get("tools_primary", [])
        if tools:
            line = f"- Tools: {', '.join(tools[:5])}"
            est = _est_tokens(line)
            if token_count + est <= max_tokens:
                lines.append(line)
                token_count += est

    # General fallback: always include current_focus if not already
    if "context_tags" not in selected_keys:
        focus = ctx_tags.get("current_focus", "")
        if focus:
            line = f"- Current focus: {focus}"
            est = _est_tokens(line)
            if token_count + est <= max_tokens:
                lines.append(line)
                token_count += est

    lines.append("User's actual message follows below:")
    return "\n".join(lines), category

# Keep v2 as fallback alias
def get_context_v2(query, profile_name=None, max_tokens=200):
    return get_context_v3(query, profile_name, max_tokens)

# ─── Injection Logging ──────────────────────────────────────────
def log_injection(platform, context_injected, profile_used, route_rule=""):
    conn = sqlite_connect()
    c = conn.cursor()
    c.execute("INSERT INTO injection_log (timestamp, platform, context_injected, profile_used, route_rule) VALUES (?, ?, ?, ?, ?)",
              (datetime.now().isoformat(), platform, context_injected[:500], profile_used, route_rule))
    conn.commit()
    conn.close()

def get_injection_history(limit=20):
    conn = sqlite_connect()
    c = conn.cursor()
    c.execute("SELECT timestamp, platform, context_injected, profile_used, route_rule FROM injection_log ORDER BY id DESC LIMIT ?", (limit,))
    rows = c.fetchall()
    conn.close()
    return [{"timestamp": r[0], "platform": r[1], "context": r[2], "profile": r[3], "rule": r[4]} for r in rows]

# ─── Window Title Observer ───────────────────────────────────────
user32 = ctypes.windll.user32

def get_foreground_window_title():
    try:
        hwnd = user32.GetForegroundWindow()
        length = user32.GetWindowTextLengthW(hwnd)
        if length == 0: return ""
        buf = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(hwnd, buf, length + 1)
        return buf.value
    except Exception:
        return ""

def get_foreground_process_name():
    try:
        hwnd = user32.GetForegroundWindow()
        pid = ctypes.wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        return psutil.Process(pid.value).name()
    except Exception:
        return ""

observer_running = False
observer_buffer = []
observer_buffer_lock = threading.Lock()

def flush_observer_buffer():
    """Batch write buffered entries to SQLite."""
    global observer_buffer
    with observer_buffer_lock:
        if not observer_buffer:
            return
        entries = observer_buffer[:]
        observer_buffer = []
    try:
        conn = sqlite_connect()
        c = conn.cursor()
        c.executemany("INSERT INTO activity_log (timestamp, window_title, process_name) VALUES (?, ?, ?)", entries)
        conn.commit()
        conn.close()
    except Exception:
        pass

def window_observer_loop():
    global observer_running
    while observer_running:
        try:
            if get_setting("tracking_enabled") == "true":
                title = get_foreground_window_title()
                proc = get_foreground_process_name()
                if title:
                    with observer_buffer_lock:
                        observer_buffer.append((datetime.now().isoformat(), title, proc))
                        should_flush = len(observer_buffer) >= 5
                    if should_flush:
                        flush_observer_buffer()
        except Exception:
            pass
        time.sleep(30)

def start_observer():
    global observer_running
    observer_running = True
    threading.Thread(target=window_observer_loop, daemon=True).start()

def purge_activity_data():
    """Delete all activity tracking data."""
    try:
        conn = sqlite_connect()
        c = conn.cursor()
        c.execute("DELETE FROM activity_log")
        conn.commit()
        conn.close()
        return True
    except Exception:
        return False

# ─── Activity Patterns ──────────────────────────────────────────
def get_activity_last_24h():
    since = (datetime.now() - timedelta(hours=24)).isoformat()
    conn = sqlite_connect()
    c = conn.cursor()
    c.execute("SELECT timestamp, window_title, process_name FROM activity_log WHERE timestamp >= ? ORDER BY timestamp DESC", (since,))
    rows = c.fetchall()
    conn.close()
    return [{"timestamp": r[0], "window_title": r[1], "process_name": r[2]} for r in rows]

def get_activity_patterns():
    since = (datetime.now() - timedelta(hours=24)).isoformat()
    conn = sqlite_connect()
    c = conn.cursor()
    c.execute("SELECT timestamp, window_title, process_name FROM activity_log WHERE timestamp >= ?", (since,))
    rows = c.fetchall()
    conn.close()
    if not rows:
        return {"top_apps": [], "active_hours": [], "top_titles": []}

    app_time = Counter()
    hour_counts = Counter()
    title_counts = Counter()
    for ts, title, proc in rows:
        pn = proc.replace(".exe", "") if proc else "Unknown"
        app_time[pn] += 30
        try:
            hour_counts[datetime.fromisoformat(ts).hour] += 1
        except Exception:
            pass
        if title:
            title_counts[title[:60]] += 1

    top_apps = []
    for app, secs in app_time.most_common(10):
        m = secs // 60
        h = m // 60
        top_apps.append({"name": app, "time": f"{h}h {m%60:02d}m" if h > 0 else f"{m}m", "seconds": secs})

    active_hours = [{"hour": f"{h:02d}:00", "count": cnt} for h, cnt in sorted(hour_counts.items(), key=lambda x: x[1], reverse=True)[:5]]
    top_titles = [{"title": t, "count": c} for t, c in title_counts.most_common(5)]
    return {"top_apps": top_apps, "active_hours": active_hours, "top_titles": top_titles}

# ─── Smart Activity Analyzer ────────────────────────────────────
EXT_TO_TECH = {
    ".py": "Python", ".js": "JavaScript", ".ts": "TypeScript", ".tsx": "React",
    ".jsx": "React", ".rs": "Rust", ".go": "Go", ".java": "Java", ".kt": "Kotlin",
    ".swift": "Swift", ".cpp": "C++", ".c": "C", ".rb": "Ruby", ".php": "PHP",
    ".vue": "Vue", ".svelte": "Svelte", ".sql": "SQL", ".html": "HTML", ".css": "CSS",
    ".scss": "SCSS", ".json": "JSON", ".yaml": "YAML", ".yml": "YAML",
    ".md": "Markdown", ".sh": "Bash", ".ps1": "PowerShell",
}

APP_LABELS = {
    "code": "VS Code", "devenv": "Visual Studio", "pycharm64": "PyCharm",
    "idea64": "IntelliJ", "webstorm64": "WebStorm", "chrome": "Chrome",
    "firefox": "Firefox", "msedge": "Edge", "discord": "Discord",
    "slack": "Slack", "teams": "Teams", "notion": "Notion",
    "figma": "Figma", "photoshop": "Photoshop", "illustrator": "Illustrator",
    "blender": "Blender", "terminal": "Terminal", "windowsterminal": "Windows Terminal",
    "cmd": "Command Prompt", "powershell": "PowerShell", "explorer": "Explorer",
    "spotify": "Spotify", "postman": "Postman", "insomnia": "Insomnia",
}

def analyze_daily_activity():
    """Analyze last 24h of window titles and extract insights."""
    since = (datetime.now() - timedelta(hours=24)).isoformat()
    conn = sqlite_connect()
    c = conn.cursor()
    c.execute("SELECT timestamp, window_title, process_name FROM activity_log WHERE timestamp >= ?", (since,))
    rows = c.fetchall()
    conn.close()

    if not rows:
        return {"total_records": 0, "apps": [], "detected_projects": [], "detected_tech": [],
                "peak_hours": [], "total_minutes": 0}

    app_secs = Counter()
    hour_counts = Counter()
    detected_projects = set()
    detected_tech = set()
    detected_tools = set()

    for ts, title, proc in rows:
        pn = (proc or "").replace(".exe", "").lower()
        label = APP_LABELS.get(pn, pn.title() if pn else "Unknown")
        app_secs[label] += 30

        try:
            hour_counts[datetime.fromisoformat(ts).hour] += 1
        except Exception:
            pass

        if title:
            # Extract project names from VS Code / IDE titles
            # Pattern: "filename - ProjectName - VS Code"
            parts = [p.strip() for p in title.split(" - ")]
            if len(parts) >= 3 and any(ide in parts[-1].lower() for ide in ["code", "studio", "pycharm", "intellij", "webstorm"]):
                proj = parts[-2] if len(parts) >= 3 else ""
                if proj and len(proj) > 1 and not proj.startswith("[") and proj not in ("Visual Studio Code",):
                    detected_projects.add(proj)

            # Detect tech from file extensions in title
            for ext, tech in EXT_TO_TECH.items():
                if ext in title.lower():
                    detected_tech.add(tech)

            # Detect tools from title
            for tool_kw in ["figma", "postman", "docker", "terminal", "git"]:
                if tool_kw in title.lower():
                    detected_tools.add(tool_kw.title())

    apps = []
    for app, secs in app_secs.most_common(15):
        m = secs // 60
        h = m // 60
        apps.append({"name": app, "time": f"{h}h {m%60:02d}m" if h > 0 else f"{m}m", "seconds": secs})

    peak = sorted(hour_counts.items(), key=lambda x: x[1], reverse=True)[:3]
    peak_hours = [f"{h:02d}:00" for h, _ in peak]

    return {
        "total_records": len(rows),
        "total_minutes": len(rows) * 30 // 60,
        "apps": apps,
        "detected_projects": sorted(detected_projects),
        "detected_tech": sorted(detected_tech),
        "detected_tools": sorted(detected_tools),
        "peak_hours": peak_hours,
    }

def suggest_profile_updates():
    """Compare activity analysis with current profile and suggest updates."""
    analysis = analyze_daily_activity()
    profile = load_profile()
    suggestions = []

    current_tech = set(t.lower() for t in profile.get("context_tags", {}).get("tech", []))
    current_tools = set(t.lower() for t in profile.get("preferences", {}).get("tools_primary", []))
    current_projects = set(p.get("name", "").lower() for p in profile.get("projects", []))
    current_interests = set(t.lower() for t in profile.get("context_tags", {}).get("interests", []))

    # Suggest new tech
    for tech in analysis.get("detected_tech", []):
        if tech.lower() not in current_tech:
            suggestions.append({
                "type": "add_tech",
                "field": "context_tags.tech",
                "value": tech,
                "reason_en": f"Detected {tech} in your window titles today",
                "reason_ko": f"오늘 창 제목에서 {tech}이(가) 감지되었습니다",
            })

    # Suggest new tools
    for tool in analysis.get("detected_tools", []):
        if tool.lower() not in current_tools:
            suggestions.append({
                "type": "add_tool",
                "field": "preferences.tools_primary",
                "value": tool,
                "reason_en": f"You used {tool} today. Add to primary tools?",
                "reason_ko": f"오늘 {tool}을(를) 사용했습니다. 주요 도구에 추가할까요?",
            })

    # Suggest new tools from top apps
    for app_info in analysis.get("apps", [])[:5]:
        app = app_info["name"]
        if app.lower() not in current_tools and app.lower() not in ("unknown", "explorer", "chrome", "edge", "firefox"):
            secs = app_info["seconds"]
            if secs >= 600:  # at least 10 minutes
                suggestions.append({
                    "type": "add_tool",
                    "field": "preferences.tools_primary",
                    "value": app,
                    "reason_en": f"Used {app} for {app_info['time']} today. Add to primary tools?",
                    "reason_ko": f"오늘 {app}을(를) {app_info['time']} 사용했습니다. 주요 도구에 추가할까요?",
                })

    # Suggest new projects
    for proj in analysis.get("detected_projects", []):
        if proj.lower() not in current_projects:
            suggestions.append({
                "type": "add_project",
                "field": "projects",
                "value": proj,
                "reason_en": f"Detected project '{proj}' from window titles. Add to projects?",
                "reason_ko": f"창 제목에서 프로젝트 '{proj}'이(가) 감지되었습니다. 프로젝트에 추가할까요?",
            })

    return suggestions

def apply_suggestion(suggestion):
    """Apply a single suggestion to the active profile."""
    profile = load_profile()
    stype = suggestion.get("type", "")
    value = suggestion.get("value", "")

    if stype == "add_tech":
        tech = profile.get("context_tags", {}).get("tech", [])
        if value not in tech:
            tech.append(value)
            profile["context_tags"]["tech"] = tech

    elif stype == "add_tool":
        tools = profile.get("preferences", {}).get("tools_primary", [])
        if value not in tools:
            tools.append(value)
            profile["preferences"]["tools_primary"] = tools

    elif stype == "add_project":
        projects = profile.get("projects", [])
        existing = [p.get("name", "").lower() for p in projects]
        if value.lower() not in existing:
            projects.append({"name": value, "status": "active", "stack": "", "description": "Detected from activity"})
            profile["projects"] = projects

    save_profile(profile)
    return profile

# ─── Weekly Summary ──────────────────────────────────────────────
def get_weekly_summary():
    since = (datetime.now() - timedelta(days=7)).isoformat()
    conn = sqlite_connect()
    c = conn.cursor()
    c.execute("SELECT timestamp, window_title, process_name FROM activity_log WHERE timestamp >= ?", (since,))
    rows = c.fetchall()
    conn.close()

    if len(rows) < 10:
        return None

    total_min = len(rows) * 30 // 60
    app_secs = Counter()
    day_counts = Counter()
    all_tech = set()

    for ts, title, proc in rows:
        pn = (proc or "").replace(".exe", "").lower()
        label = APP_LABELS.get(pn, pn.title() if pn else "Unknown")
        app_secs[label] += 30
        try:
            day_counts[datetime.fromisoformat(ts).strftime("%A")] += 1
        except Exception:
            pass
        for ext, tech in EXT_TO_TECH.items():
            if ext in (title or "").lower():
                all_tech.add(tech)

    top_apps = [{"name": a, "seconds": s} for a, s in app_secs.most_common(5)]
    best_day = max(day_counts.items(), key=lambda x: x[1])[0] if day_counts else "N/A"

    return {
        "total_hours": round(total_min / 60, 1),
        "top_apps": top_apps,
        "most_productive_day": best_day,
        "detected_tech": sorted(all_tech),
        "total_records": len(rows),
    }

# ─── Cold Start ──────────────────────────────────────────────────
TECH_KEYWORDS = {
    "python","javascript","typescript","react","vue","angular","node","nodejs",
    "electron","next","nextjs","django","flask","fastapi","rust","go","golang",
    "java","kotlin","swift","c++","cpp","ruby","php","sql","sqlite","postgres",
    "mongodb","redis","docker","kubernetes","aws","azure","gcp","git","github",
    "tailwind","css","html","linux","windows","macos","api","rest","graphql",
    "tensorflow","pytorch","openai","claude","gpt","llm","ai","ml","deep learning",
    "machine learning","data science","devops","ci/cd","figma","photoshop","blender"
}

def parse_chatgpt_zip(zipdata):
    try:
        zf = zipfile.ZipFile(io.BytesIO(zipdata))
    except Exception:
        return None
    conversations_data = None
    for name in zf.namelist():
        if "conversations.json" in name.lower():
            conversations_data = json.loads(zf.read(name))
            break
    if not conversations_data:
        return None
    all_user_text = []
    for conv in conversations_data:
        mapping = conv.get("mapping", {})
        for node in mapping.values():
            msg = node.get("message")
            if not msg or msg.get("author", {}).get("role") != "user":
                continue
            for part in msg.get("content", {}).get("parts", []):
                if isinstance(part, str) and part.strip():
                    all_user_text.append(part)
    combined = " ".join(all_user_text).lower()
    word_freq = Counter(re.findall(r'[a-zA-Z0-9\+\#/]+', combined))
    tech_found = [t for t in TECH_KEYWORDS if (len(t.split()) == 1 and word_freq.get(t, 0) >= 2) or (len(t.split()) > 1 and t in combined)]
    name_guess = ""
    for text in all_user_text[:20]:
        m = re.search(r"(?:[Mm]y name is|I'?m called)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)", text)
        if m:
            name_guess = m.group(1)
            break
    interests = set()
    for kw, label in {"design":"Design","ux":"UX Design","ui":"UI Design","music":"Music","gaming":"Gaming","writing":"Writing","finance":"Finance","productivity":"Productivity","automation":"Automation"}.items():
        if word_freq.get(kw, 0) >= 2:
            interests.add(label)
    avg_len = sum(len(t.split()) for t in all_user_text) / max(len(all_user_text), 1)
    comm_style = "Brief and direct" if avg_len < 15 else "Moderate detail" if avg_len < 40 else "Detailed and structured"
    return {"name": name_guess, "tech": sorted(set(t.capitalize() if len(t) <= 3 else t.title() for t in tech_found)),
            "interests": sorted(interests), "communication_style": comm_style, "total_messages": len(all_user_text)}

def parse_text_history(text):
    if not text or len(text.strip()) < 20:
        return None
    combined = text.lower()
    word_freq = Counter(re.findall(r'[a-zA-Z0-9\+\#/]+', combined))
    tech_found = [t for t in TECH_KEYWORDS if (len(t.split()) == 1 and word_freq.get(t, 0) >= 1) or (len(t.split()) > 1 and t in combined)]
    name_guess = ""
    m = re.search(r"(?:[Mm]y name is|I'?m called)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)", text)
    if m:
        name_guess = m.group(1)
    interests = set()
    for kw, label in {"design":"Design","ux":"UX Design","music":"Music","gaming":"Gaming","writing":"Writing","finance":"Finance","productivity":"Productivity","automation":"Automation"}.items():
        if word_freq.get(kw, 0) >= 1:
            interests.add(label)
    sentences = [s for s in re.split(r'[.!?\n]', text) if s.strip()]
    avg_len = sum(len(s.split()) for s in sentences) / max(len(sentences), 1)
    comm_style = "Brief and direct" if avg_len < 15 else "Moderate detail" if avg_len < 40 else "Detailed and structured"
    if not tech_found and not name_guess and not interests:
        return None
    return {"name": name_guess, "tech": sorted(set(t.capitalize() if len(t) <= 3 else t.title() for t in tech_found)),
            "interests": sorted(interests), "communication_style": comm_style, "total_messages": len(sentences)}

# ─── HTTP Handler ────────────────────────────────────────────────
class SelfCoreHandler(BaseHTTPRequestHandler):
    def _json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _body(self):
        try:
            length = int(self.headers.get("Content-Length", 0))
        except (ValueError, TypeError):
            length = 0
        return self.rfile.read(length) if length > 0 else b""

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
      try:
        parsed = urlparse(self.path)
        p = parsed.path
        qs = parse_qs(parsed.query)

        if p == "/api/health":
            self._json({"status": "ok", "version": "4.0"})
        elif p == "/api/profile":
            self._json(load_profile(qs.get("name", [None])[0]))
        elif p == "/api/profiles":
            self._json({"profiles": list_profiles(), "active": get_active_profile_name()})
        elif p == "/api/context":
            query = qs.get("query", [""])[0]
            ctx, rule = get_context_v2(query)
            profile_name = get_active_profile_name()
            log_injection("clipboard", ctx[:200], profile_name, rule)
            self._json({"context": ctx, "route_rule": rule})
        elif p == "/api/settings":
            key = qs.get("key", [None])[0]
            if key:
                self._json({"key": key, "value": get_setting(key)})
            else:
                keys = ["ui_lang","active_profile","first_launch_done","tracking_enabled","export_password"]
                self._json({k: get_setting(k) for k in keys})
        elif p == "/api/activity":
            self._json({"activity": get_activity_last_24h()})
        elif p == "/api/patterns":
            self._json(get_activity_patterns())
        elif p == "/api/analyze":
            self._json(analyze_daily_activity())
        elif p == "/api/suggestions":
            self._json({"suggestions": suggest_profile_updates()})
        elif p == "/api/weekly":
            data = get_weekly_summary()
            self._json(data if data else {"error": "Not enough data", "total_records": 0})
        elif p == "/api/injections":
            limit = int(qs.get("limit", ["20"])[0])
            self._json({"injections": get_injection_history(limit)})
        elif p == "/api/analyze/status":
            if ANALYSIS_ENGINE_AVAILABLE:
                self._json(get_progress())
            else:
                self._json({"status": "unavailable", "progress": 0, "message": "Analysis engine not loaded"})
        elif p == "/api/ollama/status":
            if ANALYSIS_ENGINE_AVAILABLE:
                force = qs.get("force", [""])[0].lower() == "true"
                self._json(check_ollama_status(force=force))
            else:
                self._json({"installed": False, "running": False, "model_available": False, "model_name": "llama3.2:3b", "gpu_available": False, "gpu_usage_percent": None})
        elif p == "/api/ollama/cleanup":
            if ANALYSIS_ENGINE_AVAILABLE:
                self._json(cleanup_orphan_ollama())
            else:
                self._json({"status": "unavailable", "cleaned": []})
        else:
            self._json({"error": "Not found"}, 404)
      except Exception as e:
        print(f"[SelfCore] GET {self.path} error: {e}")
        try:
            self._json({"error": "Internal server error"}, 500)
        except Exception:
            pass

    def do_POST(self):
      try:
        parsed = urlparse(self.path)
        p = parsed.path

        if p == "/api/profile":
            body = self._body()
            try:
                data = json.loads(body)
                name = data.pop("_profile_name", None)
                save_profile(data, name)
                self._json({"status": "saved"})
            except json.JSONDecodeError:
                self._json({"error": "Invalid JSON"}, 400)

        elif p == "/api/profiles/switch":
            try:
                data = json.loads(self._body())
                name = data.get("name", "default")
                if os.path.exists(profile_path(name)):
                    set_active_profile_name(name)
                    self._json({"status": "switched", "active": name})
                else:
                    self._json({"error": "Profile not found"}, 404)
            except json.JSONDecodeError:
                self._json({"error": "Invalid JSON"}, 400)

        elif p == "/api/profiles/create":
            try:
                data = json.loads(self._body())
                name = data.get("name", "").strip()
                if not name:
                    self._json({"error": "Name required"}, 400)
                    return
                save_profile(json.loads(json.dumps(DEFAULT_SCHEMA)), name)
                self._json({"status": "created", "name": name})
            except json.JSONDecodeError:
                self._json({"error": "Invalid JSON"}, 400)

        elif p == "/api/profiles/delete":
            try:
                data = json.loads(self._body())
                name = data.get("name", "")
                if name == get_active_profile_name():
                    remaining = [x for x in list_profiles() if x != name]
                    if remaining:
                        set_active_profile_name(remaining[0])
                    else:
                        set_active_profile_name("default")
                        save_profile(json.loads(json.dumps(DEFAULT_SCHEMA)), "default")
                deleted = delete_profile(name)
                self._json({"status": "deleted"} if deleted else {"error": "Not found"}, 200 if deleted else 404)
            except json.JSONDecodeError:
                self._json({"error": "Invalid JSON"}, 400)

        elif p == "/api/settings":
            try:
                data = json.loads(self._body())
                for k, v in data.items():
                    set_setting(k, str(v))
                self._json({"status": "saved"})
            except json.JSONDecodeError:
                self._json({"error": "Invalid JSON"}, 400)

        elif p == "/api/export":
            pw = None
            body = self._body()
            if body:
                try: pw = json.loads(body).get("password")
                except Exception: pass
            encrypted = encrypt_data(json.dumps(load_profile(), ensure_ascii=False), pw)
            self._json({"encrypted": encrypted, "filename": "selfcore_export.self.enc"})

        elif p == "/api/import":
            try:
                req = json.loads(self._body())
                data = json.loads(decrypt_data(req.get("encrypted", ""), req.get("password")))
                save_profile(data)
                self._json({"status": "imported", "profile": data})
            except Exception as e:
                self._json({"error": str(e)}, 400)

        elif p == "/api/import/chatgpt":
            result = parse_chatgpt_zip(self._body())
            self._json({"status": "parsed", "extracted": result} if result else {"error": "Could not parse"}, 200 if result else 400)

        elif p == "/api/import/text":
            try:
                text = json.loads(self._body()).get("text", "")
                result = parse_text_history(text)
                self._json({"status": "parsed", "extracted": result} if result else {"error": "No data extracted"}, 200 if result else 400)
            except json.JSONDecodeError:
                self._json({"error": "Invalid JSON"}, 400)

        elif p == "/api/injection/log":
            try:
                data = json.loads(self._body())
                log_injection(data.get("platform", "unknown"), data.get("context_injected", ""), data.get("profile_used", ""), data.get("route_rule", ""))
                self._json({"status": "logged"})
            except json.JSONDecodeError:
                self._json({"error": "Invalid JSON"}, 400)

        elif p == "/api/suggestions/apply":
            try:
                suggestion = json.loads(self._body())
                profile = apply_suggestion(suggestion)
                self._json({"status": "applied", "profile": profile})
            except Exception as e:
                self._json({"error": str(e)}, 400)

        elif p == "/api/activity/purge":
            ok = purge_activity_data()
            self._json({"status": "purged"} if ok else {"error": "Failed to purge"}, 200 if ok else 500)

        elif p == "/api/analyze/chatgpt":
            if not ANALYSIS_ENGINE_AVAILABLE:
                self._json({"error": "Analysis engine not available"}, 500)
                return
            try:
                body = self._body()
                messages = parse_chatgpt_export(body)
                if not messages:
                    self._json({"error": "No user messages found"}, 400)
                    return
                result = run_full_analysis(messages)
                result["source"] = "chatgpt"
                self._json(result)
            except Exception as e:
                self._json({"error": str(e)}, 500)

        elif p == "/api/analyze/claude":
            if not ANALYSIS_ENGINE_AVAILABLE:
                self._json({"error": "Analysis engine not available"}, 500)
                return
            try:
                body = self._body()
                messages = parse_claude_export(body)
                if not messages:
                    self._json({"error": "No user messages found"}, 400)
                    return
                result = run_full_analysis(messages)
                result["source"] = "claude"
                self._json(result)
            except Exception as e:
                self._json({"error": str(e)}, 500)

        elif p == "/api/analyze/text":
            if not ANALYSIS_ENGINE_AVAILABLE:
                self._json({"error": "Analysis engine not available"}, 500)
                return
            try:
                data = json.loads(self._body())
                text = data.get("text", "")
                if not text.strip():
                    self._json({"error": "Empty text"}, 400)
                    return
                messages = parse_text_paste(text)
                if not messages:
                    self._json({"error": "No content extracted"}, 400)
                    return
                result = run_full_analysis(messages)
                result["source"] = "text"
                self._json(result)
            except json.JSONDecodeError:
                self._json({"error": "Invalid JSON"}, 400)
            except Exception as e:
                self._json({"error": str(e)}, 500)

        elif p == "/api/analyze/merge":
            if not ANALYSIS_ENGINE_AVAILABLE:
                self._json({"error": "Analysis engine not available"}, 500)
                return
            try:
                data = json.loads(self._body())
                results_list = data.get("results", [])
                merged = merge_analysis_results(results_list)
                self._json(merged)
            except json.JSONDecodeError:
                self._json({"error": "Invalid JSON"}, 400)
            except Exception as e:
                self._json({"error": str(e)}, 500)

        elif p == "/api/ollama/start":
            if ANALYSIS_ENGINE_AVAILABLE:
                ok = start_ollama_if_needed()
                self._json({"status": "started" if ok else "failed", "running": ok})
            else:
                self._json({"status": "unavailable", "running": False})

        elif p == "/api/ollama/pull":
            if ANALYSIS_ENGINE_AVAILABLE:
                ok = pull_model_if_needed()
                self._json({"status": "ready" if ok else "failed", "model_available": ok})
            else:
                self._json({"status": "unavailable", "model_available": False})

        elif p == "/api/analyze/deep":
            if not ANALYSIS_ENGINE_AVAILABLE:
                self._json({"error": "Analysis engine not available"}, 500)
                return
            try:
                data = json.loads(self._body())
                source = data.get("source")
                if not source:
                    self._json({"error": "Missing source field"}, 400)
                    return
                input_data = data.get("data", "")
                use_llm = data.get("use_llm", True)
                result = run_full_analysis(
                    source=source, data=input_data, use_llm=use_llm
                )
                self._json(result)
            except json.JSONDecodeError:
                self._json({"error": "Invalid JSON"}, 400)
            except Exception as e:
                self._json({"error": str(e)}, 500)

        elif p == "/api/analyze/topics":
            if not ANALYSIS_ENGINE_AVAILABLE:
                self._json({"error": "Analysis engine not available"}, 500)
                return
            try:
                data = json.loads(self._body())
                texts = data.get("texts", [])
                language = data.get("language")
                result = extract_topics(texts, language)
                self._json(result)
            except json.JSONDecodeError:
                self._json({"error": "Invalid JSON"}, 400)
            except Exception as e:
                self._json({"error": str(e)}, 500)

        elif p == "/api/analyze/style":
            if not ANALYSIS_ENGINE_AVAILABLE:
                self._json({"error": "Analysis engine not available"}, 500)
                return
            try:
                data = json.loads(self._body())
                texts = data.get("texts", [])
                result = analyze_communication_style(texts)
                self._json(result)
            except json.JSONDecodeError:
                self._json({"error": "Invalid JSON"}, 400)
            except Exception as e:
                self._json({"error": str(e)}, 500)

        elif p == "/api/analyze/suggestions":
            if not ANALYSIS_ENGINE_AVAILABLE:
                self._json({"error": "Analysis engine not available"}, 500)
                return
            try:
                data = json.loads(self._body())
                analysis_result = data.get("analysis_result", {})
                current_profile = data.get("current_profile")
                if current_profile is None:
                    current_profile = load_profile()
                suggestions = generate_profile_updates(analysis_result, current_profile)
                self._json({"suggestions": suggestions})
            except json.JSONDecodeError:
                self._json({"error": "Invalid JSON"}, 400)
            except Exception as e:
                self._json({"error": str(e)}, 500)

        elif p == "/api/analyze/suggestions/apply":
            if not ANALYSIS_ENGINE_AVAILABLE:
                self._json({"error": "Analysis engine not available"}, 500)
                return
            try:
                data = json.loads(self._body())
                accepted = data.get("accepted", [])
                profile = data.get("profile")
                if profile is None:
                    profile = load_profile()
                updated = apply_suggestions(profile, accepted)
                updated = sanitize_profile_data(updated)
                save_profile(updated)
                self._json({"status": "applied", "profile": updated})
            except json.JSONDecodeError:
                self._json({"error": "Invalid JSON"}, 400)
            except Exception as e:
                self._json({"error": str(e)}, 500)

        else:
            self._json({"error": "Not found"}, 404)
      except Exception as e:
        print(f"[SelfCore] POST {self.path} error: {e}")
        try:
            self._json({"error": "Internal server error"}, 500)
        except Exception:
            pass

    def log_message(self, format, *args):
        pass

# ─── Main ─────────────────────────────────────────────────────────
if __name__ == "__main__":
    if not list_profiles():
        save_profile(DEFAULT_SCHEMA, "default")
        set_active_profile_name("default")
        print("[SelfCore] Created default profile")
    for k, v in [("export_password", DEFAULT_PASSWORD), ("tracking_enabled", "false"), ("ui_lang", "en")]:
        if not get_setting(k):
            set_setting(k, v)
    start_observer()

    # Phase 4B-2: Cleanup orphan Ollama models on startup
    if ANALYSIS_ENGINE_AVAILABLE:
        try:
            cleanup_result = cleanup_orphan_ollama()
            if cleanup_result.get("cleaned"):
                print(f"[SelfCore] Cleaned orphan models: {cleanup_result['cleaned']}")
            else:
                print(f"[SelfCore] Ollama cleanup: {cleanup_result.get('status', 'ok')}")
        except Exception as e:
            print(f"[SelfCore] Ollama cleanup skipped: {e}")

    # Try ports 8100-8102
    server = None
    for port in (8100, 8101, 8102):
        try:
            server = HTTPServer(("127.0.0.1", port), SelfCoreHandler)
            print(f"[SelfCore] Backend v4.0 running on http://127.0.0.1:{port}")
            break
        except OSError as e:
            print(f"[SelfCore] Port {port} in use, trying next...")
            if port == 8102:
                print("[SelfCore] ERROR: All ports 8100-8102 in use. Exiting.")
                raise SystemExit(1)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        observer_running = False
        flush_observer_buffer()
        print("\n[SelfCore] Shutting down.")
        server.server_close()
