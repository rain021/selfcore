const { contextBridge, ipcRenderer } = require("electron");

contextBridge.exposeInMainWorld("electronAPI", {
  platform: process.platform,
  minimize: () => ipcRenderer.send("win-minimize"),
  close: () => ipcRenderer.send("win-close"),
});
