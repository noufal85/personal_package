# File Managers

A comprehensive Python package for managing Plex media libraries, featuring a **unified CLI interface** (`plex-cli`) that provides tools for movie duplicate detection, TV show organization, automated media management, and AI-powered media assistance.

## 🎉 **NEW: Unified CLI Interface**

**All functionality is now available through a single, powerful command: `plex-cli`**

```bash
# Quick start - Interactive mode
plex-cli

# Direct commands
plex-cli movies duplicates
plex-cli tv organize --demo
plex-cli files organize --execute
plex-cli media assistant "Do I have The Batman?"
plex-cli config show
```

## 🚀 Features

### 🎬 Movie Management
- **Duplicate Detection** - Find and analyze duplicate movies across multiple directories
- **Smart Analysis** - Identify which files to keep based on quality and size
- **Comprehensive Reports** - Generate detailed inventory and duplicate reports
- **Space Optimization** - Calculate potential space savings from removing duplicates

### 📺 TV Show Management  
- **Episode Organization** - Automatically organize loose TV episodes into proper show folders
- **Enhanced Search** - Improved fuzzy matching finds partial matches (e.g., "kin" finds "Vikings", "Tulsa King")
- **Advanced Duplicate Detection** - Multi-layered duplicate detection with 58% false positive reduction
- **Safe Duplicate Deletion** - Multiple safety modes: dry-run (preview), trash (recoverable), permanent
- **Folder Analysis** - Analyze existing TV directory structure and organization
- **Smart Cleanup** - Automatically remove empty and small folders after organization
- **Safety First** - Dry run mode shows what would be changed before making any moves

### 🤖 AI-Powered Media Assistant
- **Natural Language Queries** - Ask questions like "Do I have The Batman?" or "How many seasons of Breaking Bad do I have?"
- **Smart Search** - Uses fuzzy matching and AI-powered query processing for accurate results
- **Database Caching** - SQLite database for lightning-fast searches across large collections
- **External API Integration** - TMDB/TVDB integration for enhanced metadata and missing episode detection
- **Missing Episode Analysis** - Find gaps in your TV show collections with completeness reporting

### 🤖 AI-Powered Auto-Organizer  
- **Intelligent Classification** - Uses AWS Bedrock Claude 3.5 Sonnet to identify media types
- **Multi-Format Support** - Handles movies, TV shows, documentaries, stand-up comedy, and audiobooks
- **Smart Directory Selection** - Automatically chooses appropriate Plex directories with space checking
- **Robust Fallback** - Falls back to rule-based classification when AI is unavailable
- **Multi-Directory Support** - Tries alternative directories when primary locations are full

### 📊 Reporting
- **Multiple Formats** - Reports available in both human-readable (.txt) and machine-readable (.json) formats
- **Timestamped** - All reports are timestamped for easy tracking
- **Comprehensive** - Detailed analysis with file sizes, paths, and recommendations

## 📦 Installation

```bash
# Install in development mode
pip install -e .

# Install with development dependencies
pip install -e ".[dev]"
```

## 🚀 **Unified CLI Quick Start**

### Installation and Setup
```bash
# Install the package
pip install -e .

# Set up the plex-cli alias (recommended)
echo 'plex-cli() {
    if [ $# -eq 0 ]; then
        python3 -m file_managers.cli.personal_cli --interactive
    else
        python3 -m file_managers.cli.personal_cli "$@"
    fi
}' >> ~/.bashrc
source ~/.bashrc
```

### Using the Unified CLI

#### **Interactive Mode (Recommended for Beginners)**
```bash
# Start the interactive menu system
plex-cli

# Navigate through organized menus:
# 1. Files - Duplicates, database, auto-organize
# 2. Movies - Duplicates, search, reports  
# 3. TV - Organize, search, missing episodes, reports
# 4. Media - AI assistant, database, status
# 5. Config - Show settings, paths, API management
```

#### **Direct Commands (Power Users)**

**File Operations:**
```bash
plex-cli files duplicates --type movies     # Find movie duplicates
plex-cli files database --rebuild           # Rebuild media database
plex-cli files organize                     # Auto-organize downloads (dry-run)
plex-cli files organize --execute           # Actually organize files
plex-cli files organize --no-ai             # Rule-based classification only
```

**Movie Management:**
```bash
plex-cli movies duplicates                  # Find duplicate movies
plex-cli movies duplicates --delete         # Interactive deletion mode
plex-cli movies search "The Batman"         # Search movie collection
plex-cli movies reports                     # Generate comprehensive reports
```

**TV Show Management:**
```bash
plex-cli tv organize                        # Analyze TV episode organization
plex-cli tv organize --demo                 # Preview what would be moved
plex-cli tv organize --execute              # Actually move files
plex-cli tv search "Breaking Bad"           # Search TV shows (enhanced fuzzy matching)
plex-cli tv missing "Game of Thrones"       # Find missing episodes
plex-cli tv reports                         # Generate TV reports
```

**Advanced TV File Organizer (Standalone):**
```bash
# Enhanced duplicate detection and analysis
python3 -m file_managers.plex.tv_organizer.cli.tv_organizer_cli duplicates --scan --report

# Safe deletion modes (with extensive safety checks)
python3 -m file_managers.plex.tv_organizer.cli.tv_organizer_cli duplicates --scan --delete --mode dry-run
python3 -m file_managers.plex.tv_organizer.cli.tv_organizer_cli duplicates --scan --delete --mode trash --confidence 90

# Directory structure analysis and path resolution
python3 -m file_managers.plex.tv_organizer.cli.tv_organizer_cli resolve --analyze --report
python3 -m file_managers.plex.tv_organizer.cli.tv_organizer_cli resolve --stats
```

**Cross-Media Operations:**
```bash
plex-cli media assistant "Do I have Inception?"     # AI-powered search
plex-cli media assistant --interactive              # Interactive AI mode
plex-cli media database --rebuild                   # Database management
plex-cli media status                               # System status check
```

**Configuration Management:**
```bash
plex-cli config show                        # View all configuration
plex-cli config paths                       # Show directory paths
plex-cli config apis                        # API configuration help
plex-cli config apis --check                # Test API connectivity
```

### Help System
```bash
plex-cli --help                            # Main help
plex-cli movies --help                     # Movie commands help
plex-cli tv organize --help                # Specific command help
```

---

## 🛠️ **Legacy CLI Commands** (Still Available)

### Movie Duplicate Detection and Reports

```bash
# Generate movie inventory and duplicate reports
python -m file_managers.plex.utils.report_generator

# Interactive movie duplicate scanner
python -m file_managers.plex.cli.movie_duplicates

# Scan custom directories
python -m file_managers.plex.cli.movie_duplicates --custom "/path/to/movies1,/path/to/movies2"
```

### AI-Powered Media Assistant

```bash
# Interactive natural language media search
python -m file_managers.plex.cli.media_assistant --interactive

# Single query mode
python -m file_managers.plex.cli.media_assistant "Do I have the movie The Batman?"

# Season and episode analysis
python -m file_managers.plex.cli.media_assistant "Am I missing episodes for Game of Thrones season 8?"

# Rebuild database cache for faster searches
python -m file_managers.plex.cli.media_assistant --rebuild-db
```

### Media Database Management

```bash
# Rebuild the entire media database
python -m file_managers.plex.cli.media_database_cli --rebuild

# Show database status and statistics
python -m file_managers.plex.cli.media_database_cli --status

# Show detailed database statistics
python -m file_managers.plex.cli.media_database_cli --stats
```

### TV Show Organization

```bash
# Analyze TV directories (dry run - safe)
python -m file_managers.plex.utils.tv_mover

# Actually organize episodes and clean up folders
python -m file_managers.plex.utils.tv_mover --execute

# Generate TV analysis reports
python -m file_managers.plex.utils.tv_report_generator
```

### Auto-Organizer (AI-Powered)

```bash
# Preview AI-powered organization (safe dry run) 
python -m file_managers.plex.utils.auto_organizer --verbose

# Actually organize files with AI classification
python -m file_managers.plex.utils.auto_organizer --execute

# Note: Generates detailed reports showing exactly where each file was moved
# Reports saved to: reports/auto_organizer_YYYYMMDD_HHMMSS.txt
```

## ⚙️ Configuration

### Centralized Configuration
All media paths and settings are centralized in `file_managers/plex/config/media_config.yaml`. This makes it easy to:
- Update directory paths in one place
- Modify file size thresholds  
- Change video file extensions
- Adjust safety settings

### Pre-configured Directories
The package comes pre-configured for QNAP NAS servers:

**Movie Directories:**
- `/mnt/qnap/plex/Movie/`
- `/mnt/qnap/Media/Movies/`
- `/mnt/qnap/Multimedia/Movies/`

**TV Directories:**
- `/mnt/qnap/plex/TV/`
- `/mnt/qnap/Media/TV/`
- `/mnt/qnap/Multimedia/TV/`

### Customization
1. **Edit Configuration File:** Modify `file_managers/plex/config/media_config.yaml`
2. **Command Line Override:** Use `--custom` flag for one-time custom directories:
```bash
python -m file_managers.plex.utils.tv_mover --custom "/my/tv/path1,/my/tv/path2"
```

### Key Settings
- **Small Folder Threshold:** 100MB (configurable)
- **Video Extensions:** .mp4, .mkv, .avi, .mov, .wmv, etc.
- **Report Formats:** Text (.txt) and JSON (.json)
- **Safety Features:** Dry run mode, confirmations, backups
- **AI Classification:** Optional AWS Bedrock integration for intelligent media type detection

### External API Configuration (Optional)
For enhanced AI-powered features, create a `.env` file in the project root:

```bash
# .env file - AI Media Assistant & Auto-Organizer
TMDB_API_KEY=your_tmdb_key_here
TVDB_API_KEY=your_tvdb_key_here
AWS_ACCESS_KEY_ID=your_access_key_here
AWS_SECRET_ACCESS_KEY=your_secret_key_here
AWS_DEFAULT_REGION=us-east-1
BEDROCK_MODEL_ID=anthropic.claude-3-5-sonnet-20241022-v2:0
```

**Benefits with API keys:**
- **TMDB/TVDB**: Enhanced metadata, missing episode detection, external database suggestions
- **AWS Bedrock**: Advanced AI-powered query processing and media classification
- **Fallback**: All features work without API keys using pattern matching and local data

**Note:** All features work without API keys, but external APIs provide enhanced accuracy and suggestions.

## 🔄 How Auto-Organizer Works

The AI-powered auto-organizer follows a sophisticated 5-step workflow to intelligently organize your downloaded media files:

### **Step 1: 🔍 File Discovery**
```
Downloads Directory: /mnt/d/Completed/
├── The.Dark.Knight.2008.1080p.BluRay.x264.mkv
├── Game.of.Thrones.S01E01.720p.HDTV.x264.mkv  
├── Planet.Earth.Documentary.2006.1080p.mkv
└── Dave.Chappelle.Sticks.and.Stones.2019.mp4
```
- Recursively scans the downloads directory (`/mnt/d/Completed/`)
- Identifies video files based on extensions (.mp4, .mkv, .avi, etc.)
- Calculates file sizes for space management

### **Step 2: 🤖 AI Classification**
```
🤖 Classifying 4 files using AI...
[1/4] The.Dark.Knight.2008.1080p.BluRay.x264.mkv
    Type: MOVIE (AI), Target: /mnt/qnap/plex/Movie/
[2/4] Game.of.Thrones.S01E01.720p.HDTV.x264.mkv  
    Type: TV (AI), Target: /mnt/qnap/plex/TV/
[3/4] Planet.Earth.Documentary.2006.1080p.mkv
    Type: DOCUMENTARY (AI), Target: /mnt/qnap/Media/Documentary/
[4/4] Dave.Chappelle.Sticks.and.Stones.2019.mp4
    Type: STANDUP (AI), Target: /mnt/qnap/Media/standups/
```
- **Primary**: Uses AWS Bedrock Claude 3.5 Sonnet for intelligent classification
- **Fallback**: Rule-based pattern matching when AI is unavailable  
- **Categories**: MOVIE, TV, DOCUMENTARY, STANDUP, AUDIOBOOK, OTHER
- **Classification Source**: Clearly shows whether each result came from "AI" or "Rule-based" classification

### **Step 3: 📂 Directory Mapping**
```
Classification Results:
├── MOVIE → /mnt/qnap/plex/Movie/ (primary)
│           /mnt/qnap/Media/Movies/ (fallback)
│           /mnt/qnap/Multimedia/Movies/ (tertiary)
├── TV → /mnt/qnap/plex/TV/ (primary)
│        /mnt/qnap/Media/TV/ (fallback)  
│        /mnt/qnap/Multimedia/TV/ (tertiary)
├── DOCUMENTARY → /mnt/qnap/Media/Documentary/ (primary)
└── STANDUP → /mnt/qnap/Media/standups/ (primary)
```
- Maps each media type to appropriate Plex directories
- Provides multiple fallback locations for space management
- Prioritizes directories based on configuration

### **Step 4: 💾 Smart Organization**
```
📦 Organizing 4 files...
├── MOVIE: The.Dark.Knight.2008.1080p.BluRay.x264.mkv
│   ├── ✓ Space check: /mnt/qnap/plex/Movie/ (15.2GB available)
│   ├── ✓ Create directory if needed
│   └── ✅ Move: /mnt/qnap/plex/Movie/The.Dark.Knight.2008.1080p.BluRay.x264.mkv
├── TV: Game.of.Thrones.S01E01.720p.HDTV.x264.mkv
│   ├── ⚠️ Space check: /mnt/qnap/plex/TV/ (insufficient space)
│   ├── ✓ Fallback: /mnt/qnap/Media/TV/ (8.7GB available)
│   └── ✅ Move: /mnt/qnap/Media/TV/Game.of.Thrones.S01E01.720p.HDTV.x264.mkv
└── [continues for all files...]
```
- **Space Checking**: Verifies sufficient disk space (file size + 1GB buffer)
- **Directory Creation**: Creates target directories if they don't exist
- **Conflict Resolution**: Handles filename conflicts with numbering
- **Fallback Logic**: Tries alternative directories if primary is full

### **Step 5: 📊 Comprehensive Reporting**
```
📄 AUTO-ORGANIZER REPORT
============================================================
Generated: 2025-06-14 18:30:15
Mode: DRY RUN / EXECUTION
Total Files Processed: 4
Successful Moves: 4
Failed Moves: 0
Total Space Freed: 12.8 GB

✅ SUCCESSFUL MOVES:
────────────────────
The.Dark.Knight.2008.1080p.BluRay.x264.mkv
  FROM: /mnt/d/Completed/The.Dark.Knight.2008.1080p.BluRay.x264.mkv
  TO:   /mnt/qnap/plex/Movie/The.Dark.Knight.2008.1080p.BluRay.x264.mkv
  SIZE: 4.2 GB
  TYPE: MOVIE (AI Classification)

Game.of.Thrones.S01E01.720p.HDTV.x264.mkv
  FROM: /mnt/d/Completed/Game.of.Thrones.S01E01.720p.HDTV.x264.mkv
  TO:   /mnt/qnap/Media/TV/Game.of.Thrones.S01E01.720p.HDTV.x264.mkv
  SIZE: 2.1 GB  
  TYPE: TV (AI Classification)

Planet.Earth.Documentary.2006.1080p.mkv
  FROM: /mnt/d/Completed/Planet.Earth.Documentary.2006.1080p.mkv
  TO:   /mnt/qnap/Media/Documentary/Planet.Earth.Documentary.2006.1080p.mkv
  SIZE: 3.8 GB
  TYPE: DOCUMENTARY (AI Classification)

Dave.Chappelle.Sticks.and.Stones.2019.mp4
  FROM: /mnt/d/Completed/Dave.Chappelle.Sticks.and.Stones.2019.mp4
  TO:   /mnt/qnap/Media/standups/Dave.Chappelle.Sticks.and.Stones.2019.mp4
  SIZE: 2.7 GB
  TYPE: STANDUP (AI Classification)

❌ FAILED MOVES:
────────────────────
Large.Movie.File.2024.4K.UHD.mkv
  FROM: /mnt/d/Completed/Large.Movie.File.2024.4K.UHD.mkv
  INTENDED TARGET: /mnt/qnap/plex/Movie/
  TYPE: MOVIE (AI Classification)
  ERROR: All target directories failed (space or access issues)
```

### **🛡️ Safety Features**
- **Dry Run Mode**: Preview all operations before execution (default)
- **Confirmation Required**: Must type "ORGANIZE" to proceed with actual moves
- **Detailed Logging**: Complete audit trail of all operations
- **Error Recovery**: Graceful handling of network issues, permission errors, etc.
- **Rollback Capable**: Maintains source/target paths for potential rollback

### **📈 Intelligence Features**
- **Pattern Recognition**: Learns from filename patterns and structures
- **Quality Detection**: Identifies resolution, codec, and source information
- **Series Detection**: Recognizes season/episode patterns (S01E01, 1x01, etc.)
- **Source Analysis**: Distinguishes between BluRay, WEBRip, HDTV sources
- **Multi-Language**: Handles international titles and naming conventions

### 📋 **Enhanced Report Details**

Every auto-organizer operation generates a comprehensive report with complete transparency:

#### **✅ Successful Moves Include:**
- **Complete File Paths**: Full source and destination paths with filenames
- **File Sizes**: Human-readable format (4.2 GB, 1.8 MB, etc.)
- **Classification Details**: MOVIE, TV, DOCUMENTARY, STANDUP, AUDIOBOOK
- **Classification Source**: "(AI Classification)" or "(Rule-based Classification)"
- **Exact Destinations**: Shows precisely where each file was moved

#### **❌ Failed Moves Include:**
- **Source Path**: Complete path to the file that couldn't be moved
- **Intended Target**: Shows where the file was supposed to go
- **Classification Info**: Type and source of classification
- **Specific Error**: Detailed reason for failure (space, permissions, network, etc.)

#### **📊 Summary Statistics:**
- Total files processed
- Successful vs failed move counts  
- Total disk space freed/organized
- Execution mode (DRY RUN vs EXECUTION)
- Timestamp for tracking

This comprehensive reporting ensures you always know exactly what happened during organization, making the process completely transparent and auditable.

## 🔧 Detailed Usage

### Movie Management

#### 1. Movie Duplicate Detection
```bash
# Basic duplicate scan with predefined directories
python -m file_managers.plex.cli.movie_duplicates

# Scan custom directories
python -m file_managers.plex.cli.movie_duplicates --custom "C:/Movies,D:/Films"

# Interactive deletion mode (DANGEROUS - creates backups)
python -m file_managers.plex.cli.movie_duplicates --delete
```

#### 2. Movie Report Generation
```bash
# Generate comprehensive movie reports
python -m file_managers.plex.utils.report_generator

# Reports are saved to reports/ directory:
# - movie_inventory_YYYYMMDD_HHMMSS.txt/json
# - duplicates_YYYYMMDD_HHMMSS.txt/json
```

### TV Show Management

#### 1. TV Episode Organization
```bash
# Preview what would be organized (safe dry run)
python -m file_managers.plex.utils.tv_mover

# Actually move episodes to proper folders
python -m file_managers.plex.utils.tv_mover --execute

# Verbose output showing scan progress
python -m file_managers.plex.utils.tv_mover --verbose

# Find and delete small folders (<100MB) before organizing
python -m file_managers.plex.utils.tv_mover --delete-small --execute
```

**TV Mover Features:**
- ✅ Finds loose episodes outside show folders
- ✅ Moves episodes to existing show folders or creates new ones
- ✅ Automatically cleans up empty/small folders after moves
- ✅ Handles file conflicts by renaming
- ✅ Safety confirmations before making changes

#### 2. TV Analysis and Reports
```bash
# Generate TV folder analysis reports
python -m file_managers.plex.utils.tv_report_generator
```

### Advanced TV File Organizer (Standalone Module)

#### 1. Enhanced Duplicate Detection with Deletion
```bash
# Safe preview of duplicate detection (no files touched)
python3 -m file_managers.plex.tv_organizer.cli.tv_organizer_cli duplicates --scan

# Generate comprehensive duplicate report
python3 -m file_managers.plex.tv_organizer.cli.tv_organizer_cli duplicates --scan --report

# Preview what would be deleted (completely safe)
python3 -m file_managers.plex.tv_organizer.cli.tv_organizer_cli duplicates --scan --delete --mode dry-run

# Move duplicates to trash (recoverable deletion)
python3 -m file_managers.plex.tv_organizer.cli.tv_organizer_cli duplicates --scan --delete --mode trash

# High-confidence deletion only (90%+ confidence)
python3 -m file_managers.plex.tv_organizer.cli.tv_organizer_cli duplicates --scan --delete --mode trash --confidence 90

# Show statistics only
python3 -m file_managers.plex.tv_organizer.cli.tv_organizer_cli duplicates --stats
```

**Advanced Duplicate Detection Features:**
- ✅ **Enhanced False Positive Filtering** - Reduces false positives by 58%
- ✅ **Content Analysis** - Distinguishes different episodes vs true duplicates
- ✅ **Confidence Scoring** - Only processes high-confidence matches (80%+ default)
- ✅ **Multi-Mode Deletion** - dry-run (preview), trash (safe), permanent (dangerous)
- ✅ **Safety Validation** - File existence, lock status, size checks, user confirmation
- ✅ **Production Tested** - 10,493 episodes, 558 duplicate groups, 134GB space savings

#### 2. Directory Structure Analysis and Path Resolution
```bash
# Analyze TV directory organization and generate comprehensive report
python3 -m file_managers.plex.tv_organizer.cli.tv_organizer_cli resolve --analyze --report

# Show organization statistics
python3 -m file_managers.plex.tv_organizer.cli.tv_organizer_cli resolve --stats

# Scan for path resolution opportunities  
python3 -m file_managers.plex.tv_organizer.cli.tv_organizer_cli resolve --scan

# Show specific show path resolution
python3 -m file_managers.plex.tv_organizer.cli.tv_organizer_cli resolve --show "Breaking Bad"

# Generate JSON output for automation
python3 -m file_managers.plex.tv_organizer.cli.tv_organizer_cli resolve --analyze --format json --output analysis.json
```

**Path Resolution Features:**
- ✅ **Directory Structure Mapping** - Comprehensive analysis of TV show organization patterns
- ✅ **Fuzzy Show Name Matching** - Advanced similarity matching (80% threshold)
- ✅ **Multi-Factor Scoring** - Match (40%), organization (30%), space (20%), proximity (10%)
- ✅ **Organization Quality Scoring** - 0-100 scoring system for show directories
- ✅ **Production Results** - 327 shows, 9,979 episodes, 312 shows needing attention

#### 3. Module Status and Help
```bash
# Show module status and available phases
python3 -m file_managers.plex.tv_organizer.cli.tv_organizer_cli status

# Show configuration
python3 -m file_managers.plex.tv_organizer.cli.tv_organizer_cli config --show

# Get help for specific commands
python3 -m file_managers.plex.tv_organizer.cli.tv_organizer_cli duplicates --help
python3 -m file_managers.plex.tv_organizer.cli.tv_organizer_cli resolve --help
```

## 📊 Report Types

### Movie Reports
- **Inventory Report** - Complete movie library overview with sizes and statistics
- **Duplicate Report** - Detailed duplicate analysis with space savings calculations

### TV Reports  
- **Folder Analysis** - Current TV directory structure and organization
- **Organization Plan** - What episodes would be moved during organization

### Advanced TV File Organizer Reports
- **Enhanced Duplicate Report** - Comprehensive duplicate analysis with confidence scores and false positive filtering
- **Path Resolution Report** - Directory structure analysis with organization quality scoring (0-100)
- **Deletion Reports** - Detailed deletion operation reports with safety validation results

All reports are saved to the `reports/` directory (or `reports/tv/` for TV File Organizer) in both `.txt` and `.json` formats.

## 🛡️ Safety Features

### Dry Run Mode
All tools default to dry run mode, showing what would be changed without making any modifications:
```bash
# Safe preview (default)
python -m file_managers.plex.utils.tv_mover

# Actually execute changes
python -m file_managers.plex.utils.tv_mover --execute
```

### Confirmation Prompts
Operations that modify files require explicit confirmation:
```bash
Type 'EXECUTE' to proceed with moving 15 episodes: EXECUTE
```

### Automatic Cleanup
The TV mover automatically cleans up empty or small folders (<100MB) after moving episodes, keeping your directories tidy.

## 🏗️ Architecture

```
file_managers/
├── utils/                     # General utilities
│   └── file_utils.py         # File operations
├── cli/                      # Command-line interfaces
│   └── file_manager.py       # General file management
└── plex/                     # Plex-specific functionality
    ├── config/              # Configuration management
    │   ├── config.py              # Python configuration interface
    │   └── media_config.yaml      # YAML configuration file
    ├── utils/               # Plex utilities
    │   ├── movie_scanner.py       # Movie duplicate detection
    │   ├── report_generator.py    # Movie report generation
    │   ├── tv_scanner.py          # TV episode detection
    │   ├── tv_report_generator.py # TV report generation
    │   ├── tv_mover.py            # TV episode organization
    │   ├── deletion_manager.py    # Interactive deletion
    │   ├── ai_query_processor.py  # AI-powered query processing
    │   ├── episode_analyzer.py    # TV episode completeness analysis
    │   ├── external_api.py        # External API integrations (TMDB/TVDB)
    │   ├── media_searcher.py      # Media search and matching
    │   └── media_database.py      # SQLite database for fast searches
    ├── tv_organizer/        # Advanced TV File Organizer (Standalone Module)
    │   ├── cli/
    │   │   └── tv_organizer_cli.py    # Standalone CLI with deletion functionality
    │   ├── core/
    │   │   ├── duplicate_detector.py  # Enhanced duplicate detection with deletion
    │   │   └── path_resolver.py       # Directory structure analysis
    │   ├── models/
    │   │   ├── episode.py             # Episode data structures
    │   │   ├── duplicate.py           # Duplicate groups and deletion plans
    │   │   └── path_resolution.py     # Path resolution models
    │   └── INSTRUCTIONS.md            # Comprehensive usage documentation
    └── cli/                 # Plex CLI tools
        ├── movie_duplicates.py    # Movie duplicate scanner
        ├── media_assistant.py     # AI-powered media assistant
        └── media_database_cli.py  # Database management CLI
```

## 🔧 Development

### Code Quality
```bash
# Format code
black .

# Lint code
ruff check .

# Type checking
mypy file_managers
```

### Testing
```bash
# Run all tests
pytest

# Run specific test files
pytest tests/test_file_utils.py
pytest tests/test_movie_scanner.py
```

## 🌟 Key Benefits

- **🎯 Automated** - Intelligent detection and organization of media files
- **🛡️ Safe** - Dry run modes and confirmations prevent accidental data loss  
- **📊 Comprehensive** - Detailed reports for tracking and analysis
- **🧹 Clean** - Automatic cleanup of empty and unnecessary folders
- **⚙️ Flexible** - Support for custom directories and configurations
- **🚀 Fast** - Efficient scanning and processing of large media libraries
- **🔍 Enhanced Search** - Improved fuzzy matching finds partial matches (e.g., "kin" → "Vikings", "Tulsa King")
- **🗑️ Safe Deletion** - Multi-layered duplicate deletion with 58% false positive reduction
- **📈 Production Tested** - 10,000+ episodes tested, 134GB+ space savings identified

## 📝 Examples

### Complete Movie Analysis Workflow
```bash
# 1. Generate comprehensive movie reports
python -m file_managers.plex.utils.report_generator

# 2. Review duplicates interactively
python -m file_managers.plex.cli.movie_duplicates

# 3. Delete duplicates if desired (creates backups)
python -m file_managers.plex.cli.movie_duplicates --delete
```

### Complete TV Organization Workflow
```bash
# 1. Preview what would be organized
python -m file_managers.plex.utils.tv_mover --verbose

# 2. Generate detailed TV reports
python -m file_managers.plex.utils.tv_report_generator

# 3. Actually organize episodes
python -m file_managers.plex.utils.tv_mover --execute
```

## ⚠️ Important Notes

- **Backup First** - Always backup your media files before running organization tools
- **Network Shares** - Ensure QNAP/NAS shares are properly mounted before running tools
- **Permissions** - Verify you have read/write permissions to all directories
- **Testing** - Use dry run mode first to preview changes

## 🤝 Contributing

1. Follow the existing code style and patterns
2. Add type hints for all new functions
3. Include comprehensive error handling
4. Test with various file structures before submitting

---

**File Managers** - Keeping your Plex media library organized and optimized! 🎬📺