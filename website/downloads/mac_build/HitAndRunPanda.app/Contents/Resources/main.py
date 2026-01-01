"""
Hit & Run Productivity Pet - A Desktop Widget for Windows & Mac
A cute panda that periodically reminds you to complete tasks.
Now with Red Alert mode and flexible time intervals!
"""

import sys
import json
import os
import platform
import random
from datetime import datetime
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QVBoxLayout,
    QHBoxLayout, QSystemTrayIcon, QMenu, QDialog, QScrollArea,
    QFrame, QLineEdit, QSpinBox, QListWidget, QMessageBox,
    QComboBox, QCheckBox, QTabWidget, QGroupBox
)
from PyQt6.QtCore import (
    Qt, QTimer, QPropertyAnimation, QPoint, QEasingCurve,
    pyqtProperty
)
from PyQt6.QtGui import QIcon, QPixmap, QAction, QFont, QTransform, QColor, QPalette
from PyQt6.QtNetwork import QLocalServer, QLocalSocket

# Platform detection
IS_MAC = platform.system() == "Darwin"
IS_WINDOWS = platform.system() == "Windows"

def get_font(size=10, weight=None):
    """Get platform-appropriate font."""
    family = "SF Pro" if IS_MAC else "Segoe UI"
    if weight:
        return QFont(family, size, weight)
    return QFont(family, size)

# Configuration defaults
CONFIG = {
    "character_size": 120,
    "walk_speed_ms": 2500,
    "frame_duration_ms": 150,
}

ASSETS_DIR = os.path.join(os.path.dirname(__file__), "assets")
HISTORY_FILE = os.path.join(os.path.dirname(__file__), "history.json")
SETTINGS_FILE = os.path.join(os.path.dirname(__file__), "settings.json")


def get_default_settings():
    """Get default settings."""
    return {
        "first_run": True,
        "panda_enabled": False,
        "panda_interval": 30,
        "panda_interval_unit": "seconds",  # seconds, minutes, hours, days
        "tasks": [
            "Did you drink water?",
            "Time to stretch!",
            "Take a quick break?",
            "Check your posture!",
            "Rest your eyes for 20 seconds?",
        ],
        "red_alert_enabled": False,
        "red_alert_interval": 1,
        "red_alert_interval_unit": "hours",
        "red_alert_message": "DRINK WATER NOW!"
    }


def load_settings():
    """Load settings from JSON file."""
    defaults = get_default_settings()
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r") as f:
                saved = json.load(f)
                defaults.update(saved)
        except (json.JSONDecodeError, IOError):
            pass
    return defaults


def save_settings(settings):
    """Save settings to JSON file."""
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f, indent=2)


def interval_to_ms(value: int, unit: str) -> int:
    """Convert interval to milliseconds."""
    multipliers = {
        "seconds": 1000,
        "minutes": 60 * 1000,
        "hours": 60 * 60 * 1000,
        "days": 24 * 60 * 60 * 1000
    }
    return value * multipliers.get(unit, 1000)


def load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r") as f:
                return json.load(f)
        except:
            return []
    return []


def save_history(history):
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=2)


def log_task(task: str, completed: bool):
    history = load_history()
    history.append({
        "task": task,
        "completed": completed,
        "timestamp": datetime.now().isoformat()
    })
    save_history(history)


class SpriteManager:
    """Manages loading and caching of sprite images."""
    
    def __init__(self, size: int):
        self.size = size
        self.sprites = {}
        self.load_sprites()
        
    def load_sprites(self):
        # Walking frames (1-4)
        self.sprites["walk"] = []
        for i in range(1, 5):
            path = os.path.join(ASSETS_DIR, f"walking panda {i}.png")
            pixmap = QPixmap(path).scaled(
                self.size, self.size,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.sprites["walk"].append(pixmap)
        
        # Victory frames (1-3)
        self.sprites["victory"] = []
        for i in range(1, 4):
            path = os.path.join(ASSETS_DIR, f"victory panda {i}.png")
            pixmap = QPixmap(path).scaled(
                self.size, self.size,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.sprites["victory"].append(pixmap)
        
        # Angry & crying
        path = os.path.join(ASSETS_DIR, "angry panda.png")
        self.sprites["angry"] = QPixmap(path).scaled(self.size, self.size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        
        path = os.path.join(ASSETS_DIR, "crying panda.png")
        self.sprites["crying"] = QPixmap(path).scaled(self.size, self.size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        
        # Mirrored walking frames
        self.sprites["walk_mirror"] = []
        transform = QTransform().scale(-1, 1)
        for pixmap in self.sprites["walk"]:
            self.sprites["walk_mirror"].append(pixmap.transformed(transform))
    
    def get_walk_frame(self, index: int, mirrored: bool = False) -> QPixmap:
        frames = self.sprites["walk_mirror"] if mirrored else self.sprites["walk"]
        return frames[index % len(frames)]
    
    def get_victory_frame(self, index: int) -> QPixmap:
        return self.sprites["victory"][index % len(self.sprites["victory"])]
    
    def get_angry(self) -> QPixmap:
        return self.sprites["angry"]
    
    def get_crying(self) -> QPixmap:
        return self.sprites["crying"]


class CharacterWidget(QWidget):
    """The animated panda character."""
    
    def __init__(self, sprite_manager: SpriteManager):
        super().__init__()
        self.sprites = sprite_manager
        self._pos = QPoint(0, 0)
        self.walk_frame = 0
        self.is_mirrored = False
        self.current_state = "idle"
        self.coming_from_left = False
        
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self.size = CONFIG["character_size"]
        self.setFixedSize(self.size, self.size)
        
        self.image_label = QLabel(self)
        self.image_label.setFixedSize(self.size, self.size)
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.frame_timer = QTimer()
        self.frame_timer.timeout.connect(self.next_frame)
        
        self.victory_cycle = 0
        self.victory_jumping = False
        
        self.set_frame(self.sprites.get_walk_frame(0))
        
    def set_frame(self, pixmap: QPixmap):
        self.image_label.setPixmap(pixmap)
        
    def next_frame(self):
        if self.current_state == "walking":
            self.walk_frame = (self.walk_frame + 1) % 4
            self.set_frame(self.sprites.get_walk_frame(self.walk_frame, self.is_mirrored))
        elif self.current_state == "victory":
            if not self.victory_jumping:
                self.set_frame(self.sprites.get_victory_frame(0))
                self.victory_jumping = True
                self.victory_cycle = 0
            else:
                jump_frame = 1 + (self.victory_cycle % 2)
                self.set_frame(self.sprites.get_victory_frame(jump_frame))
                self.victory_cycle += 1
    
    def start_walking(self, mirrored: bool = False):
        self.current_state = "walking"
        self.is_mirrored = mirrored
        self.walk_frame = 0
        self.frame_timer.start(CONFIG["frame_duration_ms"])
        
    def start_victory(self):
        self.current_state = "victory"
        self.victory_jumping = False
        self.victory_cycle = 0
        self.frame_timer.start(CONFIG["frame_duration_ms"] + 50)
        
    def show_angry(self):
        self.current_state = "angry"
        self.frame_timer.stop()
        self.set_frame(self.sprites.get_angry())
        
    def show_crying(self):
        self.current_state = "crying"
        self.frame_timer.stop()
        self.set_frame(self.sprites.get_crying())
        
    def stop_animation(self):
        self.frame_timer.stop()
        self.current_state = "idle"
    
    @pyqtProperty(QPoint)
    def pos(self):
        return self._pos
    
    @pos.setter
    def pos(self, value):
        self._pos = value
        self.move(value)


class SpeechBubble(QWidget):
    """Speech bubble with task and YES/NO buttons."""
    
    def __init__(self, task: str, on_yes, on_no, from_left: bool = False):
        super().__init__()
        self.from_left = from_left
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setup_ui(task, on_yes, on_no)
        
    def setup_ui(self, task: str, on_yes, on_no):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        
        container = QFrame()
        container.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 15px;
                border: 3px solid #333;
            }
        """)
        container_layout = QVBoxLayout(container)
        container_layout.setSpacing(12)
        
        task_label = QLabel(task)
        task_label.setWordWrap(True)
        task_label.setFont(get_font(11))
        task_label.setStyleSheet("color: #333; border: none;")
        task_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        container_layout.addWidget(task_label)
        
        btn_layout = QHBoxLayout()
        
        yes_btn = QPushButton("YES ✓")
        yes_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        yes_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50; color: white; border: none;
                padding: 10px 25px; border-radius: 10px; font-weight: bold; font-size: 13px;
            }
            QPushButton:hover { background-color: #45a049; }
        """)
        yes_btn.clicked.connect(on_yes)
        
        no_btn = QPushButton("NO ✗")
        no_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        no_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336; color: white; border: none;
                padding: 10px 25px; border-radius: 10px; font-weight: bold; font-size: 13px;
            }
            QPushButton:hover { background-color: #da190b; }
        """)
        no_btn.clicked.connect(on_no)
        
        btn_layout.addWidget(yes_btn)
        btn_layout.addWidget(no_btn)
        container_layout.addLayout(btn_layout)
        
        layout.addWidget(container)
        self.setFixedSize(240, 130)


class RedAlertScreen(QWidget):
    """Full screen horror red alert."""
    
    def __init__(self, message: str, on_dismiss):
        super().__init__()
        self.on_dismiss_callback = on_dismiss
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint
        )
        self.showFullScreen()
        
        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor("#1a0000"))
        self.setPalette(palette)
        
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.warning = QLabel("⚠ WARNING ⚠")
        self.warning.setFont(QFont("Impact", 60, QFont.Weight.Bold))
        self.warning.setStyleSheet("color: #ff0000;")
        self.warning.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.warning)
        
        self.message_label = QLabel(message)
        self.message_label.setFont(QFont("Impact", 100, QFont.Weight.Bold))
        self.message_label.setStyleSheet("color: #ff0000;")
        self.message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.message_label)
        
        self.subtext = QLabel("DO IT NOW!")
        self.subtext.setFont(QFont("Arial", 30))
        self.subtext.setStyleSheet("color: #880000;")
        self.subtext.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.subtext)
        
        btn = QPushButton("I WILL DO IT")
        btn.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet("""
            QPushButton {
                background-color: #330000; color: #ff0000;
                border: 3px solid #ff0000; padding: 20px 50px; margin-top: 50px;
            }
            QPushButton:hover { background-color: #ff0000; color: #000000; }
        """)
        btn.clicked.connect(self.dismiss)
        layout.addWidget(btn, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # ESC hint
        esc_hint = QLabel("(Press ESC or click button to close)")
        esc_hint.setStyleSheet("color: #550000; margin-top: 20px;")
        esc_hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(esc_hint)
        
        self.flash_timer = QTimer()
        self.flash_timer.timeout.connect(self.flash)
        self.flash_timer.start(100)
        self.flash_state = False
        
        self.shake_timer = QTimer()
        self.shake_timer.timeout.connect(self.shake_text)
        self.shake_timer.start(50)
    
    def keyPressEvent(self, event):
        """Close on ESC key."""
        if event.key() == Qt.Key.Key_Escape:
            self.dismiss()
        
    def flash(self):
        self.flash_state = not self.flash_state
        palette = self.palette()
        color = "#2a0000" if self.flash_state else "#0a0000"
        palette.setColor(QPalette.ColorRole.Window, QColor(color))
        self.setPalette(palette)
        
    def shake_text(self):
        ox, oy = random.randint(-5, 5), random.randint(-3, 3)
        self.message_label.setStyleSheet(f"color: #ff0000; margin-left: {ox}px; margin-top: {oy}px;")
        
    def dismiss(self):
        """Stop everything and close."""
        self.flash_timer.stop()
        self.shake_timer.stop()
        self.hide()
        self.close()
        self.deleteLater()
        if self.on_dismiss_callback:
            self.on_dismiss_callback()


class HistoryDialog(QDialog):
    """Dialog showing task completion history."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Task History")
        self.setFixedSize(400, 500)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        history = load_history()
        completed = sum(1 for h in history if h["completed"])
        missed = len(history) - completed
        
        stats_label = QLabel(f"✓ Completed: {completed}  |  ✗ Missed: {missed}")
        stats_label.setFont(get_font(12, QFont.Weight.Bold))
        stats_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        stats_label.setStyleSheet("padding: 10px; background-color: #f0f0f0; border-radius: 8px;")
        layout.addWidget(stats_label)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none;")
        
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setSpacing(5)
        
        for entry in reversed(history[-50:]):
            frame = QFrame()
            frame.setStyleSheet(f"QFrame {{ background-color: {'#e8f5e9' if entry['completed'] else '#ffebee'}; border-radius: 8px; padding: 5px; }}")
            
            h_layout = QHBoxLayout(frame)
            icon = "✓" if entry["completed"] else "✗"
            icon_label = QLabel(icon)
            icon_label.setFont(get_font(14))
            icon_label.setStyleSheet(f"color: {'#4CAF50' if entry['completed'] else '#f44336'};")
            h_layout.addWidget(icon_label)
            
            info_layout = QVBoxLayout()
            task_label = QLabel(entry["task"])
            task_label.setFont(get_font(10))
            try:
                dt = datetime.fromisoformat(entry["timestamp"])
                time_str = dt.strftime("%Y-%m-%d %H:%M")
            except:
                time_str = "Unknown"
            time_label = QLabel(time_str)
            time_label.setFont(get_font(8))
            time_label.setStyleSheet("color: #888;")
            info_layout.addWidget(task_label)
            info_layout.addWidget(time_label)
            h_layout.addLayout(info_layout)
            h_layout.addStretch()
            
            scroll_layout.addWidget(frame)
        
        if not history:
            empty = QLabel("No history yet!\nThe panda will visit you soon.")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty.setStyleSheet("color: #888; padding: 20px;")
            scroll_layout.addWidget(empty)
        
        scroll_layout.addStretch()
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)


class SettingsDialog(QDialog):
    """Settings dashboard with tabs for Panda and Red Alert."""
    
    def __init__(self, controller, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.setWindowTitle("🐼 Hit & Run Panda - Settings")
        self.setFixedSize(500, 650)
        # Make it show in taskbar and stay on top
        self.setWindowFlags(
            Qt.WindowType.Window |
            Qt.WindowType.WindowStaysOnTopHint
        )
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Title header
        title = QLabel("🐼 Hit & Run Panda")
        title.setFont(get_font(18, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: #333; padding: 10px;")
        layout.addWidget(title)
        
        # Tabs
        tabs = QTabWidget()
        tabs.addTab(self.create_panda_tab(), "🐼 Panda")
        tabs.addTab(self.create_red_alert_tab(), "🚨 Red Alert")
        layout.addWidget(tabs)
        
        # Save button
        save_btn = QPushButton("💾 Save All Settings")
        save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        save_btn.setFont(get_font(12, QFont.Weight.Bold))
        save_btn.setStyleSheet("""
            QPushButton { background-color: #2196F3; color: white; border: none; padding: 15px; border-radius: 10px; }
            QPushButton:hover { background-color: #1976D2; }
        """)
        save_btn.clicked.connect(self.save_all)
        layout.addWidget(save_btn)
        
    def create_panda_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)
        
        # Enable checkbox
        self.panda_enabled = QCheckBox("Enable Panda Reminders 🐼")
        self.panda_enabled.setFont(get_font(12, QFont.Weight.Bold))
        self.panda_enabled.setChecked(self.controller.settings.get("panda_enabled", False))
        layout.addWidget(self.panda_enabled)
        
        # Interval section
        interval_group = QGroupBox("Reminder Interval")
        interval_layout = QHBoxLayout(interval_group)
        
        self.panda_interval = QSpinBox()
        self.panda_interval.setRange(1, 999)
        self.panda_interval.setValue(self.controller.settings.get("panda_interval", 30))
        self.panda_interval.setFont(get_font(11))
        interval_layout.addWidget(self.panda_interval)
        
        self.panda_unit = QComboBox()
        self.panda_unit.addItems(["seconds", "minutes", "hours", "days"])
        self.panda_unit.setCurrentText(self.controller.settings.get("panda_interval_unit", "seconds"))
        self.panda_unit.setFont(get_font(11))
        interval_layout.addWidget(self.panda_unit)
        interval_layout.addStretch()
        
        layout.addWidget(interval_group)
        
        # Tasks section
        tasks_label = QLabel("Tasks (panda will ask these):")
        tasks_label.setFont(get_font(11, QFont.Weight.Bold))
        layout.addWidget(tasks_label)
        
        add_layout = QHBoxLayout()
        self.task_input = QLineEdit()
        self.task_input.setPlaceholderText("Type a new task...")
        self.task_input.setFont(get_font(10))
        self.task_input.setStyleSheet("padding: 8px; border: 2px solid #ddd; border-radius: 8px;")
        self.task_input.returnPressed.connect(self.add_task)
        add_layout.addWidget(self.task_input)
        
        add_btn = QPushButton("+ Add")
        add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_btn.setStyleSheet("background-color: #4CAF50; color: white; border: none; padding: 8px 15px; border-radius: 8px;")
        add_btn.clicked.connect(self.add_task)
        add_layout.addWidget(add_btn)
        layout.addLayout(add_layout)
        
        self.task_list = QListWidget()
        self.task_list.setFont(get_font(10))
        self.task_list.setStyleSheet("border: 2px solid #ddd; border-radius: 8px; padding: 5px;")
        for task in self.controller.settings.get("tasks", []):
            self.task_list.addItem(task)
        layout.addWidget(self.task_list)
        
        delete_btn = QPushButton("🗑️ Delete Selected")
        delete_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        delete_btn.setStyleSheet("background-color: #f44336; color: white; border: none; padding: 8px 15px; border-radius: 8px;")
        delete_btn.clicked.connect(lambda: self.task_list.takeItem(self.task_list.currentRow()) if self.task_list.currentRow() >= 0 else None)
        layout.addWidget(delete_btn)
        
        return widget
        
    def create_red_alert_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)
        
        # Enable checkbox
        self.red_alert_enabled = QCheckBox("Enable Red Alert Mode 🚨")
        self.red_alert_enabled.setFont(get_font(12, QFont.Weight.Bold))
        self.red_alert_enabled.setChecked(self.controller.settings.get("red_alert_enabled", False))
        layout.addWidget(self.red_alert_enabled)
        
        # Description
        desc = QLabel("Full-screen aggressive reminder that demands attention!")
        desc.setStyleSheet("color: #666; font-style: italic;")
        layout.addWidget(desc)
        
        # Interval
        interval_group = QGroupBox("Red Alert Interval")
        interval_layout = QHBoxLayout(interval_group)
        
        self.red_interval = QSpinBox()
        self.red_interval.setRange(1, 999)
        self.red_interval.setValue(self.controller.settings.get("red_alert_interval", 1))
        self.red_interval.setFont(get_font(11))
        interval_layout.addWidget(self.red_interval)
        
        self.red_unit = QComboBox()
        self.red_unit.addItems(["seconds", "minutes", "hours", "days"])
        self.red_unit.setCurrentText(self.controller.settings.get("red_alert_interval_unit", "hours"))
        self.red_unit.setFont(get_font(11))
        interval_layout.addWidget(self.red_unit)
        interval_layout.addStretch()
        
        layout.addWidget(interval_group)
        
        # Message
        msg_group = QGroupBox("Alert Message")
        msg_layout = QVBoxLayout(msg_group)
        
        self.red_message = QLineEdit()
        self.red_message.setText(self.controller.settings.get("red_alert_message", "DRINK WATER NOW!"))
        self.red_message.setFont(get_font(12))
        self.red_message.setStyleSheet("padding: 10px; border: 2px solid #f44336; border-radius: 8px;")
        msg_layout.addWidget(self.red_message)
        
        layout.addWidget(msg_group)
        
        # Test button
        test_btn = QPushButton("🚨 Test Red Alert")
        test_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        test_btn.setFont(get_font(11, QFont.Weight.Bold))
        test_btn.setStyleSheet("""
            QPushButton { background-color: #f44336; color: white; border: none; padding: 12px; border-radius: 8px; }
            QPushButton:hover { background-color: #d32f2f; }
        """)
        test_btn.clicked.connect(self.test_red_alert)
        layout.addWidget(test_btn)
        
        layout.addStretch()
        return widget
        
    def add_task(self):
        task = self.task_input.text().strip()
        if task:
            self.task_list.addItem(task)
            self.task_input.clear()
            
    def test_red_alert(self):
        msg = self.red_message.text() or "TEST ALERT!"
        self.controller.show_red_alert(msg)
            
    def save_all(self):
        tasks = [self.task_list.item(i).text() for i in range(self.task_list.count())]
        if not tasks:
            QMessageBox.warning(self, "Warning", "You need at least one task!")
            return
        
        # Mark first run as complete
        self.controller.settings["first_run"] = False
        self.controller.is_first_run = False
        
        self.controller.settings["panda_enabled"] = self.panda_enabled.isChecked()
        self.controller.settings["panda_interval"] = self.panda_interval.value()
        self.controller.settings["panda_interval_unit"] = self.panda_unit.currentText()
        self.controller.settings["tasks"] = tasks
        self.controller.settings["red_alert_enabled"] = self.red_alert_enabled.isChecked()
        self.controller.settings["red_alert_interval"] = self.red_interval.value()
        self.controller.settings["red_alert_interval_unit"] = self.red_unit.currentText()
        self.controller.settings["red_alert_message"] = self.red_message.text()
        
        save_settings(self.controller.settings)
        self.controller.update_timers()
        
        QMessageBox.information(self, "Saved", "Settings saved! 🐼")
        self.close()


class PetController:
    """Main controller for the productivity pet."""
    
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False)
        
        self.settings = load_settings()
        self.is_first_run = self.settings.get("first_run", True)
        
        self.sprite_manager = SpriteManager(CONFIG["character_size"])
        
        self.character = CharacterWidget(self.sprite_manager)
        self.bubble = None
        self.red_alert_screen = None
        self.current_task = ""
        self.task_index = 0
        self.is_busy = False
        self.coming_from_left = False
        
        # Screen geometry
        screen = self.app.primaryScreen().availableGeometry()
        self.screen_width = screen.width()
        self.screen_height = screen.height()
        self.char_size = CONFIG["character_size"]
        
        # Positions for both sides
        self.bottom_y = self.screen_height - self.char_size - 50
        
        self.setup_tray()
        
        # Panda timer
        self.panda_timer = QTimer()
        self.panda_timer.timeout.connect(self.trigger_reminder)
        
        # Red alert timer
        self.red_alert_timer = QTimer()
        self.red_alert_timer.timeout.connect(self.trigger_red_alert)
        
        # Only start timers if not first run
        if not self.is_first_run:
            self.update_timers()
        
        # Walk animation
        self.walk_animation = QPropertyAnimation(self.character, b"pos")
        self.walk_animation.setEasingCurve(QEasingCurve.Type.Linear)
        self.walk_animation.setDuration(CONFIG["walk_speed_ms"])
        
        # IPC server
        self.server = QLocalServer()
        self.server.removeServer("HitAndRunPanda")
        self.server.listen("HitAndRunPanda")
        self.server.newConnection.connect(self.handle_cli_command)
        
    def setup_tray(self):
        self.tray = QSystemTrayIcon()
        icon_path = os.path.join(ASSETS_DIR, "walking panda 1.png")
        self.tray.setIcon(QIcon(icon_path))
        
        menu = QMenu()
        
        show_action = QAction("🐼 Show Panda Now", menu)
        show_action.triggered.connect(self.trigger_reminder)
        menu.addAction(show_action)
        
        menu.addSeparator()
        
        settings_action = QAction("⚙️ Settings", menu)
        settings_action.triggered.connect(self.show_settings)
        menu.addAction(settings_action)
        
        history_action = QAction("📊 History", menu)
        history_action.triggered.connect(self.show_history)
        menu.addAction(history_action)
        
        menu.addSeparator()
        
        red_alert_action = QAction("🚨 Test Red Alert", menu)
        red_alert_action.triggered.connect(self.trigger_red_alert)
        menu.addAction(red_alert_action)
        
        menu.addSeparator()
        
        quit_action = QAction("❌ Quit", menu)
        quit_action.triggered.connect(self.quit_app)
        menu.addAction(quit_action)
        
        self.tray.setContextMenu(menu)
        self.tray.setToolTip("Hit & Run Panda")
        self.tray.show()
        
    def update_timers(self):
        # Panda timer - only if enabled
        if self.settings.get("panda_enabled", False):
            panda_ms = interval_to_ms(
                self.settings.get("panda_interval", 30),
                self.settings.get("panda_interval_unit", "seconds")
            )
            self.panda_timer.setInterval(panda_ms)
            self.panda_timer.start()
        else:
            self.panda_timer.stop()
        
        # Red alert timer
        if self.settings.get("red_alert_enabled", False):
            red_ms = interval_to_ms(
                self.settings.get("red_alert_interval", 1),
                self.settings.get("red_alert_interval_unit", "hours")
            )
            self.red_alert_timer.setInterval(red_ms)
            self.red_alert_timer.start()
        else:
            self.red_alert_timer.stop()
            
    def get_positions(self, from_left: bool):
        """Get start, on-screen, and exit positions based on direction."""
        if from_left:
            off_screen = QPoint(-self.char_size - 50, self.bottom_y)
            on_screen = QPoint(50, self.bottom_y)
        else:
            off_screen = QPoint(self.screen_width + 50, self.bottom_y)
            on_screen = QPoint(self.screen_width - self.char_size - 50, self.bottom_y)
        return off_screen, on_screen
        
    def trigger_reminder(self):
        if self.is_busy:
            return
        self.is_busy = True
        
        # Random side
        self.coming_from_left = random.choice([True, False])
        
        tasks = self.settings.get("tasks", ["Did you drink water?"])
        self.current_task = tasks[self.task_index % len(tasks)]
        self.task_index += 1
        
        off_pos, on_pos = self.get_positions(self.coming_from_left)
        self.current_on_pos = on_pos
        self.current_off_pos = off_pos
        
        self.character.move(off_pos)
        self.character.show()
        
        # Walking: mirrored if coming from left (facing right)
        self.character.start_walking(mirrored=self.coming_from_left)
        
        self.walk_animation.setStartValue(off_pos)
        self.walk_animation.setEndValue(on_pos)
        self.walk_animation.finished.connect(self.on_arrived)
        self.walk_animation.start()
        
    def on_arrived(self):
        try:
            self.walk_animation.finished.disconnect(self.on_arrived)
        except:
            pass
        
        self.character.stop_animation()
        self.character.set_frame(self.sprite_manager.get_walk_frame(0, mirrored=self.coming_from_left))
        
        self.bubble = SpeechBubble(self.current_task, self.on_yes, self.on_no, self.coming_from_left)
        
        # Position bubble based on side
        if self.coming_from_left:
            bubble_x = self.current_on_pos.x() + self.char_size + 10
        else:
            bubble_x = self.current_on_pos.x() - 160
        bubble_y = self.current_on_pos.y() - 50
        
        self.bubble.move(bubble_x, bubble_y)
        self.bubble.show()
        
    def on_yes(self):
        log_task(self.current_task, True)
        self.hide_bubble()
        self.character.start_victory()
        QTimer.singleShot(1500, self.walk_off_screen)
        
    def on_no(self):
        log_task(self.current_task, False)
        self.hide_bubble()
        if random.choice([True, False]):
            self.character.show_angry()
        else:
            self.character.show_crying()
        QTimer.singleShot(1500, self.walk_off_screen)
        
    def hide_bubble(self):
        if self.bubble:
            self.bubble.hide()
            self.bubble.deleteLater()
            self.bubble = None
        
    def walk_off_screen(self):
        self.character.stop_animation()
        # Walk back the way it came (mirrored = NOT coming_from_left now)
        self.character.start_walking(mirrored=not self.coming_from_left)
        
        self.walk_animation.setStartValue(self.current_on_pos)
        self.walk_animation.setEndValue(self.current_off_pos)
        self.walk_animation.finished.connect(self.on_left)
        self.walk_animation.start()
        
    def on_left(self):
        try:
            self.walk_animation.finished.disconnect(self.on_left)
        except:
            pass
        self.character.stop_animation()
        self.character.hide()
        self.is_busy = False
        
    def trigger_red_alert(self):
        msg = self.settings.get("red_alert_message", "DRINK WATER NOW!")
        self.show_red_alert(msg)
        
    def show_red_alert(self, message: str):
        if self.red_alert_screen:
            self.red_alert_screen.close()
        self.red_alert_screen = RedAlertScreen(message, self.on_red_alert_dismiss)
        self.red_alert_screen.show()
        
    def on_red_alert_dismiss(self):
        self.red_alert_screen = None
        
    def show_history(self):
        dialog = HistoryDialog()
        dialog.exec()
    
    def show_settings(self):
        dialog = SettingsDialog(self)
        dialog.exec()
        
    def quit_app(self):
        self.server.close()
        self.tray.hide()
        self.app.quit()
    
    def handle_cli_command(self):
        socket = self.server.nextPendingConnection()
        if socket and socket.waitForReadyRead(1000):
            cmd = socket.readAll().data().decode().strip()
            if cmd == "show":
                self.trigger_reminder()
            elif cmd == "settings":
                self.show_settings()
            elif cmd == "history":
                self.show_history()
            elif cmd == "redalert":
                self.trigger_red_alert()
            socket.write(b"ok")
            socket.flush()
            socket.disconnectFromServer()
        
    def run(self):
        # Show settings on first run - IMMEDIATELY and blocking
        if self.is_first_run:
            print("🐼 First run! Opening settings...")
            self.show_first_run_settings()
        else:
            if self.settings.get("panda_enabled"):
                interval = self.settings.get("panda_interval", 30)
                unit = self.settings.get("panda_interval_unit", "seconds")
                print(f"🐼 Panda enabled: every {interval} {unit}")
            else:
                print("🐼 Panda is disabled. Right-click tray icon → Settings to enable.")
            if self.settings.get("red_alert_enabled"):
                r_int = self.settings.get("red_alert_interval", 1)
                r_unit = self.settings.get("red_alert_interval_unit", "hours")
                print(f"🚨 Red Alert enabled: every {r_int} {r_unit}")
        return self.app.exec()
    
    def show_first_run_settings(self):
        """Show settings dialog on first run."""
        msg = QMessageBox()
        msg.setWindowTitle("Welcome! 🐼")
        msg.setText("Welcome to Hit & Run Panda!")
        msg.setInformativeText(
            "Configure your reminders in the settings.\n"
            "Check 'Enable Panda Reminders' and save!"
        )
        msg.setIcon(QMessageBox.Icon.Information)
        msg.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint)
        msg.exec()
        
        # Show settings dialog
        dialog = SettingsDialog(self)
        dialog.activateWindow()
        dialog.raise_()
        dialog.exec()


def send_command(cmd: str) -> bool:
    app = QApplication(sys.argv)
    socket = QLocalSocket()
    socket.connectToServer("HitAndRunPanda")
    if socket.waitForConnected(1000):
        socket.write(cmd.encode())
        socket.flush()
        socket.waitForReadyRead(1000)
        socket.disconnectFromServer()
        return True
    return False


if __name__ == "__main__":
    if len(sys.argv) > 1:
        cmd = sys.argv[1].lower()
        if cmd in ("show", "settings", "history", "redalert"):
            if send_command(cmd):
                print(f"✓ Sent '{cmd}'")
            else:
                print("✗ Panda not running! Start with: python main.py")
            sys.exit(0)
        else:
            print("Usage: python main.py [show|settings|history|redalert]")
            sys.exit(1)
    
    controller = PetController()
    sys.exit(controller.run())
