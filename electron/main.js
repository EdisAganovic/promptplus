const { app, BrowserWindow, Tray, Menu, globalShortcut, ipcMain, shell, dialog } = require('electron');
const path = require('node:path');
const fs = require('node:fs');
const { spawn } = require('node:child_process');

const SHORTCUT = 'CommandOrControl+Alt+P';
let backend;
let backendReady;
let mainWindow;
let searchWindow;
let tray;
let quitting = false;
const iconPath = () => app.isPackaged
  ? path.join(process.resourcesPath, 'icon.ico')
  : path.join(app.getAppPath(), 'icon.ico');

// Contract: Python prints {event:"ready",port,token}; Electron fetches
// /api/prompts with X-PromptPlus-Token; the picker receives keyword/content;
// selection sends only keyword over backend stdin as a paste command.
function startBackend() {
  const executable = app.isPackaged
    ? path.join(process.resourcesPath, 'backend', 'PromptPlusBackend.exe')
    : (process.env.PROMPTPLUS_PYTHON || path.join(app.getAppPath(), '.venv', 'Scripts', 'python.exe'));
  const args = app.isPackaged ? [] : [path.join(app.getAppPath(), 'backend.py')];
  if (!fs.existsSync(executable)) {
    throw new Error(`Python backend not found: ${executable}`);
  }
  backend = spawn(executable, args, {
    cwd: app.isPackaged ? path.dirname(executable) : app.getAppPath(),
    env: {
      ...process.env,
      PROMPTPLUS_DESKTOP_EXE: process.env.PORTABLE_EXECUTABLE_FILE || process.execPath,
      ...(app.isPackaged ? {} : { PROMPTPLUS_DESKTOP_PROJECT: app.getAppPath() }),
    },
    stdio: ['pipe', 'pipe', 'pipe'],
    windowsHide: true,
  });
  backend.stderr.on('data', chunk => console.error(`[backend] ${chunk.toString().trim()}`));
  let pending = '';
  return new Promise((resolve, reject) => {
    const timer = setTimeout(() => reject(new Error('Python backend did not start in 30 seconds')), 30000);
    backend.once('error', error => { clearTimeout(timer); reject(error); });
    backend.once('exit', code => {
      clearTimeout(timer);
      if (!backendReady) reject(new Error(`Python backend exited with code ${code}`));
      else if (!quitting) dialog.showErrorBox('PromptPlus', 'The Python backend stopped unexpectedly.');
    });
    backend.stdout.on('data', chunk => {
      pending += chunk.toString();
      let newline;
      while ((newline = pending.indexOf('\n')) !== -1) {
        const line = pending.slice(0, newline).trim();
        pending = pending.slice(newline + 1);
        try {
          const message = JSON.parse(line);
          if (message.event === 'ready' && Number.isInteger(message.port) && typeof message.token === 'string') {
            backendReady = message;
            clearTimeout(timer);
            resolve(message);
          }
        } catch { if (line) console.log(`[backend] ${line}`); }
      }
    });
  });
}

function createMainWindow(port) {
  mainWindow = new BrowserWindow({
    width: 1200, height: 870, minWidth: 800, minHeight: 600,
    title: 'PromptPlus', icon: iconPath(),
    show: false, backgroundColor: '#1a1b27',
    webPreferences: { nodeIntegration: false, contextIsolation: true, sandbox: true },
  });
  const allowedOrigin = `http://127.0.0.1:${port}`;
  mainWindow.webContents.on('will-navigate', (event, url) => {
    if (new URL(url).origin !== allowedOrigin) { event.preventDefault(); shell.openExternal(url); }
  });
  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    if (url.startsWith('https://')) shell.openExternal(url);
    return { action: 'deny' };
  });
  mainWindow.on('close', event => {
    if (!quitting) { event.preventDefault(); mainWindow.hide(); }
  });
  mainWindow.loadURL(allowedOrigin);
  if (!process.argv.includes('--minimize')) mainWindow.once('ready-to-show', () => mainWindow.show());
}

function createSearchWindow() {
  searchWindow = new BrowserWindow({
    width: 520, height: 400, resizable: false, frame: false,
    alwaysOnTop: true, skipTaskbar: true, show: false,
    backgroundColor: '#1a1b27',
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      nodeIntegration: false, contextIsolation: true, sandbox: true,
    },
  });
  searchWindow.loadFile(path.join(__dirname, 'quick-search.html'));
  searchWindow.webContents.on('did-finish-load', () => {
    if (searchWindow.isVisible()) searchWindow.webContents.send('reset-search');
  });
  searchWindow.on('blur', () => searchWindow.hide());
}

function showSearch() {
  if (!searchWindow) return;
  searchWindow.center();
  searchWindow.show();
  searchWindow.focus();
  searchWindow.webContents.send('reset-search');
}

function createTray() {
  tray = new Tray(iconPath());
  tray.setToolTip('PromptPlus');
  tray.setContextMenu(Menu.buildFromTemplate([
    { label: 'Open PromptPlus', click: () => mainWindow.show() },
    { label: 'Quick Search', click: showSearch },
    { type: 'separator' },
    { label: 'Quit', click: () => { quitting = true; app.quit(); } },
  ]));
  tray.on('double-click', () => mainWindow.show());
}

ipcMain.handle('list-prompts', async event => {
  if (event.sender !== searchWindow?.webContents || !backendReady) return [];
  const response = await fetch(`http://127.0.0.1:${backendReady.port}/api/prompts`, {
    headers: { 'X-PromptPlus-Token': backendReady.token },
  });
  if (!response.ok) throw new Error(`Prompt list failed: ${response.status}`);
  return response.json();
});
ipcMain.handle('paste-prompt', (event, keyword) => {
  if (event.sender !== searchWindow?.webContents || typeof keyword !== 'string') return false;
  searchWindow.hide();
  // Give the previous application time to regain focus before pasting.
  setTimeout(() => backend?.stdin.writable && backend.stdin.write(JSON.stringify({ type: 'paste', keyword }) + '\n'), 250);
  return true;
});
ipcMain.on('close-search', event => {
  if (event.sender === searchWindow?.webContents) searchWindow.hide();
});

if (!app.requestSingleInstanceLock()) {
  app.quit();
} else {
  app.on('second-instance', () => { if (mainWindow) { mainWindow.show(); mainWindow.focus(); } });
  app.whenReady().then(async () => {
    try {
      // Keep the tray context menu, but remove Electron's default window menu.
      Menu.setApplicationMenu(null);
      const ready = await startBackend();
      createMainWindow(ready.port);
      createSearchWindow();
      createTray();
      if (!globalShortcut.register(SHORTCUT, showSearch)) {
        console.warn(`${SHORTCUT} is already in use; Quick Search remains available from the tray.`);
      }
    } catch (error) {
      dialog.showErrorBox('PromptPlus startup failed', String(error));
      quitting = true;
      app.quit();
    }
  });
  app.on('before-quit', () => {
    quitting = true;
    globalShortcut.unregisterAll();
    if (backend?.stdin.writable) backend.stdin.write('{"type":"shutdown"}\n');
    setTimeout(() => { if (backend && !backend.killed) backend.kill(); }, 2000).unref();
  });
}
