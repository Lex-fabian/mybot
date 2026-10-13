/**
 * ============================================================================
 *  MyBot — Proceso Principal de Electron (Desktop Native App)
 * ============================================================================
 */

const { app, BrowserWindow, dialog, ipcMain, shell } = require("electron");
const path = require("path");
const fs = require("fs");
const { spawn, spawnSync } = require("child_process");
const http = require("http");

let mainWindow = null;
let pythonProcess = null;
const SERVER_URL = "http://127.0.0.1:58421";

// Abre enlaces externos en el navegador del sistema (nunca dentro de la app).
function abrirEnlaceExterno(url) {
  try {
    const destino = new URL(String(url));
    if (destino.protocol === "http:" || destino.protocol === "https:") {
      shell.openExternal(destino.toString());
      return true;
    }
  } catch (e) {
    console.warn(`[MyBot] URL externa inválida: ${url}`);
  }
  return false;
}

ipcMain.handle("open-external", (_evento, url) => abrirEnlaceExterno(url));

// Termina el backend de Python (y sus procesos hijos) en un solo sitio.
function detenerPython() {
  if (!pythonProcess) return;
  const pid = pythonProcess.pid;
  pythonProcess = null;
  try {
    if (process.platform === "win32") {
      spawn("taskkill", ["/pid", String(pid), "/f", "/t"]);
    } else {
      process.kill(pid, "SIGTERM");
    }
  } catch (e) {
    console.error("Error terminando proceso Python:", e);
  }
}

// 1. Localizar un Python REAL (evita el "stub" de la Microsoft Store, que existe
//    como comando pero falla al ejecutarse con el código 9009).
function candidatosPython() {
  const lista = [];

  if (process.platform === "win32") {
    const base = path.join(process.env.LOCALAPPDATA || "", "Programs", "Python");
    let dirs = [];
    try {
      dirs = fs.readdirSync(base);
    } catch (e) {
      dirs = [];
    }
    dirs
      .filter((d) => /^Python3\d+$/.test(d))
      .sort()
      .reverse()
      .forEach((d) => lista.push(path.join(base, d, "python.exe")));

    lista.push("py", "python", "python3");
  } else {
    lista.push("python3", "python");
  }

  return lista;
}

function pythonEsValido(ejecutable) {
  // El stub de la Microsoft Store vive en WindowsApps y siempre falla.
  if (String(ejecutable).toLowerCase().includes("windowsapps")) {
    return false;
  }
  try {
    const res = spawnSync(ejecutable, ["--version"], {
      encoding: "utf8",
      windowsHide: true,
      timeout: 20000,
    });
    if (res.error) return false;
    const salida = `${res.stdout || ""}${res.stderr || ""}`;
    return res.status === 0 && /python\s*3\.\d+/i.test(salida);
  } catch (e) {
    return false;
  }
}

function detectarPython() {
  for (const candidato of candidatosPython()) {
    if (pythonEsValido(candidato)) {
      return candidato;
    }
  }
  return null;
}

// 1. Iniciar el Backend de Python en segundo plano
function startPythonBackend() {
  const scriptPath = path.join(__dirname, "mybot_backend.py");
  const ejecutable = detectarPython();

  if (!ejecutable) {
    dialog.showErrorBox(
      "Python no encontrado",
      "MyBot necesita Python 3.10 o superior instalado.\n\n" +
      "Descárgalo desde https://www.python.org/downloads/ y marca la opción " +
      "\"Add python.exe to PATH\" durante la instalación.\n\n" +
      "Si ya lo tienes instalado, desactiva el alias de la Microsoft Store en\n" +
      "Configuración > Aplicaciones > Configuración avanzada > Alias de ejecución."
    );
    app.quit();
    return;
  }

  console.log(`[Python] Ejecutable detectado: ${ejecutable}`);

  const proc = spawn(ejecutable, [scriptPath], {
    cwd: __dirname,
    env: process.env,
    stdio: ["ignore", "pipe", "pipe"],
    windowsHide: true,
  });

  let arrancado = false;

  proc.on("error", (err) => {
    console.error(`[Python] Error al lanzar "${ejecutable}":`, err);
  });

  proc.stdout.on("data", (data) => {
    arrancado = true;
    console.log(`[Python stdout]: ${data}`);
  });

  proc.stderr.on("data", (data) => {
    console.error(`[Python stderr]: ${data}`);
  });

  proc.on("close", (code) => {
    console.log(`[Python] Proceso finalizado con código ${code}`);
    if (!arrancado && pythonProcess === proc) {
      console.warn("[Python] El backend terminó prematuramente. Verifica 'pip install -r requirements.txt'.");
    }
  });

  pythonProcess = proc;
}

// 2. Esperar a que el servidor HTTP esté listo (con tiempo límite)
function waitForServer(callback, intentos = 0) {
  const MAX_INTENTOS = 150; // ~30 segundos

  if (intentos >= MAX_INTENTOS) {
    dialog.showErrorBox(
      "No se pudo iniciar MyBot",
      "El servidor interno (Python) no respondió.\n\n" +
      "Comprueba que las dependencias estén instaladas ejecutando:\n" +
      "    pip install -r requirements.txt"
    );
    app.quit();
    return;
  }

  const req = http.get(SERVER_URL, (res) => {
    if (res.statusCode === 200) {
      callback();
    } else {
      setTimeout(() => waitForServer(callback, intentos + 1), 200);
    }
  });

  req.on("error", () => {
    setTimeout(() => waitForServer(callback, intentos + 1), 200);
  });

  req.end();
}

// 3. Crear la ventana nativa de escritorio
function createWindow() {
  const iconPath = process.platform === "win32"
    ? path.join(__dirname, "assets", "icono.ico")
    : path.join(__dirname, "assets", "icono.png");

  mainWindow = new BrowserWindow({
    title: "MyBot — TikTok Live TTS & Donaciones Pro",
    width: 820,
    height: 920,
    minWidth: 720,
    minHeight: 840,
    backgroundColor: "#F2F4F8",
    autoHideMenuBar: true,
    show: false,
    icon: iconPath,
    webPreferences: {
      preload: path.join(__dirname, "preload.js"),
      nodeIntegration: false,
      contextIsolation: true,
    },
  });

  // Cualquier enlace que intente abrir una ventana nueva se envía al navegador del sistema.
  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    abrirEnlaceExterno(url);
    return { action: "deny" };
  });

  mainWindow.loadURL(SERVER_URL);

  mainWindow.once("ready-to-show", () => {
    mainWindow.show();
  });

  mainWindow.on("closed", () => {
    mainWindow = null;
  });
}

// 4. Ciclo de vida de la aplicación
app.whenReady().then(() => {
  // Establecer AppUserModelID para Windows (icono propio en la barra de tareas)
  if (process.platform === "win32") {
    app.setAppUserModelId("mybot.tiktoklive.tts.desktop");
  }

  startPythonBackend();

  waitForServer(() => {
    createWindow();
  });

  app.on("activate", () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

app.on("window-all-closed", () => {
  detenerPython();
  if (process.platform !== "darwin") {
    app.quit();
  }
});

app.on("before-quit", () => {
  detenerPython();
});
