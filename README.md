# 🐼 Hit & Run Panda

A cute desktop productivity pet that reminds you to drink water, stretch, and take breaks.

**Works on Windows and macOS!**

## Features

- 🐼 Animated panda walks onto screen with reminders
- ⏰ Customizable reminder intervals (seconds/minutes/hours/days)
- 📊 Track your progress with history
- 🚨 Red Alert mode for urgent reminders
- 🔕 Lives quietly in system tray

## Installation

### From Source (Both Platforms)

```bash
# Install dependencies
pip install -r requirements.txt

# Run directly
python main.py

# Or install to system
python setup.py
```

### Build Standalone Executable

```bash
# Windows: Creates .exe
# macOS: Creates .app bundle
python build.py
```

## Usage

- Right-click the tray icon for menu
- First run opens settings automatically
- Configure your tasks and intervals
- Enable Panda Reminders to start

### CLI Commands

```bash
python main.py show      # Trigger panda now
python main.py settings  # Open settings
python main.py history   # Show history
python main.py redalert  # Test red alert
```

## Requirements

- Python 3.8+
- PyQt6

## License

MIT
