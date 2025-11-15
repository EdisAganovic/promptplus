#!/usr/bin/env python3
"""
Test script to verify the loading animation works properly
This script tests the Qt loading animation without starting the full FastAPI server
"""

import sys
import time
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel
from PyQt6.QtCore import QTimer, Qt
import threading

class TestLoadingScreen(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Loading Animation Test")
        self.setGeometry(100, 100, 600, 400)
        
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setCentralWidget(main_widget)
        
        # Loading text with animated dots
        self.loading_text = QLabel("Loading")
        self.loading_text.setStyleSheet("color: #e6e6ff; font-size: 24px; font-weight: bold;")
        main_layout.addWidget(self.loading_text, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # Initialize loading animation
        self.dots = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_loading_animation)
        self.timer.start(500)  # Update every 500ms
        
        # Close after 5 seconds to demonstrate the animation
        QTimer.singleShot(5000, self.close)
    
    def update_loading_animation(self):
        """Update the loading animation with animated dots."""
        self.dots = (self.dots + 1) % 4
        dots_text = "." * self.dots
        self.loading_text.setText(f"Loading{dots_text}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TestLoadingScreen()
    window.show()
    sys.exit(app.exec())