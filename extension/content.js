(() => {
  "use strict";

  const PLATFORM = detectPlatform();
  if (!PLATFORM) return;

  let badge = null;
  let lang = "en";
  let autoInject = false;

  const TR = {
    injected: { en: "SelfCore context injected", ko: "SelfCore 맥락이 주입되었습니다" },
    noBackend: { en: "SelfCore not running", ko: "SelfCore가 실행되지 않음" },
  };

  function tr(key) {
    return (TR[key] && TR[key][lang]) || TR[key]?.en || key;
  }

  // ─── Platform detection ──────────────────────
  function detectPlatform() {
    const host = location.hostname;
    if (host.includes("claude.ai")) return "claude";
    if (host.includes("chatgpt.com")) return "chatgpt";
    if (host.includes("gemini.google.com")) return "gemini";
    if (host.includes("chat.mistral.ai")) return "mistral";
    return null;
  }

  // ─── Input field selectors per platform ──────
  function getInputField() {
    switch (PLATFORM) {
      case "claude":
        return document.querySelector("div.ProseMirror[contenteditable='true']")
          || document.querySelector("div[contenteditable='true']")
          || document.querySelector("fieldset textarea");
      case "chatgpt":
        return document.querySelector("div#prompt-textarea[contenteditable]")
          || document.querySelector("textarea#prompt-textarea")
          || document.querySelector("div[contenteditable='true'][data-placeholder]");
      case "gemini":
        return document.querySelector("div.ql-editor[contenteditable='true']")
          || document.querySelector("rich-textarea div[contenteditable='true']")
          || document.querySelector("textarea");
      case "mistral":
        return document.querySelector("textarea")
          || document.querySelector("div[contenteditable='true']");
      default:
        return null;
    }
  }

  function getInputText(el) {
    if (!el) return "";
    if (el.tagName === "TEXTAREA" || el.tagName === "INPUT") return el.value;
    return el.innerText || el.textContent || "";
  }

  function setInputText(el, text) {
    if (!el) return;
    if (el.tagName === "TEXTAREA" || el.tagName === "INPUT") {
      el.value = text;
      el.dispatchEvent(new Event("input", { bubbles: true }));
    } else {
      // contenteditable
      el.focus();
      // For React-based editors, we need to set innerHTML and trigger input
      el.textContent = text;
      el.dispatchEvent(new Event("input", { bubbles: true }));
      el.dispatchEvent(new Event("change", { bubbles: true }));
      // Move cursor to end
      const range = document.createRange();
      const sel = window.getSelection();
      range.selectNodeContents(el);
      range.collapse(false);
      sel.removeAllRanges();
      sel.addRange(range);
    }
  }

  // ─── Toast notification ──────────────────────
  function showToast(msg, isError = false) {
    const toast = document.createElement("div");
    toast.className = "selfcore-toast";
    toast.textContent = msg;
    if (isError) toast.style.borderColor = "#f87171";
    document.body.appendChild(toast);
    requestAnimationFrame(() => { toast.style.opacity = "1"; toast.style.transform = "translateY(0)"; });
    setTimeout(() => {
      toast.style.opacity = "0";
      toast.style.transform = "translateY(-8px)";
      setTimeout(() => toast.remove(), 300);
    }, 2500);
  }

  // ─── Context injection ───────────────────────
  async function injectContext() {
    const el = getInputField();
    const text = getInputText(el);
    if (!text.trim()) return;

    chrome.runtime.sendMessage({ type: "fetchContext", query: text }, (res) => {
      if (chrome.runtime.lastError || !res || !res.context) {
        showToast(tr("noBackend"), true);
        return;
      }
      const combined = `[Context from SelfCore: ${res.context}]\n\n${text}`;
      setInputText(el, combined);
      showToast("✓ " + tr("injected"));

      // Log the injection
      chrome.runtime.sendMessage({
        type: "logInjection",
        platform: PLATFORM,
        context: res.context.substring(0, 200),
        profile: "active",
      });
    });
  }

  // ─── Badge ───────────────────────────────────
  function createBadge() {
    if (badge) return;
    badge = document.createElement("div");
    badge.className = "selfcore-badge";
    badge.innerHTML = "🧠 <span>SelfCore</span>";
    badge.addEventListener("click", (e) => {
      e.stopPropagation();
      e.preventDefault();
      injectContext();
    });
    document.body.appendChild(badge);
    positionBadge();
  }

  function positionBadge() {
    if (!badge) return;
    const input = getInputField();
    if (input) {
      const rect = input.getBoundingClientRect();
      badge.style.position = "fixed";
      badge.style.top = Math.max(rect.top - 36, 8) + "px";
      badge.style.right = "20px";
      badge.style.zIndex = "99999";
    }
  }

  // ─── Auto-inject on send ─────────────────────
  function handleKeydown(e) {
    // Ctrl+Shift+Space manual trigger
    if (e.ctrlKey && e.shiftKey && e.code === "Space") {
      e.preventDefault();
      injectContext();
      return;
    }
    // Auto-inject on Enter (send)
    if (autoInject && e.key === "Enter" && !e.shiftKey) {
      const el = getInputField();
      const text = getInputText(el);
      if (text.trim() && !text.includes("[Context from SelfCore:")) {
        e.preventDefault();
        e.stopPropagation();
        chrome.runtime.sendMessage({ type: "fetchContext", query: text }, (res) => {
          if (res && res.context) {
            const combined = `[Context from SelfCore: ${res.context}]\n\n${text}`;
            setInputText(el, combined);
            // Log
            chrome.runtime.sendMessage({ type: "logInjection", platform: PLATFORM, context: res.context.substring(0, 200), profile: "active" });
          }
          // Re-send Enter after brief delay to submit
          setTimeout(() => {
            const input = getInputField();
            if (input) {
              // Find and click the send button instead
              const sendBtn = document.querySelector('button[aria-label="Send"]')
                || document.querySelector('button[data-testid="send-button"]')
                || document.querySelector('button.send-button');
              if (sendBtn) sendBtn.click();
            }
          }, 100);
        });
      }
    }
  }

  // ─── Init ────────────────────────────────────
  function init() {
    // Load settings
    chrome.runtime.sendMessage({ type: "getSettings" }, (settings) => {
      if (settings && settings.ui_lang) lang = settings.ui_lang;
    });
    chrome.storage.local.get(["autoInject"], (r) => {
      autoInject = r.autoInject || false;
    });

    // Listen for setting changes
    chrome.storage.onChanged.addListener((changes) => {
      if (changes.autoInject) autoInject = changes.autoInject.newValue;
    });

    document.addEventListener("keydown", handleKeydown, true);

    // Watch for input field to appear (SPA)
    const observer = new MutationObserver(() => {
      const input = getInputField();
      if (input && !badge) {
        createBadge();
      }
    });
    observer.observe(document.body, { childList: true, subtree: true });

    // Also try immediately
    setTimeout(() => {
      if (getInputField()) createBadge();
    }, 2000);

    // Reposition badge on scroll/resize
    window.addEventListener("scroll", positionBadge, { passive: true });
    window.addEventListener("resize", positionBadge, { passive: true });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
