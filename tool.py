import json
import os
import time
import pyautogui
import pyperclip
import keyboard
import threading

PROMPTS_FILE = "prompts.json"

class RealtimeTextReplacer:
    def __init__(self):
        self.prompts = self.load_prompts()
        self.current_buffer = ""
        self.is_replacing = False
        self.lock = threading.Lock()
        self.last_file_mod_time = self._get_file_mod_time()

    def load_prompts(self):
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
            new_prompts = self.load_prompts()
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
        print("Text Replacer is now active. Type a keyword followed by SPACE to trigger replacement.")
        
        keyboard.hook(self.on_key_event)
        
        try:
            while True:
                time.sleep(0.1)
                self.reload_prompts_if_needed()
        except KeyboardInterrupt:
            keyboard.unhook_all()
            print("Text Replacer stopped.")
            os._exit(0)

if __name__ == "__main__":
    replacer = RealtimeTextReplacer()
    replacer.start_monitoring()