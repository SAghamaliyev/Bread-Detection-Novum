const { app, BrowserWindow, ipcMain, session } = require("electron");
const { spawn } = require("child_process");
const fs = require("fs");
const path = require("path");
const crypto = require("crypto");
let forceQuit = false;

// Activation Configuration
// Activation code is "UFAZ2026"
const ACTIVATION_HASH = "c2c36d6bcdc0febf0638c019a91a3a5705963cea4cd14734bafbe1609357bacd"; 
const ACTIVATION_FILE = path.join(app.getPath("userData"), "activation.json");
// Импортируем функции из твоей БД
const { getMonthDays, getSummaryStats } = require("../src/db.js");

const isDev = process.env.NODE_ENV === "development" || !app.isPackaged;

function createWindow() {
  const win = new BrowserWindow({
    width: 1280,
    height: 800,
    webPreferences: {
      preload: path.join(__dirname, "preload.js"),
      contextIsolation: true,
      nodeIntegration: false,
    },
  });

  // Настройка разрешений
  session.defaultSession.setPermissionRequestHandler(
    (_webContents, permission, callback) => {
      const allowed = [
        "media",
        "mediaKeySystem",
        "geolocation",
        "notifications",
      ];
      if (allowed.includes(permission) || permission === "media") {
        return callback(true);
      }
      callback(false);
    },
  );

  session.defaultSession.setPermissionCheckHandler(
    (_webContents, permission) => {
      return ["media", "mediaKeySystem"].includes(permission);
    },
  );

  if (isDev) {
    win.loadURL("http://localhost:5173");
    win.webContents.openDevTools();
  } else {
    win.loadFile(path.join(__dirname, "../dist/index.html"));
  }

  win.on("close", (e) => {
    if (!forceQuit) {
      e.preventDefault();
      win.webContents.send("request-exit");
    }
  });
}

// --- РЕГИСТРАЦИЯ ОБРАБОТЧИКОВ IPC ---

// Activation Handlers
ipcMain.handle("check-activation", () => {
  try {
    if (fs.existsSync(ACTIVATION_FILE)) {
      const data = JSON.parse(fs.readFileSync(ACTIVATION_FILE, "utf-8"));
      return data.activated === true;
    }
  } catch (err) {
    console.error("Error checking activation:", err);
  }
  return false;
});

ipcMain.handle("activate-app", (_, code) => {
  const hash = crypto.createHash("sha256").update(code).digest("hex");
  if (hash === ACTIVATION_HASH) {
    try {
      fs.writeFileSync(ACTIVATION_FILE, JSON.stringify({ activated: true }));
      return { success: true };
    } catch (err) {
      console.error("Error saving activation:", err);
      return { success: false, error: "Storage error" };
    }
  }
  return { success: false, error: "Invalid activation code" };
});

// Обработчик платформы (уже был у тебя)
ipcMain.handle("get-platform", () => process.platform);

// Твои новые обработчики для БД
ipcMain.handle("get-month-days", async (_, year, month) => {
  return await getMonthDays(year, month);
});

ipcMain.handle("get-summary-stats", async () => {
  return await getSummaryStats();
});

ipcMain.handle("run-detection", async () => {
  return new Promise((resolve, reject) => {
    const scriptPath = path.join(__dirname, "../../final_detect.py");
    const pythonProcess = spawn("python", [scriptPath], {
      cwd: path.join(__dirname, "../../"),
    });

    pythonProcess.stdout.on("data", (data) => {
      console.log(`[Python] ${data}`);
    });

    pythonProcess.stderr.on("data", (data) => {
      console.error(`[Python Error] ${data}`);
    });

    pythonProcess.on("close", (code) => {
      console.log(`[Python] Process exited with code ${code}`);
      resolve(code);
    });

    pythonProcess.on("error", (err) => {
      console.error(`[Python] Failed to start: ${err}`);
      reject(err);
    });
  });
});

ipcMain.on("confirm-exit", () => {
  forceQuit = true;
  app.quit();
});

// ------------------------------------

app.whenReady().then(createWindow);

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") app.quit();
});

app.on("activate", () => {
  if (BrowserWindow.getAllWindows().length === 0) createWindow();
});
