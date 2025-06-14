# File Managers

A comprehensive Python package for managing Plex media libraries, providing tools for movie duplicate detection, TV show organization, and automated media management.

## 🚀 Features

### 🎬 Movie Management
- **Duplicate Detection** - Find and analyze duplicate movies across multiple directories
- **Smart Analysis** - Identify which files to keep based on quality and size
- **Comprehensive Reports** - Generate detailed inventory and duplicate reports
- **Space Optimization** - Calculate potential space savings from removing duplicates

### 📺 TV Show Management  
- **Episode Organization** - Automatically organize loose TV episodes into proper show folders
- **Folder Analysis** - Analyze existing TV directory structure and organization
- **Smart Cleanup** - Automatically remove empty and small folders after organization
- **Safety First** - Dry run mode shows what would be changed before making any moves

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

## 🛠️ Quick Start

### Movie Duplicate Detection and Reports

```bash
# Generate movie inventory and duplicate reports
python -m file_managers.plex.utils.report_generator

# Interactive movie duplicate scanner
python -m file_managers.plex.cli.movie_duplicates

# Scan custom directories
python -m file_managers.plex.cli.movie_duplicates --custom "/path/to/movies1,/path/to/movies2"
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

## 📁 Pre-configured Directories

The package comes pre-configured for QNAP NAS servers with the following directories:

### Movie Directories
- `/mnt/qnap/plex/Movie/`
- `/mnt/qnap/Media/Movies/`
- `/mnt/qnap/Multimedia/Movies/`

### TV Directories
- `/mnt/qnap/plex/TV/`
- `/mnt/qnap/Media/TV/`
- `/mnt/qnap/Multimedia/TV/`

### Custom Directories
All tools support custom directories via the `--custom` flag:
```bash
python -m file_managers.plex.utils.tv_mover --custom "/my/tv/path1,/my/tv/path2"
```

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

## 📊 Report Types

### Movie Reports
- **Inventory Report** - Complete movie library overview with sizes and statistics
- **Duplicate Report** - Detailed duplicate analysis with space savings calculations

### TV Reports  
- **Folder Analysis** - Current TV directory structure and organization
- **Organization Plan** - What episodes would be moved during organization

All reports are saved to the `reports/` directory in both `.txt` and `.json` formats.

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
    ├── utils/               # Plex utilities
    │   ├── movie_scanner.py       # Movie duplicate detection
    │   ├── report_generator.py    # Movie report generation
    │   ├── tv_scanner.py          # TV episode detection
    │   ├── tv_report_generator.py # TV report generation
    │   ├── tv_mover.py            # TV episode organization
    │   └── deletion_manager.py    # Interactive deletion
    └── cli/                 # Plex CLI tools
        └── movie_duplicates.py    # Movie duplicate scanner
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