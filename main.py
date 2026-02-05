import sys
import os
from PyQt6.QtWidgets import QApplication
from app.gui import FastAPIWebBrowser
from app.replacer import RealtimeTextReplacer, ReplacerThread

# Add current directory to sys.path to ensure modules are found
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Global reference for cleanup
_replacer_thread = None

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Check for --minimize flag
    start_minimized = "--minimize" in sys.argv
    
    # Start the text replacer in a background thread
    replacer = RealtimeTextReplacer()
    _replacer_thread = ReplacerThread(replacer)
    _replacer_thread.start()
    
    window = FastAPIWebBrowser(start_minimized=start_minimized)
    if not start_minimized:
        window.show()
    
    # Handle cleanup on exit
    def cleanup():
        if _replacer_thread:
            _replacer_thread.stop()
            _replacer_thread.wait(2000)
    
    app.aboutToQuit.connect(cleanup)
    
    sys.exit(app.exec())
