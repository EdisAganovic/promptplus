"""Global keyword replacement and prompt pasting, independent of the desktop UI."""

import json
import os
import sys
import threading
import time

import pyautogui
import pyperclip

from .utils import get_prompts_file

if sys.platform == "darwin":
    # pynput's macOS backend still expects this symbol on some PyObjC versions.
    try:
        import ctypes
        import ctypes.util

        library = ctypes.util.find_library("ApplicationServices")
        if library:
            services = ctypes.cdll.LoadLibrary(library)
            services.AXIsProcessTrusted.restype = ctypes.c_bool
            import HIServices

            HIServices.AXIsProcessTrusted = services.AXIsProcessTrusted
    except Exception:
        pass
    from pynput import keyboard as pynput_keyboard

    PASTE_KEY = "command"
else:
    import keyboard

    PASTE_KEY = "ctrl"


class RealtimeTextReplacer:
    def __init__(self, on_multiple_matches=None):
        self.lock = threading.RLock()
        self.on_multiple_matches = on_multiple_matches
        self.prompts = self._load_prompts()
        self.last_file_mod_time = self._get_file_mod_time()
        self.current_buffer = ""
        self.is_replacing = False
        self._running = True
        self._keyboard_hook = None
        self._pynput_listener = None
        self._keyword_map_cache = {}
        self._keyword_lengths_cache = set()
        self._cache_valid = False

    def _load_prompts(self):
        try:
            with open(get_prompts_file(), encoding="utf-8") as handle:
                data = json.load(handle)
            prompts = []
            if isinstance(data, list):
                for idx, item in enumerate(data):
                    if isinstance(item, dict) and isinstance(item.get("content"), str):
                        prompts.append({
                            "id": str(item.get("id") or f"p_{idx + 1}"),
                            "keyword": item.get("keyword", ""),
                            "content": item["content"],
                            "tags": item.get("tags", []) if isinstance(item.get("tags"), list) else []
                        })
            elif isinstance(data, dict):
                for idx, (key, value) in enumerate(data.items()):
                    if isinstance(value, str):
                        prompts.append({
                            "id": f"p_{idx + 1}",
                            "keyword": key,
                            "content": value,
                            "tags": []
                        })
                    elif isinstance(value, dict) and isinstance(value.get("content"), str):
                        prompts.append({
                            "id": str(value.get("id") or f"p_{idx + 1}"),
                            "keyword": key,
                            "content": value["content"],
                            "tags": value.get("tags", []) if isinstance(value.get("tags"), list) else []
                        })
            return prompts
        except (OSError, ValueError):
            return []

    def _get_file_mod_time(self):
        prompt_file = get_prompts_file()
        try:
            return prompt_file, os.stat(prompt_file).st_mtime_ns
        except OSError:
            return prompt_file, None

    def reload_prompts_if_needed(self):
        modified = self._get_file_mod_time()
        if modified != self.last_file_mod_time:
            prompts = self._load_prompts()
            with self.lock:
                self.prompts = prompts
                self._cache_valid = False
                self.last_file_mod_time = modified

    def _get_lookup_caches(self):
        if not self._cache_valid:
            mapping = {}
            for prompt in self.prompts:
                kw = prompt.get("keyword")
                if isinstance(kw, str) and kw:
                    mapping.setdefault(kw, []).append(prompt)
            self._keyword_map_cache = mapping
            self._keyword_lengths_cache = {len(key) + 1 for key in mapping}
            self._cache_valid = True
        return self._keyword_map_cache, self._keyword_lengths_cache

    def _check_for_replacement_unlocked(self):
        if self.is_replacing or not self.current_buffer:
            return None
        keyword_map, lengths = self._get_lookup_caches()
        for length in sorted(lengths, reverse=True):
            if len(self.current_buffer) >= length:
                suffix = self.current_buffer[-length:]
                if suffix.endswith(" ") and suffix[:-1] in keyword_map:
                    return suffix[:-1]
        return None

    def on_key_event(self, event):
        if self.is_replacing or event.event_type != "down":
            return
        name = getattr(event, "name", None)
        if not isinstance(name, str):
            return
        with self.lock:
            if len(name) == 1:
                self.current_buffer += name
            elif name == "space":
                self.current_buffer += " "
            elif name == "backspace":
                self.current_buffer = self.current_buffer[:-1]
            else:
                return
            if name in ("space", "backspace"):
                keyword = self._check_for_replacement_unlocked()
                if keyword:
                    keyword_map, _ = self._get_lookup_caches()
                    matches = keyword_map.get(keyword, [])
                    if matches:
                        self.current_buffer = ""
                        self.is_replacing = True
                        if len(matches) == 1:
                            threading.Thread(
                                target=self._replace_keyword_single,
                                args=(keyword, matches[0]["content"]),
                                daemon=True,
                            ).start()
                        else:
                            threading.Thread(
                                target=self._trigger_multiple_matches,
                                args=(keyword, matches),
                                daemon=True,
                            ).start()
                        return
            self.current_buffer = self.current_buffer[-50:]

    def _replace_keyword_single(self, keyword, content):
        time.sleep(0.05)
        try:
            pyautogui.press("backspace", presses=len(keyword) + 1, interval=0.015)
            self._paste_text(content)
        except Exception as exc:
            print(f"Text replacement failed: {exc}", file=sys.stderr, flush=True)
        finally:
            self.is_replacing = False

    def _trigger_multiple_matches(self, keyword, matches):
        time.sleep(0.05)
        try:
            pyautogui.press("backspace", presses=len(keyword) + 1, interval=0.015)
            if self.on_multiple_matches:
                self.on_multiple_matches(keyword, matches)
            else:
                print(json.dumps({
                    "event": "show_picker",
                    "keyword": keyword,
                    "prompts": matches
                }), flush=True)
        except Exception as exc:
            print(f"Multiple matches trigger failed: {exc}", file=sys.stderr, flush=True)
        finally:
            self.is_replacing = False

    @staticmethod
    def _paste_text(content):
        try:
            previous = pyperclip.paste()
        except Exception:
            previous = None
        try:
            pyperclip.copy(content)
            pyautogui.hotkey(PASTE_KEY, "v")
            time.sleep(0.2)
        finally:
            if previous is not None:
                try:
                    pyperclip.copy(previous)
                except Exception:
                    pass

    def paste_content(self, content):
        if not isinstance(content, str):
            return False
        with self.lock:
            self.is_replacing = True
            self.current_buffer = ""
        try:
            self._paste_text(content)
        finally:
            self.is_replacing = False
        return True

    def paste_prompt_by_id(self, prompt_id):
        self.reload_prompts_if_needed()
        with self.lock:
            target = next((p for p in self.prompts if p.get("id") == prompt_id), None)
        if target is None or not isinstance(target.get("content"), str):
            return False
        return self.paste_content(target["content"])

    def paste_prompt(self, keyword):
        self.reload_prompts_if_needed()
        with self.lock:
            target = next((p for p in self.prompts if p.get("keyword") == keyword or p.get("id") == keyword), None)
        if target is None or not isinstance(target.get("content"), str):
            return False
        return self.paste_content(target["content"])

    def paste_any(self, content=None, prompt_id=None, keyword=None):
        if isinstance(content, str) and content:
            return self.paste_content(content)
        if isinstance(prompt_id, str) and prompt_id:
            return self.paste_prompt_by_id(prompt_id)
        if isinstance(keyword, str) and keyword:
            return self.paste_prompt(keyword)
        return False

    def _pynput_on_press(self, key):
        if key == pynput_keyboard.Key.space:
            name = "space"
        elif key == pynput_keyboard.Key.backspace:
            name = "backspace"
        else:
            name = getattr(key, "char", None)
        if name is not None:
            self.on_key_event(type("KeyEvent", (), {"name": name, "event_type": "down"})())

    def start_monitoring(self):
        try:
            if sys.platform == "darwin":
                self._pynput_listener = pynput_keyboard.Listener(on_press=self._pynput_on_press)
                self._pynput_listener.start()
            else:
                with self.lock:
                    if not self._running:
                        return
                    self._keyboard_hook = keyboard.hook(self.on_key_event)
        except Exception as exc:
            print(f"Keyboard monitoring unavailable: {exc}", file=sys.stderr, flush=True)
            self._running = False
            return
        while self._running:
            time.sleep(2)
            self.reload_prompts_if_needed()

    def stop_monitoring(self):
        with self.lock:
            self._running = False
            hook = self._keyboard_hook
            self._keyboard_hook = None
        if hook is not None:
            keyboard.unhook(hook)
        if self._pynput_listener is not None:
            self._pynput_listener.stop()
