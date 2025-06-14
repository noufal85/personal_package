"""TV show report generation utilities."""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

from .tv_scanner import (
    TV_DIRECTORIES,
    TVShowGroup,
    TVEpisode,
    format_file_size,
    scan_directory_for_tv_episodes,
)


def get_reports_directory() -> Path:
    """Get the reports directory path."""
    current_dir = Path.cwd()
    reports_dir = current_dir / "reports"
    reports_dir.mkdir(exist_ok=True)
    return reports_dir


def get_timestamp() -> str:
    """Get current timestamp for report naming."""
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def analyze_existing_tv_folders(directories: List[str]) -> Dict[str, Dict]:
    """
    Analyze existing TV show folder structure and sizes.
    
    Args:
        directories: List of TV directories to analyze
        
    Returns:
        Dictionary with folder analysis data
    """
    folder_analysis = {}
    
    for directory in directories:
        directory_path = Path(directory)
        if not directory_path.exists():
            folder_analysis[directory] = {"error": "Directory not found"}
            continue
        
        folder_stats = {
            "total_folders": 0,
            "total_size": 0,
            "folders": [],
            "loose_files": []
        }
        
        try:
            # Analyze direct subdirectories (assumed to be show folders)
            for item in directory_path.iterdir():
                if item.is_dir():
                    folder_info = analyze_show_folder(item)
                    folder_stats["folders"].append(folder_info)
                    folder_stats["total_folders"] += 1
                    folder_stats["total_size"] += folder_info["size"]
                elif item.is_file() and item.suffix.lower() in {'.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm', '.m4v', '.ts', '.mpg', '.mpeg'}:
                    # Loose video files at root level
                    try:
                        file_size = item.stat().st_size
                        folder_stats["loose_files"].append({
                            "name": item.name,
                            "size": file_size,
                            "formatted_size": format_file_size(file_size),
                            "path": str(item)
                        })
                        folder_stats["total_size"] += file_size
                    except (OSError, IOError):
                        pass
                        
        except Exception as e:
            folder_analysis[directory] = {"error": str(e)}
            continue
        
        # Sort folders by size (largest first)
        folder_stats["folders"].sort(key=lambda x: x["size"], reverse=True)
        folder_stats["loose_files"].sort(key=lambda x: x["size"], reverse=True)
        
        folder_analysis[directory] = folder_stats
    
    return folder_analysis


def analyze_show_folder(folder_path: Path) -> Dict:
    """
    Analyze a single TV show folder.
    
    Args:
        folder_path: Path to the TV show folder
        
    Returns:
        Dictionary with folder analysis
    """
    folder_info = {
        "name": folder_path.name,
        "path": str(folder_path),
        "size": 0,
        "file_count": 0,
        "video_files": 0,
        "subdirectories": 0,
        "seasons": set(),
        "episodes": []
    }
    
    try:
        # Recursively analyze all files in the folder
        for file_path in folder_path.rglob('*'):
            if file_path.is_file():
                try:
                    file_size = file_path.stat().st_size
                    folder_info["size"] += file_size
                    folder_info["file_count"] += 1
                    
                    # Check if it's a video file
                    if file_path.suffix.lower() in {'.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm', '.m4v', '.ts', '.mpg', '.mpeg'}:
                        folder_info["video_files"] += 1
                        
                        # Try to extract episode information
                        from .tv_scanner import extract_tv_info_from_filename
                        tv_info = extract_tv_info_from_filename(file_path.name)
                        if tv_info:
                            show_name, season, episode = tv_info
                            folder_info["seasons"].add(season)
                            folder_info["episodes"].append({
                                "filename": file_path.name,
                                "season": season,
                                "episode": episode,
                                "size": file_size,
                                "relative_path": str(file_path.relative_to(folder_path))
                            })
                
                except (OSError, IOError):
                    pass
            elif file_path.is_dir() and file_path != folder_path:
                folder_info["subdirectories"] += 1
    
    except Exception:
        pass
    
    # Convert seasons set to sorted list for JSON serialization
    folder_info["seasons"] = sorted(list(folder_info["seasons"]))
    folder_info["season_count"] = len(folder_info["seasons"])
    folder_info["formatted_size"] = format_file_size(folder_info["size"])
    
    return folder_info


def generate_tv_folder_analysis_report(directories: List[str]) -> str:
    """
    Generate a comprehensive TV folder analysis report.
    
    Args:
        directories: List of TV directories to analyze
        
    Returns:
        Path to the generated report file
    """
    timestamp = get_timestamp()
    reports_dir = get_reports_directory()
    report_file = reports_dir / f"tv_folder_analysis_{timestamp}.txt"
    
    folder_analysis = analyze_existing_tv_folders(directories)
    
    # Calculate totals
    total_folders = 0
    total_size = 0
    total_loose_files = 0
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("📺 TV SHOW FOLDER ANALYSIS REPORT\n")
        f.write("=" * 80 + "\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Analyzed Directories: {len(directories)}\n\n")
        
        for i, directory in enumerate(directories, 1):
            f.write(f"\n📁 DIRECTORY {i}: {directory}\n")
            f.write("-" * 60 + "\n")
            
            if directory not in folder_analysis:
                f.write("❌ Directory not analyzed\n")
                continue
            
            stats = folder_analysis[directory]
            
            if "error" in stats:
                f.write(f"❌ Error: {stats['error']}\n")
                continue
            
            f.write(f"Total TV Show Folders: {stats['total_folders']}\n")
            f.write(f"Total Size: {format_file_size(stats['total_size'])}\n")
            f.write(f"Loose Files (not in show folders): {len(stats['loose_files'])}\n\n")
            
            # Update totals
            total_folders += stats['total_folders']
            total_size += stats['total_size']
            total_loose_files += len(stats['loose_files'])
            
            # Show folder details
            if stats['folders']:
                f.write("📺 TV SHOW FOLDERS (by size):\n")
                f.write("-" * 40 + "\n")
                
                for j, folder in enumerate(stats['folders'][:20], 1):  # Top 20 folders
                    f.write(f"{j:2d}. {folder['name']}\n")
                    f.write(f"    Size: {folder['formatted_size']}\n")
                    f.write(f"    Files: {folder['video_files']} video, {folder['file_count']} total\n")
                    if folder['seasons']:
                        f.write(f"    Seasons: {len(folder['seasons'])} ({', '.join(f'S{s}' for s in folder['seasons'])})\n")
                    f.write(f"    Episodes: {len(folder['episodes'])}\n")
                    f.write(f"    Path: {folder['path']}\n\n")
                
                if len(stats['folders']) > 20:
                    f.write(f"... and {len(stats['folders']) - 20} more folders\n\n")
            
            # Show loose files
            if stats['loose_files']:
                f.write("🔍 LOOSE VIDEO FILES (not in show folders):\n")
                f.write("-" * 40 + "\n")
                
                for j, loose_file in enumerate(stats['loose_files'][:10], 1):  # Top 10 loose files
                    f.write(f"{j:2d}. {loose_file['name']}\n")
                    f.write(f"    Size: {loose_file['formatted_size']}\n")
                    f.write(f"    Path: {loose_file['path']}\n\n")
                
                if len(stats['loose_files']) > 10:
                    f.write(f"... and {len(stats['loose_files']) - 10} more loose files\n\n")
        
        # Summary section
        f.write("\n" + "=" * 80 + "\n")
        f.write("📊 OVERALL SUMMARY\n")
        f.write("=" * 80 + "\n")
        f.write(f"Total Directories Analyzed: {len(directories)}\n")
        f.write(f"Total TV Show Folders: {total_folders}\n")
        f.write(f"Total Storage Used: {format_file_size(total_size)}\n")
        f.write(f"Total Loose Files: {total_loose_files}\n")
        f.write(f"Average Folder Size: {format_file_size(total_size // total_folders) if total_folders else '0 B'}\n\n")
        
        # Directory comparison
        f.write("📁 DIRECTORY COMPARISON\n")
        f.write("-" * 40 + "\n")
        for directory in directories:
            if directory in folder_analysis and "error" not in folder_analysis[directory]:
                stats = folder_analysis[directory] 
                dir_name = Path(directory).name
                f.write(f"{dir_name:20s}: {stats['total_folders']:4d} folders, {format_file_size(stats['total_size'])}\n")
    
    return str(report_file)


def generate_tv_organization_plan_report(tv_groups: List[TVShowGroup]) -> str:
    """
    Generate a report showing what episodes would be moved during organization.
    
    Args:
        tv_groups: List of TVShowGroup objects
        
    Returns:
        Path to the generated report file
    """
    timestamp = get_timestamp()
    reports_dir = get_reports_directory()
    report_file = reports_dir / f"tv_organization_plan_{timestamp}.txt"
    
    total_episodes = sum(group.episode_count for group in tv_groups)
    total_size = sum(group.total_size for group in tv_groups)
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("📺 TV SHOW ORGANIZATION PLAN\n")
        f.write("=" * 80 + "\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Shows to Organize: {len(tv_groups)}\n")
        f.write(f"Total Episodes: {total_episodes}\n")
        f.write(f"Total Size: {format_file_size(total_size)}\n\n")
        
        if not tv_groups:
            f.write("✅ No unorganized TV episodes found!\n")
            return str(report_file)
        
        # Sort by total size (largest first)
        sorted_groups = sorted(tv_groups, key=lambda x: x.total_size, reverse=True)
        
        f.write("📋 ORGANIZATION PLAN (by size):\n")
        f.write("=" * 80 + "\n")
        
        for i, group in enumerate(sorted_groups, 1):
            f.write(f"\n{i}. {group.show_name}\n")
            f.write(f"   Episodes: {group.episode_count} across {group.season_count} season(s)\n")
            f.write(f"   Total Size: {format_file_size(group.total_size)}\n")
            f.write(f"   Target Folder: {group.show_name}/\n")
            f.write("-" * 60 + "\n")
            
            # Group episodes by current directory
            episodes_by_dir = {}
            for episode in group.episodes:
                current_dir = str(episode.path.parent)
                if current_dir not in episodes_by_dir:
                    episodes_by_dir[current_dir] = []
                episodes_by_dir[current_dir].append(episode)
            
            # Show moves by source directory
            for current_dir, episodes in episodes_by_dir.items():
                f.write(f"   FROM: {current_dir}\n")
                f.write(f"   Episodes in this location: {len(episodes)}\n")
                
                # Sort episodes by season/episode
                sorted_episodes = sorted(episodes, key=lambda x: (x.season, x.episode))
                
                # Show first few episodes
                for ep in sorted_episodes[:5]:
                    f.write(f"     • S{ep.season:02d}E{ep.episode:02d} - {ep.name}\n")
                    f.write(f"       Size: {format_file_size(ep.size)}\n")
                
                if len(episodes) > 5:
                    f.write(f"     ... and {len(episodes) - 5} more episodes\n")
                
                f.write(f"   → TO: {Path(current_dir).parent / group.show_name}/\n\n")
        
        # Summary of moves by directory
        f.write("\n" + "=" * 80 + "\n")
        f.write("📊 MOVES BY SOURCE DIRECTORY\n")
        f.write("=" * 80 + "\n")
        
        all_source_dirs = {}
        for group in tv_groups:
            for episode in group.episodes:
                source_dir = str(episode.path.parent)
                if source_dir not in all_source_dirs:
                    all_source_dirs[source_dir] = {"episodes": 0, "size": 0}
                all_source_dirs[source_dir]["episodes"] += 1
                all_source_dirs[source_dir]["size"] += episode.size
        
        for source_dir, stats in sorted(all_source_dirs.items(), key=lambda x: x[1]["size"], reverse=True):
            f.write(f"{Path(source_dir).name}:\n")
            f.write(f"  Episodes to move: {stats['episodes']}\n")
            f.write(f"  Total size: {format_file_size(stats['size'])}\n")
            f.write(f"  Path: {source_dir}\n\n")
    
    return str(report_file)


def generate_tv_json_reports(directories: List[str], tv_groups: List[TVShowGroup]) -> Tuple[str, str]:
    """
    Generate JSON versions of TV reports for programmatic access.
    
    Args:
        directories: List of TV directories
        tv_groups: List of TVShowGroup objects
        
    Returns:
        Tuple of (folder_analysis_json_path, organization_plan_json_path)
    """
    timestamp = get_timestamp()
    reports_dir = get_reports_directory()
    
    # Folder analysis JSON
    folder_file = reports_dir / f"tv_folder_analysis_{timestamp}.json"
    folder_analysis = analyze_existing_tv_folders(directories)
    
    # Calculate summary statistics
    summary_stats = {
        "total_directories": len(directories),
        "total_folders": 0,
        "total_size": 0,
        "total_loose_files": 0,
        "timestamp": datetime.now().isoformat()
    }
    
    for directory, stats in folder_analysis.items():
        if "error" not in stats:
            summary_stats["total_folders"] += stats.get("total_folders", 0)
            summary_stats["total_size"] += stats.get("total_size", 0)
            summary_stats["total_loose_files"] += len(stats.get("loose_files", []))
    
    folder_data = {
        "summary": summary_stats,
        "directories": folder_analysis
    }
    
    try:
        with open(folder_file, 'w', encoding='utf-8') as f:
            json.dump(folder_data, f, indent=2, ensure_ascii=False)
    except IOError as e:
        # If file writing fails, try without indentation to reduce size
        with open(folder_file, 'w', encoding='utf-8') as f:
            json.dump(folder_data, f, ensure_ascii=False)
    
    # Organization plan JSON
    plan_file = reports_dir / f"tv_organization_plan_{timestamp}.json"
    plan_data = {
        "timestamp": datetime.now().isoformat(),
        "summary": {
            "shows_to_organize": len(tv_groups),
            "total_episodes": sum(group.episode_count for group in tv_groups),
            "total_size": sum(group.total_size for group in tv_groups)
        },
        "shows": [
            {
                "show_name": group.show_name,
                "episode_count": group.episode_count,
                "season_count": group.season_count,
                "total_size": group.total_size,
                "episodes": [
                    {
                        "filename": ep.name,
                        "season": ep.season,
                        "episode": ep.episode,
                        "size": ep.size,
                        "current_path": str(ep.path),
                        "target_folder": ep.suggested_folder
                    }
                    for ep in sorted(group.episodes, key=lambda x: (x.season, x.episode))
                ]
            }
            for group in sorted(tv_groups, key=lambda x: x.total_size, reverse=True)
        ]
    }
    
    try:
        with open(plan_file, 'w', encoding='utf-8') as f:
            json.dump(plan_data, f, indent=2, ensure_ascii=False)
    except IOError as e:
        # If file writing fails, try without indentation to reduce size
        with open(plan_file, 'w', encoding='utf-8') as f:
            json.dump(plan_data, f, ensure_ascii=False)
    
    return str(folder_file), str(plan_file)


def main() -> None:
    """Main entry point - generates TV folder analysis and organization plan reports using default directories."""
    from .tv_scanner import find_unorganized_tv_episodes
    
    print("📺 TV REPORT GENERATOR")
    print("=" * 50)
    print("🔍 Analyzing TV directories and organization...")
    
    try:
        # Generate folder analysis report
        print("📊 Generating TV folder analysis report...")
        folder_report = generate_tv_folder_analysis_report(TV_DIRECTORIES)
        print(f"✅ TV folder analysis report: {folder_report}")
        
        # Find unorganized episodes
        print("🔍 Scanning for unorganized TV episodes...")
        tv_groups = find_unorganized_tv_episodes()
        
        # Generate organization plan report
        print("📄 Generating organization plan report...")
        plan_report = generate_tv_organization_plan_report(tv_groups)
        print(f"✅ Organization plan report: {plan_report}")
        
        # Generate JSON reports
        print("📄 Generating JSON reports...")
        folder_json, plan_json = generate_tv_json_reports(TV_DIRECTORIES, tv_groups)
        print(f"✅ JSON folder analysis: {folder_json}")
        print(f"✅ JSON organization plan: {plan_json}")
        
        # Show summary
        if tv_groups:
            total_episodes = sum(group.episode_count for group in tv_groups)
            total_shows = len(tv_groups)
            total_size = sum(group.total_size for group in tv_groups)
            print(f"\n📊 SUMMARY:")
            print(f"  Total shows needing organization: {total_shows}")
            print(f"  Total episodes to organize: {total_episodes}")
            print(f"  Total size to organize: {format_file_size(total_size)}")
        else:
            print(f"\n✅ All TV episodes appear to be properly organized!")
        
        reports_dir = get_reports_directory()
        print(f"\n📁 All reports saved to: {reports_dir}")
        
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()