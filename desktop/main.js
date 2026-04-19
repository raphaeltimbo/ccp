const { app, BrowserWindow } = require("electron");
const { spawn } = require("child_process");
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
  const managePy = path.join(__dirname, "manage.py");
  djangoProcess = spawn("uv", ["run", "python", managePy, "runserver", `${port}`, "--noreload"], {
    cwd: __dirname,
    stdio: ["ignore", "pipe", "pipe"],
  });
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
      nodeIntegration: false,
      contextIsolation: true,
    },
  });

  win.loadURL(`http://127.0.0.1:${port}/`);
  win.setMenuBarVisibility(false);
}

app.whenReady().then(createWindow);

app.on("window-all-closed", () => {
  if (djangoProcess) djangoProcess.kill();
  app.quit();
});

app.on("before-quit", () => {
  if (djangoProcess) djangoProcess.kill();
});
