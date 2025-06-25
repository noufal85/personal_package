"""
TV File Organizer Module

A dedicated system for intelligently organizing TV episode files across multiple directories.
Handles duplicate detection, loose episode identification, path resolution, and safe file organization.

This module is designed to be completely separate from existing TV utilities and will not be
integrated into the main CLI until all phases are complete and thoroughly tested.

Project Phases:
- Phase 0: Duplicate Detection ✅ Complete
- Phase 1: Loose Episode Detection 🚧 Planned
- Phase 2: Path Resolution 🚧 Planned
- Phase 3: Organization Execution 🚧 Planned

Usage:
    # From project root
    python3 tv_organizer.py [command] [options]
    
    # Or as module
    python3 -m file_managers.plex.tv_organizer.cli.tv_organizer_cli [command] [options]

Documentation:
    See INSTRUCTIONS.md in this directory for detailed usage instructions.
"""

__version__ = "0.1.0"
__status__ = "Development - Phase 0 Complete"

# Module will export main classes when phases are complete
# from .core.organizer import TVOrganizer
# from .core.duplicate_detector import DuplicateDetector
# from .core.loose_episode_finder import LooseEpisodeFinder
# from .core.path_resolver import PathResolver