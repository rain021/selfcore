# SelfCore — 한국 커뮤니티 소개글

## GeekNews / 커뮤니티 게시용

### 제목
SelfCore — AI를 갈아탈 때마다 자기소개를 반복하지 마세요

### 본문

안녕하세요. 개인 프로젝트로 SelfCore를 만들었습니다.

**문제:** ChatGPT에서 Claude로, Claude에서 Gemini로 갈아탈 때마다 "나는 개발자이고, 이런 프로젝트를 하고 있고, 한국어로 답해줘"를 처음부터 다시 설명해야 합니다. AI가 나를 기억하지 못합니다.

**해결:** SelfCore는 .self 파일 하나에 나의 정체성, 기술 스택, 선호도, 프로젝트를 저장합니다. Ctrl+Shift+Space를 누르면 어떤 AI든 즉시 나를 아는 상태에서 대화를 시작합니다.

**특징:**
- ChatGPT, Claude, Gemini, Grok 대화 기록을 가져와서 자동으로 프로필 생성
- spaCy NLP로 기술 용어, 선호도 자동 추출
- Chrome Extension으로 AI 웹사이트에 자동 주입
- 100% 로컬 처리 — 서버 전송 없음, 데이터는 내 PC에만
- 한국어/영어 UI 완벽 지원
- 오픈소스 (GPL-3.0)

**기술 스택:** Electron + Python + React + spaCy + scikit-learn + Ollama (선택)

**작동 방식:**
1. ChatGPT/Claude/Gemini/Grok 대화 기록을 내보내기
2. SelfCore에 드래그 앤 드롭
3. spaCy + TF-IDF가 자동으로 기술 스택, 선호도, 주제 추출
4. .self 프로필 파일 생성 (AES-256 암호화)
5. Ctrl+Shift+Space로 어떤 AI에든 즉시 주입

**프라이버시:**
- 모든 처리는 로컬에서 진행 (서버 전송 없음)
- 텔레메트리 없음, 분석 없음
- AES-256-GCM 암호화
- 오픈소스이므로 코드 직접 검증 가능

GitHub: https://github.com/rain021/selfcore

피드백 환영합니다!
