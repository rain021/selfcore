"""
SelfCore Analysis Engine v2.6 — Phase 4A + 4B-1 + 4B-2 + 4B-3
Platform Adapters + spaCy NLP Pipeline + TF-IDF + Communication Style + Ollama LLM + Profile Suggestions

Provides:
  - ChatGPT export parser (DAG backward traversal)
  - Claude export parser
  - Text paste parser
  - Multi-source merger
  - Language detection
  - Entity extraction with EntityRuler + tech dictionary
  - Preference extraction (lexicon + dependency)
  - TF-IDF topic extraction
  - Communication style analysis
  - Ollama LLM integration (optional)
  - Sanitization layer
"""

import json
import os
import re
import subprocess
import zipfile
import io
import gc
import time
from collections import Counter
from datetime import datetime
from urllib.request import urlopen, Request
from urllib.error import URLError

import psutil
import spacy

try:
    import ijson
except ImportError:
    ijson = None

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")

# ─── Hardcoded Fallback (top 50 terms) ────────────────────────────
HARDCODED_FALLBACK = [
    "Python", "JavaScript", "TypeScript", "Java", "Kotlin", "Swift", "Rust",
    "C++", "C#", "Ruby", "PHP", "SQL", "HTML", "CSS", "Bash",
    "React", "Vue", "Angular", "Svelte", "Next.js", "Tailwind",
    "Node.js", "Express", "FastAPI", "Django", "Flask", "Spring", "Laravel",
    "React Native", "Flutter", "SwiftUI",
    "PostgreSQL", "MySQL", "MongoDB", "Redis", "SQLite", "Firebase",
    "Docker", "Kubernetes", "AWS", "Azure", "GCP", "Terraform", "Vercel",
    "TensorFlow", "PyTorch", "OpenAI", "LangChain",
    "Git", "VS Code", "Electron",
    "GraphQL", "REST", "WebSocket"
]

# ─── Hardcoded Injection Blacklist (top 20) ────────────────────────
HARDCODED_BLACKLIST = [
    "<system>", "</system>",
    "<|im_start|>", "<|im_end|>",
    "<|system|>", "<|user|>", "<|assistant|>",
    "[INST]", "[/INST]",
    "<<SYS>>", "<</SYS>>",
    "```system", "```assistant",
    "ignore previous instructions",
    "ignore all previous",
    "you are now",
    "disregard above",
    "override system prompt",
    "SYSTEM OVERRIDE",
    "jailbreak"
]

# ─── Sentiment Lexicon ──────────────────────────────────────────────
POSITIVE_WORDS = {
    "좋아", "최고", "추천", "편해", "편하", "빠르", "좋은", "훌륭",
    "유용", "강력", "멋진", "사랑", "최애", "선호", "만족", "효율",
    "love", "great", "prefer", "best", "awesome", "like", "amazing",
    "fantastic", "excellent", "wonderful", "favorite", "recommend",
    "enjoy", "good", "nice", "perfect", "powerful", "useful", "fast",
    "efficient", "elegant", "beautiful", "productive", "reliable"
}

NEGATIVE_WORDS = {
    "싫어", "별로", "짜증", "느려", "느린", "구려", "구린", "최악",
    "불편", "복잡", "어려", "어렵", "에러", "버그",
    "hate", "dislike", "terrible", "slow", "awful", "bad", "worst",
    "horrible", "annoying", "frustrating", "painful", "ugly", "broken",
    "buggy", "clunky", "avoid", "sucks", "poor", "complicated", "confusing"
}

# ─── Cached NLP models ──────────────────────────────────────────────
_nlp_en = None
_nlp_ko = None
_tech_dict = None
_korean_stopwords = None
_injection_blacklist = None

# ─── Analysis progress state ────────────────────────────────────────
_analysis_progress = {"status": "idle", "progress": 0, "message": ""}


def set_progress(status, progress, message=""):
    global _analysis_progress
    _analysis_progress = {"status": status, "progress": progress, "message": message}


def get_progress():
    return _analysis_progress.copy()


# ─── Data file loaders ──────────────────────────────────────────────
def load_tech_dictionary():
    global _tech_dict
    if _tech_dict is not None:
        return _tech_dict
    path = os.path.join(DATA_DIR, "tech_dictionary.json")
    try:
        with open(path, "r", encoding="utf-8") as f:
            _tech_dict = json.load(f)
        return _tech_dict
    except Exception:
        _tech_dict = {
            "version": "fallback",
            "patterns": [{"label": "TECH", "pattern": t} for t in HARDCODED_FALLBACK],
            "short_terms_require_context": ["Go", "C", "R", "V", "D"],
            "context_keywords": ["language", "programming", "framework", "library",
                                 "코드", "개발", "프로그래밍", "언어", "프레임워크", "라이브러리"]
        }
        return _tech_dict


def load_korean_stopwords():
    global _korean_stopwords
    if _korean_stopwords is not None:
        return _korean_stopwords
    path = os.path.join(DATA_DIR, "korean_stopwords.json")
    try:
        with open(path, "r", encoding="utf-8") as f:
            _korean_stopwords = json.load(f)
        return _korean_stopwords
    except Exception:
        _korean_stopwords = ["입니다", "합니다", "있습니다", "없습니다", "됩니다",
                             "하는", "있는", "없는", "이것은", "그것은"]
        return _korean_stopwords


def load_injection_blacklist():
    global _injection_blacklist
    if _injection_blacklist is not None:
        return _injection_blacklist
    path = os.path.join(DATA_DIR, "injection_blacklist.json")
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            _injection_blacklist = data.get("patterns", HARDCODED_BLACKLIST)
        return _injection_blacklist
    except Exception:
        _injection_blacklist = HARDCODED_BLACKLIST
        return _injection_blacklist


# ─── spaCy model loader ────────────────────────────────────────────
def get_nlp_en():
    global _nlp_en
    if _nlp_en is None:
        _nlp_en = spacy.load("en_core_web_sm")
    return _nlp_en


def get_nlp_ko():
    global _nlp_ko
    if _nlp_ko is None:
        _nlp_ko = spacy.load("ko_core_news_sm")
    return _nlp_ko


# ═══════════════════════════════════════════════════════════════════
# TASK 5a: ChatGPT Parser (DAG backward traversal)
# ═══════════════════════════════════════════════════════════════════
def parse_chatgpt_export(zip_path_or_bytes):
    """
    Opens ChatGPT export .zip, extracts conversations.json.
    Uses ijson for streaming when available, else standard json.
    For each conversation:
      1. Get current_node, if null -> skip
      2. Backward traverse: current_node -> parent -> parent... until root
      3. Filter: only nodes where message.author.role == "user"
      4. Filter: only string parts
      5. Extract text with timestamp
    Returns: [{"role": "user", "text": "...", "timestamp": ...}, ...]
    """
    set_progress("running", 10, "Opening ChatGPT export...")
    try:
        if isinstance(zip_path_or_bytes, (bytes, bytearray)):
            zf = zipfile.ZipFile(io.BytesIO(zip_path_or_bytes))
        else:
            zf = zipfile.ZipFile(zip_path_or_bytes)
    except Exception:
        set_progress("error", 0, "Invalid zip file")
        return []

    # Find conversations.json
    conv_file = None
    for name in zf.namelist():
        if "conversations.json" in name.lower():
            conv_file = name
            break
    if not conv_file:
        set_progress("error", 0, "conversations.json not found")
        zf.close()
        return []

    set_progress("running", 20, "Parsing conversations...")
    results = []

    try:
        raw_data = zf.read(conv_file)
        conversations = json.loads(raw_data)
        del raw_data
        gc.collect()

        total = len(conversations)
        for idx, conv in enumerate(conversations):
            if total > 0:
                set_progress("running", 20 + int(60 * idx / total),
                             f"Processing conversation {idx+1}/{total}")

            mapping = conv.get("mapping", {})
            current_node_id = conv.get("current_node")

            if not current_node_id or current_node_id not in mapping:
                del conv
                continue

            # Backward traverse from current_node to root
            traversal_ids = []
            node_id = current_node_id
            visited = set()
            while node_id and node_id in mapping and node_id not in visited:
                visited.add(node_id)
                traversal_ids.append(node_id)
                node_id = mapping[node_id].get("parent")

            # Reverse to chronological order
            traversal_ids.reverse()

            # Filter user messages
            for nid in traversal_ids:
                node = mapping.get(nid, {})
                msg = node.get("message")
                if not msg:
                    continue
                author = msg.get("author", {})
                if author.get("role") != "user":
                    continue
                parts = msg.get("content", {}).get("parts", [])
                text_parts = [p for p in parts if isinstance(p, str) and p.strip()]
                if text_parts:
                    ts = msg.get("create_time")
                    timestamp = None
                    if ts:
                        try:
                            timestamp = datetime.fromtimestamp(ts).isoformat()
                        except Exception:
                            pass
                    results.append({
                        "role": "user",
                        "text": " ".join(text_parts),
                        "timestamp": timestamp
                    })

            del conv
            gc.collect()

    except Exception as e:
        set_progress("error", 0, f"Parse error: {str(e)}")
        zf.close()
        return []

    zf.close()
    set_progress("running", 85, f"Extracted {len(results)} user messages")
    return results


# ═══════════════════════════════════════════════════════════════════
# TASK 5b: Claude Parser
# ═══════════════════════════════════════════════════════════════════
def parse_claude_export(zip_path_or_bytes):
    """
    Opens Claude export .zip, finds conversations JSON.
    For each conversation: filter sender=="human", extract text.
    Ignores attachments.extracted_content (Phase 1).
    Returns: [{"role": "user", "text": "...", "timestamp": ...}, ...]
    """
    set_progress("running", 10, "Opening Claude export...")
    try:
        if isinstance(zip_path_or_bytes, (bytes, bytearray)):
            zf = zipfile.ZipFile(io.BytesIO(zip_path_or_bytes))
        else:
            zf = zipfile.ZipFile(zip_path_or_bytes)
    except Exception:
        set_progress("error", 0, "Invalid zip file")
        return []

    # Find conversations JSON
    conv_file = None
    for name in zf.namelist():
        lower = name.lower()
        if lower.endswith(".json") and ("conversation" in lower or "chat" in lower):
            conv_file = name
            break
    # Fallback: any top-level JSON
    if not conv_file:
        for name in zf.namelist():
            if name.endswith(".json") and "/" not in name:
                conv_file = name
                break

    if not conv_file:
        set_progress("error", 0, "No conversations JSON found")
        zf.close()
        return []

    set_progress("running", 20, "Parsing Claude conversations...")
    results = []

    try:
        raw_data = zf.read(conv_file)
        data = json.loads(raw_data)
        del raw_data

        # Handle both array format and object-with-array format
        conversations = data if isinstance(data, list) else data.get("conversations", data.get("chats", []))
        if isinstance(conversations, dict):
            conversations = [conversations]

        total = len(conversations)
        for idx, conv in enumerate(conversations):
            if total > 0:
                set_progress("running", 20 + int(60 * idx / total),
                             f"Processing conversation {idx+1}/{total}")

            messages = conv.get("chat_messages", conv.get("messages", []))
            if not isinstance(messages, list):
                continue

            # Sort by created_at if present
            try:
                messages = sorted(messages, key=lambda m: m.get("created_at", m.get("timestamp", "")))
            except Exception:
                pass

            for msg in messages:
                sender = msg.get("sender", msg.get("role", ""))
                if sender != "human" and sender != "user":
                    continue

                # Extract text from either "text" field or content[].text
                text = ""
                if isinstance(msg.get("text"), str):
                    text = msg["text"]
                elif isinstance(msg.get("content"), list):
                    parts = []
                    for part in msg["content"]:
                        if isinstance(part, dict) and part.get("type") == "text":
                            parts.append(part.get("text", ""))
                        elif isinstance(part, str):
                            parts.append(part)
                    text = " ".join(parts)
                elif isinstance(msg.get("content"), str):
                    text = msg["content"]

                if text.strip():
                    ts = msg.get("created_at", msg.get("timestamp"))
                    results.append({
                        "role": "user",
                        "text": text.strip(),
                        "timestamp": ts
                    })

        del data
        gc.collect()

    except Exception as e:
        set_progress("error", 0, f"Parse error: {str(e)}")
        zf.close()
        return []

    zf.close()
    set_progress("running", 85, f"Extracted {len(results)} user messages")
    return results


# ═══════════════════════════════════════════════════════════════════
# TASK 5c: Text Paste Parser
# ═══════════════════════════════════════════════════════════════════
# Turn markers
USER_MARKERS = re.compile(
    r'^(?:User|Human|나|사용자)\s*:', re.MULTILINE | re.IGNORECASE
)
AI_MARKERS = re.compile(
    r'^(?:Assistant|AI|Claude|GPT|ChatGPT|봇|Bot)\s*:', re.MULTILINE | re.IGNORECASE
)
ALL_MARKERS = re.compile(
    r'^(?:User|Human|나|사용자|Assistant|AI|Claude|GPT|ChatGPT|봇|Bot)\s*:', re.MULTILINE | re.IGNORECASE
)


def parse_text_paste(text):
    """
    Detects conversation format by turn markers.
    Conversation mode: split by markers, keep user turns only.
    Free text mode: treat entire text as single user document.
    Returns: [{"role": "user", "text": "...", "timestamp": None}, ...]
    """
    if not text or not text.strip():
        return []

    set_progress("running", 30, "Parsing text input...")

    # Check for conversation markers
    user_matches = USER_MARKERS.findall(text)
    ai_matches = AI_MARKERS.findall(text)

    if user_matches or ai_matches:
        # Conversation mode
        results = []
        # Split text by all markers
        parts = ALL_MARKERS.split(text)
        # Find markers in order
        markers = ALL_MARKERS.finditer(text)
        marker_list = [m.group() for m in markers]

        # First part before any marker (ignore if empty)
        idx = 0
        for i, marker in enumerate(marker_list):
            segment = parts[i + 1].strip() if i + 1 < len(parts) else ""
            marker_lower = marker.lower()
            is_user = any(kw in marker_lower for kw in ["user", "human", "나", "사용자"])
            if is_user and segment:
                results.append({
                    "role": "user",
                    "text": segment,
                    "timestamp": None
                })

        set_progress("running", 80, f"Extracted {len(results)} user messages")
        return results
    else:
        # Free text mode
        set_progress("running", 80, "Treating as free text")
        return [{
            "role": "user",
            "text": text.strip(),
            "timestamp": None
        }]


# ═══════════════════════════════════════════════════════════════════
# TASK 5d: Multi-source Merger
# ═══════════════════════════════════════════════════════════════════
def merge_analysis_results(results):
    """
    Merges extracted data from multiple platform parsers.
    - Entities: union (deduplicated, case-insensitive)
    - Preferences: if conflict, keep BOTH and mark as "conflict"
    - Tech tags: union
    - Topics: merge and re-rank by combined weight
    Returns: merged dict with conflicts flagged
    """
    merged_tech = {}
    merged_people = {}
    merged_orgs = {}
    merged_preferences = []
    conflicts = []
    total_messages = 0

    for result in results:
        source = result.get("source", "unknown")
        entities = result.get("entities", {})
        preferences = result.get("preferences", [])
        stats = result.get("stats", {})
        total_messages += stats.get("total_messages", 0)

        # Merge tech entities (case-insensitive dedup)
        for tech in entities.get("tech", []):
            name = tech.get("name", "")
            key = name.lower()
            if key in merged_tech:
                merged_tech[key]["count"] += tech.get("count", 1)
            else:
                merged_tech[key] = {"name": name, "count": tech.get("count", 1)}

        # Merge people
        for person in entities.get("people", []):
            name = person.get("name", "")
            key = name.lower()
            if key in merged_people:
                merged_people[key]["count"] += person.get("count", 1)
            else:
                merged_people[key] = {"name": name, "count": person.get("count", 1)}

        # Merge orgs
        for org in entities.get("orgs", []):
            name = org.get("name", "")
            key = name.lower()
            if key in merged_orgs:
                merged_orgs[key]["count"] += org.get("count", 1)
            else:
                merged_orgs[key] = {"name": name, "count": org.get("count", 1)}

        # Merge preferences, check for conflicts
        for pref in preferences:
            target = pref.get("target", "").lower()
            sentiment = pref.get("sentiment", "")
            existing = [p for p in merged_preferences if p.get("target", "").lower() == target]
            if existing:
                for e in existing:
                    if e.get("sentiment") != sentiment:
                        conflicts.append({
                            "target": pref.get("target"),
                            "source_a": e.get("source", "unknown"),
                            "sentiment_a": e.get("sentiment"),
                            "source_b": source,
                            "sentiment_b": sentiment
                        })
                        e["conflict"] = True
                        pref["conflict"] = True
            pref["source"] = source
            merged_preferences.append(pref)

    return {
        "entities": {
            "tech": sorted(merged_tech.values(), key=lambda x: x["count"], reverse=True),
            "people": sorted(merged_people.values(), key=lambda x: x["count"], reverse=True),
            "orgs": sorted(merged_orgs.values(), key=lambda x: x["count"], reverse=True),
        },
        "preferences": merged_preferences,
        "conflicts": conflicts,
        "stats": {"total_messages": total_messages},
    }


# ═══════════════════════════════════════════════════════════════════
# TASK 6a: Language Detection
# ═══════════════════════════════════════════════════════════════════
KO_ENDINGS = re.compile(r'(?:했어|입니다|해줘|할게|합니다|했습니다|해요|세요|거든|잖아|는데|인데|네요|군요|지요|나요|했지|거야|건데|이야|에요|예요|어요|아요)')
EN_ENDINGS = re.compile(r'(?:ed|ing|ly|tion|ment|ness|able|ible|ous|ive|ful|less|ise|ize)\b', re.IGNORECASE)


def detect_language(text):
    """
    1st: Check sentence-final morphemes
    2nd: Character ratio (가-힣)
    3rd: Default -> "ko"
    """
    if not text:
        return "ko"

    # 1st pass: morpheme endings
    ko_count = len(KO_ENDINGS.findall(text))
    en_count = len(EN_ENDINGS.findall(text))

    if ko_count > 0 and ko_count > en_count:
        return "ko"
    if en_count > 0 and en_count > ko_count:
        return "en"

    # 2nd pass: character ratio
    total_chars = len(re.findall(r'\S', text))
    if total_chars == 0:
        return "ko"
    korean_chars = len(re.findall(r'[가-힣]', text))
    ratio = korean_chars / total_chars
    if ratio >= 0.3:
        return "ko"
    if ratio < 0.05 and total_chars > 10:
        return "en"

    # 3rd: default
    return "ko"


# ═══════════════════════════════════════════════════════════════════
# TASK 6b: Entity Extraction with EntityRuler
# ═══════════════════════════════════════════════════════════════════
def _build_entity_ruler(nlp):
    """Build and add EntityRuler to pipeline BEFORE NER."""
    tech_dict = load_tech_dictionary()
    patterns = tech_dict.get("patterns", [])

    # Remove existing entity_ruler if present
    if "entity_ruler" in nlp.pipe_names:
        nlp.remove_pipe("entity_ruler")

    ruler = nlp.add_pipe("entity_ruler", before="ner")
    ruler.add_patterns(patterns)
    return ruler


def _regex_tech_fallback(text, tech_dict):
    """
    Regex-based fallback for tech detection when spaCy tokenizer
    merges tech names with Korean particles (e.g., 'TypeScript로').
    """
    patterns = tech_dict.get("patterns", [])
    short_terms = set(tech_dict.get("short_terms_require_context", []))
    context_kw = set(w.lower() for w in tech_dict.get("context_keywords", []))
    found = Counter()

    # Build a set of pattern texts (longer patterns first to avoid substring issues)
    pattern_texts = sorted(
        [p["pattern"] for p in patterns if len(p["pattern"]) > 2],
        key=len, reverse=True
    )

    text_lower = text.lower()
    for pt in pattern_texts:
        pt_lower = pt.lower()
        if pt in short_terms:
            # Short terms need word boundary + context
            if re.search(r'\b' + re.escape(pt) + r'\b', text):
                has_ctx = any(kw in text_lower for kw in context_kw)
                if has_ctx:
                    found[pt] += len(re.findall(r'\b' + re.escape(pt) + r'\b', text))
        else:
            # Normal matching (case-insensitive for longer terms)
            matches = re.findall(re.escape(pt_lower), text_lower)
            if matches:
                found[pt] += len(matches)

    return found


def extract_entities(texts):
    """
    1. Load tech_dictionary patterns into EntityRuler
    2. Short terms: only match if UPPERCASE and context present
    3. Run spaCy pipeline + regex fallback for Korean text
    4. Collect TECH + NER entities
    5. Deduplicate and count
    Returns: {"tech": [...], "people": [...], "orgs": [...], "all_entities": [...]}
    """
    if not texts:
        return {"tech": [], "people": [], "orgs": [], "all_entities": []}

    tech_dict = load_tech_dictionary()
    short_terms = set(tech_dict.get("short_terms_require_context", []))
    context_kw = set(w.lower() for w in tech_dict.get("context_keywords", []))

    # Detect dominant language
    sample = " ".join(texts[:20])
    lang = detect_language(sample)

    # Load appropriate model
    nlp = spacy.load("en_core_web_sm") if lang == "en" else spacy.load("ko_core_news_sm")
    _build_entity_ruler(nlp)

    tech_counter = Counter()
    people_counter = Counter()
    org_counter = Counter()
    all_entities = Counter()

    set_progress("running", 50, "Extracting entities...")

    for i, text in enumerate(texts):
        if len(text) > 10000:
            text = text[:10000]
        doc = nlp(text)

        # Collect sentence-level context for short term validation
        for sent in doc.sents:
            sent_text_lower = sent.text.lower()
            sent_has_context = any(kw in sent_text_lower for kw in context_kw)

            for ent in sent.ents:
                label = ent.label_
                ent_text = ent.text.strip()

                if not ent_text:
                    continue

                if label == "TECH":
                    # Short term check
                    if ent_text in short_terms:
                        original_segment = text[ent.start_char:ent.end_char]
                        if original_segment != ent_text or not sent_has_context:
                            continue
                    tech_counter[ent_text] += 1
                    all_entities[ent_text] += 1
                elif label == "PERSON":
                    people_counter[ent_text] += 1
                    all_entities[ent_text] += 1
                elif label in ("ORG", "PRODUCT"):
                    org_counter[ent_text] += 1
                    all_entities[ent_text] += 1

        # Regex fallback: catch tech terms missed by spaCy tokenizer
        # (especially Korean text where particles attach to English words)
        regex_found = _regex_tech_fallback(text, tech_dict)
        for term, count in regex_found.items():
            if term not in tech_counter:
                tech_counter[term] += count
                all_entities[term] += count

    return {
        "tech": [{"name": n, "count": c} for n, c in tech_counter.most_common()],
        "people": [{"name": n, "count": c} for n, c in people_counter.most_common()],
        "orgs": [{"name": n, "count": c} for n, c in org_counter.most_common()],
        "all_entities": [{"name": n, "count": c} for n, c in all_entities.most_common()],
    }


# ═══════════════════════════════════════════════════════════════════
# TASK 6c: Preference Extraction
# ═══════════════════════════════════════════════════════════════════
def extract_preferences(texts, entities=None):
    """
    For each sentence containing a TECH entity:
    1st pass: Lexicon matching (positive/negative words within 5 tokens)
    2nd pass: Dependency parse confirmation
    Returns: [{"target": "...", "sentiment": "Like"/"Dislike", "confidence": "high"/"medium"}, ...]
    """
    if not texts:
        return []

    if entities is None:
        entities = extract_entities(texts)

    tech_names = set(t["name"].lower() for t in entities.get("tech", []))
    if not tech_names:
        return []

    sample = " ".join(texts[:20])
    lang = detect_language(sample)
    nlp = spacy.load("en_core_web_sm") if lang == "en" else spacy.load("ko_core_news_sm")
    _build_entity_ruler(nlp)

    preferences = {}

    set_progress("running", 70, "Extracting preferences...")

    for text in texts:
        if len(text) > 10000:
            text = text[:10000]
        doc = nlp(text)

        for sent in doc.sents:
            sent_text_lower = sent.text.lower()

            # Find tech entities in this sentence
            techs_in_sent = []
            for ent in sent.ents:
                if ent.label_ == "TECH" and ent.text.lower() in tech_names:
                    techs_in_sent.append(ent)

            if not techs_in_sent:
                continue

            # Tokenize sentence for proximity check
            tokens = [t for t in sent]

            for tech_ent in techs_in_sent:
                tech_name = tech_ent.text
                tech_key = tech_name.lower()

                # 1st pass: Lexicon matching
                sentiment = None
                confidence = "medium"

                # Check tokens within 5 positions of tech entity
                tech_start = tech_ent.start - sent.start
                tech_end = tech_ent.end - sent.start
                window_start = max(0, tech_start - 5)
                window_end = min(len(tokens), tech_end + 5)

                pos_found = False
                neg_found = False

                for ti in range(window_start, window_end):
                    token_text = tokens[ti].text.lower()
                    token_lemma = tokens[ti].lemma_.lower()
                    for pw in POSITIVE_WORDS:
                        if pw in token_text or pw in token_lemma:
                            pos_found = True
                            break
                    for nw in NEGATIVE_WORDS:
                        if nw in token_text or nw in token_lemma:
                            neg_found = True
                            break

                if pos_found and not neg_found:
                    sentiment = "Like"
                elif neg_found and not pos_found:
                    sentiment = "Dislike"
                elif pos_found and neg_found:
                    sentiment = "Like"
                    confidence = "low"

                if not sentiment:
                    continue

                # 2nd pass: Dependency parsing confirmation
                try:
                    for token in sent:
                        if token.dep_ in ("ROOT", "root") and token.pos_ == "VERB":
                            for child in token.children:
                                if child.dep_ in ("dobj", "obj", "nsubj"):
                                    if child.text.lower() == tech_key or tech_key in child.text.lower():
                                        confidence = "high"
                                        break
                except Exception:
                    pass

                # Store (keep highest confidence)
                if tech_key not in preferences or confidence == "high":
                    preferences[tech_key] = {
                        "target": tech_name,
                        "sentiment": sentiment,
                        "confidence": confidence
                    }

    return list(preferences.values())


# ═══════════════════════════════════════════════════════════════════
# Phase 4B-1: TF-IDF Topic Extraction
# ═══════════════════════════════════════════════════════════════════
def extract_topics(texts, language=None, min_messages=20):
    """
    TF-IDF topic extraction. Only runs if len(texts) >= min_messages.
    Returns top keywords weighted by TF-IDF score, filtered to repeated terms.
    """
    if not texts or len(texts) < min_messages:
        return {
            "skipped": True,
            "reason": "insufficient_data",
            "count": len(texts) if texts else 0
        }

    from sklearn.feature_extraction.text import TfidfVectorizer

    # Detect language if not specified
    if language is None:
        sample = " ".join(texts[:20])
        language = detect_language(sample)

    # Build stopwords
    if language == "ko":
        ko_stops = load_korean_stopwords()
        vectorizer = TfidfVectorizer(
            max_features=100,
            min_df=2,
            stop_words=ko_stops,
            token_pattern=r'[a-zA-Z0-9가-힣\+\#\.]+',
        )
    else:
        vectorizer = TfidfVectorizer(
            max_features=100,
            min_df=2,
            stop_words='english',
        )

    try:
        tfidf_matrix = vectorizer.fit_transform(texts)
    except ValueError:
        # All documents are empty or only stopwords
        return {
            "skipped": True,
            "reason": "no_valid_terms",
            "count": len(texts)
        }

    feature_names = vectorizer.get_feature_names_out()

    # Calculate average TF-IDF weight per term across all documents
    avg_weights = tfidf_matrix.mean(axis=0).A1  # dense 1D array

    # Count how many documents each term appears in (document frequency)
    doc_counts = (tfidf_matrix > 0).sum(axis=0).A1

    # Build keyword list
    keywords = []
    for idx, (word, weight, count) in enumerate(zip(feature_names, avg_weights, doc_counts)):
        count_int = int(count)
        keywords.append({
            "word": word,
            "weight": round(float(weight), 4),
            "count": count_int
        })

    # Sort by weight descending
    keywords.sort(key=lambda x: x["weight"], reverse=True)

    # Filter: only repeated keywords (count >= 3) are significant topics
    significant = [kw for kw in keywords if kw["count"] >= 3]

    # Return top 20
    return {
        "skipped": False,
        "top_keywords": significant[:20],
        "total_documents": len(texts)
    }


# ═══════════════════════════════════════════════════════════════════
# Phase 4B-1: Communication Style Analyzer
# ═══════════════════════════════════════════════════════════════════
_QUESTION_KO = re.compile(r'(?:어떻게|뭐|뭘|무엇|왜|어디|언제|몇|누가|누구|할까|할까요|인가요|인가|인지|건가요|건가)')
_QUESTION_EN = re.compile(r'\b(?:how|what|why|where|when|which|who|whom|whose|can|could|would|should|is|are|do|does|did)\b', re.IGNORECASE)
_CODE_PATTERNS = re.compile(r'(?:```|def\s+\w+|function\s+\w+|import\s+\w+|from\s+\w+\s+import|const\s+\w+|var\s+\w+|let\s+\w+|class\s+\w+|=>|\.map\(|\.filter\(|\(\)\s*\{)')
_FORMAL_KO = re.compile(r'(?:합니다|입니다|습니다|됩니다|겠습니다|하십시오|주십시오|드립니다|있습니다|없습니다|합니까|십시오)')
_CASUAL_KO = re.compile(r'(?:해줘|해줄래|해봐|할게|했어|했지|인데|거든|잖아|인걸|같아|이야|건데|해요|에요|예요|어요|아요|해주세요|해볼게|해볼까)')


def analyze_communication_style(texts):
    """
    Analyzes HOW the user communicates across their messages.
    Returns metrics on length, question ratio, code ratio, formality, language mix, verbosity.
    """
    if not texts:
        return {
            "avg_message_length": 0,
            "question_ratio": 0.0,
            "code_ratio": 0.0,
            "formality": "mixed",
            "language_mix": {"ko": 0.0, "en": 0.0},
            "verbosity": "concise",
            "summary": ""
        }

    total = len(texts)
    word_counts = []
    question_count = 0
    code_count = 0
    formal_count = 0
    casual_count = 0
    total_korean_chars = 0
    total_english_chars = 0
    total_chars = 0

    for text in texts:
        # Word count
        words = re.findall(r'\S+', text)
        word_counts.append(len(words))

        # Question detection
        is_question = False
        if text.rstrip().endswith('?'):
            is_question = True
        elif _QUESTION_KO.search(text):
            is_question = True
        elif _QUESTION_EN.search(text) and text.rstrip().endswith('?'):
            is_question = True
        if is_question:
            question_count += 1

        # Code detection
        if _CODE_PATTERNS.search(text):
            code_count += 1

        # Formality detection (Korean)
        formal_hits = len(_FORMAL_KO.findall(text))
        casual_hits = len(_CASUAL_KO.findall(text))
        formal_count += formal_hits
        casual_count += casual_hits

        # Language character counts
        ko_chars = len(re.findall(r'[가-힣]', text))
        en_chars = len(re.findall(r'[a-zA-Z]', text))
        total_korean_chars += ko_chars
        total_english_chars += en_chars
        total_chars += ko_chars + en_chars

    # Calculate metrics
    avg_length = sum(word_counts) / total if total > 0 else 0
    question_ratio = question_count / total if total > 0 else 0.0
    code_ratio = code_count / total if total > 0 else 0.0

    # Formality
    if formal_count > casual_count * 2:
        formality = "formal"
    elif casual_count > formal_count * 2:
        formality = "casual"
    else:
        # Check if there's enough Korean signal to judge
        if formal_count == 0 and casual_count == 0:
            formality = "mixed"
        else:
            formality = "mixed"

    # Language mix
    if total_chars > 0:
        ko_pct = round(total_korean_chars / total_chars, 2)
        en_pct = round(total_english_chars / total_chars, 2)
    else:
        ko_pct = 0.0
        en_pct = 0.0

    # Verbosity
    if avg_length < 30:
        verbosity = "concise"
    elif avg_length <= 80:
        verbosity = "moderate"
    else:
        verbosity = "detailed"

    # Auto-generate summary
    dominant_lang = "ko" if ko_pct >= en_pct else "en"
    summary = _generate_style_summary(
        avg_length, question_ratio, code_ratio, formality, verbosity, dominant_lang
    )

    return {
        "avg_message_length": round(avg_length, 1),
        "question_ratio": round(question_ratio, 2),
        "code_ratio": round(code_ratio, 2),
        "formality": formality,
        "language_mix": {"ko": ko_pct, "en": en_pct},
        "verbosity": verbosity,
        "summary": summary
    }


def _generate_style_summary(avg_len, q_ratio, code_ratio, formality, verbosity, lang):
    """Generate a one-line communication style summary."""
    if lang == "ko":
        parts = []
        if verbosity == "concise":
            parts.append("간결한")
        elif verbosity == "moderate":
            parts.append("적당한 길이의")
        else:
            parts.append("상세한")

        if formality == "formal":
            parts.append("격식체")
        elif formality == "casual":
            parts.append("캐주얼한 톤")
        else:
            parts.append("혼합 톤")

        extras = []
        if q_ratio > 0.3:
            extras.append("질문을 자주 함")
        if code_ratio > 0.2:
            extras.append("코드를 자주 공유")

        base = " ".join(parts) + " 스타일"
        if extras:
            base += ", " + ", ".join(extras)
        return base
    else:
        parts = []
        if verbosity == "concise":
            parts.append("Concise")
        elif verbosity == "moderate":
            parts.append("Moderate-length")
        else:
            parts.append("Detailed")

        if formality == "formal":
            parts.append("formal")
        elif formality == "casual":
            parts.append("casual")
        else:
            parts.append("mixed-tone")

        extras = []
        if q_ratio > 0.3:
            extras.append("asks many questions")
        if code_ratio > 0.2:
            extras.append("frequently shares code")

        base = " and ".join(parts) + " style"
        if extras:
            base += ", " + ", ".join(extras)
        return base


# ═══════════════════════════════════════════════════════════════════
# Phase 4B-2: Ollama LLM Integration
# ═══════════════════════════════════════════════════════════════════
OLLAMA_BASE = "http://127.0.0.1:11434"
OLLAMA_MODEL = "llama3.2:3b"


def _ollama_request(method, path, body=None, timeout=10):
    """Safe HTTP request to Ollama. Returns (dict, error_string)."""
    url = f"{OLLAMA_BASE}{path}"
    try:
        data = json.dumps(body).encode("utf-8") if body else None
        req = Request(url, data=data, method=method)
        if data:
            req.add_header("Content-Type", "application/json")
        with urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8")), None
    except URLError as e:
        return None, f"connection_error: {e.reason}" if hasattr(e, 'reason') else str(e)
    except Exception as e:
        return None, str(e)


def _ollama_stream_request(path, body, timeout=300):
    """Streaming HTTP request to Ollama. Yields (line_dict, error)."""
    url = f"{OLLAMA_BASE}{path}"
    try:
        data = json.dumps(body).encode("utf-8")
        req = Request(url, data=data, method="POST")
        req.add_header("Content-Type", "application/json")
        with urlopen(req, timeout=timeout) as resp:
            for line in resp:
                line = line.decode("utf-8").strip()
                if line:
                    try:
                        yield json.loads(line), None
                    except json.JSONDecodeError:
                        pass
    except Exception as e:
        yield None, str(e)


def _get_gpu_info():
    """Get GPU utilization. Returns (available, usage_percent) or (False, None)."""
    try:
        import pynvml
        pynvml.nvmlInit()
        handle = pynvml.nvmlDeviceGetHandleByIndex(0)
        util = pynvml.nvmlDeviceGetUtilizationRates(handle)
        pct = float(util.gpu)
        pynvml.nvmlShutdown()
        return True, pct
    except Exception:
        return False, None


_ollama_status_cache = {"time": 0, "result": None}

def check_ollama_status(force=False):
    """
    Check Ollama installation, server status, model availability, and GPU.
    Caches result for 10 seconds. Pass force=True to bypass cache.
    NEVER crashes.
    """
    # Return cached result if fresh (< 10 seconds)
    if not force and _ollama_status_cache["result"] is not None:
        if time.time() - _ollama_status_cache["time"] < 10:
            return _ollama_status_cache["result"]

    result = {
        "installed": False,
        "running": False,
        "model_available": False,
        "model_name": OLLAMA_MODEL,
        "gpu_available": False,
        "gpu_usage_percent": None,
    }
    try:
        # Check if ollama binary exists (fast PATH check first)
        import shutil
        if shutil.which("ollama") is None:
            result["installed"] = False
        else:
            try:
                si = subprocess.STARTUPINFO()
                si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                si.wShowWindow = 0
                proc = subprocess.run(
                    ["ollama", "--version"], capture_output=True, timeout=2,
                    startupinfo=si, creationflags=subprocess.CREATE_NO_WINDOW
                )
                result["installed"] = proc.returncode == 0
            except (FileNotFoundError, subprocess.TimeoutExpired):
                result["installed"] = False
            except Exception:
                result["installed"] = False

        # Check server running (0.5s timeout — localhost responds in ms if up)
        data, err = _ollama_request("GET", "/api/tags", timeout=0.5)
        if data is not None:
            result["running"] = True
            models = data.get("models", [])
            for m in models:
                if OLLAMA_MODEL in m.get("name", ""):
                    result["model_available"] = True
                    break

        # GPU
        gpu_ok, gpu_pct = _get_gpu_info()
        result["gpu_available"] = gpu_ok
        result["gpu_usage_percent"] = gpu_pct

    except Exception:
        pass

    # Update cache
    _ollama_status_cache["time"] = time.time()
    _ollama_status_cache["result"] = result
    return result


def start_ollama_if_needed():
    """Start Ollama server if installed but not running. Returns True if running."""
    try:
        # Already running?
        data, err = _ollama_request("GET", "/api/tags", timeout=0.5)
        if data is not None:
            return True

        # Try to start
        try:
            si = subprocess.STARTUPINFO()
            si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            si.wShowWindow = 0
            subprocess.Popen(
                ["ollama", "serve"],
                startupinfo=si,
                creationflags=subprocess.CREATE_NO_WINDOW,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except FileNotFoundError:
            print("[SelfCore] Ollama not found in PATH")
            return False
        except Exception as e:
            print(f"[SelfCore] Failed to start Ollama: {e}")
            return False

        # Wait for server to come up (poll every 1s, max 15s)
        for _ in range(15):
            time.sleep(1)
            data, err = _ollama_request("GET", "/api/tags", timeout=1)
            if data is not None:
                print("[SelfCore] Ollama server started")
                return True

        print("[SelfCore] Ollama start timeout")
        return False

    except Exception:
        return False


def pull_model_if_needed(progress_callback=None):
    """Pull model if not present. Returns True when done."""
    try:
        # Check if model exists
        status = check_ollama_status()
        if not status["running"]:
            return False
        if status["model_available"]:
            return True

        # Pull with streaming progress
        print(f"[SelfCore] Pulling model {OLLAMA_MODEL}...")
        for chunk, err in _ollama_stream_request(
            "/api/pull", {"name": OLLAMA_MODEL, "stream": True}, timeout=600
        ):
            if err:
                print(f"[SelfCore] Pull error: {err}")
                return False
            if chunk:
                status_text = chunk.get("status", "")
                total = chunk.get("total", 0)
                completed = chunk.get("completed", 0)
                pct = int(completed / total * 100) if total > 0 else 0
                if progress_callback:
                    progress_callback(pct, status_text)
                if status_text == "success":
                    print(f"[SelfCore] Model {OLLAMA_MODEL} pulled successfully")
                    return True

        # Verify
        status2 = check_ollama_status()
        return status2["model_available"]

    except Exception as e:
        print(f"[SelfCore] Pull model error: {e}")
        return False


def _unload_model(model_name):
    """Send keep_alive=0 to unload a model from memory."""
    try:
        _ollama_request("POST", "/api/generate", {
            "model": model_name,
            "prompt": "",
            "keep_alive": 0,
        }, timeout=5)
    except Exception:
        pass


def cleanup_orphan_ollama():
    """
    Called on startup. Unloads any models left in GPU memory from crashed sessions.
    NEVER crashes.
    """
    try:
        data, err = _ollama_request("GET", "/api/tags", timeout=3)
        if data is None:
            # Ollama not running, nothing to clean
            return {"status": "not_running", "cleaned": []}

        # Check loaded models
        ps_data, ps_err = _ollama_request("GET", "/api/ps", timeout=3)
        if ps_data is None:
            return {"status": "ok", "cleaned": []}

        loaded = ps_data.get("models", [])
        cleaned = []
        for m in loaded:
            model_name = m.get("name", "")
            if model_name:
                print(f"[SelfCore] Unloading orphan model: {model_name}")
                _unload_model(model_name)
                cleaned.append(model_name)

        return {"status": "ok", "cleaned": cleaned}

    except Exception as e:
        print(f"[SelfCore] Cleanup error (non-fatal): {e}")
        return {"status": "error", "cleaned": [], "error": str(e)}


def run_profile_extraction(entities, topics, preferences, communication_style, gpu_mode=True):
    """
    Use Ollama LLM for deep profile extraction.
    Returns parsed profile dict or None if LLM unavailable/fails.
    """
    def _try_unload():
        try:
            _unload_model(OLLAMA_MODEL)
        except Exception:
            pass
        # Verify unloaded
        try:
            ps_data, _ = _ollama_request("GET", "/api/ps", timeout=3)
            if ps_data:
                for m in ps_data.get("models", []):
                    if OLLAMA_MODEL in m.get("name", ""):
                        _unload_model(OLLAMA_MODEL)
        except Exception:
            pass

    try:
        # Pre-flight: GPU check
        if gpu_mode:
            gpu_ok, gpu_pct = _get_gpu_info()
            if gpu_ok and gpu_pct is not None and gpu_pct > 80:
                return {"error": "gpu_busy", "message": f"GPU is busy ({gpu_pct}%). Try CPU mode."}

        # Pre-flight: free spaCy models
        global _nlp_en, _nlp_ko
        if _nlp_en is not None:
            del _nlp_en
            _nlp_en = None
        if _nlp_ko is not None:
            del _nlp_ko
            _nlp_ko = None
        gc.collect()

        # Pre-flight: RAM check
        mem = psutil.virtual_memory()
        if mem.available < 2 * 1024 * 1024 * 1024:  # 2GB
            return {"error": "low_memory", "message": f"Not enough RAM ({mem.available // (1024*1024)}MB available). Close other apps."}

        # Check Ollama
        status = check_ollama_status()
        if not status["running"]:
            return None
        if not status["model_available"]:
            return None

        # Build prompt
        tech_list = [t["name"] for t in entities.get("tech", [])][:20]
        pref_list = [f"{p['target']}: {p['sentiment']}" for p in preferences[:10]]
        topic_list = [kw["word"] for kw in (topics.get("top_keywords", []) if isinstance(topics, dict) else [])][:10]
        style_summary = communication_style.get("summary", "") if isinstance(communication_style, dict) else ""

        system_prompt = (
            "You are a profile extraction AI. Given the analyzed data below, "
            "create a structured user profile. Output ONLY valid JSON matching "
            "the exact schema provided. Do not add explanations or markdown."
        )

        user_prompt = (
            f"Analyzed data:\n"
            f"- Tech stack used: {', '.join(tech_list) if tech_list else 'None detected'}\n"
            f"- Preferences: {'; '.join(pref_list) if pref_list else 'None detected'}\n"
            f"- Frequent topics: {', '.join(topic_list) if topic_list else 'None detected'}\n"
            f"- Communication style: {style_summary}\n\n"
            f"Fill this JSON schema exactly:\n"
            f'{{"occupation_guess": "", "primary_skills": [], "interests": [], '
            f'"communication_style": "", "current_focus": "", "personality_traits": []}}'
        )

        # LLM call
        body = {
            "model": OLLAMA_MODEL,
            "system": system_prompt,
            "prompt": user_prompt,
            "stream": False,
            "options": {"num_ctx": 2048, "temperature": 0.3},
            "keep_alive": 0,
        }

        resp_data, resp_err = _ollama_request("POST", "/api/generate", body, timeout=120)
        if resp_err or not resp_data:
            return None

        raw_response = resp_data.get("response", "")

        # Parse response
        parsed = _parse_llm_json(raw_response)
        if parsed is not None:
            _try_unload()
            return parsed

        # Retry with simplified prompt
        retry_body = {
            "model": OLLAMA_MODEL,
            "prompt": f"Based on these skills: {', '.join(tech_list[:10])}. "
                      f"Output ONLY this JSON: "
                      f'{{"occupation_guess": "...", "primary_skills": [...], '
                      f'"interests": [...], "communication_style": "...", '
                      f'"current_focus": "...", "personality_traits": [...]}}',
            "stream": False,
            "options": {"num_ctx": 1024, "temperature": 0.2},
            "keep_alive": 0,
        }
        retry_data, retry_err = _ollama_request("POST", "/api/generate", retry_body, timeout=60)
        if retry_data:
            parsed = _parse_llm_json(retry_data.get("response", ""))
            if parsed is not None:
                _try_unload()
                return parsed

        _try_unload()
        return None

    except Exception as e:
        print(f"[SelfCore] LLM extraction error: {e}")
        return None
    finally:
        # ALWAYS try to unload model
        _try_unload()


def _parse_llm_json(raw):
    """Parse LLM response, stripping markdown fences if present."""
    if not raw or not raw.strip():
        return None
    text = raw.strip()
    # Strip markdown code fences
    if text.startswith("```"):
        lines = text.split("\n")
        # Remove first and last fence lines
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()

    try:
        data = json.loads(text)
        expected_keys = {"occupation_guess", "primary_skills", "interests",
                         "communication_style", "current_focus", "personality_traits"}
        if isinstance(data, dict) and expected_keys.issubset(set(data.keys())):
            return data
        # Partial match is OK — fill missing keys
        if isinstance(data, dict):
            for k in expected_keys:
                if k not in data:
                    data[k] = [] if k in ("primary_skills", "interests", "personality_traits") else ""
            return data
    except json.JSONDecodeError:
        # Try to find JSON in the text
        match = re.search(r'\{[^{}]*\}', text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass
    return None


# ═══════════════════════════════════════════════════════════════════
# TASK 9: Sanitization Layer
# ═══════════════════════════════════════════════════════════════════
def sanitize_profile_data(profile):
    """
    Runs AFTER user confirmation, BEFORE saving to .self file.
    1. Load injection_blacklist.json (or hardcoded fallback)
    2. Check every string value recursively
    3. Remove blacklisted patterns (case-insensitive)
    4. Do NOT remove normal HTML tags (<div>, <span>)
    Returns: sanitized profile
    """
    blacklist = load_injection_blacklist()
    warnings = []

    def sanitize_value(value, path=""):
        if isinstance(value, str):
            cleaned = value
            for pattern in blacklist:
                if pattern.lower() in cleaned.lower():
                    warnings.append(f"Removed '{pattern}' from {path}")
                    # Case-insensitive removal
                    idx = cleaned.lower().find(pattern.lower())
                    while idx >= 0:
                        cleaned = cleaned[:idx] + cleaned[idx + len(pattern):]
                        idx = cleaned.lower().find(pattern.lower())
            return cleaned
        elif isinstance(value, dict):
            return {k: sanitize_value(v, f"{path}.{k}") for k, v in value.items()}
        elif isinstance(value, list):
            return [sanitize_value(v, f"{path}[{i}]") for i, v in enumerate(value)]
        return value

    sanitized = sanitize_value(profile)
    if warnings:
        print(f"[SelfCore] Sanitization warnings: {warnings}")
    return sanitized


# ═══════════════════════════════════════════════════════════════════
# Profile Suggestion Generator (Phase 4B-3)
# ═══════════════════════════════════════════════════════════════════
def generate_profile_updates(analysis_result, current_profile):
    """
    Compare analysis_result against current_profile and generate suggestions.

    Each suggestion:
      {
        "id": str,            # unique key for UI
        "type": "add_tech"|"add_interest"|"update_occupation"|"add_tool"|
                "add_project"|"update_language"|"update_style"|"remove_tech",
        "field": str,         # dotted path (e.g. "context_tags.tech")
        "value": any,         # proposed value
        "old_value": any,     # current value (for updates/removes)
        "confidence": float,  # 0.0-1.0
        "reason_en": str,
        "reason_ko": str,
        "source": str,        # "entities"|"preferences"|"topics"|"style"|"llm"
      }
    """
    suggestions = []
    idx = 0

    def _sid():
        nonlocal idx
        idx += 1
        return f"s{idx}"

    # --- Current profile data ---
    ct = current_profile.get("context_tags", {})
    current_tech = set(t.lower() for t in ct.get("tech", []))
    current_interests = set(t.lower() for t in ct.get("interests", []))
    prefs = current_profile.get("preferences", {})
    current_tools = set(t.lower() for t in prefs.get("tools_primary", []))
    current_projects = set(p.get("name", "").lower() for p in current_profile.get("projects", []))
    identity = current_profile.get("identity", {})
    current_langs = set(l.lower() for l in identity.get("language", []))
    current_occupation = identity.get("occupation", "")
    cognition = current_profile.get("cognition", {})

    # --- 1. Tech stack suggestions from entities ---
    entities = analysis_result.get("entities", {})
    for tech_item in entities.get("tech", []):
        name = tech_item.get("name", "") if isinstance(tech_item, dict) else str(tech_item)
        count = tech_item.get("count", 1) if isinstance(tech_item, dict) else 1
        if not name:
            continue
        if name.lower() not in current_tech:
            conf = min(1.0, count / 5.0)  # 5 mentions = full confidence
            suggestions.append({
                "id": _sid(), "type": "add_tech",
                "field": "context_tags.tech", "value": name,
                "old_value": None, "confidence": round(conf, 2),
                "reason_en": f"Detected '{name}' mentioned {count} time(s) in your conversations",
                "reason_ko": f"대화에서 '{name}'이(가) {count}회 감지되었습니다",
                "source": "entities",
            })

    # --- 2. Tool suggestions from tech entities (IDE/editor/tool categories) ---
    tool_keywords = {"vs code", "vscode", "vim", "neovim", "emacs", "intellij",
                     "pycharm", "webstorm", "xcode", "android studio", "postman",
                     "figma", "slack", "notion", "jira", "linear", "github",
                     "gitlab", "bitbucket", "docker", "kubernetes", "terraform",
                     "aws", "gcp", "azure", "vercel", "netlify", "heroku"}
    for tech_item in entities.get("tech", []):
        name = tech_item.get("name", "") if isinstance(tech_item, dict) else str(tech_item)
        if name.lower() in tool_keywords and name.lower() not in current_tools:
            count = tech_item.get("count", 1) if isinstance(tech_item, dict) else 1
            suggestions.append({
                "id": _sid(), "type": "add_tool",
                "field": "preferences.tools_primary", "value": name,
                "old_value": None, "confidence": round(min(1.0, count / 3.0), 2),
                "reason_en": f"'{name}' appears to be a tool you use frequently",
                "reason_ko": f"'{name}'은(는) 자주 사용하는 도구로 보입니다",
                "source": "entities",
            })

    # --- 3. Interest/topic suggestions from TF-IDF ---
    topics = analysis_result.get("topics", {})
    if not topics.get("skipped"):
        for kw in topics.get("top_keywords", [])[:10]:
            word = kw.get("word", "")
            score = kw.get("score", 0)
            count = kw.get("count", 0)
            if word and word.lower() not in current_interests and word.lower() not in current_tech:
                # Skip very short/common words
                if len(word) <= 2:
                    continue
                suggestions.append({
                    "id": _sid(), "type": "add_interest",
                    "field": "context_tags.interests", "value": word,
                    "old_value": None,
                    "confidence": round(min(1.0, score * 2), 2),
                    "reason_en": f"Topic '{word}' appeared {count} times (TF-IDF score: {score:.3f})",
                    "reason_ko": f"주제 '{word}'이(가) {count}회 등장 (TF-IDF: {score:.3f})",
                    "source": "topics",
                })

    # --- 4. Language suggestions from communication style ---
    style = analysis_result.get("communication_style", {})
    lang_mix = style.get("language_mix", {})
    for lang_code, ratio in lang_mix.items():
        if ratio > 0.2:  # at least 20% of messages
            lang_name = {"ko": "Korean", "en": "English", "ja": "Japanese",
                         "zh": "Chinese"}.get(lang_code, lang_code)
            if lang_code.lower() not in current_langs and lang_name.lower() not in current_langs:
                suggestions.append({
                    "id": _sid(), "type": "update_language",
                    "field": "identity.language", "value": lang_name,
                    "old_value": None, "confidence": round(ratio, 2),
                    "reason_en": f"{lang_name} detected in {ratio*100:.0f}% of messages",
                    "reason_ko": f"메시지의 {ratio*100:.0f}%에서 {lang_name}이(가) 감지되었습니다",
                    "source": "style",
                })

    # --- 5. Communication preference from style ---
    formality = style.get("formality", "")
    verbosity = style.get("verbosity", "")
    current_comm_pref = cognition.get("communication_preference", "")
    if formality and verbosity:
        new_pref = f"{formality}, {verbosity}"
        if new_pref.lower() != current_comm_pref.lower() and current_comm_pref == "":
            suggestions.append({
                "id": _sid(), "type": "update_style",
                "field": "cognition.communication_preference",
                "value": new_pref, "old_value": current_comm_pref,
                "confidence": 0.7,
                "reason_en": f"Your communication style appears to be {formality} and {verbosity}",
                "reason_ko": f"커뮤니케이션 스타일: {formality}, {verbosity}",
                "source": "style",
            })

    # --- 6. LLM profile suggestions (highest confidence) ---
    llm = analysis_result.get("llm_profile")
    if isinstance(llm, dict):
        # Occupation
        llm_occ = llm.get("occupation", "")
        if llm_occ and not current_occupation:
            suggestions.append({
                "id": _sid(), "type": "update_occupation",
                "field": "identity.occupation", "value": llm_occ,
                "old_value": current_occupation, "confidence": 0.85,
                "reason_en": f"LLM inferred your occupation as '{llm_occ}'",
                "reason_ko": f"LLM이 직업을 '{llm_occ}'(으)로 추정했습니다",
                "source": "llm",
            })

        # Decision style
        llm_decision = llm.get("decision_style", "")
        if llm_decision and not cognition.get("decision_style"):
            suggestions.append({
                "id": _sid(), "type": "update_style",
                "field": "cognition.decision_style", "value": llm_decision,
                "old_value": "", "confidence": 0.75,
                "reason_en": f"LLM detected decision style: '{llm_decision}'",
                "reason_ko": f"LLM이 의사결정 스타일을 '{llm_decision}'(으)로 감지했습니다",
                "source": "llm",
            })

        # Thinking patterns
        llm_patterns = llm.get("thinking_patterns", [])
        current_patterns = cognition.get("thinking_patterns", [])
        current_patterns_lower = set(p.lower() for p in current_patterns)
        for pattern in llm_patterns:
            if pattern.lower() not in current_patterns_lower:
                suggestions.append({
                    "id": _sid(), "type": "update_style",
                    "field": "cognition.thinking_patterns", "value": pattern,
                    "old_value": None, "confidence": 0.7,
                    "reason_en": f"LLM identified thinking pattern: '{pattern}'",
                    "reason_ko": f"LLM이 사고 패턴 '{pattern}'을(를) 식별했습니다",
                    "source": "llm",
                })

        # Additional tech from LLM
        llm_tech = llm.get("tech_stack", [])
        for tech_name in llm_tech:
            if tech_name.lower() not in current_tech:
                # Check if already suggested by entities
                already = any(s["value"].lower() == tech_name.lower() and s["type"] == "add_tech"
                              for s in suggestions)
                if not already:
                    suggestions.append({
                        "id": _sid(), "type": "add_tech",
                        "field": "context_tags.tech", "value": tech_name,
                        "old_value": None, "confidence": 0.8,
                        "reason_en": f"LLM identified '{tech_name}' as part of your tech stack",
                        "reason_ko": f"LLM이 '{tech_name}'을(를) 기술 스택으로 식별했습니다",
                        "source": "llm",
                    })

    # --- 7. Preference-based removal suggestions ---
    preferences = analysis_result.get("preferences", [])
    for pref in preferences:
        target = pref.get("target", "")
        sentiment = pref.get("sentiment", "")
        if sentiment == "Dislike" and target.lower() in current_tech:
            suggestions.append({
                "id": _sid(), "type": "remove_tech",
                "field": "context_tags.tech", "value": target,
                "old_value": target, "confidence": 0.6,
                "reason_en": f"You expressed dislike for '{target}' — remove from tech stack?",
                "reason_ko": f"'{target}'에 대해 부정적 의견이 감지되었습니다 -- 기술 스택에서 제거할까요?",
                "source": "preferences",
            })

    # Sort by confidence descending
    suggestions.sort(key=lambda s: s["confidence"], reverse=True)
    return suggestions


def apply_suggestions(profile, accepted_suggestions):
    """
    Apply a list of accepted suggestions to a profile dict.
    Returns the updated profile (does NOT save to disk).
    """
    import copy
    profile = copy.deepcopy(profile)

    for sug in accepted_suggestions:
        stype = sug.get("type", "")
        field = sug.get("field", "")
        value = sug.get("value", "")

        if stype == "add_tech":
            tech = profile.setdefault("context_tags", {}).setdefault("tech", [])
            if value not in tech:
                tech.append(value)

        elif stype == "add_tool":
            tools = profile.setdefault("preferences", {}).setdefault("tools_primary", [])
            if value not in tools:
                tools.append(value)

        elif stype == "add_interest":
            interests = profile.setdefault("context_tags", {}).setdefault("interests", [])
            if value not in interests:
                interests.append(value)

        elif stype == "add_project":
            projects = profile.setdefault("projects", [])
            existing = [p.get("name", "").lower() for p in projects]
            if value.lower() not in existing:
                projects.append({
                    "name": value, "status": "active",
                    "stack": "", "description": "Detected from analysis"
                })

        elif stype == "update_language":
            langs = profile.setdefault("identity", {}).setdefault("language", [])
            if value not in langs:
                langs.append(value)

        elif stype == "update_occupation":
            profile.setdefault("identity", {})["occupation"] = value

        elif stype == "update_style":
            if field == "cognition.communication_preference":
                profile.setdefault("cognition", {})["communication_preference"] = value
            elif field == "cognition.decision_style":
                profile.setdefault("cognition", {})["decision_style"] = value
            elif field == "cognition.thinking_patterns":
                patterns = profile.setdefault("cognition", {}).setdefault("thinking_patterns", [])
                if value not in patterns:
                    patterns.append(value)

        elif stype == "remove_tech":
            tech = profile.get("context_tags", {}).get("tech", [])
            profile["context_tags"]["tech"] = [t for t in tech if t.lower() != value.lower()]

    return profile


# ═══════════════════════════════════════════════════════════════════
# Full Analysis Pipeline (v2 — Phase 4B-2)
# ═══════════════════════════════════════════════════════════════════
def run_full_analysis(messages_or_data=None, source=None, data=None,
                      use_llm=True, progress_callback=None):
    """
    Master analysis pipeline. Chains all stages together.

    Can be called two ways:
      1. Legacy: run_full_analysis(messages)  — list of message dicts
      2. New:    run_full_analysis(source="text", data="...", use_llm=True)

    Returns: full analysis result dict with all fields.
    """
    def _progress(pct, msg):
        set_progress("running", pct, msg)
        if progress_callback:
            try:
                progress_callback(pct, msg)
            except Exception:
                pass

    # Handle legacy call signature
    if messages_or_data is not None and source is None:
        messages = messages_or_data
    elif source is not None and data is not None:
        # Parse based on source type
        _progress(10, "Parsing input data...")
        try:
            if source == "chatgpt":
                messages = parse_chatgpt_export(data)
            elif source == "claude":
                messages = parse_claude_export(data)
            elif source == "text":
                messages = parse_text_paste(data)
            else:
                messages = []
        except Exception as e:
            print(f"[SelfCore] Parse error: {e}")
            messages = []
    else:
        messages = []

    empty_result = {
        "source": source or "unknown",
        "total_messages": 0,
        "entities": {"tech": [], "people": [], "orgs": [], "all_entities": []},
        "preferences": [],
        "topics": {"skipped": True, "reason": "no_data", "count": 0},
        "communication_style": {
            "avg_message_length": 0, "question_ratio": 0, "code_ratio": 0,
            "formality": "mixed", "language_mix": {"ko": 0, "en": 0},
            "verbosity": "concise", "summary": ""
        },
        "llm_profile": None,
        "analyzed_at": datetime.now().isoformat(),
        "stats": {"total_messages": 0},
    }

    if not messages:
        set_progress("completed", 100, "No messages to analyze")
        return empty_result

    texts = [m["text"] for m in messages if m.get("text")]
    if not texts:
        set_progress("completed", 100, "No text content")
        return empty_result

    result = {
        "source": source or "unknown",
        "total_messages": len(messages),
        "entities": None,
        "preferences": None,
        "topics": None,
        "communication_style": None,
        "llm_profile": None,
        "analyzed_at": datetime.now().isoformat(),
        "stats": {"total_messages": len(messages)},
    }

    # Step 2: Entity extraction
    _progress(30, f"Extracting entities from {len(texts)} messages...")
    try:
        result["entities"] = extract_entities(texts)
    except Exception as e:
        print(f"[SelfCore] Entity extraction error: {e}")
        result["entities"] = {"tech": [], "people": [], "orgs": [], "all_entities": []}

    # Step 2b: Preference extraction
    _progress(40, "Extracting preferences...")
    try:
        result["preferences"] = extract_preferences(texts, result["entities"])
    except Exception as e:
        print(f"[SelfCore] Preference extraction error: {e}")
        result["preferences"] = []

    # Step 3: Language detection
    _progress(45, "Detecting language...")
    try:
        sample = " ".join(texts[:20])
        lang = detect_language(sample)
    except Exception:
        lang = "ko"

    # Step 4: Communication style
    _progress(50, "Analyzing communication style...")
    try:
        result["communication_style"] = analyze_communication_style(texts)
    except Exception as e:
        print(f"[SelfCore] Style analysis error: {e}")
        result["communication_style"] = {
            "avg_message_length": 0, "question_ratio": 0, "code_ratio": 0,
            "formality": "mixed", "language_mix": {"ko": 0, "en": 0},
            "verbosity": "concise", "summary": ""
        }

    # Step 5: TF-IDF topics
    _progress(60, "Extracting topics via TF-IDF...")
    try:
        result["topics"] = extract_topics(texts, language=lang)
    except Exception as e:
        print(f"[SelfCore] Topic extraction error: {e}")
        result["topics"] = {"skipped": True, "reason": "error", "count": len(texts)}

    # Step 6: LLM profile extraction (optional)
    if use_llm:
        _progress(70, "Running LLM profile extraction...")
        try:
            llm_result = run_profile_extraction(
                result["entities"], result["topics"],
                result["preferences"], result["communication_style"]
            )
            if isinstance(llm_result, dict) and "error" not in llm_result:
                result["llm_profile"] = llm_result
                _progress(90, "LLM extraction complete")
            elif isinstance(llm_result, dict) and "error" in llm_result:
                result["llm_profile"] = None
                _progress(90, f"LLM skipped: {llm_result.get('message', '')}")
            else:
                result["llm_profile"] = None
                _progress(90, "LLM unavailable, using statistical results")
        except Exception as e:
            print(f"[SelfCore] LLM extraction error (non-fatal): {e}")
            result["llm_profile"] = None
    else:
        result["llm_profile"] = None

    _progress(100, "Analysis complete")
    set_progress("completed", 100, "Analysis complete")
    return result
