import sys
from PyQt6.QtCore import Qt, QPoint, QRectF, QTimer
from PyQt6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout, QPushButton, QApplication, QGraphicsDropShadowEffect
)
from PyQt6.QtGui import QColor, QPainter, QPainterPath, QPen, QBrush, QFont
from logger import debug_log


class SpeechBubbleWindow(QWidget):
    """
    Independent floating, frameless, topmost speech bubble window.
    Solves text clipping / overflow by dynamically resizing to fit any text
    and keeping itself within visible screen boundaries above the avatar.
    """
    def __init__(self, parent_avatar=None):
        super().__init__(parent_avatar)
        self.avatar = parent_avatar

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_AlwaysStackOnTop, True)

        self.pointer_size = 10
        self.tail_x_offset = 0  # Position of tail relative to bubble

        # Main Layout
        self.container = QWidget(self)
        self.container.setObjectName("bubbleContainer")

        layout = QVBoxLayout(self.container)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(6)

        # Title / Tag (for reminders e.g. "⏰ Reminder")
        self.title_label = QLabel()
        self.title_label.setObjectName("bubbleTitle")
        self.title_label.setWordWrap(True)
        self.title_label.hide()
        layout.addWidget(self.title_label)

        # Message Text
        self.msg_label = QLabel()
        self.msg_label.setObjectName("bubbleText")
        self.msg_label.setWordWrap(True)
        self.msg_label.setMaximumWidth(280)
        layout.addWidget(self.msg_label)

        # Action Buttons Layout (e.g. for reminders: "Done", "Snooze")
        self.btn_layout = QHBoxLayout()
        self.btn_layout.setSpacing(8)
        self.btn_layout.setContentsMargins(0, 6, 0, 2)
        layout.addLayout(self.btn_layout)

        # Stylesheet
        self.setStyleSheet("""
            #bubbleContainer {
                background-color: rgba(255, 255, 255, 250);
                border: 1.5px solid #c0c7d0;
                border-radius: 12px;
            }
            #bubbleTitle {
                font-family: sans-serif;
                font-size: 12px;
                font-weight: bold;
                color: #d90429;
            }
            #bubbleText {
                font-family: sans-serif;
                font-size: 13px;
                color: #2b2d42;
                line-height: 1.35;
            }
            QPushButton {
                background-color: #2b2d42;
                color: white;
                border: 1px solid #45475a;
                border-radius: 6px;
                padding: 6px 12px;
                font-size: 11px;
                font-weight: bold;
                min-width: 70px;
            }
            QPushButton:hover {
                background-color: #1e1e2e;
            }
            QPushButton#doneBtn {
                background-color: #2a9d8f;
                border-color: #2a9d8f;
                color: white;
            }
            QPushButton#doneBtn:hover {
                background-color: #21867a;
            }
            QPushButton#snoozeBtn {
                background-color: #e76f51;
                border-color: #e76f51;
                color: white;
            }
            QPushButton#snoozeBtn:hover {
                background-color: #d65a3b;
            }
        """)

        # Auto-dismiss timer
        self.dismiss_timer = QTimer(self)
        self.dismiss_timer.setSingleShot(True)
        def on_timeout():
            debug_log("SPEECH", "Speech bubble duration elapsed -> hiding bubble")
            self.hide()
        self.dismiss_timer.timeout.connect(on_timeout)

    def show_message(self, text, title=None, duration=4.5, actions=None):
        """
        Display a speech bubble above the avatar.
        actions: list of dicts [{'text': 'Done', 'callback': fn}, ...]
        If duration is 0 or None, it stays open permanently until user interacts.
        """
        if title:
            self.title_label.setText(title)
            self.title_label.show()
        else:
            self.title_label.hide()

        self.msg_label.setText(text)

        # Clear old action buttons
        while self.btn_layout.count():
            item = self.btn_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        # Add new action buttons if provided
        if actions:
            for act in actions:
                btn_text = act.get("text", "OK")
                btn = QPushButton(btn_text)
                btn.setFixedHeight(32)
                btn.setMinimumWidth(105)

                if act.get("is_done"):
                    btn.setStyleSheet("""
                        QPushButton {
                            background-color: #2a9d8f;
                            color: #ffffff;
                            border: 1px solid #21867a;
                            border-radius: 6px;
                            font-size: 12px;
                            font-weight: bold;
                            padding: 4px 12px;
                        }
                        QPushButton:hover {
                            background-color: #21867a;
                        }
                    """)
                elif act.get("is_snooze"):
                    btn.setStyleSheet("""
                        QPushButton {
                            background-color: #e76f51;
                            color: #ffffff;
                            border: 1px solid #d65a3b;
                            border-radius: 6px;
                            font-size: 12px;
                            font-weight: bold;
                            padding: 4px 12px;
                        }
                        QPushButton:hover {
                            background-color: #d65a3b;
                        }
                    """)
                else:
                    btn.setStyleSheet("""
                        QPushButton {
                            background-color: #2b2d42;
                            color: #ffffff;
                            border: 1px solid #45475a;
                            border-radius: 6px;
                            font-size: 12px;
                            font-weight: bold;
                            padding: 4px 12px;
                        }
                        QPushButton:hover {
                            background-color: #1e1e2e;
                        }
                    """)

                cb = act.get("callback")
                if cb:
                    def make_click_handler(c_fn, label):
                        return lambda checked: (debug_log("SPEECH_ACTION", f"Bubble button '{label}' clicked"), c_fn(), self.hide())
                    btn.clicked.connect(make_click_handler(cb, btn_text))
                else:
                    def make_simple_handler(label):
                        return lambda checked: (debug_log("SPEECH_ACTION", f"Bubble button '{label}' clicked (dismiss)"), self.hide())
                    btn.clicked.connect(make_simple_handler(btn_text))
                self.btn_layout.addWidget(btn)

        # Compute needed width to prevent text and button clipping
        text_w = self.msg_label.fontMetrics().horizontalAdvance(text) + 48
        min_w = max(240, text_w)
        if actions:
            btn_needed = (len(actions) * 115) + 36
            min_w = max(min_w, btn_needed, 280)
        min_w = min(min_w, 400)

        self.msg_label.setFixedWidth(min_w - 28)
        self.container.setFixedWidth(min_w)

        # Force layout to compute actual height with wrapped text & buttons
        self.container.layout().activate()
        content_h = max(self.container.layout().sizeHint().height(), 105 if actions else 55)

        total_w = min_w
        total_h = content_h + self.pointer_size + 6

        self.setFixedSize(total_w, total_h)
        self.container.setGeometry(0, 0, total_w, content_h)

        self.update_position()
        self.show()
        self.raise_()
        debug_log("SPEECH", f"Speech bubble displayed: size={total_w}x{total_h}px, duration={duration}s, actions={len(actions) if actions else 0}")

        if duration and duration > 0:
            self.dismiss_timer.start(int(duration * 1000))
        else:
            self.dismiss_timer.stop()

    def update_position(self):
        """Position the bubble above the avatar and clamp to screen bounds."""
        if not self.avatar:
            return

        screen = QApplication.primaryScreen()
        if not screen:
            return
        geom = screen.availableGeometry()

        avatar_center_x = self.avatar.x() + self.avatar.width() // 2
        avatar_top_y = self.avatar.y()

        bubble_w = self.width()
        bubble_h = self.height()

        # Ideal target: centered horizontally above avatar
        target_x = avatar_center_x - (bubble_w // 2)
        target_y = avatar_top_y - bubble_h - 4

        # Clamp horizontal position to screen
        margin = 12
        clamped_x = max(geom.x() + margin, min(geom.x() + geom.width() - bubble_w - margin, target_x))

        # Clamp vertical position: if going off screen top, place below avatar instead
        if target_y < geom.y() + margin:
            target_y = avatar_top_y + self.avatar.height() + 4

        # Calculate where the pointer tail should be relative to bubble
        self.tail_x_offset = avatar_center_x - clamped_x
        self.tail_x_offset = max(18, min(bubble_w - 18, self.tail_x_offset))

        self.move(int(clamped_x), int(target_y))
        self.raise_()

    def paintEvent(self, event):
        super().paintEvent(event)
        # Draw the triangle pointer pointing down to the avatar
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        tx = self.tail_x_offset
        by = self.container.height()

        path = QPainterPath()
        path.moveTo(tx - 7, by - 1)
        path.lineTo(tx, by + self.pointer_size - 1)
        path.lineTo(tx + 7, by - 1)
        path.closeSubpath()

        painter.setPen(QPen(QColor("#d0d7de"), 1.5))
        painter.setBrush(QBrush(QColor(255, 255, 255, 245)))
        painter.drawPath(path)
