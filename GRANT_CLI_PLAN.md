# Plex CLI Centralization Plan

## Project Goal
Centralize all CLI features into a single, unified command-line interface accessible via bash alias from anywhere in the system.

---

## Current State Analysis

### Existing CLIs
- ✅ **`file_managers.cli.file_manager`** - Basic file operations (find, size)
- ✅ **`file_managers.plex.cli.movie_duplicates`** - Movie duplicate detection  
- ✅ **`file_managers.plex.cli.media_assistant`** - AI-powered media search
- ✅ **`file_managers.plex.cli.tv_organizer`** - TV episode organization
- ✅ **`file_managers.plex.cli.media_database_cli`** - Database management
- ✅ **`file_managers.plex.media_autoorganizer.cli`** - Auto file organization
- ✅ **Helper scripts:** `run_*.py` convenience launchers

### Key Features to Centralize
- ✅ File operations (duplicates, database management, organize)
- ✅ Movie management (duplicates, search, reports)
- ✅ TV show management (organize, search, missing episodes)
- ✅ AI-powered media assistant
- ✅ Database operations
- ✅ Configuration management
- [ ] Auto-organization system (Phase 3)

---

## Unified CLI Design

### Main Entry Point
**Command:** `plex-cli` (via bash alias)  
**Implementation:** `python3 -m file_managers.cli.personal_cli`

### Command Structure
```
plex-cli
├── files                    # General file operations
│   ├── duplicates          # Database-based duplicate detection for movies and TV
│   │   ├── --type          # movies/tv/all (default: all)
│   │   └── --rebuild-db    # Force database rebuild before searching
│   ├── database            # Manage the media database
│   │   ├── --rebuild       # Rebuild the entire database
│   │   └── --status        # Show database status and statistics
│   ├── organize            # Auto-organize downloaded media files using AI classification
│   │   ├── --dry-run       # Show what would be done (default mode)
│   │   ├── --execute       # Actually move files
│   │   ├── --no-ai         # Disable AI classification, use rule-based only
│   │   └── --verify-mounts # Only verify mount access and exit
│   └── reorganize          # Analyze misplaced media files using rule-based analysis
│       ├── --confidence    # Minimum confidence threshold (0.0-1.0, default: 0.7)
│       ├── --format        # Report output format (text/json/both, default: both)
│       ├── --ai            # Enable AI classification for edge cases
│       ├── --rebuild-db    # Force database rebuild before analysis
│       └── --no-external-apis # Disable external API usage (TMDB/TVDB)
├── movies                  # Movie collection management
│   ├── duplicates          # Find and manage duplicate movies
│   │   ├── --delete        # Interactive deletion mode with confirmations
│   │   └── --rebuild-db    # Force database rebuild before searching
│   ├── search              # Search movie collection by title
│   │   └── query           # Movie title to search for (required)
│   ├── reports             # Generate comprehensive movie collection reports
│   └── ratings             # OMDB rating integration for quality management
│       ├── --fetch         # Fetch ratings for all movies from OMDB API
│       ├── --stats         # Show rating database statistics
│       ├── --bad-movies    # List badly rated movies based on thresholds
│       ├── --delete-bad    # Delete badly rated movies (requires confirmation)
│       ├── --imdb-threshold    # IMDB rating threshold (default: 5.0)
│       ├── --rt-threshold      # Rotten Tomatoes threshold (default: 30%)
│       └── --meta-threshold    # Metacritic threshold (default: 40)
├── tv                      # TV show collection management
│   ├── organize            # Organize unorganized TV episodes
│   │   ├── --custom        # Comma-separated list of custom TV directories
│   │   ├── --demo          # Show what would be moved without moving files
│   │   ├── --execute       # Actually move files (requires confirmation)
│   │   └── --no-reports    # Skip generating report files
│   ├── search              # Search TV collection by show title
│   │   └── query           # TV show title to search for (required)
│   ├── missing             # Find missing episodes for TV shows
│   │   ├── show            # TV show title to analyze (required)
│   │   └── --season        # Focus on specific season (optional)
│   └── reports             # Generate comprehensive TV collection reports
├── media                   # Cross-media operations across movie and TV collections
│   ├── assistant           # AI-powered natural language media search
│   │   ├── query           # Natural language query (optional)
│   │   ├── --interactive   # Start interactive mode
│   │   └── --rebuild-db    # Rebuild media database before starting
│   ├── database            # Database operations
│   │   ├── --rebuild       # Rebuild the entire database
│   │   ├── --status        # Show database status and statistics
│   │   └── --clean         # Remove database file
│   ├── status              # System status and mount point verification
│   └── enrich              # Enrich metadata using external APIs (TMDB/TVDB)
│       ├── --limit         # Limit number of items to process
│       ├── --force         # Force re-enrichment of cached items
│       ├── --stats         # Show metadata cache statistics
│       └── --test          # Test enrichment for a specific title
└── config                  # Configuration management
    ├── show                # Show current configuration
    │   └── --section       # movies/tv/nas/settings/all (default: all)
    ├── paths               # Show configured directory paths
    │   └── --type          # movies/tv/downloads/all (default: all)
    └── apis                # API configuration management for TMDB, TVDB, AWS
        ├── --check         # Check API key status and connectivity
        └── --show          # Show configured API keys (masked for security)
```

---

## Implementation Phases

### Phase 1: Core Infrastructure ✅ COMPLETED
**Goal:** Basic CLI framework and file operations

- [x] Create unified CLI entry point (`file_managers/cli/personal_cli.py`)
- [x] Implement argument parser with subcommands structure
- [x] Add configuration management integration
- [x] Migrate basic file operations (`files find`, `files size`)
- [x] Set up bash alias system (`plex-cli`)
- [x] Create help system with examples
- [x] Test basic functionality
- [x] **BONUS:** Add interactive mode with menu navigation

**Estimated Time:** 2-3 hours  
**Status:** ✅ Phase 1 Complete - Full-featured CLI with interactive mode

### Phase 2: Media Features Migration ✅ COMPLETED
**Goal:** Core media management features

- [x] Migrate movie duplicate detection (`movies duplicates`)
- [x] Add TV episode organization (`tv organize`)
- [x] Integrate AI media assistant (`media assistant`)
- [x] Add database management commands (`media database`)
- [x] Implement media search shortcuts (`movies search`, `tv search`)
- [x] Add missing episode detection (`tv missing`)

**Estimated Time:** 3-4 hours  
**Status:** ✅ Phase 2 Complete - All core media features integrated into unified CLI

### Phase 3: Advanced Features ✅ COMPLETED
**Goal:** Auto-organization and reporting

- [x] Integrate auto-organizer (`files organize`)
- [x] Add report generation (`movies reports`, `tv reports`)
- [x] Implement configuration management (`config show/paths/apis`)
- [x] Add system status checks (`media status`) 
- [ ] Create batch operations support
- [ ] Add progress indicators for long operations

**Estimated Time:** 2-3 hours  
**Status:** ✅ Phase 3 Core Features Complete

### Phase 4: Polish & Documentation
**Goal:** User experience and maintainability

- [ ] Add command shortcuts/aliases (e.g., `personal-cli m d` for `movies duplicates`)
- [ ] Improve help system with usage examples
- [ ] Add interactive mode support
- [ ] Create comprehensive usage documentation
- [ ] Add command completion suggestions
- [ ] Performance optimizations
- [ ] Error handling improvements

**Estimated Time:** 1-2 hours

---

## Bash Alias Setup

### Global Alias Configuration
**Alias:** `plex-cli`  
**Target:** `python3 -m file_managers.cli.personal_cli`  
**Location:** `~/.bashrc` for persistent access

### Setup Commands
```bash
# Recommended: Function with interactive mode as default
echo 'plex-cli() {
    if [ $# -eq 0 ]; then
        python3 -m file_managers.cli.personal_cli --interactive
    else
        python3 -m file_managers.cli.personal_cli "$@"
    fi
}' >> ~/.bashrc
source ~/.bashrc

# Alternative: Simple alias (always interactive)
echo 'alias plex-cli="python3 -m file_managers.cli.personal_cli --interactive"' >> ~/.bashrc
```

### Benefits
- ✅ Run from anywhere in the system
- ✅ Shorter, more memorable commands
- ✅ Interactive mode by default for user-friendly experience
- ✅ Direct command mode still available when needed
- ✅ Consistent interface across all features
- ✅ Easy to extend with new functionality

---

## Example Usage (Current Implementation)

```bash
# Interactive mode (default when no arguments)
plex-cli                                     # Starts interactive menu with full navigation

# === FILE OPERATIONS ===
plex-cli files duplicates                    # Find all duplicates (movies + TV)
plex-cli files duplicates --type movies      # Find only movie duplicates
plex-cli files database --rebuild            # Rebuild entire media database
plex-cli files database --status             # Show database statistics
plex-cli files organize                      # Preview auto-organization (dry-run)
plex-cli files organize --execute            # Actually organize files with AI
plex-cli files reorganize                    # Analyze misplaced files

# === MOVIE MANAGEMENT ===
plex-cli movies duplicates                   # Find duplicate movies
plex-cli movies duplicates --delete          # Interactive deletion with confirmations
plex-cli movies search "The Batman"          # Search movie collection
plex-cli movies reports                      # Generate comprehensive movie reports

# === OMDB RATING INTEGRATION ===
plex-cli movies ratings --fetch              # Fetch OMDB ratings for all movies
plex-cli movies ratings --stats              # Show rating database statistics
plex-cli movies ratings --bad-movies         # List movies with poor ratings
plex-cli movies ratings --delete-bad         # Delete badly rated movies (with confirmation)
plex-cli movies ratings --bad-movies --imdb-threshold 4.0  # Custom IMDB threshold

# === TV SHOW MANAGEMENT ===
plex-cli tv organize                         # Analyze TV episode organization
plex-cli tv organize --demo                  # Preview what would be moved
plex-cli tv organize --execute               # Actually move episodes with confirmation
plex-cli tv search "Breaking Bad"            # Search TV collection
plex-cli tv missing "Game of Thrones"        # Find missing episodes
plex-cli tv missing "Lost" --season 3        # Check specific season for missing episodes
plex-cli tv reports                          # Generate TV collection reports

# === CROSS-MEDIA OPERATIONS ===
plex-cli media assistant "Do I have Inception?"          # AI-powered natural language search
plex-cli media assistant --interactive                   # Interactive AI assistant mode
plex-cli media database --rebuild                        # Rebuild media database
plex-cli media database --status                         # Database status and statistics
plex-cli media status                                     # System status and mount verification
plex-cli media enrich --stats                             # Show metadata cache statistics

# === CONFIGURATION MANAGEMENT ===
plex-cli config show                         # Show all configuration
plex-cli config show --section movies        # Show only movie configuration
plex-cli config paths                        # Show all configured directory paths
plex-cli config apis --check                 # Test API connectivity (TMDB, TVDB, AWS)
plex-cli config apis --show                  # Show configured API keys (masked)

# === ADVANCED FEATURES ===
plex-cli files organize --no-ai              # Rule-based classification only
plex-cli files reorganize --ai --confidence 0.8  # AI-enhanced analysis with custom threshold
plex-cli media enrich --limit 100 --force    # Force re-enrichment of 100 items

# Force interactive mode explicitly
plex-cli --interactive                       # Explicit interactive mode
plex-cli -i                                  # Short form interactive mode
```

---

## Success Criteria

### Phase 1 Complete ✅
- [x] `plex-cli` command works from any directory
- [x] Basic file operations functional
- [x] Help system displays properly
- [x] Configuration system integrated

### Phase 2 Complete ✅
- [x] All major media features accessible via unified CLI
- [x] Existing functionality preserved
- [x] Performance matches or exceeds current CLIs

### Phase 3 Complete
- [ ] Auto-organizer fully integrated
- [ ] Comprehensive reporting available
- [ ] Configuration management working

### Phase 4 Complete
- [ ] User-friendly help and examples
- [ ] Command shortcuts working
- [ ] Documentation complete
- [ ] All legacy run_*.py scripts can be deprecated

---

## Implementation Status & Current State

### 🎉 **MAJOR MILESTONE: Phase 2 Complete!**
**Date Completed:** December 21, 2024

The unified Plex CLI is now **fully functional** with all core media management features integrated into a single, cohesive interface. 

### ✅ **What's Working Now**

**🚀 Unified Entry Point:**
- `plex-cli` command works from any directory
- Interactive mode with full menu navigation
- Direct command mode for all features
- Comprehensive help system at all levels

**📁 File Operations:**
```bash
plex-cli files duplicates --type movies    # Database-based duplicate detection
plex-cli files database --rebuild          # Rebuild media database
plex-cli files organize --execute          # AI-powered auto-organization
plex-cli files reorganize --ai             # Analyze misplaced files
```

**🎬 Movie Management:**
```bash
plex-cli movies duplicates --delete        # Find and interactively delete duplicates
plex-cli movies search "The Batman"        # Search movie collection
plex-cli movies reports                    # Generate comprehensive reports
plex-cli movies ratings --fetch            # Fetch OMDB ratings for quality management
plex-cli movies ratings --delete-bad       # Delete badly rated movies
```

**📺 TV Show Management:**
```bash
plex-cli tv organize --execute             # Organize unstructured TV episodes
plex-cli tv search "Breaking Bad"          # Search TV collection
plex-cli tv missing "Game of Thrones"      # Find missing episodes with season analysis
plex-cli tv reports                        # Generate TV organization reports
```

**🎭 Cross-Media Operations:**
```bash
plex-cli media assistant "Do I have Inception?"  # AI-powered natural language search
plex-cli media assistant --interactive           # Interactive AI assistant mode
plex-cli media database --rebuild                # Database management and rebuilding
plex-cli media status                            # System status and mount verification
plex-cli media enrich --stats                    # Metadata enrichment with external APIs
```

**⚙️ Configuration Management:**
```bash
plex-cli config show --section movies      # View configuration by section
plex-cli config paths --type tv            # View directory paths by media type
plex-cli config apis --check               # Test API connectivity (TMDB, TVDB, AWS)
```

**🎯 Interactive Mode Features:**
- Full menu navigation across all feature areas
- Direct quit ('q') from any submenu without navigation
- Back navigation ('b') to return to main menu
- Smart database age reporting before rebuild prompts
- User-friendly error handling and confirmations

### 🔧 **Enhanced User Experience Features**

1. **Smart Database Management:**
   - Shows database age (e.g., "Database last updated 2.3 hours ago")
   - Intelligent rebuild prompts with context
   - Consistent behavior across all duplicate detection commands

2. **Improved Navigation:**
   - 'q' (quit) available in all submenus for instant exit
   - 'b' (back) navigation preserved for menu traversal
   - Consistent menu styling and feedback

3. **Focused Media Management:**
   - Removed generic file operations (find by extension, file size)
   - Concentrated on Plex-specific media management tasks
   - Streamlined interface for actual use cases

4. **🌟 OMDB Rating Integration:**
   - **Quality Management System:** Fetch ratings from OMDB API for entire movie collection
   - **Multi-Source Ratings:** Integrates IMDB, Rotten Tomatoes, and Metacritic scores
   - **Configurable Thresholds:** Customizable rating thresholds for quality assessment
     - IMDB: Default < 5.0 (out of 10)
     - Rotten Tomatoes: Default < 30% 
     - Metacritic: Default < 40 (out of 100)
   - **Intelligent Bad Movie Detection:** Uses majority-based scoring across available ratings
   - **Safe Deletion System:** Interactive confirmation before deleting badly rated movies
   - **Comprehensive Statistics:** Database statistics with rating coverage metrics
   - **30-Day Caching:** Efficient API usage with local SQLite database caching
   - **Quality Score Calculation:** Unified scoring system across different rating sources

### 📊 **Integration Status**

| Feature Area | Legacy CLI | Unified CLI | Status |
|--------------|------------|-------------|---------|
| Movie Duplicates | `file_managers.plex.cli.movie_duplicates` | `plex-cli movies duplicates` | ✅ **Migrated** |
| TV Organization | `file_managers.plex.cli.tv_organizer` | `plex-cli tv organize` | ✅ **Migrated** |
| Media Assistant | `file_managers.plex.cli.media_assistant` | `plex-cli media assistant` | ✅ **Migrated** |
| Database Management | `file_managers.plex.cli.media_database_cli` | `plex-cli media database` | ✅ **Migrated** |
| Auto-Organization | `file_managers.plex.media_autoorganizer.cli` | `plex-cli files organize` | ✅ **Migrated** |
| OMDB Rating System | `file_managers.plex.utils.omdb_rating_fetcher` | `plex-cli movies ratings` | ✅ **Integrated** |
| Media Reorganization | `file_managers.plex.utils.media_reorganizer` | `plex-cli files reorganize` | ✅ **Integrated** |
| Metadata Enrichment | `file_managers.plex.utils.metadata_enrichment` | `plex-cli media enrich` | ✅ **Integrated** |
| Configuration | Manual config file editing | `plex-cli config show/paths/apis` | ✅ **Enhanced** |

### 🎯 **Ready for Production Use**

The unified CLI is now **production-ready** for daily Plex media management tasks:

- **Reliability:** All core features tested and working
- **Performance:** Fast response times, efficient database operations  
- **Usability:** Intuitive commands and interactive modes
- **Documentation:** Comprehensive help and examples
- **Backward Compatibility:** Legacy commands still functional

### 🎉 **MAJOR MILESTONE: Phase 3 Complete!**
**Date Completed:** December 21, 2024

The unified Plex CLI now includes **all advanced features** and is a comprehensive media management solution.

### ✅ **Phase 3 Features Added**

**🗂️ Auto-Organization System:**
```bash
plex-cli files organize                    # Preview mode (dry-run)
plex-cli files organize --execute         # Actually organize files
plex-cli files organize --no-ai           # Rule-based classification only
plex-cli files organize --verify-mounts   # Check mount access only
```

**📊 Comprehensive Reporting:**
```bash
plex-cli movies reports                    # Movie inventory and duplicates
plex-cli tv reports                        # TV folder analysis and organization plan
```

**🔍 System Status Monitoring:**
```bash
plex-cli media status                      # Database status, mount points, disk space
```

**🔑 Enhanced Configuration Management:**
```bash
plex-cli config apis                       # API configuration help
plex-cli config apis --show               # Show configured API keys (masked)
plex-cli config apis --check              # Test API connectivity
```

**🌟 OMDB Rating Integration:**
```bash
plex-cli movies ratings --fetch            # Fetch OMDB ratings for entire movie collection
plex-cli movies ratings --stats            # Show rating database statistics and coverage
plex-cli movies ratings --bad-movies       # List movies below quality thresholds
plex-cli movies ratings --delete-bad       # Safely delete badly rated movies with confirmation
plex-cli movies ratings --bad-movies --imdb-threshold 4.5  # Custom thresholds
```
- **Multi-source rating integration:** IMDB, Rotten Tomatoes, Metacritic
- **Intelligent quality scoring:** Majority-based bad movie detection
- **Safe deletion workflow:** Interactive confirmation before removing files
- **Efficient caching:** 30-day SQLite cache to minimize API calls
- **Comprehensive statistics:** Rating coverage and database metrics

### 🚀 **Next Steps: Phase 4 Polish** (Optional)

**Status**: Ready for implementation (all dependencies complete)

Remaining optional enhancements for Phase 4:
- [ ] Batch operations support for bulk actions
- [ ] Progress indicators for long-running operations  
- [ ] Command shortcuts and aliases (e.g., `plex-cli m d` for `movies duplicates`)
- [ ] Performance optimizations and caching improvements
- [ ] Enhanced interactive mode features
- [ ] Command completion and auto-suggestions

**Estimated Time**: 1-2 hours per feature
**Priority**: Low (system is fully functional without these)

---

## Notes

- **Backward Compatibility:** ✅ Keep existing CLI entry points working during transition
- **Testing:** ✅ Test each phase thoroughly before moving to next
- **Documentation:** ✅ Update CLAUDE.md with new commands as they're implemented
- **Performance:** ✅ Ensure unified CLI doesn't introduce significant overhead