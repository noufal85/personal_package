"""TV show scanner utilities for detecting and organizing TV episodes."""

import re
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, NamedTuple, Optional, Tuple

# Static TV directories - modify these to match your setup
# TODO: Move to external config file for easier management
TV_DIRECTORIES = [
    "/mnt/qnap/Multimedia/TV/",     # \\192.168.1.27\Multimedia\TV
    "/mnt/qnap/Media/TV/",          # \\192.168.1.27\Media\TV
    "/mnt/qnap/plex/TV/"            # \\192.168.1.27\plex\TV
]

# Future media type directories (placeholders for expansion)
# MUSIC_DIRECTORIES = []
# DOCUMENTARY_DIRECTORIES = []  
# STANDUP_DIRECTORIES = []

# Common video file extensions
VIDEO_EXTENSIONS = {'.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm', '.m4v', '.ts', '.mpg', '.mpeg'}

# TV show name patterns - common naming conventions
TV_SHOW_PATTERNS = [
    # Show.Name.S01E01.Episode.Title.quality.mkv
    r'^(.+?)\.S(\d+)E(\d+)',
    # Show Name - S01E01 - Episode Title.mkv  
    r'^(.+?)\s*-\s*S(\d+)E(\d+)',
    # Show Name S01E01 Episode Title.mkv
    r'^(.+?)\s+S(\d+)E(\d+)',
    # Show.Name.1x01.Episode.Title.mkv
    r'^(.+?)\.(\d+)x(\d+)',
    # Show Name - 1x01 - Episode Title.mkv
    r'^(.+?)\s*-\s*(\d+)x(\d+)',
    # Show Name 1x01 Episode Title.mkv
    r'^(.+?)\s+(\d+)x(\d+)',
    # Show Name Season 1 Episode 01.mkv
    r'^(.+?)\s+Season\s+(\d+)\s+Episode\s+(\d+)',
    # Show Name s1e01.mkv (lowercase)
    r'^(.+?)\s+s(\d+)e(\d+)',
]


class TVEpisode(NamedTuple):
    """Represents a TV episode file with metadata."""
    name: str                    # Original filename
    show_name: str              # Detected show name
    season: int                 # Season number
    episode: int                # Episode number
    path: Path                  # Full file path
    size: int                   # File size in bytes
    suggested_folder: str       # Suggested destination folder name


class TVShowGroup(NamedTuple):
    """Represents a group of episodes for the same TV show."""
    show_name: str              # Normalized show name
    episodes: List[TVEpisode]   # List of episode files
    total_size: int             # Total size of all episodes
    season_count: int           # Number of seasons
    episode_count: int          # Total number of episodes


def normalize_show_name(show_name: str) -> str:
    """
    Normalize TV show name for consistent grouping.
    
    Args:
        show_name: Raw show name from filename
        
    Returns:
        Normalized show name
    """
    # Remove common separators and convert to lowercase
    normalized = show_name.replace('.', ' ').replace('_', ' ').replace('-', ' ')
    
    # Remove extra whitespace
    normalized = ' '.join(normalized.split())
    
    # Convert to title case for consistency
    normalized = normalized.title()
    
    # Handle common abbreviations and fixes
    replacements = {
        'Tv': 'TV',
        'Uk': 'UK',
        'Us': 'US',
        'Fbi': 'FBI',
        'Csi': 'CSI',
        'Ncis': 'NCIS',
        'Nypd': 'NYPD',
    }
    
    for old, new in replacements.items():
        normalized = normalized.replace(old, new)
    
    return normalized.strip()


def extract_tv_info_from_filename(filename: str) -> Optional[Tuple[str, int, int]]:
    """
    Extract TV show information from filename using regex patterns.
    
    Args:
        filename: The filename to analyze
        
    Returns:
        Tuple of (show_name, season, episode) or None if not detected
    """
    # Remove file extension for cleaner matching
    name_without_ext = Path(filename).stem
    
    for pattern in TV_SHOW_PATTERNS:
        match = re.search(pattern, name_without_ext, re.IGNORECASE)
        if match:
            show_name = match.group(1)
            season = int(match.group(2))
            episode = int(match.group(3))
            
            # Clean up show name
            show_name = normalize_show_name(show_name)
            
            return show_name, season, episode
    
    return None


def is_video_file(file_path: Path) -> bool:
    """Check if file is a video file based on extension."""
    return file_path.suffix.lower() in VIDEO_EXTENSIONS


def scan_directory_for_tv_episodes(directory: str) -> List[TVEpisode]:
    """
    Scan a directory for TV episode files.
    
    Args:
        directory: Directory path to scan
        
    Returns:
        List of TVEpisode objects found in the directory
    """
    episodes = []
    directory_path = Path(directory)
    
    if not directory_path.exists():
        return episodes
    
    # Recursively find all video files
    for file_path in directory_path.rglob('*'):
        if not file_path.is_file() or not is_video_file(file_path):
            continue
        
        # Extract TV show information
        tv_info = extract_tv_info_from_filename(file_path.name)
        if not tv_info:
            continue
        
        show_name, season, episode = tv_info
        
        try:
            file_size = file_path.stat().st_size
        except (OSError, IOError):
            continue
        
        # Create suggested folder name (same as normalized show name)
        suggested_folder = show_name
        
        episode_obj = TVEpisode(
            name=file_path.name,
            show_name=show_name,
            season=season,
            episode=episode,
            path=file_path,
            size=file_size,
            suggested_folder=suggested_folder
        )
        
        episodes.append(episode_obj)
    
    return episodes


def group_episodes_by_show(episodes: List[TVEpisode]) -> List[TVShowGroup]:
    """
    Group episodes by TV show name.
    
    Args:
        episodes: List of TVEpisode objects
        
    Returns:
        List of TVShowGroup objects
    """
    # Group episodes by show name
    show_groups = defaultdict(list)
    for episode in episodes:
        show_groups[episode.show_name].append(episode)
    
    # Create TVShowGroup objects
    groups = []
    for show_name, show_episodes in show_groups.items():
        total_size = sum(ep.size for ep in show_episodes)
        
        # Count unique seasons
        seasons = set(ep.season for ep in show_episodes)
        season_count = len(seasons)
        
        episode_count = len(show_episodes)
        
        group = TVShowGroup(
            show_name=show_name,
            episodes=show_episodes,
            total_size=total_size,
            season_count=season_count,
            episode_count=episode_count
        )
        groups.append(group)
    
    return groups


def find_unorganized_tv_episodes() -> List[TVShowGroup]:
    """
    Find all unorganized TV episodes in static directories.
    
    Returns:
        List of TVShowGroup objects representing shows that need organization
    """
    all_episodes = []
    
    for directory in TV_DIRECTORIES:
        episodes = scan_directory_for_tv_episodes(directory)
        all_episodes.extend(episodes)
    
    return group_episodes_by_show(all_episodes)


def find_unorganized_tv_episodes_custom(directories: List[str]) -> List[TVShowGroup]:
    """
    Find all unorganized TV episodes in custom directories.
    
    Args:
        directories: List of directory paths to scan
        
    Returns:
        List of TVShowGroup objects representing shows that need organization
    """
    all_episodes = []
    
    for directory in directories:
        episodes = scan_directory_for_tv_episodes(directory)
        all_episodes.extend(episodes)
    
    return group_episodes_by_show(all_episodes)


def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format."""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    size = float(size_bytes)
    
    while size >= 1024.0 and i < len(size_names) - 1:
        size /= 1024.0
        i += 1
    
    return f"{size:.1f} {size_names[i]}"


def print_tv_organization_report(tv_groups: List[TVShowGroup]) -> None:
    """
    Print a detailed report of TV shows that need organization.
    
    Args:
        tv_groups: List of TVShowGroup objects to report on
    """
    if not tv_groups:
        print("✅ No unorganized TV episodes found!")
        return
    
    print(f"\n📺 TV SHOW ORGANIZATION REPORT")
    print("=" * 80)
    print(f"Found {len(tv_groups)} TV shows with unorganized episodes")
    
    total_episodes = sum(group.episode_count for group in tv_groups)
    total_size = sum(group.total_size for group in tv_groups)
    
    print(f"Total episodes to organize: {total_episodes}")
    print(f"Total size: {format_file_size(total_size)}")
    
    # Sort by total size (largest first)
    sorted_groups = sorted(tv_groups, key=lambda x: x.total_size, reverse=True)
    
    print(f"\n📋 SHOWS TO ORGANIZE (by size):")
    print("-" * 80)
    
    for i, group in enumerate(sorted_groups, 1):
        print(f"\n{i}. {group.show_name}")
        print(f"   Episodes: {group.episode_count} across {group.season_count} season(s)")
        print(f"   Total Size: {format_file_size(group.total_size)}")
        print(f"   Target Folder: {group.show_name}/")
        
        # Show first few episodes as examples
        sample_episodes = sorted(group.episodes, key=lambda x: (x.season, x.episode))[:3]
        print(f"   Sample Episodes:")
        for ep in sample_episodes:
            print(f"     • S{ep.season:02d}E{ep.episode:02d} - {ep.name}")
            print(f"       Current: {ep.path.parent}")
            print(f"       → Move to: {ep.path.parent.parent / group.show_name}/")
        
        if len(group.episodes) > 3:
            print(f"     ... and {len(group.episodes) - 3} more episodes")


def print_scan_progress(directories: List[str]) -> None:
    """Print scan progress information."""
    print(f"Scanning {len(directories)} directories for TV episodes:")
    for i, directory in enumerate(directories, 1):
        print(f"  {i}. {directory}")
    print()