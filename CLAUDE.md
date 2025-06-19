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

#### AI-Powered Media Search and Analysis

**Interactive Media Assistant:**
- `python -m file_managers.plex.cli.media_assistant --interactive` - Start interactive natural language media search
- `python -m file_managers.plex.cli.media_assistant "Do I have the movie The Batman?"` - Single query mode
- `python -m file_managers.plex.cli.media_assistant "How many seasons of Breaking Bad do I have?"` - Season counting
- `python -m file_managers.plex.cli.media_assistant "Am I missing episodes for Game of Thrones?"` - Missing episode analysis
- `python run_media_assistant.py` - Interactive media assistant launcher

**Natural Language Query Examples:**
- Movie searches: "Do I have Inception?", "Is The Dark Knight in my collection?"
- TV show searches: "Do I have Breaking Bad?", "What seasons of The Office do I have?"
- Season counting: "How many seasons of Friends do I have?"
- Missing episode detection: "Am I missing episodes for Lost season 3?"
- General searches: "Find Stranger Things", "Search for Marvel movies"

**Enhanced Features (with API keys):**
- External database suggestions when media not found locally
- Complete episode count verification against official sources
- Missing episode detection with external API cross-reference
- Enhanced AI processing with AWS Bedrock
- Configure API keys in `.env` file in project root:
  ```
  TMDB_API_KEY=your_tmdb_key_here
  TVDB_API_KEY=your_tvdb_key_here
  AWS_ACCESS_KEY_ID=your_aws_key_here
  AWS_SECRET_ACCESS_KEY=your_aws_secret_here
  ```

**AI-Powered Media Search Features:**
- Natural language query processing using AWS Bedrock (Claude) or pattern matching fallback
- Fuzzy matching for titles with typos or variations
- Intelligent media type detection (movie vs TV show)
- Season and episode analysis with completeness reporting
- Integration with The Movie Database (TMDB) for metadata verification
- Interactive and single-query modes for different use cases

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
    ├── config/          # Configuration management
    │   ├── __init__.py
    │   ├── config.py          # Python configuration interface
    │   └── media_config.yaml  # YAML configuration file
    ├── utils/           # Plex utility modules
    │   ├── __init__.py
    │   ├── movie_scanner.py       # Movie duplicate detection
    │   ├── deletion_manager.py    # Interactive deletion
    │   ├── report_generator.py    # Movie report generation
    │   ├── tv_scanner.py          # TV episode detection and analysis
    │   ├── tv_report_generator.py # TV report generation
    │   ├── tv_mover.py            # TV episode organization and moving
    │   ├── ai_query_processor.py  # AI-powered natural language query processing
    │   ├── episode_analyzer.py    # TV episode completeness analysis
    │   ├── external_api.py        # External API integrations (TMDB, TVDB)
    │   ├── media_searcher.py      # Media search and matching utilities
    │   └── tv_* (other TV modules) # Additional TV-related utilities
    ├── media_autoorganizer/     # Intelligent media file auto-organizer (NEW)
    │   ├── __init__.py          # Package exports
    │   ├── README.md            # Comprehensive documentation
    │   ├── cli.py               # Command-line interface
    │   ├── organizer.py         # Main AutoOrganizer orchestrator class
    │   ├── models.py            # Data structures (MediaFile, MoveResult, etc.)
    │   ├── media_database.py    # Interface to existing media database
    │   ├── classification_db.py # SQLite caching for classifications
    │   └── ai_classifier.py     # AWS Bedrock AI classification
    └── cli/             # Plex CLI tools
        ├── __init__.py
        ├── movie_duplicates.py    # Movie duplicate scanner CLI
        └── media_assistant.py     # AI-powered media assistant CLI
```

### Configuration System

**Centralized Configuration:**
- All settings managed in `file_managers/plex/config/media_config.yaml`
- Python config interface at `file_managers/plex/config/config.py`
- Singleton pattern ensures consistent configuration across all modules

**Movie Directories (from config):**
- `/mnt/qnap/plex/Movie/` - Primary movie directory (\\192.168.1.27\plex\Movie)
- `/mnt/qnap/Media/Movies/` - Secondary movie directory (\\192.168.1.27\Media\Movies)
- `/mnt/qnap/Multimedia/Movies/` - Tertiary movie directory (\\192.168.1.27\Multimedia\Movies)

**TV Directories (from config):**
- `/mnt/qnap/plex/TV/` - Primary TV directory (\\192.168.1.27\plex\TV)
- `/mnt/qnap/Media/TV/` - Secondary TV directory (\\192.168.1.27\Media\TV)
- `/mnt/qnap/Multimedia/TV/` - Tertiary TV directory (\\192.168.1.27\Multimedia\TV)

**Configurable Settings:**
- Video file extensions
- Small folder threshold (100MB default)
- Report formats and timestamp patterns
- Safety settings and confirmation phrases
- NAS server configuration

**Reports:**
- Directory path configurable in YAML (default: `reports/`)
- Available in both human-readable (.txt) and machine-readable (.json) formats
- Timestamped filenames with configurable format

#### Media Auto-Organizer

**Intelligent Media File Organization:**
- `python -m file_managers.plex.media_autoorganizer.cli` - Full-featured auto-organizer CLI
- `python run_media_autoorganizer.py` - Convenience launcher script
- `python -m file_managers.plex.media_autoorganizer.cli --execute` - Actually organize files
- `python -m file_managers.plex.media_autoorganizer.cli --no-ai` - Rule-based classification only
- `python -m file_managers.plex.media_autoorganizer.cli --db-stats` - Show classification database stats
- `python -m file_managers.plex.media_autoorganizer.cli --verify-mounts` - Check mount access

**Auto-Organizer Features:**
- Intelligent TV episode placement using existing show locations from media database
- Smart fallback across multiple QNAP directories when access/space issues occur
- AI-powered classification (AWS Bedrock) with rule-based fallback
- Multi-tier caching (SQLite + CSV) to avoid repeated classifications
- Comprehensive error handling and directory access validation
- Detailed reporting with show information and move results
- Dry run mode for safe preview before execution
- New show directory creation in appropriate TV base directories
- Space management with 1GB safety buffer
- Filename conflict resolution

**Interactive Scripts:**
- `run_movie_scanner.py` - Easy movie duplicate scanner launcher
- `run_media_assistant.py` - Easy AI-powered media assistant launcher
- `run_media_autoorganizer.py` - Easy media auto-organizer launcher

### Design Patterns
- Utility functions in `utils/` modules for reusable functionality
- CLI tools in `cli/` modules for command-line interfaces
- Type hints throughout for better code quality
- Comprehensive error handling in public APIs