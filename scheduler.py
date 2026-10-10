import os
import json
import time
import subprocess
from datetime import datetime
from logger import debug_log


TASKS_FILE = os.path.join(os.path.dirname(__file__), "tasks.json")


class Task:
    def __init__(self, task_id, title, due_time, recurring_min=None, category="general", completed=False):
        self.id = task_id
        self.title = title
        self.due_time = float(due_time)  # Unix timestamp
        self.recurring_min = recurring_min
        self.category = category
        self.completed = completed
        self.notified = False

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "due_time": self.due_time,
            "recurring_min": self.recurring_min,
            "category": self.category,
            "completed": self.completed,
            "notified": self.notified,
        }

    @classmethod
    def from_dict(cls, data):
        t = cls(
            task_id=data["id"],
            title=data["title"],
            due_time=data["due_time"],
            recurring_min=data.get("recurring_min"),
            category=data.get("category", "general"),
            completed=data.get("completed", False),
        )
        t.notified = data.get("notified", False)
        return t

    def time_remaining_str(self):
        diff = self.due_time - time.time()
        if diff <= 0:
            return "Due now!"
        mins = int(diff // 60)
        secs = int(diff % 60)
        if mins < 60:
            return f"in {mins}m {secs}s"
        hours = mins // 60
        rem_mins = mins % 60
        return f"in {hours}h {rem_mins}m"


class ScheduleManager:
    """
    Handles scheduling, periodic reminders, quick timers,
    and persistent storage for the avatar.
    """
    def __init__(self, filepath=TASKS_FILE):
        self.filepath = filepath
        self.tasks = []
        self.load_tasks()

    def load_tasks(self):
        self.tasks = []
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for item in data:
                        self.tasks.append(Task.from_dict(item))
                debug_log("SCHEDULER", f"Loaded {len(self.tasks)} tasks from {self.filepath}")
            except Exception as e:
                debug_log("SCHEDULER", f"Error loading tasks: {e}")

    def save_tasks(self):
        try:
            data = [t.to_dict() for t in self.tasks]
            with open(self.filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            debug_log("SCHEDULER", f"Saved {len(self.tasks)} tasks to {self.filepath}")
        except Exception as e:
            debug_log("SCHEDULER", f"Error saving tasks: {e}")

    def add_task(self, title, due_time, recurring_min=None, category="general"):
        task_id = f"task_{int(time.time() * 1000)}"
        new_task = Task(task_id, title, due_time, recurring_min, category)
        self.tasks.append(new_task)
        self.save_tasks()
        debug_log("SCHEDULER", f"Added task: '{title}' (id={task_id}, due={due_time:.1f}, recurring={recurring_min}, category={category})")
        return new_task

    def add_quick_timer(self, title, minutes, recurring=False, category="general"):
        due_time = time.time() + (minutes * 60)
        rec = minutes if recurring else None
        debug_log("SCHEDULER", f"add_quick_timer: '{title}', {minutes}m, recurring={recurring}, category={category}")
        return self.add_task(title, due_time, recurring_min=rec, category=category)

    def complete_task(self, task_id):
        for t in self.tasks:
            if t.id == task_id:
                t.completed = True
                self.save_tasks()
                debug_log("SCHEDULER", f"Task marked completed: '{t.title}' (id={task_id})")
                return True
        debug_log("SCHEDULER", f"Task completion failed (not found): id={task_id}")
        return False

    def snooze_task(self, task_id, minutes=5):
        for t in self.tasks:
            if t.id == task_id:
                t.due_time = time.time() + (minutes * 60)
                t.notified = False
                self.save_tasks()
                debug_log("SCHEDULER", f"Task snoozed for {minutes}m: '{t.title}' (id={task_id}, next due={t.due_time:.1f})")
                return True
        debug_log("SCHEDULER", f"Task snooze failed (not found): id={task_id}")
        return False

    def delete_task(self, task_id):
        self.tasks = [t for t in self.tasks if t.id != task_id]
        self.save_tasks()
        debug_log("SCHEDULER", f"Deleted task id={task_id}")

    def get_active_tasks(self):
        self.load_tasks()
        active = [t for t in self.tasks if not t.completed]
        active.sort(key=lambda x: x.due_time)
        return active

    def get_next_upcoming_task(self):
        active = self.get_active_tasks()
        return active[0] if active else None

    def check_due_tasks(self):
        """
        Returns list of tasks that have just triggered.
        Handles recurring task rollover.
        """
        now = time.time()
        due_tasks = []

        for t in self.tasks:
            if not t.completed and not t.notified and t.due_time <= now:
                t.notified = True
                due_tasks.append(t)
                debug_log("SCHEDULER", f"Task became due: '{t.title}' (id={t.id}, scheduled due={t.due_time:.1f}, now={now:.1f})")

                # Send system desktop notification
                self.send_desktop_notification(t.title, f"⏰ Reminder from your Avatar ({t.category.title()})")

                # If recurring, set next alarm
                if t.recurring_min:
                    t.due_time = now + (t.recurring_min * 60)
                    t.notified = False
                    debug_log("SCHEDULER", f"Recurring task rollover: '{t.title}' next due in {t.recurring_min}m")

        if due_tasks:
            self.save_tasks()

        return due_tasks

    def send_desktop_notification(self, title, message):
        """Send native Linux desktop notification via notify-send if available."""
        debug_log("NOTIFICATION", f"Sending system notify-send: '{title}' - '{message}'")
        try:
            subprocess.Popen([
                "notify-send",
                "-a", "Desktop Avatar",
                "-u", "critical",
                title,
                message
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception as e:
            debug_log("NOTIFICATION", f"notify-send failed: {e}")
