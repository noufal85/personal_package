# TV Organization Display Improvements

## Problem Solved
The previous TV organization display was unclear about what files were moving where. Users saw lists of small folders to be deleted but couldn't clearly see the actual episode move operations.

## Enhanced Display Format

### Before (Unclear):
```
133. Prodigal Son S01-S02 br 10bit ddp hevc-d3g
    Size: 26.2 MB
    Files: 73
    Path: /mnt/qnap/Media/TV/Prodigal Son S01-S02 br 10bit ddp hevc-d3g

Total size to be freed: 634.7 MB
INFO: Episodes to move: 1535
INFO: Small folders to clean: 136
```

### After (Crystal Clear):

```
📺 EPISODE MOVES - WHAT'S MOVING WHERE:
======================================================================

📊 MOVE SUMMARY:
   • 1535 episodes will be moved
   • 45 shows affected  
   • 2.3 TB of data
   • 32 new show folders will be created

🎬 Breaking Bad
   📊 62 episodes (45.2 GB)
   📂 MOVE to existing: /mnt/qnap/Media/TV/Breaking Bad (2008)
   📤 FROM: /mnt/qnap/plex/TV/Breaking Bad Season 1
   📋 Sample episodes:
      1. S01E01 - Breaking.Bad.S01E01.Pilot.mkv
         FROM: /mnt/qnap/plex/TV/Breaking Bad Season 1
         TO:   /mnt/qnap/Media/TV/Breaking Bad (2008)/Season 1
      2. S01E02 - Breaking.Bad.S01E02.Cat's.In.The.Bag.mkv
         FROM: /mnt/qnap/plex/TV/Breaking Bad Season 1  
         TO:   /mnt/qnap/Media/TV/Breaking Bad (2008)/Season 1
      ... and 60 more episodes

🎬 The Mandalorian
   📊 24 episodes (18.7 GB)
   📁 CREATE new folder: /mnt/qnap/Media/TV/The Mandalorian (2019)
   📤 FROM multiple locations:
      • /mnt/qnap/plex/TV/Loose Episodes (12 episodes)
      • /mnt/qnap/Multimedia/TV/Random (12 episodes)
   📋 Sample episodes:
      1. S01E01 - The.Mandalorian.S01E01.Chapter.1.mkv
         FROM: /mnt/qnap/plex/TV/Loose Episodes
         TO:   /mnt/qnap/Media/TV/The Mandalorian (2019)/Season 1
      ... and 23 more episodes

🗑️  SMALL FOLDERS TO BE DELETED (CLEANUP):
======================================================================
ℹ️  These are small folders (<100MB) that will be deleted:

 1. 📭 .deletedByTMM (EMPTY)
    📊 Size: 0 B
    📄 Files: 0
    📂 Path: /mnt/qnap/Multimedia/TV/.deletedByTMM

 2. 📁 Prodigal Son S01-S02 br 10bit ddp hevc-d3g
    📊 Size: 26.2 MB
    📄 Files: 73
    📂 Path: /mnt/qnap/Media/TV/Prodigal Son S01-S02 br 10bit ddp hevc-d3g

... and 134 more small folders (608.5 MB)

🗃️  Total cleanup: 634.7 MB in 136 folders

⚠️  NOTE: These are separate from the episode moves above!
   Episodes are MOVED to proper locations, small folders are DELETED.

======================================================================
📋 ORGANIZATION SUMMARY
======================================================================

📺 EPISODE MOVES:
   • 1535 TV episodes will be MOVED to proper show folders
   • 2.3 TB of video content will be organized
   • 45 shows will be organized
   • 32 new show folders will be created

🗑️  CLEANUP:
   • 136 small/empty folders will be DELETED
   • 634.7 MB of cleanup space will be freed

⚠️  EXECUTION MODE - CHANGES WILL BE MADE!
   📺 Episodes will be MOVED to proper show folders
   🗑️  Small folders will be DELETED
   💾 Make sure you have BACKUPS before proceeding!
======================================================================
```

## Key Improvements

### 1. Clear Section Separation
- **Episode Moves**: What actual TV episodes are being moved where
- **Small Folder Cleanup**: What small/empty folders are being deleted
- **Summary**: Overall impact and confirmation

### 2. Visual Hierarchy
- 📺 Episode moves clearly distinguished from 🗑️ cleanup
- 🎬 Show-by-show breakdown with episode counts
- 📊 Size and count information for all operations
- 📤 Source locations clearly shown
- 📂 Target locations clearly indicated

### 3. Sample Episodes
- Shows actual episode files being moved
- Clear FROM/TO paths for each episode
- Episode numbering (S01E01) for easy identification

### 4. Move Types Clarified
- 📁 CREATE new folder vs 📂 MOVE to existing
- Shows whether show folders need to be created
- Handles multiple source locations per show

### 5. Safety Emphasis
- Clear separation between MOVES and DELETIONS
- Backup reminders
- Execution vs preview mode clearly indicated

## Result
Users now have complete clarity about:
- Which episodes are moving where
- What new folders will be created  
- What existing folders will be used
- What small folders will be deleted (separate from moves)
- Total impact of the organization operation

This eliminates confusion and provides confidence before executing the organization.