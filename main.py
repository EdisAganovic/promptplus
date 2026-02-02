import sys
import os
from PyQt6.QtWidgets import QApplication
from app.gui import FastAPIWebBrowser

# Add current directory to sys.path to ensure modules are found
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FastAPIWebBrowser()
    window.show()
    sys.exit(app.exec())
