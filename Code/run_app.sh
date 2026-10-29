#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

cd "$SCRIPT_DIR"

if [ ! -f 'app_ui.py' ]; then
    echo 'Error: app_ui.py is missing.'
    exit 1
fi

# Preserve the caller's X11 display + auth cookie for sudo.
# Without this, root cannot connect to a user VNC/X session (e.g. TurboVNC :1)
# and Qt fails with: "No protocol specified" / "could not connect to display".
if [ -z "${DISPLAY:-}" ]; then
    echo 'Error: DISPLAY is not set. Run this from a graphical session (e.g. VNC).'
    exit 1
fi

XAUTH="${XAUTHORITY:-$HOME/.Xauthority}"
if [ ! -r "$XAUTH" ]; then
    echo "Error: X authority file not readable: $XAUTH"
    exit 1
fi

# Desktop/menu clicks have no TTY; use a zenity askpass so sudo can prompt.
SUDO_FLAGS=()
if [ ! -t 0 ]; then
    ASKPASS="$SCRIPT_DIR/sudo_askpass.sh"
    if [ -x "$ASKPASS" ]; then
        export SUDO_ASKPASS="$ASKPASS"
        SUDO_FLAGS+=(-A)
    fi
fi

sudo "${SUDO_FLAGS[@]}" env DISPLAY="$DISPLAY" XAUTHORITY="$XAUTH" python3 app_ui.py
