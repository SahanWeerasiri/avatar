#!/usr/bin/env python3
"""
Desktop Companion 2D Animated Avatar
A desktop pet written in Python using PyQt6.
Roams along your screen, reacts to clicks, follows your cursor with its eyes,
sleeps, talks, and responds to physics dragging and dropping.
"""

import os
import sys
import signal
import argparse

# On Linux (Wayland / X11), pure Wayland forbids client windows from setting their own coordinates.
# Setting QT_QPA_PLATFORM=xcb uses XWayland, allowing the avatar to roam freely across the desktop.
if sys.platform.startswith("linux") and "QT_QPA_PLATFORM" not in os.environ and os.environ.get("DISPLAY"):
    os.environ["QT_QPA_PLATFORM"] = "xcb"

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer, qInstallMessageHandler, QtMsgType

from avatar_window import AvatarWindow


def qt_message_filter(mode, context, message):
    """Suppress font bearing calculations and internal warning spam."""
    if "minimum bearings" in message or "bearings for" in message:
        return
    if mode in (QtMsgType.QtCriticalMsg, QtMsgType.QtFatalMsg):
        print(f"[Qt] {message}", file=sys.stderr)


def parse_args():
    parser = argparse.ArgumentParser(description="2D Animated Desktop Avatar in Python")
    parser.add_argument(
        "--size",
        type=int,
        default=160,
        help="Size of the avatar window in pixels (default: 160)"
    )
    parser.add_argument(
        "--speed",
        type=float,
        default=70.0,
        help="Walking speed in pixels/second (default: 70.0)"
    )
    parser.add_argument(
        "--theme",
        type=str,
        default="orange",
        choices=["orange", "lavender", "sakura", "midnight", "snow"],
        help="Fur color theme (default: orange)"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable detailed debug event logging"
    )
    return parser.parse_args()


def main():
    args = parse_args()
    from logger import set_debug, is_debug, debug_log
    set_debug(args.debug)
    if is_debug():
        debug_log("SYSTEM", "=== DEBUG MODE ENABLED ===")
        debug_log("CONFIG", f"Options: size={args.size}, speed={args.speed}, theme={args.theme}, debug={args.debug}")

    # Suppress font bearing warnings
    qInstallMessageHandler(qt_message_filter)

    # Ensure clean terminal exit on Ctrl+C
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    app = QApplication(sys.argv)
    app.setApplicationName("DesktopAvatar")

    # IMPORTANT: Keep the avatar running when the scheduling dialog or any secondary window is closed
    app.setQuitOnLastWindowClosed(False)

    # Periodic timer to allow Python's signal handler to process Ctrl+C
    sig_timer = QTimer()
    sig_timer.start(300)
    sig_timer.timeout.connect(lambda: None)

    window = AvatarWindow(size=args.size)
    window.behavior.walk_speed = args.speed
    if args.theme != "orange":
        window.set_color_theme(args.theme)

    window.show()

    print("=" * 60)
    print("🐾 2D Desktop Avatar is now running!")
    print("=" * 60)
    print("• Left-Click: Pet the avatar (happy animation & hearts)")
    print("• Left-Click & Drag: Pick up and move anywhere on your screen")
    print("• Release in Air: Watch gravity drop and bounce on the floor!")
    print("• Right-Click: Open menu for colors, speed, actions, and exit")
    print("• Press Ctrl+C in this terminal to quit")
    print("=" * 60)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
