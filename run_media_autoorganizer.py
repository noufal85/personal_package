#!/usr/bin/env python3
"""Convenience script to run the Media Auto-Organizer

This script provides an easy way to launch the media auto-organizer
without having to remember the full module path.
"""

import sys
from file_managers.plex.media_autoorganizer.cli import main

if __name__ == "__main__":
    # Pass all command line arguments to the CLI
    sys.exit(main())