#!/usr/bin/env python3
"""TV show organizer CLI tool."""

import argparse
import sys
from pathlib import Path
from typing import List

from ..utils.tv_scanner import (
    find_unorganized_tv_episodes,
    find_unorganized_tv_episodes_custom,
    print_tv_organization_report,
    print_scan_progress,
    TV_DIRECTORIES,
)
from ..utils.tv_report_generator import (
    generate_tv_folder_analysis_report,
    generate_tv_organization_plan_report,
    generate_tv_json_reports,
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
    """Main entry point for TV show organizer CLI."""
    parser = argparse.ArgumentParser(
        description="Analyze and organize TV show episodes in Plex directories",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Static TV Directories Configured:
{chr(10).join(f"  - {path}" for path in TV_DIRECTORIES)}

Examples:
  # Analyze predefined TV directories (default)
  python -m file_managers.plex.cli.tv_organizer
  
  # Analyze custom directories instead
  python -m file_managers.plex.cli.tv_organizer --custom "C:/TV,D:/Shows"
  
  # Generate folder analysis report only
  python -m file_managers.plex.cli.tv_organizer --folder-analysis-only
  
  # Show what would be moved (demonstration mode)
  python -m file_managers.plex.cli.tv_organizer --demo
        """
    )
    
    parser.add_argument(
        "--custom",
        help="Comma-separated list of custom TV directories to analyze instead of static paths"
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
    
    parser.add_argument(
        "--no-reports",
        action="store_true",
        help="Skip generating report files (only show console output)"
    )
    
    parser.add_argument(
        "--folder-analysis-only",
        action="store_true",
        help="Only analyze existing folder structure, don't look for unorganized episodes"
    )
    
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Demonstration mode: show what would be moved without actually moving files"
    )
    
    parser.add_argument(
        "--organize",
        action="store_true",
        help="Actually organize episodes by moving them to show folders (DANGEROUS: will move files)"
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
        directories = TV_DIRECTORIES
        use_static = True
    
    if args.verbose:
        directory_type = "predefined" if use_static else "custom"
        print(f"📺 TV Show Organizer")
        print(f"📁 Using {directory_type} directories")
        print_scan_progress(directories)
    
    try:
        # Generate folder analysis report first
        if not args.no_reports:
            print(f"📊 Analyzing existing TV folder structure...")
            folder_report = generate_tv_folder_analysis_report(directories)
            print(f"✅ TV folder analysis report: {folder_report}")
        
        # If only folder analysis requested, stop here
        if args.folder_analysis_only:
            print(f"\n📊 Folder analysis complete!")
            return
        
        # Find unorganized episodes
        if use_static:
            tv_groups = find_unorganized_tv_episodes()
        else:
            tv_groups = find_unorganized_tv_episodes_custom(directories)
        
        # Handle demonstration mode
        if args.demo:
            print(f"\n🎯 DEMONSTRATION MODE")
            print("=" * 60)
            print("This shows what WOULD be moved during organization")
            print("NO FILES WILL ACTUALLY BE MOVED")
            print("=" * 60)
            
            # Print console report
            print_tv_organization_report(tv_groups)
            
            if tv_groups:
                print(f"\n📋 Organization Summary:")
                total_episodes = sum(group.episode_count for group in tv_groups)
                total_shows = len(tv_groups)
                print(f"  • {total_shows} TV shows need organization")
                print(f"  • {total_episodes} episodes would be moved")
                print(f"  • Target folders would be created automatically")
                print(f"\n💡 Use --organize flag to actually perform the moves")
            
            return
        
        # Handle actual organization mode
        if args.organize:
            print(f"\n🗂️  ORGANIZATION MODE - WARNING!")
            print("=" * 60)
            print("⚠️  You are about to MOVE TV episode files!")
            print("⚠️  This will change your file structure!")
            print("⚠️  Make sure you have backups!")
            print("=" * 60)
            
            if not tv_groups:
                print("✅ No unorganized episodes found - nothing to move!")
                return
            
            confirm = input("\\nType 'ORGANIZE FILES' to continue: ").strip()
            if confirm == "ORGANIZE FILES":
                print("🗂️  Starting TV show organization...")
                # TODO: Implement actual file moving logic
                print("⚠️  Organization functionality coming soon!")
                print("     Use --demo mode to see what would be moved")
            else:
                print("🚫 Organization cancelled")
            return
        
        # Default: Analysis mode
        print_tv_organization_report(tv_groups)
        
        # Generate organization plan report
        if not args.no_reports:
            print(f"\\n📄 Generating organization plan report...")
            
            try:
                # Generate organization plan report
                plan_report = generate_tv_organization_plan_report(tv_groups)
                print(f"✅ Organization plan report: {plan_report}")
                
                # Generate JSON reports for programmatic access
                folder_json, plan_json = generate_tv_json_reports(directories, tv_groups)
                print(f"✅ JSON folder analysis: {folder_json}")
                print(f"✅ JSON organization plan: {plan_json}")
                
                print(f"\\n📁 All reports saved to: {Path(plan_report).parent}")
                
            except Exception as e:
                print(f"⚠️  Warning: Could not generate reports: {e}", file=sys.stderr)
        
        # Summary
        if tv_groups:
            total_episodes = sum(group.episode_count for group in tv_groups)
            total_shows = len(tv_groups)
            print(f"\\n📊 SUMMARY:")
            print(f"  Total shows needing organization: {total_shows}")
            print(f"  Total episodes to organize: {total_episodes}")
            print(f"\\n⚠️  IMPORTANT: This is analysis only - NO FILES WERE MOVED")
            print(f"      Use --demo to see organization plan")
            print(f"      Use --organize to actually move files (coming soon)")
        else:
            print(f"\\n✅ All TV episodes appear to be properly organized!")
        
    except KeyboardInterrupt:
        print("\\nScan interrupted by user.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error during analysis: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()