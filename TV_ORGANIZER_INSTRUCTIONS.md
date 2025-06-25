# TV File Organizer - Usage Instructions

## Overview

The TV File Organizer is a standalone module for intelligently managing TV episode files. It provides duplicate detection, loose episode identification, path resolution, and safe file organization capabilities.

**Current Status**: Phase 0 (Duplicate Detection) is complete and ready to use. Phases 1-3 are planned for future development.

## Installation & Setup

No additional installation required - the TV organizer uses the existing project configuration and dependencies.

### Prerequisites
- Python 3.7+
- Access to TV directories configured in `file_managers/plex/config/media_config.yaml`
- Required dependencies from the main project

## Running the TV Organizer

There are three ways to run the TV File Organizer:

### Method 1: Standalone Script (Recommended)
```bash
# From the project root directory
python3 tv_organizer.py [command] [options]
```

### Method 2: Python Module
```bash
# From the project root directory  
python3 -m file_managers.plex.tv_organizer.cli.tv_organizer_cli [command] [options]
```

### Method 3: Direct Script Execution
```bash
# Navigate to the CLI directory
cd file_managers/plex/tv_organizer/cli/
python3 tv_organizer_cli.py [command] [options]
```

## Available Commands

### 🔍 Phase 0: Duplicate Detection (Available Now)

#### Basic Duplicate Scan
```bash
# Scan all directories and show statistics
python3 tv_organizer.py duplicates --scan

# Scan and generate detailed report
python3 tv_organizer.py duplicates --scan --report

# Show statistics only (if already scanned)
python3 tv_organizer.py duplicates --stats
```

#### Duplicate Reports
```bash
# Generate text report (default)
python3 tv_organizer.py duplicates --report --output my_duplicates.txt

# Generate JSON report
python3 tv_organizer.py duplicates --report --format json --output duplicates.json

# Show duplicates for specific show
python3 tv_organizer.py duplicates --show "Breaking Bad"
```

#### Custom Directories
```bash
# Scan custom directories instead of config defaults
python3 tv_organizer.py duplicates --scan --directories /path/to/tv1 /path/to/tv2
```

#### Short Aliases
```bash
# Use short command aliases
python3 tv_organizer.py dup --scan          # 'dup' instead of 'duplicates'
python3 tv_organizer.py d --stats           # 'd' instead of 'duplicates'
```

### 🔧 Configuration Commands

#### Show Configuration
```bash
# Display current TV directories and settings
python3 tv_organizer.py config --show

# Short alias
python3 tv_organizer.py cfg --show
```

### 📊 Status Commands

#### Check Status
```bash
# Show current phase status and available commands
python3 tv_organizer.py status

# Short alias  
python3 tv_organizer.py stat
```

### 🚧 Future Commands (Coming Soon)

These commands are placeholders for future phases:

```bash
# Phase 1: Loose Episode Detection (planned)
python3 tv_organizer.py loose --scan

# Phase 2: Path Resolution (planned)
python3 tv_organizer.py resolve --analyze

# Phase 3: Organization Execution (planned)
python3 tv_organizer.py organize --dry-run
python3 tv_organizer.py organize --execute
```

## Command Options

### Global Options
- `--verbose`, `-v`: Enable verbose output and debug logging
- `--directories`: Specify custom TV directories to scan
- `--version`: Show version information
- `--help`: Show help information

### Duplicate Command Options
- `--scan`: Scan directories and detect duplicates
- `--report`: Generate detailed duplicate report
- `--stats`: Show duplicate statistics summary
- `--show SHOW_NAME`: Show duplicates for specific show
- `--output FILE`: Output file for reports (default: tv_duplicate_report.txt)
- `--format FORMAT`: Output format - 'text' or 'json' (default: text)

## Usage Examples

### Quick Start
```bash
# 1. Check status and configuration
python3 tv_organizer.py status
python3 tv_organizer.py config --show

# 2. Scan for duplicates and generate report
python3 tv_organizer.py duplicates --scan --report

# 3. Check specific show
python3 tv_organizer.py duplicates --show "Game of Thrones"
```

### Advanced Usage
```bash
# Verbose scanning with custom output
python3 tv_organizer.py --verbose duplicates --scan --report \
  --output detailed_duplicates.txt

# JSON report for processing
python3 tv_organizer.py duplicates --scan --format json \
  --output duplicates_$(date +%Y%m%d).json

# Scan specific directories only
python3 tv_organizer.py duplicates --scan \
  --directories "/mnt/qnap/plex/TV" "/mnt/qnap/Media/TV"
```

### Integration Examples
```bash
# Generate daily duplicate report
python3 tv_organizer.py duplicates --scan --format json \
  --output "reports/duplicates_$(date +%Y%m%d).json"

# Check for duplicates of specific show after download
python3 tv_organizer.py duplicates --show "The Mandalorian" --verbose

# Quick statistics check
python3 tv_organizer.py dup --stats
```

## Output Files

### Text Reports
- **Default**: `tv_duplicate_report.txt` in project root
- **Format**: Human-readable with detailed analysis
- **Contents**: Statistics, duplicate groups, recommendations, file locations

### JSON Reports  
- **Default**: `tv_duplicate_report.json` in project root
- **Format**: Structured data for programmatic processing
- **Contents**: Metadata, statistics, detailed episode information

### Sample Text Report Structure
```
TV EPISODE DUPLICATE DETECTION REPORT
==================================================

SUMMARY:
  Total Episodes Scanned: 10496
  Duplicate Groups Found: 1334
  Total Duplicate Files: 2885
  Space Used by Duplicates: 2124.09 GB
  Potential Space Savings: 912.62 GB
  Space Efficiency Gain: 43.0%

DUPLICATE GROUPS:
------------------------------

1. Breaking Bad S01E01: 2 duplicates, 3553.1MB total, 1776.6MB can be saved
   Action: keep_best_quality
   Keep: Breaking.Bad.S01E01.1080p.BluRay.x264-group.mkv
         (1080p, 1776.5MB)
   Remove:
     - Breaking.Bad.S01E01.720p.HDTV.x264-group.mkv
       (720p, 1776.6MB)
```

## Configuration

The TV organizer uses the existing configuration from:
`file_managers/plex/config/media_config.yaml`

### Default TV Directories
- `/mnt/qnap/Media/TV/`
- `/mnt/qnap/Multimedia/TV/`  
- `/mnt/qnap/plex/TV/`

### Customizing Directories
You can override the default directories using the `--directories` option:

```bash
python3 tv_organizer.py duplicates --scan \
  --directories "/path/to/tv1" "/path/to/tv2" "/path/to/tv3"
```

## Safety Features

### Read-Only Operations
- **Phase 0** (current) is completely read-only
- No files are modified, moved, or deleted
- Safe to run on production TV libraries
- Only analyzes and reports findings

### Future Safety Features (Phases 1-3)
- Dry-run mode for testing operations
- Comprehensive backup and rollback capabilities
- Atomic operations with safety checks
- Progress checkpoints and error recovery

## Troubleshooting

### Common Issues

#### Permission Errors
```bash
# Make sure script is executable
chmod +x tv_organizer.py

# Check directory permissions
ls -la /mnt/qnap/plex/TV/
```

#### Import Errors
```bash
# Make sure you're in the project root directory
pwd
# Should show: /home/noufal/personal_package

# Check Python path
python3 -c "import sys; print(sys.path)"
```

#### No Episodes Found
```bash
# Check configuration
python3 tv_organizer.py config --show

# Test with verbose logging
python3 tv_organizer.py --verbose duplicates --scan

# Try custom directories
python3 tv_organizer.py duplicates --scan --directories "/your/tv/path"
```

#### Large Scan Times
- Initial scans of large TV libraries (10,000+ episodes) may take 1-2 minutes
- Use `--verbose` to see progress
- Results are cached within each run

### Debug Information
```bash
# Enable verbose logging for troubleshooting
python3 tv_organizer.py --verbose duplicates --scan

# Check system status
python3 tv_organizer.py status
python3 tv_organizer.py config --show
```

## Performance Notes

### Scan Performance
- **10,000+ episodes**: ~1-2 minutes initial scan
- **1,000 episodes**: ~10-20 seconds
- **Duplicate detection**: Very fast after initial scan
- **Memory usage**: Moderate (stores episode metadata)

### Optimization Tips
- Use `--stats` for quick checks without full reports
- Use JSON format for large datasets
- Scan specific directories when possible
- Use verbose mode only for debugging

## Development Status

### ✅ Phase 0: Duplicate Detection (Complete)
- Full TV directory scanning
- Advanced duplicate detection with quality analysis
- Comprehensive reporting (text and JSON)
- Show-specific duplicate analysis
- Space savings calculations
- Production-ready and tested

### 🚧 Phase 1: Loose Episode Detection (Planned)
- Identify episodes not properly organized
- Classify different types of loose episodes
- Generate organization recommendations

### 🚧 Phase 2: Path Resolution (Planned)  
- Enhanced fuzzy matching for show folders
- Optimal destination path determination
- Conflict resolution for ambiguous matches

### 🚧 Phase 3: Organization Execution (Planned)
- Safe file move/copy operations  
- Dry-run testing capabilities
- Backup and rollback features
- Progress tracking and recovery

## Integration

### With Main Plex CLI
The TV organizer is intentionally **separate** from the main `plex-cli` until all phases are complete and thoroughly tested.

### Scripting Integration
```bash
#!/bin/bash
# Daily duplicate check script

cd /home/noufal/personal_package
python3 tv_organizer.py duplicates --scan --format json \
  --output "reports/duplicates_$(date +%Y%m%d).json"

# Process results...
```

### API Integration (Future)
Future versions may provide Python API access:
```python
from file_managers.plex.tv_organizer import DuplicateDetector

detector = DuplicateDetector()
episodes = detector.scan_all_directories()
duplicates = detector.detect_duplicates()
```

## Support

### Getting Help
```bash
# General help
python3 tv_organizer.py --help

# Command-specific help  
python3 tv_organizer.py duplicates --help
python3 tv_organizer.py config --help

# Show current status
python3 tv_organizer.py status
```

### Reporting Issues
When reporting issues, include:
1. Command that failed
2. Error message
3. Output from `python3 tv_organizer.py --verbose config --show`
4. OS and Python version

### Feature Requests
The TV organizer follows a phased development approach. Current focus is on completing Phase 1 (Loose Episode Detection) before moving to Phase 2 and 3.