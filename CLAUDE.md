# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Rules

- **Testing**: Do not create or write test files unless explicitly requested by the user
- **Documentation**: Only create documentation files when explicitly asked
- **System Commands**: Never run commands that require sudo or elevated privileges directly. Instead, provide the user with the exact commands to run manually in their terminal. This includes mounting network shares, installing packages, or any system-level operations.

## Repository Overview

Personal packages repository containing utility scripts and tools. Currently includes the `file_managers` package for file management utilities, CLI tools, and movie duplicate detection.

## Development Commands

### Package Management
- `pip install -e .` - Install package in development mode
- `pip install -e ".[dev]"` - Install with development dependencies

### Code Quality
- `black .` - Format code
- `ruff check .` - Lint code  
- `mypy file_managers` - Type checking

### Testing
- `pytest` - Run all tests
- `pytest tests/test_file_utils.py` - Run file utilities tests
- `pytest tests/test_movie_scanner.py` - Run movie scanner tests

### Package Usage

#### General File Management
- `python -m file_managers.cli.file_manager find <directory> <extension>` - Find files by extension
- `python -m file_managers.cli.file_manager size <file>` - Get file size

#### Plex Movie Management

**Movie Duplicate Detection:**
- `python -m file_managers.plex.cli.movie_duplicates` - Scan predefined Plex directories for duplicates
- `python -m file_managers.plex.cli.movie_duplicates --custom "path1,path2"` - Scan custom directories
- `python -m file_managers.plex.cli.movie_duplicates --delete` - Interactive deletion mode
- `python run_movie_scanner.py` - Interactive movie duplicate scanner

**Movie Report Generation:**
- `python -m file_managers.plex.utils.report_generator` - Generate movie inventory and duplicate reports
- Reports saved to `reports/` directory in both text and JSON formats
- Includes duplicate analysis with space savings calculations and movie library inventory

#### Plex TV Management

**TV Show Analysis and Reports:**
- `python -m file_managers.plex.utils.tv_report_generator` - Generate TV folder analysis and organization plan reports

**TV Episode Organization:**
- `python -m file_managers.plex.utils.tv_mover` - Organize loose TV episodes (dry run by default)
- `python -m file_managers.plex.utils.tv_mover --execute` - Actually move episodes to proper show folders
- `python -m file_managers.plex.utils.tv_mover --delete-small` - Also find and delete small folders (<100MB)
- `python -m file_managers.plex.utils.tv_mover --custom "path1,path2"` - Use custom TV directories
- Automatically cleans up empty/small folders after moving episodes

**TV Episode Organization Features:**
- Finds episodes outside proper show folders (loose files, season folders)
- Moves episodes to existing show folders or creates new ones
- Automatic cleanup of empty/small folders (<100MB) after moves
- Dry run mode shows what would be moved without making changes
- Safety confirmations before executing moves

## Architecture

### Package Structure
```
file_managers/
├── __init__.py          # Package initialization
├── utils/               # General utility modules
│   ├── __init__.py
│   └── file_utils.py    # File operations utilities
├── cli/                 # General CLI tools
│   ├── __init__.py
│   └── file_manager.py  # File management CLI tool
└── plex/                # Plex-specific functionality
    ├── __init__.py
    ├── utils/           # Plex utility modules
    │   ├── __init__.py
    │   ├── movie_scanner.py       # Movie duplicate detection
    │   ├── deletion_manager.py    # Interactive deletion
    │   ├── report_generator.py    # Movie report generation
    │   ├── tv_scanner.py          # TV episode detection and analysis
    │   ├── tv_report_generator.py # TV report generation
    │   ├── tv_mover.py            # TV episode organization and moving
    │   └── tv_* (other TV modules) # Additional TV-related utilities
    └── cli/             # Plex CLI tools
        ├── __init__.py
        └── movie_duplicates.py    # Movie duplicate scanner CLI
```

### Static Configuration

**Movie Directories:**
- `/mnt/qnap/plex/Movie/` - Primary movie directory (\\192.168.1.27\plex\Movie)
- `/mnt/qnap/Media/Movies/` - Secondary movie directory (\\192.168.1.27\Media\Movies)
- `/mnt/qnap/Multimedia/Movies/` - Tertiary movie directory (\\192.168.1.27\Multimedia\Movies)

**TV Directories:**
- `/mnt/qnap/plex/TV/` - Primary TV directory (\\192.168.1.27\plex\TV)
- `/mnt/qnap/Media/TV/` - Secondary TV directory (\\192.168.1.27\Media\TV)
- `/mnt/qnap/Multimedia/TV/` - Tertiary TV directory (\\192.168.1.27\Multimedia\TV)

**Reports:**
- All reports are saved to `reports/` directory in the project root
- Available in both human-readable (.txt) and machine-readable (.json) formats
- Timestamped filenames for easy tracking

**Interactive Scripts:**
- `run_movie_scanner.py` - Easy movie duplicate scanner launcher

### Design Patterns
- Utility functions in `utils/` modules for reusable functionality
- CLI tools in `cli/` modules for command-line interfaces
- Type hints throughout for better code quality
- Comprehensive error handling in public APIs