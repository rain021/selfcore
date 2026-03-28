const API = "http://127.0.0.1:8100";

// Check backend on install
chrome.runtime.onInstalled.addListener(async () => {
  try {
    const res = await fetch(`${API}/api/health`);
    if (!res.ok) throw new Error();
    console.log("[SelfCore] Backend connected");
  } catch {
    chrome.notifications.create("selfcore-start", {
      type: "basic",
      title: "SelfCore",
      message: "Start SelfCore desktop app first / SelfCore 데스크톱 앱을 먼저 실행하세요",
      iconUrl: "icon128.png",
    });
  }
  // Default settings
  chrome.storage.local.get(["autoInject"], (r) => {
    if (r.autoInject === undefined) {
      chrome.storage.local.set({ autoInject: false });
    }
  });
});

// Listen for messages from content script
chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg.type === "fetchContext") {
    const url = `${API}/api/context?query=${encodeURIComponent(msg.query)}`;
    fetch(url)
      .then((r) => r.json())
      .then((data) => sendResponse({ context: data.context || "" }))
      .catch(() => sendResponse({ context: "" }));
    return true; // async
  }
  if (msg.type === "logInjection") {
    const body = JSON.stringify({
      platform: msg.platform,
      context_injected: msg.context,
      profile_used: msg.profile,
    });
    fetch(`${API}/api/injection/log`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body,
    }).catch(() => {});
    return false;
  }
  if (msg.type === "getSettings") {
    fetch(`${API}/api/settings`)
      .then((r) => r.json())
      .then((d) => sendResponse(d))
      .catch(() => sendResponse(null));
    return true;
  }
  if (msg.type === "getProfiles") {
    fetch(`${API}/api/profiles`)
      .then((r) => r.json())
      .then((d) => sendResponse(d))
      .catch(() => sendResponse(null));
    return true;
  }
  if (msg.type === "checkHealth") {
    fetch(`${API}/api/health`)
      .then((r) => r.json())
      .then((d) => sendResponse({ ok: true, data: d }))
      .catch(() => sendResponse({ ok: false }));
    return true;
  }
});
