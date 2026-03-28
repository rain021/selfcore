# Changelog

## v1.0.0 (2026-03-28)

### Features
- .self profile creation, editing, encryption (AES-256-GCM), export/import
- Korean and English UI with instant language switching (203 translation keys)
- Multi-profile support (Work, Personal, Creative)
- Context injection via Ctrl+Shift+Space (clipboard method)
- Chrome Extension for automatic context injection (Claude, ChatGPT, Gemini, Mistral)
- ChatGPT data export parsing (DAG backward traversal)
- Claude data export parsing
- Free text paste analysis
- spaCy NLP entity extraction with 244-term tech dictionary
- Preference detection (Like/Dislike) with lexicon + dependency parsing
- TF-IDF topic clustering with Korean stopword support
- Communication style analysis (formality, verbosity, code ratio)
- Ollama 3B LLM integration for deep profile extraction
- Dynamic Context Router v3 with category-based routing and 200-token budget
- Profile update suggestions with confidence scoring and user confirmation
- Prompt injection sanitization
- Activity tracking with window title observer
- Injection transparency logging
- Weekly summary with detected projects and tech
- Orphan Ollama process cleanup on startup

### Privacy
- 100% local processing — zero data leaves your PC
- Python backend binds to 127.0.0.1 only
- No telemetry, no analytics, no external network calls
- AES-256-GCM encrypted .self file exports
