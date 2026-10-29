#!/bin/bash
# Graphical password helper for sudo -A (desktop/menu launches have no TTY).
exec zenity --password --title='Authentication Required' \
    --text='Freenove Tower Cooler needs administrator privileges:' 2>/dev/null
