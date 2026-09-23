# PromptPlus

PromptPlus replaces typed keywords with saved prompts in other applications. Electron provides the desktop dashboard, tray, and Quick Search; a local Python process serves the dashboard and watches for keyword triggers.

## Features

- Create, edit, tag, import, and export prompts in the desktop dashboard.
- Type a keyword such as `:translate` followed by Space to replace it.
- Press `Ctrl+Alt+P` on Windows/Linux (or `Command+Alt+P` on macOS) for Quick Search. Choose a prompt to paste it into the previously focused application.
- Close the dashboard to keep PromptPlus in the system tray. The tray menu can reopen it or quit.
- Prompt changes are saved atomically in `prompts.json`.

The global shortcut is registered through the operating system. If another application owns it, PromptPlus leaves that shortcut alone and Quick Search remains available in the tray menu.

## Development on Windows

Install Python dependencies into `.venv` and install the Electron dependencies:

```powershell
uv venv .venv
uv pip install --python .venv\Scripts\python.exe -r requirements.txt
npm install
npm start
```

The Electron process starts `backend.py` automatically. Set `PROMPTPLUS_PYTHON` to another Python executable if you do not use `.venv`.

## Build a Windows executable

Install PyInstaller in the virtual environment, then run:

```powershell
uv pip install --python .venv\Scripts\python.exe pyinstaller
.venv\Scripts\python.exe build.py
```

The result is one installer file: `dist-electron/PromptPlus-Setup-0.5.0.exe`. Run it to install the Electron application and its bundled Python backend. The older `dist/PromptPlus` folder, if present, is a Qt build and is not the Electron application.

In a packaged build, prompts and settings are stored in `%LOCALAPPDATA%\PromptPlus`. Development uses the project directory. The app requires permission to monitor keyboard input and simulate paste events.
