const { app, BrowserWindow, Tray, Menu, globalShortcut, Notification, nativeImage, dialog, clipboard, ipcMain } = require("electron");
const path = require("path");
const http = require("http");

let mainWindow = null;
let tray = null;
let currentLang = "en";
let activeProfile = "default";
let windowVisible = true;
let backendPort = 8100; // Discovered dynamically

const TR = {
  "tray.editProfile":   { en: "Edit Profile", ko: "프로필 편집 열기" },
  "tray.quit":          { en: "Quit", ko: "종료" },
  "tray.active":        { en: "Active profile", ko: "활성 프로필" },
  "quit.message":       { en: "Are you sure you want to quit SelfCore?", ko: "SelfCore를 종료하시겠습니까?" },
  "quit.yes":           { en: "Quit", ko: "종료" },
  "quit.no":            { en: "Cancel", ko: "취소" },
  "notify.ready":       { en: "SelfCore context ready. Paste into your AI.", ko: "SelfCore 맥락이 준비되었습니다. AI에 붙여넣으세요." },
  "notify.backendDown": { en: "Cannot connect to SelfCore backend", ko: "SelfCore 백엔드에 연결할 수 없습니다" },
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
    backgroundColor: "#0f172a",
    webPreferences: {
      preload: path.join(__dirname, "preload.js"),
      contextIsolation: true,
      nodeIntegration: false,
    },
    icon: path.join(__dirname, "assets", "icon.png"),
  });

  mainWindow.loadURL("http://localhost:3000");

  mainWindow.on("close", (e) => {
    e.preventDefault();
    refreshLangAndProfile().then(() => {
      dialog.showMessageBox(mainWindow, {
        type: "question",
        buttons: [tr("quit.yes"), tr("quit.no")],
        defaultId: 1,
        title: "SelfCore",
        message: tr("quit.message"),
      }).then((result) => {
        if (result.response === 0) {
          mainWindow.destroy();
          app.quit();
        }
      });
    });
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
  tray.setToolTip("SelfCore — Personal AI Identity Engine");
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
    label: p === activeProfile ? `● ${p}` : `  ${p}`,
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
      click: () => { mainWindow?.destroy(); app.quit(); },
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
        console.log("[SelfCore] Step 4: No context returned — backend may be down");
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
        console.log(`[SelfCore] Step 6: VERIFY FAILED — clipboard mismatch (got ${verify.length} chars)`);
        new Notification({
          title: "SelfCore",
          body: "Clipboard write failed — try again",
          silent: true,
        }).show();
        return;
      }
      console.log(`[SelfCore] Step 6: Clipboard verified OK (${verify.length} chars)`);

      // Step 7: Show success notification only after verified write
      new Notification({
        title: "SelfCore",
        body: "✓ " + tr("notify.ready"),
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

// Periodically refresh tray (only when window is visible, to save resources)
setInterval(async () => {
  try {
    if (windowVisible) await updateTrayMenu();
  } catch {}
}, 15000);

app.whenReady().then(async () => {
  await discoverBackendPort();
  await refreshLangAndProfile();
  createWindow();
  await createTray();
  registerShortcut();
});

app.on("will-quit", () => { globalShortcut.unregisterAll(); });
app.on("window-all-closed", () => { app.quit(); });
