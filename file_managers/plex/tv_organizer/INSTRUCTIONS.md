# TV File Organizer - Instructions

## Quick Start

The TV File Organizer is a standalone module for intelligently managing TV episode files. Currently, Phase 0 (Duplicate Detection) and Phase 1 (Loose Episode Detection) are complete and ready to use.

### Prerequisites
- Python 3.7+
- Access to TV directories configured in the project
- Run from project root directory: `/home/noufal/personal_package`

## Running the TV Organizer

### Method 1: Standalone Script (Recommended)
```bash
# From project root
python3 tv_organizer.py [command] [options]
```

### Method 2: Python Module
```bash
# From project root
python3 -m file_managers.plex.tv_organizer.cli.tv_organizer_cli [command] [options]
```

### Method 3: Direct Script Execution
```bash
# Navigate to this directory first
cd file_managers/plex/tv_organizer/cli/
python3 tv_organizer_cli.py [command] [options]
```

## Available Commands

### 🔍 Phase 0: Enhanced Duplicate Detection (Available Now)

#### Basic Usage
```bash
# Quick status check
python3 tv_organizer.py status

# Show configuration
python3 tv_organizer.py config --show

# Scan for duplicates (enhanced detection with false positive filtering)
python3 tv_organizer.py duplicates --scan

# Generate detailed report (saves to reports/tv/ directory)
python3 tv_organizer.py duplicates --scan --report

# Show statistics only
python3 tv_organizer.py dup --stats
```

#### Duplicate Deletion (Available Now)
```bash
# Preview what would be deleted (safe, no actual deletion)
python3 tv_organizer.py duplicates --scan --delete --mode dry-run

# Preview with higher confidence threshold (more conservative)
python3 tv_organizer.py duplicates --scan --delete --mode dry-run --confidence 95

# Move duplicates to system trash/recycle bin (safe, recoverable)
python3 tv_organizer.py duplicates --scan --delete --mode trash

# Permanent deletion (DANGEROUS - files cannot be recovered!)
python3 tv_organizer.py duplicates --scan --delete --mode permanent

# Force deletion without confirmations (use with extreme caution)
python3 tv_organizer.py dup --delete --mode trash --force
```

#### Advanced Usage
```bash
# Check specific show
python3 tv_organizer.py duplicates --show "Breaking Bad"

# JSON format output
python3 tv_organizer.py dup --scan --format json --output duplicates.json

# Custom output file
python3 tv_organizer.py duplicates --report --output my_report.txt

# Verbose logging
python3 tv_organizer.py --verbose duplicates --scan

# Custom directories
python3 tv_organizer.py duplicates --scan --directories /path/tv1 /path/tv2
```

#### Command Aliases
```bash
# Short aliases for quick access
python3 tv_organizer.py dup --scan          # 'dup' = duplicates
python3 tv_organizer.py d --stats           # 'd' = duplicates  
python3 tv_organizer.py cfg --show          # 'cfg' = config
python3 tv_organizer.py stat                # 'stat' = status
```

### 🔍 Phase 1: Loose Episode Detection (Planned)

```bash
# Phase 1 is planned for future development
python3 tv_organizer.py loose --scan       # 🚧 Coming soon
```

### 🔍 Phase 2: Path Resolution (Available Now)

#### Basic Usage
```bash
# Analyze directory structure and show organization statistics
python3 tv_organizer.py resolve --stats

# Analyze directory structure and generate comprehensive report
python3 tv_organizer.py resolve --analyze --report

# Scan for path resolution opportunities
python3 tv_organizer.py resolve --scan
```

#### Advanced Usage
```bash
# Check specific show path resolution
python3 tv_organizer.py resolve --show "Breaking Bad"

# Filter by confidence level
python3 tv_organizer.py resolve --scan --confidence high
python3 tv_organizer.py resolve --scan --confidence medium

# JSON format output
python3 tv_organizer.py resolve --analyze --format json --output path_analysis.json

# Custom output file
python3 tv_organizer.py resolve --report --output my_path_report.txt

# Verbose analysis
python3 tv_organizer.py --verbose resolve --analyze --report
```

#### Command Aliases
```bash
# Short aliases for quick access
python3 tv_organizer.py r --stats          # 'r' = resolve
```

### 🚧 Future Commands (Coming Soon)

```bash
# Phase 3: Organization Execution (planned)
python3 tv_organizer.py organize --dry-run
python3 tv_organizer.py organize --execute
```

## Output Formats

### Text Reports (Default)
- Human-readable format
- Detailed analysis and recommendations
- Default filenames: 
  - Duplicates: `reports/tv/duplicate_report.txt`
  - Path Resolution: `reports/tv/path_resolution_report.txt`

### JSON Reports
- Machine-readable format for processing
- Structured data with metadata
- Use: `--format json`

## Common Use Cases

### Daily Library Check
```bash
# Quick duplicate statistics
python3 tv_organizer.py dup --stats

# Quick path resolution statistics
python3 tv_organizer.py resolve --stats

# Generate dated reports
python3 tv_organizer.py dup --scan --format json --output "duplicates_$(date +%Y%m%d).json"
python3 tv_organizer.py resolve --analyze --format json --output "path_analysis_$(date +%Y%m%d).json"
```

### After Downloading New Content
```bash
# Check for duplicates of specific show
python3 tv_organizer.py duplicates --show "The Mandalorian"

# Check path resolution for specific show
python3 tv_organizer.py resolve --show "The Mandalorian"

# Full analysis with verbose output
python3 tv_organizer.py --verbose duplicates --scan --report
python3 tv_organizer.py --verbose resolve --analyze --report
```

### Integration with Scripts
```bash
#!/bin/bash
# Example automation script for complete TV library analysis
cd /home/noufal/personal_package

# Generate daily reports
python3 tv_organizer.py duplicates --scan --format json --output "reports/duplicates_$(date +%Y%m%d).json"
python3 tv_organizer.py resolve --analyze --format json --output "reports/path_analysis_$(date +%Y%m%d).json"

# Quick status summary
echo "=== TV Library Analysis ==="
python3 tv_organizer.py dup --stats
python3 tv_organizer.py resolve --stats
```

## Deletion Safety Features

### Multiple Safety Layers
- **Dry-Run Mode**: Preview deletions without making any changes
- **Confidence Scoring**: Only delete duplicates with high confidence scores (80%+ default)
- **Safety Checks**: Verify file accessibility, size reasonableness, and lock status
- **User Confirmation**: Interactive confirmation for each deletion operation
- **Trash Mode**: Move files to system trash instead of permanent deletion
- **Force Protection**: Confirmations cannot be bypassed without explicit --force flag

### Safety Checks Performed
1. **File Existence**: Verify file exists and is accessible
2. **File Not Locked**: Check file is not in use by another process
3. **Size Reasonable**: Flag files that are suspiciously small (< 100KB) or large (> 50GB)
4. **User Confirmation**: Get explicit user approval for each deletion

### Deletion Modes
- **dry-run**: Preview only, no files modified (safest)
- **trash**: Move to system trash/recycle bin (safe, recoverable)
- **permanent**: Immediate deletion (dangerous, irreversible)

### Confidence Thresholds
- **80% (default)**: Balanced approach, good for most users
- **90%**: Conservative approach, fewer deletions but higher certainty
- **95%+**: Very conservative, only most obvious duplicates

## Configuration

### Default TV Directories
- `/mnt/qnap/Media/TV/`
- `/mnt/qnap/Multimedia/TV/`
- `/mnt/qnap/plex/TV/`

### Override Directories
```bash
python3 tv_organizer.py duplicates --scan --directories "/custom/path1" "/custom/path2"
```

## Safety Features

### Phase 0 (Current)
- **Read-Only**: No files are modified, moved, or deleted
- **Safe Testing**: Can be run on production TV libraries
- **Analysis Only**: Only reports findings

### Future Phases
- Dry-run mode for testing
- Backup and rollback capabilities
- Comprehensive safety checks

## Performance

### Typical Scan Times
- **10,000+ episodes**: 1-2 minutes
- **1,000 episodes**: 10-20 seconds
- **Memory usage**: Moderate (stores episode metadata)

### Real Test Results
```
Phase 0 - Duplicate Detection:
✅ 10,496 episodes scanned
✅ 1,334 duplicate groups found
✅ 2,885 total duplicate files
✅ 912.62 GB potential space savings (43% efficiency)

Phase 1 - Loose Episode Detection:
✅ 10,496 episodes scanned
✅ 588 loose episodes found
✅ 192 loose episode groups
✅ 38 shows affected
✅ 393.98 GB in loose episodes
```

## Troubleshooting

### Common Issues

#### Command Not Found
```bash
# Make sure you're in project root
pwd
# Should show: /home/noufal/personal_package

# Check script exists
ls -la tv_organizer.py
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

#### Permission Errors
```bash
# Check directory permissions
ls -la /mnt/qnap/plex/TV/

# Ensure script is executable
chmod +x tv_organizer.py
```

### Debug Information
```bash
# Enable verbose logging
python3 tv_organizer.py --verbose duplicates --scan

# Check system status
python3 tv_organizer.py status
python3 tv_organizer.py config --show
```

## Help and Support

### Getting Help
```bash
# General help
python3 tv_organizer.py --help

# Command-specific help
python3 tv_organizer.py duplicates --help
python3 tv_organizer.py config --help
```

### Reporting Issues
Include this information:
1. Command that failed
2. Error message
3. Output from: `python3 tv_organizer.py --verbose config --show`
4. OS and Python version

## Development Status

### ✅ Phase 0: Complete
- **Enhanced Duplicate Detection**: Full TV directory scanning with false positive filtering
- **Content Analysis**: Intelligent detection of different episode content
- **Version Detection**: Identifies true duplicates with _1, _2 suffixes
- **Confidence Scoring**: Only reports high-confidence matches (≥70%)
- **Quality Analysis**: Smart quality and format detection
- **Comprehensive Reporting**: Text and JSON formats with runtime information
- **Safe Duplicate Deletion**: Multi-layered safety system with dry-run, trash, and permanent modes
- **Interactive Confirmation**: User confirmation system with confidence-based filtering
- **Production Ready**: Tested with 10,000+ episodes, reduces false positives by 58%

### ✅ Phase 2: Complete
- **Directory Structure Mapping**: Comprehensive analysis of TV show organization patterns
- **Show Directory Discovery**: Intelligent detection of existing show folders across multiple TV directories  
- **Season Structure Analysis**: Understanding of season organization patterns for each show
- **Path Destination Scoring**: Multi-factor scoring system for optimal file placement destinations
- **Fuzzy Show Name Matching**: Advanced similarity matching to connect episodes with existing shows
- **Space Availability Assessment**: Real-time disk space analysis for safe file operations
- **Organization Quality Scoring**: 0-100 scoring system for show directory organization quality
- **Conflict Resolution**: Detection and handling of naming conflicts and multiple valid destinations
- **Comprehensive Statistics**: Detailed analysis of library organization with actionable insights
- **Production Ready**: Tested with 10,000+ episodes, 327 shows across 3 TV directories

### 🚧 Planned Phases
- **Phase 1**: Loose Episode Detection (parked for future development)
- **Phase 3**: Safe file organization execution

## Module Structure

```
file_managers/plex/tv_organizer/
├── INSTRUCTIONS.md              # This file
├── cli/
│   └── tv_organizer_cli.py     # Main CLI interface
├── core/
│   ├── duplicate_detector.py   # ✅ Phase 0 complete
│   └── path_resolver.py        # ✅ Phase 2 complete
├── models/
│   ├── episode.py              # Episode data model
│   ├── duplicate.py            # Duplicate group model
│   └── path_resolution.py      # ✅ Path resolution models
└── utils/                      # Utility functions
```

## Examples

### Quick Workflow
```bash
# 1. Check status
python3 tv_organizer.py status

# 2. Scan for duplicates and analyze path resolution
python3 tv_organizer.py duplicates --scan --report
python3 tv_organizer.py resolve --analyze --report

# 3. Check specific show
python3 tv_organizer.py duplicates --show "Game of Thrones"
python3 tv_organizer.py resolve --show "Game of Thrones"
```

### Advanced Workflow
```bash
# 1. Comprehensive analysis with verbose output
python3 tv_organizer.py --verbose duplicates --scan --report --output detailed_duplicates.txt
python3 tv_organizer.py --verbose resolve --analyze --report --output detailed_resolution.txt

# 2. Generate JSON for processing
python3 tv_organizer.py duplicates --scan --format json --output duplicates_analysis.json
python3 tv_organizer.py resolve --analyze --format json --output path_analysis.json

# 3. Filter path resolutions by confidence
python3 tv_organizer.py resolve --scan --confidence high
python3 tv_organizer.py resolve --scan --confidence medium

# 4. Check configuration
python3 tv_organizer.py config --show
```

## Integration

### Standalone Module
- **Separate from main plex-cli**: Independent operation
- **No interference**: Won't affect existing TV utilities
- **Safe testing**: Can be tested without impacting main system

### Future Integration
- Will be integrated into main plex-cli when all phases complete
- Currently focusing on Phase 1 development
- Maintaining separation for safety and testing

---

**Note**: This is a separate module from existing TV utilities. It will not be integrated into the main CLI until all phases are complete and thoroughly tested.