# Media Mover Caching Workflow

The media mover now supports a two-phase caching workflow that separates decision-making from execution.

## 🎯 Benefits
- **Fast Decision Making**: Quickly approve/reject moves without waiting for execution
- **Batch Execution**: Execute all approved moves in one efficient batch
- **Repeatability**: Re-execute the same moves later if needed
- **Safety**: Review all decisions before any files are moved

## 📋 Phase 1: Decision Phase

Make decisions on which files to move and cache them for later execution:

```bash
# Interactive decision making with caching
plex-cli files move reports/media_reorganization_latest.json --dry-run

# Or using the media mover directly
python3 -m file_managers.plex.utils.media_mover reports/latest.json --dry-run
```

**During Decision Phase:**
- `y` - Approve this move (adds to cache)
- `s` - Skip this file
- `q` - Finish decisions and execute approved moves
- `a` - Approve all remaining files
- `x` - Cancel without executing anything

**Output**: Creates `cache/move_decisions_SESSIONID.json` with approved moves

## 🚀 Phase 2: Execution Phase

Execute previously approved moves from cache:

```bash
# List available cached decisions
plex-cli files move --list-cache
python3 -m file_managers.plex.utils.media_mover --list-cache

# Execute a specific cache file
plex-cli files move --execute-cache cache/move_decisions_20250624_190249.json
python3 -m file_managers.plex.utils.media_mover --execute-cache cache/move_decisions_20250624_190249.json

# Execute in live mode (actually move files)
plex-cli files move --execute-cache cache/move_decisions_20250624_190249.json
```

## 🗂️ Cache File Structure

```json
{
  "session_id": "20250624_190249",
  "timestamp": "2025-06-24T19:02:50.150465",
  "dry_run": true,
  "total_approved": 2,
  "approved_moves": [
    {
      "source_path": "/source/path/file.mkv",
      "target_path": "/target/path/file.mkv", 
      "move_type": "tv_episode_to_existing_show",
      "operation_data": {
        "current_category": "movies",
        "suggested_category": "TV",
        "confidence": 0.90,
        "reasoning": "TV Pattern: TV episode detected",
        "file_size": 2684354560,
        "file_size_readable": "2.5 GB"
      }
    }
  ]
}
```

## 🎛️ New Options

**Decision Options:**
- `y` - Yes, approve this move
- `s` - Skip this file  
- `q` - Quit and execute approved moves
- `a` - Approve all remaining files
- `x` - Cancel all (quit without executing)

**CLI Commands:**
- `--list-cache` - Show available cached decision files
- `--execute-cache <file>` - Execute moves from cache file
- `--dry-run` - Preview mode (no actual file moves)

## 📊 Enhanced Features

1. **TV Episode Organization**: Automatically detects existing show folders and places episodes correctly
2. **Folder-Level Moves**: Moves entire folders instead of individual files when appropriate  
3. **Proper Target Paths**: Uses correct mount points from configuration
4. **Session Tracking**: Each session has unique ID for cache management
5. **Statistics**: Detailed reporting on approved vs executed moves

## 🔄 Typical Workflow

1. **Generate Report**: `plex-cli files reorganize --ai`
2. **Make Decisions**: `plex-cli files move` (uses latest report)
3. **Review Cache**: `plex-cli files move --list-cache`
4. **Execute Moves**: `plex-cli files move --execute-cache <cache_file>`

This workflow allows you to quickly make decisions on thousands of files, then execute them all at once when you're ready.