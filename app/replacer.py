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
from PyQt6.QtCore import QThread, QTimer

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
        # OPTIMIZATION: Cache sorted keywords to avoid sorting on every check
        self._sorted_keywords_cache = None
        self._cache_valid = False

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
                    # OPTIMIZATION: Invalidate cache when prompts change
                    self._cache_valid = False
            self.last_file_mod_time = current_file_mod_time

    def _get_sorted_keywords(self):
        """OPTIMIZATION: Cache sorted keywords to avoid sorting on every keypress."""
        if self._cache_valid and self._sorted_keywords_cache is not None:
            return self._sorted_keywords_cache
        
        with self.lock:
            local_prompts = dict(self.prompts)
        
        self._sorted_keywords_cache = sorted(local_prompts.keys(), key=len, reverse=True)
        self._cache_valid = True
        return self._sorted_keywords_cache

    def on_key_event(self, event):
        # OPTIMIZATION: Early exit checks before acquiring lock
        if self.is_replacing or event.event_type != keyboard.KEY_DOWN:
            return
        
        # FIX: Use lock for thread-safe buffer access
        with self.lock:
            if len(event.name) == 1:
                self.current_buffer += event.name
            elif event.name == 'space':
                self.current_buffer += ' '
                # Check for replacement while holding lock
                keyword = self._check_for_replacement_unlocked()
                if keyword:
                    replacement_text = self.prompts.get(keyword, '')
                    self.current_buffer = ""
                    self.is_replacing = True
                    # Schedule replacement outside lock
                    QTimer.singleShot(0, lambda: self._do_replacement(keyword, replacement_text))
                    return
            elif event.name == 'backspace':
                self.current_buffer = self.current_buffer[:-1]
                # Check if the backspace revealed a valid keyword + space
                keyword = self._check_for_replacement_unlocked()
                if keyword:
                    replacement_text = self.prompts.get(keyword, '')
                    self.current_buffer = ""
                    self.is_replacing = True
                    # Schedule replacement outside lock
                    QTimer.singleShot(0, lambda: self._do_replacement(keyword, replacement_text))
                    return
            
            if len(self.current_buffer) > 100:
                self.current_buffer = self.current_buffer[-100:]

    def _check_for_replacement_unlocked(self):
        """Internal method - must be called with lock held. Returns keyword if match found."""
        if self.is_replacing:
            return None
        sorted_keywords = self._get_sorted_keywords()
        for keyword in sorted_keywords:
            trigger_phrase = keyword + ' '
            if self.current_buffer.endswith(trigger_phrase):
                return keyword
        return None

    def _do_replacement(self, keyword, replacement_text):
        """Perform the actual text replacement."""
        try:
            total_length = len(keyword) + 1
            pyautogui.press('backspace', presses=total_length, interval=0.003)
            original_clipboard = pyperclip.paste()
            try:
                pyperclip.copy(replacement_text)
                pyautogui.hotkey('ctrl', 'v')
            finally:
                pyperclip.copy(original_clipboard)
        finally:
            self.is_replacing = False

    def check_for_replacement(self):
        """Public method - now deprecated, kept for compatibility."""
        pass

    def perform_replacement(self, keyword):
        """Deprecated - kept for compatibility, redirects to _do_replacement."""
        with self.lock:
            replacement_text = self.prompts.get(keyword, '')
        self._do_replacement(keyword, replacement_text)

    def start_monitoring(self):
        print("Text Replacer is now active.")
        keyboard.hook(self.on_key_event)
        # OPTIMIZATION: Increased sleep interval from 0.1s to 0.2s for lower CPU usage
        # File check only happens every 10 cycles (every 2 seconds) to reduce I/O
        check_counter = 0
        while self._running:
            time.sleep(0.2)
            check_counter += 1
            # Only check file modification every 10 iterations (2 seconds)
            if check_counter >= 10:
                self.reload_prompts_if_needed()
                check_counter = 0

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
