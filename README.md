# 🐾 2D Animated Desktop Avatar & Work Companion (Python + PyQt6)

An interactive, animated 2D desktop screen pet and productivity assistant written in Python using **PyQt6**.

It roams along the bottom of your screen/taskbar, follows your mouse cursor with its eyes, reacts to petting and dragging, and helps you **schedule work**, **set timers**, and **notifies you with reminders**!

---

## ✨ Features

### 📅 Personal Work Scheduler & Notifications
* **Task & Work Scheduler:** Open via Right-Click menu or double-click to add, schedule, and view upcoming tasks.
* **1-Click Quick Timers:**
  * 🍅 **Pomodoro Focus (25m):** Deep work sessions.
  * ☕ **Short Break (5m):** Rest time.
  * 💧 **Hydration Reminder (Every 30m):** Recurring health alerts.
  * 🧘 **Stretch & Relax (45m):** Break reminders.
* **Custom Scheduling Options:**
  * In *X* minutes countdown.
  * At a specific time today (e.g., 14:30).
  * Recurring interval (every *X* minutes).
* **Proactive Notifications:**
  * When a task is due, the avatar dances happily, speaks the alert in a speech bubble with **✔ Done** and **💤 +5m Snooze** buttons!
  * Also sends native Linux desktop notifications (`notify-send`) so you never miss an alert.
* **Persistent Tasks:** Automatically saves scheduled tasks to `tasks.json`.

### 💬 Dynamic Floating Speech Bubbles (No Clipping / Overflow)
* Uses an independent, floating speech bubble window that automatically resizes and word-wraps text of any length.
* Clamps to screen edges and stays visible above the avatar without ever clipping off-screen.

### 🎮 Non-Intrusive Desktop Companion Lifecycle
* **Sleeps in Corner by Default:** At startup, the avatar walks to the bottom-left corner and curls up to sleep quietly, ensuring zero distraction while you work.
* **Wakes Up on Click/Interaction:** Clicking, petting, or dragging the avatar wakes it up with hearts and allows it to interact and roam for ~20 seconds. Once left alone, it walks back to the bottom-left corner and sleeps.
* **Stationary Reminder Alerts:** When a scheduled reminder is due, the avatar wakes up and stays stationary with a persistent notification bubble containing **✔ Done** and **💤 +5m Snooze** buttons.
* **Stays Open Until You Click:** The reminder window remains open indefinitely until you take action. Once an option is chosen, the avatar walks back to the corner to sleep!

---

## 🚀 Quick Start

### 1. Launch with Runner Script:
```bash
./run.sh
```

### 2. Or Run Directly with Python:
```bash
.venv/bin/python3 main.py
```

### Options:
```bash
./run.sh --size 180 --speed 90 --theme sakura
```
* `--size <int>`: Avatar window size in pixels (default: `160`).
* `--speed <float>`: Walking speed in pixels/second (default: `70.0`).
* `--theme <name>`: `orange`, `lavender`, `sakura`, `midnight`, `snow`.
* `--debug`: Enable timestamped event logging for debugging.

### 🔍 Debug Mode
To inspect internal events (clicks, dragging, gravity physics, reminders, timers, state changes):
```bash
./run.sh --debug
```

---

## ⚡ Start Automatically at PC Boot / Login

You can set the avatar to automatically start whenever you log into your PC:

* **Enable Autostart:**
  ```bash
  ./setup_autostart.sh
  ```
* **Check Status:**
  ```bash
  ./setup_autostart.sh status
  ```
* **Disable Autostart:**
  ```bash
  ./setup_autostart.sh remove
  ```

---

## 🎮 Controls

| Action | Control | Description |
| :--- | :--- | :--- |
| **Open Scheduler** | Double-Click / Right-Click Menu | Opens task scheduler & timer manager |
| **Pet / Play** | Left-Click | Triggers happy dance & hearts |
| **Pick Up** | Click & Hold Left Mouse | Drags avatar anywhere on screen |
| **Drop in Air** | Release Left Mouse | Falls with gravity and lands with a bounce |
| **Context Menu** | Right-Click | Access scheduler, timers, colors, speed, actions, and exit |
| **Quit** | Right-Click ➔ Quit *(or Ctrl+C in terminal)* | Closes the avatar |

---

## 📁 Architecture

* `main.py`: Application entry point with Linux XWayland (`xcb`) desktop positioning.
* `avatar_window.py`: Transparent overlay `QWidget` managing physics, coordinates, and interactions.
* `character.py`: Procedural vector 2D mascot engine with eye tracking and animations.
* `behaviors.py`: Autonomous state machine (corner sleeping, napping, idle roaming, active interaction).
* `scheduler.py`: Background task manager, timers, recurring intervals, and desktop alerts.
* `schedule_dialog.py`: Modern GUI to manage work schedules, Pomodoro, and quick timers.
* `speech_bubble.py`: Independent floating speech bubble overlay preventing text overflow & clipping.
* `logger.py`: Formatted event logging system active only with `--debug`.
