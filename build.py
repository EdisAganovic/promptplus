"""Build the Python backend and package it with the Electron Windows app."""

import os
import json
import subprocess
import sys
from pathlib import Path

import PyInstaller.__main__


ROOT = Path(__file__).resolve().parent
VERSION = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))["version"]
if sys.platform != "win32":
    raise SystemExit("This build currently targets Windows only.")

PyInstaller.__main__.run([
    str(ROOT / "backend.py"),
    "--name=PromptPlusBackend",
    "--onedir",
    "--console",
    "--clean",
    "--noupx",
    "--noconfirm",
    f"--distpath={ROOT / 'dist'}",
    f"--workpath={ROOT / 'build' / 'backend'}",
    f"--specpath={ROOT / 'build' / 'backend'}",
    f"--add-data={ROOT / 'templates'};templates",
    f"--add-data={ROOT / 'static'};static",
    f"--add-data={ROOT / 'icon.ico'};.",
    f"--add-data={ROOT / 'prompts.json'};.",
    "--hidden-import=uvicorn.logging",
    "--hidden-import=uvicorn.loops.auto",
    "--hidden-import=uvicorn.protocols.http.auto",
    "--hidden-import=uvicorn.lifespan.on",
    "--exclude-module=PyQt6",
])

backend_output = ROOT / "dist" / "PromptPlusBackend"
if not (backend_output / "PromptPlusBackend.exe").is_file():
    raise SystemExit("Python backend build did not produce an executable.")

# electron-builder copies this exact directory to resources/backend.
desktop_backend = ROOT / "dist" / "backend"
if desktop_backend.exists():
    import shutil

    shutil.rmtree(desktop_backend)
import shutil

shutil.copytree(backend_output, desktop_backend)
subprocess.run(["npm.cmd", "run", "dist:win"], cwd=ROOT, check=True)
print(f"Installer executable: {ROOT / 'dist-electron' / f'PromptPlus-Setup-{VERSION}.exe'}")
