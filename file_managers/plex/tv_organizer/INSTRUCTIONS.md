# TV File Organizer - Instructions

## Quick Start

The TV File Organizer is a standalone module for intelligently managing TV episode files. Currently, Phase 0 (Duplicate Detection) is complete and ready to use.

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

### 🔍 Phase 0: Duplicate Detection (Available Now)

#### Basic Usage
```bash
# Quick status check
python3 tv_organizer.py status

# Show configuration
python3 tv_organizer.py config --show

# Scan for duplicates
python3 tv_organizer.py duplicates --scan

# Generate detailed report
python3 tv_organizer.py duplicates --scan --report

# Show statistics only
python3 tv_organizer.py dup --stats
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

### 🚧 Future Commands (Coming Soon)

```bash
# Phase 1: Loose Episode Detection (planned)
python3 tv_organizer.py loose --scan

# Phase 2: Path Resolution (planned)
python3 tv_organizer.py resolve --analyze

# Phase 3: Organization Execution (planned)
python3 tv_organizer.py organize --dry-run
python3 tv_organizer.py organize --execute
```

## Output Formats

### Text Reports (Default)
- Human-readable format
- Detailed analysis and recommendations
- Default filename: `tv_duplicate_report.txt`

### JSON Reports
- Machine-readable format for processing
- Structured data with metadata
- Use: `--format json`

## Common Use Cases

### Daily Duplicate Check
```bash
# Quick statistics
python3 tv_organizer.py dup --stats

# Generate dated report
python3 tv_organizer.py dup --scan --format json --output "duplicates_$(date +%Y%m%d).json"
```

### After Downloading New Content
```bash
# Check for duplicates of specific show
python3 tv_organizer.py duplicates --show "The Mandalorian"

# Full scan with verbose output
python3 tv_organizer.py --verbose duplicates --scan --report
```

### Integration with Scripts
```bash
#!/bin/bash
# Example automation script
cd /home/noufal/personal_package
python3 tv_organizer.py duplicates --scan --format json --output "reports/duplicates_$(date +%Y%m%d).json"
```

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
✅ 10,496 episodes scanned
✅ 1,334 duplicate groups found
✅ 2,885 total duplicate files
✅ 912.62 GB potential space savings (43% efficiency)
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
- **Duplicate Detection**: Full TV directory scanning
- **Quality Analysis**: Smart quality and format detection
- **Comprehensive Reporting**: Text and JSON formats
- **Production Ready**: Tested with 10,000+ episodes

### 🚧 Planned Phases
- **Phase 1**: Loose Episode Detection
- **Phase 2**: Path Resolution with enhanced matching
- **Phase 3**: Safe file organization execution

## Module Structure

```
file_managers/plex/tv_organizer/
├── INSTRUCTIONS.md              # This file
├── cli/
│   └── tv_organizer_cli.py     # Main CLI interface
├── core/
│   ├── duplicate_detector.py   # ✅ Phase 0 complete
│   ├── loose_episode_finder.py # 🚧 Phase 1 planned
│   └── path_resolver.py        # 🚧 Phase 2 planned
├── models/
│   ├── episode.py              # Episode data model
│   └── duplicate.py            # Duplicate group model
└── utils/                      # Utility functions
```

## Examples

### Quick Workflow
```bash
# 1. Check status
python3 tv_organizer.py status

# 2. Scan for duplicates
python3 tv_organizer.py duplicates --scan --report

# 3. Check specific show
python3 tv_organizer.py duplicates --show "Game of Thrones"
```

### Advanced Workflow
```bash
# 1. Verbose scan with custom output
python3 tv_organizer.py --verbose duplicates --scan --report --output detailed_report.txt

# 2. Generate JSON for processing
python3 tv_organizer.py duplicates --scan --format json --output analysis.json

# 3. Check configuration
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