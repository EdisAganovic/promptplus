import sys
import threading
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel, QHBoxLayout, QPushButton
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtCore import QUrl, QTimer, Qt
from PyQt6.QtGui import QRegion, QPainterPath, QPolygon

# Import your FastAPI app from the 'ui.py' file
# Ensure 'ui.py' exists in the same folder and contains a FastAPI instance named 'app'.
from ui import app
import uvicorn


class FastAPIWebBrowser(QMainWindow):
    def __init__(self):
        super().__init__()
        self.port = 8080  # Using a unique port to avoid conflicts
        self.setWindowTitle("GPTPlus - Text Replacement Tool")
        self.setGeometry(100, 100, 1200, 800)

        # Remove the title bar and window buttons to make it borderless
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)

        # Create a rounded window mask
        self.create_rounded_mask(10)  # 15px corner radius

        # Create a main widget and layout
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)  # Remove margins
        main_layout.setSpacing(0)  # Remove spacing
        self.setCentralWidget(main_widget)

        # Create custom title bar. It's crucial to store it as a class
        # attribute (e.g., self.title_bar) so we can reference it later
        # in the mouse event handlers.
        self.title_bar = QWidget()
        self.title_bar.setFixedHeight(40)  # Set height for title bar
        self.title_bar.setStyleSheet("background-color: #1a1b27; border-top-left-radius: 15px; border-top-right-radius: 15px;")  # Dark background with rounded top corners
        title_layout = QHBoxLayout(self.title_bar)
        title_layout.setContentsMargins(15, 0, 15, 0)

        # Add app name label
        app_name = QLabel("GPTPlus - Text Replacement Tool")
        app_name.setStyleSheet("color: #e6e6ff; font-weight: bold; font-size: 14px;")
        title_layout.addWidget(app_name)

        title_layout.addStretch()  # Push subsequent widgets to the right

        # Add close button
        close_button = QPushButton("✕")
        close_button.setFixedSize(30, 30)
        # A stylesheet with a :hover pseudo-state is cleaner than handling mouse enter/leave events
        close_button.setStyleSheet("""
            QPushButton {
                background-color: #ef4444;
                color: white;
                border: none;
                font-weight: bold;
                font-size: 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #dc2626;
            }
        """)
        close_button.clicked.connect(self.close)
        title_layout.addWidget(close_button)

        # Add title bar and browser to main layout
        main_layout.addWidget(self.title_bar)

        # Create a web view widget
        self.browser = QWebEngineView()
        self.browser.setStyleSheet("border-bottom-left-radius: 15px; border-bottom-right-radius: 15px;")  # Rounded bottom corners for browser
        main_layout.addWidget(self.browser)

        # Variable to store the mouse position when dragging starts
        self.old_pos = None

        # Start the FastAPI server in a separate thread
        self.server_thread = threading.Thread(target=self.run_server, daemon=True)
        self.server_thread.start()

        # Wait a moment for the server to start, then load the page
        QTimer.singleShot(2000, self.load_page)
        
    def create_rounded_mask(self, radius):
        """Create a rounded rectangle mask for the window"""
        # Use QTimer to delay the mask creation until after the window is properly shown
        QTimer.singleShot(0, lambda: self.apply_rounded_mask(radius))
        
    def apply_rounded_mask(self, radius):
        """Apply the rounded rectangle mask"""
        from PyQt6.QtCore import QRect
        from PyQt6.QtGui import QPainterPath
        from PyQt6.QtCore import QRectF
        
        rect = self.rect()
        path = QPainterPath()
        path.addRoundedRect(QRectF(rect), radius, radius)
        
        # Convert path to polygon for the mask
        polygon = path.toFillPolygon().toPolygon()
        self.setMask(QRegion(polygon))

    def run_server(self):
        """Run the FastAPI server in a separate thread."""
        uvicorn.run(app, host="127.0.0.1", port=self.port, log_level="info")

    def load_page(self):
        """Load the FastAPI web interface after the server has started."""
        self.browser.load(QUrl(f"http://127.0.0.1:{self.port}"))

    # --- Corrected Window Dragging Logic ---

    def mousePressEvent(self, event):
        """This event is fired when a mouse button is pressed."""
        # We only start dragging if the left button is pressed and the cursor is over our title_bar
        if event.button() == Qt.MouseButton.LeftButton and self.title_bar.underMouse():
            self.old_pos = event.globalPosition().toPoint()
            event.accept()

    def mouseMoveEvent(self, event):
        """This event is fired when the mouse is moved."""
        # We only move the window if we are in a dragging state (self.old_pos is set)
        if self.old_pos is not None:
            # Calculate the difference between the current mouse position and the last known position
            delta = event.globalPosition().toPoint() - self.old_pos
            # Move the window's top-left corner by that difference
            self.move(self.pos() + delta)
            # **THE FIX**: Update the last known position to the current mouse position.
            self.old_pos = event.globalPosition().toPoint()
            event.accept()

    def mouseReleaseEvent(self, event):
        """This event is fired when a mouse button is released."""
        # Stop dragging when the left mouse button is released
        if event.button() == Qt.MouseButton.LeftButton:
            self.old_pos = None
            event.accept()


def main():
    # Create Qt application
    qt_app = QApplication(sys.argv)

    # Create and show the main window
    window = FastAPIWebBrowser()
    window.show()

    # Run the Qt application event loop
    sys.exit(qt_app.exec())


if __name__ == "__main__":
    main()