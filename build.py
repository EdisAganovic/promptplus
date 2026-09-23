"""Build the Python backend and package it with the Electron Windows app."""

import json
import shutil
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

# electron-builder copies this directory to resources/backend.
subprocess.run(["npm.cmd", "run", "dist:win"], cwd=ROOT, check=True)
output = ROOT / "dist-electron"
installer = output / f"PromptPlus-Setup-{VERSION}.exe"
if not installer.is_file():
    raise SystemExit("Electron build did not produce an installer.")

# Keep the release directory focused on the one distributable file.
for filename in ("builder-debug.yml", "latest.yml", f"{installer.name}.blockmap"):
    (output / filename).unlink(missing_ok=True)
for dirname in (".icon-ico", "win-unpacked"):
    temporary_dir = output / dirname
    if temporary_dir.is_dir():
        shutil.rmtree(temporary_dir)

print(f"Installer executable: {installer}")
