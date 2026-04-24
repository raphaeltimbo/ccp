const { app, BrowserWindow, dialog, ipcMain } = require("electron");
const { spawn } = require("child_process");
const fs = require("fs/promises");
const path = require("path");
const net = require("net");

const DJANGO_PORT = 8418;
let djangoProcess = null;

function findOpenPort(startPort) {
  return new Promise((resolve, reject) => {
    const server = net.createServer();
    server.once("error", () => resolve(findOpenPort(startPort + 1)));
    server.once("listening", () => {
      server.close(() => resolve(startPort));
    });
    server.listen(startPort);
  });
}

function waitForServer(port, retries = 60) {
  return new Promise((resolve, reject) => {
    const attempt = () => {
      const client = net.createConnection({ port }, () => {
        client.end();
        resolve();
      });
      client.on("error", () => {
        if (retries <= 0) return reject(new Error("Django did not start"));
        retries--;
        setTimeout(attempt, 500);
      });
    };
    attempt();
  });
}

function startDjango(port) {
  const args = ["runserver", `${port}`, "--noreload"];

  if (app.isPackaged) {
    // In the packaged build, the Django sidecar ships as a PyInstaller
    // onedir bundle under resources/django/ with a ccp-django(.exe) entry.
    const djangoDir = path.join(process.resourcesPath, "django");
    const exeName = process.platform === "win32" ? "ccp-django.exe" : "ccp-django";
    const djangoExe = path.join(djangoDir, exeName);
    djangoProcess = spawn(djangoExe, args, {
      cwd: djangoDir,
      stdio: ["ignore", "pipe", "pipe"],
    });
  } else {
    const managePy = path.join(__dirname, "manage.py");
    djangoProcess = spawn("uv", ["run", "python", managePy, ...args], {
      cwd: __dirname,
      stdio: ["ignore", "pipe", "pipe"],
    });
  }

  djangoProcess.stdout.on("data", (d) => process.stdout.write(`[django] ${d}`));
  djangoProcess.stderr.on("data", (d) => process.stderr.write(`[django] ${d}`));
  djangoProcess.on("close", (code) => {
    console.log(`Django exited with code ${code}`);
    djangoProcess = null;
  });
}

async function createWindow() {
  const port = await findOpenPort(DJANGO_PORT);
  startDjango(port);
  await waitForServer(port);

  const win = new BrowserWindow({
    width: 1440,
    height: 900,
    minWidth: 900,
    minHeight: 600,
    title: "CCP — Centrifugal Compressor Performance",
    webPreferences: {
      preload: path.join(__dirname, "preload.js"),
      nodeIntegration: false,
      contextIsolation: true,
    },
  });

  win.loadURL(`http://127.0.0.1:${port}/`);
  win.setMenuBarVisibility(false);
}

ipcMain.handle("ccp:saveFile", async (event, { suggestedName, bytes } = {}) => {
  const win = BrowserWindow.fromWebContents(event.sender);
  const result = await dialog.showSaveDialog(win, {
    title: "Save CCP session",
    defaultPath: suggestedName || "session.ccp",
    filters: [{ name: "CCP session", extensions: ["ccp"] }],
  });
  if (result.canceled || !result.filePath) return { canceled: true };
  try {
    await fs.writeFile(result.filePath, Buffer.from(bytes));
    return { path: result.filePath };
  } catch (e) {
    return { error: e.message };
  }
});

ipcMain.handle("ccp:openFile", async (event) => {
  const win = BrowserWindow.fromWebContents(event.sender);
  const result = await dialog.showOpenDialog(win, {
    title: "Open CCP session",
    properties: ["openFile"],
    filters: [{ name: "CCP session", extensions: ["ccp"] }],
  });
  if (result.canceled || !result.filePaths?.length) return { canceled: true };
  try {
    const filePath = result.filePaths[0];
    const buf = await fs.readFile(filePath);
    return { name: path.basename(filePath), bytes: new Uint8Array(buf) };
  } catch (e) {
    return { error: e.message };
  }
});

app.whenReady().then(createWindow);

app.on("window-all-closed", () => {
  if (djangoProcess) djangoProcess.kill();
  app.quit();
});

app.on("before-quit", () => {
  if (djangoProcess) djangoProcess.kill();
});
