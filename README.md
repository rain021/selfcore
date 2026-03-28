# SelfCore -- Personal AI Identity Engine

Own your AI identity. One file. Every AI.

## What is SelfCore?

SelfCore creates a portable `.self` file containing your identity, skills, preferences, and context. This file can be injected into any AI (Claude, ChatGPT, Gemini, Mistral) so every AI already knows you. All data stays on your PC. Nothing is sent to any server.

## Features

- Profile editor with identity, projects, preferences, tech stack
- AI chat history analysis (ChatGPT and Claude export parsing)
- Smart entity extraction with spaCy NLP
- TF-IDF topic clustering
- Communication style analysis (formality, verbosity, code ratio)
- Optional deep analysis with local LLM (Ollama)
- Profile suggestion generator with confidence scoring
- Chrome Extension for automatic context injection
- Clipboard injection (Ctrl+Shift+Space) as universal fallback
- Dynamic Context Router v3 with Korean + English query classification
- Multi-profile support (Work, Personal, Creative)
- Korean and English UI (200+ translation keys)
- AES-256 encrypted .self file export/import
- Activity tracking and insights dashboard
- Weekly summary with detected projects and tech
- 100% local -- zero data leaves your PC

## Installation

### Prerequisites
- Node.js 18+
- Python 3.10+
- Windows 10/11

### Setup
```bash
cd SelfCore
npm install
setup_python.bat
```

Or install Python dependencies manually:
```bash
pip install -r requirements.txt
python -m spacy download en_core_web_sm
python -m spacy download ko_core_news_sm
```

### Run
Double-click `SelfCore.vbs` on the Desktop, or:
```bash
npm run app:dev
```

This starts three processes:
1. Python backend (`selfcore.py`) on port 8100
2. Next.js dev server on port 3000
3. Electron desktop app

## Chrome Extension Setup

1. Open Chrome -> chrome://extensions
2. Enable "Developer mode" (top right)
3. Click "Load unpacked"
4. Select the SelfCore/extension folder
5. Pin the SelfCore extension in your toolbar

## How to Use

1. Launch SelfCore and fill in your profile
2. Open any AI website (Claude, ChatGPT, Gemini, Mistral)
3. Press Ctrl+Shift+Space before typing your message
4. Paste (Ctrl+V) -- your AI now knows you
5. Or use the Chrome Extension for automatic injection

### Analysis Tab
1. Import ChatGPT or Claude data export (.zip)
2. Or paste conversation text directly
3. Review detected tech stack, preferences, and topics
4. Generate profile suggestions and apply selected ones
5. Optionally enable Ollama for LLM-powered deep analysis

## Tech Stack

Electron 41, Python 3.13, React 19 / Next.js 16, SQLite, spaCy 3.8, scikit-learn, Tailwind CSS 4

## Privacy

All data is stored locally on your PC. SelfCore never connects to external servers. The Python backend binds to 127.0.0.1 only. Your .self files are encrypted with AES-256-GCM. Window title tracking only records app names locally.

## License

GPL-3.0 -- See [LICENSE](LICENSE) for details.
