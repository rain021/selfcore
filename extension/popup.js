const TR = {
  subtitle:    { en: "AI Context Bridge", ko: "AI 맥락 브릿지" },
  connection:  { en: "CONNECTION", ko: "연결 상태" },
  connected:   { en: "Connected", ko: "연결됨" },
  disconnected:{ en: "Not running", ko: "실행 안 됨" },
  profile:     { en: "ACTIVE PROFILE", ko: "활성 프로필" },
  autoInject:  { en: "Auto-inject on send", ko: "전송 시 자동 주입" },
  openEditor:  { en: "Open SelfCore Editor", ko: "SelfCore 편집기 열기" },
};

let lang = "en";

function t(key) {
  return (TR[key] && TR[key][lang]) || TR[key]?.en || key;
}

function updateLabels() {
  document.getElementById("subtitle").textContent = t("subtitle");
  document.getElementById("lbl-status").textContent = t("connection");
  document.getElementById("lbl-profile").textContent = t("profile");
  document.getElementById("lbl-auto").textContent = t("autoInject");
  document.getElementById("open-editor").textContent = t("openEditor");
}

async function init() {
  // Check health
  chrome.runtime.sendMessage({ type: "checkHealth" }, (res) => {
    const el = document.getElementById("conn-status");
    if (res && res.ok) {
      el.innerHTML = `<span class="dot dot-green"></span>${t("connected")}`;
    } else {
      el.innerHTML = `<span class="dot dot-red"></span>${t("disconnected")}`;
    }
  });

  // Get settings + language
  chrome.runtime.sendMessage({ type: "getSettings" }, (settings) => {
    if (settings && settings.ui_lang) {
      lang = settings.ui_lang;
      updateLabels();
      // Re-check health with correct language
      chrome.runtime.sendMessage({ type: "checkHealth" }, (res) => {
        const el = document.getElementById("conn-status");
        if (res && res.ok) {
          el.innerHTML = `<span class="dot dot-green"></span>${t("connected")}`;
        } else {
          el.innerHTML = `<span class="dot dot-red"></span>${t("disconnected")}`;
        }
      });
    }
  });

  // Get profiles
  chrome.runtime.sendMessage({ type: "getProfiles" }, (data) => {
    if (data && data.active) {
      document.getElementById("profile-name").textContent = data.active;
    }
  });

  // Auto-inject toggle
  chrome.storage.local.get(["autoInject"], (r) => {
    const toggle = document.getElementById("auto-toggle");
    if (r.autoInject) toggle.classList.add("active");

    toggle.addEventListener("click", () => {
      const isActive = toggle.classList.toggle("active");
      chrome.storage.local.set({ autoInject: isActive });
    });
  });

  // Open editor link
  document.getElementById("open-editor").addEventListener("click", (e) => {
    e.preventDefault();
    chrome.tabs.create({ url: "http://localhost:3000" });
  });

  updateLabels();
}

document.addEventListener("DOMContentLoaded", init);
