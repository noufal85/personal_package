"""Report generation utilities for movie duplicate detection and inventory management."""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Tuple

from .movie_scanner import DuplicateGroup, MovieFile, format_file_size, scan_directory_for_movies
from ..config.config import config


def get_reports_directory() -> Path:
    """Get the reports directory, creating it if it doesn't exist."""
    reports_dir = config.get_reports_path()
    reports_dir.mkdir(exist_ok=True)
    return reports_dir


def generate_timestamp() -> str:
    """Generate timestamp string for report filenames."""
    return datetime.now().strftime(config.timestamp_format)


def generate_duplicate_report(duplicates: List[DuplicateGroup]) -> Tuple[str, str]:
    """
    Generate duplicate movies report in both text and JSON formats.
    
    Args:
        duplicates: List of DuplicateGroup objects
        
    Returns:
        Tuple of (text_report_path, json_report_path)
    """
    timestamp = generate_timestamp()
    reports_dir = get_reports_directory()
    
    # Generate filenames
    txt_filename = f"duplicates_{timestamp}.txt"
    json_filename = f"duplicates_{timestamp}.json"
    txt_path = reports_dir / txt_filename
    json_path = reports_dir / json_filename
    
    # Calculate summary statistics
    total_wasted_space = sum(
        sum(movie.size for movie in group.files) - group.best_file.size
        for group in duplicates
    )
    total_duplicate_files = sum(len(group.files) - 1 for group in duplicates)
    
    # Sort duplicates by wasted space (largest first)
    duplicates_sorted = sorted(
        duplicates,
        key=lambda g: sum(movie.size for movie in g.files) - g.best_file.size,
        reverse=True
    )
    
    # Generate text report
    _generate_duplicate_text_report(duplicates_sorted, txt_path, total_wasted_space, total_duplicate_files)
    
    # Generate JSON report
    _generate_duplicate_json_report(duplicates_sorted, json_path, total_wasted_space, total_duplicate_files)
    
    return str(txt_path), str(json_path)


def _generate_duplicate_text_report(duplicates: List[DuplicateGroup], output_path: Path, 
                                   total_wasted_space: int, total_duplicate_files: int) -> None:
    """Generate human-readable duplicate movies report."""
    with open(output_path, 'w', encoding='utf-8') as f:
        # Header
        f.write("🔍 DUPLICATE MOVIES REPORT\n")
        f.write("=" * 80 + "\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Duplicate Groups Found: {len(duplicates)}\n")
        f.write(f"Total Duplicate Files: {total_duplicate_files}\n")
        f.write(f"Total Wasted Space: {format_file_size(total_wasted_space)}\n\n")
        
        f.write("🎬 DUPLICATE GROUPS (by wasted space)\n")
        f.write("=" * 80 + "\n\n")
        
        # Process each duplicate group
        for i, group in enumerate(duplicates, 1):
            # Calculate wasted space for this group
            group_wasted = sum(movie.size for movie in group.files) - group.best_file.size
            
            f.write(f"{i}. {group.normalized_name.title()}\n")
            f.write(f"   Copies Found: {len(group.files)}\n")
            f.write(f"   Wasted Space: {format_file_size(group_wasted)}\n")
            f.write("-" * 60 + "\n")
            
            # List all files in the group, sorted by size (largest first)
            files_sorted = sorted(group.files, key=lambda x: x.size, reverse=True)
            
            for j, movie in enumerate(files_sorted, 1):
                is_keep = movie == group.best_file
                marker = "🟢 KEEP" if is_keep else "❌ DELETE CANDIDATE"
                
                f.write(f"  {j}. {movie.name}\n")
                f.write(f"     Size: {format_file_size(movie.size)} {marker}\n")
                f.write(f"     Path: {movie.path.parent}\n")
                if movie.year:
                    f.write(f"     Year: {movie.year}\n")
                f.write("\n")
            
            # Recommendation
            f.write(f"   → RECOMMENDATION: Keep '{group.best_file.name}'\n")
            f.write(f"     Location: {group.best_file.path.parent}\n\n")
        
        # Summary footer
        f.write("=" * 80 + "\n")
        f.write("📊 SUMMARY\n")
        f.write("=" * 80 + "\n")
        f.write(f"Total duplicate groups: {len(duplicates)}\n")
        f.write(f"Total files that can be deleted: {total_duplicate_files}\n")
        f.write(f"Total space that can be recovered: {format_file_size(total_wasted_space)}\n\n")
        f.write("⚠️  IMPORTANT: This is analysis only - NO FILES HAVE BEEN DELETED\n")


def _generate_duplicate_json_report(duplicates: List[DuplicateGroup], output_path: Path,
                                   total_wasted_space: int, total_duplicate_files: int) -> None:
    """Generate machine-readable duplicate movies report."""
    report_data = {
        "timestamp": datetime.now().isoformat(),
        "summary": {
            "duplicate_groups": len(duplicates),
            "total_duplicate_files": total_duplicate_files,
            "total_wasted_space": total_wasted_space
        },
        "duplicates": []
    }
    
    for group in duplicates:
        group_wasted = sum(movie.size for movie in group.files) - group.best_file.size
        
        group_data = {
            "normalized_name": group.normalized_name,
            "file_count": len(group.files),
            "wasted_space": group_wasted,
            "files": [],
            "recommended_keep": {
                "name": group.best_file.name,
                "path": str(group.best_file.path)
            }
        }
        
        for movie in group.files:
            movie_data = {
                "name": movie.name,
                "size": movie.size,
                "year": movie.year,
                "path": str(movie.path),
                "is_smallest": movie == group.best_file
            }
            group_data["files"].append(movie_data)
        
        report_data["duplicates"].append(group_data)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report_data, f, indent=2, ensure_ascii=False)


def generate_movie_inventory_report(directory_paths: List[str]) -> Tuple[str, str]:
    """
    Generate comprehensive movie inventory reports in both text and JSON formats.
    
    Args:
        directory_paths: List of directory paths to analyze
        
    Returns:
        Tuple of (text_report_path, json_report_path)
    """
    timestamp = generate_timestamp()
    reports_dir = get_reports_directory()
    
    # Generate filenames
    txt_filename = f"movie_inventory_{timestamp}.txt"
    json_filename = f"movie_inventory_{timestamp}.json"
    txt_path = reports_dir / txt_filename
    json_path = reports_dir / json_filename
    
    # Collect movie data from all directories
    directory_data = []
    for directory_path in directory_paths:
        try:
            movies = scan_directory_for_movies(directory_path)
            if movies:  # Only include directories with movies
                directory_info = {
                    "path": directory_path,
                    "movie_count": len(movies),
                    "total_size": sum(movie.size for movie in movies),
                    "movies": movies
                }
                directory_data.append(directory_info)
        except FileNotFoundError:
            # Skip directories that don't exist
            continue
    
    # Generate text report
    _generate_inventory_text_report(directory_data, txt_path)
    
    # Generate JSON report
    _generate_inventory_json_report(directory_data, json_path)
    
    return str(txt_path), str(json_path)


def _generate_inventory_text_report(directory_data: List[Dict], output_path: Path) -> None:
    """Generate human-readable movie inventory report."""
    with open(output_path, 'w', encoding='utf-8') as f:
        # Header
        f.write("🎬 MOVIE INVENTORY REPORT\n")
        f.write("=" * 80 + "\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Scanned Directories: {len(directory_data)}\n\n\n")
        
        # Process each directory
        for i, dir_info in enumerate(directory_data, 1):
            f.write(f"📁 DIRECTORY {i}: {dir_info['path']}\n")
            f.write("-" * 60 + "\n")
            f.write(f"Total Movies: {dir_info['movie_count']}\n")
            f.write(f"Total Size: {format_file_size(dir_info['total_size'])}\n")
            
            if dir_info['movie_count'] > 0:
                avg_size = dir_info['total_size'] / dir_info['movie_count']
                f.write(f"Average File Size: {format_file_size(int(avg_size))}\n\n")
                
                # Sort movies by size (largest first) and show top 10
                movies_sorted = sorted(dir_info['movies'], key=lambda x: x.size, reverse=True)
                f.write("Movies by Size (Largest First):\n")
                
                for j, movie in enumerate(movies_sorted[:10], 1):  # Show top 10
                    f.write(f"    {j}. {movie.name}\n")
                    f.write(f"       Size: {format_file_size(movie.size)}\n")
                    if movie.year:
                        f.write(f"       Year: {movie.year}\n")
                    f.write(f"       Path: {movie.path.parent}\n\n")
                
                if len(movies_sorted) > 10:
                    f.write(f"    ... and {len(movies_sorted) - 10} more movies\n\n")
            
            f.write("\n")
        
        # Summary
        total_movies = sum(dir_info['movie_count'] for dir_info in directory_data)
        total_size = sum(dir_info['total_size'] for dir_info in directory_data)
        
        f.write("=" * 80 + "\n")
        f.write("📊 OVERALL SUMMARY\n")
        f.write("=" * 80 + "\n")
        f.write(f"Total directories scanned: {len(directory_data)}\n")
        f.write(f"Total movies found: {total_movies}\n")
        f.write(f"Total library size: {format_file_size(total_size)}\n")
        if total_movies > 0:
            avg_size = total_size / total_movies
            f.write(f"Average movie size: {format_file_size(int(avg_size))}\n")


def _generate_inventory_json_report(directory_data: List[Dict], output_path: Path) -> None:
    """Generate machine-readable movie inventory report."""
    report_data = {
        "timestamp": datetime.now().isoformat(),
        "directories": []
    }
    
    for dir_info in directory_data:
        dir_data = {
            "path": dir_info["path"],
            "movie_count": dir_info["movie_count"],
            "total_size": dir_info["total_size"],
            "movies": []
        }
        
        for movie in dir_info["movies"]:
            movie_data = {
                "name": movie.name,
                "normalized_name": movie.normalized_name,
                "size": movie.size,
                "year": movie.year,
                "path": str(movie.path)
            }
            dir_data["movies"].append(movie_data)
        
        report_data["directories"].append(dir_data)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report_data, f, indent=2, ensure_ascii=False)


def generate_combined_movie_reports(directory_paths: List[str], duplicates: List[DuplicateGroup]) -> Dict[str, str]:
    """
    Generate both inventory and duplicate reports for the same dataset.
    
    Args:
        directory_paths: List of directory paths that were scanned
        duplicates: List of DuplicateGroup objects found
        
    Returns:
        Dictionary with report paths: {
            'inventory_txt': path,
            'inventory_json': path,
            'duplicates_txt': path,
            'duplicates_json': path
        }
    """
    # Generate inventory reports
    inventory_txt, inventory_json = generate_movie_inventory_report(directory_paths)
    
    # Generate duplicate reports
    duplicates_txt, duplicates_json = generate_duplicate_report(duplicates)
    
    return {
        'inventory_txt': inventory_txt,
        'inventory_json': inventory_json,
        'duplicates_txt': duplicates_txt,
        'duplicates_json': duplicates_json
    }


def print_report_summary(report_paths: Dict[str, str]) -> None:
    """Print a summary of generated reports."""
    print("\n📄 REPORTS GENERATED")
    print("=" * 50)
    
    if 'inventory_txt' in report_paths:
        print(f"📊 Movie Inventory (Text): {report_paths['inventory_txt']}")
    if 'inventory_json' in report_paths:
        print(f"📊 Movie Inventory (JSON): {report_paths['inventory_json']}")
    if 'duplicates_txt' in report_paths:
        print(f"🔍 Duplicates Report (Text): {report_paths['duplicates_txt']}")
    if 'duplicates_json' in report_paths:
        print(f"🔍 Duplicates Report (JSON): {report_paths['duplicates_json']}")
    
    # Show reports directory
    reports_dir = get_reports_directory()
    print(f"\n📁 All reports saved to: {reports_dir}")


def main() -> None:
    """Main entry point - generates both inventory and duplicate reports using default directories."""
    from .movie_scanner import find_duplicate_movies_in_static_paths
    
    print("📄 MOVIE REPORT GENERATOR")
    print("=" * 50)
    print("🔍 Scanning for movies and duplicates...")
    
    try:
        # Find duplicates using static paths
        duplicates = find_duplicate_movies_in_static_paths()
        
        # Generate both reports
        report_paths = generate_combined_movie_reports(config.movie_directories, duplicates)
        
        # Show results
        if duplicates:
            total_duplicates = sum(len(group.files) - 1 for group in duplicates)
            total_wasted = sum(
                sum(movie.size for movie in group.files) - group.best_file.size
                for group in duplicates
            )
            print(f"🔍 Found {len(duplicates)} duplicate groups with {total_duplicates} files")
            print(f"💾 Potential space savings: {format_file_size(total_wasted)}")
        else:
            print("✅ No duplicates found - library is well organized!")
        
        print_report_summary(report_paths)
        
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()