"""
TextFlow - Text Replacement Tool
Entry point for the application.
"""
import sys
import os
from PyQt6.QtWidgets import QApplication

from app.utils import check_existing_instances
from app.replacer import RealtimeTextReplacer, ReplacerThread, QuickSearchWindow
from app.gui import FastAPIWebBrowser
import keyboard
import threading

# Global reference for cleanup
_replacer_thread = None
_quick_search_window = None
_hotkey_thread = None


def show_quick_search(replacer):
    """Function to show the quick search window."""
    global _quick_search_window
    # Create the quick search window if it doesn't exist
    if _quick_search_window is None:
        _quick_search_window = QuickSearchWindow(replacer)
    # Show the window
    _quick_search_window.show()
    _quick_search_window.raise_()
    _quick_search_window.activateWindow()


def setup_global_hotkey(replacer):
    """Setup global hotkey for quick search."""
    # Register the global hotkey
    keyboard.add_hotkey('ctrl+shift+p', lambda: show_quick_search(replacer))


def main():
    # Instance check disabled for now
    # script_name = os.path.basename(__file__)
    # is_running, existing_pid = check_existing_instances(script_name)
    # if is_running:
    #     print(f"Another instance of the program is already running (PID: {existing_pid}).")
    #     print("Only one instance of TextFlow should be running at a time.")
    #     sys.exit(0)

    global _replacer_thread
    global _quick_search_window

    qt_app = QApplication(sys.argv)

    # Start the text replacer in a background thread
    replacer = RealtimeTextReplacer()
    _replacer_thread = ReplacerThread(replacer)
    _replacer_thread.start()

    # Setup global hotkey in a separate thread
    _hotkey_thread = threading.Thread(target=setup_global_hotkey, args=(replacer,), daemon=True)
    _hotkey_thread.start()

    window = FastAPIWebBrowser()
    window.show()

    # Handle cleanup on exit
    def cleanup():
        global _quick_search_window
        if _quick_search_window:
            _quick_search_window.close()
            _quick_search_window = None
        if _replacer_thread:
            _replacer_thread.stop()
            _replacer_thread.wait(2000)
        # Unregister hotkeys
        keyboard.unhook_all()

    qt_app.aboutToQuit.connect(cleanup)

    sys.exit(qt_app.exec())


if __name__ == "__main__":
    main()