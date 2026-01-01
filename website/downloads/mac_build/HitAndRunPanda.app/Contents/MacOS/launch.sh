#!/bin/bash

# Hit and Run Panda - Mac Launcher
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
RESOURCES="$DIR/../Resources"

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    osascript -e 'display dialog "Python 3 is required.\n\nInstall from python.org or run:\nbrew install python3" with title "Hit and Run Panda" buttons {"OK"} default button 1 with icon stop'
    exit 1
fi

# Check/install PyQt6
if ! python3 -c "import PyQt6" 2>/dev/null; then
    osascript -e 'display dialog "Installing required packages...\nThis only happens once." with title "Hit and Run Panda" buttons {"OK"} default button 1'
    python3 -m pip install --user PyQt6 >/dev/null 2>&1
fi

# Run the app
cd "$RESOURCES"
python3 main.py &
