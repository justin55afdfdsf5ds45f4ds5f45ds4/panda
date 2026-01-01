"""
Hit & Run Panda Launcher
This .pyw file runs without showing a console window on Windows.
Double-click to start the panda!
"""

import sys
import os

# Add the directory to path
sys.path.insert(0, os.path.dirname(__file__))

# Import and run
from main import PetController

if __name__ == "__main__":
    controller = PetController()
    sys.exit(controller.run())
