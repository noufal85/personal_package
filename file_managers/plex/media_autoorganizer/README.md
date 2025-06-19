# Media Auto-Organizer

An intelligent media file organization system that automatically classifies and moves downloaded media files to appropriate Plex directories using AI and rule-based classification.

## Features

- **Intelligent TV Episode Placement**: Automatically finds existing show directories and places episodes with their shows
- **Smart Directory Fallback**: Tries multiple QNAP directories when one fails due to space or access issues
- **AI-Powered Classification**: Uses AWS Bedrock for accurate media type detection with rule-based fallback
- **Comprehensive Caching**: Multi-tier caching (SQLite + CSV) to avoid repeated classifications
- **Mount Access Validation**: Verifies all target directories before processing
- **Space Management**: Checks available space and includes 1GB safety buffer
- **Detailed Reporting**: Generates comprehensive reports with show information and move results
- **Conflict Resolution**: Handles filename conflicts automatically
- **Dry Run Mode**: Preview all moves before execution

## Architecture

The system is modularly designed with separate components for different responsibilities:

```
media_autoorganizer/
├── __init__.py              # Package initialization and exports
├── README.md                # This documentation
├── cli.py                   # Command-line interface
├── organizer.py             # Main AutoOrganizer orchestrator class
├── models.py                # Data structures (MediaFile, MoveResult, etc.)
├── media_database.py        # Interface to existing media database
├── classification_db.py     # SQLite caching for classifications
└── ai_classifier.py         # AWS Bedrock AI classification
```

## Components

### 1. AutoOrganizer (`organizer.py`)

**Main orchestrator class that coordinates the entire workflow.**

**Key Methods:**
- `verify_mount_access()`: Validates all target directories are accessible
- `scan_downloads()`: Scans downloads directory for media files
- `classify_files()`: Classifies files using multi-tier approach
- `organize_files()`: Moves files to appropriate locations
- `run_full_organization()`: Executes complete workflow
- `generate_report()`: Creates detailed move reports

**Usage:**
```python
from file_managers.plex.media_autoorganizer import AutoOrganizer

# Dry run mode (default)
organizer = AutoOrganizer(dry_run=True, use_ai=True)
report_path = organizer.run_full_organization()

# Execute mode with AI disabled
organizer = AutoOrganizer(dry_run=False, use_ai=False)
report_path = organizer.run_full_organization()
```

### 2. MediaDatabase (`media_database.py`)

**Interfaces with the prebuilt JSON media database to find existing TV show locations.**

**Key Methods:**
- `find_tv_show_location(show_name)`: Finds existing directory for a TV show
- `extract_tv_info(filename)`: Extracts show name, season, episode from filename
- `mark_directory_failed(directory)`: Tracks failed directories to avoid repeated attempts

**TV Show Matching:**
- Exact name matching
- Fuzzy matching with normalization
- Year removal and special character handling
- Word-by-word similarity scoring

**Filename Pattern Support:**
- `Show.Name.S01E01.Title.mkv`
- `Show Name - S01E01 - Title.mkv`
- `Show.Name.1x01.Title.mkv`
- `Show Name (2023) S01E01.mkv`
- `[Group] Show Name - 01 [Season 1].mkv`

### 3. ClassificationDatabase (`classification_db.py`)

**SQLite database for persistent classification caching.**

**Key Methods:**
- `get_classification(filename)`: Retrieves cached classification
- `store_classification()`: Stores single classification
- `store_batch_classifications()`: Stores multiple classifications efficiently
- `get_stats()`: Returns database statistics
- `clear_database()`: Clears all cached data

**Database Schema:**
```sql
CREATE TABLE classifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT NOT NULL UNIQUE,
    media_type TEXT NOT NULL,
    classification_source TEXT NOT NULL,
    confidence REAL DEFAULT 0.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 4. BedrockClassifier (`ai_classifier.py`)

**AI-powered classification using AWS Bedrock with intelligent fallback.**

**Key Methods:**
- `classify_batch(filenames)`: Processes multiple files in one API call
- `classify_file(filename)`: Classifies single file
- `_fallback_classification(filename)`: Rule-based fallback when AI unavailable

**AI Features:**
- Supports Anthropic Claude and Llama models
- Batch processing for efficiency (10 files per batch)
- Exponential backoff with jitter for throttling
- Automatic fallback to rule-based classification
- Model access validation and error handling

**Rule-Based Patterns:**
- **TV Shows**: `s01`, `season`, `episode`, `hdtv`, etc.
- **Documentaries**: `documentary`, `bbc`, `nat geo`, etc.
- **Stand-up**: `standup`, `comedy special`, `live at`, etc.

### 5. Data Models (`models.py`)

**Core data structures used throughout the system.**

**MediaType Enum:**
- `MOVIE`: Feature films
- `TV`: TV series episodes
- `DOCUMENTARY`: Documentary content
- `STANDUP`: Stand-up comedy specials
- `AUDIOBOOK`: Audio books
- `OTHER`: Unclassified content

**MediaFile NamedTuple:**
```python
MediaFile(
    path: Path,              # File/directory path
    size: int,               # Size in bytes
    media_type: MediaType,   # Classified type
    target_directory: str,   # Target location
    classification_source: str,  # How it was classified
    show_name: str,          # TV show name (if applicable)
    season: int,             # Season number (if applicable)
    episode: int             # Episode number (if applicable)
)
```

**MoveResult NamedTuple:**
```python
MoveResult(
    success: bool,           # Move success status
    source_path: Path,       # Original location
    target_path: Path,       # New location (if successful)
    error: str,              # Error message (if failed)
    space_freed: int         # Bytes freed from downloads
)
```

### 6. Command Line Interface (`cli.py`)

**Comprehensive CLI with all options for interactive and automated use.**

**Key Features:**
- Dry run and execution modes
- AI enable/disable options
- Database management commands
- Mount verification utilities
- Verbose and quiet output modes

## Usage

### Basic Usage

```bash
# Dry run (preview mode - default)
python -m file_managers.plex.media_autoorganizer.cli

# Actually move files
python -m file_managers.plex.media_autoorganizer.cli --execute

# Use rule-based classification only (faster, no AI costs)
python -m file_managers.plex.media_autoorganizer.cli --no-ai
```

### Database Management

```bash
# Show classification statistics
python -m file_managers.plex.media_autoorganizer.cli --db-stats

# Clear cached classifications
python -m file_managers.plex.media_autoorganizer.cli --clear-db
```

### System Verification

```bash
# Verify mount access only
python -m file_managers.plex.media_autoorganizer.cli --verify-mounts

# Verbose output for debugging
python -m file_managers.plex.media_autoorganizer.cli --verbose
```

### Full Example

```bash
# Complete workflow with execution
python -m file_managers.plex.media_autoorganizer.cli --execute --verbose
```

## Workflow

1. **Mount Verification**: Checks all target directories for accessibility and write permissions
2. **File Scanning**: Scans downloads directory for media files and directories
3. **Classification**: Uses multi-tier approach:
   - Check SQLite database cache
   - Check CSV cache
   - Apply obvious rule-based patterns
   - Use AI classification for remaining files
4. **TV Show Placement**: For TV episodes:
   - Extract show name, season, episode from filename
   - Search existing media database for show location
   - Use existing location or create new show directory
5. **File Organization**: Move files with:
   - Space availability checking
   - Directory access validation
   - Filename conflict resolution
   - Smart fallback across multiple directories
6. **Reporting**: Generate detailed reports with:
   - Move success/failure status
   - Show information for TV episodes
   - Space freed calculations
   - Error details for failures

## Configuration

The system uses the existing configuration from `file_managers/plex/config/config.py`:

- **Downloads Directory**: `/mnt/e/tors2/completed/`
- **Movie Directories**: 3 QNAP directories with priority fallback
- **TV Directories**: 3 QNAP directories with priority fallback
- **Video Extensions**: Configurable list of supported formats
- **AWS Bedrock Settings**: Model, region, tokens, temperature

## Directory Structure

### Target Directories

**Movies:**
- `/mnt/qnap/plex/Movie/` (Primary)
- `/mnt/qnap/Media/Movies/` (Secondary)
- `/mnt/qnap/Multimedia/Movies/` (Tertiary)

**TV Shows:**
- `/mnt/qnap/plex/TV/` (Primary)
- `/mnt/qnap/Media/TV/` (Secondary)
- `/mnt/qnap/Multimedia/TV/` (Tertiary)

**Documentaries:**
- `/mnt/qnap/Media/Documentary/`

**Stand-up Comedy:**
- `/mnt/qnap/Media/standups/`

### Smart Placement Logic

**For TV Episodes:**
1. Extract show name from filename
2. Search media database for existing show directory
3. If found: Place episode in existing show directory
4. If not found: Create new show directory in available TV base directory
5. If creation fails: Try next available TV directory

**For Movies:**
1. Try primary movie directory
2. If space/access issues: Try secondary directory
3. If all fail: Report error with details

## Error Handling

### Directory Access Issues
- Tracks failed directories to avoid repeated attempts
- Falls back to alternative directories automatically
- Provides clear error messages with suggested solutions

### Space Management
- Checks available space before attempting moves
- Requires 1GB safety buffer beyond file size
- Falls back to directories with sufficient space

### Filename Conflicts
- Automatically resolves conflicts by adding numeric suffixes
- Preserves original filename structure
- Handles both files and directories

### AI Classification Issues
- Automatic fallback to rule-based classification
- Intelligent throttling and retry logic
- Graceful handling of API errors and credential issues

## Reports

Generated reports include:

### Summary Information
- Total files processed
- Successful vs failed moves
- Total space freed
- Processing mode (dry run vs execution)

### Successful Moves
- Source and target paths
- File sizes
- Media types and show information
- Classification sources

### Failed Moves
- Error descriptions
- Intended target directories
- Troubleshooting information

### Example Report
```
🤖 AUTO-ORGANIZER REPORT
============================================================
Generated: 2025-01-18 14:30:15
Mode: DRY RUN
Total Files Processed: 15
Successful Moves: 12
Failed Moves: 3
Total Space Freed: 45.2 GB

✅ SUCCESSFUL MOVES:
----------------------------------------
  Game.of.Thrones.S08E06.The.Iron.Throne.mkv
    FROM: /mnt/e/tors2/completed/Game.of.Thrones.S08E06.The.Iron.Throne.mkv
    TO:   /mnt/qnap/plex/TV/Game of Thrones/Game.of.Thrones.S08E06.The.Iron.Throne.mkv
    SIZE: 3.2 GB
    TYPE: TV - Game of Thrones S08E06 (Rule-based Classification)
```

## Dependencies

- **Python 3.8+**
- **boto3**: AWS Bedrock integration
- **pathlib**: Path handling
- **sqlite3**: Classification caching
- **csv**: Legacy cache support
- **json**: Media database parsing
- **re**: Pattern matching for show detection

## Performance Considerations

### Batch Processing
- AI classification processes files in batches of 10
- Reduces API calls and improves efficiency
- Includes intelligent delays between batches

### Caching Strategy
- SQLite database for persistent caching
- CSV fallback for legacy compatibility
- Multi-tier lookup for optimal performance

### Memory Usage
- Processes files incrementally
- Does not load entire media database into memory
- Efficient pattern matching and database queries

## Troubleshooting

### Common Issues

**Mount Access Failures:**
```bash
# Check mount status
python -m file_managers.plex.media_autoorganizer.cli --verify-mounts

# Remount QNAP shares if needed
sudo mount -t cifs //192.168.1.27/plex /mnt/qnap/plex -o username=noufal85,uid=$(id -u),gid=$(id -g),iocharset=utf8,file_mode=0777,dir_mode=0777
```

**AI Classification Issues:**
```bash
# Use rule-based only to avoid API issues
python -m file_managers.plex.media_autoorganizer.cli --no-ai

# Check AWS credentials
aws configure list
```

**Database Issues:**
```bash
# View database stats
python -m file_managers.plex.media_autoorganizer.cli --db-stats

# Clear cache if corrupted
python -m file_managers.plex.media_autoorganizer.cli --clear-db
```

### Debug Mode
```bash
# Verbose output for troubleshooting
python -m file_managers.plex.media_autoorganizer.cli --verbose --verify-mounts
```

## Future Enhancements

- Season-based organization within show directories
- Integration with external APIs (TMDB, TVDB) for metadata
- Web interface for remote management
- Scheduled/automated execution
- Integration with download clients
- Support for additional media types (music, books)
- Machine learning improvements for classification accuracy