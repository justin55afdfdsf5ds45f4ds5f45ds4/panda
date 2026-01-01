"""
RED ALERT MODE - Aggressive full-screen reminder
This will scare you into drinking water.
"""

import sys
import random
from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QPushButton, QVBoxLayout
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QFont, QColor, QPalette

class RedAlertScreen(QWidget):
    """Full screen horror alert."""
    
    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint
        )
        self.showFullScreen()
        
        # Blood red background
        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor("#1a0000"))
        self.setPalette(palette)
        
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Warning text
        self.warning = QLabel("⚠ WARNING ⚠")
        self.warning.setFont(QFont("Impact", 60, QFont.Weight.Bold))
        self.warning.setStyleSheet("color: #ff0000;")
        self.warning.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.warning)
        
        # Main message
        self.message = QLabel("DRINK WATER")
        self.message.setFont(QFont("Impact", 120, QFont.Weight.Bold))
        self.message.setStyleSheet("color: #ff0000;")
        self.message.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.message)
        
        # Subtext
        self.subtext = QLabel("YOUR BODY DEMANDS HYDRATION")
        self.subtext.setFont(QFont("Arial", 30))
        self.subtext.setStyleSheet("color: #880000;")
        self.subtext.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.subtext)
        
        # Dismiss button
        self.btn = QPushButton("I WILL DRINK WATER")
        self.btn.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        self.btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn.setStyleSheet("""
            QPushButton {
                background-color: #330000;
                color: #ff0000;
                border: 3px solid #ff0000;
                padding: 20px 50px;
                margin-top: 50px;
            }
            QPushButton:hover {
                background-color: #ff0000;
                color: #000000;
            }
        """)
        self.btn.clicked.connect(self.dismiss)
        layout.addWidget(self.btn, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # Flashing effect
        self.flash_timer = QTimer()
        self.flash_timer.timeout.connect(self.flash)
        self.flash_timer.start(100)
        self.flash_state = False
        
        # Shake effect
        self.shake_timer = QTimer()
        self.shake_timer.timeout.connect(self.shake_text)
        self.shake_timer.start(50)
        
    def flash(self):
        """Flash the background between dark red and black."""
        self.flash_state = not self.flash_state
        palette = self.palette()
        if self.flash_state:
            palette.setColor(QPalette.ColorRole.Window, QColor("#2a0000"))
        else:
            palette.setColor(QPalette.ColorRole.Window, QColor("#0a0000"))
        self.setPalette(palette)
        
    def shake_text(self):
        """Shake the text randomly."""
        offset_x = random.randint(-5, 5)
        offset_y = random.randint(-3, 3)
        self.message.setStyleSheet(f"""
            color: #ff0000;
            margin-left: {offset_x}px;
            margin-top: {offset_y}px;
        """)
        
    def dismiss(self):
        """Close the alert."""
        self.flash_timer.stop()
        self.shake_timer.stop()
        self.close()
        QApplication.quit()


class RedAlertController:
    """Controller that triggers red alert every X seconds."""
    
    def __init__(self, interval_seconds=10):
        self.app = QApplication(sys.argv)
        self.interval = interval_seconds * 1000
        self.alert = None
        
        # Start first alert immediately
        self.show_alert()
        
        # Setup timer for recurring alerts
        self.timer = QTimer()
        self.timer.timeout.connect(self.show_alert)
        self.timer.start(self.interval)
        
    def show_alert(self):
        """Show the red alert screen."""
        if self.alert:
            self.alert.close()
        self.alert = RedAlertScreen()
        self.alert.show()
        print("🚨 RED ALERT TRIGGERED!")
        
    def run(self):
        print("🚨 RED ALERT MODE ACTIVATED")
        print(f"Alert will trigger every {self.interval // 1000} seconds")
        print("Press Ctrl+C to stop")
        return self.app.exec()


if __name__ == "__main__":
    controller = RedAlertController(interval_seconds=10)
    sys.exit(controller.run())
