const { contextBridge, ipcRenderer } = require("electron");

contextBridge.exposeInMainWorld("electron", {
  getPlatform: () => ipcRenderer.invoke("get-platform"),
  getMonthDays: (year, month) => ipcRenderer.invoke("get-month-days", year, month),
  getSummaryStats: () => ipcRenderer.invoke("get-summary-stats"),
});