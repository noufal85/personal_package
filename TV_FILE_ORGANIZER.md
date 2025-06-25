# TV File Organizer Project

## Project Overview

A dedicated TV file organization system that intelligently identifies, analyzes, and reorganizes TV episode files across multiple directories. This is a separate module from the existing TV utilities to ensure clean development and testing.

## Project Structure

```
file_managers/
└── plex/
    └── tv_organizer/           # NEW MODULE
        ├── __init__.py
        ├── core/
        │   ├── __init__.py
        │   ├── duplicate_detector.py      # Phase 0
        │   ├── loose_episode_finder.py    # Phase 1
        │   ├── path_resolver.py           # Phase 2
        │   └── organizer.py               # Phase 3
        ├── models/
        │   ├── __init__.py
        │   ├── episode.py                 # Episode data models
        │   ├── show.py                    # Show data models
        │   └── duplicate.py               # Duplicate data models
        ├── utils/
        │   ├── __init__.py
        │   ├── filename_parser.py         # Reuse existing parsing logic
        │   ├── folder_matcher.py          # Enhanced matching logic
        │   └── file_operations.py         # File move/copy operations
        ├── analyzers/
        │   ├── __init__.py
        │   ├── directory_analyzer.py      # Directory structure analysis
        │   └── pattern_analyzer.py        # Filename pattern analysis
        └── cli/
            ├── __init__.py
            └── tv_organizer_cli.py         # Standalone CLI (when ready)
```

## Development Phases

### Phase 0: Duplicate Detection
**Goal**: Identify duplicate episodes across all TV directories
**Status**: 🚧 Planning

#### Objectives:
- [ ] Scan all configured TV directories
- [ ] Identify video files that represent the same episode
- [ ] Handle various filename formats and quality indicators
- [ ] Detect duplicates by:
  - Show name (fuzzy matching)
  - Season number
  - Episode number
  - File size comparison
- [ ] Generate duplicate reports with recommendations (keep largest, etc.)

#### Key Components:
- `DuplicateDetector` class
- `Episode` model with comparison methods
- `DuplicateGroup` model for grouping related files
- Fuzzy show name matching
- Quality/resolution detection

#### Test Cases:
- Same episode with different qualities (1080p vs 720p)
- Same episode with different file formats (.mkv vs .mp4)
- Case variations in show names (MobLand vs Mobland)
- Different naming conventions for same episode

---

### Phase 1: Loose Episode Detection
**Goal**: Identify episodes that are not properly organized in show folders
**Status**: 🚧 Planning

#### Objectives:
- [ ] Detect episodes in root TV directories (not in show folders)
- [ ] Identify episodes in generic folders (Downloads, Temp, etc.)
- [ ] Find episodes in incorrectly named folders
- [ ] Detect individual episode folders that should be consolidated
- [ ] Handle season folders outside of show folders

#### Key Components:
- `LooseEpisodeFinder` class
- `EpisodeLocation` model (proper vs loose)
- Directory structure analysis
- Pattern recognition for proper vs improper organization

#### Classification:
1. **Root loose files**: Episodes directly in TV root directories
2. **Misplaced folders**: Individual episode folders (e.g., "Show S01E01")
3. **Generic folders**: Episodes in "Downloads", "New", "Unsorted" folders
4. **Season folders**: Season folders not under proper show folders
5. **Incorrect show folders**: Folders with wrong/partial show names

---

### Phase 2: Path Resolution
**Goal**: Determine the correct destination path for each loose episode
**Status**: 🚧 Planning

#### Objectives:
- [ ] Match loose episodes to existing show folders (enhanced fuzzy matching)
- [ ] Determine optimal target directory when multiple TV directories exist
- [ ] Handle show folders with different naming conventions
- [ ] Resolve conflicts when multiple potential destinations exist
- [ ] Create new show folder recommendations when needed

#### Key Components:
- `PathResolver` class
- `ShowMatcher` with enhanced fuzzy logic
- `DestinationStrategy` for choosing between multiple TV directories
- `ConflictResolver` for handling ambiguous matches

#### Matching Strategies:
1. **Exact match**: Direct show name match
2. **Fuzzy match**: Case-insensitive, punctuation-agnostic
3. **Alias match**: Handle known show name variations
4. **Partial match**: Handle abbreviated or extended names
5. **Year resolution**: Handle shows with same names but different years

#### Directory Selection:
- Prefer existing show folder locations
- Consider available space
- Respect directory hierarchy preferences
- Handle network vs local storage preferences

---

### Phase 3: Organization Execution
**Goal**: Execute the file organization plan with safety and reliability
**Status**: 🚧 Planning

#### Objectives:
- [ ] Create comprehensive move/copy plans
- [ ] Implement dry-run mode for safe testing
- [ ] Handle file conflicts and duplicates during moves
- [ ] Create necessary directory structures
- [ ] Provide detailed progress reporting
- [ ] Implement rollback capabilities
- [ ] Handle network/permission errors gracefully

#### Key Components:
- `Organizer` orchestrator class
- `MoveOperation` model
- `ProgressTracker` for real-time updates
- `SafetyValidator` for pre-move checks
- `RollbackManager` for undo operations

#### Safety Features:
- Pre-move validation (space, permissions, conflicts)
- Atomic operations where possible
- Comprehensive logging
- Backup/rollback support
- Progress checkpoints
- Error recovery

---

## Reusable Components

### From Existing Codebase:
- `extract_tv_info_from_filename()` from `tv_scanner.py`
- `normalize_show_name()` from `tv_scanner.py`
- Video file detection logic
- Configuration management
- File size formatting utilities

### Enhanced/New Components:
- Improved fuzzy matching algorithms
- Duplicate detection logic
- Path resolution strategies
- Progress tracking and reporting
- Error handling and recovery

## Configuration

```yaml
tv_organizer:
  directories:
    - /mnt/qnap/plex/TV/
    - /mnt/qnap/Media/TV/
    - /mnt/qnap/Multimedia/TV/
  
  duplicate_detection:
    size_threshold_mb: 50  # Ignore size differences smaller than this
    quality_preference: ["4K", "1080p", "720p", "480p"]
    format_preference: [".mkv", ".mp4", ".avi"]
  
  loose_detection:
    exclude_folders: ["Season *", "Specials", "Extras"]
    max_depth: 3  # How deep to scan for loose episodes
  
  path_resolution:
    prefer_existing_locations: true
    create_missing_folders: true
    naming_convention: "{show_name}/Season {season:02d}"
  
  safety:
    dry_run_default: true
    require_confirmation: true
    backup_before_move: false
    max_file_size_gb: 50  # Safety limit for individual files
```

## Testing Strategy

### Unit Tests:
- Individual component testing
- Mock file system operations
- Fuzzy matching accuracy
- Edge case handling

### Integration Tests:
- End-to-end workflow testing
- Multi-directory scanning
- Conflict resolution
- Error recovery

### Test Data:
- Sample TV directory structures
- Various filename formats
- Duplicate scenarios
- Edge cases (special characters, long names, etc.)

## Success Criteria

### Phase 0 Complete:
- ✅ Accurately identifies all duplicate episodes
- ✅ Provides clear duplicate reports with recommendations
- ✅ Handles various quality and format combinations
- ✅ Fast scanning of large directory structures

### Phase 1 Complete:
- ✅ Identifies all types of loose episodes
- ✅ Correctly classifies organization status
- ✅ Minimal false positives
- ✅ Clear reporting of findings

### Phase 2 Complete:
- ✅ Accurate show matching (>95% success rate)
- ✅ Optimal destination path selection
- ✅ Conflict resolution without user confusion
- ✅ Handles edge cases gracefully

### Phase 3 Complete:
- ✅ Safe, reliable file operations
- ✅ Comprehensive progress reporting
- ✅ Robust error handling and recovery
- ✅ User confidence in the process

## Future Enhancements

- Integration with media databases (TMDB, TVDB)
- Automatic quality upgrade detection
- Subtitle file handling
- Integration with media server refresh
- Web interface for remote management
- Scheduled automatic organization

## Notes

- Keep this module completely separate from existing TV utilities
- Do not integrate with main CLI until all phases are complete and tested
- Focus on reliability and user confidence over speed
- Provide extensive logging and user feedback
- Design for extensibility and maintenance