"""TV show episode organization and moving utilities."""

import argparse
import os
import shutil
from pathlib import Path
from typing import List, Dict, NamedTuple, Optional, Tuple
from collections import defaultdict

from .tv_scanner import (
    extract_tv_info_from_filename,
    is_video_file,
    format_file_size,
    normalize_show_name
)
from ..config.config import config

# Get TV directories from config
TV_DIRECTORIES = config.tv_directories


class EpisodeMove(NamedTuple):
    """Represents a planned episode move operation."""
    source_path: Path
    target_path: Path
    show_name: str
    season: int
    episode: int
    size: int
    action: str  # 'move_to_existing' or 'create_folder_and_move'


class SmallFolder(NamedTuple):
    """Represents a small folder that can be deleted."""
    path: Path
    size: int
    file_count: int


class TVMoveAnalysis(NamedTuple):
    """Results of TV directory analysis for moves."""
    moves: List[EpisodeMove]
    existing_show_folders: Dict[str, Path]
    new_folders_needed: List[str]
    small_folders: List[SmallFolder]
    total_episodes: int
    total_size: int


def _enhanced_normalize_show_name(show_name: str) -> str:
    """
    Enhanced show name normalization for better matching.
    
    Handles cases like:
    - "Mobland" vs "MobLand" 
    - "Breaking Bad" vs "Breaking.Bad"
    - "Game of Thrones" vs "Game Of Thrones"
    """
    # Remove common separators and convert to lowercase for comparison
    normalized = show_name.lower()
    normalized = normalized.replace('.', '').replace('_', '').replace('-', '')
    normalized = normalized.replace('  ', ' ').replace('  ', ' ')  # Multiple spaces to single
    normalized = normalized.strip()
    
    # Remove years in parentheses for matching
    import re
    normalized = re.sub(r'\s*\(\d{4}\)', '', normalized)
    
    # Remove common quality indicators that might be in folder names
    quality_indicators = ['1080p', '720p', '4k', 'hdtv', 'webrip', 'bluray', 'x264', 'x265', 'hevc']
    for indicator in quality_indicators:
        normalized = normalized.replace(indicator.lower(), '')
    
    # Clean up multiple spaces again
    normalized = ' '.join(normalized.split())
    
    return normalized


def _find_best_matching_show_folder(episode_show_name: str, existing_folders: Dict[str, Path]) -> Optional[Path]:
    """
    Find the best matching existing show folder using fuzzy matching.
    
    Args:
        episode_show_name: Show name extracted from episode filename
        existing_folders: Dictionary of existing show folders
        
    Returns:
        Path to best matching folder, or None if no good match found
    """
    episode_normalized = _enhanced_normalize_show_name(episode_show_name)
    
    # First try exact match
    for folder_key, folder_path in existing_folders.items():
        if _enhanced_normalize_show_name(folder_key) == episode_normalized:
            return folder_path
    
    # Then try fuzzy matching - look for folder names that contain the episode show name
    # or vice versa (handles "Mobland" folder matching "MobLand S01E01" episode)
    best_match = None
    best_score = 0
    
    for folder_key, folder_path in existing_folders.items():
        folder_normalized = _enhanced_normalize_show_name(folder_key)
        
        # Calculate similarity score
        score = 0
        
        # Special handling for case variations like "MobLand" vs "Mobland"
        # Check if they're the same after removing case and special chars
        episode_clean = episode_normalized.replace(' ', '').lower()
        folder_clean = folder_normalized.replace(' ', '').lower()
        
        # Check if this folder name looks like an individual episode folder
        # (contains season/episode patterns like "s01e01", "season 1", etc.)
        import re
        is_episode_folder = bool(re.search(r's\d+e\d+|season\s+\d+|s\d+\s|e\d+\s', folder_path.name.lower()))
        
        if episode_clean == folder_clean:
            if is_episode_folder:
                score = 0.70  # Lower score for individual episode folders
            else:
                score = 0.95  # Very high score for case-only differences in main folders
        elif episode_clean in folder_clean:
            # Check if the episode name is contained in the folder name
            # This handles "mobland" episode matching "mobland season 1" folder
            if is_episode_folder:
                score = 0.65  # Lower score for episode folders
            else:
                score = 0.9
        elif folder_clean in episode_clean:
            # Check if folder name is contained in episode name
            # This handles "mobland" folder matching "mobland s01e01" episode
            if is_episode_folder:
                score = 0.60  # Lower score for episode folders
            else:
                score = 0.85
        
        # Check if one is contained in the other (original logic)
        if episode_normalized in folder_normalized or folder_normalized in episode_normalized:
            # Prefer shorter names (more general folders over specific episode files)
            if len(folder_normalized) <= len(episode_normalized):
                score = max(score, 0.8)  # High score for folder containing episode name
            else:
                score = max(score, 0.7)  # Lower score for episode name containing folder name
        
        # Check for word-by-word matching
        episode_words = set(episode_normalized.split())
        folder_words = set(folder_normalized.split())
        
        if episode_words and folder_words:
            # Jaccard similarity (intersection over union)
            intersection = len(episode_words & folder_words)
            union = len(episode_words | folder_words)
            word_similarity = intersection / union if union > 0 else 0
            
            if word_similarity > 0.6:  # At least 60% word overlap
                score = max(score, word_similarity * 0.75)
        
        # Update best match if this is better
        if score > best_score and score >= 0.6:  # Minimum 60% confidence
            best_score = score
            best_match = folder_path
        elif score == best_score and score >= 0.6:
            # If scores are equal, prefer shorter folder names (more general)
            # This helps "Mobland" beat "MobLand S01E01" as a target
            if best_match and len(folder_path.name) < len(best_match.name):
                best_match = folder_path
    
    return best_match


def _handle_duplicate_episodes(moves: List[EpisodeMove]) -> List[EpisodeMove]:
    """
    Handle duplicate episodes by keeping the largest file.
    
    Args:
        moves: List of planned episode moves
        
    Returns:
        Filtered list with duplicates resolved (keeping largest file)
    """
    # Group by target path (same show, season, episode)
    from collections import defaultdict
    episode_groups = defaultdict(list)
    
    for move in moves:
        # Group by show, season, episode
        key = (move.show_name.lower(), move.season, move.episode)
        episode_groups[key].append(move)
    
    # Keep only the largest file for each episode
    filtered_moves = []
    duplicates_removed = []
    
    for episode_key, episode_moves in episode_groups.items():
        if len(episode_moves) == 1:
            # No duplicates
            filtered_moves.append(episode_moves[0])
        else:
            # Multiple files for same episode - keep largest
            largest_move = max(episode_moves, key=lambda m: m.size)
            filtered_moves.append(largest_move)
            
            # Track removed duplicates for logging
            for move in episode_moves:
                if move != largest_move:
                    duplicates_removed.append((move, largest_move))
    
    # Log duplicate removals
    if duplicates_removed:
        import logging
        logger = logging.getLogger("tv_organization")
        logger.info(f"Removed {len(duplicates_removed)} duplicate episodes (keeping largest files)")
        for removed, kept in duplicates_removed:
            logger.info(f"Duplicate: Removed {removed.source_path} ({format_file_size(removed.size)}) - Kept {kept.source_path} ({format_file_size(kept.size)})")
    
    return filtered_moves


def find_existing_show_folders(directory: str) -> Dict[str, Path]:
    """
    Find existing TV show folders in a directory with enhanced matching.
    
    Args:
        directory: Path to TV directory to scan
        
    Returns:
        Dictionary mapping normalized show names to their folder paths
    """
    show_folders = {}
    directory_path = Path(directory)
    
    if not directory_path.exists():
        return show_folders
    
    try:
        for item in directory_path.iterdir():
            if item.is_dir():
                # Use enhanced normalization for better matching
                normalized_name = _enhanced_normalize_show_name(item.name)
                
                # Store multiple variations to catch different naming patterns
                show_folders[normalized_name] = item
                
                # Also store case variations for better matching
                case_variants = [
                    item.name.lower(),
                    item.name.upper(), 
                    item.name.title(),
                    normalized_name.lower()
                ]
                
                for variant in case_variants:
                    if variant not in show_folders:
                        show_folders[variant] = item
                        
    except PermissionError:
        pass
    
    return show_folders


def find_loose_episodes(directory: str) -> List[Tuple[Path, str, int, int]]:
    """
    Find TV episodes that are loose (not in show folders).
    
    Args:
        directory: Path to TV directory to scan
        
    Returns:
        List of tuples: (file_path, show_name, season, episode)
    """
    loose_episodes = []
    directory_path = Path(directory)
    
    if not directory_path.exists():
        return loose_episodes
    
    try:
        # Scan root level and immediate subdirectories that don't look like show folders
        for item in directory_path.iterdir():
            if item.is_file() and is_video_file(item):
                # Check if it's a TV episode
                tv_info = extract_tv_info_from_filename(item.name)
                if tv_info:
                    show_name, season, episode = tv_info
                    loose_episodes.append((item, show_name, season, episode))
            
            elif item.is_dir():
                # Check if this directory looks like a season folder (e.g., "Season 1", "S01")
                dir_name_lower = item.name.lower()
                if any(pattern in dir_name_lower for pattern in ['season', 'series', 's0', 's1', 's2']):
                    # This might be a season folder outside a show folder
                    for episode_file in item.rglob('*'):
                        if episode_file.is_file() and is_video_file(episode_file):
                            tv_info = extract_tv_info_from_filename(episode_file.name)
                            if tv_info:
                                show_name, season, episode = tv_info
                                loose_episodes.append((episode_file, show_name, season, episode))
                
                # Also check one level deeper for loose episodes in non-show folders
                else:
                    try:
                        for subitem in item.iterdir():
                            if subitem.is_file() and is_video_file(subitem):
                                tv_info = extract_tv_info_from_filename(subitem.name)
                                if tv_info:
                                    show_name, season, episode = tv_info
                                    loose_episodes.append((subitem, show_name, season, episode))
                    except PermissionError:
                        continue
    
    except PermissionError:
        pass
    
    return loose_episodes


def find_small_folders(directory: str, max_size_mb: int = None) -> List[SmallFolder]:
    """
    Find folders smaller than the specified size.
    
    Args:
        directory: Path to TV directory to scan
        max_size_mb: Maximum folder size in MB (default: from config)
        
    Returns:
        List of SmallFolder objects
    """
    small_folders = []
    directory_path = Path(directory)
    
    if max_size_mb is None:
        max_size_mb = config.small_folder_threshold_mb
    max_size_bytes = max_size_mb * 1024 * 1024  # Convert MB to bytes
    
    if not directory_path.exists():
        return small_folders
    
    try:
        for item in directory_path.iterdir():
            if item.is_dir():
                try:
                    # Calculate folder size recursively
                    folder_size = 0
                    file_count = 0
                    
                    for file_path in item.rglob('*'):
                        if file_path.is_file():
                            try:
                                folder_size += file_path.stat().st_size
                                file_count += 1
                            except (OSError, PermissionError):
                                continue
                    
                    # Only consider folders smaller than max_size
                    if folder_size < max_size_bytes:
                        small_folder = SmallFolder(
                            path=item,
                            size=folder_size,
                            file_count=file_count
                        )
                        small_folders.append(small_folder)
                        
                except (OSError, PermissionError):
                    continue
    
    except PermissionError:
        pass
    
    return small_folders


def analyze_tv_moves(directories: List[str], find_small_folders_flag: bool = False, max_size_mb: int = None) -> TVMoveAnalysis:
    """
    Analyze TV directories to determine what episodes need to be moved.
    
    Args:
        directories: List of TV directory paths to analyze
        find_small_folders_flag: Whether to find small folders for deletion
        max_size_mb: Maximum folder size in MB for small folder detection (default: from config)
        
    Returns:
        TVMoveAnalysis with planned moves and small folders
    """
    if max_size_mb is None:
        max_size_mb = config.small_folder_threshold_mb
    all_moves = []
    all_existing_folders = {}
    new_folders_needed = set()
    all_small_folders = []
    total_episodes = 0
    total_size = 0
    
    for directory in directories:
        if not Path(directory).exists():
            continue
            
        # Find existing show folders
        existing_folders = find_existing_show_folders(directory)
        all_existing_folders.update(existing_folders)
        
        # Find small folders if requested
        if find_small_folders_flag:
            small_folders = find_small_folders(directory, max_size_mb)
            all_small_folders.extend(small_folders)
        
        # Find loose episodes
        loose_episodes = find_loose_episodes(directory)
        
        for episode_path, show_name, season, episode in loose_episodes:
            try:
                file_size = episode_path.stat().st_size
            except OSError:
                file_size = 0
            
            total_episodes += 1
            total_size += file_size
            
            # Use enhanced matching to find existing show folder
            best_match_folder = _find_best_matching_show_folder(show_name, all_existing_folders)
            
            if best_match_folder:
                # Move to existing show folder (with enhanced matching)
                # Create season folder if needed
                season_folder = best_match_folder / f"Season {season}"
                target_path = season_folder / episode_path.name
                action = 'move_to_existing'
                target_show_name = best_match_folder.name  # Use actual folder name
            else:
                # Need to create new show folder
                show_folder_name = show_name  # Use original extracted name
                target_folder = Path(directory) / show_folder_name
                season_folder = target_folder / f"Season {season}"
                target_path = season_folder / episode_path.name
                action = 'create_folder_and_move'
                new_folders_needed.add(show_folder_name)
                target_show_name = show_name
            
            move = EpisodeMove(
                source_path=episode_path,
                target_path=target_path,
                show_name=target_show_name,  # Use consistent show name
                season=season,
                episode=episode,
                size=file_size,
                action=action
            )
            all_moves.append(move)
    
    # Handle duplicates by keeping largest files
    all_moves = _handle_duplicate_episodes(all_moves)
    
    return TVMoveAnalysis(
        moves=all_moves,
        existing_show_folders=all_existing_folders,
        new_folders_needed=sorted(list(new_folders_needed)),
        small_folders=all_small_folders,
        total_episodes=total_episodes,
        total_size=total_size
    )


def print_move_analysis(analysis: TVMoveAnalysis, dry_run: bool = True) -> None:
    """
    Print detailed analysis of planned TV episode moves.
    
    Args:
        analysis: TVMoveAnalysis object with move plans
        dry_run: Whether this is a dry run (affects messaging)
    """
    mode_text = "DRY RUN - PREVIEW MODE" if dry_run else "EXECUTION MODE"
    action_text = "would be" if dry_run else "will be"
    
    print(f"TV EPISODE ORGANIZATION ANALYSIS")
    print("=" * 60)
    print(f"Mode: {mode_text}")
    print(f"Episodes found: {analysis.total_episodes}")
    print(f"Total size: {format_file_size(analysis.total_size)}")
    print(f"New folders needed: {len(analysis.new_folders_needed)}")
    print(f"Existing show folders: {len(analysis.existing_show_folders)}")
    print(f"Small folders found: {len(analysis.small_folders)}")
    
    if not analysis.moves and not analysis.small_folders:
        print("\nNo loose episodes or small folders found - all episodes are properly organized!")
        return
    
    # Group moves by show
    moves_by_show = defaultdict(list)
    for move in analysis.moves:
        moves_by_show[move.show_name].append(move)
    
    print(f"\n📺 EPISODE MOVES - WHAT'S MOVING WHERE:")
    print("=" * 70)
    
    # Show a clear summary first
    if analysis.moves:
        print(f"📊 MOVE SUMMARY:")
        print(f"   • {len(analysis.moves)} episodes will be moved")
        print(f"   • {len(moves_by_show)} shows affected")
        print(f"   • {format_file_size(analysis.total_size)} of data")
        if len(analysis.new_folders_needed) > 0:
            print(f"   • {len(analysis.new_folders_needed)} new show folders will be created")
        print()
    
    # Show detailed moves by show
    for show_name, moves in sorted(moves_by_show.items()):
        show_size = sum(move.size for move in moves)
        print(f"🎬 {show_name}")
        print(f"   📊 {len(moves)} episodes ({format_file_size(show_size)})")
        
        # Check if folder needs to be created
        create_folder = any(move.action == 'create_folder_and_move' for move in moves)
        if create_folder:
            folder_path = moves[0].target_path.parent
            print(f"   📁 CREATE new folder: {folder_path}")
        else:
            existing_folder = moves[0].target_path.parent
            print(f"   📂 MOVE to existing: {existing_folder}")
        
        # Show source locations being moved from
        source_dirs = set(move.source_path.parent for move in moves)
        if len(source_dirs) == 1:
            print(f"   📤 FROM: {list(source_dirs)[0]}")
        else:
            print(f"   📤 FROM multiple locations:")
            for source_dir in sorted(source_dirs):
                move_count = len([m for m in moves if m.source_path.parent == source_dir])
                print(f"      • {source_dir} ({move_count} episodes)")
        
        # Show sample episodes with clear before/after
        print(f"   📋 Sample episodes:")
        sorted_moves = sorted(moves, key=lambda x: (x.season, x.episode))
        for i, move in enumerate(sorted_moves[:5], 1):  # Show first 5
            episode_info = f"S{move.season:02d}E{move.episode:02d}"
            print(f"      {i}. {episode_info} - {move.source_path.name}")
            print(f"         FROM: {move.source_path.parent}")
            print(f"         TO:   {move.target_path.parent}")
        
        if len(moves) > 5:
            print(f"      ... and {len(moves) - 5} more episodes")
        print()
    
    # Summary of new folders
    if analysis.new_folders_needed:
        print(f"\nNEW FOLDERS THAT {action_text.upper()} CREATED:")
        print("-" * 40)
        for folder_name in analysis.new_folders_needed:
            print(f"   {folder_name}")
    
    # Summary by action type
    moves_to_existing = [m for m in analysis.moves if m.action == 'move_to_existing']
    moves_to_new = [m for m in analysis.moves if m.action == 'create_folder_and_move']
    
    print(f"\nSUMMARY:")
    print(f"   Episodes moving to existing folders: {len(moves_to_existing)}")
    print(f"   Episodes moving to new folders: {len(moves_to_new)}")
    print(f"   Total episodes to organize: {len(analysis.moves)}")
    print(f"   Total data to move: {format_file_size(analysis.total_size)}")
    
    # Show small folders section with clear separation
    if analysis.small_folders:
        print(f"\n🗑️  SMALL FOLDERS TO BE DELETED (CLEANUP):")
        print("=" * 70)
        print(f"ℹ️  These are small folders (<100MB) that will be deleted:")
        print()
        
        # Sort by size (smallest first)
        sorted_small_folders = sorted(analysis.small_folders, key=lambda x: x.size)
        
        # Show first 10 with more details, then summarize
        for i, folder in enumerate(sorted_small_folders[:10], 1):
            if folder.size == 0:
                print(f"{i:2d}. 📭 {folder.path.name} (EMPTY)")
            else:
                print(f"{i:2d}. 📁 {folder.path.name}")
            print(f"    📊 Size: {format_file_size(folder.size)}")
            print(f"    📄 Files: {folder.file_count}")
            print(f"    📂 Path: {folder.path}")
            print()
        
        if len(analysis.small_folders) > 10:
            remaining = len(analysis.small_folders) - 10
            remaining_size = sum(f.size for f in sorted_small_folders[10:])
            print(f"... and {remaining} more small folders ({format_file_size(remaining_size)})")
            print()
        
        small_folders_size = sum(folder.size for folder in analysis.small_folders)
        print(f"🗃️  Total cleanup: {format_file_size(small_folders_size)} in {len(analysis.small_folders)} folders")
        print()
        print("⚠️  NOTE: These are separate from the episode moves above!")
        print("   Episodes are MOVED to proper locations, small folders are DELETED.")
    
    # Clear final summary
    print(f"\n" + "=" * 70)
    print(f"📋 ORGANIZATION SUMMARY")
    print(f"=" * 70)
    
    if analysis.moves:
        print(f"📺 EPISODE MOVES:")
        print(f"   • {len(analysis.moves)} TV episodes will be MOVED to proper show folders")
        print(f"   • {format_file_size(analysis.total_size)} of video content will be organized")
        print(f"   • {len(moves_by_show)} shows will be organized")
        if len(analysis.new_folders_needed) > 0:
            print(f"   • {len(analysis.new_folders_needed)} new show folders will be created")
    
    if analysis.small_folders:
        small_folders_size = sum(folder.size for folder in analysis.small_folders)
        print(f"\n🗑️  CLEANUP:")
        print(f"   • {len(analysis.small_folders)} small/empty folders will be DELETED")
        print(f"   • {format_file_size(small_folders_size)} of cleanup space will be freed")
    
    if dry_run:
        print(f"\n🔍 THIS IS PREVIEW MODE - NO CHANGES WILL BE MADE")
        print(f"   Use --execute mode to actually perform the organization")
    else:
        print(f"\n⚠️  EXECUTION MODE - CHANGES WILL BE MADE!")
        print(f"   📺 Episodes will be MOVED to proper show folders")
        if analysis.small_folders:
            print(f"   🗑️  Small folders will be DELETED")
        print(f"   💾 Make sure you have BACKUPS before proceeding!")
    
    print(f"=" * 70)


def delete_small_folders(small_folders: List[SmallFolder]) -> Tuple[int, int]:
    """
    Delete small folders.
    
    Args:
        small_folders: List of SmallFolder objects to delete
        
    Returns:
        Tuple of (success_count, error_count)
    """
    success_count = 0
    error_count = 0
    
    if not small_folders:
        return success_count, error_count
    
    print(f"\nDELETING SMALL FOLDERS...")
    print("=" * 50)
    
    for i, folder in enumerate(small_folders, 1):
        print(f"\n[{i}/{len(small_folders)}] Deleting: {folder.path.name}")
        print(f"  Path: {folder.path}")
        print(f"  Size: {format_file_size(folder.size)} ({folder.file_count} files)")
        
        try:
            # Use shutil.rmtree to recursively delete the folder
            shutil.rmtree(str(folder.path))
            print(f"  Successfully deleted")
            success_count += 1
            
        except Exception as e:
            print(f"  Failed to delete: {e}")
            error_count += 1
    
    return success_count, error_count


def find_empty_or_small_folders_after_moves(moves: List[EpisodeMove], directories: List[str], max_size_mb: int = None) -> List[SmallFolder]:
    """
    Find folders that became empty or small after moving episodes.
    
    Args:
        moves: List of moves that were performed
        directories: List of directories to check
        max_size_mb: Maximum folder size in MB to consider for deletion (default: from config)
        
    Returns:
        List of SmallFolder objects that should be deleted
    """
    folders_to_check = set()
    
    if max_size_mb is None:
        max_size_mb = config.small_folder_threshold_mb
    max_size_bytes = max_size_mb * 1024 * 1024
    
    # Collect all source directories that had files moved from them
    for move in moves:
        source_parent = move.source_path.parent
        folders_to_check.add(source_parent)
        
        # Also check parent directories in case they became empty
        current = source_parent
        for directory in directories:
            directory_path = Path(directory)
            try:
                # Check if source_parent is within this TV directory
                if current.is_relative_to(directory_path) and current != directory_path:
                    while current.parent != directory_path and current != current.parent:
                        folders_to_check.add(current.parent)
                        current = current.parent
                break
            except (ValueError, OSError):
                continue
    
    small_folders = []
    
    for folder_path in folders_to_check:
        if not folder_path.exists():
            continue
            
        try:
            # Calculate current folder size
            folder_size = 0
            file_count = 0
            
            for file_path in folder_path.rglob('*'):
                if file_path.is_file():
                    try:
                        folder_size += file_path.stat().st_size
                        file_count += 1
                    except (OSError, PermissionError):
                        continue
            
            # Consider folder for deletion if it's empty or smaller than threshold
            if folder_size < max_size_bytes:
                small_folder = SmallFolder(
                    path=folder_path,
                    size=folder_size,
                    file_count=file_count
                )
                small_folders.append(small_folder)
                
        except (OSError, PermissionError):
            continue
    
    return small_folders


def execute_moves(analysis: TVMoveAnalysis, delete_small: bool = False, directories: List[str] = None) -> bool:
    """
    Execute the planned TV episode moves and automatically clean up empty/small folders.
    
    Args:
        analysis: TVMoveAnalysis with moves to execute
        delete_small: Whether to delete pre-existing small folders
        directories: List of TV directories (for cleanup after moves)
        
    Returns:
        True if all operations completed successfully, False otherwise
    """
    import logging
    logger = logging.getLogger("tv_organization")
    
    print(f"\n🚀 EXECUTING TV EPISODE MOVES...")
    print("=" * 70)
    logger.info(f"Starting execution of {len(analysis.moves)} moves")
    
    success_count = 0
    error_count = 0
    
    # Create new folders first
    if analysis.new_folders_needed:
        print(f"\n📁 Creating {len(analysis.new_folders_needed)} new show folders...")
        logger.info(f"Creating {len(analysis.new_folders_needed)} new folders")
        
        for i, folder_name in enumerate(analysis.new_folders_needed, 1):
            # Find the directory where this folder should be created
            folder_moves = [m for m in analysis.moves if m.target_path.parent.name == folder_name]
            if folder_moves:
                target_folder = folder_moves[0].target_path.parent
                try:
                    target_folder.mkdir(parents=True, exist_ok=True)
                    print(f"   [{i}/{len(analysis.new_folders_needed)}] ✅ Created: {target_folder}")
                    logger.info(f"Created folder: {target_folder}")
                except Exception as e:
                    print(f"   [{i}/{len(analysis.new_folders_needed)}] ❌ Failed: {target_folder} - {e}")
                    logger.error(f"Failed to create folder {target_folder}: {e}")
                    error_count += 1
                    continue
    
    # Execute moves with detailed progress tracking
    if analysis.moves:
        print(f"\n📺 Moving {len(analysis.moves)} TV episodes...")
        logger.info(f"Starting move execution for {len(analysis.moves)} episodes")
        
        # Group moves by show for better progress display
        from collections import defaultdict
        moves_by_show = defaultdict(list)
        for move in analysis.moves:
            moves_by_show[move.show_name].append(move)
        
        for show_name, show_moves in moves_by_show.items():
            print(f"\n🎬 Processing: {show_name} ({len(show_moves)} episodes)")
            logger.info(f"Processing show: {show_name} - {len(show_moves)} episodes")
            
            for j, move in enumerate(show_moves, 1):
                episode_info = f"S{move.season:02d}E{move.episode:02d}"
                print(f"   [{j}/{len(show_moves)}] {episode_info} - {move.source_path.name}")
                print(f"      FROM: {move.source_path.parent}")
                print(f"      TO:   {move.target_path.parent}")
                
                try:
                    # Ensure target directory exists
                    move.target_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    # Check if target file already exists
                    if move.target_path.exists():
                        print(f"      ⚠️  Target exists, creating unique name...")
                        logger.warning(f"Target file exists: {move.target_path}")
                        # Create unique name by adding number
                        base_name = move.target_path.stem
                        extension = move.target_path.suffix
                        counter = 1
                        original_target = move.target_path
                        while move.target_path.exists():
                            new_name = f"{base_name}_{counter}{extension}"
                            move = move._replace(target_path=move.target_path.parent / new_name)
                            counter += 1
                        print(f"      📝 New name: {move.target_path.name}")
                        logger.info(f"Using unique name: {move.target_path.name}")
                    
                    # Perform the move
                    file_size = move.source_path.stat().st_size
                    shutil.move(str(move.source_path), str(move.target_path))
                    print(f"      ✅ Moved ({format_file_size(file_size)})")
                    logger.info(f"Successfully moved: {move.source_path} -> {move.target_path}")
                    success_count += 1
                    
                except Exception as e:
                    print(f"      ❌ Failed: {e}")
                    logger.error(f"Failed to move {move.source_path}: {e}")
                    error_count += 1
    
    print(f"\n📊 MOVE RESULTS:")
    print(f"   ✅ Successful moves: {success_count}")
    print(f"   ❌ Failed moves: {error_count}")
    print(f"   📋 Total processed: {len(analysis.moves)}")
    
    if success_count > 0:
        moved_size = sum(move.size for move in analysis.moves)
        print(f"   💾 Data organized: {format_file_size(moved_size)}")
    
    logger.info(f"Move results: {success_count} success, {error_count} failed")
    
    # Delete pre-existing small folders if requested
    delete_success = 0
    delete_errors = 0
    if delete_small and analysis.small_folders:
        print(f"\n🗑️  CLEANING PRE-EXISTING SMALL FOLDERS...")
        logger.info(f"Cleaning {len(analysis.small_folders)} small folders")
        delete_success, delete_errors = delete_small_folders(analysis.small_folders)
        print(f"\n📊 SMALL FOLDER CLEANUP RESULTS:")
        print(f"   ✅ Successful deletions: {delete_success}")
        print(f"   ❌ Failed deletions: {delete_errors}")
        print(f"   📋 Total processed: {len(analysis.small_folders)}")
        logger.info(f"Small folder cleanup: {delete_success} success, {delete_errors} failed")
    
    # Automatically clean up folders that became empty/small after moves
    cleanup_success = 0
    cleanup_errors = 0
    if analysis.moves and directories:
        print(f"\n🧹 CLEANING UP EMPTY/SMALL FOLDERS AFTER MOVES...")
        print("=" * 70)
        logger.info("Starting post-move cleanup")
        
        # Find folders that became empty or small after the moves
        folders_to_cleanup = find_empty_or_small_folders_after_moves(analysis.moves, directories)
        
        if folders_to_cleanup:
            print(f"📂 Found {len(folders_to_cleanup)} folders to clean up:")
            logger.info(f"Found {len(folders_to_cleanup)} folders for cleanup")
            
            for folder in folders_to_cleanup:
                if folder.size == 0:
                    print(f"   📭 {folder.path.name} (EMPTY)")
                    logger.debug(f"Empty folder for cleanup: {folder.path}")
                else:
                    print(f"   📁 {folder.path.name} ({format_file_size(folder.size)}, {folder.file_count} files)")
                    logger.debug(f"Small folder for cleanup: {folder.path} - {folder.size} bytes")
            
            cleanup_success, cleanup_errors = delete_small_folders(folders_to_cleanup)
            print(f"\n📊 POST-MOVE CLEANUP RESULTS:")
            print(f"   ✅ Successful cleanups: {cleanup_success}")
            print(f"   ❌ Failed cleanups: {cleanup_errors}")
            print(f"   📋 Total processed: {len(folders_to_cleanup)}")
            logger.info(f"Post-move cleanup: {cleanup_success} success, {cleanup_errors} failed")
        else:
            print("✅ No folders need cleanup - source directories still contain content.")
            logger.info("No post-move cleanup needed")
    
    # Final summary
    total_success = success_count + delete_success + cleanup_success
    total_errors = error_count + delete_errors + cleanup_errors
    
    print(f"\n🎉 TV ORGANIZATION COMPLETE!")
    print("=" * 70)
    print(f"📊 FINAL SUMMARY:")
    print(f"   📺 Episodes moved: {success_count}")
    if delete_success > 0:
        print(f"   🗑️  Small folders cleaned: {delete_success}")
    if cleanup_success > 0:
        print(f"   🧹 Post-move cleanup: {cleanup_success}")
    print(f"   ✅ Total successful operations: {total_success}")
    if total_errors > 0:
        print(f"   ❌ Total errors: {total_errors}")
    print("=" * 70)
    
    if total_errors == 0:
        print("🎊 ALL OPERATIONS COMPLETED SUCCESSFULLY!")
        logger.info("TV organization completed successfully - no errors")
    else:
        print(f"⚠️  COMPLETED WITH {total_errors} ERRORS - check log for details")
        logger.warning(f"TV organization completed with {total_errors} errors")
    
    return error_count == 0 and delete_errors == 0 and cleanup_errors == 0


def main() -> None:
    """Main entry point for TV episode mover."""
    parser = argparse.ArgumentParser(
        description="Organize TV episodes by moving them into proper show folders",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Static TV Directories Configured:
{chr(10).join(f"  - {path}" for path in config.tv_directories)}

Examples:
  # Dry run with default directories (preview mode)
  python -m file_managers.plex.utils.tv_mover
  
  # Dry run with custom directories
  python -m file_managers.plex.utils.tv_mover --custom "C:/TV,D:/Shows"
  
  # Dry run and find small folders for deletion
  python -m file_managers.plex.utils.tv_mover --delete-small
  
  # Dry run with custom size threshold (50MB instead of 100MB)
  python -m file_managers.plex.utils.tv_mover --delete-small --max-size 50
  
  # Actually execute the moves (DANGEROUS!)
  python -m file_managers.plex.utils.tv_mover --execute
  
  # Execute moves and delete small folders (VERY DANGEROUS!)
  python -m file_managers.plex.utils.tv_mover --execute --delete-small
        """
    )
    
    parser.add_argument(
        "--custom",
        help="Comma-separated list of custom TV directories to analyze instead of static paths"
    )
    
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Actually execute the moves (DEFAULT: dry run mode)"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output"
    )
    
    parser.add_argument(
        "--delete-small",
        action="store_true",
        help=f"Delete folders smaller than specified size (default: {config.small_folder_threshold_mb}MB)"
    )
    
    parser.add_argument(
        "--max-size",
        type=int,
        default=None,
        help=f"Maximum folder size in MB for deletion (default: {config.small_folder_threshold_mb})"
    )
    
    args = parser.parse_args()
    
    # Determine directories to use
    if args.custom:
        directories = [d.strip() for d in args.custom.split(',') if d.strip()]
        use_static = False
    else:
        directories = TV_DIRECTORIES
        use_static = True
    
    try:
        # Analyze what needs to be moved
        if args.verbose:
            directory_type = "predefined" if use_static else "custom"
            print(f"Analyzing {directory_type} TV directories...")
            for i, directory in enumerate(directories, 1):
                print(f"  {i}. {directory}")
            print()
        
        analysis = analyze_tv_moves(directories, find_small_folders_flag=args.delete_small, max_size_mb=args.max_size)
        
        # Show analysis results
        print_move_analysis(analysis, dry_run=not args.execute)
        
        # Execute moves if requested
        if args.execute:
            if analysis.moves or (args.delete_small and analysis.small_folders):
                print(f"\n" + "WARNING: " * 10)
                if analysis.moves:
                    print("You are about to MOVE TV episode files!")
                if args.delete_small and analysis.small_folders:
                    print(f"You are about to DELETE {len(analysis.small_folders)} small folders!")
                print("This will change your file structure!")
                print("Make sure you have backups before proceeding!")
                print("WARNING: " * 10)
                
                action_items = []
                if analysis.moves:
                    action_items.append(f"moving {len(analysis.moves)} episodes")
                if args.delete_small and analysis.small_folders:
                    action_items.append(f"deleting {len(analysis.small_folders)} small folders")
                
                action_text = " and ".join(action_items)
                confirm = input(f"\nType 'EXECUTE' to proceed with {action_text}: ").strip()
                if confirm == "EXECUTE":
                    success = execute_moves(analysis, delete_small=args.delete_small, directories=directories)
                    if success:
                        print(f"\nAll operations completed successfully!")
                    else:
                        print(f"\nSome operations failed - check the output above")
                else:
                    print(f"\nOperation cancelled")
            else:
                print(f"\nNo operations needed - all episodes are already organized!")
                if args.delete_small:
                    print(f"No small folders found to delete.")
        
    except KeyboardInterrupt:
        print(f"\nOperation cancelled by user")
    except Exception as e:
        print(f"Error during analysis: {e}")


if __name__ == "__main__":
    main()