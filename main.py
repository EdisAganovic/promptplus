import sys
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QObject, pyqtSignal, Qt
from app.gui import FastAPIWebBrowser
from app.replacer import RealtimeTextReplacer, ReplacerThread, QuickSearchWindow
import keyboard
import threading

# Add current directory to sys.path to ensure modules are found
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Suppress Qt QPA console warnings (like DPI awareness access denied)
os.environ["QT_LOGGING_RULES"] = "qt.qpa.window=false"

# Global references for cleanup
_replacer_thread = None
_quick_search_window = None

class QuickSearchManager(QObject):
    """Bridge for safely triggering UI actions from background threads to the main GUI thread."""
    show_search = pyqtSignal()
    
    def __init__(self, replacer):
        super().__init__()
        self.replacer = replacer
        self.show_search.connect(self.handle_show_search, Qt.ConnectionType.QueuedConnection)

    def handle_show_search(self):
        """Function to show the quick search window. Now guaranteed to be on Main Thread."""
        global _quick_search_window
        # Create the quick search window if it doesn't exist
        if _quick_search_window is None:
            _quick_search_window = QuickSearchWindow(self.replacer)
        
        # Show and focus the window
        _quick_search_window.show()
        _quick_search_window.raise_()
        _quick_search_window.activateWindow()
        
        # Reset and focus the input field explicitly after a tiny delay
        # to ensure the keyboard shortcut 'p' event is fully swallowed by the OS
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(50, _quick_search_window.search_input.clear)
        QTimer.singleShot(60, _quick_search_window.search_input.setFocus)

if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Check for --minimize flag
    start_minimized = "--minimize" in sys.argv

    # Start the text replacer in a background thread
    replacer = RealtimeTextReplacer()
    _replacer_thread = ReplacerThread(replacer)
    _replacer_thread.start()

    # Setup cross-thread trigger using our Custom Manager
    trigger_manager = QuickSearchManager(replacer)

    # Setup global hotkey to emit the signal and suppress it from OS
    try:
        # Use suppress=True to prevent the 'p' from being typed into the search box
        keyboard.add_hotkey('ctrl+alt+p', trigger_manager.show_search.emit, suppress=True)
    except Exception as e:
        print(f"WARNING: Global hotkey 'ctrl+alt+p' could not be registered. Error: {e}")

    window = FastAPIWebBrowser(start_minimized=start_minimized)
    if not start_minimized:
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

    app.aboutToQuit.connect(cleanup)

    sys.exit(app.exec())
