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
- QuickSearchWindow: Standalone window for quick prompt search

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
from PyQt6.QtCore import QThread, QTimer, Qt
from PyQt6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, 
                             QHBoxLayout, QLineEdit, QListWidget, 
                             QListWidgetItem, QWidget, QLabel, QPushButton, QGraphicsDropShadowEffect)
from PyQt6.QtGui import QFont, QPalette, QColor, QIcon

from .utils import PROMPTS_FILE, load_prompts, load_settings
import os
import json


class RealtimeTextReplacer:
    def __init__(self):
        self.prompts = self._load_prompts_for_replacer()
        self.current_buffer = ""
        self.is_replacing = False
        self.lock = threading.RLock()
        self.last_file_mod_time = self._get_file_mod_time()
        self._running = True
        # OPTIMIZATION: Cache set of keyword lengths and the prompts dictionary for O(1) lookups
        self._keyword_lengths_cache = set()
        self._prompts_cache = {}
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

    def _get_lookup_caches(self):
        """OPTIMIZATION: Returns (prompts_dict, keyword_lengths_set) for O(1) hash map matching."""
        if self._cache_valid:
            return self._prompts_cache, self._keyword_lengths_cache

        local_prompts = dict(self.prompts)

        # Cache lengths of all triggers to avoid checking irrelevant lengths
        lengths = set()
        for keyword in local_prompts.keys():
            # We match keyword + ' '
            lengths.add(len(keyword) + 1)
            
        self._prompts_cache = local_prompts
        self._keyword_lengths_cache = lengths
        self._cache_valid = True
        
        return self._prompts_cache, self._keyword_lengths_cache

    def on_key_event(self, event):
        try:
            # OPTIMIZATION: Early exit checks before acquiring lock
            if self.is_replacing or event.event_type != keyboard.KEY_DOWN:
                return

            # FIX: Use lock for thread-safe buffer access
            with self.lock:
                # Safely check event name type and length
                if not hasattr(event, 'name') or not isinstance(event.name, str):
                    return
                    
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
                        threading.Thread(target=self._do_replacement, args=(keyword, replacement_text), daemon=True).start()
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
                        threading.Thread(target=self._do_replacement, args=(keyword, replacement_text), daemon=True).start()
                        return

                if len(self.current_buffer) > 50:
                    self.current_buffer = self.current_buffer[-50:]
        except Exception as e:
            print(f"Error processing key event: {e}")

    def _check_for_replacement_unlocked(self):
        """Internal method - must be called with lock held. Returns keyword if match found."""
        if self.is_replacing or not self.current_buffer:
            return None
            
        prompts_cache, lengths_cache = self._get_lookup_caches()
        if not prompts_cache:
            return None
            
        buffer_len = len(self.current_buffer)
        
        # Test substrings backwards matching exact cached lengths
        # Sort lengths ascending to match shortest trigger first, or descending for longest.
        # Often longest matching is preferred if triggers overlap (e.g. ":e " vs ":em ")
        for length in sorted(lengths_cache, reverse=True):
            if buffer_len >= length:
                # Slice the end of the buffer to match the target length
                suffix = self.current_buffer[-length:]
                # All triggers end with a space
                if suffix.endswith(' '):
                    keyword = suffix[:-1]
                    if keyword in prompts_cache:
                        return keyword
                    
        return None

    def _do_replacement(self, keyword, replacement_text):
        """Perform the actual text replacement."""
        # Wait slightly to ensure the physical trigger key (like space) has fully registered in the target app
        time.sleep(0.05)
        try:
            total_length = len(keyword) + 1
            pyautogui.press('backspace', presses=total_length, interval=0.015)
            
            try:
                original_clipboard = pyperclip.paste()
            except Exception:
                original_clipboard = ""
                
            try:
                pyperclip.copy(replacement_text)
                pyautogui.hotkey('ctrl', 'v')
            except Exception as e:
                print(f"Error during replacement paste: {e}")
            finally:
                # Safety releases: prevent PyAutoGUI from leaving modifiers down
                for key in ['ctrl', 'shift', 'alt', 'v']:
                    pyautogui.keyUp(key)

                # Slight delay to ensure Ctrl+V completes before restoring old clipboard
                time.sleep(0.05)
                try:
                    if original_clipboard:
                        pyperclip.copy(original_clipboard)
                except Exception:
                    pass
        except Exception as e:
            print(f"Error in _do_replacement: {e}")
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
        try:
            keyboard.hook(self.on_key_event)
        except Exception as e:
            print(f"CRITICAL: Failed to hook keyboard. Text replacement will not work. Error: {e}")
            self._running = False
            return

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


class ReplacerThread(QThread):
    """Thread to run the text replacer in background."""
    def __init__(self, replacer):
        super().__init__()
        self.replacer = replacer

    def run(self):
        self.replacer.start_monitoring()

    def stop(self):
        self.replacer.stop_monitoring()


class QuickSearchWindow(QMainWindow):
    """Standalone window for quick prompt search with global hotkey."""
    
    def __init__(self, replacer):
        # Initialize in the main thread context
        super().__init__()
        self.replacer = replacer
        self.current_theme = None
        self.init_ui()
        
    def init_ui(self):
        # Window properties
        self.setWindowTitle('Quick Search - PromptPlus')
        self.setWindowFlags(Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # Main widget and layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # Add shadow effect
        self.shadow = QGraphicsDropShadowEffect()
        self.shadow.setBlurRadius(30)
        self.shadow.setXOffset(0)
        self.shadow.setYOffset(10)
        self.central_widget.setGraphicsEffect(self.shadow)
        
        self.layout = QVBoxLayout(self.central_widget)
        self.layout.setContentsMargins(15, 15, 15, 15)
        self.layout.setSpacing(12)
        
        # Debounce timer for search input
        self.search_timer = QTimer(self)
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(lambda: self.filter_prompts(self.search_input.text()))
        
        # Search input layout with Close Button
        self.search_layout = QHBoxLayout()
        self.search_layout.setContentsMargins(0, 0, 0, 0)
        self.search_layout.setSpacing(10)

        # Search input
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText('Pretraži promptove...')
        self.search_input.setFont(QFont('Inter', 12))
        self.search_input.textChanged.connect(lambda: self.search_timer.start(150))
        self.search_input.returnPressed.connect(self.insert_selected_prompt)

        # Close button
        self.close_btn = QPushButton("✕")
        self.close_btn.setFixedSize(30, 30)
        self.close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.close_btn.clicked.connect(self.close)

        self.search_layout.addWidget(self.search_input)
        self.search_layout.addWidget(self.close_btn)
        
        # Results list
        self.results_list = QListWidget()
        self.results_list.setFont(QFont('Inter', 11))
        self.results_list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.results_list.itemDoubleClicked.connect(self.insert_selected_prompt)
        
        # Add widgets to layout
        self.layout.addLayout(self.search_layout)
        self.layout.addWidget(self.results_list)
        
        # Set size
        self.resize(500, 400)
        
        # Load prompts
        self.all_prompts = list(self.replacer.prompts.items())
        
        # Apply theme styling
        self.apply_theme()
        
        # Connect escape key
        self.search_input.keyPressEvent = self.search_input_keyPressEvent

    def apply_theme(self):
        """Apply theme-specific colors and styles to the Quick Search window."""
        self.settings = load_settings()
        new_theme = self.settings.get("theme", "dark")
        
        # Optimization: Only re-apply if theme changed
        if new_theme == self.current_theme:
            return
            
        self.current_theme = new_theme
        is_dark = self.current_theme == "dark"

        # Theme Variables
        bg_color = "#1a1b27" if is_dark else "#ffffff"
        input_bg = "#232534" if is_dark else "#f3f4f6"
        border_color = "#3a3f4b" if is_dark else "#e5e7eb"
        text_primary = "#e6e6ff" if is_dark else "#1f2937"
        text_secondary = "#9ca3af" if is_dark else "#6b7280"
        accent_color = "#6366f1"
        hover_bg = "#2a2c3d" if is_dark else "#f9fafb"

        # Update shadow
        self.shadow.setColor(QColor(0, 0, 0, 100 if is_dark else 40))

        self.central_widget.setStyleSheet(f"""
            QWidget {{
                background-color: {bg_color};
                border-radius: 0px;
                border: 1px solid {border_color};
                color: {text_primary};
            }}
        """)

        self.search_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {input_bg};
                border: 1px solid {border_color};
                border-radius: 0px;
                padding: 12px 15px;
                color: {text_primary};
                font-size: 14px;
            }}
            QLineEdit:focus {{
                border: 2px solid {accent_color};
                background-color: {bg_color};
            }}
        """)

        self.close_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {text_secondary};
                border: none;
                font-size: 16px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                color: #ef4444;
                background-color: {input_bg};
                border-radius: 4px;
            }}
        """)

        self.results_list.setStyleSheet(f"""
            QListWidget {{
                background-color: transparent;
                border: none;
                outline: none;
                padding: 5px 0px;
            }}
            QListWidget::item {{
                padding: 12px 10px;
                border-radius: 0px;
                margin-bottom: 4px;
                color: {text_primary};
            }}
            QListWidget::item:hover {{
                background-color: {hover_bg};
            }}
            QListWidget::item:selected {{
                background-color: {accent_color};
                color: white;
            }}
            QScrollBar:vertical {{
                border: none;
                background: transparent;
                width: 8px;
                margin: 0px 0px 0px 0px;
            }}
            QScrollBar::handle:vertical {{
                background: {border_color};
                min-height: 20px;
                border-radius: 0px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
        """)

        self.results_list.itemDoubleClicked.connect(self.insert_selected_prompt)
        
        # Add widgets to layout
        layout.addLayout(search_layout)
        layout.addWidget(self.results_list)
        
        # Set size
        self.resize(500, 400)
        
        # Load prompts
        self.all_prompts = list(self.replacer.prompts.items())
        self.populate_results()
        
        # Connect escape key
        self.search_input.keyPressEvent = self.search_input_keyPressEvent
    
    def search_input_keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.close()
        elif event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
            self.insert_selected_prompt()
        elif event.key() == Qt.Key.Key_Down:
            current_row = self.results_list.currentRow()
            if current_row < self.results_list.count() - 1:
                self.results_list.setCurrentRow(current_row + 1)
        elif event.key() == Qt.Key.Key_Up:
            current_row = self.results_list.currentRow()
            if current_row > 0:
                self.results_list.setCurrentRow(current_row - 1)
        else:
            # Call the original keyPressEvent
            QLineEdit.keyPressEvent(self.search_input, event)
    
    def populate_results(self):
        """Populate the results list with all prompts."""
        self.results_list.clear()
        for keyword, content in self.all_prompts:
            clean_content = content.replace('\n', ' ').replace('\r', '')
            item_text = f" {keyword}   —   {clean_content[:60]}{'...' if len(clean_content) > 60 else ''}"
            item = QListWidgetItem(item_text)
            item.setData(Qt.ItemDataRole.UserRole, content)
            self.results_list.addItem(item)
            
        if self.results_list.count() > 0:
            self.results_list.setCurrentRow(0)
            self.results_list.item(0).setSelected(True)
    
    def filter_prompts(self, text):
        """Filter prompts based on search text."""
        self.results_list.clear()
        text = text.lower()
        
        for keyword, content in self.all_prompts:
            if text in keyword.lower() or text in content.lower():
                clean_content = content.replace('\n', ' ').replace('\r', '')
                item_text = f" {keyword}   —   {clean_content[:60]}{'...' if len(clean_content) > 60 else ''}"
                item = QListWidgetItem(item_text)
                item.setData(Qt.ItemDataRole.UserRole, content)
                self.results_list.addItem(item)
                
        if self.results_list.count() > 0:
            self.results_list.setCurrentRow(0)
            self.results_list.item(0).setSelected(True)
    
    def insert_selected_prompt(self):
        """Insert the selected prompt into the active application."""
        current_item = self.results_list.currentItem()
        if current_item:
            content = current_item.data(Qt.ItemDataRole.UserRole)
            
            # Hide the window immediately to restore OS focus to the previous application
            self.hide()
            QApplication.processEvents() # Force Qt to visibly close the window right away
            
            # Wait 150ms for the OS context switch to complete, then perform the paste
            QTimer.singleShot(150, lambda: self._perform_paste(content))
        else:
            self.close()

    def _perform_paste(self, content):
        """Helper to safely manage clipboard and paste after focus is restored."""
        try:
            original_clipboard = pyperclip.paste()
        except:
            original_clipboard = ""
            
        try:
            pyperclip.copy(content)
            # Paste using Ctrl+V
            pyautogui.hotkey('ctrl', 'v')
        except Exception as e:
            print(f"Error during paste: {e}")
        finally:
            # explicitly release keys just in case pyautogui leaves them down
            for key in ['ctrl', 'shift', 'alt', 'v']:
                pyautogui.keyUp(key)
                
            # Wait 200ms before restoring original clipboard to ensure paste completed
            QTimer.singleShot(200, lambda: self._restore_clipboard_and_close(original_clipboard))
            
    def _restore_clipboard_and_close(self, original_clipboard):
        """Helper to clean up clipboard and fully close the window."""
        try:
            if original_clipboard:
                pyperclip.copy(original_clipboard)
        except:
            pass
        self.close()
    
    def showEvent(self, event):
        """Center the window on the screen when shown and refresh data."""
        super().showEvent(event)
        
        # Dynamically refresh theme in case user changed it in Web UI
        self.apply_theme()
        # Center the window
        screen = QApplication.primaryScreen()
        screen_geometry = screen.geometry()
        x = (screen_geometry.width() - self.width()) // 2
        y = (screen_geometry.height() - self.height()) // 2
        self.move(x, y)
        
        # Reload fresh prompts from memory in case user edited them in main UI
        self.all_prompts = list(self.replacer.prompts.items())
        
        # Reset search input for fresh open (this automatically calls filter_prompts)
        self.search_input.clear()
        
        # Fallback populate just in case clear() doesn't trigger a change
        if not self.search_input.text():
            self.populate_results()
            
        self.search_input.setFocus()
