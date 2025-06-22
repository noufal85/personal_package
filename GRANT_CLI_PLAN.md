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
├── files          # General file operations
│   ├── find       # Find files by extension
│   ├── size       # Get file size  
│   └── organize   # Auto-organize downloads
├── movies         # Movie management
│   ├── duplicates # Find/remove duplicates
│   ├── search     # Search collection
│   └── reports    # Generate reports
├── tv             # TV show management
│   ├── organize   # Organize episodes
│   ├── search     # Search shows
│   ├── missing    # Find missing episodes
│   └── reports    # Generate reports
├── media          # Cross-media operations
│   ├── assistant  # AI-powered search
│   ├── database   # Database operations
│   └── status     # System status
└── config         # Configuration management
    ├── show       # Show current config
    ├── paths      # Manage paths
    └── apis       # API key management
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

## Example Usage (Post-Implementation)

```bash
# Interactive mode (default when no arguments)
plex-cli                                     # Starts interactive menu

# Direct command mode (when arguments provided)
plex-cli files find /path/to/dir mp4         # Find MP4 files
plex-cli files size /path/to/file.mp4        # Get file size
plex-cli config show                         # Show configuration
plex-cli config paths                        # Show configured paths

# Phase 2+ features (coming soon):
plex-cli movies duplicates                   # Find duplicate movies
plex-cli movies duplicates --delete          # Interactive deletion
plex-cli tv organize                         # Organize TV episodes
plex-cli tv missing "Breaking Bad"           # Find missing episodes
plex-cli media assistant "Do I have Inception?" # AI search

# Force interactive mode explicitly
plex-cli --interactive                       # Explicit interactive mode
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
plex-cli files duplicates --type movies    # Find movie duplicates
plex-cli files database --rebuild          # Rebuild media database
```

**🎬 Movie Management:**
```bash
plex-cli movies duplicates                 # Find duplicate movies
plex-cli movies duplicates --delete        # Interactive deletion
plex-cli movies search "The Batman"        # Search collection
```

**📺 TV Show Management:**
```bash
plex-cli tv organize                       # Analyze episode organization
plex-cli tv organize --demo                # Preview moves
plex-cli tv search "Breaking Bad"          # Search shows
plex-cli tv missing "Game of Thrones"      # Find missing episodes
```

**🎭 Cross-Media Operations:**
```bash
plex-cli media assistant "Do I have Inception?"  # AI-powered search
plex-cli media assistant --interactive           # Interactive AI mode
plex-cli media database --status                 # Database management
```

**⚙️ Configuration Management:**
```bash
plex-cli config show                       # View all settings
plex-cli config paths                      # View directory paths
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

### 📊 **Integration Status**

| Feature Area | Legacy CLI | Unified CLI | Status |
|--------------|------------|-------------|---------|
| Movie Duplicates | `file_managers.plex.cli.movie_duplicates` | `plex-cli movies duplicates` | ✅ **Migrated** |
| TV Organization | `file_managers.plex.cli.tv_organizer` | `plex-cli tv organize` | ✅ **Migrated** |
| Media Assistant | `file_managers.plex.cli.media_assistant` | `plex-cli media assistant` | ✅ **Migrated** |
| Database Management | `file_managers.plex.cli.media_database_cli` | `plex-cli media database` | ✅ **Migrated** |
| Configuration | Manual config file editing | `plex-cli config show/paths` | ✅ **Enhanced** |

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

### 🚀 **Next Steps: Phase 4 Polish** (Optional)

Remaining low-priority features for Phase 4:
- Batch operations support for bulk actions
- Progress indicators for long-running operations  
- Command shortcuts and aliases
- Performance optimizations

---

## Notes

- **Backward Compatibility:** ✅ Keep existing CLI entry points working during transition
- **Testing:** ✅ Test each phase thoroughly before moving to next
- **Documentation:** ✅ Update CLAUDE.md with new commands as they're implemented
- **Performance:** ✅ Ensure unified CLI doesn't introduce significant overhead