import sys
import time
from PyQt6.QtCore import Qt, QTimer, QPoint
from PyQt6.QtWidgets import (
    QWidget, QMenu, QApplication
)
from PyQt6.QtGui import QCursor, QColor, QAction, QActionGroup

from character import AvatarCharacter
from behaviors import BehaviorManager
from speech_bubble import SpeechBubbleWindow
from scheduler import ScheduleManager
from schedule_dialog import ScheduleDialog
from logger import debug_log


class AvatarWindow(QWidget):
    """
    Transparent, frameless, topmost overlay window for the desktop avatar.
    Handles screen positioning, desktop boundaries, mouse dragging,
    gravity physics, and user interaction.
    """
    def __init__(self, size=160):
        super().__init__()
        self.avatar_size = size
        self.setFixedSize(self.avatar_size, self.avatar_size)

        # Setup transparent overlay window flags
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)

        # Precise floating point coordinates for smooth sub-pixel physics
        self.pos_x = 40.0
        self.pos_y = 0.0

        # Engine components
        self.character = AvatarCharacter(size=self.avatar_size)
        self.behavior = BehaviorManager(self.character)

        # Speech bubble overlay (non-clipped, floating, auto-wrapped)
        self.speech_bubble = SpeechBubbleWindow(self)
        self.character.on_speech_requested = self.say

        # Task and work scheduler
        self.scheduler = ScheduleManager()
        self.schedule_dialog = None
        self.last_scheduler_check = time.time()
        self.active_reminder = False

        # Physics
        self.gravity = 1400.0  # px/s^2
        self.fall_vy = 0.0
        self.is_falling = False

        # Dragging & click tracking
        self.is_dragging = False
        self.drag_start_pos = QPoint()
        self.drag_start_time = 0.0

        # Timing
        self.last_frame_time = time.time()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.game_loop)
        self.timer.start(16)  # ~60 FPS

        # Initial placement on screen floor (bottom-left)
        self.place_on_screen_floor()

        # Friendly initial greeting
        QTimer.singleShot(700, lambda: self.say(
            "Hi friend! I'm here to cheer for you and help schedule your tasks! ✨",
            title="✨ Ready to help!",
            duration=5.0
        ))

    def get_screen_bounds(self):
        screen = QApplication.primaryScreen()
        if screen:
            geom = screen.availableGeometry()
            return geom.x(), geom.y(), geom.width(), geom.height()
        return 0, 0, 1920, 1080

    def get_floor_y(self):
        _, sy, _, sh = self.get_screen_bounds()
        return sy + sh - self.avatar_size

    def place_on_screen_floor(self):
        """Place avatar near bottom-left so it walks to the corner and sleeps."""
        sx, _, sw, _ = self.get_screen_bounds()
        floor_y = self.get_floor_y()
        start_x = sx + 75
        self.pos_x = float(start_x)
        self.pos_y = float(floor_y)
        debug_log("WINDOW", f"Placing avatar on floor at ({self.pos_x:.1f}, {self.pos_y:.1f}) (screen bounds={self.get_screen_bounds()})")
        self.move(int(round(self.pos_x)), int(round(self.pos_y)))

    def change_size(self, new_size):
        debug_log("CONFIG", f"Changing avatar size from {self.avatar_size}px to {new_size}px")
        self.avatar_size = new_size
        self.setFixedSize(new_size, new_size)
        self.character = AvatarCharacter(size=new_size)
        self.behavior.character = self.character
        # Adjust floor position
        floor_y = self.get_floor_y()
        self.pos_y = float(floor_y)
        self.move(int(round(self.pos_x)), int(round(self.pos_y)))
        self.update()

    def set_color_theme(self, theme_name):
        themes = {
            "orange": (QColor(255, 160, 80), QColor(230, 130, 50), QColor(255, 245, 230)),
            "lavender": (QColor(185, 165, 235), QColor(150, 130, 205), QColor(250, 245, 255)),
            "sakura": (QColor(255, 182, 193), QColor(240, 150, 165), QColor(255, 245, 248)),
            "midnight": (QColor(70, 75, 95), QColor(45, 50, 70), QColor(230, 235, 245)),
            "snow": (QColor(245, 245, 250), QColor(210, 215, 225), QColor(255, 255, 255)),
        }
        if theme_name in themes:
            debug_log("CONFIG", f"Applying fur color theme '{theme_name}'")
            main, dark, belly = themes[theme_name]
            self.character.fur_main = main
            self.character.fur_dark = dark
            self.character.fur_belly = belly
            self.character.add_particle("sparkle")

    def game_loop(self):
        now = time.time()
        dt = min(0.05, now - self.last_frame_time)
        self.last_frame_time = now

        sx, _, sw, _ = self.get_screen_bounds()
        min_x = sx
        max_x = sx + sw - self.avatar_size
        floor_y = self.get_floor_y()

        # Mouse relative position for eye tracking
        cursor_pos = QCursor.pos()
        center_x = self.x() + self.avatar_size / 2
        center_y = self.y() + self.avatar_size / 2
        mouse_rel = (cursor_pos.x() - center_x, cursor_pos.y() - center_y)

        # Physics: Falling
        if self.character.state == "falling":
            self.fall_vy += self.gravity * dt
            self.pos_y += self.fall_vy * dt

            if self.pos_y >= floor_y:
                self.pos_y = float(floor_y)
                self.fall_vy = 0.0
                debug_log("PHYSICS", f"Landed on floor (y={self.pos_y:.1f}). Triggering squash bounce and waking up")
                self.character.trigger_landing_squish()
                self.behavior.wake_up(duration=20.0, reason="physics")
            self.move(int(round(self.pos_x)), int(round(self.pos_y)))
            if self.speech_bubble.isVisible():
                self.speech_bubble.update_position()

        # Autonomous horizontal walking
        elif not self.is_dragging:
            dx = self.behavior.update(dt, self.pos_x, min_x, max_x)
            if dx != 0:
                self.pos_x += dx
                self.pos_x = max(float(min_x), min(float(max_x), self.pos_x))
                self.move(int(round(self.pos_x)), int(round(self.pos_y)))
                if self.speech_bubble.isVisible():
                    self.speech_bubble.update_position()

        # Check due scheduled tasks
        if now - self.last_scheduler_check >= 1.0:
            self.last_scheduler_check = now
            due_tasks = self.scheduler.check_due_tasks()
            for t in due_tasks:
                debug_log("REMINDER", f"Due task triggered: '{t.title}' (id={t.id}, category={t.category}). Presenting reminder bubble.")
                self.active_reminder = True
                self.behavior.wake_up_for_reminder()
                for _ in range(5):
                    self.character.add_particle("sparkle")

                def make_done_cb(tid, title):
                    def cb():
                        debug_log("REMINDER", f"'Accept' clicked for task '{title}' (id={tid}). Completing task.")
                        self.active_reminder = False
                        self.scheduler.complete_task(tid)
                        self.say("Task completed! Going back to sleep~ 💤", duration=3.0, force=True)
                        QTimer.singleShot(2200, self.behavior.on_reminder_dismissed)
                    return cb

                def make_snooze_cb(tid, title):
                    def cb():
                        debug_log("REMINDER", f"'Snooze' clicked for task '{title}' (id={tid}). Snoozing for 5 minutes.")
                        self.active_reminder = False
                        self.scheduler.snooze_task(tid, 5)
                        self.say("Snoozed for 5 minutes! ⏰", duration=3.0, force=True)
                        QTimer.singleShot(2200, self.behavior.on_reminder_dismissed)
                    return cb

                actions = [
                    {"text": "Accept", "is_done": True, "callback": make_done_cb(t.id, t.title)},
                    {"text": "Snooze 5m", "is_snooze": True, "callback": make_snooze_cb(t.id, t.title)},
                ]
                # duration=0 keeps reminder window open indefinitely until user clicks!
                self.say(f"Time for: {t.title}!", title="⏰ Scheduled Reminder Due!", duration=0, actions=actions, force=True)

        # Update character animation state
        self.character.update(dt, mouse_rel)
        self.update()

    def say(self, text, duration=4.5, title=None, actions=None, force=False):
        """Displays text in the floating, auto-wrapped speech bubble."""
        if self.active_reminder and not force and not actions:
            debug_log("SPEECH", f"Speech suppressed because an active reminder is in progress: '{text}'")
            return
        act_names = [a.get("text") for a in actions] if actions else None
        debug_log("SPEECH", f"Avatar saying: '{text}' (title={title}, duration={duration}, actions={act_names}, force={force})")
        self.speech_bubble.show_message(text, title=title, duration=duration, actions=actions)

    def open_schedule_dialog(self):
        debug_log("UI_EVENT", "Opening Work & Reminder Scheduler dialog")
        self.behavior.wake_up(duration=60.0, reason="user")
        if self.schedule_dialog is None:
            self.schedule_dialog = ScheduleDialog(self.scheduler, on_tasks_updated=lambda msg: self.say(msg, duration=3.5))
        self.schedule_dialog.show()
        self.schedule_dialog.raise_()
        self.schedule_dialog.activateWindow()

    def start_quick_timer(self, title, minutes, category="work"):
        debug_log("TIMER", f"Starting quick timer: '{title}' ({minutes}m, category={category})")
        self.behavior.wake_up(duration=20.0, reason="user")
        self.scheduler.add_quick_timer(title, minutes, recurring=False, category=category)
        self.say(f"Timer started: {title} ({minutes}m)! I will alert you! ⏳", title="⏱ Timer Active", duration=4.0)

    def start_recurring_timer(self, title, minutes, category="health"):
        debug_log("TIMER", f"Starting recurring timer: '{title}' every {minutes}m (category={category})")
        self.behavior.wake_up(duration=20.0, reason="user")
        self.scheduler.add_quick_timer(title, minutes, recurring=True, category=category)
        self.say(f"Set recurring reminder: {title} every {minutes} mins! 💧", title="🔁 Recurring Set", duration=4.0)

    def speak_next_task(self):
        debug_log("UI_EVENT", "Querying next upcoming task from schedule")
        self.behavior.wake_up(duration=20.0, reason="user")
        active_tasks = self.scheduler.get_active_tasks()
        if active_tasks:
            next_t = active_tasks[0]
            count = len(active_tasks)
            extra = f" (+{count-1} more)" if count > 1 else ""
            msg = f"Next task: '{next_t.title}' ({next_t.time_remaining_str()}){extra}"
            debug_log("SCHEDULER", f"Found {count} active tasks. Next: '{next_t.title}' due at {next_t.due_time}")
            self.say(msg, title="📋 Work Schedule", duration=6.0, force=True)
        else:
            debug_log("SCHEDULER", "No active tasks found in schedule")
            self.say(
                "You have no tasks scheduled! Right-click and choose 'Schedule Work' to add one! ✨",
                title="📋 Work Schedule",
                duration=5.0,
                force=True
            )

    def paintEvent(self, event):
        from PyQt6.QtGui import QPainter
        painter = QPainter(self)
        self.character.draw(painter)

    # ---------------- Mouse Events ----------------
    def mousePressEvent(self, event):
        pos = event.position().toPoint()
        if event.button() == Qt.MouseButton.LeftButton:
            debug_log("MOUSE", f"Left mouse pressed at ({pos.x()}, {pos.y()}) -> starting drag")
            self.is_dragging = True
            self.drag_start_pos = pos
            self.drag_start_time = time.time()
            self.character.state = "dragged"
            self.behavior.wake_up(duration=25.0, reason="drag")
            self.fall_vy = 0.0
        elif event.button() == Qt.MouseButton.RightButton:
            debug_log("MOUSE", f"Right mouse pressed at ({pos.x()}, {pos.y()}) -> opening context menu")
            self.behavior.wake_up(duration=35.0, reason="menu")
            self.show_context_menu(event.globalPosition().toPoint())

    def mouseMoveEvent(self, event):
        if self.is_dragging:
            delta = event.position().toPoint() - self.drag_start_pos
            new_x = self.x() + delta.x()
            new_y = self.y() + delta.y()
            self.pos_x = float(new_x)
            self.pos_y = float(new_y)
            self.move(new_x, new_y)
            if self.speech_bubble.isVisible():
                self.speech_bubble.update_position()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.is_dragging:
            self.is_dragging = False
            duration = time.time() - self.drag_start_time
            floor_y = self.get_floor_y()
            debug_log("MOUSE", f"Left mouse released at ({self.pos_x:.1f}, {self.pos_y:.1f}), held for {duration:.3f}s (floor_y={floor_y:.1f})")

            # Click detection (quick release without long drag)
            if duration < 0.25 and abs(self.pos_y - floor_y) < 25:
                debug_log("MOUSE", f"Quick click detected ({duration:.3f}s) -> petting avatar & spawning hearts")
                self.behavior.wake_up(duration=25.0, reason="user")
                for _ in range(4):
                    self.character.add_particle("heart")
                return

            # Check if dropped in mid-air
            if self.pos_y < floor_y - 10:
                debug_log("PHYSICS", f"Dropped in mid-air (y={self.pos_y:.1f} < floor={floor_y:.1f}) -> starting gravity fall")
                self.character.state = "falling"
                self.fall_vy = 0.0
            else:
                debug_log("PHYSICS", f"Placed on floor -> landing squish")
                self.pos_y = float(floor_y)
                self.move(int(round(self.pos_x)), int(round(self.pos_y)))
                self.character.trigger_landing_squish()
                self.behavior.wake_up(duration=20.0, reason="physics")
            if self.speech_bubble.isVisible():
                self.speech_bubble.update_position()

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            debug_log("MOUSE", "Left double click detected -> opening schedule dialog")
            self.behavior.wake_up(duration=35.0, reason="user")
            for _ in range(5):
                self.character.add_particle("heart")
            self.open_schedule_dialog()

    def start_walking(self):
        debug_log("BEHAVIOR", "start_walking requested")
        self.behavior.wake_up(duration=30.0, reason="user")

    def show_context_menu(self, global_pos):
        debug_log("MENU", f"Opening context menu at global pos ({global_pos.x()}, {global_pos.y()})")
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #2b2d42;
                color: #edf2f4;
                border: 1px solid #8d99ae;
                border-radius: 8px;
                padding: 6px;
                font-family: sans-serif;
                font-size: 13px;
            }
            QMenu::item {
                padding: 6px 20px 6px 20px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #ef233c;
                color: white;
            }
            QMenu::separator {
                height: 1px;
                background: #8d99ae;
                margin: 4px 10px;
            }
        """)

        # Work & Reminder Scheduler Actions
        act_sched = menu.addAction("📅 Work & Reminder Scheduler...")
        act_sched.triggered.connect(lambda: (debug_log("MENU", "Selected: Work & Reminder Scheduler"), self.open_schedule_dialog()))

        act_next = menu.addAction("📋 What's Next on My Schedule?")
        act_next.triggered.connect(lambda: (debug_log("MENU", "Selected: What's Next on My Schedule"), self.speak_next_task()))

        # Quick Timer Submenu
        timer_menu = menu.addMenu("⏱ Quick Timers")
        timer_menu.setStyleSheet(menu.styleSheet())
        timer_menu.addAction("🍅 25m Pomodoro Focus").triggered.connect(lambda: (debug_log("MENU", "Selected Quick Timer: Pomodoro 25m"), self.start_quick_timer("🍅 Pomodoro Focus", 25, "work")))
        timer_menu.addAction("☕ 5m Short Break").triggered.connect(lambda: (debug_log("MENU", "Selected Quick Timer: Short Break 5m"), self.start_quick_timer("☕ Quick Break", 5, "break")))
        timer_menu.addAction("💧 Hydrate (Every 30m)").triggered.connect(lambda: (debug_log("MENU", "Selected Quick Timer: Hydrate 30m"), self.start_recurring_timer("💧 Drink Water", 30, "health")))
        timer_menu.addAction("🧘 45m Stretch Break").triggered.connect(lambda: (debug_log("MENU", "Selected Quick Timer: Stretch 45m"), self.start_quick_timer("🧘 Stretch & Relax", 45, "health")))

        menu.addSeparator()

        # Interaction Actions
        act_pet = menu.addAction("♥ Pet Avatar")
        act_pet.triggered.connect(lambda: (debug_log("MENU", "Selected: Pet Avatar"), self.behavior.set_state("happy")))

        act_talk = menu.addAction("💬 Say Something")
        import random
        quotes = [
            "You are doing great!",
            "Take a deep breath~",
            "I'm cheering for you! 🌟",
            "(=^･ω･^=) Meow!",
            "Let's stay productive today! ✨",
            "Don't forget to take short breaks!",
        ]
        act_talk.triggered.connect(lambda: (debug_log("MENU", "Selected: Say Something"), self.say(random.choice(quotes), 4.0)))

        menu.addSeparator()

        # State overrides
        act_walk = menu.addAction("🐾 Wake Up & Walk")
        act_walk.triggered.connect(lambda: (debug_log("MENU", "Selected: Wake Up & Walk"), self.behavior.wake_up(duration=35.0, reason="user")))

        act_sleep = menu.addAction("💤 Go to Sleep in Corner")
        act_sleep.triggered.connect(lambda: (debug_log("MENU", "Selected: Go to Sleep in Corner"), self.behavior.send_to_sleep()))

        menu.addSeparator()

        # Submenu: Color theme
        color_menu = menu.addMenu("🎨 Fur Color")
        color_menu.setStyleSheet(menu.styleSheet())
        color_menu.addAction("Golden Orange (Default)").triggered.connect(lambda: (debug_log("MENU", "Theme selected: orange"), self.set_color_theme("orange")))
        color_menu.addAction("Sakura Pink").triggered.connect(lambda: (debug_log("MENU", "Theme selected: sakura"), self.set_color_theme("sakura")))
        color_menu.addAction("Lavender Purple").triggered.connect(lambda: (debug_log("MENU", "Theme selected: lavender"), self.set_color_theme("lavender")))
        color_menu.addAction("Midnight Charcoal").triggered.connect(lambda: (debug_log("MENU", "Theme selected: midnight"), self.set_color_theme("midnight")))
        color_menu.addAction("Snow White").triggered.connect(lambda: (debug_log("MENU", "Theme selected: snow"), self.set_color_theme("snow")))

        # Submenu: Speed
        speed_menu = menu.addMenu("⚡ Walk Speed")
        speed_menu.setStyleSheet(menu.styleSheet())
        speed_menu.addAction("Slow (40 px/s)").triggered.connect(lambda: (debug_log("MENU", "Speed selected: 40 px/s"), setattr(self.behavior, 'walk_speed', 40.0)))
        speed_menu.addAction("Normal (70 px/s)").triggered.connect(lambda: (debug_log("MENU", "Speed selected: 70 px/s"), setattr(self.behavior, 'walk_speed', 70.0)))
        speed_menu.addAction("Fast (120 px/s)").triggered.connect(lambda: (debug_log("MENU", "Speed selected: 120 px/s"), setattr(self.behavior, 'walk_speed', 120.0)))

        # Submenu: Size
        size_menu = menu.addMenu("📏 Size")
        size_menu.setStyleSheet(menu.styleSheet())
        size_menu.addAction("Small (120px)").triggered.connect(lambda: (debug_log("MENU", "Size selected: 120px"), self.change_size(120)))
        size_menu.addAction("Medium (160px)").triggered.connect(lambda: (debug_log("MENU", "Size selected: 160px"), self.change_size(160)))
        size_menu.addAction("Large (210px)").triggered.connect(lambda: (debug_log("MENU", "Size selected: 210px"), self.change_size(210)))

        menu.addSeparator()
        act_quit = menu.addAction("❌ Quit Avatar")
        act_quit.triggered.connect(lambda: (debug_log("MENU", "Selected: Quit Avatar"), QApplication.instance().quit()))

        menu.exec(global_pos)
