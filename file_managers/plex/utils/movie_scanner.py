"""Movie duplicate detection utilities."""

import os
import re
from pathlib import Path
from typing import Dict, List, NamedTuple, Set, Tuple
from collections import defaultdict

# Static list of movie directory paths  
# QNAP Server: 192.168.1.27 mounted at /mnt/qnap/
# TODO: Move to external config file for easier management
MOVIE_DIRECTORIES = [
    "/mnt/qnap/plex/Movie/",         # \\192.168.1.27\plex\Movie
    "/mnt/qnap/Media/Movies/",       # \\192.168.1.27\Media\Movies  
    "/mnt/qnap/Multimedia/Movies/",  # \\192.168.1.27\Multimedia\Movies
]


class MovieFile(NamedTuple):
    """Represents a movie file with its metadata."""
    path: Path
    name: str
    normalized_name: str
    size: int
    year: str


class DuplicateGroup(NamedTuple):
    """Represents a group of duplicate movies."""
    normalized_name: str
    files: List[MovieFile]
    best_file: MovieFile  # The file to keep (largest/best quality)


def normalize_movie_name(filename: str) -> str:
    """
    Normalize movie filename for comparison.
    
    Removes quality indicators, release groups, and other metadata
    to focus on the actual movie title.
    """
    # Remove file extension
    name = Path(filename).stem
    
    # Common patterns to remove
    patterns_to_remove = [
        r'\b(720p|1080p|480p|4K|2160p)\b',  # Quality
        r'\b(BluRay|BRRip|DVDRip|WEBRip|HDTV|CAM|TS)\b',  # Source
        r'\b(x264|x265|H264|H265|HEVC|DivX|XviD)\b',  # Codec
        r'\b(AC3|DTS|AAC|MP3)\b',  # Audio
        r'\[(.*?)\]',  # Release group in brackets
        r'\{(.*?)\}',  # Release group in braces
        r'-\w+$',  # Release group at end after dash
        r'\.REPACK\.',  # Repack indicator
        r'\.PROPER\.',  # Proper release indicator
        r'\.EXTENDED\.',  # Extended cut
        r'\.UNRATED\.',  # Unrated version
        r'\.DC\.',  # Director's cut
    ]
    
    # Apply removal patterns
    for pattern in patterns_to_remove:
        name = re.sub(pattern, '', name, flags=re.IGNORECASE)
    
    # Replace dots, underscores, and multiple spaces with single space
    name = re.sub(r'[._]+', ' ', name)
    name = re.sub(r'\s+', ' ', name)
    
    # Remove leading/trailing whitespace and convert to lowercase
    return name.strip().lower()


def extract_year_from_filename(filename: str) -> str:
    """Extract year from movie filename."""
    # Look for 4-digit year pattern
    year_match = re.search(r'\b(19\d{2}|20\d{2})\b', filename)
    return year_match.group(1) if year_match else ""


def scan_directory_for_movies(directory_path: str) -> List[MovieFile]:
    """
    Scan directory for movie files.
    
    Returns list of MovieFile objects for all video files found.
    """
    movie_extensions = {'.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.m4v', '.mpg', '.mpeg'}
    movies = []
    
    directory = Path(directory_path)
    if not directory.exists():
        raise FileNotFoundError(f"Directory not found: {directory_path}")
    
    for file_path in directory.rglob('*'):
        if file_path.is_file() and file_path.suffix.lower() in movie_extensions:
            try:
                size = file_path.stat().st_size
                name = file_path.name
                normalized_name = normalize_movie_name(name)
                year = extract_year_from_filename(name)
                
                movies.append(MovieFile(
                    path=file_path,
                    name=name,
                    normalized_name=normalized_name,
                    size=size,
                    year=year
                ))
            except (OSError, PermissionError):
                # Skip files we can't access
                continue
    
    return movies


def find_duplicate_movies_in_static_paths() -> List[DuplicateGroup]:
    """
    Find duplicate movies in the predefined static directory paths.
    
    Returns:
        List of DuplicateGroup objects containing duplicate movies
    """
    return find_duplicate_movies_custom(MOVIE_DIRECTORIES)


def find_duplicate_movies_custom(directory_paths: List[str]) -> List[DuplicateGroup]:
    """
    Find duplicate movies across multiple directories.
    
    Args:
        directory_paths: List of directory paths to scan
        
    Returns:
        List of DuplicateGroup objects containing duplicate movies
    """
    return find_duplicate_movies(directory_paths)


def find_duplicate_movies(directory_paths: List[str]) -> List[DuplicateGroup]:
    """
    Find duplicate movies across multiple directories.
    
    Args:
        directory_paths: List of directory paths to scan
        
    Returns:
        List of DuplicateGroup objects containing duplicate movies
    """
    all_movies = []
    
    # Collect all movies from all directories
    for directory_path in directory_paths:
        try:
            movies = scan_directory_for_movies(directory_path)
            all_movies.extend(movies)
        except FileNotFoundError as e:
            print(f"Warning: {e}")
            continue
    
    # Group movies by normalized name and year
    movie_groups = defaultdict(list)
    for movie in all_movies:
        # Use normalized name + year as key for better matching
        key = f"{movie.normalized_name}_{movie.year}" if movie.year else movie.normalized_name
        movie_groups[key].append(movie)
    
    # Find groups with duplicates
    duplicates = []
    for normalized_name, movies in movie_groups.items():
        if len(movies) > 1:
            # Sort by size to find largest (best quality)
            movies_sorted = sorted(movies, key=lambda x: x.size, reverse=True)
            best_file = movies_sorted[0]  # Largest file = best quality
            
            duplicates.append(DuplicateGroup(
                normalized_name=normalized_name,
                files=movies,
                best_file=best_file
            ))
    
    return duplicates


def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} PB"


def print_duplicate_report(duplicates: List[DuplicateGroup]) -> None:
    """Print a formatted report of duplicate movies."""
    if not duplicates:
        print("✅ No duplicate movies found across all directories.")
        return
    
    print(f"\n🔍 Found {len(duplicates)} groups of duplicate movies:\n")
    print("=" * 80)
    
    total_wasted_space = 0
    
    for i, group in enumerate(duplicates, 1):
        print(f"\n{i}. 🎬 Movie: {group.normalized_name.title()}")
        print(f"   📁 Found {len(group.files)} copies across directories:")
        
        # Calculate wasted space (all files except best/largest)
        group_wasted = sum(movie.size for movie in group.files) - group.best_file.size
        total_wasted_space += group_wasted
        
        # Group files by directory for better visualization
        by_directory = defaultdict(list)
        for movie in group.files:
            by_directory[str(movie.path.parent)].append(movie)
        
        for j, movie in enumerate(sorted(group.files, key=lambda x: x.size, reverse=True), 1):
            size_str = format_file_size(movie.size)
            is_best = movie == group.best_file
            marker = " ← 🟢 KEEP (Largest/Best Quality)" if is_best else " ← ❌ DELETE CANDIDATE"
            
            print(f"      {j}. {movie.name}")
            print(f"         📂 Path: {movie.path.parent}")
            print(f"         💾 Size: {size_str}{marker}")
            if movie.year:
                print(f"         📅 Year: {movie.year}")
        
        print(f"\n   ✅ Recommended action: Keep {group.best_file.name}")
        print(f"      📂 Location: {group.best_file.path.parent}")
        print(f"      💿 Space saved by removing duplicates: {format_file_size(group_wasted)}")
        print("-" * 80)
    
    # Summary
    print(f"\n📊 SUMMARY:")
    print(f"   🎯 Total duplicate groups: {len(duplicates)}")
    print(f"   📁 Total files that can be deleted: {sum(len(group.files) - 1 for group in duplicates)}")
    print(f"   💾 Total space that can be recovered: {format_file_size(total_wasted_space)}")
    print(f"\n⚠️  IMPORTANT: This is analysis only - NO FILES HAVE BEEN DELETED")


def print_scan_progress(directories: List[str]) -> None:
    """Print scan progress information."""
    print("🔍 Scanning directories for movie files...")
    print("📁 Directories to scan:")
    for i, directory in enumerate(directories, 1):
        print(f"   {i}. {directory}")
    print()


def main() -> None:
    """Main entry point for running movie duplicate scanner directly."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Movie duplicate detection scanner")
    parser.add_argument("--custom", type=str, help="Comma-separated list of custom directories to scan")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")
    
    args = parser.parse_args()
    
    print("🎬 MOVIE DUPLICATE SCANNER")
    print("=" * 50)
    
    try:
        if args.custom:
            # Parse custom directories
            directories = [dir_path.strip() for dir_path in args.custom.split(",")]
            print(f"📁 Scanning custom directories: {len(directories)}")
            if args.verbose:
                print_scan_progress(directories)
            duplicates = find_duplicate_movies_custom(directories)
        else:
            # Use static/default directories
            print(f"📁 Scanning predefined directories: {len(MOVIE_DIRECTORIES)}")
            if args.verbose:
                print_scan_progress(MOVIE_DIRECTORIES)
            duplicates = find_duplicate_movies_in_static_paths()
        
        print_duplicate_report(duplicates)
        
        # Summary
        if duplicates:
            total_files = sum(len(group.files) for group in duplicates)
            total_duplicates = sum(len(group.files) - 1 for group in duplicates)
            print(f"\n📊 SUMMARY: Found {len(duplicates)} duplicate groups with {total_duplicates} files that could be removed from {total_files} total files.")
        else:
            print("\n📊 SUMMARY: No duplicates found - your movie collection is well organized!")
            
    except KeyboardInterrupt:
        print("\n\n👋 Scan cancelled by user")
    except Exception as e:
        print(f"❌ Error during scan: {e}")


if __name__ == "__main__":
    main()