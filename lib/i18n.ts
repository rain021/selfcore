export type Lang = "en" | "ko";

const translations = {
  // ─── App ─────────────────────────────────────
  "app.title": { en: "SelfCore", ko: "SelfCore" },
  "app.subtitle": { en: "Personal AI Identity Engine", ko: "개인 AI 정체성 엔진" },
  "app.version": { en: "v1.0", ko: "v1.0" },
  "app.connecting": { en: "Connecting to SelfCore...", ko: "SelfCore에 연결 중..." },
  "app.error.backend": { en: "Cannot connect to SelfCore backend. Is selfcore.py running?", ko: "SelfCore 백엔드에 연결할 수 없습니다. selfcore.py가 실행 중인가요?" },

  // ─── Top bar ─────────────────────────────────
  "topbar.language": { en: "Language", ko: "언어" },
  "topbar.profile": { en: "Profile", ko: "프로필" },
  "topbar.newProfile": { en: "New Profile", ko: "새 프로필" },
  "topbar.deleteProfile": { en: "Delete Profile", ko: "프로필 삭제" },
  "topbar.deleteConfirm": { en: "Delete this profile?", ko: "이 프로필을 삭제하시겠습니까?" },
  "topbar.minimize": { en: "Minimize", ko: "최소화" },

  // ─── Onboarding ──────────────────────────────
  "onboard.welcome": { en: "Welcome to SelfCore", ko: "SelfCore에 오신 것을 환영합니다" },
  "onboard.desc": { en: "Own your AI identity. One file. Every AI.", ko: "당신의 AI 정체성을 소유하세요. 하나의 파일. 모든 AI." },
  "onboard.setup": { en: "Set Up Profile", ko: "프로필 설정하기" },
  "onboard.quick": { en: "Quick Start", ko: "빠른 시작" },
  "onboard.langSelect": { en: "Select Language", ko: "언어 선택" },

  // ─── Identity ────────────────────────────────
  "identity.title": { en: "Identity", ko: "정체성" },
  "identity.name": { en: "Name", ko: "이름" },
  "identity.occupation": { en: "Occupation", ko: "직업" },
  "identity.languages": { en: "Languages (comma-separated)", ko: "언어 (쉼표로 구분)" },
  "identity.timezone": { en: "Timezone", ko: "시간대" },
  "identity.selectTimezone": { en: "Select timezone", ko: "시간대 선택" },

  // ─── Cognition ───────────────────────────────
  "cognition.title": { en: "Cognition", ko: "사고방식" },
  "cognition.decisionStyle": { en: "Decision Style", ko: "의사결정 스타일" },
  "cognition.commPref": { en: "Communication Preference", ko: "커뮤니케이션 선호" },
  "cognition.thinkingPatterns": { en: "Thinking Patterns (comma-separated)", ko: "사고 패턴 (쉼표로 구분)" },
  "cognition.riskTolerance": { en: "Risk Tolerance", ko: "위험 감수성" },
  "cognition.select": { en: "Select", ko: "선택" },
  "cognition.low": { en: "Low", ko: "낮음" },
  "cognition.medium": { en: "Medium", ko: "보통" },
  "cognition.high": { en: "High", ko: "높음" },

  // ─── Projects ────────────────────────────────
  "projects.title": { en: "Projects", ko: "프로젝트" },
  "projects.add": { en: "+ Add Project", ko: "+ 프로젝트 추가" },
  "projects.empty": { en: 'No projects yet. Click "Add Project" to start.', ko: '"프로젝트 추가"를 클릭하여 시작하세요.' },
  "projects.remove": { en: "Remove", ko: "삭제" },
  "projects.name": { en: "Name", ko: "프로젝트 이름" },
  "projects.status": { en: "Status", ko: "상태" },
  "projects.stack": { en: "Tech Stack", ko: "기술스택" },
  "projects.description": { en: "Description", ko: "설명" },
  "projects.planning": { en: "Planning", ko: "계획 중" },
  "projects.active": { en: "Active", ko: "진행 중" },
  "projects.paused": { en: "Paused", ko: "일시중지" },
  "projects.completed": { en: "Completed", ko: "완료" },
  "projects.number": { en: "Project", ko: "프로젝트" },

  // ─── Preferences ─────────────────────────────
  "preferences.title": { en: "Preferences", ko: "선호설정" },
  "preferences.aiInteraction": { en: "AI Interaction Style", ko: "AI 상호작용 스타일" },
  "preferences.outputFormat": { en: "Output Format", ko: "출력 형식" },
  "preferences.designTaste": { en: "Design Taste", ko: "디자인 취향" },
  "preferences.primaryTools": { en: "Primary Tools (comma-separated)", ko: "주요 도구 (쉼표로 구분)" },

  // ─── Context Tags ────────────────────────────
  "context.title": { en: "Context Tags", ko: "맥락 태그" },
  "context.tech": { en: "Tech (comma-separated)", ko: "기술 태그 (쉼표로 구분)" },
  "context.interests": { en: "Interests (comma-separated)", ko: "관심사 (쉼표로 구분)" },
  "context.currentFocus": { en: "Current Focus", ko: "현재 집중" },

  // ─── Actions ─────────────────────────────────
  "action.save": { en: "Save Profile", ko: "프로필 저장" },
  "action.export": { en: "Export .self", ko: ".self 내보내기" },
  "action.import": { en: "Import .self", ko: ".self 가져오기" },
  "action.reset": { en: "Reset All", ko: "전체 초기화" },
  "action.saved": { en: "Profile saved successfully", ko: "프로필이 저장되었습니다" },
  "action.saveFail": { en: "Failed to save profile", ko: "프로필 저장에 실패했습니다" },
  "action.exported": { en: "Exported encrypted .self file", ko: "암호화된 .self 파일을 내보냈습니다" },
  "action.imported": { en: "Profile imported successfully", ko: "프로필을 성공적으로 가져왔습니다" },
  "action.importFail": { en: "Import failed — invalid file or wrong password", ko: "가져오기 실패 — 잘못된 파일이거나 비밀번호 오류" },
  "action.resetDone": { en: "Profile reset to defaults", ko: "프로필이 초기값으로 재설정되었습니다" },

  // ─── Cold Start / Import ─────────────────────
  "coldstart.title": { en: "Quick Setup from AI History", ko: "AI 히스토리에서 빠른 설정" },
  "coldstart.chatgpt": { en: "Import ChatGPT Export", ko: "ChatGPT 내보내기 가져오기" },
  "coldstart.text": { en: "Import from Text", ko: "텍스트에서 가져오기" },
  "coldstart.paste": { en: "Paste your AI conversation here...", ko: "AI 대화를 여기에 붙여넣으세요..." },
  "coldstart.analyze": { en: "Analyze Text", ko: "텍스트 분석" },
  "coldstart.cancel": { en: "Cancel", ko: "취소" },
  "coldstart.review": { en: "We found these details. Edit before saving.", ko: "이 정보를 찾았습니다. 저장 전에 수정하세요." },
  "coldstart.apply": { en: "Apply to Profile", ko: "프로필에 적용" },
  "coldstart.analyzing": { en: "Analyzing...", ko: "분석 중..." },
  "coldstart.noData": { en: "No data could be extracted.", ko: "추출할 수 있는 데이터가 없습니다." },

  // ─── Activity ────────────────────────────────
  "activity.title": { en: "Activity Insights", ko: "활동 인사이트" },
  "activity.today": { en: "Today", ko: "오늘" },
  "activity.mostActive": { en: "Most active", ko: "가장 활발한 시간" },
  "activity.noData": { en: "No activity data yet. Enable tracking to start.", ko: "아직 활동 데이터가 없습니다. 추적을 활성화하세요." },
  "activity.tracking": { en: "Window Title Tracking", ko: "창 제목 추적" },
  "activity.on": { en: "ON", ko: "켜짐" },
  "activity.off": { en: "OFF", ko: "꺼짐" },
  "activity.privacy": { en: "Only window titles are recorded locally. No content is read.", ko: "창 제목만 로컬에 기록됩니다. 내용은 읽지 않습니다." },

  // ─── Tray / Electron ─────────────────────────
  "tray.editProfile": { en: "Edit Profile", ko: "프로필 편집" },
  "tray.quit": { en: "Quit", ko: "종료" },
  "tray.active": { en: "Active", ko: "활성" },
  "quit.title": { en: "SelfCore", ko: "SelfCore" },
  "quit.message": { en: "Are you sure you want to quit SelfCore?", ko: "SelfCore를 종료하시겠습니까?" },
  "quit.yes": { en: "Quit", ko: "종료" },
  "quit.no": { en: "Cancel", ko: "취소" },

  // ─── Notifications ───────────────────────────
  "notify.ready": { en: "SelfCore context ready. Paste into your AI.", ko: "SelfCore 맥락이 준비되었습니다. AI에 붙여넣으세요." },

  // ─── Insights / Activity Analyzer ─────────────
  "insights.title": { en: "Insights", ko: "인사이트" },
  "insights.analyze": { en: "Analyze Now", ko: "지금 분석" },
  "insights.todayActivity": { en: "Today's Activity", ko: "오늘의 활동" },
  "insights.peakHours": { en: "Peak hours", ko: "집중 시간대" },
  "insights.detectedProjects": { en: "Detected projects", ko: "감지된 프로젝트" },
  "insights.detectedTech": { en: "Detected tech", ko: "감지된 기술" },
  "insights.totalTime": { en: "Total tracked time", ko: "총 추적 시간" },
  "insights.minutes": { en: "minutes", ko: "분" },

  // ─── Profile Suggestions ──────────────────────
  "suggest.title": { en: "Profile Suggestions", ko: "프로필 제안" },
  "suggest.noSuggestions": { en: "No suggestions right now. Keep using your PC!", ko: "현재 제안 사항이 없습니다. PC를 계속 사용해 주세요!" },
  "suggest.accept": { en: "Accept", ko: "수락" },
  "suggest.dismiss": { en: "Dismiss", ko: "무시" },
  "suggest.detected": { en: "Detected", ko: "감지됨" },

  // ─── Weekly Summary ───────────────────────────
  "weekly.title": { en: "Weekly Summary", ko: "주간 요약" },
  "weekly.totalHours": { en: "Total PC time", ko: "총 PC 사용 시간" },
  "weekly.hours": { en: "hours", ko: "시간" },
  "weekly.bestDay": { en: "Most productive day", ko: "가장 생산적인 요일" },
  "weekly.topApps": { en: "Top apps", ko: "상위 앱" },
  "weekly.noData": { en: "Need 7+ days of tracking data", ko: "7일 이상의 추적 데이터가 필요합니다" },

  // ─── Injection History ────────────────────────
  "injection.title": { en: "Injection History", ko: "주입 기록" },
  "injection.noData": { en: "No injections yet. Use Ctrl+Shift+Space or the Chrome Extension.", ko: "아직 주입 기록이 없습니다. Ctrl+Shift+Space 또는 Chrome 확장을 사용하세요." },
  "injection.platform": { en: "Platform", ko: "플랫폼" },
  "injection.profile": { en: "Profile", ko: "프로필" },
  "injection.rule": { en: "Route", ko: "라우트" },

  // ─── Chrome Extension ─────────────────────────
  "ext.title": { en: "Chrome Extension", ko: "Chrome 확장 프로그램" },
  "ext.installed": { en: "Extension ready — install from extension/ folder", ko: "확장 프로그램 준비 완료 — extension/ 폴더에서 설치" },

  // ─── Phase 4 — Polish ─────────────────────
  "topbar.close": { en: "Close", ko: "닫기" },
  "action.purgeActivity": { en: "Delete All Activity Data", ko: "모든 활동 데이터 삭제" },
  "action.purgeConfirm": { en: "Delete all activity tracking data? This cannot be undone.", ko: "모든 활동 추적 데이터를 삭제하시겠습니까? 이 작업은 되돌릴 수 없습니다." },
  "action.purgeDone": { en: "Activity data deleted", ko: "활동 데이터가 삭제되었습니다" },
  "insights.enableTracking": { en: "Enable activity tracking to get insights", ko: "활동 추적을 켜서 인사이트를 받아보세요" },
  "backend.connecting": { en: "Connecting to backend...", ko: "백엔드에 연결 중..." },
  "backend.error": { en: "Cannot connect to SelfCore backend", ko: "SelfCore 백엔드에 연결할 수 없습니다" },

  // ─── Phase 4A — Analysis Engine ─────────
  "analysis.title": { en: "Analysis", ko: "분석" },
  "analysis.import.chatgpt": { en: "ChatGPT Import", ko: "ChatGPT 가져오기" },
  "analysis.import.claude": { en: "Claude Import", ko: "Claude 가져오기" },
  "analysis.import.text": { en: "Paste Text", ko: "텍스트 붙여넣기" },
  "analysis.import.section": { en: "Import Data", ko: "데이터 가져오기" },
  "analysis.import.dragdrop": { en: "or drag & drop .zip file here", ko: ".zip 파일을 여기에 드래그 앤 드롭하세요" },
  "analysis.progress": { en: "Analyzing...", ko: "분석 중..." },
  "analysis.results.title": { en: "Analysis Results", ko: "분석 결과" },
  "analysis.results.techStack": { en: "Discovered Tech Stack", ko: "발견된 기술 스택" },
  "analysis.results.preferences": { en: "Detected Preferences", ko: "감지된 선호도" },
  "analysis.results.topics": { en: "Key Topics", ko: "주요 주제" },
  "analysis.results.topicsPlaceholder": { en: "Not enough messages for topic analysis (need 20+)", ko: "주제 분석에 충분한 메시지가 없습니다 (20개 이상 필요)" },
  "analysis.results.topicsScore": { en: "score", ko: "점수" },
  "analysis.results.edit": { en: "Edit", ko: "수정" },
  "analysis.results.delete": { en: "Delete", ko: "삭제" },
  "analysis.results.like": { en: "Like", ko: "좋아함" },
  "analysis.results.dislike": { en: "Dislike", ko: "별로" },
  "analysis.results.confidence": { en: "Confidence", ko: "신뢰도" },
  "analysis.results.high": { en: "High", ko: "높음" },
  "analysis.results.medium": { en: "Medium", ko: "보통" },
  "analysis.results.low": { en: "Low", ko: "낮음" },
  "analysis.results.count": { en: "mentions", ko: "회 언급" },
  "analysis.results.messages": { en: "messages analyzed", ko: "개 메시지 분석됨" },
  "analysis.conflict.title": { en: "Resolve Conflicts", ko: "충돌 해결" },
  "analysis.conflict.question": { en: "Which one?", ko: "어느 쪽?" },
  "analysis.apply": { en: "Apply to Profile", ko: "프로필에 적용" },
  "analysis.rerun": { en: "Analyze Again", ko: "다시 분석" },
  "analysis.preview": { en: "Preview changes before applying", ko: "적용 전 변경사항 미리보기" },
  "analysis.noResults": { en: "No analysis results yet. Import data to get started.", ko: "아직 분석 결과가 없습니다. 데이터를 가져와서 시작하세요." },
  "analysis.guide.chatgpt.title": { en: "How to export ChatGPT data", ko: "ChatGPT 데이터 내보내기 방법" },
  "analysis.guide.chatgpt.step1": { en: "Step 1: Log in to ChatGPT website", ko: "Step 1: ChatGPT 웹사이트 로그인" },
  "analysis.guide.chatgpt.step2": { en: "Step 2: Go to Settings → Data Controls", ko: "Step 2: 설정(Settings) → 데이터 관리(Data Controls)" },
  "analysis.guide.chatgpt.step3": { en: "Step 3: Click Export Data", ko: "Step 3: 데이터 내보내기(Export Data) 클릭" },
  "analysis.guide.chatgpt.step4": { en: "Step 4: Download .zip from email", ko: "Step 4: 이메일로 받은 .zip 다운로드" },
  "analysis.guide.chatgpt.step5": { en: "Step 5: Upload with the ChatGPT Import button above", ko: "Step 5: 위의 'ChatGPT 가져오기' 버튼에 파일 업로드" },
  "analysis.guide.claude.title": { en: "How to export Claude data", ko: "Claude 데이터 내보내기 방법" },
  "analysis.guide.claude.step1": { en: "Step 1: Log in to Claude website", ko: "Step 1: Claude 웹사이트 로그인" },
  "analysis.guide.claude.step2": { en: "Step 2: Go to Settings → Privacy", ko: "Step 2: 설정(Settings) → 개인정보(Privacy)" },
  "analysis.guide.claude.step3": { en: "Step 3: Click Export Data", ko: "Step 3: 데이터 내보내기(Export Data) 클릭" },
  "analysis.guide.claude.step4": { en: "Step 4: Download from email", ko: "Step 4: 이메일로 받은 파일 다운로드" },
  "analysis.guide.claude.step5": { en: "Step 5: Upload with the Claude Import button above", ko: "Step 5: 위의 'Claude 가져오기' 버튼에 파일 업로드" },

  // ─── Analysis Phase 4B-3 ──────────────────
  "analysis.results.style": { en: "Communication Style", ko: "커뮤니케이션 스타일" },
  "analysis.results.style.formality": { en: "Formality", ko: "격식" },
  "analysis.results.style.verbosity": { en: "Verbosity", ko: "상세도" },
  "analysis.results.style.codeRatio": { en: "Code Ratio", ko: "코드 비율" },
  "analysis.results.style.questionRatio": { en: "Question Ratio", ko: "질문 비율" },
  "analysis.results.style.avgLength": { en: "Avg Length", ko: "평균 길이" },
  "analysis.results.style.langMix": { en: "Language Mix", ko: "언어 비율" },
  "analysis.results.llmProfile": { en: "LLM Profile Extraction", ko: "LLM 프로필 추출" },
  "analysis.results.llmUnavailable": { en: "Ollama not available — using statistical analysis only", ko: "Ollama 미설치 -- 통계 분석만 사용" },
  "analysis.ollama.title": { en: "Ollama Status", ko: "Ollama 상태" },
  "analysis.ollama.installed": { en: "Installed", ko: "설치됨" },
  "analysis.ollama.notInstalled": { en: "Not installed", ko: "미설치" },
  "analysis.ollama.running": { en: "Running", ko: "실행 중" },
  "analysis.ollama.stopped": { en: "Stopped", ko: "중지됨" },
  "analysis.ollama.model": { en: "Model", ko: "모델" },
  "analysis.ollama.gpu": { en: "GPU", ko: "GPU" },
  "analysis.ollama.start": { en: "Start Ollama", ko: "Ollama 시작" },
  "analysis.ollama.pull": { en: "Pull Model", ko: "모델 다운로드" },
  "analysis.suggestions.title": { en: "Profile Suggestions", ko: "프로필 제안" },
  "analysis.suggestions.empty": { en: "No suggestions available. Run analysis first.", ko: "제안이 없습니다. 먼저 분석을 실행하세요." },
  "analysis.suggestions.accept": { en: "Accept", ko: "수락" },
  "analysis.suggestions.reject": { en: "Reject", ko: "거절" },
  "analysis.suggestions.acceptAll": { en: "Accept All", ko: "모두 수락" },
  "analysis.suggestions.applySelected": { en: "Apply Selected", ko: "선택 항목 적용" },
  "analysis.suggestions.confidence": { en: "Confidence", ko: "신뢰도" },
  "analysis.suggestions.generate": { en: "Generate Suggestions", ko: "제안 생성" },
  "analysis.suggestions.source": { en: "Source", ko: "출처" },

  // ─── Phase 5A — Hardcoded string cleanup ──
  "toast.saved": { en: "Saved", ko: "저장됨" },
  "toast.applied": { en: "applied", ko: "적용됨" },
  "toast.analysisStart": { en: "Starting analysis...", ko: "분석 시작..." },
  "toast.analysisComplete": { en: "Analysis complete!", ko: "분석 완료!" },
  "toast.zipOnly": { en: "Only .zip files supported", ko: ".zip 파일만 가능합니다" },
  "toast.merged": { en: "Results merged", ko: "결과 병합 완료" },
  "toast.appliedToProfile": { en: "Applied to profile", ko: "프로필에 적용됨" },
  "toast.suggestionsApplied": { en: "suggestions applied", ko: "개 제안 적용됨" },
  "analysis.results.noTech": { en: "No tech detected", ko: "감지된 기술이 없습니다" },
  "analysis.results.noPrefs": { en: "No preferences detected", ko: "감지된 선호도가 없습니다" },
  "analysis.results.mergeBtn": { en: "Merge Results", ko: "결과 병합" },
  "analysis.ollama.clickRefresh": { en: "Click Refresh to check status", ko: "상태를 확인하려면 Refresh를 클릭하세요" },
  "tab.editor": { en: "Profile Editor", ko: "프로필 편집기" },
} as const;

export type TranslationKey = keyof typeof translations;

export function t(key: TranslationKey, lang: Lang): string {
  const entry = translations[key];
  if (!entry) return key;
  return entry[lang] || entry["en"] || key;
}

export default translations;
