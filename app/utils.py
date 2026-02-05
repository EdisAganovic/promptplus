"""
app/utils.py - Utility Functions
=================================
- PROMPTS_FILE: Path to prompts.json
- get_current_date(): Returns formatted date string
- load_prompts(): Load prompts from JSON file
- save_prompts(prompts): Save prompts to JSON file
- count_tokens(text): Count tokens in text (uses tiktoken or fallback)
- check_existing_instances(script_name): Check if another instance is running
"""
import os
import json
import psutil
from datetime import datetime
import threading
import time

# App Version - Change this in one place
VERSION = "0.2"

# Threading lock for file operations within the same process
file_lock = threading.Lock()

import sys

# Determine base path for static resources (templates, static, icon)
if getattr(sys, 'frozen', False):
    # Running as compiled exe
    app_dir = os.path.dirname(sys.executable)
else:
    app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Determine data path for user-writable files (prompts.json, settings.json)
# When installed to Program Files, we need to use AppData instead
if getattr(sys, 'frozen', False):
    # Use AppData/Local/PromptPlus for user data
    data_dir = os.path.join(os.environ.get('LOCALAPPDATA', os.path.expanduser('~')), 'PromptPlus')
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    
    # On first run, copy prompts.json from install dir to AppData if it doesn't exist
    install_prompts = os.path.join(app_dir, "prompts.json")
    user_prompts = os.path.join(data_dir, "prompts.json")
    if os.path.exists(install_prompts) and not os.path.exists(user_prompts):
        import shutil
        shutil.copy2(install_prompts, user_prompts)
else:
    # Development mode - use project directory
    data_dir = app_dir

PROMPTS_FILE = os.path.join(data_dir, "prompts.json")
SETTINGS_FILE = os.path.join(data_dir, "settings.json")


def get_current_date():
    return datetime.now().strftime("%m.%d.%Y")


def load_prompts():
    with file_lock:
        if os.path.exists(PROMPTS_FILE):
            try:
                with open(PROMPTS_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    prompts = {}
                    for key, value in data.items():
                        if isinstance(value, str):
                            prompts[key] = {
                                'content': value,
                                'last_updated': get_current_date()
                            }
                        elif isinstance(value, dict) and 'content' in value:
                            if 'last_updated' not in value:
                                value['last_updated'] = get_current_date()
                            if 'tags' not in value or not isinstance(value['tags'], list):
                                value['tags'] = []
                            prompts[key] = value
                        else:
                            prompts[key] = {
                                'content': str(value),
                                'last_updated': get_current_date(),
                                'tags': []
                            }
                    return prompts
            except Exception as e:
                print(f"Error loading prompts: {e}")
                return {}
    return {}


def save_prompts(prompts):
    with file_lock:
        # Retry logic for Windows file locking
        max_retries = 3
        for i in range(max_retries):
            try:
                with open(PROMPTS_FILE, 'w', encoding='utf-8') as f:
                    json.dump(prompts, f, ensure_ascii=False, indent=2)
                break
            except PermissionError:
                if i == max_retries - 1:
                    raise
                time.sleep(0.05)


def load_settings():
    """Load app settings from JSON file."""
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    return {"theme": "dark", "start_with_windows": False} # Default settings


def save_settings(settings):
    """Save app settings to JSON file."""
    with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
        json.dump(settings, f, ensure_ascii=False, indent=2)


def count_tokens(text):
    try:
        import tiktoken
        encoding = tiktoken.get_encoding("cl100k_base")
        token_count = len(encoding.encode(text))
        return token_count
    except (ImportError, ValueError):
        import re
        tokens = re.findall(r'\b\w+\b|[^\w\s]', text)
        return max(len(tokens), 1)


def check_existing_instances(script_name="ui.py"):
    """Check if there are already instances of this program running."""
    current_pid = os.getpid()
    script_name_lower = script_name.lower()
    
    for proc in psutil.process_iter(['pid', 'cmdline']):
        try:
            if proc.info['pid'] == current_pid:
                continue
            cmdline = proc.info.get('cmdline')
            if cmdline:
                cmdline_lower = [arg.lower() for arg in cmdline if arg]
                for arg in cmdline_lower:
                    if script_name_lower in arg:
                        print(f"Another instance already running (PID: {proc.info['pid']})")
                        return True, proc.info['pid']
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
    return False, None


def set_start_on_boot(enabled: bool):
    """Enable or disable start on boot via Windows Registry."""
    if sys.platform != "win32":
        return

    import winreg
    
    key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
    app_name = "PromptPlus"
    
    # Use sys.executable for the compiled exe, or the full python command for dev
    if getattr(sys, 'frozen', False):
        app_path = f'"{sys.executable}" --minimize'
    else:
        # For development, we point to the main.py or ui.py
        # But realistically this is for the frozen app
        main_script = os.path.abspath(sys.modules['__main__'].__file__) if '__main__' in sys.modules and hasattr(sys.modules['__main__'], '__file__') else os.path.join(app_dir, "main.py")
        app_path = f'"{sys.executable}" "{main_script}" --minimize'

    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE)
        if enabled:
            winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, app_path)
        else:
            try:
                winreg.DeleteValue(key, app_name)
            except FileNotFoundError:
                pass
        winreg.CloseKey(key)
        return True
    except Exception as e:
        print(f"Error updating registry: {e}")
        return False
