#!/usr/bin/env python3
"""
Simple launcher for the AI-powered media assistant.

This script provides an easy way to start the interactive media assistant
without having to remember the full module path.
"""

import sys
import os

# Add the current directory to the Python path so we can import file_managers
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from file_managers.plex.cli.media_assistant import main
    
    if __name__ == '__main__':
        main()
except ImportError as e:
    print(f"Error: Could not import media assistant: {e}")
    print("Make sure you have installed the package dependencies:")
    print("pip install -e .")
    sys.exit(1)
except Exception as e:
    print(f"Error running media assistant: {e}")
    sys.exit(1)