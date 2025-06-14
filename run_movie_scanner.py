#!/usr/bin/env python3
"""Interactive movie duplicate scanner launcher."""

import os
import sys
import subprocess
from pathlib import Path


def clear_screen():
    """Clear the terminal screen."""
    os.system('cls' if os.name == 'nt' else 'clear')


def print_banner():
    """Print the application banner."""
    print("=" * 60)
    print("          🎬📺 PLEX MEDIA MANAGER 🎬📺")
    print("=" * 60)
    print()


def print_menu():
    """Print the main menu options."""
    print("🎬 MOVIE OPTIONS:")
    print("  1. Scan movies for duplicates (Analysis Only)")
    print("  2. Scan custom movie directories (Analysis Only)")
    print("  3. 🗑️  DELETE movie duplicates (DANGEROUS)")
    print("\n📺 TV SHOW OPTIONS:")
    print("  4. Analyze TV show organization")
    print("  5. TV show demo mode (show what would be moved)")
    print("  6. Analyze existing TV folder structure only")
    print("\n📊 GENERAL OPTIONS:")
    print("  7. View configured directories")
    print("  8. View recent reports")
    print("  9. Exit")
    print()


def get_user_choice():
    """Get user menu choice."""
    while True:
        try:
            choice = input("Enter your choice (1-9): ").strip()
            if choice in ['1', '2', '3', '4', '5', '6', '7', '8', '9']:
                return int(choice)
            print("Invalid choice. Please enter 1, 2, 3, 4, 5, 6, 7, 8, or 9.")
        except KeyboardInterrupt:
            print("\nExiting...")
            sys.exit(0)


def show_configured_directories():
    """Show the configured static directories for both movies and TV shows."""
    try:
        from file_managers.plex.utils.movie_scanner import MOVIE_DIRECTORIES
        from file_managers.plex.utils.tv_scanner import TV_DIRECTORIES
        
        print("\n🎬 Configured Movie Directories:")
        print("-" * 40)
        for i, directory in enumerate(MOVIE_DIRECTORIES, 1):
            print(f"  {i}. {directory}")
        
        print("\n📺 Configured TV Directories:")
        print("-" * 40)
        for i, directory in enumerate(TV_DIRECTORIES, 1):
            print(f"  {i}. {directory}")
        print()
        
    except ImportError:
        print("Error: Could not import movie scanner module.")
        print("Make sure the package is installed: pip install -e .")


def get_custom_directories():
    """Get custom directories from user input."""
    print("\nEnter custom directories to scan:")
    print("(Separate multiple directories with commas)")
    print("Example: C:/Movies, D:/Films, //192.168.1.100/media/movies")
    print()
    
    while True:
        directories = input("Directories: ").strip()
        if directories:
            return directories
        print("Please enter at least one directory.")


def view_recent_reports():
    """View and manage recent reports."""
    try:
        reports_dir = Path("reports")
        if not reports_dir.exists():
            print("No reports directory found. Run a scan first to generate reports.")
            return
        
        # Get all report files
        inventory_reports = sorted(reports_dir.glob("movie_inventory_*.txt"), reverse=True)
        duplicate_reports = sorted(reports_dir.glob("duplicates_*.txt"), reverse=True)
        
        if not inventory_reports and not duplicate_reports:
            print("No reports found. Run a scan first to generate reports.")
            return
        
        print("\n📄 Recent Reports:")
        print("-" * 50)
        
        print("\n🎬 Movie Inventory Reports:")
        for i, report in enumerate(inventory_reports[:5], 1):
            # Extract timestamp from filename
            timestamp = report.stem.split('_', 2)[-1]
            formatted_time = f"{timestamp[:8]} {timestamp[9:11]}:{timestamp[11:13]}:{timestamp[13:15]}"
            file_size = report.stat().st_size
            print(f"  {i}. {formatted_time} ({file_size:,} bytes)")
        
        print("\n🔍 Duplicate Reports:")
        for i, report in enumerate(duplicate_reports[:5], 1):
            timestamp = report.stem.split('_', 1)[-1]
            formatted_time = f"{timestamp[:8]} {timestamp[9:11]}:{timestamp[11:13]}:{timestamp[13:15]}"
            file_size = report.stat().st_size
            print(f"  {i}. {formatted_time} ({file_size:,} bytes)")
        
        print(f"\n📁 Reports location: {reports_dir.absolute()}")
        print("\nYou can open these files with any text editor to view detailed results.")
        
    except Exception as e:
        print(f"Error viewing reports: {e}")


def run_scanner(use_static=True, custom_dirs=None, verbose=True, delete_mode=False, mode="movie", tv_demo=False, tv_folder_only=False):
    """Run the Plex media manager with specified options."""
    try:
        # Build command
        cmd = [sys.executable, "-m", "file_managers.plex.cli.movie_duplicates"]
        
        if verbose:
            cmd.append("--verbose")
        
        # Mode-specific arguments
        if mode == "tv":
            cmd.append("--tv")
            if tv_demo:
                cmd.append("--demo")
            elif tv_folder_only:
                cmd.append("--folder-analysis-only")
        elif mode == "movie" and delete_mode:
            cmd.append("--delete")
        
        if not use_static and custom_dirs:
            cmd.extend(["--custom", custom_dirs])
        
        # Determine mode text for display
        if mode == "tv":
            if tv_demo:
                mode_text = "TV DEMO MODE"
            elif tv_folder_only:
                mode_text = "TV FOLDER ANALYSIS"
            else:
                mode_text = "TV ORGANIZATION ANALYSIS"
        else:
            mode_text = "MOVIE DELETION MODE" if delete_mode else "MOVIE ANALYSIS MODE"
        
        print(f"\nRunning {mode_text}")
        print(f"Command: {' '.join(cmd)}")
        print("=" * 60)
        
        # Run the command
        result = subprocess.run(cmd, capture_output=False, text=True)
        
        print("\n" + "=" * 60)
        if result.returncode == 0:
            print("✅ Operation completed successfully!")
        else:
            print("❌ Operation completed with errors.")
        
    except FileNotFoundError:
        print("Error: Could not find the Plex media manager module.")
        print("Make sure you're running this from the correct directory")
        print("and the package is installed: pip install -e .")
    except Exception as e:
        print(f"Error running operation: {e}")


def wait_for_user():
    """Wait for user to press Enter."""
    input("\nPress Enter to continue...")


def main():
    """Main interactive loop."""
    while True:
        clear_screen()
        print_banner()
        
        # Show current directory for context
        print(f"Current directory: {os.getcwd()}")
        print()
        
        print_menu()
        choice = get_user_choice()
        
        if choice == 1:
            # Movie: Scan predefined directories
            clear_screen()
            print_banner()
            print("🎬 Scanning movies for duplicates...")
            print()
            run_scanner(use_static=True, mode="movie")
            wait_for_user()
            
        elif choice == 2:
            # Movie: Scan custom directories
            clear_screen()
            print_banner()
            custom_dirs = get_custom_directories()
            clear_screen()
            print_banner()
            print(f"🎬 Scanning custom movie directories: {custom_dirs}")
            print()
            run_scanner(use_static=False, custom_dirs=custom_dirs, mode="movie")
            wait_for_user()
            
        elif choice == 3:
            # Movie: DELETE duplicates mode
            clear_screen()
            print_banner()
            print("🗑️  MOVIE DELETION MODE - WARNING!")
            print("=" * 60)
            print("⚠️  You are about to enter DELETION MODE!")
            print("⚠️  This will permanently delete duplicate movie files!")
            print("⚠️  This action CANNOT be undone!")
            print("=" * 60)
            print()
            
            confirm = input("Type 'DELETE MODE' to continue: ").strip()
            if confirm == "DELETE MODE":
                print("🗑️  Starting deletion mode...")
                run_scanner(use_static=True, verbose=True, delete_mode=True, mode="movie")
            else:
                print("🚫 Deletion mode cancelled")
            wait_for_user()
            
        elif choice == 4:
            # TV: Analyze organization
            clear_screen()
            print_banner()
            print("📺 Analyzing TV show organization...")
            print()
            run_scanner(use_static=True, mode="tv")
            wait_for_user()
            
        elif choice == 5:
            # TV: Demo mode
            clear_screen()
            print_banner()
            print("📺 TV SHOW DEMO MODE")
            print("=" * 60)
            print("This will show what would be moved during organization")
            print("NO FILES WILL ACTUALLY BE MOVED")
            print("=" * 60)
            print()
            run_scanner(use_static=True, mode="tv", tv_demo=True)
            wait_for_user()
            
        elif choice == 6:
            # TV: Folder analysis only
            clear_screen()
            print_banner()
            print("📺 Analyzing existing TV folder structure...")
            print()
            run_scanner(use_static=True, mode="tv", tv_folder_only=True)
            wait_for_user()
            
        elif choice == 7:
            # View configured directories
            clear_screen()
            print_banner()
            show_configured_directories()
            wait_for_user()
            
        elif choice == 8:
            # View recent reports
            clear_screen()
            print_banner()
            view_recent_reports()
            wait_for_user()
            
        elif choice == 9:
            # Exit
            clear_screen()
            print("👋 Thank you for using Plex Media Manager!")
            print("💾 Analysis reports are saved in the 'reports' folder")
            print("🎬 Movie duplicates: Use deletion mode carefully!")
            print("📺 TV organization: Use demo mode to preview changes!")
            break


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
        sys.exit(0)