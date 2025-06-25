#!/usr/bin/env python3
"""
Plex CLI - Unified command-line interface for all personal package features.

This is the main entry point for the plex-cli command that centralizes
all file management, media organization, and Plex utilities.
"""

import argparse
import sys
from pathlib import Path
from typing import List, Optional
from datetime import datetime

# Import utilities
from ..plex.config.config import MediaConfig

# Version info
__version__ = "1.0.0"


class PlexCLI:
    """Main CLI coordinator class."""
    
    def __init__(self):
        """Initialize the CLI with configuration."""
        self.config = MediaConfig()
        self.parser = self._create_parser()
    
    def _create_parser(self) -> argparse.ArgumentParser:
        """Create the main argument parser with subcommands."""
        parser = argparse.ArgumentParser(
            prog='plex-cli',
            description='Unified CLI for Plex media management and file organization',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog=self._get_help_epilog()
        )
        
        parser.add_argument(
            '--version',
            action='version',
            version=f'%(prog)s {__version__}'
        )
        
        parser.add_argument(
            '-v', '--verbose',
            action='store_true',
            help='Enable verbose output'
        )
        
        parser.add_argument(
            '-i', '--interactive',
            action='store_true',
            help='Start interactive mode with menu selection'
        )
        
        # Create subparsers for main command groups
        subparsers = parser.add_subparsers(
            dest='command_group',
            title='Command Groups',
            description='Available command groups',
            help='Use --help with any command group for detailed help'
        )
        
        # Files command group
        self._add_files_commands(subparsers)
        
        # Movies command group (placeholder for Phase 2)
        self._add_movies_commands(subparsers)
        
        # TV command group (placeholder for Phase 2)
        self._add_tv_commands(subparsers)
        
        # Media command group (placeholder for Phase 2)
        self._add_media_commands(subparsers)
        
        # Config command group
        self._add_config_commands(subparsers)
        
        return parser
    
    def _add_files_commands(self, subparsers) -> None:
        """Add files command group."""
        files_parser = subparsers.add_parser(
            'files',
            help='General file operations',
            description='File management utilities'
        )
        
        files_subparsers = files_parser.add_subparsers(
            dest='files_command',
            title='Files Commands',
            help='Available file operations'
        )
        
        
        # files duplicates command
        duplicates_parser = files_subparsers.add_parser(
            'duplicates',
            help='Find duplicate movies and TV episodes',
            description='Database-based duplicate detection for movies and TV shows'
        )
        duplicates_parser.add_argument(
            '--type',
            choices=['movies', 'tv', 'all'],
            default='all',
            help='Search for duplicates in movies, TV shows, or both'
        )
        duplicates_parser.add_argument(
            '--rebuild-db',
            action='store_true',
            help='Force database rebuild before searching'
        )
        
        # files database command
        database_parser = files_subparsers.add_parser(
            'database',
            help='Database management operations',
            description='Manage the media database'
        )
        database_parser.add_argument(
            '--rebuild',
            action='store_true',
            help='Rebuild the entire database'
        )
        database_parser.add_argument(
            '--status',
            action='store_true',
            help='Show database status and statistics'
        )
        
        # files organize command
        organize_parser = files_subparsers.add_parser(
            'organize',
            help='Auto-organize downloaded files',
            description='Automatically organize downloaded media files using AI classification and intelligent placement'
        )
        organize_parser.add_argument(
            '--dry-run',
            action='store_true',
            default=True,
            help='Show what would be done without making changes (default mode)'
        )
        organize_parser.add_argument(
            '--execute',
            action='store_true',
            help='Actually move files (overrides --dry-run)'
        )
        organize_parser.add_argument(
            '--no-ai',
            action='store_true',
            help='Disable AI classification, use rule-based only'
        )
        organize_parser.add_argument(
            '--verify-mounts',
            action='store_true',
            help='Only verify mount access and exit'
        )
        
        # files reorganize command (MVP)
        reorganize_parser = files_subparsers.add_parser(
            'reorganize',
            help='Analyze misplaced media files (MVP)',
            description='Identify files in wrong directories using rule-based analysis'
        )
        reorganize_parser.add_argument(
            '--confidence',
            type=float,
            default=0.7,
            help='Minimum confidence threshold (0.0-1.0, default: 0.7)'
        )
        reorganize_parser.add_argument(
            '--format',
            choices=['text', 'json', 'both'],
            default='both',
            help='Report output format (default: both)'
        )
        reorganize_parser.add_argument(
            '--ai',
            action='store_true',
            help='Enable AI classification (can detect documentaries and edge cases)'
        )
        reorganize_parser.add_argument(
            '--rebuild-db',
            action='store_true',
            help='Force database rebuild before analysis'
        )
        reorganize_parser.add_argument(
            '--no-external-apis',
            action='store_true',
            help='Disable external API usage (TMDB/TVDB)'
        )
        
        # files move command
        move_parser = files_subparsers.add_parser(
            'move',
            help='Interactive file moving with caching support',
            description='Move misplaced files with decision caching and batch execution'
        )
        move_parser.add_argument(
            'report',
            nargs='?',
            help='Path to reorganization JSON report file (from files reorganize command)'
        )
        move_parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Preview moves without actually moving files'
        )
        move_parser.add_argument(
            '--execute-cache',
            help='Execute moves from a cached decisions file'
        )
        move_parser.add_argument(
            '--list-cache',
            action='store_true',
            help='List available cached decision files'
        )
    
    def _add_movies_commands(self, subparsers) -> None:
        """Add movies command group."""
        movies_parser = subparsers.add_parser(
            'movies',
            help='Movie management',
            description='Movie collection management tools'
        )
        
        movies_subparsers = movies_parser.add_subparsers(
            dest='movies_command',
            title='Movies Commands',
            help='Available movie operations'
        )
        
        # movies duplicates command
        duplicates_parser = movies_subparsers.add_parser(
            'duplicates',
            help='Find and manage duplicate movies',
            description='Find duplicate movies in your collection'
        )
        duplicates_parser.add_argument(
            '--delete',
            action='store_true',
            help='Interactive deletion mode'
        )
        duplicates_parser.add_argument(
            '--rebuild-db',
            action='store_true',
            help='Force database rebuild before searching'
        )
        
        # movies search command
        search_parser = movies_subparsers.add_parser(
            'search',
            help='Search movie collection',
            description='Search for movies in your collection'
        )
        search_parser.add_argument(
            'query',
            help='Movie title to search for'
        )
        
        # movies reports command
        movies_subparsers.add_parser('reports', help='Generate comprehensive movie collection reports')
        
        # movies ratings command
        ratings_parser = movies_subparsers.add_parser(
            'ratings',
            help='Fetch and manage movie ratings from OMDB',
            description='Fetch ratings from OMDB API and manage movie quality database'
        )
        ratings_parser.add_argument(
            '--fetch',
            action='store_true',
            help='Fetch ratings for all movies from OMDB API'
        )
        ratings_parser.add_argument(
            '--stats',
            action='store_true',
            help='Show rating database statistics'
        )
        ratings_parser.add_argument(
            '--bad-movies',
            action='store_true',
            help='List badly rated movies based on thresholds'
        )
        ratings_parser.add_argument(
            '--delete-bad',
            action='store_true',
            help='Delete badly rated movies (requires confirmation)'
        )
        ratings_parser.add_argument(
            '--imdb-threshold',
            type=float,
            default=5.0,
            help='IMDB rating threshold for bad movies (default: 5.0)'
        )
        ratings_parser.add_argument(
            '--rt-threshold',
            type=int,
            default=30,
            help='Rotten Tomatoes threshold for bad movies (default: 30%%)'
        )
        ratings_parser.add_argument(
            '--meta-threshold',
            type=int,
            default=40,
            help='Metacritic threshold for bad movies (default: 40)'
        )
    
    def _add_tv_commands(self, subparsers) -> None:
        """Add TV command group."""
        tv_parser = subparsers.add_parser(
            'tv',
            help='TV show management',
            description='TV show collection management tools'
        )
        
        tv_subparsers = tv_parser.add_subparsers(
            dest='tv_command',
            title='TV Commands',
            help='Available TV operations'
        )
        
        # tv organize command
        organize_parser = tv_subparsers.add_parser(
            'organize',
            help='Organize TV episodes',
            description='Organize unorganized TV episodes'
        )
        organize_parser.add_argument(
            '--custom',
            help='Comma-separated list of custom TV directories'
        )
        organize_parser.add_argument(
            '--demo',
            action='store_true',
            help='Show what would be moved without moving files'
        )
        organize_parser.add_argument(
            '--execute',
            action='store_true',
            help='Actually move files (requires confirmation)'
        )
        organize_parser.add_argument(
            '--no-reports',
            action='store_true',
            help='Skip generating report files'
        )
        
        # tv search command
        search_parser = tv_subparsers.add_parser(
            'search',
            help='Search TV collection',
            description='Search for TV shows in your collection'
        )
        search_parser.add_argument(
            'query',
            help='TV show title to search for'
        )
        
        # tv missing command
        missing_parser = tv_subparsers.add_parser(
            'missing',
            help='Find missing episodes',
            description='Find missing episodes for TV shows'
        )
        missing_parser.add_argument(
            'show',
            help='TV show title to analyze'
        )
        missing_parser.add_argument(
            '--season',
            type=int,
            help='Focus on specific season'
        )
        
        # tv reports command
        tv_subparsers.add_parser('reports', help='Generate comprehensive TV collection reports')
    
    def _add_media_commands(self, subparsers) -> None:
        """Add media command group."""
        media_parser = subparsers.add_parser(
            'media',
            help='Cross-media operations',
            description='Operations across movie and TV collections'
        )
        
        media_subparsers = media_parser.add_subparsers(
            dest='media_command',
            title='Media Commands',
            help='Available media operations'
        )
        
        # media assistant command
        assistant_parser = media_subparsers.add_parser(
            'assistant',
            help='AI-powered media search',
            description='Natural language media search and analysis'
        )
        assistant_parser.add_argument(
            'query',
            nargs='?',
            help='Natural language query about your media collection'
        )
        assistant_parser.add_argument(
            '--interactive',
            action='store_true',
            help='Start interactive mode'
        )
        assistant_parser.add_argument(
            '--rebuild-db',
            action='store_true',
            help='Rebuild media database before starting'
        )
        
        # media database command
        database_parser = media_subparsers.add_parser(
            'database',
            help='Database operations',
            description='Manage the media database'
        )
        database_parser.add_argument(
            '--rebuild',
            action='store_true',
            help='Rebuild the entire database'
        )
        database_parser.add_argument(
            '--status',
            action='store_true',
            help='Show database status and statistics'
        )
        database_parser.add_argument(
            '--clean',
            action='store_true',
            help='Remove database file'
        )
        
        # media status command
        media_subparsers.add_parser('status', help='System status and mount point verification')
        
        # media enrich command
        enrich_parser = media_subparsers.add_parser(
            'enrich',
            help='Enrich metadata using external APIs',
            description='Query TMDB/TVDB APIs to enrich media metadata and improve classification accuracy'
        )
        enrich_parser.add_argument(
            '--limit',
            type=int,
            help='Limit number of items to process'
        )
        enrich_parser.add_argument(
            '--force',
            action='store_true',
            help='Force re-enrichment of cached items'
        )
        enrich_parser.add_argument(
            '--stats',
            action='store_true',
            help='Show metadata cache statistics'
        )
        enrich_parser.add_argument(
            '--test',
            type=str,
            help='Test enrichment for a specific title'
        )
    
    def _add_config_commands(self, subparsers) -> None:
        """Add config command group."""
        config_parser = subparsers.add_parser(
            'config',
            help='Configuration management',
            description='Manage plex-cli configuration'
        )
        
        config_subparsers = config_parser.add_subparsers(
            dest='config_command',
            title='Config Commands',
            help='Available configuration operations'
        )
        
        # config show command
        show_parser = config_subparsers.add_parser(
            'show',
            help='Show current configuration',
            description='Display current configuration settings'
        )
        show_parser.add_argument(
            '--section',
            choices=['movies', 'tv', 'nas', 'settings', 'all'],
            default='all',
            help='Show specific configuration section'
        )
        
        # config paths command
        paths_parser = config_subparsers.add_parser(
            'paths',
            help='Show configured paths',
            description='Display configured directory paths'
        )
        paths_parser.add_argument(
            '--type',
            choices=['movies', 'tv', 'downloads', 'all'],
            default='all',
            help='Show paths for specific media type'
        )
        
        # config apis command
        apis_parser = config_subparsers.add_parser(
            'apis',
            help='API configuration management',
            description='Manage external API configurations (TMDB, TVDB, AWS)'
        )
        apis_parser.add_argument(
            '--check',
            action='store_true',
            help='Check API key status and connectivity'
        )
        apis_parser.add_argument(
            '--show',
            action='store_true',
            help='Show configured API keys (masked for security)'
        )
    
    def _get_help_epilog(self) -> str:
        """Get help epilog with examples."""
        return """
Examples:
  plex-cli --interactive                   # Start interactive mode
  plex-cli files duplicates --type movies  # Find movie duplicates
  plex-cli files database --status        # Show database status
  plex-cli files organize                 # Auto-organize downloads (dry-run)
  plex-cli files organize --execute       # Actually organize files
  plex-cli config show                     # Show configuration
  plex-cli config paths                    # Show configured paths
  
  # Media management:
  plex-cli movies duplicates               # Find duplicate movies
  plex-cli movies search "The Batman"       # Search movie collection
  plex-cli movies reports                  # Generate movie reports
  plex-cli tv organize                     # Organize TV episodes
  plex-cli tv search "Breaking Bad"         # Search TV shows
  plex-cli tv missing "Game of Thrones"    # Find missing episodes
  plex-cli tv reports                      # Generate TV reports
  plex-cli media assistant "Do I have Inception?"  # AI-powered search
  plex-cli media database --rebuild        # Rebuild media database
  plex-cli media status                    # Check system status

For detailed help on any command group:
  plex-cli files --help
  plex-cli config --help
  
Version: """ + __version__
    
    def run(self, args: Optional[List[str]] = None) -> int:
        """
        Run the CLI with given arguments.
        
        Args:
            args: Command line arguments (uses sys.argv if None)
            
        Returns:
            Exit code (0 for success, non-zero for error)
        """
        try:
            parsed_args = self.parser.parse_args(args)
            
            # Handle interactive mode (explicit flag or no arguments)
            if parsed_args.interactive or not parsed_args.command_group:
                return self._run_interactive_mode(parsed_args)
            
            # Route to appropriate handler
            if parsed_args.command_group == 'files':
                return self._handle_files_command(parsed_args)
            elif parsed_args.command_group == 'config':
                return self._handle_config_command(parsed_args)
            elif parsed_args.command_group == 'movies':
                return self._handle_movies_command(parsed_args)
            elif parsed_args.command_group == 'tv':
                return self._handle_tv_command(parsed_args)
            elif parsed_args.command_group == 'media':
                return self._handle_media_command(parsed_args)
            else:
                print(f"Unknown command group: {parsed_args.command_group}", file=sys.stderr)
                return 1
                
        except KeyboardInterrupt:
            print("\nOperation cancelled by user.", file=sys.stderr)
            return 1
        except Exception as e:
            if parsed_args.verbose if 'parsed_args' in locals() else False:
                import traceback
                traceback.print_exc()
            else:
                print(f"Error: {e}", file=sys.stderr)
            return 1
    
    def _handle_files_command(self, args) -> int:
        """Handle files command group."""
        if not args.files_command:
            self.parser.parse_args([args.command_group, '--help'])
            return 0
        
        if args.files_command == 'duplicates':
            return self._handle_files_duplicates(args)
        elif args.files_command == 'database':
            return self._handle_files_database(args)
        elif args.files_command == 'organize':
            return self._handle_files_organize(args)
        elif args.files_command == 'reorganize':
            return self._handle_files_reorganize(args)
        elif args.files_command == 'move':
            return self._handle_files_move(args)
        else:
            print(f"Unknown files command: {args.files_command}", file=sys.stderr)
            return 1
    
    
    def _handle_files_duplicates(self, args) -> int:
        """Handle files duplicates command."""
        try:
            from ..plex.utils.media_database import MediaDatabase
            from ..plex.utils.duplicate_detector import DuplicateDetector
            
            print(f"🔍 Searching for duplicates in: {args.type}")
            print()
            
            # Initialize database
            db = MediaDatabase()
            
            # Check database age and ask for rebuild if needed
            if not args.rebuild_db:
                if not db.is_current():
                    print("⚠️  Database is outdated or doesn't exist")
                    rebuild = input("Would you like to rebuild the database? (y/n): ").strip().lower()
                    if rebuild == 'y':
                        args.rebuild_db = True
                else:
                    stats = db.get_stats()
                    last_updated = datetime.fromisoformat(stats.last_updated)
                    hours_ago = (datetime.now() - last_updated).total_seconds() / 3600
                    print(f"📊 Database last updated {hours_ago:.1f} hours ago")
                    
                    # Always ask but include the age information
                    rebuild = input(f"Rebuild database before searching? (y/n): ").strip().lower()
                    if rebuild == 'y':
                        args.rebuild_db = True
            
            # Rebuild database if requested
            if args.rebuild_db:
                print("🔄 Rebuilding database...")
                stats = db.rebuild_database()
                print(f"✅ Database rebuilt: {stats.movies_count} movies, {stats.tv_episodes_count} TV episodes")
                print()
            
            # Initialize duplicate detector
            detector = DuplicateDetector(db)
            
            # Search for duplicates
            if args.type in ['movies', 'all']:
                print("🎬 Searching for movie duplicates...")
                movie_duplicates = detector.find_movie_duplicates()
                self._display_movie_duplicates(movie_duplicates)
                print()
            
            if args.type in ['tv', 'all']:
                print("📺 Searching for TV episode duplicates...")
                tv_duplicates = detector.find_tv_duplicates()
                self._display_tv_duplicates(tv_duplicates)
                print()
            
            return 0
            
        except ImportError as e:
            print(f"❌ Missing required module: {e}")
            print("   The duplicate detector needs to be implemented.")
            return 1
        except Exception as e:
            print(f"❌ Error searching for duplicates: {e}")
            return 1
    
    def _handle_files_database(self, args) -> int:
        """Handle files database command."""
        try:
            from ..plex.utils.media_database import MediaDatabase
            
            db = MediaDatabase()
            
            if args.rebuild:
                print("🔄 Rebuilding media database...")
                stats = db.rebuild_database()
                print(f"✅ Database rebuilt successfully!")
                print(f"   📊 Movies: {stats.movies_count}")
                print(f"   📺 TV Shows: {stats.tv_shows_count}")
                print(f"   🎬 Episodes: {stats.tv_episodes_count}")
                print(f"   ⏱️  Build time: {stats.build_time_seconds:.1f}s")
                print(f"   💾 Total size: {stats.total_size_bytes / (1024**3):.1f} GB")
                
            elif args.status:
                if db.is_current():
                    stats = db.get_stats()
                    last_updated = datetime.fromisoformat(stats.last_updated)
                    hours_ago = (datetime.now() - last_updated).total_seconds() / 3600
                    
                    print("📊 Database Status")
                    print("=" * 20)
                    print(f"Status: ✅ Current")
                    print(f"Last updated: {hours_ago:.1f} hours ago")
                    print(f"Movies: {stats.movies_count}")
                    print(f"TV Shows: {stats.tv_shows_count}")
                    print(f"TV Episodes: {stats.tv_episodes_count}")
                    print(f"Total files: {stats.total_files}")
                    print(f"Total size: {stats.total_size_bytes / (1024**3):.1f} GB")
                    print(f"Build time: {stats.build_time_seconds:.1f}s")
                else:
                    print("📊 Database Status")
                    print("=" * 20)
                    print("Status: ❌ Outdated or missing")
                    print("Run 'plex-cli files database --rebuild' to update")
            else:
                # Show help if no specific action
                self.parser.parse_args(['files', 'database', '--help'])
            
            return 0
            
        except Exception as e:
            print(f"❌ Error with database operation: {e}")
            return 1
    
    def _handle_files_organize(self, args) -> int:
        """Handle files organize command."""
        try:
            from ..plex.media_autoorganizer.organizer import AutoOrganizer
            
            # Determine dry run mode: --execute overrides default --dry-run
            is_dry_run = not getattr(args, 'execute', False)
            
            # Initialize organizer
            organizer = AutoOrganizer(dry_run=is_dry_run, use_ai=not getattr(args, 'no_ai', False))
            
            # Handle verify mounts only
            if getattr(args, 'verify_mounts', False):
                print("🔍 Verifying mount access...")
                if organizer.verify_mount_access():
                    print("✅ All mount points are accessible")
                    return 0
                else:
                    print("❌ Some mount points are not accessible")
                    return 1
            
            # Show mode information
            mode = "DRY RUN" if is_dry_run else "EXECUTION"
            ai_mode = "Rule-based only" if getattr(args, 'no_ai', False) else "AI + Rule-based"
            
            print(f"🗂️  Auto-Organizer - {mode} Mode")
            print(f"   Classification: {ai_mode}")
            print()
            
            # Verify mount access before proceeding
            if not organizer.verify_mount_access():
                print("\n🚫 Organization cancelled due to mount access issues")
                print("💡 Use 'plex-cli files organize --verify-mounts' to check mount status")
                return 1
            
            # Show execution warning for non-dry-run mode
            if not is_dry_run:
                print("\n⚠️  WARNING: Files will be moved to Plex directories!")
                print("⚠️  Make sure you have backups before proceeding!")
                confirm = input("\nType 'ORGANIZE' to proceed: ").strip()
                if confirm != "ORGANIZE":
                    print("🚫 Organization cancelled")
                    return 0
            
            # Run the organization workflow
            print("🚀 Starting media organization workflow...")
            report_path = organizer.run_full_organization()
            
            if report_path:
                print(f"\n📄 Detailed report saved to: {report_path}")
                print("\n💡 TIP: Review the report for detailed information about each file move")
                if is_dry_run:
                    print("💡 TIP: Use --execute to actually move the files")
                else:
                    print("💡 TIP: If any moves failed, check mount access and available space")
            
            return 0
            
        except ImportError as e:
            print(f"❌ Auto-organizer not available: {e}")
            print("   Make sure the media_autoorganizer module is properly installed.")
            return 1
        except Exception as e:
            print(f"❌ Error during organization: {e}")
            return 1
    
    def _handle_files_reorganize(self, args) -> int:
        """Handle files reorganize command (MVP)."""
        try:
            from ..plex.utils.media_reorganizer import MediaReorganizationAnalyzer
            
            # Get parameters from args
            confidence = getattr(args, 'confidence', 0.7)
            output_format = getattr(args, 'format', 'both')
            rebuild_db = getattr(args, 'rebuild_db', False)
            
            print("🔍 Media Reorganization Analysis")
            print("=" * 35)
            print("• Process: TV/Movie Database Cache → AI LLM → Unclassified")
            print("• Analysis only - generates actionable reports for moves")
            print(f"• Output format: {output_format}")
            print()
            
            # Always use strict workflow (AI enabled by default)
            analyzer = MediaReorganizationAnalyzer(
                rebuild_db=rebuild_db,
                min_confidence=confidence,
                output_format=output_format,
                use_ai=True,  # Always enabled for strict workflow
                use_external_apis=True  # Always enabled for strict workflow
            )
            
            # Run analysis
            return analyzer.run_analysis(args)
            
        except ImportError as e:
            print(f"❌ Media reorganizer not available: {e}")
            print("   Make sure the media_reorganizer module is properly installed.")
            return 1
        except Exception as e:
            print(f"❌ Error during reorganization analysis: {e}")
            return 1
    
    def _handle_files_move(self, args) -> int:
        """Handle files move command for interactive file moving."""
        try:
            from ..plex.utils.media_mover import MediaMover
            from pathlib import Path
            
            # Handle cache listing
            if args.list_cache:
                return self._list_cached_decisions()
            
            # Initialize mover
            mover = MediaMover(dry_run=args.dry_run)
            
            # Handle cache execution
            if args.execute_cache:
                print("🚚 Media File Mover - Cache Execution")
                print("=" * 45)
                print("• Execute previously approved moves")
                print(f"• Cache file: {args.execute_cache}")
                print(f"• Mode: {'DRY RUN' if args.dry_run else 'LIVE MOVES'}")
                print()
                
                success = mover.execute_cached_moves(args.execute_cache)
                return 0 if success else 1
            
            # Handle interactive mode
            if not args.report:
                print("❌ No report file specified")
                print("   Use --help for usage information")
                return 1
            
            print("🚚 Interactive Media File Mover")
            print("=" * 35)
            print("• Decision phase: Approve moves for batch execution")
            print("• Caching: Approved moves saved for execution")
            print(f"• Report: {args.report}")
            print(f"• Mode: {'DRY RUN' if args.dry_run else 'LIVE MOVES'}")
            print()
            
            # Run interactive moves
            success = mover.run_interactive_moves(args.report)
            return 0 if success else 1
            
        except ImportError as e:
            print(f"❌ Media mover not available: {e}")
            print("   Make sure the media_mover module is properly installed.")
            return 1
        except Exception as e:
            print(f"❌ Error during move operation: {e}")
            return 1
    
    def _list_cached_decisions(self) -> int:
        """List available cached decision files."""
        try:
            from pathlib import Path
            import json
            from datetime import datetime
            
            cache_dir = Path("cache")
            if not cache_dir.exists():
                print("❌ No cache directory found")
                return 1
            
            cache_files = list(cache_dir.glob("move_decisions_*.json"))
            if not cache_files:
                print("❌ No cached decision files found")
                return 1
            
            print("🗃️ Cached Decision Files")
            print("=" * 30)
            
            for cache_file in sorted(cache_files, reverse=True):
                try:
                    with open(cache_file, 'r') as f:
                        cache_data = json.load(f)
                    
                    session_id = cache_data.get('session_id', 'Unknown')
                    timestamp = cache_data.get('timestamp', 'Unknown')
                    total_moves = cache_data.get('total_approved', 0)
                    
                    # Parse timestamp for display
                    try:
                        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                        time_str = dt.strftime('%Y-%m-%d %H:%M:%S')
                    except:
                        time_str = timestamp
                    
                    print(f"📄 {cache_file.name}")
                    print(f"   Session: {session_id}")
                    print(f"   Created: {time_str}")
                    print(f"   Moves: {total_moves}")
                    print(f"   Path: {cache_file}")
                    print()
                    
                except Exception as e:
                    print(f"❌ Error reading {cache_file}: {e}")
            
            print("Usage: plex-cli files move --execute-cache <cache_file>")
            return 0
            
        except Exception as e:
            print(f"❌ Error listing cache files: {e}")
            return 1
    
    def _handle_config_command(self, args) -> int:
        """Handle config command group."""
        if not args.config_command:
            self.parser.parse_args([args.command_group, '--help'])
            return 0
        
        if args.config_command == 'show':
            return self._handle_config_show(args)
        elif args.config_command == 'paths':
            return self._handle_config_paths(args)
        elif args.config_command == 'apis':
            return self._handle_config_apis(args)
        else:
            print(f"Unknown config command: {args.config_command}", file=sys.stderr)
            return 1
    
    def _handle_config_show(self, args) -> int:
        """Handle config show command."""
        try:
            print("📋 Plex CLI Configuration")
            print("=" * 40)
            
            if args.section in ['nas', 'all']:
                print("\n🖥️  NAS Configuration:")
                print(f"   Server IP: {self.config.nas_server_ip}")
                print(f"   Mount Point: {self.config.nas_mount_point}")
            
            if args.section in ['movies', 'all']:
                print("\n🎬 Movie Directories:")
                for i, dir_info in enumerate(self.config.movie_directories_full, 1):
                    print(f"   {i}. {dir_info['path']} (Priority {dir_info['priority']})")
                    print(f"      {dir_info['description']}")
            
            if args.section in ['tv', 'all']:
                print("\n📺 TV Directories:")
                for i, dir_info in enumerate(self.config.tv_directories_full, 1):
                    print(f"   {i}. {dir_info['path']} (Priority {dir_info['priority']})")
                    print(f"      {dir_info['description']}")
            
            if args.section in ['settings', 'all']:
                print("\n⚙️  Settings:")
                print(f"   Video Extensions: {', '.join(self.config.video_extensions)}")
                print(f"   Small Folder Threshold: {self.config.small_folder_threshold_mb} MB")
                print(f"   Reports Directory: {self.config.reports_directory}")
            
            return 0
            
        except Exception as e:
            print(f"Error showing configuration: {e}", file=sys.stderr)
            return 1
    
    def _handle_config_paths(self, args) -> int:
        """Handle config paths command."""
        try:
            print("📁 Configured Directory Paths")
            print("=" * 35)
            
            if args.type in ['movies', 'all']:
                print("\n🎬 Movie Paths:")
                for dir_info in self.config.movie_directories_full:
                    status = "✅" if Path(dir_info['path']).exists() else "❌"
                    print(f"   {status} {dir_info['path']}")
            
            if args.type in ['tv', 'all']:
                print("\n📺 TV Paths:")
                for dir_info in self.config.tv_directories_full:
                    status = "✅" if Path(dir_info['path']).exists() else "❌"
                    print(f"   {status} {dir_info['path']}")
            
            if args.type in ['downloads', 'all']:
                print("\n⬇️  Download Path:")
                download_path = self.config.downloads_directory
                status = "✅" if Path(download_path).exists() else "❌"
                print(f"   {status} {download_path}")
            
            print("\n Legend: ✅ = Accessible, ❌ = Not accessible")
            
            return 0
            
        except Exception as e:
            print(f"Error showing paths: {e}", file=sys.stderr)
            return 1
    
    def _handle_config_apis(self, args) -> int:
        """Handle config apis command."""
        try:
            import os
            from pathlib import Path
            
            if args.check:
                return self._check_api_connectivity()
            elif args.show:
                return self._show_api_configuration()
            else:
                # Default: show help and basic info
                print("🔑 API Configuration Management")
                print("=" * 35)
                print()
                print("External APIs used by plex-cli:")
                print("• TMDB (The Movie Database) - Movie metadata")
                print("• TVDB (TheTVDB) - TV show metadata")  
                print("• AWS Bedrock - AI classification")
                print()
                print("Configuration:")
                print("• API keys are read from environment variables")
                print("• Can be set in .env file in project root")
                print("• Required variables:")
                print("  - TMDB_API_KEY")
                print("  - TVDB_API_KEY")
                print("  - AWS_ACCESS_KEY_ID")
                print("  - AWS_SECRET_ACCESS_KEY")
                print()
                print("Commands:")
                print("  --show   Show configured API keys (masked)")
                print("  --check  Test API connectivity")
                
                return 0
            
        except Exception as e:
            print(f"❌ Error with API configuration: {e}")
            return 1
    
    def _show_api_configuration(self) -> int:
        """Show API configuration with masked keys."""
        try:
            import os
            
            print("🔑 API Configuration Status")
            print("=" * 30)
            print()
            
            # Check environment variables
            api_keys = {
                "TMDB_API_KEY": "The Movie Database",
                "TVDB_API_KEY": "TheTVDB", 
                "AWS_ACCESS_KEY_ID": "AWS Access Key",
                "AWS_SECRET_ACCESS_KEY": "AWS Secret Key"
            }
            
            configured_count = 0
            
            for env_var, description in api_keys.items():
                value = os.getenv(env_var)
                if value:
                    # Mask the key for security
                    if len(value) > 8:
                        masked = value[:4] + "*" * (len(value) - 8) + value[-4:]
                    else:
                        masked = "*" * len(value)
                    print(f"✅ {description}:")
                    print(f"   {env_var} = {masked}")
                    configured_count += 1
                else:
                    print(f"❌ {description}:")
                    print(f"   {env_var} = (not configured)")
            
            print()
            print(f"📊 Summary: {configured_count}/{len(api_keys)} API keys configured")
            
            if configured_count < len(api_keys):
                print()
                print("💡 To configure missing API keys:")
                print("   1. Create a .env file in the project root")
                print("   2. Add the missing environment variables")
                print("   3. Restart plex-cli to load new configuration")
            
            return 0
            
        except Exception as e:
            print(f"❌ Error showing API configuration: {e}")
            return 1
    
    def _check_api_connectivity(self) -> int:
        """Check API connectivity and status."""
        try:
            import os
            import requests
            
            print("🔍 API Connectivity Check")
            print("=" * 25)
            print()
            
            # Check TMDB API
            tmdb_key = os.getenv("TMDB_API_KEY")
            if tmdb_key:
                print("🎬 Testing TMDB API...")
                try:
                    response = requests.get(
                        f"https://api.themoviedb.org/3/configuration?api_key={tmdb_key}",
                        timeout=10
                    )
                    if response.status_code == 200:
                        print("   ✅ TMDB API: Connected successfully")
                    else:
                        print(f"   ❌ TMDB API: Error {response.status_code}")
                except requests.RequestException as e:
                    print(f"   ❌ TMDB API: Connection failed ({e})")
            else:
                print("🎬 TMDB API: ❌ Not configured")
            
            # Check AWS Bedrock (simplified check)
            aws_key = os.getenv("AWS_ACCESS_KEY_ID")
            aws_secret = os.getenv("AWS_SECRET_ACCESS_KEY")
            if aws_key and aws_secret:
                print("🤖 AWS Bedrock API:")
                print("   ✅ Credentials configured")
                print("   ℹ️  Full connectivity test requires boto3 client")
            else:
                print("🤖 AWS Bedrock API: ❌ Not configured")
            
            # Test TVDB API with JWT authentication
            tvdb_key = os.getenv("TVDB_API_KEY")
            if tvdb_key:
                print("📺 Testing TVDB API...")
                try:
                    # Test JWT authentication
                    login_response = requests.post(
                        "https://api4.thetvdb.com/v4/login",
                        json={"apikey": tvdb_key},
                        timeout=10
                    )
                    if login_response.status_code == 200:
                        print("   ✅ TVDB API: Authentication successful")
                    else:
                        print(f"   ❌ TVDB API: Authentication failed ({login_response.status_code})")
                except requests.RequestException as e:
                    print(f"   ❌ TVDB API: Connection failed ({e})")
            else:
                print("📺 TVDB API: ❌ Not configured")
            
            return 0
            
        except ImportError:
            print("❌ requests library not available for connectivity testing")
            return 1
        except Exception as e:
            print(f"❌ Error checking API connectivity: {e}")
            return 1
    
    def _handle_movies_command(self, args) -> int:
        """Handle movies command group."""
        if not args.movies_command:
            self.parser.parse_args([args.command_group, '--help'])
            return 0
        
        if args.movies_command == 'duplicates':
            return self._handle_movies_duplicates(args)
        elif args.movies_command == 'search':
            return self._handle_movies_search(args)
        elif args.movies_command == 'reports':
            return self._handle_movies_reports(args)
        elif args.movies_command == 'ratings':
            return self._handle_movies_ratings(args)
        else:
            print(f"Unknown movies command: {args.movies_command}", file=sys.stderr)
            return 1
    
    def _handle_tv_command(self, args) -> int:
        """Handle TV command group."""
        if not args.tv_command:
            self.parser.parse_args([args.command_group, '--help'])
            return 0
        
        if args.tv_command == 'organize':
            return self._handle_tv_organize(args)
        elif args.tv_command == 'search':
            return self._handle_tv_search(args)
        elif args.tv_command == 'missing':
            return self._handle_tv_missing(args)
        elif args.tv_command == 'reports':
            return self._handle_tv_reports(args)
        else:
            print(f"Unknown TV command: {args.tv_command}", file=sys.stderr)
            return 1
    
    def _handle_media_command(self, args) -> int:
        """Handle media command group."""
        if not args.media_command:
            self.parser.parse_args([args.command_group, '--help'])
            return 0
        
        if args.media_command == 'assistant':
            return self._handle_media_assistant(args)
        elif args.media_command == 'database':
            return self._handle_media_database(args)
        elif args.media_command == 'status':
            return self._handle_media_status(args)
        elif args.media_command == 'enrich':
            return self._handle_media_enrich(args)
        else:
            print(f"Unknown media command: {args.media_command}", file=sys.stderr)
            return 1
    
    def _run_interactive_mode(self, args) -> int:
        """Run the CLI in interactive mode with menu selection."""
        try:
            print("🎬 Plex CLI - Interactive Mode")
            print("=" * 40)
            print()
            
            while True:
                choice = self._show_main_menu()
                
                if choice == 'q':
                    print("Goodbye! 👋")
                    return 0
                elif choice == '1':
                    self._interactive_files_menu()
                elif choice == '2':
                    self._interactive_movies_menu()
                elif choice == '3':
                    self._interactive_tv_menu()
                elif choice == '4':
                    self._interactive_media_menu()
                elif choice == '5':
                    self._interactive_config_menu()
                else:
                    print("❌ Invalid choice. Please try again.")
                    print()
                    
        except KeyboardInterrupt:
            print("\nGoodbye! 👋")
            return 0
        except EOFError:
            print("Goodbye! 👋")
            return 0
    
    def _show_main_menu(self) -> str:
        """Show main menu and get user choice."""
        print("📋 Main Menu")
        print("-" * 20)
        print("1. 📁 Files        - General file operations")
        print("2. 🎬 Movies       - Movie management")
        print("3. 📺 TV          - TV show management")
        print("4. 🎭 Media       - Cross-media operations")
        print("5. ⚙️  Config      - Configuration management")
        print("q. Quit")
        print()
        
        choice = input("Select an option: ").strip().lower()
        print()
        return choice
    
    def _interactive_files_menu(self) -> None:
        """Handle files submenu in interactive mode."""
        while True:
            print("📁 Files Menu")
            print("-" * 15)
            print("1. Find duplicate movies/TV episodes")
            print("2. Database management")
            print("3. Auto-organize downloaded files")
            print("4. Analyze misplaced media files (MVP)")
            print("5. Move misplaced files interactively")
            print("b. Back to main menu")
            print("q. Quit")
            print()
            
            choice = input("Select an option: ").strip().lower()
            print()
            
            if choice == 'b':
                break
            elif choice == 'q':
                print("Goodbye! 👋")
                sys.exit(0)
            elif choice == '1':
                self._interactive_files_duplicates()
            elif choice == '2':
                self._interactive_files_database()
            elif choice == '3':
                self._interactive_files_organize()
            elif choice == '4':
                self._interactive_files_reorganize()
            elif choice == '5':
                self._interactive_files_move()
            else:
                print("❌ Invalid choice. Please try again.")
            print()
    
    
    def _interactive_files_duplicates(self) -> None:
        """Interactive duplicate detection command."""
        try:
            print("🔍 Duplicate Detection")
            print("-" * 20)
            print("1. Search all (movies + TV)")
            print("2. Search movies only")
            print("3. Search TV episodes only")
            print("b. Back to files menu")
            print("q. Quit")
            print()
            
            choice = input("Select search type (1-3, b, q): ").strip().lower()
            print()
            
            if choice == 'b':
                return
            elif choice == 'q':
                print("Goodbye! 👋")
                sys.exit(0)
            
            type_map = {
                '1': 'all',
                '2': 'movies', 
                '3': 'tv'
            }
            
            search_type = type_map.get(choice, 'all')
            
            if choice in type_map:
                # Ask about rebuilding database
                rebuild = input("Rebuild database before searching? (y/n): ").strip().lower() == 'y'
                print()
                
                # Create mock args object
                class MockArgs:
                    def __init__(self):
                        self.type = search_type
                        self.rebuild_db = rebuild
                
                self._handle_files_duplicates(MockArgs())
            else:
                print("❌ Invalid choice. Please try again.")
                
            input("\nPress Enter to continue...")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            input("\nPress Enter to continue...")
    
    def _interactive_files_database(self) -> None:
        """Interactive database management command."""
        try:
            print("📊 Database Management")
            print("-" * 20)
            print("1. Show database status")
            print("2. Rebuild database")
            print("b. Back to main menu")
            print("q. Quit")
            print()
            
            choice = input("Select operation (1-2, b, q): ").strip().lower()
            print()
            
            if choice == 'b':
                return
            elif choice == 'q':
                print("Goodbye! 👋")
                sys.exit(0)
            
            # Create mock args object
            class MockArgs:
                def __init__(self):
                    if choice == '1':
                        self.status = True
                        self.rebuild = False
                    elif choice == '2':
                        self.status = False
                        self.rebuild = True
                    else:
                        print("❌ Invalid choice. Please try again.")
                        return
            
            if choice in ['1', '2']:
                self._handle_files_database(MockArgs())
                input("\nPress Enter to continue...")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            input("\nPress Enter to continue...")
    
    def _interactive_files_organize(self) -> None:
        """Interactive auto-organize command."""
        try:
            print("🗂️  Auto-Organize Downloaded Files")
            print("-" * 35)
            print("1. Preview mode (show what would be moved)")
            print("2. Execution mode (actually move files)")
            print("3. Verify mount access only")
            print("b. Back to main menu")
            print("q. Quit")
            print()
            
            choice = input("Select mode (1-3, b, q): ").strip().lower()
            print()
            
            if choice == 'b':
                return
            elif choice == 'q':
                print("Goodbye! 👋")
                sys.exit(0)
            
            if choice == '3':
                # Verify mounts only
                class MockArgs:
                    def __init__(self):
                        self.verify_mounts = True
                        self.execute = False
                        self.no_ai = False
                
                self._handle_files_organize(MockArgs())
                input("\nPress Enter to continue...")
                return
            elif choice in ['1', '2']:
                # Ask about AI classification
                use_ai = input("Use AI classification? (y/n): ").strip().lower() == 'y'
                print()
                
                # Create mock args object
                class MockArgs:
                    def __init__(self):
                        self.execute = choice == '2'
                        self.no_ai = not use_ai
                        self.verify_mounts = False
                
                self._handle_files_organize(MockArgs())
                input("\nPress Enter to continue...")
            else:
                print("❌ Invalid choice. Please try again.")
                input("\nPress Enter to continue...")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            input("\nPress Enter to continue...")
    
    def _interactive_files_reorganize(self) -> None:
        """Interactive reorganization analysis with unified workflow."""
        try:
            print("🔍 Media Reorganization Analysis")
            print("-" * 35)
            print("This will analyze your media directories for misplaced files.")
            print("• Process: TV/Movie Database Cache → AI → Unclassified")
            print("• Generates actionable reports with move commands")
            print("• Analysis only - no files will be moved")
            print()
            
            # No options - use fixed confidence threshold
            confidence = 0.7  # Fixed threshold
            
            print(f"\n🚀 Starting analysis: Database Cache → AI → Unclassified...")
            print()
            
            # Create mock args and run analysis
            class MockArgs:
                def __init__(self):
                    self.confidence = confidence
                    self.format = 'both'
                    # Unified workflow always uses AI and external APIs
                    self.ai = True
                    self.no_external_apis = False
                    self.rebuild_db = False
            
            self._handle_files_reorganize(MockArgs())
            input("\nPress Enter to continue...")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            input("\nPress Enter to continue...")
    
    def _interactive_files_move(self) -> None:
        """Interactive file moving command."""
        try:
            print("🚚 Interactive File Mover")
            print("-" * 25)
            print("Move misplaced files based on reorganization analysis")
            print()
            
            # Check for latest report
            latest_report = Path("reports/media_reorganization_latest.json")
            
            if not latest_report.exists():
                print("❌ No reorganization analysis found!")
                print("   Please run option 4 (Analyze misplaced media files) first.")
                input("\nPress Enter to continue...")
                return
            
            # Show latest report info
            try:
                import json
                with open(latest_report, 'r') as f:
                    report_data = json.load(f)
                
                report_time = report_data.get('report_metadata', {}).get('timestamp', 'Unknown')
                total_files = report_data.get('execution_summary', {}).get('total_misplaced_files', 0)
                
                print(f"📊 Using latest analysis:")
                print(f"   Report generated: {report_time}")
                print(f"   Misplaced files found: {total_files}")
                
                if total_files == 0:
                    print("✅ No files need to be moved!")
                    input("\nPress Enter to continue...")
                    return
                
            except Exception:
                print("⚠️  Using latest report (couldn't read details)")
            
            print()
            
            # Ask for dry run mode
            dry_run_choice = input("Run in dry-run mode? (y/n - default: y): ").strip().lower()
            dry_run = dry_run_choice != 'n'
            
            print()
            print(f"🚀 Starting {'DRY RUN' if dry_run else 'LIVE'} move operation...")
            print()
            
            # Create mock args and run move
            class MockArgs:
                def __init__(self):
                    self.report = str(latest_report)
                    self.dry_run = dry_run
                    self.execute_cache = None
                    self.list_cache = False
            
            self._handle_files_move(MockArgs())
            input("\nPress Enter to continue...")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            input("\nPress Enter to continue...")
    
    def _interactive_movies_menu(self) -> None:
        """Handle movies submenu in interactive mode."""
        while True:
            print("🎬 Movies Menu")
            print("-" * 15)
            print("1. Find duplicate movies")
            print("2. Search movie collection")
            print("3. Generate movie reports")
            print("4. Fetch and manage movie ratings")
            print("b. Back to main menu")
            print("q. Quit")
            print()
            
            choice = input("Select an option: ").strip().lower()
            print()
            
            if choice == 'b':
                break
            elif choice == 'q':
                print("Goodbye! 👋")
                sys.exit(0)
            elif choice == '1':
                self._interactive_movies_duplicates()
            elif choice == '2':
                self._interactive_movies_search()
            elif choice == '3':
                self._interactive_movies_reports()
            elif choice == '4':
                self._handle_ratings_interactive()
            else:
                print("❌ Invalid choice. Please try again.")
            print()
    
    def _interactive_tv_menu(self) -> None:
        """Handle TV submenu in interactive mode."""
        while True:
            print("📺 TV Menu")
            print("-" * 10)
            print("1. Organize TV episodes")
            print("2. Search TV collection")
            print("3. Find missing episodes")
            print("4. Generate TV reports")
            print("b. Back to main menu")
            print("q. Quit")
            print()
            
            choice = input("Select an option: ").strip().lower()
            print()
            
            if choice == 'b':
                break
            elif choice == 'q':
                print("Goodbye! 👋")
                sys.exit(0)
            elif choice == '1':
                self._interactive_tv_organize()
            elif choice == '2':
                self._interactive_tv_search()
            elif choice == '3':
                self._interactive_tv_missing()
            elif choice == '4':
                self._interactive_tv_reports()
            else:
                print("❌ Invalid choice. Please try again.")
            print()
    
    def _interactive_media_menu(self) -> None:
        """Handle media submenu in interactive mode."""
        while True:
            print("🎭 Media Menu")
            print("-" * 12)
            print("1. AI-powered media assistant")
            print("2. Database management")
            print("3. System status check")
            print("4. Metadata enrichment")
            print("b. Back to main menu")
            print("q. Quit")
            print()
            
            choice = input("Select an option: ").strip().lower()
            print()
            
            if choice == 'b':
                break
            elif choice == 'q':
                print("Goodbye! 👋")
                sys.exit(0)
            elif choice == '1':
                self._interactive_media_assistant()
            elif choice == '2':
                self._interactive_media_database()
            elif choice == '3':
                self._interactive_media_status()
            elif choice == '4':
                self._interactive_media_enrich()
            else:
                print("❌ Invalid choice. Please try again.")
            print()
    
    def _interactive_config_menu(self) -> None:
        """Handle config submenu in interactive mode."""
        while True:
            print("⚙️ Configuration Menu")
            print("-" * 22)
            print("1. Show current configuration")
            print("2. Show configured paths")
            print("3. API configuration")
            print("b. Back to main menu")
            print("q. Quit")
            print()
            
            choice = input("Select an option: ").strip().lower()
            print()
            
            if choice == 'b':
                break
            elif choice == 'q':
                print("Goodbye! 👋")
                sys.exit(0)
            elif choice == '1':
                self._interactive_config_show()
            elif choice == '2':
                self._interactive_config_paths()
            elif choice == '3':
                self._interactive_config_apis()
            else:
                print("❌ Invalid choice. Please try again.")
            print()
    
    def _interactive_config_show(self) -> None:
        """Interactive config show command."""
        print("📋 Configuration Sections")
        print("-" * 25)
        print("1. All configuration")
        print("2. NAS configuration")
        print("3. Movie directories")
        print("4. TV directories")
        print("5. Settings")
        print("b. Back to config menu")
        print("q. Quit")
        print()
        
        choice = input("Select section (1-5, b, q): ").strip().lower()
        print()
        
        if choice == 'b':
            return
        elif choice == 'q':
            print("Goodbye! 👋")
            sys.exit(0)
        
        section_map = {
            '1': 'all',
            '2': 'nas',
            '3': 'movies',
            '4': 'tv',
            '5': 'settings'
        }
        
        section = section_map.get(choice, 'all')
        
        if choice in section_map:
            # Create mock args object
            class MockArgs:
                def __init__(self):
                    self.section = section
            
            self._handle_config_show(MockArgs())
        else:
            print("❌ Invalid choice. Please try again.")
        
        input("\nPress Enter to continue...")
    
    def _interactive_config_paths(self) -> None:
        """Interactive config paths command."""
        print("📁 Path Types")
        print("-" * 15)
        print("1. All paths")
        print("2. Movie paths")
        print("3. TV paths")
        print("4. Download paths")
        print("b. Back to config menu")
        print("q. Quit")
        print()
        
        choice = input("Select path type (1-4, b, q): ").strip().lower()
        print()
        
        if choice == 'b':
            return
        elif choice == 'q':
            print("Goodbye! 👋")
            sys.exit(0)
        
        type_map = {
            '1': 'all',
            '2': 'movies',
            '3': 'tv',
            '4': 'downloads'
        }
        
        path_type = type_map.get(choice, 'all')
        
        if choice in type_map:
            # Create mock args object
            class MockArgs:
                def __init__(self):
                    self.type = path_type
            
            self._handle_config_paths(MockArgs())
        else:
            print("❌ Invalid choice. Please try again.")
            
        input("\nPress Enter to continue...")
    
    def _interactive_config_apis(self) -> None:
        """Interactive API configuration management."""
        try:
            print("🔑 API Configuration Management")
            print("-" * 35)
            print("1. Show API configuration status")
            print("2. Test API connectivity")
            print("3. API configuration help")
            print()
            
            choice = input("Select option (1-3): ").strip()
            print()
            
            # Create mock args object
            class MockArgs:
                def __init__(self):
                    if choice == '1':
                        self.show = True
                        self.check = False
                    elif choice == '2':
                        self.show = False
                        self.check = True
                    else:
                        self.show = False
                        self.check = False
            
            self._handle_config_apis(MockArgs())
            input("\nPress Enter to continue...")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            input("\nPress Enter to continue...")
    
    # Interactive helpers for Phase 2 features
    def _interactive_movies_duplicates(self) -> None:
        """Interactive movie duplicates detection."""
        try:
            print("🔍 Movie Duplicate Detection")
            print("-" * 30)
            
            # Check database status and show age
            from ..plex.utils.media_database import MediaDatabase
            db = MediaDatabase()
            
            if db.is_current():
                stats = db.get_stats()
                last_updated = datetime.fromisoformat(stats.last_updated)
                hours_ago = (datetime.now() - last_updated).total_seconds() / 3600
                print(f"📊 Database last updated: {hours_ago:.1f} hours ago")
                rebuild = input(f"Rebuild database before searching? (y/n): ").strip().lower() == 'y'
            else:
                print("⚠️  Database is outdated or doesn't exist")
                rebuild = input("Rebuild database before searching? (y/n): ").strip().lower() == 'y'
            
            delete_mode = input("Enable interactive deletion mode? (y/n): ").strip().lower() == 'y'
            print()
            
            # Create mock args object
            class MockArgs:
                def __init__(self):
                    self.rebuild_db = rebuild
                    self.delete = delete_mode
            
            self._handle_movies_duplicates(MockArgs())
            input("\nPress Enter to continue...")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            input("\nPress Enter to continue...")
    
    def _interactive_movies_search(self) -> None:
        """Interactive movie search."""
        try:
            query = input("Enter movie title to search for: ").strip()
            if not query:
                print("❌ Movie title cannot be empty.")
                return
            
            print(f"\n🔍 Searching for '{query}'...")
            
            # Create mock args object
            class MockArgs:
                def __init__(self):
                    self.query = query
            
            self._handle_movies_search(MockArgs())
            input("\nPress Enter to continue...")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            input("\nPress Enter to continue...")
    
    def _interactive_movies_reports(self) -> None:
        """Interactive movie reports generation."""
        try:
            print("📊 Movie Reports Generation")
            print("-" * 30)
            print("This will generate comprehensive movie collection reports including:")
            print("• Movie inventory with collection statistics")
            print("• Duplicate movies analysis and potential space savings")
            print()
            
            proceed = input("Generate movie reports? (y/n): ").strip().lower() == 'y'
            if not proceed:
                return
                
            print()
            
            # Create mock args object (no specific arguments needed)
            class MockArgs:
                pass
            
            self._handle_movies_reports(MockArgs())
            input("\nPress Enter to continue...")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            input("\nPress Enter to continue...")
    
    def _interactive_tv_organize(self) -> None:
        """Interactive TV episode organization."""
        try:
            print("🗂️  TV Episode Organization")
            print("-" * 25)
            print("1. Use predefined TV directories")
            print("2. Use custom directories")
            print()
            
            choice = input("Select directory option (1-2): ").strip()
            print()
            
            custom_dirs = None
            if choice == '2':
                custom_dirs = input("Enter comma-separated directory paths: ").strip()
                if not custom_dirs:
                    print("❌ Custom directories cannot be empty.")
                    return
            
            print("Organization mode:")
            print("1. Analysis only (show what would be moved)")
            print("2. Demo mode (detailed preview)")
            print("3. Execute mode (actually move files - DANGEROUS!)")
            print()
            
            mode_choice = input("Select mode (1-3): ").strip()
            print()
            
            # Create mock args object
            class MockArgs:
                def __init__(self):
                    self.custom = custom_dirs
                    self.no_reports = False
                    self.demo = mode_choice == '2'
                    self.execute = mode_choice == '3'
            
            self._handle_tv_organize(MockArgs())
            input("\nPress Enter to continue...")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            input("\nPress Enter to continue...")
    
    def _interactive_tv_search(self) -> None:
        """Interactive TV show search."""
        try:
            query = input("Enter TV show title to search for: ").strip()
            if not query:
                print("❌ TV show title cannot be empty.")
                return
            
            print(f"\n🔍 Searching for '{query}'...")
            
            # Create mock args object
            class MockArgs:
                def __init__(self):
                    self.query = query
            
            self._handle_tv_search(MockArgs())
            input("\nPress Enter to continue...")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            input("\nPress Enter to continue...")
    
    def _interactive_tv_missing(self) -> None:
        """Interactive missing episodes analysis."""
        try:
            show = input("Enter TV show title to analyze: ").strip()
            if not show:
                print("❌ TV show title cannot be empty.")
                return
            
            season_input = input("Enter season number (optional, press Enter for all): ").strip()
            season = int(season_input) if season_input.isdigit() else None
            
            print(f"\n🔍 Analyzing missing episodes for '{show}'...")
            
            # Create mock args object
            class MockArgs:
                def __init__(self):
                    self.show = show
                    self.season = season
            
            self._handle_tv_missing(MockArgs())
            input("\nPress Enter to continue...")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            input("\nPress Enter to continue...")
    
    def _interactive_tv_reports(self) -> None:
        """Interactive TV reports generation."""
        try:
            print("📊 TV Reports Generation")
            print("-" * 25)
            print("This will generate comprehensive TV collection reports including:")
            print("• TV folder structure analysis")
            print("• Episode organization plan for unorganized episodes")
            print()
            
            proceed = input("Generate TV reports? (y/n): ").strip().lower() == 'y'
            if not proceed:
                return
                
            print()
            
            # Create mock args object (no specific arguments needed)
            class MockArgs:
                pass
            
            self._handle_tv_reports(MockArgs())
            input("\nPress Enter to continue...")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            input("\nPress Enter to continue...")
    
    def _interactive_media_assistant(self) -> None:
        """Interactive media assistant."""
        try:
            print("🎬 AI-Powered Media Assistant")
            print("-" * 30)
            print("Enter your question about your media collection.")
            print("Examples:")
            print("  • Do I have the movie 'Inception'?")
            print("  • How many seasons of 'The Office' do I have?")
            print("  • Am I missing episodes for 'Breaking Bad'?")
            print()
            
            query = input("Your question: ").strip()
            if not query:
                print("❌ Question cannot be empty.")
                return
            
            print()
            
            # Create mock args object
            class MockArgs:
                def __init__(self):
                    self.query = query
                    self.interactive = False
                    self.rebuild_db = False
            
            self._handle_media_assistant(MockArgs())
            input("\nPress Enter to continue...")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            input("\nPress Enter to continue...")
    
    def _interactive_media_database(self) -> None:
        """Interactive media database management."""
        try:
            print("📊 Media Database Management")
            print("-" * 30)
            print("1. Show database status")
            print("2. Rebuild database")
            print("3. Clean database (remove file)")
            print("b. Back to media menu")
            print()
            
            choice = input("Select operation (1-3, b): ").strip().lower()
            print()
            
            # Handle back option
            if choice in ['b', 'back']:
                return
            
            # Create mock args object
            class MockArgs:
                def __init__(self):
                    if choice == '1':
                        self.status = True
                        self.rebuild = False
                        self.clean = False
                    elif choice == '2':
                        self.status = False
                        self.rebuild = True
                        self.clean = False
                    elif choice == '3':
                        self.status = False
                        self.rebuild = False
                        self.clean = True
                    else:
                        print("Invalid choice. Please select 1-3 or b.")
                        input("Press Enter to continue...")
                        return
            
            self._handle_media_database(MockArgs())
            input("\nPress Enter to continue...")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            input("\nPress Enter to continue...")
    
    def _interactive_media_status(self) -> None:
        """Interactive system status check."""
        try:
            print("🔍 System Status Check")
            print("-" * 25)
            print("This will check:")
            print("• Database status and statistics")
            print("• Directory access and mount points")
            print("• Available disk space")
            print()
            
            proceed = input("Run system status check? (y/n): ").strip().lower() == 'y'
            if not proceed:
                return
                
            print()
            
            # Create mock args object (no specific arguments needed)
            class MockArgs:
                pass
            
            self._handle_media_status(MockArgs())
            input("\nPress Enter to continue...")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            input("\nPress Enter to continue...")
    
    def _interactive_media_enrich(self) -> None:
        """Interactive metadata enrichment."""
        try:
            print("🎬 Metadata Enrichment Tool")
            print("-" * 30)
            print("This tool queries external APIs (TMDB, TVDB) to enrich your media")
            print("database with accurate metadata for improved classification.")
            print()
            print("Features:")
            print("• Identifies documentaries, stand-up comedy, and other genres")
            print("• Improves reorganization accuracy")
            print("• Caches results to avoid repeated API calls")
            print()
            
            # Show current cache stats
            try:
                from ..plex.utils.metadata_enrichment import MetadataEnricher
                enricher = MetadataEnricher()
                stats = enricher.cache.get_stats()
                if stats['total_items'] > 0:
                    print(f"📊 Current cache: {stats['total_items']} items")
                    print(f"   By type: {dict(stats['by_type'])}")
                    print()
            except:
                pass
            
            print("Options:")
            print("1. View cache statistics")
            print("2. Test single title enrichment")
            print("3. Enrich sample (10 items)")
            print("4. Full enrichment (all items)")
            print("5. Force re-enrichment (cached items)")
            print("b. Back to media menu")
            print("q. Quit")
            print()
            
            choice = input("Select option (1-5, b, q): ").strip().lower()
            print()
            
            if choice == 'b':
                return
            elif choice == 'q':
                print("Goodbye! 👋")
                sys.exit(0)
            
            if choice == '1':
                # Show stats
                class MockArgs:
                    def __init__(self):
                        self.stats = True
                        self.test = None
                        self.limit = None
                        self.force = False
                
                self._handle_media_enrich(MockArgs())
                
            elif choice == '2':
                # Test single title
                title = input("Enter filename to test: ").strip()
                if title:
                    class MockArgs:
                        def __init__(self):
                            self.stats = False
                            self.test = title
                            self.limit = None
                            self.force = False
                    
                    self._handle_media_enrich(MockArgs())
                else:
                    print("❌ Title cannot be empty")
                
            elif choice == '3':
                # Sample enrichment
                class MockArgs:
                    def __init__(self):
                        self.stats = False
                        self.test = None
                        self.limit = 10
                        self.force = False
                
                self._handle_media_enrich(MockArgs())
                
            elif choice == '4':
                # Full enrichment
                class MockArgs:
                    def __init__(self):
                        self.stats = False
                        self.test = None
                        self.limit = None
                        self.force = False
                
                self._handle_media_enrich(MockArgs())
                
            elif choice == '5':
                # Force re-enrichment
                limit = input("Enter limit (or press Enter for all): ").strip()
                limit_val = int(limit) if limit.isdigit() else None
                
                class MockArgs:
                    def __init__(self):
                        self.stats = False
                        self.test = None
                        self.limit = limit_val
                        self.force = True
                
                self._handle_media_enrich(MockArgs())
                
            else:
                print("❌ Invalid choice")
                
            input("\nPress Enter to continue...")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            input("\nPress Enter to continue...")
    
    def _display_movie_duplicates(self, duplicates) -> None:
        """Display movie duplicate results."""
        if not duplicates:
            print("✅ No movie duplicates found!")
            return
        
        print(f"🎬 Found {len(duplicates)} movie duplicate groups:")
        print()
        
        total_wasted_space = 0
        for i, group in enumerate(duplicates, 1):
            files = group.files
            best_file = group.best_file
            wasted_space = sum(f.size for f in files if f != best_file)
            total_wasted_space += wasted_space
            
            print(f"{i}. {group.normalized_name}")
            print(f"   Best: {best_file.path} ({self._format_size(best_file.size)})")
            
            duplicates_to_remove = [f for f in files if f != best_file]
            for dup in duplicates_to_remove:
                print(f"   Dup:  {dup.path} ({self._format_size(dup.size)})")
            
            if wasted_space > 0:
                print(f"   💾 Potential space savings: {self._format_size(wasted_space)}")
            print()
        
        print(f"💾 Total potential space savings: {self._format_size(total_wasted_space)}")
    
    def _display_tv_duplicates(self, duplicates) -> None:
        """Display TV episode duplicate results."""
        if not duplicates:
            print("✅ No TV episode duplicates found!")
            return
        
        print(f"📺 Found {len(duplicates)} TV episode duplicate groups:")
        print()
        
        total_wasted_space = 0
        for i, group in enumerate(duplicates, 1):
            files = group.files
            best_file = group.best_file
            wasted_space = sum(f.size for f in files if f != best_file)
            total_wasted_space += wasted_space
            
            print(f"{i}. {group.show_name} S{group.season:02d}E{group.episode:02d}")
            print(f"   Best: {best_file.path} ({self._format_size(best_file.size)})")
            
            duplicates_to_remove = [f for f in files if f != best_file]
            for dup in duplicates_to_remove:
                print(f"   Dup:  {dup.path} ({self._format_size(dup.size)})")
            
            if wasted_space > 0:
                print(f"   💾 Potential space savings: {self._format_size(wasted_space)}")
            print()
        
        print(f"💾 Total potential space savings: {self._format_size(total_wasted_space)}")
    
    def _format_size(self, size_bytes: int) -> str:
        """Format file size in human-readable format."""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} PB"
    
    # Movies command handlers
    def _handle_movies_duplicates(self, args) -> int:
        """Handle movies duplicates command."""
        try:
            from ..plex.utils.media_database import MediaDatabase
            from ..plex.utils.duplicate_detector import DuplicateDetector
            
            print("🔍 Searching for movie duplicates...")
            print()
            
            # Initialize database
            db = MediaDatabase()
            
            # Check database age and ask for rebuild if needed
            if not args.rebuild_db:
                if not db.is_current():
                    print("⚠️  Database is outdated or doesn't exist")
                    rebuild = input("Would you like to rebuild the database? (y/n): ").strip().lower()
                    if rebuild == 'y':
                        args.rebuild_db = True
                else:
                    stats = db.get_stats()
                    last_updated = datetime.fromisoformat(stats.last_updated)
                    hours_ago = (datetime.now() - last_updated).total_seconds() / 3600
                    print(f"📊 Database last updated {hours_ago:.1f} hours ago")
                    
                    # Always ask but include the age information
                    rebuild = input(f"Rebuild database before searching? (y/n): ").strip().lower()
                    if rebuild == 'y':
                        args.rebuild_db = True
            
            # Rebuild database if requested
            if args.rebuild_db:
                print("🔄 Rebuilding database...")
                stats = db.rebuild_database()
                print(f"✅ Database rebuilt: {stats.movies_count} movies, {stats.tv_episodes_count} TV episodes")
                print()
            
            # Initialize duplicate detector
            detector = DuplicateDetector(db)
            
            # Search for movie duplicates
            print("🎬 Searching for movie duplicates...")
            movie_duplicates = detector.find_movie_duplicates()
            self._display_movie_duplicates(movie_duplicates)
            
            # Handle deletion if requested
            if args.delete and movie_duplicates:
                print()
                return self._handle_interactive_deletion(movie_duplicates, 'movies')
            
            return 0
            
        except ImportError as e:
            print(f"❌ Missing required module: {e}")
            print("   The duplicate detector may not be fully implemented.")
            return 1
        except Exception as e:
            print(f"❌ Error searching for duplicates: {e}")
            return 1
    
    def _handle_movies_search(self, args) -> int:
        """Handle movies search command."""
        try:
            from ..plex.utils.media_searcher import MediaSearcher
            
            searcher = MediaSearcher()
            result = searcher.search_movies(args.query)
            
            if not result.matches:
                print(f"❌ No movies found matching '{args.query}'")
                return 0
            
            print(f"🎬 Found {result.total_found} movie(s) matching '{args.query}':")
            print()
            
            for i, match in enumerate(result.matches[:10], 1):  # Show top 10 matches
                year_str = f" ({match.year})" if match.year else ""
                size_str = self._format_size(match.file_size) if match.file_size else ""
                confidence_str = f" [{match.confidence:.1%} match]" if match.confidence < 0.95 else ""
                
                print(f"{i}. {match.title}{year_str}{confidence_str}")
                print(f"   📁 {match.path}")
                if size_str:
                    print(f"   📊 {size_str}")
                print()
            
            return 0
            
        except ImportError as e:
            print(f"❌ Missing required module: {e}")
            return 1
        except Exception as e:
            print(f"❌ Error searching for movies: {e}")
            return 1
    
    def _handle_movies_reports(self, args) -> int:
        """Handle movies reports command."""
        try:
            from ..plex.utils.report_generator import (
                generate_movie_inventory_report,
                generate_duplicate_report
            )
            from ..plex.utils.duplicate_detector import DuplicateDetector
            from ..plex.utils.media_database import MediaDatabase
            
            print("📊 Generating movie collection reports...")
            print()
            
            # Initialize database and duplicate detector
            db = MediaDatabase()
            
            # Check if database needs rebuild
            if not db.is_current():
                print("⚠️  Database is outdated or doesn't exist")
                rebuild = input("Would you like to rebuild the database? (y/n): ").strip().lower()
                if rebuild == 'y':
                    print("🔄 Rebuilding database...")
                    stats = db.rebuild_database()
                    print(f"✅ Database rebuilt: {stats.movies_count} movies")
                    print()
                else:
                    print("ℹ️  Using existing database (may be outdated)")
                    print()
            
            # Generate movie inventory report
            print("📋 Generating movie inventory report...")
            try:
                # Get movie directories from config
                movie_directories = self.config.movie_directories
                txt_path, json_path = generate_movie_inventory_report(movie_directories)
                print(f"✅ Movie inventory report generated:")
                print(f"   📄 Text: {txt_path}")
                print(f"   📄 JSON: {json_path}")
            except Exception as e:
                print(f"❌ Error generating inventory report: {e}")
            
            print()
            
            # Generate duplicate report
            print("🔍 Generating duplicate movies report...")
            try:
                detector = DuplicateDetector(db)
                movie_duplicates = detector.find_movie_duplicates()
                
                if movie_duplicates:
                    txt_path, json_path = generate_duplicate_report(movie_duplicates)
                    print(f"✅ Duplicate movies report generated:")
                    print(f"   📄 Text: {txt_path}")
                    print(f"   📄 JSON: {json_path}")
                    print(f"   🎬 Found {len(movie_duplicates)} duplicate groups")
                else:
                    print("✅ No duplicates found - no duplicate report needed")
            except Exception as e:
                print(f"❌ Error generating duplicate report: {e}")
            
            print()
            print("📊 Movie reports generation complete!")
            
            return 0
            
        except ImportError as e:
            print(f"❌ Report generation not available: {e}")
            return 1
        except Exception as e:
            print(f"❌ Error generating reports: {e}")
            return 1
    
    def _handle_movies_ratings(self, args) -> int:
        """Handle movies ratings command."""
        try:
            from ..plex.utils.omdb_rating_fetcher import OMDBRatingFetcher, OMDBRatingDatabase
            
            # Handle different rating operations
            if args.stats:
                return self._handle_ratings_stats()
            elif args.fetch:
                return self._handle_ratings_fetch()
            elif args.bad_movies:
                return self._handle_ratings_bad_movies(args)
            elif args.delete_bad:
                return self._handle_ratings_delete_bad(args)
            else:
                # Interactive mode
                return self._handle_ratings_interactive()
                
        except ImportError as e:
            print(f"❌ OMDB rating fetcher not available: {e}")
            return 1
        except Exception as e:
            print(f"❌ Error with ratings command: {e}")
            return 1
    
    def _handle_ratings_stats(self) -> int:
        """Show rating database statistics."""
        try:
            from ..plex.utils.omdb_rating_fetcher import OMDBRatingDatabase
            
            print("📊 Movie Ratings Database Statistics")
            print("=" * 40)
            
            db = OMDBRatingDatabase()
            stats = db.get_stats()
            
            print(f"Total movies with ratings: {stats['total_movies']:,}")
            print(f"Movies with IMDB ratings: {stats['with_imdb_rating']:,}")
            print(f"Movies with Rotten Tomatoes: {stats['with_rotten_tomatoes']:,}")
            print(f"Movies with Metacritic: {stats['with_metacritic']:,}")
            
            if stats['average_imdb_rating']:
                print(f"Average IMDB rating: {stats['average_imdb_rating']}/10")
            
            print(f"Database location: {stats['database_path']}")
            
            return 0
            
        except Exception as e:
            print(f"❌ Error showing stats: {e}")
            return 1
    
    def _handle_ratings_fetch(self) -> int:
        """Fetch ratings for all movies."""
        try:
            from ..plex.utils.omdb_rating_fetcher import OMDBRatingFetcher
            from ..plex.utils.media_database import MediaDatabase
            
            print("🎬 Fetching Movie Ratings from OMDB")
            print("=" * 40)
            
            # Load movie database
            db = MediaDatabase()
            if not db.is_current():
                print("⚠️  Movie database is outdated")
                rebuild = input("Rebuild database first? (y/n): ").strip().lower()
                if rebuild == 'y':
                    print("🔄 Rebuilding database...")
                    db.rebuild_database()
                    print("✅ Database rebuilt")
            
            # Get movies
            movies = db.get_movies()
            print(f"📽️  Found {len(movies)} movies to process")
            print()
            
            # Initialize fetcher
            fetcher = OMDBRatingFetcher()
            
            # Progress callback
            def progress_callback(current, total, filename):
                print(f"   📊 Processing {current}/{total}: {filename}")
            
            # Fetch ratings
            summary = fetcher.fetch_ratings_for_movies(movies, progress_callback)
            
            # Show summary
            print(f"\\n✅ Rating fetch completed!")
            print(f"   📊 Processed: {summary['processed']}/{summary['total_movies']} movies")
            print(f"   📈 Success rate: {summary['success_rate']:.1f}%")
            print(f"   🔄 API calls: {summary['stats']['api_calls']}")
            print(f"   💾 Cache hits: {summary['stats']['cache_hits']}")
            print(f"   📄 Log file: {summary['log_file']}")
            
            return 0
            
        except Exception as e:
            print(f"❌ Error fetching ratings: {e}")
            return 1
    
    def _handle_ratings_bad_movies(self, args) -> int:
        """List badly rated movies."""
        try:
            from ..plex.utils.omdb_rating_fetcher import OMDBRatingDatabase
            
            print("📉 Badly Rated Movies")
            print("=" * 25)
            print(f"Thresholds: IMDB < {args.imdb_threshold}, RT < {args.rt_threshold}%, Metacritic < {args.meta_threshold}")
            print()
            
            db = OMDBRatingDatabase()
            bad_movies = db.get_badly_rated_movies(
                args.imdb_threshold,
                args.rt_threshold, 
                args.meta_threshold
            )
            
            if not bad_movies:
                print("✅ No badly rated movies found!")
                return 0
            
            print(f"Found {len(bad_movies)} badly rated movies:")
            print()
            
            total_size = 0
            for i, movie in enumerate(bad_movies, 1):
                print(f"{i}. {movie.title} ({movie.year or 'Unknown'})")
                print(f"   IMDB: {movie.imdb_rating or 'N/A'}/10")
                print(f"   Rotten Tomatoes: {movie.rotten_tomatoes or 'N/A'}%")
                print(f"   Metacritic: {movie.metacritic or 'N/A'}/100")
                print(f"   Quality Score: {movie.get_quality_score():.1f}/100")
                print(f"   Size: {movie._format_file_size(movie.file_size)}")
                print(f"   Path: {movie.file_path}")
                print()
                total_size += movie.file_size
            
            print(f"💾 Total size of badly rated movies: {self._format_file_size(total_size)}")
            
            return 0
            
        except Exception as e:
            print(f"❌ Error listing bad movies: {e}")
            return 1
    
    def _handle_ratings_delete_bad(self, args) -> int:
        """Delete badly rated movies with confirmation."""
        try:
            from ..plex.utils.omdb_rating_fetcher import OMDBRatingDatabase
            import os
            
            print("🗑️  Delete Badly Rated Movies")
            print("=" * 30)
            print(f"Thresholds: IMDB < {args.imdb_threshold}, RT < {args.rt_threshold}%, Metacritic < {args.meta_threshold}")
            print()
            
            db = OMDBRatingDatabase()
            bad_movies = db.get_badly_rated_movies(
                args.imdb_threshold,
                args.rt_threshold,
                args.meta_threshold
            )
            
            if not bad_movies:
                print("✅ No badly rated movies found!")
                return 0
            
            # Show movies to be deleted
            total_size = sum(movie.file_size for movie in bad_movies)
            print(f"⚠️  {len(bad_movies)} movies marked for deletion:")
            for movie in bad_movies[:10]:  # Show first 10
                print(f"   • {movie.title} ({movie.year}) - Quality: {movie.get_quality_score():.1f}/100")
            
            if len(bad_movies) > 10:
                print(f"   ... and {len(bad_movies) - 10} more movies")
            
            print(f"\\n💾 Total space to be freed: {self._format_file_size(total_size)}")
            print()
            
            # Confirmation
            print("⚠️  THIS WILL PERMANENTLY DELETE THESE MOVIE FILES!")
            confirm1 = input("Type 'DELETE BADLY RATED MOVIES' to confirm: ").strip()
            
            if confirm1 != "DELETE BADLY RATED MOVIES":
                print("❌ Deletion cancelled - confirmation text didn't match")
                return 0
            
            confirm2 = input("Are you absolutely sure? (yes/no): ").strip().lower()
            if confirm2 != "yes":
                print("❌ Deletion cancelled")
                return 0
            
            # Delete files
            deleted_count = 0
            deleted_size = 0
            failed_deletions = []
            
            print(f"\\n🗑️  Deleting {len(bad_movies)} badly rated movies...")
            
            for movie in bad_movies:
                try:
                    if os.path.exists(movie.file_path):
                        file_size = os.path.getsize(movie.file_path)
                        os.remove(movie.file_path)
                        print(f"   ✅ Deleted: {movie.title}")
                        deleted_count += 1
                        deleted_size += file_size
                    else:
                        print(f"   ⚠️  File not found: {movie.title}")
                except Exception as e:
                    print(f"   ❌ Failed to delete {movie.title}: {e}")
                    failed_deletions.append(movie.title)
            
            # Summary
            print(f"\\n📊 Deletion Summary:")
            print(f"   ✅ Successfully deleted: {deleted_count} movies")
            print(f"   💾 Space freed: {self._format_file_size(deleted_size)}")
            if failed_deletions:
                print(f"   ❌ Failed deletions: {len(failed_deletions)}")
            
            return 0
            
        except Exception as e:
            print(f"❌ Error deleting bad movies: {e}")
            return 1
    
    def _handle_ratings_interactive(self) -> int:
        """Interactive ratings menu."""
        while True:
            print("🎬 Movie Ratings Menu")
            print("-" * 20)
            print("1. Fetch ratings from OMDB")
            print("2. Show database statistics")  
            print("3. List badly rated movies")
            print("4. Delete badly rated movies")
            print("b. Back to movies menu")
            print("q. Quit")
            print()
            
            choice = input("Select option (1-4, b, q): ").strip().lower()
            
            if choice == 'b':
                return 0
            elif choice == 'q':
                print("Goodbye! 👋")
                sys.exit(0)
            elif choice == '1':
                self._handle_ratings_fetch()
                input("\\nPress Enter to continue...")
            elif choice == '2':
                self._handle_ratings_stats()
                input("\\nPress Enter to continue...")
            elif choice == '3':
                # Use default thresholds
                class MockArgs:
                    imdb_threshold = 5.0
                    rt_threshold = 30
                    meta_threshold = 40
                self._handle_ratings_bad_movies(MockArgs())
                input("\\nPress Enter to continue...")
            elif choice == '4':
                class MockArgs:
                    imdb_threshold = 5.0
                    rt_threshold = 30
                    meta_threshold = 40
                self._handle_ratings_delete_bad(MockArgs())
                input("\\nPress Enter to continue...")
            else:
                print("❌ Invalid choice. Please try again.")
            
            print()
    
    def _format_file_size(self, size_bytes: int) -> str:
        """Format file size in human-readable format."""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} PB"
    
    # TV command handlers
    def _handle_tv_organize(self, args) -> int:
        """Handle TV organize command."""
        try:
            from ..plex.utils.tv_scanner import (
                find_unorganized_tv_episodes,
                find_unorganized_tv_episodes_custom,
                print_tv_organization_report
            )
            from ..plex.utils.tv_report_generator import (
                generate_tv_folder_analysis_report,
                generate_tv_organization_plan_report
            )
            
            # Determine directories to use
            if args.custom:
                directories = [d.strip() for d in args.custom.split(',') if d.strip()]
                if not directories:
                    print("Error: No valid custom directories specified", file=sys.stderr)
                    return 1
                
                # Validate directories exist
                valid_directories = []
                for directory in directories:
                    if Path(directory).exists():
                        valid_directories.append(directory)
                    else:
                        print(f"Warning: Directory does not exist: {directory}", file=sys.stderr)
                
                if not valid_directories:
                    print("Error: No valid directories found", file=sys.stderr)
                    return 1
                
                tv_groups = find_unorganized_tv_episodes_custom(valid_directories)
            else:
                tv_groups = find_unorganized_tv_episodes()
            
            # Generate reports if not disabled
            if not args.no_reports:
                print("📊 Analyzing existing TV folder structure...")
                try:
                    if args.custom:
                        folder_report = generate_tv_folder_analysis_report(valid_directories)
                    else:
                        from ..plex.config.config import MediaConfig
                        config = MediaConfig()
                        folder_report = generate_tv_folder_analysis_report(config.tv_directories)
                    print(f"✅ TV folder analysis report: {folder_report}")
                except Exception as e:
                    print(f"⚠️  Warning: Could not generate folder analysis: {e}")
            
            # Handle demo mode
            if args.demo:
                print(f"\n🎯 DEMONSTRATION MODE")
                print("=" * 60)
                print("This shows what WOULD be moved during organization")
                print("NO FILES WILL ACTUALLY BE MOVED")
                print("=" * 60)
                
                print_tv_organization_report(tv_groups)
                
                if tv_groups:
                    total_episodes = sum(group.episode_count for group in tv_groups)
                    total_shows = len(tv_groups)
                    print(f"\n📋 Organization Summary:")
                    print(f"  • {total_shows} TV shows need organization")
                    print(f"  • {total_episodes} episodes would be moved")
                    print(f"  • Target folders would be created automatically")
                    print(f"\n💡 Use --execute flag to actually perform the moves")
                
                return 0
            
            # Handle execute mode
            if args.execute:
                if not tv_groups:
                    print("✅ No unorganized episodes found - nothing to move!")
                    return 0
                
                print(f"\n🗂️  ORGANIZATION MODE - WARNING!")
                print("=" * 60)
                print("⚠️  You are about to MOVE TV episode files!")
                print("⚠️  This will change your file structure!")
                print("⚠️  Make sure you have backups!")
                print("=" * 60)
                
                confirm = input("\nType 'ORGANIZE FILES' to continue: ").strip()
                if confirm == "ORGANIZE FILES":
                    print("🗂️  Starting TV show organization...")
                    # TODO: Implement actual file moving logic
                    print("⚠️  Organization functionality coming soon!")
                    print("     Use --demo mode to see what would be moved")
                else:
                    print("🚫 Organization cancelled")
                return 0
            
            # Default: Analysis mode
            print_tv_organization_report(tv_groups)
            
            # Generate organization plan report
            if not args.no_reports:
                print(f"\n📄 Generating organization plan report...")
                try:
                    plan_report = generate_tv_organization_plan_report(tv_groups)
                    print(f"✅ Organization plan report: {plan_report}")
                except Exception as e:
                    print(f"⚠️  Warning: Could not generate plan report: {e}")
            
            # Summary
            if tv_groups:
                total_episodes = sum(group.episode_count for group in tv_groups)
                total_shows = len(tv_groups)
                print(f"\n📊 SUMMARY:")
                print(f"  Total shows needing organization: {total_shows}")
                print(f"  Total episodes to organize: {total_episodes}")
                print(f"\n⚠️  IMPORTANT: This is analysis only - NO FILES WERE MOVED")
                print(f"      Use --demo to see organization plan")
                print(f"      Use --execute to actually move files (coming soon)")
            else:
                print(f"\n✅ All TV episodes appear to be properly organized!")
            
            return 0
            
        except ImportError as e:
            print(f"❌ Missing required module: {e}")
            return 1
        except Exception as e:
            print(f"❌ Error organizing TV episodes: {e}")
            return 1
    
    def _handle_tv_search(self, args) -> int:
        """Handle TV search command."""
        try:
            from ..plex.utils.media_searcher import MediaSearcher
            
            searcher = MediaSearcher()
            result = searcher.search_tv_shows(args.query)
            
            if not result.matches:
                print(f"❌ No TV shows found matching '{args.query}'")
                return 0
            
            # Get season summary
            season_info = searcher.get_tv_show_seasons(args.query)
            
            print(f"📺 Found '{season_info['show_title']}'")
            print(f"   Seasons: {season_info['total_seasons']}")
            print(f"   Episodes: {season_info['total_episodes']}")
            print()
            
            # Show season breakdown
            if season_info['seasons']:
                print("📋 Season breakdown:")
                for season_num in sorted(season_info['seasons'].keys()):
                    episodes = season_info['seasons'][season_num]
                    episode_range = self._get_episode_range(episodes)
                    print(f"   Season {season_num}: {len(episodes)} episodes {episode_range}")
                print()
            
            # Show some file paths
            print("📁 Sample files:")
            unique_paths = set()
            for match in result.matches[:3]:
                unique_paths.add(str(Path(match.path).parent))
            
            for path in list(unique_paths)[:3]:
                print(f"   {path}")
            
            return 0
            
        except ImportError as e:
            print(f"❌ Missing required module: {e}")
            return 1
        except Exception as e:
            print(f"❌ Error searching for TV shows: {e}")
            return 1
    
    def _handle_tv_missing(self, args) -> int:
        """Handle TV missing episodes command."""
        try:
            from ..plex.utils.episode_analyzer import EpisodeAnalyzer
            
            analyzer = EpisodeAnalyzer()
            
            print(f"🔍 Analyzing missing episodes for '{args.show}'")
            if args.season:
                print(f"   Focusing on Season {args.season}")
            print()
            
            report = analyzer.analyze_missing_episodes(args.show, args.season)
            
            if not report.found_locally:
                print(f"❌ '{args.show}' not found in your collection")
                return 0
            
            print(f"📺 {report.show_title}")
            print(f"   Completeness: {report.completeness_percent:.1f}%")
            
            if report.total_missing == 0:
                print("   ✅ Collection appears complete!")
            else:
                print(f"   ❌ Missing {report.total_missing} episode(s)")
                
                if report.missing_seasons:
                    print(f"   Missing entire seasons: {sorted(report.missing_seasons)}")
                
                for season_num, missing_episodes in report.missing_episodes.items():
                    if missing_episodes:
                        episodes_str = self._format_episode_list(missing_episodes)
                        print(f"   Season {season_num}: Missing episodes {episodes_str}")
            
            print()
            print(f"📊 Your collection: {len(report.local_seasons)} seasons")
            if report.api_seasons:
                print(f"   Expected total: {len(report.api_seasons)} seasons")
            
            return 0
            
        except ImportError as e:
            print(f"❌ Missing required module: {e}")
            return 1
        except Exception as e:
            print(f"❌ Error analyzing missing episodes: {e}")
            return 1
    
    def _handle_tv_reports(self, args) -> int:
        """Handle TV reports command."""
        try:
            from ..plex.utils.tv_report_generator import (
                generate_tv_folder_analysis_report,
                generate_tv_organization_plan_report
            )
            from ..plex.utils.tv_scanner import find_unorganized_tv_episodes
            
            print("📊 Generating TV collection reports...")
            print()
            
            # Get TV directories from config
            tv_directories = self.config.tv_directories
            
            # Generate TV folder analysis report
            print("📋 Analyzing TV folder structure...")
            try:
                folder_report_path = generate_tv_folder_analysis_report(tv_directories)
                print(f"✅ TV folder analysis report generated:")
                print(f"   📄 Report: {folder_report_path}")
            except Exception as e:
                print(f"❌ Error generating folder analysis: {e}")
            
            print()
            
            # Generate TV organization plan report
            print("🗂️  Analyzing TV episode organization...")
            try:
                tv_groups = find_unorganized_tv_episodes()
                
                if tv_groups:
                    plan_report_path = generate_tv_organization_plan_report(tv_groups)
                    print(f"✅ TV organization plan report generated:")
                    print(f"   📄 Report: {plan_report_path}")
                    
                    total_episodes = sum(group.episode_count for group in tv_groups)
                    total_shows = len(tv_groups)
                    print(f"   📺 Found {total_shows} shows with {total_episodes} unorganized episodes")
                else:
                    print("✅ All TV episodes appear to be properly organized")
                    print("   📄 No organization plan report needed")
            except Exception as e:
                print(f"❌ Error generating organization plan: {e}")
            
            print()
            print("📊 TV reports generation complete!")
            
            return 0
            
        except ImportError as e:
            print(f"❌ TV report generation not available: {e}")
            return 1
        except Exception as e:
            print(f"❌ Error generating TV reports: {e}")
            return 1
    
    # Media command handlers
    def _handle_media_assistant(self, args) -> int:
        """Handle media assistant command."""
        try:
            from ..plex.cli.media_assistant import MediaAssistant
            from ..plex.utils.media_database import MediaDatabase
            
            # Handle database rebuild
            if args.rebuild_db:
                print("🔄 Rebuilding media database...")
                database = MediaDatabase()
                stats = database.rebuild_database()
                
                print(f"✅ Database rebuilt successfully!")
                print(f"   📊 Movies: {stats.movies_count}")
                print(f"   📺 TV Shows: {stats.tv_shows_count}")
                print(f"   🎬 Episodes: {stats.tv_episodes_count}")
                print(f"   ⏱️  Build time: {stats.build_time_seconds}s")
                print(f"   💾 Total size: {stats.total_size_bytes / (1024**3):.1f} GB")
                print()
                
                if not args.query and not args.interactive:
                    return 0  # Exit after rebuild if no other action requested
            
            if not args.query and not args.interactive and not args.rebuild_db:
                print("Usage: plex-cli media assistant [query] or use --interactive")
                return 1
            
            # Initialize assistant
            assistant = MediaAssistant(verbose=False, use_database=True)
            
            if args.interactive:
                # Interactive mode
                print("🎬 Plex Media Assistant - Interactive Mode")
                print("Ask questions about your media collection in natural language.")
                print("Examples:")
                print("  • Do I have the movie 'Inception'?")
                print("  • How many seasons of 'The Office' do I have?")
                print("  • Am I missing episodes for 'Breaking Bad'?")
                print()
                print("Type 'quit' or 'exit' to leave.")
                print()
                
                while True:
                    try:
                        query = input("❓ Your question: ").strip()
                        if query.lower() in ['quit', 'exit', 'q']:
                            print("Goodbye! 👋")
                            break
                        
                        if query:
                            print()
                            assistant.process_query(query)
                            print()
                    except KeyboardInterrupt:
                        print("\nGoodbye! 👋")
                        break
                    except EOFError:
                        break
            else:
                # Single query mode
                assistant.process_query(args.query)
            
            return 0
            
        except ImportError as e:
            print(f"❌ Missing required module: {e}")
            return 1
        except Exception as e:
            print(f"❌ Error with media assistant: {e}")
            return 1
    
    def _handle_media_database(self, args) -> int:
        """Handle media database command."""
        try:
            from ..plex.utils.media_database import MediaDatabase
            
            db = MediaDatabase()
            
            if args.clean:
                if db.db_path.exists():
                    db.db_path.unlink()
                    print(f"✅ Database file removed: {db.db_path}")
                else:
                    print("ℹ️  Database file does not exist")
                return 0
            
            if args.rebuild:
                print("🔄 Rebuilding media database...")
                stats = db.rebuild_database()
                print(f"✅ Database rebuilt successfully!")
                print(f"   📊 Movies: {stats.movies_count}")
                print(f"   📺 TV Shows: {stats.tv_shows_count}")
                print(f"   🎬 Episodes: {stats.tv_episodes_count}")
                print(f"   ⏱️  Build time: {stats.build_time_seconds:.1f}s")
                print(f"   💾 Total size: {stats.total_size_bytes / (1024**3):.1f} GB")
                
            elif args.status:
                if db.is_current():
                    stats = db.get_stats()
                    last_updated = datetime.fromisoformat(stats.last_updated)
                    hours_ago = (datetime.now() - last_updated).total_seconds() / 3600
                    
                    print("📊 Database Status")
                    print("=" * 20)
                    print(f"Status: ✅ Current")
                    print(f"Last updated: {hours_ago:.1f} hours ago")
                    print(f"Movies: {stats.movies_count}")
                    print(f"TV Shows: {stats.tv_shows_count}")
                    print(f"TV Episodes: {stats.tv_episodes_count}")
                    print(f"Total files: {stats.total_files}")
                    print(f"Total size: {stats.total_size_bytes / (1024**3):.1f} GB")
                    print(f"Build time: {stats.build_time_seconds:.1f}s")
                else:
                    print("📊 Database Status")
                    print("=" * 20)
                    print("Status: ❌ Outdated or missing")
                    print("Run 'plex-cli media database --rebuild' to update")
            else:
                # Show help if no specific action
                self.parser.parse_args(['media', 'database', '--help'])
            
            return 0
            
        except Exception as e:
            print(f"❌ Error with database operation: {e}")
            return 1
    
    def _handle_media_status(self, args) -> int:
        """Handle media status command."""
        try:
            import shutil
            from pathlib import Path
            from ..plex.utils.media_database import MediaDatabase
            
            print("🔍 System Status Check")
            print("=" * 30)
            print()
            
            # Check database status
            print("📊 Database Status:")
            db = MediaDatabase()
            if db.is_current():
                stats = db.get_stats()
                last_updated = datetime.fromisoformat(stats.last_updated)
                hours_ago = (datetime.now() - last_updated).total_seconds() / 3600
                print(f"   ✅ Current (updated {hours_ago:.1f} hours ago)")
                print(f"   📊 {stats.movies_count} movies, {stats.tv_shows_count} TV shows")
                print(f"   💾 {stats.total_size_bytes / (1024**3):.1f} GB total size")
            else:
                print("   ❌ Outdated or missing")
            print()
            
            # Check mount points and directory access
            print("📁 Directory Access Status:")
            all_directories = [
                ("Movie", self.config.movie_directories),
                ("TV", self.config.tv_directories),
                ("Downloads", [self.config.downloads_directory])
            ]
            
            total_accessible = 0
            total_directories = 0
            
            for dir_type, directories in all_directories:
                print(f"   {dir_type} Directories:")
                for directory in directories:
                    total_directories += 1
                    dir_path = Path(directory)
                    
                    if dir_path.exists() and dir_path.is_dir():
                        try:
                            # Test write access
                            test_file = dir_path / ".plex_cli_test"
                            test_file.touch()
                            test_file.unlink()
                            
                            # Get disk space
                            total, used, free = shutil.disk_usage(directory)
                            free_gb = free / (1024**3)
                            
                            print(f"     ✅ {directory} ({free_gb:.1f} GB free)")
                            total_accessible += 1
                        except (PermissionError, OSError):
                            print(f"     ⚠️  {directory} (access issues)")
                    else:
                        print(f"     ❌ {directory} (not accessible)")
            print()
            
            # Overall status summary
            print("📋 Summary:")
            print(f"   Directory Access: {total_accessible}/{total_directories} directories accessible")
            
            if total_accessible == total_directories:
                print("   🟢 System Status: All systems operational")
                return 0
            elif total_accessible > 0:
                print("   🟡 System Status: Partial functionality")
                return 0
            else:
                print("   🔴 System Status: No directories accessible")
                return 1
            
        except Exception as e:
            print(f"❌ Error checking system status: {e}")
            return 1
    
    def _handle_media_enrich(self, args) -> int:
        """Handle media enrich command."""
        try:
            from ..plex.utils.metadata_enrichment import MetadataEnricher
            
            print("🎬 Media Metadata Enrichment Tool")
            print("=" * 40)
            
            # Handle stats display
            if args.stats:
                enricher = MetadataEnricher()
                stats = enricher.cache.get_stats()
                print("\nMetadata Cache Statistics:")
                print(f"Total items: {stats['total_items']}")
                print("\nBy type:")
                for media_type, count in stats['by_type'].items():
                    print(f"  {media_type}: {count}")
                print("\nBy source:")
                for source, count in stats['by_source'].items():
                    print(f"  {source}: {count}")
                return 0
            
            # Handle single title test
            if args.test:
                enricher = MetadataEnricher()
                title, year = enricher.extract_title_and_year(args.test)
                print(f"Testing enrichment for: {title} ({year})")
                metadata = enricher.enrich_title(title, year)
                if metadata:
                    print(f"Result: {metadata.media_type} (confidence: {metadata.confidence:.2f})")
                    print(f"Genres: {metadata.genres}")
                    if metadata.overview:
                        print(f"Overview: {metadata.overview[:100]}...")
                else:
                    print("No metadata found")
                return 0
            
            # Run full enrichment
            print("This tool will query external APIs (TMDB, TVDB) to enrich your media database")
            print("with accurate metadata for improved classification.")
            print()
            
            if args.limit:
                print(f"Processing limit: {args.limit} items")
            if args.force:
                print("Force mode: Re-enriching cached items")
            print()
            
            confirm = input("Proceed with metadata enrichment? (y/n): ").strip().lower()
            if confirm != 'y':
                print("Enrichment cancelled")
                return 0
            
            print("\n🚀 Starting metadata enrichment...")
            
            enricher = MetadataEnricher()
            results = enricher.enrich_database(
                limit=args.limit,
                skip_cached=not args.force
            )
            
            print(f"\n✅ Enrichment completed!")
            print(f"📊 Results:")
            for key, value in results.items():
                print(f"   {key.replace('_', ' ').title()}: {value}")
            
            # Show updated cache stats
            stats = enricher.cache.get_stats()
            print(f"\n📈 Updated Cache Statistics:")
            print(f"   Total items: {stats['total_items']}")
            print(f"   By type: {dict(stats['by_type'])}")
            
            print(f"\n💡 TIP: Use 'plex-cli files reorganize' with enhanced classification")
            
            return 0
            
        except ImportError as e:
            print(f"❌ Metadata enrichment not available: {e}")
            print("   Make sure the metadata_enrichment module is properly installed.")
            return 1
        except Exception as e:
            print(f"❌ Error during metadata enrichment: {e}")
            return 1
    
    # Helper methods for Phase 2 features
    def _handle_interactive_deletion(self, duplicates, media_type: str) -> int:
        """Handle interactive deletion of duplicates."""
        try:
            from ..plex.utils.deletion_manager import DeletionManager
            
            print(f"🗑️  Interactive deletion mode for {media_type}...")
            
            deletion_manager = DeletionManager()
            if media_type == 'movies':
                deletion_manager.interactive_delete_movies(duplicates)
            else:
                deletion_manager.interactive_delete_tv_episodes(duplicates)
            
            return 0
            
        except ImportError as e:
            print(f"❌ Interactive deletion not available: {e}")
            return 1
        except Exception as e:
            print(f"❌ Error during interactive deletion: {e}")
            return 1
    
    def _get_episode_range(self, episodes) -> str:
        """Get a formatted episode range string."""
        episode_nums = [ep['episode'] for ep in episodes if ep.get('episode') is not None]
        if not episode_nums:
            return ""
        
        episode_nums.sort()
        if len(episode_nums) == 1:
            return f"(E{episode_nums[0]})"
        elif episode_nums == list(range(episode_nums[0], episode_nums[-1] + 1)):
            return f"(E{episode_nums[0]}-E{episode_nums[-1]})"
        else:
            return f"(E{episode_nums[0]}...E{episode_nums[-1]}, {len(episode_nums)} total)"
    
    def _format_episode_list(self, episodes) -> str:
        """Format a list of episode numbers for display."""
        if len(episodes) <= 5:
            return ", ".join(f"E{ep}" for ep in episodes)
        else:
            return f"E{episodes[0]}-E{episodes[-1]} ({len(episodes)} episodes)"


def main() -> int:
    """Main entry point for plex-cli."""
    cli = PlexCLI()
    return cli.run()


if __name__ == '__main__':
    sys.exit(main())