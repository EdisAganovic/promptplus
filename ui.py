"""
GPTPlus - Text Replacement Tool
Entry point for the application.
"""
import sys
import os
from PyQt6.QtWidgets import QApplication

from app.utils import check_existing_instances
from app.replacer import RealtimeTextReplacer, ReplacerThread
from app.gui import FastAPIWebBrowser

# Global reference for cleanup
_replacer_thread = None


def main():
    # Instance check disabled for now
    # script_name = os.path.basename(__file__)
    # is_running, existing_pid = check_existing_instances(script_name)
    # if is_running:
    #     print(f"Another instance of the program is already running (PID: {existing_pid}).")
    #     print("Only one instance of GPTPlus should be running at a time.")
    #     sys.exit(0)

    global _replacer_thread

    qt_app = QApplication(sys.argv)
    
    # Start the text replacer in a background thread
    replacer = RealtimeTextReplacer()
    _replacer_thread = ReplacerThread(replacer)
    _replacer_thread.start()

    window = FastAPIWebBrowser()
    window.show()
    
    # Handle cleanup on exit
    def cleanup():
        if _replacer_thread:
            _replacer_thread.stop()
            _replacer_thread.wait(2000)
    
    qt_app.aboutToQuit.connect(cleanup)
    
    sys.exit(qt_app.exec())


if __name__ == "__main__":
    main()