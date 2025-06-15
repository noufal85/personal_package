#!/usr/bin/env python3
"""Movie duplicate scanner CLI tool."""

import argparse
import sys
from pathlib import Path
from typing import List

from ..utils.movie_scanner import (
    find_duplicate_movies_in_static_paths,
    find_duplicate_movies_custom,
    print_duplicate_report,
    print_scan_progress,
    MOVIE_DIRECTORIES,
)


def parse_directory_list(directories_str: str) -> List[str]:
    """Parse comma-separated directory list."""
    directories = [d.strip() for d in directories_str.split(',')]
    return [d for d in directories if d]  # Remove empty strings


def validate_directories(directories: List[str]) -> List[str]:
    """Validate that directories exist and are accessible."""
    valid_directories = []
    for directory in directories:
        path = Path(directory)
        if not path.exists():
            print(f"Warning: Directory does not exist: {directory}", file=sys.stderr)
            continue
        if not path.is_dir():
            print(f"Warning: Path is not a directory: {directory}", file=sys.stderr)
            continue
        valid_directories.append(directory)
    
    return valid_directories


def main() -> None:
    """Main entry point for movie duplicate scanner CLI."""
    parser = argparse.ArgumentParser(
        description="Find duplicate movies in predefined Plex directories",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Static Directories Configured:
{chr(10).join(f"  - {path}" for path in MOVIE_DIRECTORIES)}

Examples:
  # Scan predefined static directories (default)
  python -m file_managers.cli.movie_duplicates
  
  # Scan custom directories instead
  python -m file_managers.cli.movie_duplicates --custom "C:/Movies,D:/Films"
        """
    )
    
    parser.add_argument(
        "--custom",
        help="Comma-separated list of custom directories to scan instead of static paths"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output showing scan progress"
    )
    
    parser.add_argument(
        "--min-size",
        type=int,
        default=10,
        help="Minimum file size in MB to consider (default: 10MB)"
    )
    
    args = parser.parse_args()
    
    # Determine which directories to use
    if args.custom:
        directories = parse_directory_list(args.custom)
        if not directories:
            print("Error: No valid custom directories specified", file=sys.stderr)
            sys.exit(1)
        directories = validate_directories(directories)
        if not directories:
            print("Error: No valid custom directories found", file=sys.stderr)
            sys.exit(1)
        use_static = False
    else:
        directories = MOVIE_DIRECTORIES
        use_static = True
    
    if args.verbose:
        directory_type = "predefined" if use_static else "custom"
        print(f"🎬 Movie Duplicate Scanner")
        print(f"📁 Using {directory_type} directories")
        print_scan_progress(directories)
    
    try:2
        # Find duplicates using appropriate method
        if use_static:
            duplicates = find_duplicate_movies_in_static_paths()
        else:
            duplicates = find_duplicate_movies_custom(directories)
        
        # Print report
        print_duplicate_report(duplicates)
        
        # Summary
        if duplicates:
            total_duplicates = sum(len(group.files) - 1 for group in duplicates)
            print(f"\nSummary:")
            print(f"  Total duplicate groups: {len(duplicates)}")
            print(f"  Total duplicate files: {total_duplicates}")
            print(f"\nNote: This is a dry run. No files were deleted.")
            print(f"      Review the results before implementing deletion logic.")
        
    except KeyboardInterrupt:
        print("\nScan interrupted by user.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error during scan: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()