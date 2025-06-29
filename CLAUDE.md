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

#### Unified CLI (Recommended - Phase 3 Complete!)
**Main Entry Point:** `plex-cli` (alias for `python3 -m file_managers.cli.personal_cli`)

**General File Operations:**
- `plex-cli files duplicates --type movies` - Find movie duplicates
- `plex-cli files database --rebuild` - Rebuild media database
- `plex-cli files organize` - Auto-organize downloads (dry-run mode)
- `plex-cli files organize --execute` - Actually organize files
- `plex-cli files organize --no-ai` - Rule-based classification only
- `plex-cli files reorganize` - Analyze misplaced media files (database-based)
- `plex-cli files reorganize --ai` - Enhanced analysis with AI classification
- `plex-cli files reorganize --rebuild-db` - Force database rebuild before analysis
- `plex-cli files reorganize --no-external-apis` - Disable TMDB/TVDB usage

**Movie Management:**
- `plex-cli movies duplicates` - Find duplicate movies
- `plex-cli movies duplicates --delete` - Interactive deletion mode
- `plex-cli movies search "The Batman"` - Search movie collection
- `plex-cli movies reports` - Generate comprehensive movie collection reports

**TV Show Management:**
- `plex-cli tv organize` - Analyze TV episode organization
- `plex-cli tv organize --demo` - Preview what would be moved
- `plex-cli tv organize --execute` - Actually move files (with confirmation)
- `plex-cli tv search "Breaking Bad"` - Search TV shows (enhanced fuzzy matching)
- `plex-cli tv missing "Game of Thrones"` - Find missing episodes
- `plex-cli tv missing "Lost" --season 3` - Check specific season
- `plex-cli tv reports` - Generate comprehensive TV collection reports

**TV Duplicate Management (Advanced):**
- `python3 -m file_managers.plex.tv_organizer.cli.tv_organizer_cli duplicates --scan` - Enhanced duplicate detection
- `python3 -m file_managers.plex.tv_organizer.cli.tv_organizer_cli duplicates --scan --delete --mode dry-run` - Preview deletions (safe)
- `python3 -m file_managers.plex.tv_organizer.cli.tv_organizer_cli duplicates --scan --delete --mode trash` - Move duplicates to trash
- `python3 -m file_managers.plex.tv_organizer.cli.tv_organizer_cli duplicates --scan --delete --mode permanent` - Permanent deletion (dangerous!)
- `python3 -m file_managers.plex.tv_organizer.cli.tv_organizer_cli resolve --analyze --report` - Path resolution analysis

**Cross-Media Operations:**
- `plex-cli media assistant "Do I have Inception?"` - AI-powered natural language search
- `plex-cli media assistant --interactive` - Interactive AI assistant mode
- `plex-cli media database --rebuild` - Rebuild media database
- `plex-cli media database --status` - Show database status
- `plex-cli media status` - System status and mount point verification

**Configuration:**
- `plex-cli config show` - Show all configuration
- `plex-cli config show --section movies` - Show movie configuration only
- `plex-cli config paths` - Show configured directory paths
- `plex-cli config apis` - API configuration management
- `plex-cli config apis --show` - Show configured API keys (masked)
- `plex-cli config apis --check` - Test API connectivity

**Interactive Mode:**
- `plex-cli` or `plex-cli --interactive` - Start interactive menu mode

#### Legacy CLI Commands (Still Available)

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

**Movie Quality Management:**
- `plex-cli movies ratings --fetch` - Fetch OMDB ratings for all movies
- `plex-cli movies ratings --stats` - Show rating database statistics
- `plex-cli movies ratings --bad-movies` - List badly rated movies
- `plex-cli movies ratings --delete-bad` - Delete badly rated movies (with confirmation)
- `plex-cli movies ratings --imdb-threshold 4.0` - Set IMDB threshold for bad movies
- `plex-cli movies ratings --rt-threshold 25` - Set Rotten Tomatoes threshold (default: 30%)
- `plex-cli movies ratings --meta-threshold 35` - Set Metacritic threshold (default: 40)

**OMDB Rating Features:**
- Fetches IMDB, Rotten Tomatoes, and Metacritic ratings for movies
- Caches ratings locally to avoid repeated API calls (30-day cache)
- Calculates overall quality scores from multiple rating sources
- Identifies badly rated movies based on configurable thresholds
- Safe deletion with double confirmation for badly rated movies
- Rate-limited API calls (10 requests/second) with retry logic
- Comprehensive logging and progress tracking

#### Plex TV Management

**TV Show Analysis and Reports:**
- `python -m file_managers.plex.utils.tv_report_generator` - Generate TV folder analysis and organization plan reports

**TV Episode Organization:**
- `plex-cli tv organize` - Analyze TV folder structure and generate organization plan
- `plex-cli tv organize --demo` - Preview mode showing what would be moved
- `plex-cli tv organize --execute` - Interactive TV organization with detailed logging
- `python -m file_managers.plex.utils.tv_mover` - Direct TV mover utility (dry run by default)
- `python -m file_managers.plex.utils.tv_mover --execute` - Actually move episodes to proper show folders
- `python -m file_managers.plex.utils.tv_mover --delete-small` - Also find and delete small folders (<100MB)
- `python -m file_managers.plex.utils.tv_mover --custom "path1,path2"` - Use custom TV directories
- `python run_tv_organization.py` - Demo script showing TV organization features

**TV Episode Organization Features:**
- Finds episodes outside proper show folders (loose files, season folders)
- Moves episodes to existing show folders or creates new ones
- Automatic cleanup of empty/small folders (<100MB) after moves
- Dry run mode shows what would be moved without making changes
- Safety confirmations before executing moves
- **Enhanced Logging**: Session-specific logs with detailed progress tracking
- **Real-time Progress**: Show-by-show move tracking with file sizes
- **Error Recovery**: Unique filename generation for conflicts
- **Comprehensive Cleanup**: Post-move cleanup of empty/small folders
- **Double Confirmation**: Two-step safety confirmation for execution

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
  OMDB_API_KEY=your_omdb_key_here
  ```

**API Integration Notes:**
- TVDB v4 API uses JWT authentication (automatically handled)
- TMDB API uses direct API key authentication
- Both APIs have rate limiting built-in to prevent errors
- Use `plex-cli config apis --check` to test API connectivity

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
    ├── tv_organizer/        # Advanced TV File Organizer (STANDALONE MODULE)
    │   ├── __init__.py          # Package exports
    │   ├── INSTRUCTIONS.md      # Comprehensive usage documentation
    │   ├── cli/
    │   │   └── tv_organizer_cli.py    # Standalone CLI with deletion functionality
    │   ├── core/
    │   │   ├── duplicate_detector.py  # Enhanced duplicate detection with deletion
    │   │   └── path_resolver.py       # Directory structure analysis and path resolution
    │   ├── models/
    │   │   ├── episode.py             # Episode data structures
    │   │   ├── duplicate.py           # Duplicate groups and deletion plans
    │   │   └── path_resolution.py     # Path resolution and destination scoring
    │   └── utils/                     # TV utility functions
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

#### Media Reorganization Analyzer (NEW - Database-Based)

**Intelligent Misplaced Media Detection:**
- `plex-cli files reorganize` - Database-based analysis of misplaced files
- `plex-cli files reorganize --ai` - Enhanced AI classification (OpenAI GPT-4o-mini)
- `plex-cli files reorganize --rebuild-db` - Force database rebuild before analysis
- `plex-cli files reorganize --no-external-apis` - Disable TMDB/TVDB integration
- `plex-cli files reorganize --confidence 0.9` - High confidence threshold only
- `plex-cli files reorganize --format json` - JSON output for automation

**Reorganizer Features:**
- **Database-Driven**: Uses existing media database for instant analysis (11,967+ files in seconds)
- **Multi-Tier Classification**: AI → External APIs → Enhanced Rules with intelligent fallbacks
- **Documentary Detection**: Advanced pattern recognition finds documentaries in movie folders
- **Stand-up Comedy Detection**: Identifies comedy specials misplaced in TV/movie directories
- **Parent Folder Analysis**: Uses TV show folder names for better external API results
- **External API Integration**: TMDB/TVDB for verification and documentary detection
- **Confidence Scoring**: Detailed confidence metrics with configurable thresholds
- **Comprehensive Reporting**: Text and JSON reports with category transitions and space analysis

**Performance Characteristics:**
- **Database Loading**: 11,967 files in ~2 seconds (vs 5+ minutes directory scanning)
- **Rule-Based Analysis**: ~12 seconds for full collection analysis
- **AI Enhancement**: Limited to 50 files for testing (2s per file)
- **Results**: Finds 485 misplaced files vs 107 with previous methods

**API Usage:**
- **OpenAI**: Intelligent filename classification with batch processing
- **TMDB**: Movie verification and documentary genre detection
- **TVDB**: TV show verification using parent folder names
- **Rate Limiting**: Respects API quotas with exponential backoff

**Categories Detected:**
- Movies misplaced in TV folders
- TV episodes in movie directories
- Documentaries in regular movie folders
- Stand-up comedy specials in wrong categories
- Multi-part movies vs TV episodes

**Documentation**: See `MEDIA_REORGANIZER_DOCUMENTATION.md` for detailed architecture, flowcharts, and usage examples.

#### TV File Organizer (Standalone Advanced Module)

**Enhanced TV Episode Management:**
- `python3 -m file_managers.plex.tv_organizer.cli.tv_organizer_cli duplicates --scan --report` - Advanced duplicate detection
- `python3 -m file_managers.plex.tv_organizer.cli.tv_organizer_cli duplicates --scan --delete --mode dry-run` - Preview deletions (safe)
- `python3 -m file_managers.plex.tv_organizer.cli.tv_organizer_cli duplicates --scan --delete --mode trash --confidence 90` - High-confidence deletion to trash
- `python3 -m file_managers.plex.tv_organizer.cli.tv_organizer_cli resolve --analyze --report` - Directory structure analysis
- `python3 -m file_managers.plex.tv_organizer.cli.tv_organizer_cli resolve --stats` - Organization statistics
- `python3 -m file_managers.plex.tv_organizer.cli.tv_organizer_cli status` - Module status and phase information

**TV File Organizer Features:**
- **Phase 0 (Complete)**: Enhanced duplicate detection with false positive filtering, content analysis, and confidence scoring
- **Phase 2 (Complete)**: Path resolution with directory structure mapping, fuzzy show name matching, and destination scoring
- **Safe Duplicate Deletion**: Multi-layered safety system with dry-run, trash, and permanent modes
- **Interactive Confirmation**: User confirmation system with confidence-based filtering (80%+ default)
- **Enhanced Safety Checks**: File existence, lock status, size validation, and user confirmation requirements
- **Comprehensive Reporting**: Text and JSON formats with confidence scores and detailed analysis
- **Production Ready**: Tested with 10,000+ episodes, 327 shows across 3 TV directories

**Safety Features:**
- **Multiple Deletion Modes**: dry-run (preview), trash (recoverable), permanent (irreversible)
- **Confidence Thresholds**: 80% default, 90% conservative, 95%+ very conservative
- **Safety Validation**: File accessibility, size reasonableness, lock status verification
- **Force Protection**: Requires explicit --force flag to bypass confirmations
- **Interactive Confirmation**: Per-file and batch confirmation options

**Recent Test Results:**
- **10,493 episodes** scanned across 3 TV directories
- **558 duplicate groups** identified with 1,154 duplicate files
- **134 GB potential space savings** at 80% confidence threshold
- **155 safe operations** from 170 total (safety filtering works)
- **Enhanced filtering** reduces false positives by 58%

**Documentation**: See `file_managers/plex/tv_organizer/INSTRUCTIONS.md` for comprehensive usage guide and safety information.

**Enhanced TV Search (Fixed):**
- **Improved Fuzzy Matching**: Finds partial word matches (e.g., "kin" finds "Vikings", "Tulsa King", "Shrinking")
- **Dynamic Thresholds**: 0.3 for short queries (≤4 chars), 0.35 for longer queries
- **Substring Detection**: Handles searches like "gangs" → "Gangs of London"
- **Better Relevance**: Word-level + partial matching with confidence scoring

**Interactive Scripts:**
- `run_movie_scanner.py` - Easy movie duplicate scanner launcher
- `run_media_assistant.py` - Easy AI-powered media assistant launcher
- `run_media_autoorganizer.py` - Easy media auto-organizer launcher
- `run_tv_organization.py` - TV organization features and demo

**Interactive Menu Navigation:**
- `b` or `back` - Return to previous menu
- `q` or `quit` - Exit application
- All interactive menus include proper exit options
- Input validation prevents invalid choices
- Recursive menu support for complex workflows

### Design Patterns
- Utility functions in `utils/` modules for reusable functionality
- CLI tools in `cli/` modules for command-line interfaces
- Type hints throughout for better code quality
- Comprehensive error handling in public APIs