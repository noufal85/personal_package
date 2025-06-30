# TV File Organizer CLI

**Advanced TV Episode Management with Safe Duplicate Deletion**

## Quick Start

From project root (`/home/noufal/personal_package`):

```bash
# Check module status and available phases
python3 -m file_managers.plex.tv_organizer.cli.tv_organizer_cli status

# Safe duplicate detection (no files touched)
python3 -m file_managers.plex.tv_organizer.cli.tv_organizer_cli duplicates --scan --report

# Preview deletion (completely safe)
python3 -m file_managers.plex.tv_organizer.cli.tv_organizer_cli duplicates --scan --delete --mode dry-run

# Directory structure analysis
python3 -m file_managers.plex.tv_organizer.cli.tv_organizer_cli resolve --analyze --report

# Get comprehensive help
python3 -m file_managers.plex.tv_organizer.cli.tv_organizer_cli --help
```

## Available Commands

### ✅ Phase 0: Enhanced Duplicate Detection (Complete)
```bash
# Basic duplicate scanning
python3 -m file_managers.plex.tv_organizer.cli.tv_organizer_cli duplicates --scan
python3 -m file_managers.plex.tv_organizer.cli.tv_organizer_cli duplicates --scan --report
python3 -m file_managers.plex.tv_organizer.cli.tv_organizer_cli duplicates --stats

# Safe deletion modes with extensive safety checks
python3 -m file_managers.plex.tv_organizer.cli.tv_organizer_cli duplicates --scan --delete --mode dry-run
python3 -m file_managers.plex.tv_organizer.cli.tv_organizer_cli duplicates --scan --delete --mode trash
python3 -m file_managers.plex.tv_organizer.cli.tv_organizer_cli duplicates --scan --delete --mode permanent

# Advanced options
python3 -m file_managers.plex.tv_organizer.cli.tv_organizer_cli duplicates --scan --delete --mode trash --confidence 90
python3 -m file_managers.plex.tv_organizer.cli.tv_organizer_cli duplicates --show "Breaking Bad"
```

**Key Features:**
- **Enhanced Filtering**: 58% false positive reduction with content analysis
- **Confidence Scoring**: 80% default threshold, configurable (70-95%)
- **Multi-Mode Deletion**: dry-run (preview), trash (recoverable), permanent (dangerous)
- **Safety Validation**: File existence, lock status, size checks, user confirmation
- **Production Tested**: 10,493 episodes, 558 duplicate groups, 134GB space savings

### ✅ Phase 2: Path Resolution (Complete)
```bash
# Directory structure analysis and reporting
python3 -m file_managers.plex.tv_organizer.cli.tv_organizer_cli resolve --analyze --report
python3 -m file_managers.plex.tv_organizer.cli.tv_organizer_cli resolve --stats

# Path resolution scanning
python3 -m file_managers.plex.tv_organizer.cli.tv_organizer_cli resolve --scan
python3 -m file_managers.plex.tv_organizer.cli.tv_organizer_cli resolve --scan --confidence high

# Show-specific analysis
python3 -m file_managers.plex.tv_organizer.cli.tv_organizer_cli resolve --show "Game of Thrones"

# JSON output for automation
python3 -m file_managers.plex.tv_organizer.cli.tv_organizer_cli resolve --analyze --format json --output analysis.json
```

**Key Features:**
- **Directory Mapping**: Comprehensive analysis of TV show organization patterns
- **Fuzzy Matching**: Advanced similarity matching (80% threshold) for show names
- **Multi-Factor Scoring**: Match (40%), organization (30%), space (20%), proximity (10%)
- **Quality Assessment**: 0-100 organization scoring for show directories
- **Production Results**: 327 shows, 9,979 episodes analyzed

### Utility Commands
```bash
# Configuration and status
python3 -m file_managers.plex.tv_organizer.cli.tv_organizer_cli config --show
python3 -m file_managers.plex.tv_organizer.cli.tv_organizer_cli status

# Help system
python3 -m file_managers.plex.tv_organizer.cli.tv_organizer_cli --help
python3 -m file_managers.plex.tv_organizer.cli.tv_organizer_cli duplicates --help
python3 -m file_managers.plex.tv_organizer.cli.tv_organizer_cli resolve --help
```

### 🚧 Future Phases (Planned)
- **Phase 1**: Loose Episode Detection (parked for future development)
- **Phase 3**: Safe File Organization Execution

## Deletion Safety Features

### Multiple Safety Layers
- **Dry-Run Mode**: Preview deletions without making any changes
- **Confidence Scoring**: Only delete duplicates with high confidence scores (80%+ default)
- **Safety Checks**: Verify file accessibility, size reasonableness, and lock status
- **User Confirmation**: Interactive confirmation for each deletion operation
- **Trash Mode**: Move files to system trash instead of permanent deletion
- **Force Protection**: Confirmations cannot be bypassed without explicit --force flag

### Deletion Modes
- **dry-run**: Preview only, no files modified (safest)
- **trash**: Move to system trash/recycle bin (safe, recoverable)
- **permanent**: Immediate deletion (dangerous, irreversible)

### Confidence Thresholds
- **80% (default)**: Balanced approach, good for most users
- **90%**: Conservative approach, fewer deletions but higher certainty
- **95%+**: Very conservative, only most obvious duplicates

## Output Formats

- **Text** (default): Human-readable reports with detailed analysis
- **JSON**: Machine-readable data (`--format json`) for automation
- **Reports**: Saved to `reports/tv/` directory with timestamps

## Real-World Performance

**Recent Production Test Results:**
- **10,493 episodes** scanned across 3 TV directories
- **558 duplicate groups** identified with 1,154 duplicate files
- **134 GB potential space savings** at 80% confidence threshold
- **155 safe operations** from 170 total (safety filtering working)
- **Enhanced filtering** reduces false positives by 58%
- **Scan time**: ~45 seconds for 10,000+ episodes

## Documentation

- **Comprehensive Guide**: `../INSTRUCTIONS.md` - Detailed usage instructions and safety information
- **Configuration**: Uses centralized config from `file_managers/plex/config/media_config.yaml`
- **Architecture**: See main project README.md for complete module structure

## Module Structure

```
tv_organizer/
├── INSTRUCTIONS.md                    # Comprehensive usage guide
├── cli/
│   ├── README.md                     # This file
│   └── tv_organizer_cli.py          # Main CLI with deletion functionality
├── core/
│   ├── duplicate_detector.py        # Enhanced duplicate detection with deletion
│   └── path_resolver.py             # Directory structure analysis
├── models/
│   ├── episode.py                   # Episode data structures
│   ├── duplicate.py                 # Duplicate groups and deletion plans
│   └── path_resolution.py           # Path resolution models
└── utils/                           # Utility functions
```

## Development Status

### ✅ **Phase 0: Complete** 
Enhanced duplicate detection with false positive filtering, content analysis, confidence scoring, and safe multi-mode deletion system.

### ✅ **Phase 2: Complete**
Directory structure mapping, fuzzy show name matching, multi-factor destination scoring, and comprehensive organization analysis.

### 🚧 **Future Development**
- Phase 1: Loose Episode Detection (parked)
- Phase 3: Safe file organization execution

---

**TV File Organizer** - Production-ready duplicate detection and directory analysis for large TV collections! 📺🔍