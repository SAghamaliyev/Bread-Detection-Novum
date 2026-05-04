const { contextBridge, ipcRenderer } = require("electron");

contextBridge.exposeInMainWorld("electron", {
  getPlatform: () => ipcRenderer.invoke("get-platform"),
  getMonthDays: (year, month) =>
    ipcRenderer.invoke("get-month-days", year, month),
  getSummaryStats: () => ipcRenderer.invoke("get-summary-stats"),
  onExitRequested: (callback) => ipcRenderer.on("request-exit", callback),
  runDetection: () => ipcRenderer.invoke("run-detection"),
  confirmExit: () => ipcRenderer.send("confirm-exit"),
});
