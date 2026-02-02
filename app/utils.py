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

PROMPTS_FILE = "prompts.json"


def get_current_date():
    return datetime.now().strftime("%m.%d.%Y")


def load_prompts():
    if os.path.exists(PROMPTS_FILE):
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
                        'content': value,
                        'last_updated': get_current_date(),
                        'tags': []
                    }
            return prompts
    return {}


def save_prompts(prompts):
    with open(PROMPTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(prompts, f, ensure_ascii=False, indent=2)


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
