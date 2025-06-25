#!/usr/bin/env python3
"""
TV File Organizer - Standalone CLI Launcher

Convenient launcher script for the TV File Organizer CLI.
This script can be run directly from the project root.

Usage:
    python3 tv_organizer.py [command] [options]
    
Examples:
    python3 tv_organizer.py duplicates --scan --report
    python3 tv_organizer.py status
    python3 tv_organizer.py config --show
    python3 tv_organizer.py --help
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import and run the CLI
from file_managers.plex.tv_organizer.cli.tv_organizer_cli import main

if __name__ == "__main__":
    sys.exit(main())