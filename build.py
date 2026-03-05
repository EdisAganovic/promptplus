import PyInstaller.__main__
import os
import sys

# Define paths
base_dir = os.path.dirname(os.path.abspath(__file__))
icon_path = os.path.join(base_dir, "icon.ico")
main_path = os.path.join(base_dir, "main.py")

# Ensure icon exists
if not os.path.exists(icon_path):
    print(f"Warning: Icon not found at {icon_path}")
    icon_arg = []
else:
    icon_arg = [f'--icon={icon_path}']

# UPX compression - reduces executable size by 50-70%
# UPX should be installed separately: https://github.com/upx/upx/releases
# Or specify custom path: upx_dir = r"C:\path\to\upx"
upx_dir = "upx"  # Assumes UPX is in PATH

# PyInstaller arguments
args = [
    main_path,
    '--name=PromptPlus',
    '--onedir',
    '--noconsole',
    f'--upx-dir={upx_dir}',
    '--add-data=templates;templates',
    '--add-data=static;static',
    '--add-data=icon.ico;.',
    '--add-data=prompts.json;.',
    # Hidden imports mostly for Uvicorn
    '--hidden-import=uvicorn.logging',
    '--hidden-import=uvicorn.loops',
    '--hidden-import=uvicorn.loops.auto',
    '--hidden-import=uvicorn.protocols',
    '--hidden-import=uvicorn.protocols.http',
    '--hidden-import=uvicorn.protocols.http.auto',
    '--hidden-import=uvicorn.lifespan',
    '--hidden-import=uvicorn.lifespan.on',
    '--hidden-import=app.api',
    # Exclude heavy unused libraries
    '--exclude-module=streamlit',
    '--exclude-module=matplotlib',
    '--exclude-module=numpy',
    '--exclude-module=pandas',
    '--exclude-module=scipy',
    '--exclude-module=tkinter',
    '--exclude-module=notebook',
    '--exclude-module=ipython',
    '--exclude-module=share',
    # Exclude unused Qt modules (BIG SAVINGS)
    '--exclude-module=PyQt6.QtQml',
    '--exclude-module=PyQt6.QtQuick',
    '--exclude-module=PyQt6.QtQuickWidgets',
    '--exclude-module=PyQt6.QtSql',
    '--exclude-module=PyQt6.QtMultimedia',
    '--exclude-module=PyQt6.QtMultimediaWidgets',
    '--exclude-module=PyQt6.QtDesigner',
    '--exclude-module=PyQt6.QtHelp',
    '--exclude-module=PyQt6.QtTest',
    '--exclude-module=PyQt6.QtXml',
    '--exclude-module=PyQt6.QtSvg',
    '--exclude-module=PyQt6.QtBluetooth',
    '--exclude-module=PyQt6.QtDBus',
    '--exclude-module=PyQt6.QtNfc',
    '--exclude-module=PyQt6.QtPositioning',
    '--exclude-module=PyQt6.QtLocation',
    '--exclude-module=PyQt6.QtSensors',
    '--exclude-module=PyQt6.QtSerialPort',
    '--exclude-module=PyQt6.QtWebSockets',
    '--exclude-module=PyQt6.uic',
    '-y',
] + icon_arg

print("Building PromptPlus...")
try:
    PyInstaller.__main__.run(args)
    print("\n---------------------------------------------------------")
    print("Build complete! executable is in the 'dist' folder.")
    print("---------------------------------------------------------")
except Exception as e:
    print(f"Build failed: {e}")
    sys.exit(1)

# Post-build: Copy folders to dist for easier access/updates in onedir mode
import shutil
dist_dir = os.path.join(base_dir, "dist", "PromptPlus")
if os.path.exists(dist_dir):
    print("Copying resources to dist folder...")
    
    # Copy templates
    src_templates = os.path.join(base_dir, "templates")
    dst_templates = os.path.join(dist_dir, "templates")
    if os.path.exists(src_templates):
        if os.path.exists(dst_templates): shutil.rmtree(dst_templates)
        shutil.copytree(src_templates, dst_templates)
        print(f" - Copied templates to {dst_templates}")

    # Copy static
    src_static = os.path.join(base_dir, "static")
    dst_static = os.path.join(dist_dir, "static")
    if os.path.exists(src_static):
        if os.path.exists(dst_static): shutil.rmtree(dst_static)
        shutil.copytree(src_static, dst_static)
        print(f" - Copied static to {dst_static}")
        
    # Copy prompts.json
    src_prompts = os.path.join(base_dir, "prompts.json")
    dst_prompts = os.path.join(dist_dir, "prompts.json")
    if os.path.exists(src_prompts):
        shutil.copy2(src_prompts, dst_prompts)
        print(f" - Copied prompts.json to {dst_prompts}")

    # Copy icon.ico for installer/shortcuts
    src_icon = os.path.join(base_dir, "icon.ico")
    dst_icon = os.path.join(dist_dir, "icon.ico")
    if os.path.exists(src_icon):
        shutil.copy2(src_icon, dst_icon)
        print(f" - Copied icon.ico to {dst_icon}")
    
    print("\n---------------------------------------------------------")
    print(f"Build complete! Open: {dist_dir}")
    print("---------------------------------------------------------")
