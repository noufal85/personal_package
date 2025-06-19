"""Command Line Interface for Media Auto-Organizer

This module provides a comprehensive CLI for the media auto-organizer with all
the options and features needed for interactive and automated use.

Features:
- Dry run and execution modes
- AI and rule-based classification options
- Database statistics and management
- Mount verification
- Comprehensive help and examples
"""

import argparse

from ..config.config import config
from .organizer import AutoOrganizer


def main() -> None:
    """Main entry point for the media auto-organizer CLI."""
    parser = argparse.ArgumentParser(
        description="Automatically organize downloaded media files using AI classification and intelligent placement",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
DIRECTORY CONFIGURATION:
  Downloads: {config.downloads_directory}

  Target Directories:
    Movies:        {config.movie_directories}
    TV Shows:      {config.tv_directories}  
    Documentaries: {config.documentary_directories}
    Stand-ups:     {config.standup_directories}

FEATURES:
  • Intelligent TV episode placement using existing show locations
  • Smart fallback across multiple QNAP directories
  • AI-powered classification with rule-based fallback
  • Directory access validation and space management
  • Comprehensive reporting and error handling

EXAMPLES:
  # Dry run (preview mode - default)
  python -m file_managers.plex.media_autoorganizer.cli
  
  # Actually organize files
  python -m file_managers.plex.media_autoorganizer.cli --execute
  
  # Use rule-based classification only (faster, no AI throttling)
  python -m file_managers.plex.media_autoorganizer.cli --no-ai
  
  # Show database statistics
  python -m file_managers.plex.media_autoorganizer.cli --db-stats
  
  # Verify mount access only
  python -m file_managers.plex.media_autoorganizer.cli --verify-mounts

WORKFLOW:
  1. Scans downloads directory for media files
  2. Classifies files using cached, rule-based, and AI methods
  3. For TV episodes: finds existing show locations or creates new show directories
  4. For movies: places in available movie directories with space/access validation
  5. Generates detailed reports with move results and show information
        """
    )
    
    # Main operation modes
    parser.add_argument(
        "--execute",
        action="store_true", 
        help="Actually move files (default: dry run mode)"
    )
    
    parser.add_argument(
        "--verify-mounts",
        action="store_true",
        help="Only verify mount access and exit (no file processing)"
    )
    
    # Classification options
    parser.add_argument(
        "--no-ai",
        action="store_true",
        help="Disable AI classification, use rule-based only (avoids throttling and API costs)"
    )
    
    # Database management
    parser.add_argument(
        "--db-stats",
        action="store_true",
        help="Show classification database statistics and exit"
    )
    
    parser.add_argument(
        "--clear-db",
        action="store_true",
        help="Clear all cached classifications from database (requires confirmation)"
    )
    
    # Output options
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output with detailed processing information"
    )
    
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Minimize output (only show critical information and results)"
    )
    
    args = parser.parse_args()
    
    # Handle conflicting options
    if args.verbose and args.quiet:
        print("❌ Error: --verbose and --quiet cannot be used together")
        return
    
    try:
        organizer = AutoOrganizer(dry_run=not args.execute, use_ai=not args.no_ai)
        
        # Handle database operations
        if args.db_stats:
            show_database_stats(organizer)
            return
        
        if args.clear_db:
            clear_database(organizer)
            return
        
        # Handle mount verification only
        if args.verify_mounts:
            if organizer.verify_mount_access():
                print("✅ All mount points are accessible")
            else:
                print("❌ Some mount points are not accessible")
            return
        
        # Verify mount access before proceeding with organization
        if not organizer.verify_mount_access():
            print("\n🚫 Organization cancelled due to mount access issues")
            print("💡 Use --verify-mounts to check mount status")
            return
        
        # Show execution warning for non-dry-run mode
        if args.execute:
            print("\n⚠️  WARNING: Files will be moved to Plex directories!")
            print("⚠️  Make sure you have backups before proceeding!")
            confirm = input("\nType 'ORGANIZE' to proceed: ").strip()
            if confirm != "ORGANIZE":
                print("🚫 Organization cancelled")
                return
        
        # Run the full organization workflow
        report_path = organizer.run_full_organization()
        
        if report_path:
            print(f"\n📄 Detailed report saved to: {report_path}")
            
            if not args.quiet:
                print("\n💡 TIP: Review the report for detailed information about each file move")
                if args.execute:
                    print("💡 TIP: If any moves failed, check mount access and available space")
                else:
                    print("💡 TIP: Run with --execute to actually move the files")
        
    except KeyboardInterrupt:
        print("\n👋 Organization cancelled by user")
    except Exception as e:
        print(f"❌ Error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()


def show_database_stats(organizer: AutoOrganizer) -> None:
    """Show classification database statistics."""
    stats = organizer.classification_db.get_stats()
    print("📊 CLASSIFICATION DATABASE STATISTICS")
    print("=" * 50)
    print(f"Database Location: {organizer.classification_db.db_path}")
    print(f"Total Classifications: {stats['total']}")
    
    if stats['by_type']:
        print("\nBy Media Type:")
        for media_type, count in sorted(stats['by_type'].items()):
            print(f"  {media_type:12}: {count:,}")
    
    if stats['by_source']:
        print("\nBy Classification Source:")
        for source, count in sorted(stats['by_source'].items()):
            print(f"  {source:15}: {count:,}")
    
    print(f"\nMedia Database: {len(organizer.media_db.tv_shows):,} TV shows loaded")
    if organizer.media_db.failed_directories:
        print(f"Failed Directories: {len(organizer.media_db.failed_directories)}")
        for failed_dir in sorted(organizer.media_db.failed_directories):
            print(f"  ❌ {failed_dir}")


def clear_database(organizer: AutoOrganizer) -> None:
    """Clear the classification database with confirmation."""
    stats = organizer.classification_db.get_stats()
    total = stats['total']
    
    if total == 0:
        print("📊 Classification database is already empty")
        return
    
    print(f"⚠️  WARNING: This will delete {total:,} cached classifications!")
    print("⚠️  This will cause files to be re-classified on next run")
    confirm = input("\nType 'CLEAR' to proceed: ").strip()
    
    if confirm == "CLEAR":
        organizer.classification_db.clear_database()
        print(f"✅ Cleared {total:,} classifications from database")
    else:
        print("🚫 Database clear cancelled")


if __name__ == "__main__":
    main()