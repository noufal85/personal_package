"""CLI tool for managing the media database cache."""

import argparse
import sys
from pathlib import Path

try:
    from ..utils.media_database import MediaDatabase
except ImportError:
    # Allow running as script
    sys.path.append(str(Path(__file__).parent.parent.parent))
    from plex.utils.media_database import MediaDatabase

def format_size(size_bytes: int) -> str:
    """Format file size in human-readable format."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} PB"

def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Manage the media database cache for faster searches",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --rebuild        # Rebuild the entire database
  %(prog)s --status         # Show database status
  %(prog)s --clean          # Remove database file
  %(prog)s --stats          # Show detailed statistics
        """
    )
    
    parser.add_argument(
        '--rebuild',
        action='store_true',
        help='Rebuild the entire media database'
    )
    
    parser.add_argument(
        '--status',
        action='store_true',
        help='Show database status and basic statistics'
    )
    
    parser.add_argument(
        '--stats',
        action='store_true',
        help='Show detailed database statistics'
    )
    
    parser.add_argument(
        '--clean',
        action='store_true',
        help='Remove the database file'
    )
    
    parser.add_argument(
        '--path',
        help='Custom path for database file'
    )
    
    args = parser.parse_args()
    
    if not any([args.rebuild, args.status, args.stats, args.clean]):
        parser.print_help()
        return
    
    # Initialize database
    database = MediaDatabase(args.path)
    
    if args.clean:
        if database.db_path.exists():
            database.db_path.unlink()
            print(f"✅ Database file removed: {database.db_path}")
        else:
            print("ℹ️  Database file does not exist")
        return
    
    if args.rebuild:
        print("🔄 Rebuilding media database...")
        print("   This may take a few minutes for large collections...")
        print()
        
        try:
            stats = database.rebuild_database()
            
            print("✅ Database rebuilt successfully!")
            print()
            print("📊 DATABASE STATISTICS:")
            print(f"   Movies: {stats.movies_count:,}")
            print(f"   TV Shows: {stats.tv_shows_count:,}")
            print(f"   TV Episodes: {stats.tv_episodes_count:,}")
            print(f"   Total Files: {stats.total_files:,}")
            print(f"   Total Size: {format_size(stats.total_size_bytes)}")
            print(f"   Build Time: {stats.build_time_seconds:.1f} seconds")
            print(f"   Database File: {database.db_path}")
            print()
            print("📁 DIRECTORIES SCANNED:")
            for directory in stats.directories_scanned:
                print(f"   • {directory}")
                
        except Exception as e:
            print(f"❌ Failed to rebuild database: {e}")
            sys.exit(1)
    
    elif args.status or args.stats:
        if not database.db_path.exists():
            print("❌ Database file does not exist. Run --rebuild to create it.")
            return
        
        stats = database.get_stats()
        
        if not stats.last_updated:
            print("⚠️  Database appears to be empty or corrupted. Run --rebuild.")
            return
        
        # Basic status
        print("📊 MEDIA DATABASE STATUS")
        print("=" * 40)
        print(f"Database File: {database.db_path}")
        print(f"Last Updated: {stats.last_updated}")
        print(f"Is Current: {'✅ Yes' if database.is_current() else '⚠️  No (outdated)'}")
        print()
        
        print("📈 COLLECTION SUMMARY:")
        print(f"   Movies: {stats.movies_count:,}")
        print(f"   TV Shows: {stats.tv_shows_count:,}")
        print(f"   TV Episodes: {stats.tv_episodes_count:,}")
        print(f"   Total Files: {stats.total_files:,}")
        print(f"   Total Size: {format_size(stats.total_size_bytes)}")
        
        if args.stats:
            print()
            print("⚙️  BUILD DETAILS:")
            print(f"   Build Time: {stats.build_time_seconds:.1f} seconds")
            print(f"   Directories Scanned: {len(stats.directories_scanned)}")
            print()
            
            print("📁 SCANNED DIRECTORIES:")
            for directory in stats.directories_scanned:
                exists = "✅" if Path(directory).exists() else "❌"
                print(f"   {exists} {directory}")
            
            # File size information
            db_size = database.db_path.stat().st_size if database.db_path.exists() else 0
            print()
            print("💾 DATABASE FILE:")
            print(f"   Size: {format_size(db_size)}")
            print(f"   Path: {database.db_path}")
            
            if not database.is_current():
                print()
                print("⚠️  RECOMMENDATION:")
                print("   Database is outdated. Run --rebuild to refresh with latest files.")

if __name__ == '__main__':
    main()