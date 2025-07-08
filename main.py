#!/usr/bin/env python3
"""
Main entry point - redirects to app.py for deployment compatibility
"""

import subprocess
import sys

if __name__ == "__main__":
    # Run app.py which contains the main application
    subprocess.run([sys.executable, "app.py"])