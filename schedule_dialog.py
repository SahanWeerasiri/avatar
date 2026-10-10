import time
from datetime import datetime
from PyQt6.QtCore import Qt, QTimer, QTime
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTimeEdit, QSpinBox, QComboBox, QListWidget, QListWidgetItem, QWidget,
    QTabWidget, QGroupBox, QFrame
)
from logger import debug_log


class ScheduleDialog(QDialog):
    """
    Modern GUI dialog to add, schedule, and view tasks and timers.
    """
    def __init__(self, scheduler, on_tasks_updated=None, parent=None):
        super().__init__(parent)
        self.scheduler = scheduler
        self.on_tasks_updated = on_tasks_updated

        self.setWindowTitle("📅 Avatar Work & Reminder Scheduler")
        self.resize(520, 560)
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, False)

        # Apply clean dark theme styling
        self.setStyleSheet("""
            QDialog {
                background-color: #1e1e2e;
                color: #cdd6f4;
                font-family: sans-serif;
            }
            QLabel {
                color: #cdd6f4;
                font-size: 13px;
            }
            QLineEdit, QSpinBox, QTimeEdit, QComboBox {
                background-color: #313244;
                color: #cdd6f4;
                border: 1px solid #45475a;
                border-radius: 6px;
                padding: 6px 10px;
                font-size: 13px;
            }
            QLineEdit:focus, QSpinBox:focus, QTimeEdit:focus, QComboBox:focus {
                border: 1px solid #cba6f7;
            }
            QPushButton {
                background-color: #45475a;
                color: #cdd6f4;
                border: none;
                border-radius: 6px;
                padding: 7px 14px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #585b70;
            }
            QPushButton#primaryBtn {
                background-color: #f38ba8;
                color: #11111b;
            }
            QPushButton#primaryBtn:hover {
                background-color: #eba0ac;
            }
            QPushButton#quickBtn {
                background-color: #313244;
                border: 1px solid #45475a;
                color: #cdd6f4;
                padding: 8px;
                border-radius: 8px;
            }
            QPushButton#quickBtn:hover {
                background-color: #45475a;
                border-color: #89b4fa;
            }
            QGroupBox {
                border: 1px solid #313244;
                border-radius: 8px;
                margin-top: 14px;
                padding-top: 10px;
                font-weight: bold;
                color: #89b4fa;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 4px;
            }
            QListWidget {
                background-color: #181825;
                border: 1px solid #313244;
                border-radius: 8px;
                padding: 6px;
            }
        """)

        self._build_ui()

        # Update countdowns every second
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.populate_task_list)
        self.refresh_timer.start(1000)

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(18, 16, 18, 16)
        main_layout.setSpacing(14)

        # Header Title
        title_label = QLabel("✨ Avatar Personal Assistant & Work Scheduler")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #cba6f7;")
        main_layout.addWidget(title_label)

        # --- Quick Presets Section ---
        quick_group = QGroupBox("⚡ 1-Click Quick Timers")
        quick_layout = QHBoxLayout(quick_group)
        quick_layout.setSpacing(8)

        presets = [
            ("🍅 Pomodoro (25m)", 25, False, "work"),
            ("☕ Short Break (5m)", 5, False, "break"),
            ("💧 Hydrate (Every 30m)", 30, True, "health"),
            ("🧘 Stretch (45m)", 45, False, "health"),
        ]
        for label, mins, rec, cat in presets:
            btn = QPushButton(label)
            btn.setObjectName("quickBtn")
            btn.clicked.connect(lambda checked, l=label, m=mins, r=rec, c=cat: self.add_quick_preset(l, m, r, c))
            quick_layout.addWidget(btn)

        main_layout.addWidget(quick_group)

        # --- Custom Schedule Form ---
        custom_group = QGroupBox("➕ Schedule New Work / Reminder")
        form_layout = QVBoxLayout(custom_group)
        form_layout.setSpacing(10)

        # Task Name
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Title:"))
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("e.g. Review timetable, Submit report, Study session...")
        name_layout.addWidget(self.title_input)
        form_layout.addLayout(name_layout)

        # Timing Mode
        time_mode_layout = QHBoxLayout()
        time_mode_layout.addWidget(QLabel("Schedule by:"))

        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["In X Minutes", "At Specific Time (Today)", "Recurring Every X Minutes"])
        self.mode_combo.currentIndexChanged.connect(self.on_mode_changed)
        time_mode_layout.addWidget(self.mode_combo)

        # Minutes spinbox (for mode 0 and 2)
        self.mins_spin = QSpinBox()
        self.mins_spin.setRange(1, 1440)
        self.mins_spin.setValue(30)
        self.mins_spin.setSuffix(" mins")
        time_mode_layout.addWidget(self.mins_spin)

        # Time picker (for mode 1)
        self.time_picker = QTimeEdit()
        self.time_picker.setTime(QTime.currentTime().addSecs(1800))
        self.time_picker.hide()
        time_mode_layout.addWidget(self.time_picker)

        form_layout.addLayout(time_mode_layout)

        # Category and Add Button
        bottom_form_layout = QHBoxLayout()
        bottom_form_layout.addWidget(QLabel("Category:"))
        self.cat_combo = QComboBox()
        self.cat_combo.addItems(["work", "study", "health", "break", "general"])
        bottom_form_layout.addWidget(self.cat_combo)

        add_btn = QPushButton("Add to Schedule")
        add_btn.setObjectName("primaryBtn")
        add_btn.clicked.connect(self.add_custom_task)
        bottom_form_layout.addWidget(add_btn)

        form_layout.addLayout(bottom_form_layout)
        main_layout.addWidget(custom_group)

        # --- Active Tasks List ---
        list_header_layout = QHBoxLayout()
        list_label = QLabel("📋 Active Work & Scheduled Reminders:")
        list_label.setStyleSheet("font-weight: bold; color: #89b4fa;")
        list_header_layout.addWidget(list_label)

        list_header_layout.addStretch()
        main_layout.addLayout(list_header_layout)

        self.task_list = QListWidget()
        main_layout.addWidget(self.task_list)

        self.populate_task_list()

    def showEvent(self, event):
        super().showEvent(event)
        debug_log("DIALOG", "ScheduleDialog shown on screen")

    def closeEvent(self, event):
        super().closeEvent(event)
        debug_log("DIALOG", "ScheduleDialog closed")

    def on_mode_changed(self, index):
        debug_log("DIALOG", f"Schedule mode combo changed to index={index} ('{self.mode_combo.currentText()}')")
        if index == 1:  # Specific time
            self.mins_spin.hide()
            self.time_picker.show()
        else:
            self.mins_spin.show()
            self.time_picker.hide()

    def add_quick_preset(self, label, minutes, recurring, category):
        debug_log("DIALOG", f"Preset clicked: '{label}' ({minutes}m, recurring={recurring}, category={category})")
        self.scheduler.add_quick_timer(label, minutes, recurring=recurring, category=category)
        self.populate_task_list()
        if self.on_tasks_updated:
            self.on_tasks_updated(f"Added timer: {label}!")

    def add_custom_task(self):
        title = self.title_input.text().strip()
        if not title:
            debug_log("DIALOG", "Add custom task ignored: title is empty")
            return

        category = self.cat_combo.currentText()
        mode = self.mode_combo.currentIndex()
        debug_log("DIALOG", f"Adding custom task: '{title}', mode={mode}, category='{category}'")

        if mode == 0:  # In X minutes
            mins = self.mins_spin.value()
            self.scheduler.add_quick_timer(title, mins, recurring=False, category=category)
        elif mode == 1:  # Specific time today
            qtime = self.time_picker.time()
            now = datetime.now()
            target_dt = now.replace(hour=qtime.hour(), minute=qtime.minute(), second=0, microsecond=0)
            if target_dt.timestamp() <= time.time():
                # If target time is earlier today, set for tomorrow
                target_dt = target_dt.fromtimestamp(target_dt.timestamp() + 86400)
            self.scheduler.add_task(title, target_dt.timestamp(), category=category)
        elif mode == 2:  # Recurring
            mins = self.mins_spin.value()
            self.scheduler.add_quick_timer(title, mins, recurring=True, category=category)

        self.title_input.clear()
        self.populate_task_list()
        if self.on_tasks_updated:
            self.on_tasks_updated(f"Scheduled: '{title}'!")

    def populate_task_list(self):
        self.task_list.clear()
        active_tasks = self.scheduler.get_active_tasks()

        if not active_tasks:
            item = QListWidgetItem("No upcoming tasks. Add one above!")
            item.setFlags(Qt.ItemFlag.NoItemFlags)
            self.task_list.addItem(item)
            return

        for t in active_tasks:
            item = QListWidgetItem()
            widget = QWidget()
            layout = QHBoxLayout(widget)
            layout.setContentsMargins(8, 4, 8, 4)

            # Icon based on category
            cat_icons = {"work": "💼", "health": "💧", "break": "☕", "study": "📚", "general": "📌"}
            icon = cat_icons.get(t.category, "📌")

            rec_badge = " [🔁]" if t.recurring_min else ""
            info_text = f"{icon} <b>{t.title}</b>{rec_badge} <font color='#a6adc8'>({t.time_remaining_str()})</font>"
            label = QLabel(info_text)
            label.setTextFormat(Qt.TextFormat.RichText)
            layout.addWidget(label)

            layout.addStretch()

            # Done button
            done_btn = QPushButton("✔ Done")
            done_btn.setStyleSheet("background-color: #a6e3a1; color: #11111b; padding: 3px 8px; font-size: 11px;")
            done_btn.clicked.connect(lambda checked, tid=t.id: self.mark_done(tid))
            layout.addWidget(done_btn)

            # Snooze button
            snooze_btn = QPushButton("+5m")
            snooze_btn.setStyleSheet("background-color: #fab387; color: #11111b; padding: 3px 6px; font-size: 11px;")
            snooze_btn.clicked.connect(lambda checked, tid=t.id: self.snooze(tid))
            layout.addWidget(snooze_btn)

            # Delete button
            del_btn = QPushButton("🗑")
            del_btn.setStyleSheet("background-color: #f38ba8; color: #11111b; padding: 3px 6px; font-size: 11px;")
            del_btn.clicked.connect(lambda checked, tid=t.id: self.delete_task(tid))
            layout.addWidget(del_btn)

            item.setSizeHint(widget.sizeHint())
            self.task_list.addItem(item)
            self.task_list.setItemWidget(item, widget)

    def mark_done(self, task_id):
        debug_log("DIALOG", f"mark_done clicked for task id={task_id}")
        self.scheduler.complete_task(task_id)
        self.populate_task_list()
        if self.on_tasks_updated:
            self.on_tasks_updated("Great job finishing that task! 🎉")

    def snooze(self, task_id):
        debug_log("DIALOG", f"snooze clicked for task id={task_id}")
        self.scheduler.snooze_task(task_id, 5)
        self.populate_task_list()
        if self.on_tasks_updated:
            self.on_tasks_updated("Snoozed for 5 minutes! ⏰")

    def delete_task(self, task_id):
        debug_log("DIALOG", f"delete_task clicked for task id={task_id}")
        self.scheduler.delete_task(task_id)
        self.populate_task_list()
