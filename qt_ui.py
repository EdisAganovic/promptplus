import sys
import time
import threading
import requests
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel, QHBoxLayout, QPushButton
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtCore import QUrl, QTimer, Qt, QThread, pyqtSignal
from PyQt6.QtGui import QRegion, QPainterPath, QPolygon

# Import your FastAPI app from the 'ui.py' file
# Ensure 'ui.py' exists in the same folder and contains a FastAPI instance named 'app'.
from ui import app
import uvicorn


class LoadingThread(QThread):
    server_ready = pyqtSignal()

    def run(self):
        """Run the FastAPI server in a separate thread."""
        import threading
        def start_server():
            uvicorn.run(app, host="127.0.0.1", port=8080, log_level="info")
        
        # Start the server in a daemon thread so it doesn't prevent the program from exiting
        server_thread = threading.Thread(target=start_server, daemon=True)
        server_thread.start()
        
        # Wait for the server to be ready by polling
        max_attempts = 60  # Maximum attempts (30 seconds with 0.5s intervals)
        attempts = 0
        
        while attempts < max_attempts:
            try:
                # Try to connect to the server
                response = requests.get(f"http://127.0.0.1:8080", timeout=1)
                if response.status_code == 200:
                    # Server is ready
                    break
            except requests.exceptions.RequestException:
                # Server is not ready yet, wait and try again
                time.sleep(0.5)
                attempts += 1
        
        # Emit signal that server is ready regardless of whether it actually responded
        # (in case of issues, we still want to stop the loading animation)
        self.server_ready.emit()


class FastAPIWebBrowser(QMainWindow):
    def __init__(self):
        super().__init__()
        self.port = 8080  # Using a unique port to avoid conflicts
        self.setWindowTitle("GPTPlus - Text Replacement Tool")
        self.setGeometry(100, 100, 1200, 800)

        # Remove the title bar and window buttons to make it borderless
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)



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

        # Add minimize button
        minimize_button = QPushButton("−")
        minimize_button.setFixedSize(30, 30)
        minimize_button.setStyleSheet("""
            QPushButton {
                background-color: #6b7280;
                color: white;
                border: none;
                font-weight: bold;
                font-size: 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #4b5563;
            }
        """)
        minimize_button.clicked.connect(self.showMinimized)
        title_layout.addWidget(minimize_button)

        # Add maximize button
        self.maximize_button = QPushButton("□")
        self.maximize_button.setFixedSize(30, 30)
        self.maximize_button.setStyleSheet("""
            QPushButton {
                background-color: #6b7280;
                color: white;
                border: none;
                font-weight: bold;
                font-size: 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #4b5563;
            }
        """)
        self.maximize_button.clicked.connect(self.toggle_maximize)
        title_layout.addWidget(self.maximize_button)

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

        # Create a rounded window mask
        self.create_rounded_mask(10)  # 10px corner radius

        # Add title bar and browser to main layout
        main_layout.addWidget(self.title_bar)

        # Create loading screen
        self.loading_widget = QWidget()
        loading_layout = QVBoxLayout(self.loading_widget)
        loading_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Loading text with animated dots
        self.loading_text = QLabel("Loading")
        self.loading_text.setStyleSheet("color: #e6e6ff; font-size: 24px; font-weight: bold;")
        loading_layout.addWidget(self.loading_text, alignment=Qt.AlignmentFlag.AlignCenter)

        # Set initial loading screen
        main_layout.addWidget(self.loading_widget)

        # Create a web view widget (initially hidden)
        self.browser = QWebEngineView()
        self.browser.setStyleSheet("border-bottom-left-radius: 15px; border-bottom-right-radius: 15px;")  # Rounded bottom corners for browser
        # Set the background color to black
        from PyQt6.QtGui import QColor
        self.browser.page().setBackgroundColor(QColor("#000000"))
        self.browser.hide()  # Initially hidden
        main_layout.addWidget(self.browser)

        # Variables to store the mouse position when dragging/resizing starts
        self.old_pos = None
        self.is_resizing = False
        self.resize_start_size = None
        self.resize_direction = None  # To track which edge is being used for resizing
        self.normal_geometry = None  # To store window geometry before maximizing

        # Initialize loading animation
        self.dots = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_loading_animation)
        self.timer.start(500)  # Update every 500ms

        # Start the FastAPI server in a separate thread
        self.server_thread = LoadingThread()
        self.server_thread.server_ready.connect(self.on_server_ready)
        self.server_thread.start()
        
        # Also start a timer to periodically check if the server is ready
        # This provides a backup in case the server starts without triggering the signal
        self.check_timer = QTimer(self)
        self.check_timer.timeout.connect(self.check_server_status)
        self.check_timer.start(1000)  # Check every second
        
        # Connect window state change to update maximize button text
        # Since PyQt6 doesn't have a direct signal for window state change,
        # we'll override changeEvent to handle it

    def update_loading_animation(self):
        """Update the loading animation with animated dots."""
        self.dots = (self.dots + 1) % 4
        dots_text = "." * self.dots
        self.loading_text.setText(f"Loading{dots_text}")

    def on_server_ready(self):
        """Called when the server is ready."""
        self.timer.stop()  # Stop the loading animation
        self.loading_text.setText("Loading... Done!")
        # Switch to the browser after a short delay
        QTimer.singleShot(500, self.show_browser)

    def check_server_status(self):
        """Check if the server is accessible and switch to browser if it is"""
        try:
            response = requests.get(f"http://127.0.0.1:{self.port}", timeout=1)
            if response.status_code == 200:
                self.on_server_ready()
        except requests.exceptions.RequestException:
            # Server is not ready yet
            pass
            
    def toggle_maximize(self):
        """Toggle between maximized and normal window state."""
        if self.isMaximized():
            self.showNormal()
            # Update the maximize button text to indicate normal state
            self.maximize_button.setText("□")
        else:
            # Store current geometry before maximizing
            self.normal_geometry = self.geometry()
            self.showMaximized()
            # Update the maximize button text to indicate maximized state
            self.maximize_button.setText("❐")
    
    def on_window_state_changed(self):
        """Update the maximize button text based on window state."""
        if self.isMaximized():
            # Don't apply rounded mask when maximized
            self.setMask(QRegion())  # Clear the mask
            self.maximize_button.setText("❐")
        else:
            # Reapply rounded mask when not maximized
            self.create_rounded_mask(10)
            self.maximize_button.setText("□")
    
    def show_browser(self):
        """Show the browser and hide the loading screen."""
        # Stop the check timer since we're now showing the browser
        self.check_timer.stop()
        
        self.loading_widget.hide()
        self.browser.show()
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

    def mousePressEvent(self, event):
        """This event is fired when a mouse button is pressed."""
        # Check if the click is on the title bar to enable dragging
        if event.button() == Qt.MouseButton.LeftButton and self.title_bar.underMouse():
            # Don't start resizing if we're on the title bar
            self.old_pos = event.globalPosition().toPoint()
            self.is_resizing = False  # Ensure resizing is not active
            event.accept()
        # Check if the click is near the window edges to enable resizing
        # Only if not clicking on the title bar
        elif event.button() == Qt.MouseButton.LeftButton and not self.title_bar.underMouse():
            self.start_resizing(event)
            event.accept()
        
    def mouseMoveEvent(self, event):
        """This event is fired when the mouse is moved."""
        # Handle window dragging
        if self.old_pos is not None and not self.is_resizing:
            # Calculate the difference between the current mouse position and the last known position
            delta = event.globalPosition().toPoint() - self.old_pos
            # Move the window's top-left corner by that difference
            self.move(self.pos() + delta)
            # Update the last known position to the current mouse position
            self.old_pos = event.globalPosition().toPoint()
            event.accept()
        # Handle window resizing
        elif self.is_resizing and self.resize_start_size is not None:
            self.resize_window(event)
            event.accept()
        
        # Change cursor when hovering near window edges for resizing
        if not self.isMaximized():  # Don't show resize cursor when maximized
            pos = event.position().toPoint()
            width, height = self.width(), self.height()
            
            # Define margin for resize detection (10 pixels from edge)
            margin = 10
            
            # Determine which edge is being hovered over
            on_left_edge = pos.x() < margin
            on_right_edge = pos.x() > width - margin
            on_top_edge = pos.y() < margin
            on_bottom_edge = pos.y() > height - margin
            
            # Set cursor based on which edge is being hovered
            if (on_left_edge and on_top_edge) or (on_right_edge and on_bottom_edge):
                self.setCursor(Qt.CursorShape.SizeFDiagCursor)  # Diagonal resize
            elif (on_right_edge and on_top_edge) or (on_left_edge and on_bottom_edge):
                self.setCursor(Qt.CursorShape.SizeBDiagCursor)  # Diagonal resize
            elif on_left_edge or on_right_edge:
                self.setCursor(Qt.CursorShape.SizeHorCursor)  # Horizontal resize
            elif on_top_edge or on_bottom_edge:
                self.setCursor(Qt.CursorShape.SizeVerCursor)  # Vertical resize
            else:
                # Reset cursor if not near edges
                self.unsetCursor()

    def mouseReleaseEvent(self, event):
        """This event is fired when a mouse button is released."""
        # Stop dragging when the left mouse button is released
        if event.button() == Qt.MouseButton.LeftButton:
            self.old_pos = None
            self.is_resizing = False
            self.resize_start_size = None
            self.resize_direction = None
            event.accept()
            
    def start_resizing(self, event):
        """Start resizing the window if the mouse is near the edge."""
        # Get the current mouse position relative to the window
        pos = event.position().toPoint()
        width, height = self.width(), self.height()
        
        # Define margin for resize detection (10 pixels from edge)
        margin = 10
        
        # Determine which edge is being clicked
        on_left_edge = pos.x() < margin
        on_right_edge = pos.x() > width - margin
        on_top_edge = pos.y() < margin
        on_bottom_edge = pos.y() > height - margin
        
        # Set flags based on which edge is being clicked
        if on_left_edge and on_top_edge:
            self.resize_direction = 'top_left'
        elif on_right_edge and on_top_edge:
            self.resize_direction = 'top_right'
        elif on_left_edge and on_bottom_edge:
            self.resize_direction = 'bottom_left'
        elif on_right_edge and on_bottom_edge:
            self.resize_direction = 'bottom_right'
        elif on_left_edge:
            self.resize_direction = 'left'
        elif on_right_edge:
            self.resize_direction = 'right'
        elif on_top_edge:
            self.resize_direction = 'top'
        elif on_bottom_edge:
            self.resize_direction = 'bottom'
        else:
            # Not near any edge
            self.resize_direction = None
            return
            
        self.is_resizing = True
        self.resize_start_size = self.size()
        self.resize_start_pos = event.globalPosition().toPoint()

    def resize_window(self, event):
        """Resize the window based on mouse movement."""
        if not self.resize_direction or not self.resize_start_size:
            return
            
        # Get the current mouse position
        current_pos = event.globalPosition().toPoint()
        delta = current_pos - self.resize_start_pos
        
        # Calculate new dimensions
        new_width = self.resize_start_size.width()
        new_height = self.resize_start_size.height()
        new_x = self.x()
        new_y = self.y()
        
        # Adjust dimensions based on the resize direction
        if 'left' in self.resize_direction:
            new_width -= delta.x()
            new_x += delta.x()
        elif 'right' in self.resize_direction:
            new_width += delta.x()
            
        if 'top' in self.resize_direction:
            new_height -= delta.y()
            new_y += delta.y()
        elif 'bottom' in self.resize_direction:
            new_height += delta.y()
        
        # Apply minimum size constraints
        min_width, min_height = 800, 600
        new_width = max(new_width, min_width)
        new_height = max(new_height, min_height)
        
        # Resize the window
        self.setGeometry(new_x, new_y, new_width, new_height)
        
        # Update the rounded mask if the window size changed
        self.create_rounded_mask(10)  # Update the mask with new size

    def changeEvent(self, event):
        """Handle window state changes to update the maximize button."""
        if event.type() == event.Type.WindowStateChange:
            self.on_window_state_changed()
        super().changeEvent(event)


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