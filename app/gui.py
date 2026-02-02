"""
app/gui.py - Qt GUI Components
===============================
Classes:
- LoadingThread(QThread): Starts uvicorn server, emits server_ready signal
- FastAPIWebBrowser(QMainWindow): Frameless window with embedded WebView
  - Custom title bar with min/max/close buttons
  - Rounded corners, drag-to-move, edge-resize
  - Loading animation while server starts
"""
import os
import time
import threading
import requests
import uvicorn
from PyQt6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QWidget, 
                             QLabel, QHBoxLayout, QPushButton, QFileDialog,
                             QGraphicsDropShadowEffect)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtCore import QUrl, QTimer, Qt, QThread, pyqtSignal, QRect
from PyQt6.QtGui import QRegion, QPainterPath, QColor, QIcon

from .api import app


class LoadingThread(QThread):
    server_ready = pyqtSignal()

    def run(self):
        """Run the FastAPI server in a separate thread."""
        def start_server():
            # In frozen noconsole app, stdout/stderr might be None
            # causing uvicorn default logger to crash
            config = uvicorn.Config(app, host="127.0.0.1", port=8080, log_config=None)
            server = uvicorn.Server(config)
            server.run()
        
        server_thread = threading.Thread(target=start_server, daemon=True)
        server_thread.start()
        
        max_attempts = 60
        attempts = 0
        while attempts < max_attempts:
            try:
                response = requests.get("http://127.0.0.1:8080", timeout=1)
                if response.status_code == 200:
                    self.server_ready.emit()
                    return
            except requests.exceptions.RequestException:
                time.sleep(0.5)
                attempts += 1
        
        self.server_ready.emit()


class FastAPIWebBrowser(QMainWindow):
    def __init__(self):
        super().__init__()
        self.port = 8080
        
        # Set Window Icon
        import sys
        if getattr(sys, 'frozen', False):
            root_dir = sys._MEIPASS if hasattr(sys, '_MEIPASS') else os.path.dirname(sys.executable)
        else:
            root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            
        icon_path = os.path.join(root_dir, "icon.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
            
        self.setWindowTitle("PromptPlus - Text Replacement Tool")
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)
        self.setMinimumSize(800, 600)
        
        # Set geometry and center on screen
        width, height = 1200, 870
        screen = QApplication.primaryScreen().availableGeometry()
        x = (screen.width() - width) // 2
        y = (screen.height() - height) // 2
        self.setGeometry(x, y, width, height)

        # Resize edge margin - 12px for 4K reliability
        self.resize_margin = 12
        
        main_widget = QWidget()
        main_widget.setObjectName("mainWidget")
        main_widget.setStyleSheet("""
            #mainWidget {
                background-color: #1a1b27;
                border: 1px solid #3a3f4b;
                border-radius: 0px;
            }
        """)
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        self.setCentralWidget(main_widget)

        self.title_bar = QWidget()
        self.title_bar.setFixedHeight(40)
        self.title_bar.setStyleSheet("background-color: #1a1b27;")
        title_layout = QHBoxLayout(self.title_bar)
        title_layout.setContentsMargins(15, 0, 0, 0)
        title_layout.setSpacing(0) # Flush buttons touch each other
        
        # KEY FIX: Force Arrow cursor on title bar to prevent resize cursor bleed-through
        self.title_bar.setCursor(Qt.CursorShape.ArrowCursor)
        self.title_bar.setMouseTracking(True)

        app_name = QLabel("PromptPlus - Text Replacement Tool v0.1")
        app_name.setStyleSheet("color: #e6e6ff; font-weight: bold; font-size: 14px;")
        title_layout.addWidget(app_name, alignment=Qt.AlignmentFlag.AlignVCenter)
        title_layout.addStretch()

        minimize_button = QPushButton("−")
        minimize_button.setFixedSize(45, 40)
        minimize_button.setCursor(Qt.CursorShape.PointingHandCursor)
        minimize_button.setStyleSheet("""
            QPushButton { background-color: transparent; color: white; border: none; font-size: 20px; border-radius: 0px; }
            QPushButton:hover { background-color: #3b3f4c; }
        """)
        minimize_button.clicked.connect(self.showMinimized)
        title_layout.addWidget(minimize_button)

        self.maximize_button = QPushButton("□")
        self.maximize_button.setFixedSize(45, 40)
        self.maximize_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.maximize_button.setStyleSheet("""
            QPushButton { background-color: transparent; color: white; border: none; font-size: 16px; border-radius: 0px; padding-bottom: 2px; }
            QPushButton:hover { background-color: #3b3f4c; }
        """)
        self.maximize_button.clicked.connect(self.toggle_maximize)
        title_layout.addWidget(self.maximize_button)

        close_button = QPushButton("✕")
        close_button.setFixedSize(45, 40)
        close_button.setCursor(Qt.CursorShape.PointingHandCursor)
        close_button.setStyleSheet("""
            QPushButton { background-color: transparent; color: white; border: none; font-size: 16px; border-radius: 0px; }
            QPushButton:hover { background-color: #e81123; }
        """)
        close_button.clicked.connect(self.close)
        title_layout.addWidget(close_button)

        main_layout.addWidget(self.title_bar)

        self.loading_widget = QWidget()
        loading_layout = QVBoxLayout(self.loading_widget)
        loading_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.loading_text = QLabel("Loading")
        self.loading_text.setStyleSheet("color: #e6e6ff; font-size: 24px; font-weight: bold;")
        loading_layout.addWidget(self.loading_text, alignment=Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.loading_widget)

        self.browser = QWebEngineView()
        self.browser.setStyleSheet("border-radius: 0px;")
        self.browser.page().setBackgroundColor(QColor("#1a1b27"))
        self.browser.hide()
        main_layout.addWidget(self.browser)

        self.old_pos = None
        self.is_resizing = False
        self.resize_direction = None
        self.resize_start_geometry = None
        self.setMouseTracking(True)
        self.centralWidget().setMouseTracking(True)
        
        # Enable recursive mouse tracking for all child widgets
        self.set_recursive_mouse_tracking(self)
        
        # Install event filter on the app to capture all mouse move events
        QApplication.instance().installEventFilter(self)

        self.loading_timer = QTimer(self)
        self.dots = 0
        self.loading_timer.timeout.connect(self.update_loading_animation)
        self.loading_timer.start(500)

        self.server_thread = LoadingThread()
        self.server_thread.server_ready.connect(self.on_server_ready)
        self.server_thread.start()
        
    def set_recursive_mouse_tracking(self, widget):
        """Enable mouse tracking for a widget and all its children recursively."""
        widget.setMouseTracking(True)
        for child in widget.findChildren(QWidget):
            child.setMouseTracking(True)

    def eventFilter(self, obj, event):
        """Global event filter to capture events from child widgets for window management."""
        from PyQt6.QtCore import QEvent
        
        # Mouse Move: Handle resize cursor updates and active resizing
        if event.type() == QEvent.Type.MouseMove:
            pos = self.mapFromGlobal(event.globalPosition().toPoint())
            
            if self.is_resizing:
                self.resize_window(event)
                return True
            elif self.old_pos is not None:
                # Handle dragging if title bar didn't catch it
                delta = event.globalPosition().toPoint() - self.old_pos
                self.move(self.pos() + delta)
                self.old_pos = event.globalPosition().toPoint()
                return True
            elif not self.isMaximized():
                if self.rect().contains(pos):
                    self.update_resize_cursor(pos)
        
        # Mouse Press: Detect start of resize or drag near edges
        elif event.type() == QEvent.Type.MouseButtonPress and event.button() == Qt.MouseButton.LeftButton:
            pos = self.mapFromGlobal(event.globalPosition().toPoint())
            
            # 1. Edge Resize check (Highest Priority)
            if not self.isMaximized():
                direction = self.get_resize_direction(pos)
                if direction:
                    self.start_resizing(event, direction)
                    return True
            
            # 2. Title Bar Drag check
            if self.title_bar.geometry().contains(pos):
                # Don't intercept if clicking buttons (they are nested in the title bar)
                child = self.childAt(pos)
                if child and isinstance(child, QPushButton):
                    return False
                    
                self.old_pos = event.globalPosition().toPoint()
                return True
                
        # Mouse Release: Reset states
        elif event.type() == QEvent.Type.MouseButtonRelease:
            if self.is_resizing or self.old_pos is not None:
                self.mouseReleaseEvent(event)
                return True
                
        return super().eventFilter(obj, event)

    def update_loading_animation(self):
        self.dots = (self.dots + 1) % 4
        self.loading_text.setText(f"Loading{'.' * self.dots}")

    def on_server_ready(self):
        if self.loading_timer.isActive():
            self.loading_timer.stop()
            self.loading_text.setText("Loading... Done!")
            QTimer.singleShot(500, self.show_browser)

    def show_browser(self):
        self.loading_widget.hide()
        self.browser.show()
        
        # Refresh mouse tracking for the now visible browser and its children
        self.set_recursive_mouse_tracking(self.browser)
        
        # Connect download requested signal to handle "Save As"
        self.browser.page().profile().downloadRequested.connect(self.on_download_requested)
        
        self.browser.load(QUrl(f"http://127.0.0.1:{self.port}"))

    def on_download_requested(self, download):
        """Handle download requests by showing a native Save File dialog."""
        suggested_path = download.downloadFileName()
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Prompt Export",
            suggested_path,
            "JSON Files (*.json);;All Files (*)"
        )
        
        if file_path:
            download.setDownloadDirectory(os.path.dirname(file_path))
            download.setDownloadFileName(os.path.basename(file_path))
            download.accept()
        else:
            download.cancel()
        
    def toggle_maximize(self):
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()

    def on_window_state_changed(self):
        if self.isMaximized():
            self.maximize_button.setText("❐")
        else:
            self.maximize_button.setText("□")
        self.setMask(QRegion()) # Ensure sharp edges always



    def get_resize_direction(self, pos):
        margin = self.resize_margin
        
        on_left = pos.x() < margin
        on_right = pos.x() > self.width() - margin
        on_top = pos.y() < margin
        on_bottom = pos.y() > self.height() - margin
        
        # Priority 1: Check corners and edges for resize triggers
        if on_left and on_top: return 'top_left'
        if on_right and on_top: return 'top_right'
        if on_left and on_bottom: return 'bottom_left'
        if on_right and on_bottom: return 'bottom_right'
        if on_left: return 'left'
        if on_right: return 'right'
        if on_top: return 'top'
        if on_bottom: return 'bottom'

        # Priority 2: Only if not at edge, check if we are in the title bar area
        child = self.childAt(pos)
        if child is not None:
             curr = child
             while curr is not None and curr is not self:
                 if curr is self.title_bar:
                     return None
                 curr = curr.parent()
        
        return None

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if self.title_bar.geometry().contains(event.pos()):
                self.toggle_maximize()
                event.accept()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            # Check for resize FIRST
            if not self.isMaximized():
                direction = self.get_resize_direction(event.pos())
                if direction:
                    self.start_resizing(event, direction)
                    event.accept()
                    return

            # Only then check for dragging
            if self.title_bar.geometry().contains(event.pos()):
                self.old_pos = event.globalPosition().toPoint()
                event.accept()
                return

    def start_resizing(self, event, direction):
        self.is_resizing = True
        self.resize_direction = direction
        self.resize_start_pos = event.globalPosition().toPoint()
        self.resize_start_geometry = self.geometry()

    def mouseMoveEvent(self, event):
        # Update cursor proactively to show resize pointers at edges
        if not self.is_resizing and self.old_pos is None:
            self.update_resize_cursor(event.pos())
            
        if self.old_pos is not None and not self.is_resizing:
            delta = event.globalPosition().toPoint() - self.old_pos
            self.move(self.pos() + delta)
            self.old_pos = event.globalPosition().toPoint()
        elif self.is_resizing:
            self.resize_window(event)

    def resize_window(self, event):
        if not self.is_resizing or not self.resize_start_geometry:
            return
        delta = event.globalPosition().toPoint() - self.resize_start_pos
        new_geometry = QRect(self.resize_start_geometry)

        if 'left' in self.resize_direction:
            new_width = self.resize_start_geometry.width() - delta.x()
            if new_width > self.minimumWidth():
                new_geometry.setLeft(self.resize_start_geometry.left() + delta.x())
        if 'right' in self.resize_direction:
            new_geometry.setWidth(self.resize_start_geometry.width() + delta.x())
        if 'top' in self.resize_direction:
            new_height = self.resize_start_geometry.height() - delta.y()
            if new_height > self.minimumHeight():
                new_geometry.setTop(self.resize_start_geometry.top() + delta.y())
        if 'bottom' in self.resize_direction:
            new_geometry.setHeight(self.resize_start_geometry.height() + delta.y())
        
        self.setGeometry(new_geometry)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.old_pos = None
            self.is_resizing = False
            self.resize_direction = None
            self.resize_start_geometry = None
            while QApplication.overrideCursor():
                QApplication.restoreOverrideCursor()
            self.unsetCursor()

    def update_resize_cursor(self, pos):
        if self.isMaximized():
            if QApplication.overrideCursor(): QApplication.restoreOverrideCursor()
            self.setCursor(Qt.CursorShape.ArrowCursor)
            return

        direction = self.get_resize_direction(pos)
        cursor_map = {
            'top_left': Qt.CursorShape.SizeFDiagCursor,
            'bottom_right': Qt.CursorShape.SizeFDiagCursor,
            'top_right': Qt.CursorShape.SizeBDiagCursor,
            'bottom_left': Qt.CursorShape.SizeBDiagCursor,
            'left': Qt.CursorShape.SizeHorCursor,
            'right': Qt.CursorShape.SizeHorCursor,
            'top': Qt.CursorShape.SizeVerCursor,
            'bottom': Qt.CursorShape.SizeVerCursor
        }

        if direction in cursor_map:
            new_cursor = cursor_map[direction]
            if QApplication.overrideCursor() and QApplication.overrideCursor().shape() == new_cursor:
                return # Already set
            QApplication.setOverrideCursor(new_cursor)
        else:
            # Not in resize zone - restore default behavior
            while QApplication.overrideCursor():
                QApplication.restoreOverrideCursor()
            self.setCursor(Qt.CursorShape.ArrowCursor)

    def changeEvent(self, event):
        if event.type() == event.Type.WindowStateChange:
            self.on_window_state_changed()
        super().changeEvent(event)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Mask removed to allow edge resize detection
