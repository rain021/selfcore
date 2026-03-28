const { app, BrowserWindow, Tray, Menu, globalShortcut, Notification, nativeImage, dialog, clipboard, ipcMain } = require("electron");
const path = require("path");
const http = require("http");
const fs = require("fs");

// ─── Crash diagnostics ──────────────────────
const LOG_PATH = path.join(__dirname, "crash.log");
function crashLog(msg) {
  const line = `[${new Date().toISOString()}] ${msg}\n`;
  try { fs.appendFileSync(LOG_PATH, line); } catch {}
  console.log(msg);
}
process.on("uncaughtException", (err) => {
  crashLog(`UNCAUGHT EXCEPTION: ${err.stack || err}`);
});
process.on("unhandledRejection", (reason) => {
  crashLog(`UNHANDLED REJECTION: ${reason?.stack || reason}`);
});

// ─── Single instance lock ────────────────────
const gotLock = app.requestSingleInstanceLock();
if (!gotLock) {
  crashLog("Another instance is running — quitting this one.");
  app.quit();
}

let mainWindow = null;
let tray = null;
let currentLang = "en";
let activeProfile = "default";
let windowVisible = true;
let backendPort = 8100;
let isQuitting = false;

const FRONTEND_URL = "http://localhost:3000";
const MAX_LOAD_RETRIES = 30;  // 30 x 2s = 60s max wait
let loadRetries = 0;
let lastLoadFailed = false;

const TR = {
  "tray.editProfile":   { en: "Edit Profile", ko: "\ud504\ub85c\ud544 \ud3b8\uc9d1 \uc5f4\uae30" },
  "tray.quit":          { en: "Quit", ko: "\uc885\ub8cc" },
  "tray.active":        { en: "Active profile", ko: "\ud65c\uc131 \ud504\ub85c\ud544" },
  "quit.message":       { en: "Are you sure you want to quit SelfCore?", ko: "SelfCore\ub97c \uc885\ub8cc\ud558\uc2dc\uaca0\uc2b5\ub2c8\uae4c?" },
  "quit.yes":           { en: "Quit", ko: "\uc885\ub8cc" },
  "quit.no":            { en: "Cancel", ko: "\ucde8\uc18c" },
  "notify.ready":       { en: "SelfCore context ready. Paste into your AI.", ko: "SelfCore \ub9e5\ub77d\uc774 \uc900\ube44\ub418\uc5c8\uc2b5\ub2c8\ub2e4. AI\uc5d0 \ubd99\uc5ec\ub123\uc73c\uc138\uc694." },
  "notify.backendDown": { en: "Cannot connect to SelfCore backend", ko: "SelfCore \ubc31\uc5d4\ub4dc\uc5d0 \uc5f0\uacb0\ud560 \uc218 \uc5c6\uc2b5\ub2c8\ub2e4" },
};

function tr(key) {
  const entry = TR[key];
  if (!entry) return key;
  return entry[currentLang] || entry["en"];
}

function fetchJSON(urlPath) {
  return new Promise((resolve) => {
    http.get(`http://127.0.0.1:${backendPort}${urlPath}`, (res) => {
      let data = "";
      res.on("data", (chunk) => (data += chunk));
      res.on("end", () => {
        try { resolve(JSON.parse(data)); } catch { resolve(null); }
      });
    }).on("error", () => resolve(null));
  });
}

function postJSON(urlPath, data) {
  return new Promise((resolve) => {
    const body = JSON.stringify(data);
    const req = http.request({
      hostname: "127.0.0.1", port: backendPort, path: urlPath,
      method: "POST", headers: { "Content-Type": "application/json", "Content-Length": Buffer.byteLength(body) },
    }, (res) => {
      let d = "";
      res.on("data", (chunk) => (d += chunk));
      res.on("end", () => { try { resolve(JSON.parse(d)); } catch { resolve(null); } });
    });
    req.on("error", () => resolve(null));
    req.write(body);
    req.end();
  });
}

// Discover which port the Python backend is running on (8100-8102)
function discoverBackendPort() {
  return new Promise((resolve) => {
    const ports = [8100, 8101, 8102];
    let found = false;
    let pending = ports.length;
    for (const port of ports) {
      const req = http.get(`http://127.0.0.1:${port}/api/health`, (res) => {
        let data = "";
        res.on("data", (chunk) => (data += chunk));
        res.on("end", () => {
          if (!found) {
            try {
              const json = JSON.parse(data);
              if (json.status === "ok") {
                found = true;
                backendPort = port;
                console.log(`[SelfCore] Backend discovered on port ${port}`);
                resolve(port);
              }
            } catch {}
          }
          if (--pending === 0 && !found) resolve(null);
        });
      });
      req.on("error", () => { if (--pending === 0 && !found) resolve(null); });
      req.setTimeout(1000, () => { req.destroy(); });
    }
  });
}

async function refreshLangAndProfile() {
  const settings = await fetchJSON("/api/settings");
  if (settings) {
    currentLang = settings.ui_lang || "en";
    activeProfile = settings.active_profile || "default";
  }
}

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 900,
    height: 700,
    frame: false,
    center: true,
    resizable: true,
    show: false,  // Don't show until page is ready
    backgroundColor: "#0f172a",
    webPreferences: {
      preload: path.join(__dirname, "preload.js"),
      contextIsolation: true,
      nodeIntegration: false,
    },
    icon: path.join(__dirname, "assets", "icon.png"),
  });

  crashLog("createWindow: loading " + FRONTEND_URL);
  loadRetries = 0;
  lastLoadFailed = false;
  mainWindow.loadURL(FRONTEND_URL);

  // Show window only after page loads successfully (not the error page)
  mainWindow.webContents.on("did-finish-load", () => {
    if (lastLoadFailed) {
      // This is the error page loading after did-fail-load — ignore
      lastLoadFailed = false;
      return;
    }
    crashLog("createWindow: page loaded OK");
    loadRetries = 0;
    if (mainWindow && !mainWindow.isDestroyed()) {
      mainWindow.show();
    }
  });

  // Retry on load failure (Next.js not ready yet)
  mainWindow.webContents.on("did-fail-load", (event, errorCode, errorDescription, validatedURL) => {
    lastLoadFailed = true;
    loadRetries++;
    crashLog(`createWindow: LOAD FAILED code=${errorCode} desc=${errorDescription} (retry ${loadRetries}/${MAX_LOAD_RETRIES})`);
    if (loadRetries < MAX_LOAD_RETRIES && !isQuitting) {
      setTimeout(() => {
        if (mainWindow && !mainWindow.isDestroyed()) {
          crashLog(`createWindow: retrying load... (attempt ${loadRetries})`);
          lastLoadFailed = false;
          mainWindow.loadURL(FRONTEND_URL);
        }
      }, 2000);
    }
  });

  // Log renderer crashes
  mainWindow.webContents.on("render-process-gone", (event, details) => {
    crashLog(`createWindow: RENDERER CRASHED reason=${details.reason} exitCode=${details.exitCode}`);
    // Attempt to recover by reloading
    if (details.reason !== "killed" && !isQuitting) {
      setTimeout(() => {
        if (mainWindow && !mainWindow.isDestroyed()) {
          crashLog("createWindow: attempting reload after crash...");
          mainWindow.loadURL(FRONTEND_URL);
        }
      }, 2000);
    }
  });

  mainWindow.on("closed", () => {
    crashLog("createWindow: window closed");
    mainWindow = null;
  });

  mainWindow.on("close", (e) => {
    if (isQuitting) return;  // Let it close during app quit
    e.preventDefault();
    refreshLangAndProfile().then(() => {
      if (!mainWindow || mainWindow.isDestroyed()) return;
      dialog.showMessageBox(mainWindow, {
        type: "question",
        buttons: [tr("quit.yes"), tr("quit.no")],
        defaultId: 1,
        title: "SelfCore",
        message: tr("quit.message"),
      }).then((result) => {
        if (result.response === 0) {
          isQuitting = true;
          mainWindow.destroy();
          app.quit();
        }
      });
    }).catch(() => {});
  });

  mainWindow.on("hide", () => { windowVisible = false; });
  mainWindow.on("show", () => { windowVisible = true; });
  mainWindow.on("minimize", () => { windowVisible = false; });
  mainWindow.on("restore", () => { windowVisible = true; });
}

// ─── IPC from renderer ──────────────────────
ipcMain.on("win-minimize", () => {
  if (mainWindow) {
    mainWindow.hide();
    windowVisible = false;
  }
});

ipcMain.on("win-close", () => {
  if (mainWindow) mainWindow.close();
});

// ─── Tray ───────────────────────────────────
async function createTray() {
  const iconPath = path.join(__dirname, "assets", "icon.png");
  let trayIcon;
  try {
    trayIcon = nativeImage.createFromPath(iconPath).resize({ width: 16, height: 16 });
  } catch {
    trayIcon = nativeImage.createEmpty();
  }

  tray = new Tray(trayIcon);
  tray.setToolTip("SelfCore \u2014 Personal AI Identity Engine");
  await updateTrayMenu();

  tray.on("click", () => {
    if (mainWindow) {
      mainWindow.show();
      mainWindow.focus();
      windowVisible = true;
    }
  });
}

async function updateTrayMenu() {
  if (!tray) return;
  await refreshLangAndProfile();

  const profiles = await fetchJSON("/api/profiles");
  const profileList = profiles?.profiles || ["default"];

  const profileSubmenu = profileList.map((p) => ({
    label: p === activeProfile ? `\u25cf ${p}` : `  ${p}`,
    click: async () => {
      await postJSON("/api/profiles/switch", { name: p });
      await updateTrayMenu();
    },
  }));

  const contextMenu = Menu.buildFromTemplate([
    { label: `${tr("tray.active")}: ${activeProfile}`, enabled: false },
    { type: "separator" },
    ...profileSubmenu,
    { type: "separator" },
    {
      label: tr("tray.editProfile"),
      click: () => { if (mainWindow) { mainWindow.show(); mainWindow.focus(); windowVisible = true; } },
    },
    { type: "separator" },
    {
      label: tr("tray.quit"),
      click: () => {
        isQuitting = true;
        mainWindow?.destroy();
        app.quit();
      },
    },
  ]);

  tray.setContextMenu(contextMenu);
}

// ─── Global shortcut ────────────────────────
function registerShortcut() {
  globalShortcut.register("Ctrl+Shift+Space", async () => {
    try {
      console.log("[SelfCore] Step 1: Shortcut triggered");

      // Re-discover port in case backend restarted
      await discoverBackendPort();
      await refreshLangAndProfile();

      // Step 2: Read current clipboard
      const clipText = clipboard.readText();
      console.log(`[SelfCore] Step 2: Clipboard read (${clipText.length} chars)`);

      if (!clipText || clipText.trim().length === 0) {
        console.log("[SelfCore] Step 2: Clipboard empty, injecting context only");
      }

      // Step 3: Fetch context from API
      const query = clipText.trim() || "general";
      const apiUrl = `/api/context?query=${encodeURIComponent(query)}`;
      console.log(`[SelfCore] Step 3: Fetching context from port ${backendPort}: ${apiUrl}`);

      const result = await fetchJSON(apiUrl);
      console.log(`[SelfCore] Step 4: API response: ${result ? "OK" : "FAILED"}`);

      if (!result || !result.context) {
        console.log("[SelfCore] Step 4: No context returned \u2014 backend may be down");
        new Notification({
          title: "SelfCore",
          body: tr("notify.backendDown"),
          silent: true,
        }).show();
        return;
      }

      // Step 5: Write combined text to clipboard
      const context = result.context;
      const combined = clipText.trim()
        ? context + "\n\n---\n\n" + clipText
        : context;
      clipboard.writeText(combined);
      console.log(`[SelfCore] Step 5: Wrote to clipboard (${combined.length} chars)`);

      // Step 6: Verify clipboard was written correctly
      const verify = clipboard.readText();
      if (verify !== combined) {
        console.log(`[SelfCore] Step 6: VERIFY FAILED \u2014 clipboard mismatch (got ${verify.length} chars)`);
        new Notification({
          title: "SelfCore",
          body: "Clipboard write failed \u2014 try again",
          silent: true,
        }).show();
        return;
      }
      console.log(`[SelfCore] Step 6: Clipboard verified OK (${verify.length} chars)`);

      // Step 7: Show success notification only after verified write
      new Notification({
        title: "SelfCore",
        body: "\u2713 " + tr("notify.ready"),
        silent: true,
      }).show();

    } catch (err) {
      console.log(`[SelfCore] Shortcut error: ${err.message}`);
      new Notification({
        title: "SelfCore",
        body: tr("notify.backendDown"),
        silent: true,
      }).show();
    }
  });
}

// ─── Second instance handler ─────────────────
app.on("second-instance", () => {
  crashLog("second-instance: bringing existing window to front");
  if (mainWindow) {
    if (mainWindow.isMinimized()) mainWindow.restore();
    mainWindow.show();
    mainWindow.focus();
    windowVisible = true;
  }
});

// Periodically refresh tray (only when window is visible, to save resources)
setInterval(async () => {
  try {
    if (windowVisible) await updateTrayMenu();
  } catch {}
}, 15000);

app.whenReady().then(async () => {
  try {
    crashLog("app.whenReady: starting...");
    await discoverBackendPort();
    crashLog(`app.whenReady: backend on port ${backendPort}`);
    await refreshLangAndProfile();
    crashLog("app.whenReady: creating window...");
    createWindow();
    crashLog("app.whenReady: creating tray...");
    await createTray();
    crashLog("app.whenReady: registering shortcut...");
    registerShortcut();
    crashLog("app.whenReady: fully initialized");
  } catch (err) {
    crashLog(`app.whenReady: FATAL ERROR: ${err.stack || err}`);
  }
});

app.on("before-quit", () => {
  crashLog("app: before-quit");
  isQuitting = true;
});
app.on("will-quit", () => {
  crashLog("app: will-quit");
  globalShortcut.unregisterAll();
});
app.on("window-all-closed", () => {
  crashLog("app: window-all-closed");
  // On Windows, quit only if intentionally quitting
  if (isQuitting) {
    app.quit();
  }
});
