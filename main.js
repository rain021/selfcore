const { app, BrowserWindow, Tray, Menu, globalShortcut, Notification, nativeImage, dialog, clipboard, ipcMain } = require("electron");
const path = require("path");
const http = require("http");

let mainWindow = null;
let tray = null;
let currentLang = "en";
let activeProfile = "default";
let windowVisible = true;

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
    http.get(`http://127.0.0.1:8100${urlPath}`, (res) => {
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
      hostname: "127.0.0.1", port: 8100, path: urlPath,
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
      await refreshLangAndProfile();
      const clipText = clipboard.readText();
      if (!clipText || clipText.trim().length === 0) return;

      const result = await fetchJSON(`/api/context?query=${encodeURIComponent(clipText)}`);
      const context = result?.context;
      if (context) {
        const combined = context + "\n\n---\n\n" + clipText;
        clipboard.writeText(combined);
        new Notification({
          title: "SelfCore",
          body: "✓ " + tr("notify.ready"),
          silent: true,
        }).show();
      } else {
        new Notification({
          title: "SelfCore",
          body: tr("notify.backendDown"),
          silent: true,
        }).show();
      }
    } catch (err) {
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
  await refreshLangAndProfile();
  createWindow();
  await createTray();
  registerShortcut();
});

app.on("will-quit", () => { globalShortcut.unregisterAll(); });
app.on("window-all-closed", () => { app.quit(); });
