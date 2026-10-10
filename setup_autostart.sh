#!/usr/bin/env bash
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
AUTOSTART_DIR="$HOME/.config/autostart"
DESKTOP_FILE="$AUTOSTART_DIR/desktop-avatar.desktop"

case "$1" in
    remove|uninstall|disable)
        if [ -f "$DESKTOP_FILE" ]; then
            rm -f "$DESKTOP_FILE"
            echo "✅ Autostart disabled. Removed: $DESKTOP_FILE"
        else
            echo "ℹ️  Autostart was not enabled."
        fi
        ;;
    status)
        if [ -f "$DESKTOP_FILE" ]; then
            echo "✅ Desktop Avatar autostart is ENABLED."
            echo "File: $DESKTOP_FILE"
            cat "$DESKTOP_FILE"
        else
            echo "❌ Desktop Avatar autostart is currently DISABLED."
        fi
        ;;
    *)
        mkdir -p "$AUTOSTART_DIR"
        cat > "$DESKTOP_FILE" << EOF
[Desktop Entry]
Type=Application
Exec=$DIR/run.sh
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
X-GNOME-Autostart-Delay=2
Name=Desktop Avatar
Comment=Interactive 2D Desktop Screen Pet & Scheduler
Icon=applications-other
Terminal=false
Categories=Utility;
EOF
        chmod +x "$DESKTOP_FILE"
        echo "============================================================"
        echo "🎉 Autostart successfully ENABLED!"
        echo "============================================================"
        echo "The avatar will now start automatically whenever your PC logs in."
        echo "Created file: $DESKTOP_FILE"
        echo ""
        echo "To disable autostart in the future, run:"
        echo "  ./setup_autostart.sh remove"
        echo "============================================================"
        ;;
esac
