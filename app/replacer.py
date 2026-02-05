"""
app/replacer.py - Text Replacement Engine
==========================================
Classes:
- RealtimeTextReplacer: Monitors keyboard, replaces typed keywords with prompts
  - start_monitoring(): Start keyboard hook loop
  - stop_monitoring(): Stop and cleanup
- ReplacerThread(QThread): Runs replacer in background thread
  - run(): Calls replacer.start_monitoring()
  - stop(): Calls replacer.stop_monitoring()

IMPORTANT: DO NOT CHANGE THE TEXT REPLACEMENT METHOD!
======================================================
The perform_replacement() function uses pyautogui for:
  - pyautogui.press('backspace', ...) to delete the keyword
  - pyautogui.hotkey('ctrl', 'v') to paste the replacement
  
This method has been proven to be FAST and RELIABLE.
Do NOT replace it with keyboard library or any other method.
"""
import time
import threading
import keyboard
import pyautogui
import pyperclip
from PyQt6.QtCore import QThread

from .utils import PROMPTS_FILE, load_prompts
import os
import json


class RealtimeTextReplacer:
    def __init__(self):
        self.prompts = self._load_prompts_for_replacer()
        self.current_buffer = ""
        self.is_replacing = False
        self.lock = threading.Lock()
        self.last_file_mod_time = self._get_file_mod_time()
        self._running = True

    def _load_prompts_for_replacer(self):
        if os.path.exists(PROMPTS_FILE):
            try:
                with open(PROMPTS_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    prompts = {}
                    for key, value in data.items():
                        if isinstance(value, dict) and 'content' in value:
                            prompts[key] = value['content']
                        else:
                            prompts[key] = value
                    return prompts
            except (json.JSONDecodeError, IOError):
                return {}
        return {}

    def _get_file_mod_time(self):
        if os.path.exists(PROMPTS_FILE):
            return os.path.getmtime(PROMPTS_FILE)
        return None

    def reload_prompts_if_needed(self):
        current_file_mod_time = self._get_file_mod_time()
        if current_file_mod_time and current_file_mod_time != self.last_file_mod_time:
            new_prompts = self._load_prompts_for_replacer()
            if new_prompts != self.prompts:
                with self.lock:
                    self.prompts = new_prompts
            self.last_file_mod_time = current_file_mod_time

    def on_key_event(self, event):
        if self.is_replacing or event.event_type != keyboard.KEY_DOWN:
            return
        if len(event.name) == 1:
            self.current_buffer += event.name
        elif event.name == 'space':
            self.current_buffer += ' '
            self.check_for_replacement()
        elif event.name == 'backspace':
            self.current_buffer = self.current_buffer[:-1]
        if len(self.current_buffer) > 100:
            self.current_buffer = self.current_buffer[-100:]

    def check_for_replacement(self):
        if self.is_replacing:
            return
        with self.lock:
            local_prompts = dict(self.prompts)
        sorted_keywords = sorted(local_prompts.keys(), key=len, reverse=True)
        for keyword in sorted_keywords:
            trigger_phrase = keyword + ' '
            if self.current_buffer.endswith(trigger_phrase):
                self.perform_replacement(keyword)
                return

    def perform_replacement(self, keyword):
        self.is_replacing = True
        with self.lock:
            replacement_text = self.prompts[keyword]
        total_length = len(keyword) + 1
        pyautogui.press('backspace', presses=total_length, interval=0.003)
        original_clipboard = pyperclip.paste()
        try:
            pyperclip.copy(replacement_text)
            pyautogui.hotkey('ctrl', 'v')
        finally:
            pyperclip.copy(original_clipboard)
        self.current_buffer = ""
        self.is_replacing = False

    def start_monitoring(self):
        print("Text Replacer is now active.")
        keyboard.hook(self.on_key_event)
        while self._running:
            time.sleep(0.1)
            self.reload_prompts_if_needed()

    def stop_monitoring(self):
        self._running = False
        keyboard.unhook_all()
        print("Text Replacer stopped.")


class ReplacerThread(QThread):
    """Thread to run the text replacer in background."""
    def __init__(self, replacer):
        super().__init__()
        self.replacer = replacer

    def run(self):
        self.replacer.start_monitoring()

    def stop(self):
        self.replacer.stop_monitoring()
