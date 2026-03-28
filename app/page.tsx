"use client";

import { useEffect, useState, useRef, useCallback } from "react";
import { t, Lang } from "../lib/i18n";

declare global {
  interface Window {
    electronAPI?: { platform: string; minimize: () => void; close: () => void };
  }
}

const API = "http://127.0.0.1:8100";

const CARD: React.CSSProperties = {
  background: "rgba(15,23,42,0.7)",
  backdropFilter: "saturate(180%) blur(20px)",
  WebkitBackdropFilter: "saturate(180%) blur(20px)",
  borderRadius: "16px",
  border: "1px solid rgba(255,255,255,0.1)",
  padding: "20px",
};
const LABEL: React.CSSProperties = { fontSize: "12px", color: "rgba(255,255,255,0.5)", marginBottom: "4px", display: "block", textTransform: "uppercase", letterSpacing: "0.05em" };
const ACCENT = "#58E6FF";

interface Project { name: string; status: string; stack: string; description: string }
interface SelfProfile {
  version: string;
  identity: { name: string; language: string[]; timezone: string; occupation: string };
  cognition: { decision_style: string; communication_preference: string; thinking_patterns: string[]; risk_tolerance: string };
  projects: Project[];
  preferences: { ai_interaction: string; output_format: string; design_taste: string; tools_primary: string[] };
  context_tags: { tech: string[]; interests: string[]; current_focus: string };
}
interface Suggestion { type: string; field: string; value: string; reason_en: string; reason_ko: string }
interface InjectionEntry { timestamp: string; platform: string; context: string; profile: string; rule: string }
interface AnalysisApp { name: string; time: string; seconds: number }

const EMPTY_PROJECT: Project = { name: "", status: "planning", stack: "", description: "" };
const TIMEZONES = ["UTC","Asia/Seoul","Asia/Tokyo","Asia/Shanghai","Asia/Singapore","America/New_York","America/Chicago","America/Denver","America/Los_Angeles","Europe/London","Europe/Paris","Europe/Berlin","Australia/Sydney"];

export default function ProfileEditor() {
  const [lang, setLang] = useState<Lang>("en");
  const [profile, setProfile] = useState<SelfProfile | null>(null);
  const [profiles, setProfiles] = useState<string[]>([]);
  const [activeProfile, setActiveProfile] = useState("default");
  const [status, setStatus] = useState("");
  const [saveCheck, setSaveCheck] = useState(false);
  const [loading, setLoading] = useState(true);
  const [showOnboard, setShowOnboard] = useState(false);
  const [fadeIn, setFadeIn] = useState(false);
  // Cold Start
  const [showTextImport, setShowTextImport] = useState(false);
  const [importText, setImportText] = useState("");
  const [extracted, setExtracted] = useState<any>(null);
  const [analyzing, setAnalyzing] = useState(false);
  // Activity
  const [trackingOn, setTrackingOn] = useState(false);
  const [activityApps, setActivityApps] = useState<AnalysisApp[]>([]);
  const [activeHours, setActiveHours] = useState<{ hour: string; count: number }[]>([]);
  // Insights
  const [analysisData, setAnalysisData] = useState<any>(null);
  const [suggestions, setSuggestions] = useState<Suggestion[]>([]);
  const [injections, setInjections] = useState<InjectionEntry[]>([]);
  const [weeklySummary, setWeeklySummary] = useState<any>(null);
  // Tabs
  const [tab, setTab] = useState<"editor" | "insights" | "analysis">("editor");
  // Toast
  const [toast, setToast] = useState("");
  // Analysis (Phase 4A)
  const [analysisResult, setAnalysisResult] = useState<any>(null);
  const [analysisResults, setAnalysisResults] = useState<any[]>([]);
  const [analysisLoading, setAnalysisLoading] = useState(false);
  const [analysisProgress, setAnalysisProgress] = useState(0);
  const [analysisMsg, setAnalysisMsg] = useState("");
  const [showTextModal, setShowTextModal] = useState(false);
  const [analysisText, setAnalysisText] = useState("");
  const [showGuide, setShowGuide] = useState<string | null>(null);
  const [showApplyPreview, setShowApplyPreview] = useState(false);
  const [conflictResolutions, setConflictResolutions] = useState<Record<string, string>>({});
  // Phase 4B-3
  const [ollamaStatus, setOllamaStatus] = useState<any>(null);
  const [analysisSuggestions, setAnalysisSuggestions] = useState<any[]>([]);
  const [selectedSuggestions, setSelectedSuggestions] = useState<Set<string>>(new Set());
  const chatgptAnalysisRef = useRef<HTMLInputElement>(null);
  const claudeAnalysisRef = useRef<HTMLInputElement>(null);
  const dropRef = useRef<HTMLDivElement>(null);

  const fileRef = useRef<HTMLInputElement>(null);
  const chatgptRef = useRef<HTMLInputElement>(null);

  const T = useCallback((key: Parameters<typeof t>[0]) => t(key, lang), [lang]);

  const showToast = (msg: string) => { setToast(msg); setTimeout(() => setToast(""), 2500); };

  useEffect(() => {
    (async () => {
      try {
        const [settings, profilesData] = await Promise.all([
          fetch(`${API}/api/settings`).then(r => r.json()),
          fetch(`${API}/api/profiles`).then(r => r.json()),
        ]);
        const uiLang = (settings.ui_lang === "ko" ? "ko" : "en") as Lang;
        setLang(uiLang);
        setTrackingOn(settings.tracking_enabled === "true");
        const active = profilesData.active || "default";
        setProfiles(profilesData.profiles || []);
        setActiveProfile(active);
        const profileData = await fetch(`${API}/api/profile?name=${active}`).then(r => r.json());
        setProfile(profileData);
        if (settings.first_launch_done !== "true") setShowOnboard(true);
        try {
          const patterns = await fetch(`${API}/api/patterns`).then(r => r.json());
          setActivityApps(patterns.top_apps || []);
          setActiveHours(patterns.active_hours || []);
        } catch {}
        setLoading(false);
        setTimeout(() => setFadeIn(true), 50);
      } catch {
        setStatus("Failed to connect to backend");
        setLoading(false);
      }
    })();
  }, []);

  const flash = (msg: string) => { setStatus(msg); setTimeout(() => setStatus(""), 3000); };
  const csvToArr = (s: string) => s.split(",").map(x => x.trim()).filter(Boolean);
  const arrToCsv = (a: string[]) => a.join(", ");

  const changeLang = async (l: Lang) => { setLang(l); await fetch(`${API}/api/settings`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ ui_lang: l }) }); };
  const refreshProfiles = async () => { const r = await fetch(`${API}/api/profiles`).then(r => r.json()); setProfiles(r.profiles || []); setActiveProfile(r.active || "default"); };
  const switchProfile = async (name: string) => { await fetch(`${API}/api/profiles/switch`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ name }) }); const d = await fetch(`${API}/api/profile?name=${name}`).then(r => r.json()); setProfile(d); setActiveProfile(name); await refreshProfiles(); };
  const createProfile = async () => { const name = prompt(T("topbar.newProfile") + ":"); if (!name?.trim()) return; await fetch(`${API}/api/profiles/create`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ name: name.trim() }) }); await refreshProfiles(); await switchProfile(name.trim()); };
  const deleteCurrentProfile = async () => { if (profiles.length <= 1) return; if (!confirm(T("topbar.deleteConfirm"))) return; await fetch(`${API}/api/profiles/delete`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ name: activeProfile }) }); await refreshProfiles(); const r = await fetch(`${API}/api/profiles`).then(r => r.json()); const d = await fetch(`${API}/api/profile?name=${r.active || "default"}`).then(r => r.json()); setProfile(d); setActiveProfile(r.active || "default"); };

  const save = async () => {
    if (!profile) return;
    const r = await fetch(`${API}/api/profile`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ ...profile, _profile_name: activeProfile }) });
    if (r.ok) {
      setSaveCheck(true);
      setTimeout(() => setSaveCheck(false), 2500);
      showToast(`✓ ${T("toast.saved")}`);
    } else {
      flash(T("action.saveFail"));
    }
  };
  const exportSelf = async () => { const r = await fetch(`${API}/api/export`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({}) }); const d = await r.json(); const a = document.createElement("a"); a.href = URL.createObjectURL(new Blob([d.encrypted], { type: "text/plain" })); a.download = d.filename || "selfcore_export.self.enc"; a.click(); flash(T("action.exported")); };
  const importSelf = () => fileRef.current?.click();
  const handleImport = async (e: React.ChangeEvent<HTMLInputElement>) => { const f = e.target.files?.[0]; if (!f) return; const txt = await f.text(); const r = await fetch(`${API}/api/import`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ encrypted: txt }) }); if (r.ok) { const d = await r.json(); setProfile(d.profile); flash(T("action.imported")); } else flash(T("action.importFail")); e.target.value = ""; };
  const resetAll = () => { setProfile({ version: "1.0", identity: { name: "", language: [], timezone: "", occupation: "" }, cognition: { decision_style: "", communication_preference: "", thinking_patterns: [], risk_tolerance: "" }, projects: [], preferences: { ai_interaction: "", output_format: "", design_taste: "", tools_primary: [] }, context_tags: { tech: [], interests: [], current_focus: "" } }); flash(T("action.resetDone")); };

  // Cold Start
  const handleChatGPTUpload = async (e: React.ChangeEvent<HTMLInputElement>) => { const f = e.target.files?.[0]; if (!f) return; setAnalyzing(true); const r = await fetch(`${API}/api/import/chatgpt`, { method: "POST", body: await f.arrayBuffer() }); if (r.ok) { const d = await r.json(); setExtracted(d.extracted); } else flash(T("coldstart.noData")); setAnalyzing(false); e.target.value = ""; };
  const analyzeText = async () => { if (!importText.trim()) return; setAnalyzing(true); const r = await fetch(`${API}/api/import/text`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ text: importText }) }); if (r.ok) { const d = await r.json(); setExtracted(d.extracted); } else flash(T("coldstart.noData")); setAnalyzing(false); };
  const applyExtracted = () => { if (!extracted || !profile) return; const u = { ...profile }; if (extracted.name) u.identity = { ...u.identity, name: extracted.name }; if (extracted.tech?.length) u.context_tags = { ...u.context_tags, tech: [...new Set([...u.context_tags.tech, ...extracted.tech])] }; if (extracted.interests?.length) u.context_tags = { ...u.context_tags, interests: [...new Set([...u.context_tags.interests, ...extracted.interests])] }; if (extracted.communication_style) u.cognition = { ...u.cognition, communication_preference: extracted.communication_style }; setProfile(u); setExtracted(null); setShowTextImport(false); setImportText(""); };

  const toggleTracking = async () => { const v = !trackingOn; setTrackingOn(v); await fetch(`${API}/api/settings`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ tracking_enabled: v ? "true" : "false" }) }); };

  // Profile setters
  const setI = (k: string, v: any) => { if (profile) setProfile({ ...profile, identity: { ...profile.identity, [k]: v } }); };
  const setC = (k: string, v: any) => { if (profile) setProfile({ ...profile, cognition: { ...profile.cognition, [k]: v } }); };
  const setP = (k: string, v: any) => { if (profile) setProfile({ ...profile, preferences: { ...profile.preferences, [k]: v } }); };
  const setCT = (k: string, v: any) => { if (profile) setProfile({ ...profile, context_tags: { ...profile.context_tags, [k]: v } }); };
  const updateProj = (i: number, k: string, v: string) => { if (!profile) return; const p = [...profile.projects]; p[i] = { ...p[i], [k]: v }; setProfile({ ...profile, projects: p }); };
  const addProj = () => { if (profile) setProfile({ ...profile, projects: [...profile.projects, { ...EMPTY_PROJECT }] }); };
  const rmProj = (i: number) => { if (profile) setProfile({ ...profile, projects: profile.projects.filter((_, j) => j !== i) }); };

  // Insights
  const loadInsights = async () => {
    try {
      const [an, su, inj, wk] = await Promise.all([
        fetch(`${API}/api/analyze`).then(r => r.json()),
        fetch(`${API}/api/suggestions`).then(r => r.json()),
        fetch(`${API}/api/injections`).then(r => r.json()),
        fetch(`${API}/api/weekly`).then(r => r.json()),
      ]);
      setAnalysisData(an);
      setSuggestions(su.suggestions || []);
      setInjections(inj.injections || []);
      setWeeklySummary(wk.total_records ? wk : null);
    } catch {}
  };

  const acceptSuggestion = async (s: Suggestion, idx: number) => {
    await fetch(`${API}/api/suggestions/apply`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(s) });
    const d = await fetch(`${API}/api/profile`).then(r => r.json());
    setProfile(d);
    setSuggestions(prev => prev.filter((_, i) => i !== idx));
    showToast(`'${s.value}' ${T("toast.applied")}`);
  };
  const dismissSuggestion = (idx: number) => { setSuggestions(prev => prev.filter((_, i) => i !== idx)); };

  const purgeActivity = async () => {
    if (!confirm(T("action.purgeConfirm"))) return;
    await fetch(`${API}/api/activity/purge`, { method: "POST" });
    setAnalysisData(null);
    setInjections([]);
    setWeeklySummary(null);
    showToast(T("action.purgeDone"));
  };

  // ─── Analysis (Phase 4A) ─────────────────
  const pollProgress = async () => {
    try {
      const r = await fetch(`${API}/api/analyze/status`).then(r => r.json());
      setAnalysisProgress(r.progress || 0);
      setAnalysisMsg(r.message || "");
      return r.status;
    } catch { return "error"; }
  };

  const runAnalysis = async (endpoint: string, body: any, isFile = false) => {
    setAnalysisLoading(true);
    setAnalysisProgress(5);
    setAnalysisMsg(T("toast.analysisStart"));
    try {
      const opts: RequestInit = { method: "POST" };
      if (isFile) {
        opts.body = body;
      } else {
        opts.headers = { "Content-Type": "application/json" };
        opts.body = JSON.stringify(body);
      }
      const r = await fetch(`${API}${endpoint}`, opts);
      if (!r.ok) {
        const err = await r.json().catch(() => ({ error: "Unknown error" }));
        showToast(err.error || "Analysis failed");
        setAnalysisLoading(false);
        return;
      }
      const result = await r.json();
      setAnalysisResult(result);
      setAnalysisResults(prev => [...prev, result]);
      showToast(T("toast.analysisComplete"));
    } catch (e: any) {
      showToast(e.message || "Analysis failed");
    }
    setAnalysisLoading(false);
    setAnalysisProgress(100);
  };

  const handleAnalysisChatGPT = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0]; if (!f) return;
    await runAnalysis("/api/analyze/chatgpt", await f.arrayBuffer(), true);
    e.target.value = "";
  };

  const handleAnalysisClaude = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0]; if (!f) return;
    await runAnalysis("/api/analyze/claude", await f.arrayBuffer(), true);
    e.target.value = "";
  };

  const handleAnalysisText = async () => {
    if (!analysisText.trim()) return;
    await runAnalysis("/api/analyze/text", { text: analysisText });
    setShowTextModal(false);
    setAnalysisText("");
  };

  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    const f = e.dataTransfer.files[0];
    if (!f || !f.name.endsWith(".zip")) { showToast(T("toast.zipOnly")); return; }
    const name = f.name.toLowerCase();
    const endpoint = name.includes("claude") ? "/api/analyze/claude" : "/api/analyze/chatgpt";
    await runAnalysis(endpoint, await f.arrayBuffer(), true);
  };

  const handleDragOver = (e: React.DragEvent) => { e.preventDefault(); e.stopPropagation(); };

  const deleteTechResult = (idx: number) => {
    if (!analysisResult) return;
    const tech = [...(analysisResult.entities?.tech || [])];
    tech.splice(idx, 1);
    setAnalysisResult({ ...analysisResult, entities: { ...analysisResult.entities, tech } });
  };

  const deletePrefResult = (idx: number) => {
    if (!analysisResult) return;
    const prefs = [...(analysisResult.preferences || [])];
    prefs.splice(idx, 1);
    setAnalysisResult({ ...analysisResult, preferences: prefs });
  };

  const mergeResults = async () => {
    if (analysisResults.length < 2) return;
    setAnalysisLoading(true);
    try {
      const r = await fetch(`${API}/api/analyze/merge`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ results: analysisResults })
      });
      if (r.ok) {
        const merged = await r.json();
        setAnalysisResult(merged);
        showToast(T("toast.merged"));
      }
    } catch {}
    setAnalysisLoading(false);
  };

  const applyAnalysisToProfile = () => {
    if (!analysisResult || !profile) return;
    const u = { ...profile };
    const techNames = (analysisResult.entities?.tech || []).map((t: any) => t.name);
    if (techNames.length > 0) {
      u.context_tags = { ...u.context_tags, tech: [...new Set([...u.context_tags.tech, ...techNames])] };
    }
    const likedTools = (analysisResult.preferences || []).filter((p: any) => p.sentiment === "Like").map((p: any) => p.target);
    if (likedTools.length > 0) {
      u.preferences = { ...u.preferences, tools_primary: [...new Set([...u.preferences.tools_primary, ...likedTools])] };
    }
    setProfile(u);
    showToast(T("toast.appliedToProfile"));
    setShowApplyPreview(false);
  };

  const resetAnalysis = () => {
    setAnalysisResult(null);
    setAnalysisResults([]);
    setConflictResolutions({});
    setShowApplyPreview(false);
    setAnalysisSuggestions([]);
    setSelectedSuggestions(new Set());
  };

  const fetchOllamaStatus = async () => {
    try {
      const r = await fetch(`${API}/api/ollama/status`).then(r => r.json());
      setOllamaStatus(r);
    } catch {}
  };

  const startOllama = async () => {
    try {
      await fetch(`${API}/api/ollama/start`, { method: "POST" });
      await fetchOllamaStatus();
    } catch {}
  };

  const pullModel = async () => {
    try {
      await fetch(`${API}/api/ollama/pull`, { method: "POST" });
      await fetchOllamaStatus();
    } catch {}
  };

  const generateSuggestions = async () => {
    if (!analysisResult || !profile) return;
    try {
      const r = await fetch(`${API}/api/analyze/suggestions`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ analysis_result: analysisResult, current_profile: profile })
      });
      if (r.ok) {
        const d = await r.json();
        setAnalysisSuggestions(d.suggestions || []);
        setSelectedSuggestions(new Set((d.suggestions || []).map((s: any) => s.id)));
      }
    } catch {}
  };

  const toggleSuggestion = (id: string) => {
    setSelectedSuggestions(prev => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id); else next.add(id);
      return next;
    });
  };

  const applySelectedSuggestions = async () => {
    const accepted = analysisSuggestions.filter(s => selectedSuggestions.has(s.id));
    if (!accepted.length) return;
    try {
      const r = await fetch(`${API}/api/analyze/suggestions/apply`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ accepted, profile })
      });
      if (r.ok) {
        const d = await r.json();
        setProfile(d.profile);
        showToast(`${accepted.length} ${T("toast.suggestionsApplied")}`);
        setAnalysisSuggestions([]);
        setSelectedSuggestions(new Set());
      }
    } catch {}
  };

  // Onboarding
  const finishOnboard = async (quick: boolean) => {
    if (quick && profile) {
      setProfile({ version: "1.0", identity: { name: "Alex Kim", language: ["Korean", "English"], timezone: "Asia/Seoul", occupation: "Software Developer" }, cognition: { decision_style: "Analytical, data-driven", communication_preference: "Concise and structured", thinking_patterns: ["systematic", "visual", "iterative"], risk_tolerance: "medium" }, projects: [{ name: "SelfCore", status: "active", stack: "Electron + Python + React", description: "Personal AI Identity Engine" }], preferences: { ai_interaction: "Direct, skip pleasantries", output_format: "Structured with headers and code blocks", design_taste: "Dark glassmorphism, minimal", tools_primary: ["VS Code", "Claude", "Git"] }, context_tags: { tech: ["Python", "TypeScript", "Electron", "React"], interests: ["AI", "UX Design", "Productivity"], current_focus: "Building SelfCore" } });
    }
    await fetch(`${API}/api/settings`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ first_launch_done: "true" }) });
    setShowOnboard(false);
  };

  // ─── RENDER ────────────────────────────────
  if (loading) return (
    <div style={{ display: "flex", alignItems: "center", justifyContent: "center", height: "100vh", flexDirection: "column", gap: "16px" }}>
      <div style={{ width: "48px", height: "48px", borderRadius: "50%", background: `linear-gradient(135deg, ${ACCENT}, #0ea5e9)`, display: "flex", alignItems: "center", justifyContent: "center", fontSize: "24px", fontWeight: 700, color: "#0f172a" }}>S</div>
      <p style={{ color: "rgba(255,255,255,0.5)", fontSize: "16px" }}>{T("app.connecting")}</p>
    </div>
  );
  if (!profile) return (
    <div style={{ display: "flex", alignItems: "center", justifyContent: "center", height: "100vh", flexDirection: "column", gap: "16px" }}>
      <p style={{ color: "#f87171", fontSize: "16px" }}>{T("app.error.backend")}</p>
      <p style={{ color: "rgba(255,255,255,0.3)", fontSize: "13px" }}>{T("backend.connecting")}</p>
    </div>
  );

  if (showOnboard) {
    return (
      <div style={{ display: "flex", alignItems: "center", justifyContent: "center", height: "100vh", padding: "32px" }}>
        <div style={{ ...CARD, maxWidth: "480px", width: "100%", textAlign: "center", padding: "40px" }}>
          <div style={{ fontSize: "48px", marginBottom: "16px" }}>🧠</div>
          <h1 style={{ fontSize: "28px", fontWeight: 700, marginBottom: "8px" }}>{T("onboard.welcome")}</h1>
          <p style={{ color: "rgba(255,255,255,0.5)", marginBottom: "28px", fontSize: "15px" }}>{T("onboard.desc")}</p>
          <div style={{ marginBottom: "24px" }}>
            <label style={{ ...LABEL, textAlign: "center" as any }}>{T("onboard.langSelect")}</label>
            <div style={{ display: "flex", gap: "12px", justifyContent: "center", marginTop: "8px" }}>
              <button onClick={() => changeLang("en")} style={{ ...pillBtn, background: lang === "en" ? ACCENT : "rgba(255,255,255,0.1)", color: lang === "en" ? "#0f172a" : "#fff" }}>English</button>
              <button onClick={() => changeLang("ko")} style={{ ...pillBtn, background: lang === "ko" ? ACCENT : "rgba(255,255,255,0.1)", color: lang === "ko" ? "#0f172a" : "#fff" }}>한국어</button>
            </div>
          </div>
          <div style={{ display: "flex", gap: "12px", justifyContent: "center" }}>
            <button onClick={() => finishOnboard(false)} style={{ border: "none", borderRadius: "10px", padding: "12px 24px", fontSize: "15px", fontWeight: 600, cursor: "pointer", background: "rgba(255,255,255,0.1)", color: "#fff" }}>{T("onboard.setup")}</button>
            <button onClick={() => finishOnboard(true)} style={{ border: "none", borderRadius: "10px", padding: "12px 24px", fontSize: "15px", fontWeight: 600, cursor: "pointer", background: ACCENT, color: "#0f172a" }}>{T("onboard.quick")}</button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div style={{ padding: "32px", minHeight: "100vh", opacity: fadeIn ? 1 : 0, transition: "opacity 0.5s ease" }}>
      {/* TOAST */}
      {toast && (
        <div style={{ position: "fixed", top: "20px", left: "50%", transform: "translateX(-50%)", background: "rgba(88,230,255,0.15)", border: `1px solid ${ACCENT}`, borderRadius: "10px", padding: "10px 24px", color: ACCENT, fontSize: "14px", fontWeight: 600, zIndex: 9999, backdropFilter: "blur(12px)", animation: "fadeSlideIn 0.3s ease" }}>
          {toast}
        </div>
      )}

      {/* TOP BAR */}
      <div className="titlebar-drag" style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "20px" }}>
        {/* Left: Logo + Name */}
        <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
          <div style={{ width: "36px", height: "36px", borderRadius: "50%", background: `linear-gradient(135deg, ${ACCENT}, #0ea5e9)`, display: "flex", alignItems: "center", justifyContent: "center", fontSize: "18px", fontWeight: 700, color: "#0f172a" }}>S</div>
          <div>
            <h1 style={{ fontSize: "20px", fontWeight: 700, margin: 0 }}>SelfCore</h1>
            <p style={{ fontSize: "11px", color: "rgba(255,255,255,0.35)", margin: 0 }}>{T("app.subtitle")} — v{profile.version}</p>
          </div>
        </div>
        {/* Center: Language + Profile */}
        <div className="titlebar-nodrag" style={{ display: "flex", alignItems: "center", gap: "10px" }}>
          <select value={lang} onChange={(e) => changeLang(e.target.value as Lang)} style={{ width: "auto", padding: "4px 8px", fontSize: "12px", borderRadius: "6px", background: "rgba(255,255,255,0.1)", border: "1px solid rgba(255,255,255,0.15)", color: "#fff" }}>
            <option value="en">EN</option>
            <option value="ko">KO</option>
          </select>
          <select value={activeProfile} onChange={(e) => switchProfile(e.target.value)} style={{ width: "auto", padding: "4px 8px", fontSize: "12px", borderRadius: "6px", background: "rgba(255,255,255,0.1)", border: "1px solid rgba(255,255,255,0.15)", color: "#fff" }}>
            {profiles.map(p => <option key={p} value={p}>{p}</option>)}
          </select>
          <button onClick={createProfile} title={T("topbar.newProfile")} style={smBtn}>+</button>
          {profiles.length > 1 && <button onClick={deleteCurrentProfile} title={T("topbar.deleteProfile")} style={{ ...smBtn, color: "#f87171", borderColor: "rgba(248,113,113,0.3)" }}>✕</button>}
          <div style={{ width: "1px", height: "20px", background: "rgba(255,255,255,0.1)", margin: "0 4px" }} />
          <button onClick={() => window.electronAPI?.minimize()} title={T("topbar.minimize")} style={smBtn}>─</button>
          <button onClick={() => window.electronAPI?.close()} title={T("topbar.close")} style={{ ...smBtn, color: "#f87171" }}>✕</button>
        </div>
      </div>

      {/* TAB BAR */}
      <div style={{ display: "flex", gap: "8px", marginBottom: "20px" }}>
        <TabBtn label={T("tab.editor")} active={tab === "editor"} onClick={() => setTab("editor")} />
        <TabBtn label={T("insights.title")} active={tab === "insights"} onClick={() => { setTab("insights"); loadInsights(); }} />
        <TabBtn label={`🔬 ${T("analysis.title")}`} active={tab === "analysis"} onClick={() => setTab("analysis")} />
      </div>

      {status && <div style={{ ...CARD, marginBottom: "20px", padding: "12px 20px", borderColor: ACCENT, color: ACCENT, fontSize: "14px" }}>{status}</div>}

      {tab === "analysis" ? (
        /* ─── ANALYSIS TAB ─── */
        <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
          {/* 1. IMPORT SECTION */}
          <div style={CARD} ref={dropRef} onDrop={handleDrop} onDragOver={handleDragOver}>
            <h2 style={h2Style}>{T("analysis.import.section")}</h2>
            <div style={{ display: "flex", gap: "12px", flexWrap: "wrap", marginBottom: "12px" }}>
              <button onClick={() => chatgptAnalysisRef.current?.click()} style={{ ...pillBtn, background: "rgba(16,163,127,0.15)", color: "#34d399", border: "1px solid rgba(52,211,153,0.3)" }}>{T("analysis.import.chatgpt")}</button>
              <button onClick={() => claudeAnalysisRef.current?.click()} style={{ ...pillBtn, background: "rgba(167,139,250,0.15)", color: "#a78bfa", border: "1px solid rgba(167,139,250,0.3)" }}>{T("analysis.import.claude")}</button>
              <button onClick={() => setShowTextModal(true)} style={{ ...pillBtn, background: `${ACCENT}15`, color: ACCENT, border: `1px solid ${ACCENT}44` }}>{T("analysis.import.text")}</button>
              {analysisResults.length >= 2 && <button onClick={mergeResults} style={{ ...pillBtn, background: "rgba(251,191,36,0.15)", color: "#fbbf24", border: "1px solid rgba(251,191,36,0.3)" }}>{T("analysis.results.mergeBtn")}</button>}
            </div>
            <input ref={chatgptAnalysisRef} type="file" accept=".zip" style={{ display: "none" }} onChange={handleAnalysisChatGPT} />
            <input ref={claudeAnalysisRef} type="file" accept=".zip" style={{ display: "none" }} onChange={handleAnalysisClaude} />
            <p style={{ fontSize: "12px", color: "rgba(255,255,255,0.3)" }}>{T("analysis.import.dragdrop")}</p>

            {/* 2. Progress bar */}
            {analysisLoading && (
              <div style={{ marginTop: "16px" }}>
                <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "6px" }}>
                  <span style={{ fontSize: "12px", color: ACCENT }}>{T("analysis.progress")}</span>
                  <span style={{ fontSize: "12px", color: "rgba(255,255,255,0.5)" }}>{analysisProgress}%</span>
                </div>
                <div style={{ height: "6px", background: "rgba(255,255,255,0.1)", borderRadius: "3px", overflow: "hidden" }}>
                  <div style={{ height: "100%", width: `${analysisProgress}%`, background: `linear-gradient(90deg, ${ACCENT}, #0ea5e9)`, borderRadius: "3px", transition: "width 0.3s ease" }} />
                </div>
                {analysisMsg && <p style={{ fontSize: "11px", color: "rgba(255,255,255,0.4)", marginTop: "4px" }}>{analysisMsg}</p>}
              </div>
            )}
          </div>

          {/* TEXT MODAL */}
          {showTextModal && (
            <div style={CARD}>
              <h2 style={h2Style}>{T("analysis.import.text")}</h2>
              <textarea rows={8} placeholder={T("coldstart.paste")} value={analysisText} onChange={(e) => setAnalysisText(e.target.value)} style={{ resize: "vertical", marginBottom: "12px" }} />
              <div style={{ display: "flex", gap: "8px" }}>
                <button onClick={handleAnalysisText} disabled={analysisLoading} style={{ ...pillBtn, background: `${ACCENT}22`, color: ACCENT, border: `1px solid ${ACCENT}44` }}>{analysisLoading ? T("analysis.progress") : T("coldstart.analyze")}</button>
                <button onClick={() => { setShowTextModal(false); setAnalysisText(""); }} style={{ ...pillBtn, background: "rgba(255,255,255,0.05)", color: "rgba(255,255,255,0.5)" }}>{T("coldstart.cancel")}</button>
              </div>
            </div>
          )}

          {/* 3. RESULTS SECTION */}
          {analysisResult ? (
            <>
              {/* Tech Stack */}
              <div style={CARD}>
                <h2 style={h2Style}>{T("analysis.results.techStack")}</h2>
                <p style={{ fontSize: "12px", color: "rgba(255,255,255,0.4)", marginBottom: "12px" }}>{analysisResult.stats?.total_messages || 0} {T("analysis.results.messages")}</p>
                <div style={{ display: "flex", flexWrap: "wrap", gap: "8px" }}>
                  {(analysisResult.entities?.tech || []).map((tech: any, i: number) => (
                    <div key={i} style={{ background: "rgba(88,230,255,0.08)", border: "1px solid rgba(88,230,255,0.15)", borderRadius: "8px", padding: "6px 12px", display: "flex", alignItems: "center", gap: "8px" }}>
                      <span style={{ fontSize: "13px", color: "#fff" }}>{tech.name}</span>
                      <span style={{ fontSize: "11px", color: ACCENT }}>{tech.count} {T("analysis.results.count")}</span>
                      <button onClick={() => deleteTechResult(i)} style={{ background: "none", border: "none", color: "rgba(248,113,113,0.6)", cursor: "pointer", fontSize: "12px", padding: "0 2px" }}>✕</button>
                    </div>
                  ))}
                  {(analysisResult.entities?.tech || []).length === 0 && <p style={{ fontSize: "13px", color: "rgba(255,255,255,0.3)" }}>{T("analysis.results.noTech")}</p>}
                </div>
              </div>

              {/* Preferences */}
              <div style={CARD}>
                <h2 style={h2Style}>{T("analysis.results.preferences")}</h2>
                <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                  {(analysisResult.preferences || []).map((pref: any, i: number) => (
                    <div key={i} style={{ display: "flex", alignItems: "center", gap: "12px", background: "rgba(30,41,59,0.5)", borderRadius: "10px", padding: "10px 16px", border: "1px solid rgba(255,255,255,0.05)" }}>
                      <span style={{ fontSize: "13px", color: "#fff", fontWeight: 600, minWidth: "100px" }}>{pref.target}</span>
                      <span style={{ fontSize: "12px", color: pref.sentiment === "Like" ? "#34d399" : "#f87171", background: pref.sentiment === "Like" ? "rgba(52,211,153,0.15)" : "rgba(248,113,113,0.15)", padding: "2px 10px", borderRadius: "6px" }}>
                        {pref.sentiment === "Like" ? T("analysis.results.like") : T("analysis.results.dislike")}
                      </span>
                      <span style={{ fontSize: "11px", color: "rgba(255,255,255,0.4)" }}>{T("analysis.results.confidence")}: {pref.confidence === "high" ? T("analysis.results.high") : pref.confidence === "medium" ? T("analysis.results.medium") : T("analysis.results.low")}</span>
                      <button onClick={() => deletePrefResult(i)} style={{ background: "none", border: "none", color: "rgba(248,113,113,0.6)", cursor: "pointer", fontSize: "12px", marginLeft: "auto" }}>✕</button>
                    </div>
                  ))}
                  {(analysisResult.preferences || []).length === 0 && <p style={{ fontSize: "13px", color: "rgba(255,255,255,0.3)" }}>{T("analysis.results.noPrefs")}</p>}
                </div>
              </div>

              {/* Topics */}
              <div style={CARD}>
                <h2 style={h2Style}>{T("analysis.results.topics")}</h2>
                {analysisResult.topics?.skipped ? (
                  <p style={{ fontSize: "13px", color: "rgba(255,255,255,0.3)" }}>{T("analysis.results.topicsPlaceholder")}</p>
                ) : (
                  <div style={{ display: "flex", flexWrap: "wrap", gap: "8px" }}>
                    {(analysisResult.topics?.top_keywords || []).map((kw: any, i: number) => (
                      <div key={i} style={{ background: "rgba(251,191,36,0.08)", border: "1px solid rgba(251,191,36,0.15)", borderRadius: "8px", padding: "6px 12px", display: "flex", alignItems: "center", gap: "8px" }}>
                        <span style={{ fontSize: "13px", color: "#fff" }}>{kw.word}</span>
                        <span style={{ fontSize: "11px", color: "#fbbf24" }}>{kw.count}x</span>
                        <span style={{ fontSize: "10px", color: "rgba(255,255,255,0.3)" }}>{T("analysis.results.topicsScore")}: {kw.score?.toFixed(3)}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Communication Style */}
              {analysisResult.communication_style && (
                <div style={CARD}>
                  <h2 style={h2Style}>{T("analysis.results.style")}</h2>
                  <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(180px, 1fr))", gap: "12px" }}>
                    <div style={{ background: "rgba(30,41,59,0.5)", borderRadius: "10px", padding: "12px 16px", border: "1px solid rgba(255,255,255,0.05)" }}>
                      <span style={LABEL}>{T("analysis.results.style.formality")}</span>
                      <span style={{ fontSize: "15px", color: "#fff", fontWeight: 600 }}>{analysisResult.communication_style.formality}</span>
                    </div>
                    <div style={{ background: "rgba(30,41,59,0.5)", borderRadius: "10px", padding: "12px 16px", border: "1px solid rgba(255,255,255,0.05)" }}>
                      <span style={LABEL}>{T("analysis.results.style.verbosity")}</span>
                      <span style={{ fontSize: "15px", color: "#fff", fontWeight: 600 }}>{analysisResult.communication_style.verbosity}</span>
                    </div>
                    <div style={{ background: "rgba(30,41,59,0.5)", borderRadius: "10px", padding: "12px 16px", border: "1px solid rgba(255,255,255,0.05)" }}>
                      <span style={LABEL}>{T("analysis.results.style.codeRatio")}</span>
                      <span style={{ fontSize: "15px", color: "#fff", fontWeight: 600 }}>{((analysisResult.communication_style.code_ratio || 0) * 100).toFixed(1)}%</span>
                    </div>
                    <div style={{ background: "rgba(30,41,59,0.5)", borderRadius: "10px", padding: "12px 16px", border: "1px solid rgba(255,255,255,0.05)" }}>
                      <span style={LABEL}>{T("analysis.results.style.questionRatio")}</span>
                      <span style={{ fontSize: "15px", color: "#fff", fontWeight: 600 }}>{((analysisResult.communication_style.question_ratio || 0) * 100).toFixed(1)}%</span>
                    </div>
                    <div style={{ background: "rgba(30,41,59,0.5)", borderRadius: "10px", padding: "12px 16px", border: "1px solid rgba(255,255,255,0.05)" }}>
                      <span style={LABEL}>{T("analysis.results.style.avgLength")}</span>
                      <span style={{ fontSize: "15px", color: "#fff", fontWeight: 600 }}>{Math.round(analysisResult.communication_style.avg_message_length || 0)} chars</span>
                    </div>
                    <div style={{ background: "rgba(30,41,59,0.5)", borderRadius: "10px", padding: "12px 16px", border: "1px solid rgba(255,255,255,0.05)" }}>
                      <span style={LABEL}>{T("analysis.results.style.langMix")}</span>
                      <span style={{ fontSize: "15px", color: "#fff", fontWeight: 600 }}>
                        {Object.entries(analysisResult.communication_style.language_mix || {}).map(([k, v]: [string, any]) => `${k}: ${(v * 100).toFixed(0)}%`).join(" / ")}
                      </span>
                    </div>
                  </div>
                  {analysisResult.communication_style.summary && (
                    <p style={{ fontSize: "12px", color: "rgba(255,255,255,0.4)", marginTop: "12px" }}>{analysisResult.communication_style.summary}</p>
                  )}
                </div>
              )}

              {/* LLM Profile */}
              {analysisResult.llm_profile ? (
                <div style={{ ...CARD, borderColor: "rgba(167,139,250,0.2)" }}>
                  <h2 style={{ ...h2Style, color: "#a78bfa" }}>{T("analysis.results.llmProfile")}</h2>
                  <pre style={{ fontSize: "12px", color: "rgba(255,255,255,0.6)", background: "rgba(30,41,59,0.5)", borderRadius: "8px", padding: "12px", overflow: "auto", maxHeight: "200px", border: "1px solid rgba(255,255,255,0.05)" }}>
                    {JSON.stringify(analysisResult.llm_profile, null, 2)}
                  </pre>
                </div>
              ) : (
                <div style={{ ...CARD, opacity: 0.6 }}>
                  <h2 style={h2Style}>{T("analysis.results.llmProfile")}</h2>
                  <p style={{ fontSize: "13px", color: "rgba(255,255,255,0.3)" }}>{T("analysis.results.llmUnavailable")}</p>
                </div>
              )}

              {/* 6. Conflicts */}
              {analysisResult.conflicts?.length > 0 && (
                <div style={{ ...CARD, borderColor: "rgba(251,191,36,0.3)" }}>
                  <h2 style={{ ...h2Style, color: "#fbbf24" }}>{T("analysis.conflict.title")}</h2>
                  {analysisResult.conflicts.map((c: any, i: number) => (
                    <div key={i} style={{ background: "rgba(251,191,36,0.05)", borderRadius: "10px", padding: "14px", marginBottom: "10px", border: "1px solid rgba(251,191,36,0.15)" }}>
                      <p style={{ fontSize: "13px", color: "#fff", marginBottom: "8px" }}>
                        {c.source_a}: {c.target} {c.sentiment_a === "Like" ? "👍" : "👎"} / {c.source_b}: {c.target} {c.sentiment_b === "Like" ? "👍" : "👎"} -- {T("analysis.conflict.question")}
                      </p>
                      <div style={{ display: "flex", gap: "8px" }}>
                        <label style={{ display: "flex", alignItems: "center", gap: "4px", fontSize: "12px", color: "#34d399", cursor: "pointer" }}>
                          <input type="radio" name={`conflict-${i}`} value="Like" checked={conflictResolutions[c.target] === "Like"} onChange={() => setConflictResolutions(prev => ({ ...prev, [c.target]: "Like" }))} /> {T("analysis.results.like")}
                        </label>
                        <label style={{ display: "flex", alignItems: "center", gap: "4px", fontSize: "12px", color: "#f87171", cursor: "pointer" }}>
                          <input type="radio" name={`conflict-${i}`} value="Dislike" checked={conflictResolutions[c.target] === "Dislike"} onChange={() => setConflictResolutions(prev => ({ ...prev, [c.target]: "Dislike" }))} /> {T("analysis.results.dislike")}
                        </label>
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {/* 5. SUGGESTIONS SECTION */}
              <div style={CARD}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "12px" }}>
                  <h2 style={{ ...h2Style, margin: 0 }}>{T("analysis.suggestions.title")}</h2>
                  <button onClick={generateSuggestions} style={{ ...pillBtn, background: `${ACCENT}15`, color: ACCENT, border: `1px solid ${ACCENT}33`, padding: "6px 14px", fontSize: "12px" }}>{T("analysis.suggestions.generate")}</button>
                </div>
                {analysisSuggestions.length > 0 ? (
                  <>
                    <div style={{ display: "flex", flexDirection: "column", gap: "8px", marginBottom: "12px" }}>
                      {analysisSuggestions.map((s: any) => (
                        <div key={s.id} style={{ display: "flex", alignItems: "center", gap: "12px", background: selectedSuggestions.has(s.id) ? "rgba(88,230,255,0.05)" : "rgba(30,41,59,0.5)", borderRadius: "10px", padding: "10px 16px", border: selectedSuggestions.has(s.id) ? `1px solid ${ACCENT}33` : "1px solid rgba(255,255,255,0.05)", cursor: "pointer", transition: "all 0.2s ease" }} onClick={() => toggleSuggestion(s.id)}>
                          <input type="checkbox" checked={selectedSuggestions.has(s.id)} onChange={() => toggleSuggestion(s.id)} style={{ accentColor: ACCENT }} />
                          <div style={{ flex: 1 }}>
                            <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "2px" }}>
                              <span style={{ fontSize: "13px", color: "#fff", fontWeight: 600 }}>{s.value}</span>
                              <span style={{ fontSize: "10px", color: "rgba(255,255,255,0.3)", background: "rgba(255,255,255,0.05)", padding: "1px 6px", borderRadius: "4px" }}>{s.type}</span>
                              <span style={{ fontSize: "10px", color: "rgba(255,255,255,0.3)", background: "rgba(255,255,255,0.05)", padding: "1px 6px", borderRadius: "4px" }}>{T("analysis.suggestions.source")}: {s.source}</span>
                            </div>
                            <p style={{ fontSize: "11px", color: "rgba(255,255,255,0.4)", margin: 0 }}>{lang === "ko" ? s.reason_ko : s.reason_en}</p>
                          </div>
                          <div style={{ display: "flex", alignItems: "center", gap: "4px", minWidth: "70px" }}>
                            <div style={{ width: "40px", height: "4px", background: "rgba(255,255,255,0.1)", borderRadius: "2px", overflow: "hidden" }}>
                              <div style={{ height: "100%", width: `${(s.confidence || 0) * 100}%`, background: s.confidence >= 0.7 ? "#34d399" : s.confidence >= 0.4 ? "#fbbf24" : "#f87171", borderRadius: "2px" }} />
                            </div>
                            <span style={{ fontSize: "10px", color: "rgba(255,255,255,0.4)" }}>{((s.confidence || 0) * 100).toFixed(0)}%</span>
                          </div>
                        </div>
                      ))}
                    </div>
                    <div style={{ display: "flex", gap: "8px", justifyContent: "center" }}>
                      <button onClick={() => setSelectedSuggestions(new Set(analysisSuggestions.map((s: any) => s.id)))} style={{ ...pillBtn, fontSize: "12px", padding: "6px 14px", background: "rgba(255,255,255,0.05)", color: "rgba(255,255,255,0.5)" }}>{T("analysis.suggestions.acceptAll")}</button>
                      <button onClick={applySelectedSuggestions} disabled={selectedSuggestions.size === 0} style={{ ...pillBtn, fontSize: "12px", padding: "6px 14px", background: selectedSuggestions.size > 0 ? `${ACCENT}22` : "rgba(255,255,255,0.03)", color: selectedSuggestions.size > 0 ? ACCENT : "rgba(255,255,255,0.2)", border: `1px solid ${selectedSuggestions.size > 0 ? ACCENT + "44" : "rgba(255,255,255,0.05)"}` }}>
                        {T("analysis.suggestions.applySelected")} ({selectedSuggestions.size})
                      </button>
                    </div>
                  </>
                ) : (
                  <p style={{ fontSize: "13px", color: "rgba(255,255,255,0.3)" }}>{T("analysis.suggestions.empty")}</p>
                )}
              </div>

              {/* Apply/Reset Section */}
              <div style={{ ...CARD, display: "flex", flexDirection: "column", gap: "12px", alignItems: "center" }}>
                {showApplyPreview && (
                  <div style={{ width: "100%", background: "rgba(88,230,255,0.05)", borderRadius: "10px", padding: "16px", border: "1px solid rgba(88,230,255,0.15)", marginBottom: "8px" }}>
                    <p style={{ fontSize: "13px", color: ACCENT, marginBottom: "8px" }}>{T("analysis.preview")}</p>
                    {(analysisResult.entities?.tech || []).length > 0 && <p style={{ fontSize: "12px", color: "rgba(255,255,255,0.5)" }}>+ Tech: {(analysisResult.entities?.tech || []).map((t: any) => t.name).join(", ")}</p>}
                    {(analysisResult.preferences || []).filter((p: any) => p.sentiment === "Like").length > 0 && <p style={{ fontSize: "12px", color: "rgba(255,255,255,0.5)", marginTop: "4px" }}>+ Tools: {(analysisResult.preferences || []).filter((p: any) => p.sentiment === "Like").map((p: any) => p.target).join(", ")}</p>}
                  </div>
                )}
                <div style={{ display: "flex", gap: "12px" }}>
                  <button onClick={() => { if (showApplyPreview) applyAnalysisToProfile(); else setShowApplyPreview(true); }} style={{ ...pillBtn, background: `${ACCENT}22`, color: ACCENT, border: `1px solid ${ACCENT}44` }}>
                    {showApplyPreview ? T("analysis.apply") : T("analysis.preview")}
                  </button>
                  <button onClick={resetAnalysis} style={{ ...pillBtn, background: "rgba(248,113,113,0.1)", color: "#f87171", border: "1px solid rgba(248,113,113,0.2)" }}>{T("analysis.rerun")}</button>
                </div>
              </div>
            </>
          ) : !analysisLoading && (
            <div style={{ ...CARD, textAlign: "center" as any, padding: "40px" }}>
              <p style={{ fontSize: "14px", color: "rgba(255,255,255,0.3)" }}>{T("analysis.noResults")}</p>
            </div>
          )}

          {/* 4. OLLAMA STATUS SECTION */}
          <div style={CARD}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "12px" }}>
              <h2 style={{ ...h2Style, margin: 0 }}>{T("analysis.ollama.title")}</h2>
              <button onClick={fetchOllamaStatus} style={{ ...pillBtn, padding: "4px 12px", fontSize: "11px", background: "rgba(255,255,255,0.05)", color: "rgba(255,255,255,0.5)" }}>Refresh</button>
            </div>
            {ollamaStatus ? (
              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(150px, 1fr))", gap: "10px" }}>
                <div style={{ background: "rgba(30,41,59,0.5)", borderRadius: "8px", padding: "10px 14px", border: "1px solid rgba(255,255,255,0.05)" }}>
                  <span style={LABEL}>Status</span>
                  <span style={{ fontSize: "13px", color: ollamaStatus.installed ? "#34d399" : "#f87171", fontWeight: 600 }}>{ollamaStatus.installed ? T("analysis.ollama.installed") : T("analysis.ollama.notInstalled")}</span>
                </div>
                <div style={{ background: "rgba(30,41,59,0.5)", borderRadius: "8px", padding: "10px 14px", border: "1px solid rgba(255,255,255,0.05)" }}>
                  <span style={LABEL}>Server</span>
                  <span style={{ fontSize: "13px", color: ollamaStatus.running ? "#34d399" : "#fbbf24", fontWeight: 600 }}>{ollamaStatus.running ? T("analysis.ollama.running") : T("analysis.ollama.stopped")}</span>
                </div>
                <div style={{ background: "rgba(30,41,59,0.5)", borderRadius: "8px", padding: "10px 14px", border: "1px solid rgba(255,255,255,0.05)" }}>
                  <span style={LABEL}>{T("analysis.ollama.model")}</span>
                  <span style={{ fontSize: "13px", color: ollamaStatus.model_available ? "#34d399" : "rgba(255,255,255,0.4)", fontWeight: 600 }}>{ollamaStatus.model_name || "N/A"} {ollamaStatus.model_available ? "✓" : ""}</span>
                </div>
                <div style={{ background: "rgba(30,41,59,0.5)", borderRadius: "8px", padding: "10px 14px", border: "1px solid rgba(255,255,255,0.05)" }}>
                  <span style={LABEL}>{T("analysis.ollama.gpu")}</span>
                  <span style={{ fontSize: "13px", color: ollamaStatus.gpu_available ? "#34d399" : "rgba(255,255,255,0.4)", fontWeight: 600 }}>{ollamaStatus.gpu_available ? `${ollamaStatus.gpu_usage_percent ?? "?"}%` : "N/A"}</span>
                </div>
              </div>
            ) : (
              <p style={{ fontSize: "13px", color: "rgba(255,255,255,0.3)" }}>{T("analysis.ollama.clickRefresh")}</p>
            )}
            {ollamaStatus?.installed && (
              <div style={{ display: "flex", gap: "8px", marginTop: "12px" }}>
                {!ollamaStatus.running && <button onClick={startOllama} style={{ ...pillBtn, fontSize: "12px", padding: "6px 14px", background: "rgba(52,211,153,0.15)", color: "#34d399", border: "1px solid rgba(52,211,153,0.3)" }}>{T("analysis.ollama.start")}</button>}
                {!ollamaStatus.model_available && <button onClick={pullModel} style={{ ...pillBtn, fontSize: "12px", padding: "6px 14px", background: "rgba(167,139,250,0.15)", color: "#a78bfa", border: "1px solid rgba(167,139,250,0.3)" }}>{T("analysis.ollama.pull")}</button>}
              </div>
            )}
          </div>

          {/* 7. GUIDE SECTION */}
          <div style={CARD}>
            <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
              <button onClick={() => setShowGuide(showGuide === "chatgpt" ? null : "chatgpt")} style={{ ...pillBtn, background: "rgba(255,255,255,0.03)", textAlign: "left" as any, display: "flex", justifyContent: "space-between", alignItems: "center", width: "100%" }}>
                <span>{T("analysis.guide.chatgpt.title")}</span>
                <span style={{ fontSize: "12px" }}>{showGuide === "chatgpt" ? "▲" : "▼"}</span>
              </button>
              {showGuide === "chatgpt" && (
                <div style={{ padding: "12px 16px", background: "rgba(255,255,255,0.02)", borderRadius: "8px" }}>
                  {(["step1", "step2", "step3", "step4", "step5"] as const).map(s => (
                    <p key={s} style={{ fontSize: "13px", color: "rgba(255,255,255,0.5)", padding: "4px 0" }}>{T(`analysis.guide.chatgpt.${s}` as any)}</p>
                  ))}
                </div>
              )}
              <button onClick={() => setShowGuide(showGuide === "claude" ? null : "claude")} style={{ ...pillBtn, background: "rgba(255,255,255,0.03)", textAlign: "left" as any, display: "flex", justifyContent: "space-between", alignItems: "center", width: "100%" }}>
                <span>{T("analysis.guide.claude.title")}</span>
                <span style={{ fontSize: "12px" }}>{showGuide === "claude" ? "▲" : "▼"}</span>
              </button>
              {showGuide === "claude" && (
                <div style={{ padding: "12px 16px", background: "rgba(255,255,255,0.02)", borderRadius: "8px" }}>
                  {(["step1", "step2", "step3", "step4", "step5"] as const).map(s => (
                    <p key={s} style={{ fontSize: "13px", color: "rgba(255,255,255,0.5)", padding: "4px 0" }}>{T(`analysis.guide.claude.${s}` as any)}</p>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      ) : tab === "editor" ? (
        <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
          {/* COLD START */}
          <div style={CARD}>
            <h2 style={h2Style}>{T("coldstart.title")}</h2>
            <div style={{ display: "flex", gap: "12px", flexWrap: "wrap" }}>
              <button onClick={() => chatgptRef.current?.click()} style={{ ...pillBtn, background: "rgba(16,163,127,0.15)", color: "#34d399", border: "1px solid rgba(52,211,153,0.3)" }}>{T("coldstart.chatgpt")}</button>
              <button onClick={() => setShowTextImport(!showTextImport)} style={{ ...pillBtn, background: "rgba(167,139,250,0.15)", color: "#a78bfa", border: "1px solid rgba(167,139,250,0.3)" }}>{T("coldstart.text")}</button>
            </div>
            <input ref={chatgptRef} type="file" accept=".zip" style={{ display: "none" }} onChange={handleChatGPTUpload} />
            {showTextImport && (
              <div style={{ marginTop: "16px" }}>
                <textarea rows={5} placeholder={T("coldstart.paste")} value={importText} onChange={(e) => setImportText(e.target.value)} style={{ resize: "vertical", marginBottom: "12px" }} />
                <div style={{ display: "flex", gap: "8px" }}>
                  <button onClick={analyzeText} disabled={analyzing} style={{ ...pillBtn, background: `${ACCENT}22`, color: ACCENT, border: `1px solid ${ACCENT}44` }}>{analyzing ? T("coldstart.analyzing") : T("coldstart.analyze")}</button>
                  <button onClick={() => { setShowTextImport(false); setImportText(""); }} style={{ ...pillBtn, background: "rgba(255,255,255,0.05)", color: "rgba(255,255,255,0.5)" }}>{T("coldstart.cancel")}</button>
                </div>
              </div>
            )}
            {extracted && (
              <div style={{ marginTop: "16px", background: "rgba(88,230,255,0.05)", borderRadius: "12px", padding: "16px", border: "1px solid rgba(88,230,255,0.15)" }}>
                <p style={{ color: ACCENT, fontSize: "13px", marginBottom: "12px" }}>{T("coldstart.review")}</p>
                {extracted.name && <p style={{ fontSize: "13px", color: "#fff", marginBottom: "4px" }}>Name: <strong>{extracted.name}</strong></p>}
                {extracted.tech?.length > 0 && <p style={{ fontSize: "13px", color: "#fff", marginBottom: "4px" }}>Tech: <strong>{extracted.tech.join(", ")}</strong></p>}
                {extracted.interests?.length > 0 && <p style={{ fontSize: "13px", color: "#fff", marginBottom: "4px" }}>Interests: <strong>{extracted.interests.join(", ")}</strong></p>}
                <p style={{ fontSize: "13px", color: "#fff", marginBottom: "12px" }}>Style: <strong>{extracted.communication_style}</strong></p>
                <button onClick={applyExtracted} style={{ ...pillBtn, background: `${ACCENT}22`, color: ACCENT, border: `1px solid ${ACCENT}44` }}>{T("coldstart.apply")}</button>
              </div>
            )}
          </div>

          {/* ACTIVITY */}
          <div style={CARD}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
              <h2 style={{ ...h2Style, margin: 0 }}>{T("activity.title")}</h2>
              <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                <span style={{ fontSize: "12px", color: "rgba(255,255,255,0.5)" }}>{T("activity.tracking")}:</span>
                <button onClick={toggleTracking} style={{ ...pillBtn, padding: "4px 12px", fontSize: "12px", background: trackingOn ? "rgba(52,211,153,0.2)" : "rgba(255,255,255,0.05)", color: trackingOn ? "#34d399" : "rgba(255,255,255,0.4)", border: trackingOn ? "1px solid rgba(52,211,153,0.3)" : "1px solid rgba(255,255,255,0.1)" }}>
                  {trackingOn ? T("activity.on") : T("activity.off")}
                </button>
              </div>
            </div>
            {activityApps.length > 0 ? (
              <div>
                <p style={{ fontSize: "13px", color: "rgba(255,255,255,0.5)", marginBottom: "8px" }}>{T("activity.today")}:</p>
                <div style={{ display: "flex", gap: "8px", flexWrap: "wrap", marginBottom: "12px" }}>
                  {activityApps.slice(0, 6).map((a, i) => <Tag key={i} label={`${a.name} `} value={a.time} />)}
                </div>
                {activeHours.length > 0 && <p style={{ fontSize: "12px", color: "rgba(255,255,255,0.4)" }}>{T("activity.mostActive")}: {activeHours.slice(0, 3).map(h => h.hour).join(", ")}</p>}
              </div>
            ) : (
              <div>
                <p style={{ fontSize: "13px", color: "rgba(255,255,255,0.3)" }}>{T("insights.enableTracking")}</p>
                <p style={{ fontSize: "11px", color: "rgba(255,255,255,0.2)", marginTop: "4px" }}>{T("activity.privacy")}</p>
              </div>
            )}
          </div>

          {/* IDENTITY */}
          <div style={CARD}>
            <h2 style={h2Style}>{T("identity.title")}</h2>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px" }}>
              <Field label={T("identity.name")} value={profile.identity.name} onChange={(v) => setI("name", v)} placeholder={lang === "ko" ? "이름을 입력하세요" : "Enter your name"} />
              <Field label={T("identity.occupation")} value={profile.identity.occupation} onChange={(v) => setI("occupation", v)} placeholder={lang === "ko" ? "예: 소프트웨어 개발자" : "e.g. Software Developer"} />
              <Field label={T("identity.languages")} value={arrToCsv(profile.identity.language)} onChange={(v) => setI("language", csvToArr(v))} placeholder={lang === "ko" ? "예: Korean, English" : "e.g. English, Korean"} />
              <div><label style={LABEL}>{T("identity.timezone")}</label><select value={profile.identity.timezone} onChange={(e) => setI("timezone", e.target.value)}><option value="">{T("identity.selectTimezone")}</option>{TIMEZONES.map(tz => <option key={tz} value={tz}>{tz}</option>)}</select></div>
            </div>
          </div>

          {/* COGNITION */}
          <div style={CARD}>
            <h2 style={h2Style}>{T("cognition.title")}</h2>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px" }}>
              <Field label={T("cognition.decisionStyle")} value={profile.cognition.decision_style} onChange={(v) => setC("decision_style", v)} placeholder={lang === "ko" ? "예: 분석적, 데이터 기반" : "e.g. Analytical, data-driven"} />
              <Field label={T("cognition.commPref")} value={profile.cognition.communication_preference} onChange={(v) => setC("communication_preference", v)} placeholder={lang === "ko" ? "예: 간결하고 구조적" : "e.g. Concise and structured"} />
              <Field label={T("cognition.thinkingPatterns")} value={arrToCsv(profile.cognition.thinking_patterns)} onChange={(v) => setC("thinking_patterns", csvToArr(v))} placeholder={lang === "ko" ? "예: 체계적, 시각적" : "e.g. systematic, visual"} />
              <div><label style={LABEL}>{T("cognition.riskTolerance")}</label><select value={profile.cognition.risk_tolerance} onChange={(e) => setC("risk_tolerance", e.target.value)}><option value="">{T("cognition.select")}</option><option value="low">{T("cognition.low")}</option><option value="medium">{T("cognition.medium")}</option><option value="high">{T("cognition.high")}</option></select></div>
            </div>
          </div>

          {/* PROJECTS */}
          <div style={CARD}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
              <h2 style={{ ...h2Style, margin: 0 }}>{T("projects.title")}</h2>
              <button onClick={addProj} style={{ background: ACCENT, color: "#0f172a", border: "none", borderRadius: "8px", padding: "6px 14px", fontSize: "13px", fontWeight: 600, cursor: "pointer" }}>{T("projects.add")}</button>
            </div>
            {profile.projects.length === 0 && <p style={{ color: "rgba(255,255,255,0.3)", fontSize: "13px" }}>{T("projects.empty")}</p>}
            {profile.projects.map((proj, idx) => (
              <div key={idx} style={{ background: "rgba(30,41,59,0.5)", borderRadius: "12px", padding: "16px", marginBottom: idx < profile.projects.length - 1 ? "12px" : "0", border: "1px solid rgba(255,255,255,0.05)" }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "12px" }}>
                  <span style={{ fontSize: "13px", color: "rgba(255,255,255,0.4)" }}>{T("projects.number")} #{idx + 1}</span>
                  <button onClick={() => rmProj(idx)} style={{ background: "rgba(255,80,80,0.2)", color: "#ff5050", border: "1px solid rgba(255,80,80,0.3)", borderRadius: "6px", padding: "4px 10px", fontSize: "12px", cursor: "pointer" }}>{T("projects.remove")}</button>
                </div>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px" }}>
                  <Field label={T("projects.name")} value={proj.name} onChange={(v) => updateProj(idx, "name", v)} placeholder={lang === "ko" ? "프로젝트 이름" : "Project name"} />
                  <div><label style={LABEL}>{T("projects.status")}</label><select value={proj.status} onChange={(e) => updateProj(idx, "status", e.target.value)}><option value="planning">{T("projects.planning")}</option><option value="active">{T("projects.active")}</option><option value="paused">{T("projects.paused")}</option><option value="completed">{T("projects.completed")}</option></select></div>
                  <Field label={T("projects.stack")} value={proj.stack} onChange={(v) => updateProj(idx, "stack", v)} placeholder={lang === "ko" ? "예: React, Python" : "e.g. React, Python"} />
                  <div><label style={LABEL}>{T("projects.description")}</label><textarea rows={2} value={proj.description} onChange={(e) => updateProj(idx, "description", e.target.value)} placeholder={lang === "ko" ? "프로젝트 설명" : "Project description"} style={{ resize: "vertical" }} /></div>
                </div>
              </div>
            ))}
          </div>

          {/* PREFERENCES */}
          <div style={CARD}>
            <h2 style={h2Style}>{T("preferences.title")}</h2>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px" }}>
              <Field label={T("preferences.aiInteraction")} value={profile.preferences.ai_interaction} onChange={(v) => setP("ai_interaction", v)} placeholder={lang === "ko" ? "예: 직접적, 간결하게" : "e.g. Direct, skip pleasantries"} />
              <Field label={T("preferences.outputFormat")} value={profile.preferences.output_format} onChange={(v) => setP("output_format", v)} placeholder={lang === "ko" ? "예: 헤더와 코드 블록 포함" : "e.g. Structured with headers"} />
              <Field label={T("preferences.designTaste")} value={profile.preferences.design_taste} onChange={(v) => setP("design_taste", v)} placeholder={lang === "ko" ? "예: 다크 미니멀" : "e.g. Dark minimal"} />
              <Field label={T("preferences.primaryTools")} value={arrToCsv(profile.preferences.tools_primary)} onChange={(v) => setP("tools_primary", csvToArr(v))} placeholder={lang === "ko" ? "예: VS Code, Git" : "e.g. VS Code, Git"} />
            </div>
          </div>

          {/* CONTEXT TAGS */}
          <div style={CARD}>
            <h2 style={h2Style}>{T("context.title")}</h2>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px" }}>
              <Field label={T("context.tech")} value={arrToCsv(profile.context_tags.tech)} onChange={(v) => setCT("tech", csvToArr(v))} placeholder={lang === "ko" ? "예: Python, React, Docker" : "e.g. Python, React, Docker"} />
              <Field label={T("context.interests")} value={arrToCsv(profile.context_tags.interests)} onChange={(v) => setCT("interests", csvToArr(v))} placeholder={lang === "ko" ? "예: AI, 디자인, 생산성" : "e.g. AI, Design, Productivity"} />
              <div style={{ gridColumn: "1 / -1" }}><Field label={T("context.currentFocus")} value={profile.context_tags.current_focus} onChange={(v) => setCT("current_focus", v)} placeholder={lang === "ko" ? "현재 집중하고 있는 작업" : "What you're currently focused on"} /></div>
            </div>
          </div>

          {/* ACTION BAR */}
          <div style={{ ...CARD, display: "flex", gap: "12px", flexWrap: "wrap", justifyContent: "center" }}>
            <ActBtn label={saveCheck ? (lang === "ko" ? "✓ 저장됨" : "✓ Saved") : T("action.save")} icon="💾" color={ACCENT} onClick={save} />
            <ActBtn label={T("action.export")} icon="📤" color="#a78bfa" onClick={exportSelf} />
            <ActBtn label={T("action.import")} icon="📥" color="#34d399" onClick={importSelf} />
            <ActBtn label={T("action.reset")} icon="🗑️" color="#f87171" onClick={resetAll} />
          </div>
        </div>
      ) : (
        /* ─── INSIGHTS TAB ─── */
        <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
          {/* TODAY'S ANALYSIS */}
          <div style={CARD}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
              <h2 style={{ ...h2Style, margin: 0 }}>{T("insights.todayActivity")}</h2>
              <button onClick={loadInsights} style={{ ...pillBtn, padding: "6px 14px", fontSize: "12px", background: `${ACCENT}22`, color: ACCENT, border: `1px solid ${ACCENT}44` }}>{T("insights.analyze")}</button>
            </div>
            {analysisData && analysisData.total_records > 0 ? (
              <div>
                <p style={{ fontSize: "13px", color: "rgba(255,255,255,0.4)", marginBottom: "10px" }}>{T("insights.totalTime")}: <strong style={{ color: "#fff" }}>{analysisData.total_minutes} {T("insights.minutes")}</strong></p>
                <div style={{ display: "flex", gap: "8px", flexWrap: "wrap", marginBottom: "12px" }}>
                  {(analysisData.apps || []).slice(0, 8).map((a: any, i: number) => <Tag key={i} label={`${a.name} `} value={a.time} />)}
                </div>
                {analysisData.peak_hours?.length > 0 && <p style={{ fontSize: "12px", color: "rgba(255,255,255,0.4)", marginBottom: "8px" }}>{T("insights.peakHours")}: <strong style={{ color: "#fff" }}>{analysisData.peak_hours.join(", ")}</strong></p>}
                {analysisData.detected_projects?.length > 0 && <p style={{ fontSize: "12px", color: "rgba(255,255,255,0.4)", marginBottom: "8px" }}>{T("insights.detectedProjects")}: <strong style={{ color: "#fff" }}>{analysisData.detected_projects.join(", ")}</strong></p>}
                {analysisData.detected_tech?.length > 0 && <p style={{ fontSize: "12px", color: "rgba(255,255,255,0.4)" }}>{T("insights.detectedTech")}: <strong style={{ color: "#fff" }}>{analysisData.detected_tech.join(", ")}</strong></p>}
              </div>
            ) : (
              <p style={{ fontSize: "13px", color: "rgba(255,255,255,0.3)" }}>{T("insights.enableTracking")}</p>
            )}
          </div>

          {/* SUGGESTIONS */}
          <div style={CARD}>
            <h2 style={h2Style}>{T("suggest.title")}</h2>
            {suggestions.length > 0 ? suggestions.map((s, i) => (
              <div key={i} style={{ background: "rgba(88,230,255,0.05)", borderRadius: "10px", padding: "14px", marginBottom: i < suggestions.length - 1 ? "10px" : "0", border: "1px solid rgba(88,230,255,0.1)" }}>
                <p style={{ fontSize: "13px", color: "#fff", marginBottom: "8px" }}>{lang === "ko" ? s.reason_ko : s.reason_en}</p>
                <div style={{ display: "flex", gap: "8px" }}>
                  <button onClick={() => acceptSuggestion(s, i)} style={{ ...pillBtn, padding: "4px 14px", fontSize: "12px", background: "rgba(52,211,153,0.15)", color: "#34d399", border: "1px solid rgba(52,211,153,0.3)" }}>{T("suggest.accept")}</button>
                  <button onClick={() => dismissSuggestion(i)} style={{ ...pillBtn, padding: "4px 14px", fontSize: "12px", background: "rgba(255,255,255,0.05)", color: "rgba(255,255,255,0.4)" }}>{T("suggest.dismiss")}</button>
                </div>
              </div>
            )) : (
              <p style={{ fontSize: "13px", color: "rgba(255,255,255,0.3)" }}>{T("suggest.noSuggestions")}</p>
            )}
          </div>

          {/* WEEKLY */}
          <div style={CARD}>
            <h2 style={h2Style}>{T("weekly.title")}</h2>
            {weeklySummary ? (
              <div>
                <p style={{ fontSize: "13px", color: "rgba(255,255,255,0.5)", marginBottom: "8px" }}>{T("weekly.totalHours")}: <strong style={{ color: "#fff" }}>{weeklySummary.total_hours} {T("weekly.hours")}</strong></p>
                <p style={{ fontSize: "13px", color: "rgba(255,255,255,0.5)", marginBottom: "8px" }}>{T("weekly.bestDay")}: <strong style={{ color: "#fff" }}>{weeklySummary.most_productive_day}</strong></p>
                {weeklySummary.top_apps?.length > 0 && <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>{weeklySummary.top_apps.slice(0, 5).map((a: any, i: number) => <Tag key={i} label={a.name} value={`${Math.round(a.seconds / 3600)}h`} />)}</div>}
              </div>
            ) : (
              <p style={{ fontSize: "13px", color: "rgba(255,255,255,0.3)" }}>{T("weekly.noData")}</p>
            )}
          </div>

          {/* INJECTION HISTORY */}
          <div style={CARD}>
            <h2 style={h2Style}>{T("injection.title")}</h2>
            {injections.length > 0 ? (
              <div style={{ maxHeight: "300px", overflowY: "auto" }}>
                {injections.map((inj, i) => {
                  const time = inj.timestamp ? new Date(inj.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }) : "";
                  return (
                    <div key={i} style={{ display: "flex", gap: "12px", alignItems: "flex-start", padding: "8px 0", borderBottom: i < injections.length - 1 ? "1px solid rgba(255,255,255,0.05)" : "none" }}>
                      <span style={{ fontSize: "12px", color: "rgba(255,255,255,0.3)", minWidth: "50px" }}>{time}</span>
                      <span style={{ fontSize: "12px", color: ACCENT, minWidth: "70px", textTransform: "capitalize" }}>{inj.platform}</span>
                      <span style={{ fontSize: "12px", color: "rgba(255,255,255,0.5)", minWidth: "60px" }}>{inj.profile}</span>
                      <span style={{ fontSize: "11px", color: "rgba(255,255,255,0.25)", minWidth: "50px" }}>{inj.rule}</span>
                      <span style={{ fontSize: "11px", color: "rgba(255,255,255,0.3)", flex: 1, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{inj.context?.substring(0, 80)}</span>
                    </div>
                  );
                })}
              </div>
            ) : (
              <p style={{ fontSize: "13px", color: "rgba(255,255,255,0.3)" }}>{T("injection.noData")}</p>
            )}
          </div>

          {/* PURGE DATA */}
          <div style={{ ...CARD, display: "flex", justifyContent: "center" }}>
            <button onClick={purgeActivity} style={{ ...pillBtn, background: "rgba(248,113,113,0.1)", color: "#f87171", border: "1px solid rgba(248,113,113,0.2)" }}>{T("action.purgeActivity")}</button>
          </div>
        </div>
      )}

      <input ref={fileRef} type="file" accept=".enc,.self,.self.enc" style={{ display: "none" }} onChange={handleImport} />
    </div>
  );
}

// ─── Sub-Components ─────────────────────────────────────────────
const h2Style: React.CSSProperties = { fontSize: "18px", fontWeight: 600, color: "#58E6FF", marginBottom: "16px" };
const pillBtn: React.CSSProperties = { background: "rgba(255,255,255,0.1)", border: "1px solid rgba(255,255,255,0.15)", color: "#fff", borderRadius: "8px", padding: "8px 16px", fontSize: "13px", fontWeight: 600, cursor: "pointer" };
const smBtn: React.CSSProperties = { background: "rgba(255,255,255,0.08)", border: "1px solid rgba(255,255,255,0.12)", color: "#fff", width: "28px", height: "28px", borderRadius: "6px", cursor: "pointer", fontSize: "14px", display: "flex", alignItems: "center", justifyContent: "center" };

function Field({ label, value, onChange, placeholder }: { label: string; value: string; onChange: (v: string) => void; placeholder?: string }) {
  return <div><label style={{ fontSize: "12px", color: "rgba(255,255,255,0.5)", marginBottom: "4px", display: "block", textTransform: "uppercase", letterSpacing: "0.05em" }}>{label}</label><input value={value} onChange={(e) => onChange(e.target.value)} placeholder={placeholder} /></div>;
}

function Tag({ label, value }: { label: string; value: string }) {
  return <span style={{ background: "rgba(88,230,255,0.08)", border: "1px solid rgba(88,230,255,0.15)", borderRadius: "8px", padding: "4px 10px", fontSize: "12px", color: "#fff" }}>{label}<strong style={{ color: "#58E6FF" }}>{value}</strong></span>;
}

function TabBtn({ label, active, onClick }: { label: string; active: boolean; onClick: () => void }) {
  return <button onClick={onClick} style={{ background: active ? "rgba(88,230,255,0.15)" : "rgba(255,255,255,0.05)", border: active ? "1px solid rgba(88,230,255,0.3)" : "1px solid rgba(255,255,255,0.08)", color: active ? "#58E6FF" : "rgba(255,255,255,0.5)", borderRadius: "8px", padding: "8px 16px", fontSize: "13px", fontWeight: 600, cursor: "pointer", transition: "all 0.2s" }}>{label}</button>;
}

function ActBtn({ label, icon, color, onClick }: { label: string; icon: string; color: string; onClick: () => void }) {
  return (
    <button onClick={onClick} style={{ background: `${color}22`, border: `1px solid ${color}44`, color, borderRadius: "10px", padding: "10px 20px", fontSize: "14px", fontWeight: 600, cursor: "pointer", display: "flex", alignItems: "center", gap: "8px", transition: "all 0.2s" }}
      onMouseEnter={(e) => { e.currentTarget.style.background = `${color}33`; e.currentTarget.style.transform = "translateY(-1px)"; }}
      onMouseLeave={(e) => { e.currentTarget.style.background = `${color}22`; e.currentTarget.style.transform = "translateY(0)"; }}>
      <span>{icon}</span>{label}
    </button>
  );
}
