#!/usr/bin/env python3
"""
Main entry point for Render deployment
Redirects to render_no_auth_bot.py
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import and run the render bot
from render_no_auth_bot import main

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())