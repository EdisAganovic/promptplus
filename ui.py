"""
TextFlow - Text Replacement Tool
Entry point for the application.
"""
import sys
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QObject, pyqtSignal, Qt

from app.utils import check_existing_instances
from app.replacer import RealtimeTextReplacer, ReplacerThread, QuickSearchWindow
from app.gui import FastAPIWebBrowser
import keyboard
import threading

# Global reference for cleanup
_replacer_thread = None
_quick_search_window = None
_hotkey_handle = None


class QuickSearchSignalBridge(QObject):
    """Move global keyboard callbacks onto Qt's GUI thread safely."""
    triggered = pyqtSignal()


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


def setup_global_hotkey(bridge):
    """Setup global hotkey for quick search."""
    global _hotkey_handle
    # Leave physical key events untouched. The callback runs when the
    # shortcut's final key is released; modifiers may still be held.
    _hotkey_handle = keyboard.add_hotkey(
        'ctrl+alt+p', bridge.triggered.emit,
        suppress=False, trigger_on_release=True
    )


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

    bridge = QuickSearchSignalBridge()
    bridge.triggered.connect(lambda: show_quick_search(replacer), Qt.ConnectionType.QueuedConnection)
    setup_global_hotkey(bridge)

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
        if _hotkey_handle is not None:
            try:
                keyboard.remove_hotkey(_hotkey_handle)
            except Exception as e:
                print(f"WARNING: Could not unregister global hotkey: {e}")

    qt_app.aboutToQuit.connect(cleanup)

    sys.exit(qt_app.exec())


if __name__ == "__main__":
    main()
