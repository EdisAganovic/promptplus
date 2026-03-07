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
                             QGraphicsDropShadowEffect, QSystemTrayIcon, QMenu)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtCore import QUrl, QTimer, Qt, QThread, pyqtSignal, QRect, QObject, QFileSystemWatcher
from PyQt6.QtGui import QRegion, QPainterPath, QColor, QIcon

from .api import app
from .utils import load_settings, SETTINGS_FILE, VERSION


class LoadingThread(QThread):
    server_ready = pyqtSignal(int)

    def __init__(self, start_port=8080):
        super().__init__()
        self.port = start_port

    def run(self):
        """Run the FastAPI server on an available port."""
        import socket
        
        # Find an available port
        current_port = self.port
        while current_port < 8100:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                try:
                    s.bind(("127.0.0.1", current_port))
                    self.port = current_port
                    break
                except socket.error:
                    current_port += 1
        
        def start_server():
            # In frozen noconsole app, stdout/stderr might be None
            # causing uvicorn default logger to crash
            config = uvicorn.Config(
                app, 
                host="127.0.0.1", 
                port=self.port, 
                log_config=None,
                log_level="error"  # Suppress all non-error messages
            )
            server = uvicorn.Server(config)
            server.run()

        server_thread = threading.Thread(target=start_server, daemon=True)
        server_thread.start()

        # Faster initial check with exponential backoff for slow CPUs
        max_attempts = 60
        attempts = 0
        sleep_time = 0.3  # Start faster
        while attempts < max_attempts:
            try:
                response = requests.get(f"http://127.0.0.1:{self.port}", timeout=0.5)
                if response.status_code == 200:
                    self.server_ready.emit(self.port)
                    return
            except requests.exceptions.RequestException:
                time.sleep(sleep_time)
                attempts += 1
                sleep_time = min(sleep_time * 1.2, 0.8)  # Cap at 0.8s

        self.server_ready.emit(self.port)


class FastAPIWebBrowser(QMainWindow):
    def __init__(self, start_minimized=False):
        super().__init__()
        self.port = 8080
        self.start_minimized = start_minimized
        self.settings = load_settings()
        self.current_theme = self.settings.get("theme", "dark")
        self.last_settings_mod_time = os.path.getmtime(SETTINGS_FILE) if os.path.exists(SETTINGS_FILE) else 0

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
        # Base style will be updated by apply_theme
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        self.setCentralWidget(main_widget)

        self.title_bar = QWidget()
        self.title_bar.setFixedHeight(40)
        title_layout = QHBoxLayout(self.title_bar)
        title_layout.setContentsMargins(15, 0, 0, 0)
        title_layout.setSpacing(0) # Flush buttons touch each other

        # KEY FIX: Force Arrow cursor on title bar to prevent resize cursor bleed-through
        self.title_bar.setCursor(Qt.CursorShape.ArrowCursor)
        self.title_bar.setMouseTracking(True)

        self.app_name = QLabel(f"PromptPlus - Text Replacement Tool v{VERSION}")
        title_layout.addWidget(self.app_name, alignment=Qt.AlignmentFlag.AlignVCenter)
        title_layout.addStretch()

        self.minimize_button = QPushButton("−")
        self.minimize_button.setFixedSize(45, 40)
        self.minimize_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.minimize_button.clicked.connect(self.showMinimized)
        title_layout.addWidget(self.minimize_button)

        self.maximize_button = QPushButton("□")
        self.maximize_button.setFixedSize(45, 40)
        self.maximize_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.maximize_button.clicked.connect(self.toggle_maximize)
        title_layout.addWidget(self.maximize_button)

        self.close_button = QPushButton("✕")
        self.close_button.setFixedSize(45, 40)
        self.close_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.close_button.clicked.connect(self.close)
        title_layout.addWidget(self.close_button)

        main_layout.addWidget(self.title_bar)

        self.loading_widget = QWidget()
        loading_layout = QVBoxLayout(self.loading_widget)
        loading_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.loading_text = QLabel("Loading")
        loading_layout.addWidget(self.loading_text, alignment=Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.loading_widget)

        self.browser = QWebEngineView()
        self.browser.setStyleSheet("border-radius: 0px;")
        # Background will be set in apply_theme
        self.browser.hide()
        main_layout.addWidget(self.browser)

        # Apply initial theme
        self.apply_theme(self.current_theme)

        self.old_pos = None
        self.is_resizing = False
        self.resize_direction = None
        self.resize_start_geometry = None
        self.setMouseTracking(True)
        self.centralWidget().setMouseTracking(True)

        # OPTIMIZATION: Only enable mouse tracking on title bar (not all children)
        # This reduces CPU overhead from tracking events on every widget
        self.title_bar.setMouseTracking(True)
        for btn in [self.minimize_button, self.maximize_button, self.close_button]:
            btn.setMouseTracking(True)

        # Install event filter on the app to capture all mouse move events
        QApplication.instance().installEventFilter(self)

        # OPTIMIZATION: Faster loading animation (400ms) for better feel
        self.loading_timer = QTimer(self)
        self.dots = 0
        self.loading_timer.timeout.connect(self.update_loading_animation)
        self.loading_timer.start(400)

        self.server_thread = LoadingThread(start_port=self.port)
        self.server_thread.server_ready.connect(self.on_server_ready)
        self.server_thread.start()

        # Instant theme syncing via File Watcher
        self.settings_watcher = QFileSystemWatcher([SETTINGS_FILE])
        self.settings_watcher.fileChanged.connect(self.poll_theme_settings)

        # Initialize System Tray
        self.setup_tray_icon()

        # OPTIMIZATION: Cache for cursor state to avoid redundant setOverrideCursor calls
        self._last_cursor_shape = None
        self._cursor_update_threshold = 3  # Pixels to move before updating cursor
        self._last_cursor_pos = None

    def apply_theme(self, theme):
        """Apply theme-specific styling to the Qt components."""
        is_dark = theme == "dark"
        
        # Color palette
        bg_color = "#1a1b27" if is_dark else "#f5f5f7"
        title_bg = "#1a1b27" if is_dark else "#ebedef"
        border_color = "#3a3f4b" if is_dark else "#dee2e6"
        text_color = "#e6e6ff" if is_dark else "#1f2937"
        hover_bg = "#3b3f4c" if is_dark else "#e0e2e5"
        
        # Main Window
        self.centralWidget().setStyleSheet(f"""
            #mainWidget {{
                background-color: {bg_color};
                border: 1px solid {border_color};
                border-radius: 0px;
            }}
        """)
        
        # Title Bar
        self.title_bar.setStyleSheet(f"background-color: {title_bg};")
        self.app_name.setStyleSheet(f"color: {text_color}; font-weight: bold; font-size: 14px;")
        
        # Buttons
        btn_style = f"""
            QPushButton {{ background-color: transparent; color: {text_color}; border: none; border-radius: 0px; }}
            QPushButton:hover {{ background-color: {hover_bg}; }}
        """
        self.minimize_button.setStyleSheet(btn_style + "QPushButton { font-size: 20px; }")
        self.maximize_button.setStyleSheet(btn_style + "QPushButton { font-size: 16px; padding-bottom: 2px; }")
        self.close_button.setStyleSheet(btn_style + f"QPushButton {{ font-size: 16px; }} QPushButton:hover {{ background-color: #e81123; color: white; }}")
        
        # Loading Text
        self.loading_text.setStyleSheet(f"color: {text_color}; font-size: 24px; font-weight: bold;")
        
        # Browser Background
        self.browser.page().setBackgroundColor(QColor(bg_color))
        
        # Tray Menu Styling
        menu_style = f"""
            QMenu {{
                background-color: {bg_color};
                color: {text_color};
                border: 1px solid {border_color};
                border-radius: 8px;
                padding: 10px 0px;
                font-size: 14px;
            }}
            QMenu::item {{
                padding: 8px 30px;
                background-color: transparent;
                border: none;
            }}
            QMenu::item:selected {{
                background-color: {hover_bg};
                color: {text_color};
            }}
            QMenu::separator {{
                height: 1px;
                background: {border_color};
                margin: 5px 15px;
            }}
        """
        if hasattr(self, 'tray_menu'):
            self.tray_menu.setStyleSheet(menu_style)

    def setup_tray_icon(self):
        """Initialize the system tray icon and its context menu."""
        self.tray_icon = QSystemTrayIcon(self)
        
        # Reuse existing icon
        root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        import sys
        if getattr(sys, 'frozen', False):
            root_dir = sys._MEIPASS if hasattr(sys, '_MEIPASS') else os.path.dirname(sys.executable)
        
        icon_path = os.path.join(root_dir, "icon.ico")
        if os.path.exists(icon_path):
            self.tray_icon.setIcon(QIcon(icon_path))
        
        # Tray Context Menu
        self.tray_menu = QMenu()
        self.apply_theme(self.current_theme) # Re-apply to include menu styling
        
        open_action = self.tray_menu.addAction("Otvori")
        open_action.triggered.connect(self.show_normal)
        
        self.tray_menu.addSeparator()
        
        exit_action = self.tray_menu.addAction("Izađi")
        exit_action.triggered.connect(self.safe_exit)
        
        self.tray_icon.setContextMenu(self.tray_menu)
        
        # Click behavior
        self.tray_icon.activated.connect(self.on_tray_icon_activated)
        
        self.tray_icon.show()

    def poll_theme_settings(self):
        """Check if settings file was updated (e.g. by Web UI) and apply theme changes."""
        if not os.path.exists(SETTINGS_FILE):
            return
            
        try:
            mod_time = os.path.getmtime(SETTINGS_FILE)
            if mod_time > self.last_settings_mod_time:
                self.last_settings_mod_time = mod_time
                new_settings = load_settings()
                new_theme = new_settings.get("theme", self.current_theme)
                
                if new_theme != self.current_theme:
                    self.current_theme = new_theme
                    self.apply_theme(new_theme)
        except Exception:
            pass

    def on_tray_icon_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.show_normal()

    def show_normal(self):
        """Restore window and ensure it's visible."""
        self.showNormal() # Handles restoring from minimized state
        self.show()
        self.activateWindow()
        self.raise_()

    def safe_exit(self):
        """Ensure clean exit from tray menu."""
        # FIX: Remove event filter to prevent memory leak
        try:
            QApplication.instance().removeEventFilter(self)
        except:
            pass
        QApplication.instance().quit()

    def closeEvent(self, event):
        """FIX: Clean up event filter when window is closed."""
        try:
            QApplication.instance().removeEventFilter(self)
        except:
            pass
        event.accept()

    def eventFilter(self, obj, event):
        """Global event filter to capture events from child widgets for window management."""
        from PyQt6.QtCore import QEvent

        # OPTIMIZATION: Fast path - only process events for our window
        # Skip expensive checks if event is not for our window hierarchy
        if not isinstance(obj, QWidget):
            return super().eventFilter(obj, event)

        # OPTIMIZATION: Use objectName check instead of while-loop parent traversal
        # This is O(1) instead of O(n) where n is depth of widget tree
        if obj.window() is not self:
            return super().eventFilter(obj, event)

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
                # OPTIMIZATION: Throttle cursor updates - only update if moved enough
                global_pos = event.globalPosition().toPoint()
                if self._last_cursor_pos is None or \
                   (abs(global_pos.x() - self._last_cursor_pos.x()) > self._cursor_update_threshold or
                    abs(global_pos.y() - self._last_cursor_pos.y()) > self._cursor_update_threshold):
                    self._last_cursor_pos = global_pos
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

    def on_server_ready(self, port):
        self.port = port
        if self.loading_timer.isActive():
            self.loading_timer.stop()
            self.loading_text.setText("Ready!")
            QTimer.singleShot(100, self.show_browser)
            # FIX: Respect start_minimized flag - don't show window if minimized
            if not self.start_minimized:
                QTimer.singleShot(150, self.show)

    def show_browser(self):
        self.loading_widget.hide()
        self.browser.show()

        # OPTIMIZATION: Only enable mouse tracking on browser itself, not children
        self.browser.setMouseTracking(True)

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
            # FIX: Reset cursor position cache on maximize to prevent flicker
            self._last_cursor_pos = None
        else:
            self.maximize_button.setText("□")
        self.setMask(QRegion()) # Ensure sharp edges always

        # Minimize to tray behavior
        if self.isMinimized():
            self.hide()



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
            # FIX: Reset cursor position cache
            self._last_cursor_pos = None
            while QApplication.overrideCursor():
                QApplication.restoreOverrideCursor()
            self.unsetCursor()

    def update_resize_cursor(self, pos):
        if self.isMaximized():
            if QApplication.overrideCursor(): QApplication.restoreOverrideCursor()
            self.setCursor(Qt.CursorShape.ArrowCursor)
            self._last_cursor_shape = Qt.CursorShape.ArrowCursor
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
            # OPTIMIZATION: Only update if cursor shape actually changed
            if self._last_cursor_shape == new_cursor:
                return
            QApplication.setOverrideCursor(new_cursor)
            self._last_cursor_shape = new_cursor
        else:
            # Not in resize zone - restore default behavior
            if self._last_cursor_shape != Qt.CursorShape.ArrowCursor:
                while QApplication.overrideCursor():
                    QApplication.restoreOverrideCursor()
                self.setCursor(Qt.CursorShape.ArrowCursor)
                self._last_cursor_shape = Qt.CursorShape.ArrowCursor

    def changeEvent(self, event):
        if event.type() == event.Type.WindowStateChange:
            self.on_window_state_changed()
        super().changeEvent(event)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Mask removed to allow edge resize detection
