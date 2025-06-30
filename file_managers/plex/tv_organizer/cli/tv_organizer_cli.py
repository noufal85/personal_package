#!/usr/bin/env python3
"""
Standalone CLI for TV File Organizer

This is a separate CLI interface for the TV File Organizer module.
It provides access to all phases of TV organization without being integrated
into the main plex-cli system.

Usage:
    python3 -m file_managers.plex.tv_organizer.cli.tv_organizer_cli [command] [options]
    
    Or using the standalone script:
    python3 tv_organizer.py [command] [options]
"""

import argparse
import sys
import logging
from pathlib import Path
from typing import Optional, List
import json
import time
from datetime import datetime, timedelta

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from file_managers.plex.tv_organizer.core.duplicate_detector import DuplicateDetector
from file_managers.plex.tv_organizer.core.path_resolver import PathResolver
from file_managers.plex.tv_organizer.models.path_resolution import ConfidenceLevel, ResolutionType
from file_managers.plex.tv_organizer.models.duplicate import DeletionMode, DeletionStatus, DeletionPlan
from file_managers.plex.config.config import config


class CLIDuplicateDetector(DuplicateDetector):
    """
    CLI-aware duplicate detector that can handle user confirmations.
    """
    
    def __init__(self, tv_directories=None, force_mode=False):
        super().__init__(tv_directories)
        self.force_mode = force_mode
    
    def _confirm_deletion(self, operation) -> bool:
        """
        Get user confirmation for deletion operation.
        
        Args:
            operation: DeletionOperation to confirm
            
        Returns:
            True if user confirms, False otherwise
        """
        if self.force_mode:
            return True
        
        print(f"\n⚠️  Confirm deletion:")
        print(f"   File: {operation.episode.filename}")
        print(f"   Size: {operation.episode.size_mb:.1f} MB")
        print(f"   Reason: {operation.reason}")
        print(f"   Mode: {operation.deletion_mode.value}")
        
        if operation.safety_warnings:
            print(f"   Warnings:")
            for warning in operation.safety_warnings:
                print(f"     • {warning}")
        
        while True:
            try:
                response = input("   Delete this file? [y/N/a/q]: ").strip().lower()
                if response in ['y', 'yes']:
                    return True
                elif response in ['n', 'no', '']:
                    return False
                elif response in ['a', 'all']:
                    self.force_mode = True
                    return True
                elif response in ['q', 'quit']:
                    raise KeyboardInterrupt("User quit deletion process")
                else:
                    print("   Please enter y(es), n(o), a(ll), or q(uit)")
            except (KeyboardInterrupt, EOFError):
                print("\n   Deletion cancelled by user")
                raise KeyboardInterrupt("User cancelled deletion")


class TVOrganizerCLI:
    """
    Standalone CLI for TV File Organizer.
    """
    
    def __init__(self):
        """Initialize the CLI."""
        self.logger = self._setup_logging()
    
    def _setup_logging(self, verbose: bool = False) -> logging.Logger:
        """Setup logging configuration."""
        level = logging.DEBUG if verbose else logging.INFO
        logging.basicConfig(
            level=level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(sys.stdout)
            ]
        )
        return logging.getLogger(__name__)
    
    def create_parser(self) -> argparse.ArgumentParser:
        """Create the main argument parser."""
        parser = argparse.ArgumentParser(
            prog='tv-organizer',
            description='TV File Organizer - Intelligent TV episode management',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog=self._get_help_epilog()
        )
        
        parser.add_argument(
            '--version',
            action='version',
            version='TV Organizer v0.2.0 (Phase 0-2 Complete)'
        )
        
        parser.add_argument(
            '-v', '--verbose',
            action='store_true',
            help='Enable verbose output and debug logging'
        )
        
        parser.add_argument(
            '--directories',
            nargs='+',
            help='Custom TV directories to scan (overrides config)'
        )
        
        # Create subcommands
        subparsers = parser.add_subparsers(
            dest='command',
            title='Commands',
            description='Available TV organizer commands',
            help='Use --help with any command for detailed information'
        )
        
        # Phase 0: Duplicate detection
        self._add_duplicate_commands(subparsers)
        
        # Future phases (placeholders)
        self._add_future_commands(subparsers)
        
        # Utility commands
        self._add_utility_commands(subparsers)
        
        return parser
    
    def _add_duplicate_commands(self, subparsers):
        """Add duplicate detection commands."""
        duplicates_parser = subparsers.add_parser(
            'duplicates',
            aliases=['dup', 'd'],
            help='Phase 0: Detect duplicate episodes',
            description='Scan TV directories and identify duplicate episodes'
        )
        
        duplicates_parser.add_argument(
            '--scan',
            action='store_true',
            help='Scan directories and detect duplicates'
        )
        
        duplicates_parser.add_argument(
            '--report',
            action='store_true',
            help='Generate detailed duplicate report'
        )
        
        duplicates_parser.add_argument(
            '--stats',
            action='store_true',
            help='Show duplicate statistics summary'
        )
        
        duplicates_parser.add_argument(
            '--show',
            type=str,
            help='Show duplicates for specific show name'
        )
        
        duplicates_parser.add_argument(
            '--output',
            type=str,
            default='reports/tv/duplicate_report.txt',
            help='Output file for duplicate report (default: reports/tv/duplicate_report.txt)'
        )
        
        duplicates_parser.add_argument(
            '--format',
            choices=['text', 'json'],
            default='text',
            help='Output format for reports (default: text)'
        )
        
        # Deletion options
        duplicates_parser.add_argument(
            '--delete',
            action='store_true',
            help='Enable deletion mode (requires --mode)'
        )
        
        duplicates_parser.add_argument(
            '--mode',
            choices=['dry-run', 'trash', 'permanent'],
            default='dry-run',
            help='Deletion mode: dry-run (preview), trash (safe), permanent (dangerous)'
        )
        
        duplicates_parser.add_argument(
            '--confidence',
            type=float,
            default=80.0,
            help='Minimum confidence score for deletion (0-100, default: 80)'
        )
        
        duplicates_parser.add_argument(
            '--force',
            action='store_true',
            help='Skip confirmations (dangerous! Use with extreme caution)'
        )
        
    
    def _add_future_commands(self, subparsers):
        """Add placeholder commands for future phases."""
        # Phase 1: Loose episode detection (planned)
        loose_parser = subparsers.add_parser(
            'loose',
            aliases=['l'],
            help='Phase 1: Loose episode detection (🚧 Coming Soon)',
            description='Identify episodes not properly organized in show folders'
        )
        
        loose_parser.add_argument(
            '--scan',
            action='store_true',
            help='🚧 Phase 1 - Not yet implemented'
        )
        
        # Phase 2: Path resolution (available)
        resolve_parser = subparsers.add_parser(
            'resolve',
            aliases=['r'],
            help='Phase 2: Path resolution - Determine optimal destinations',
            description='Analyze TV directory structure and resolve optimal destinations for episodes'
        )
        
        resolve_parser.add_argument(
            '--analyze',
            action='store_true',
            help='Analyze directory structure and show path resolution recommendations'
        )
        
        resolve_parser.add_argument(
            '--scan',
            action='store_true',
            help='Scan directories and generate path resolution plan'
        )
        
        resolve_parser.add_argument(
            '--report',
            action='store_true',
            help='Generate detailed path resolution report'
        )
        
        resolve_parser.add_argument(
            '--stats',
            action='store_true',
            help='Show directory organization statistics'
        )
        
        resolve_parser.add_argument(
            '--show',
            type=str,
            help='Show path resolution for specific show name'
        )
        
        resolve_parser.add_argument(
            '--confidence',
            choices=['high', 'medium', 'low', 'all'],
            default='all',
            help='Filter resolutions by confidence level (default: all)'
        )
        
        resolve_parser.add_argument(
            '--output',
            type=str,
            default='reports/tv/path_resolution_report.txt',
            help='Output file for resolution report (default: reports/tv/path_resolution_report.txt)'
        )
        
        resolve_parser.add_argument(
            '--format',
            choices=['text', 'json'],
            default='text',
            help='Output format for reports (default: text)'
        )
    
        # Phase 3: Organization execution (planned)
        organize_parser = subparsers.add_parser(
            'organize',
            aliases=['org', 'o'],
            help='Phase 3: Organization execution (🚧 Coming Soon)',
            description='Execute file organization with safety checks'
        )
        
        organize_parser.add_argument(
            '--execute',
            action='store_true',
            help='🚧 Phase 3 - Not yet implemented'
        )
        
        organize_parser.add_argument(
            '--dry-run',
            action='store_true',
            help='🚧 Phase 3 - Not yet implemented'
        )
    
    def _add_utility_commands(self, subparsers):
        """Add utility commands."""
        # Config command
        config_parser = subparsers.add_parser(
            'config',
            aliases=['cfg'],
            help='Show configuration information',
            description='Display TV organizer configuration'
        )
        
        config_parser.add_argument(
            '--show',
            action='store_true',
            help='Show current configuration'
        )
        
        # Status command
        status_parser = subparsers.add_parser(
            'status',
            aliases=['stat'],
            help='Show TV organizer status',
            description='Display current status and phase information'
        )
    
    def _get_help_epilog(self) -> str:
        """Get help epilog with examples."""
        return """
Examples:
  # Phase 0: Enhanced Duplicate Detection (Available)
  python3 tv_organizer.py duplicates --scan --report         # Scan and generate report
  python3 tv_organizer.py duplicates --stats                 # Show statistics only
  python3 tv_organizer.py duplicates --show "Breaking Bad"   # Show duplicates for specific show
  python3 tv_organizer.py dup --format json --output dups.json  # JSON format output
  
  # Duplicate Deletion (Available)
  python3 tv_organizer.py duplicates --scan --delete --mode dry-run    # Preview deletions (safe)
  python3 tv_organizer.py duplicates --scan --delete --mode trash      # Move duplicates to trash
  python3 tv_organizer.py duplicates --scan --delete --mode permanent  # Permanent deletion (dangerous!)
  python3 tv_organizer.py dup --delete --mode trash --confidence 90    # High confidence deletion only
  
  # Phase 1: Loose Episode Detection (Coming Soon)
  python3 tv_organizer.py loose --scan                       # 🚧 Phase 1 - Not implemented
  
  # Phase 2: Path Resolution (Available)
  python3 tv_organizer.py resolve --analyze --report         # Analyze directory structure and generate report
  python3 tv_organizer.py resolve --stats                    # Show organization statistics
  python3 tv_organizer.py resolve --scan --confidence high   # Show high confidence resolutions
  python3 tv_organizer.py resolve --show "Breaking Bad"      # Show path resolution for specific show
  
  # Phase 3: Organization Execution (Coming Soon)
  python3 tv_organizer.py organize --dry-run                 # 🚧 Phase 3 - Not implemented
  
  # Utility Commands
  python3 tv_organizer.py config --show                      # Show configuration
  python3 tv_organizer.py status                             # Show status and phase info
  
  # Custom directories
  python3 tv_organizer.py duplicates --scan --directories /path/to/tv1 /path/to/tv2

Phase Status:
  ✅ Phase 0: Duplicate Detection - Complete and tested
  🚧 Phase 1: Loose Episode Detection - Planned
  ✅ Phase 2: Path Resolution - Complete and tested
  🚧 Phase 3: Organization Execution - Planned

Configuration:
  TV directories are loaded from: file_managers/plex/config/media_config.yaml
  Default directories: {directories}
        """.format(directories=', '.join(config.tv_directories))
    
    def run_duplicates_command(self, args) -> int:
        """Run duplicate detection commands."""
        start_time = time.time()
        self._start_time = start_time  # Store for report generation
        start_datetime = datetime.now()
        
        print("🔍 TV File Organizer - Phase 0: Duplicate Detection")
        print("=" * 60)
        
        # Get directories
        directories = args.directories or config.tv_directories
        print(f"📁 TV Directories: {len(directories)}")
        for i, directory in enumerate(directories, 1):
            print(f"  {i}. {directory}")
        print()
        
        # Initialize enhanced duplicate detector
        print(f"🔍 Using Enhanced Duplicate Detection")
        print("   ✅ False positive filtering enabled")
        print("   ✅ Content analysis enabled")
        print("   ✅ Confidence scoring enabled")
        print()
        
        # Initialize detector
        force_mode = getattr(args, 'force', False)
        detector = CLIDuplicateDetector(directories, force_mode=force_mode)
        
        try:
            # Always scan first
            if args.scan or args.report or args.stats or args.show:
                print("🔍 Scanning directories for episodes...")
                episodes = detector.scan_all_directories()
                print(f"✅ Found {len(episodes)} total episodes")
                
                print("🔍 Detecting duplicates...")
                duplicate_groups = detector.detect_duplicates()
                print(f"⚠️  Found {len(duplicate_groups)} duplicate groups")
                print()
            
            # Show statistics
            if args.stats or args.scan:
                stats = detector.get_duplicate_statistics()
                self._print_duplicate_stats(stats)
            
            # Show specific show
            if args.show:
                self._show_duplicates_for_show(detector, args.show)
            
            # Handle deletion mode
            if args.delete:
                return self._handle_deletion(detector, args)
            
            # Generate report
            if args.report or (args.scan and not args.stats and not args.show):
                self._generate_duplicate_report(detector, args.output, args.format)
            
            return 0
            
        except Exception as e:
            print(f"❌ Error: {e}")
            if args.verbose:
                import traceback
                traceback.print_exc()
            return 1
    
    def _print_duplicate_stats(self, stats: dict):
        """Print duplicate statistics."""
        print("📊 Duplicate Statistics:")
        print(f"  • Total episodes scanned: {stats.get('total_episodes', 'N/A')}")
        print(f"  • Duplicate groups found: {stats['total_duplicate_groups']}")
        print(f"  • Total duplicate files: {stats['total_duplicate_files']}")
        print(f"  • Space used by duplicates: {stats['total_space_used_gb']:.2f} GB")
        print(f"  • Potential space savings: {stats['potential_space_saved_gb']:.2f} GB")
        print(f"  • Space efficiency gain: {stats['space_efficiency']:.1f}%")
        print()
    
    def _show_duplicates_for_show(self, detector: DuplicateDetector, show_name: str):
        """Show duplicates for a specific show."""
        print(f"🎬 Duplicates for '{show_name}':")
        print("-" * 40)
        
        show_groups = detector.get_duplicates_for_show(show_name)
        
        if not show_groups:
            print(f"✅ No duplicates found for '{show_name}'")
            return
        
        for i, group in enumerate(show_groups, 1):
            print(f"\n{i}. {group.get_summary()}")
            print(f"   Recommended action: {group.recommended_action.value}")
            
            if group.recommended_keeper:
                print(f"   Keep: {group.recommended_keeper.filename}")
                print(f"         ({group.recommended_keeper.quality.value}, "
                      f"{group.recommended_keeper.size_mb:.1f}MB)")
            
            if group.recommended_removals:
                print("   Remove:")
                for episode in group.recommended_removals:
                    print(f"     - {episode.filename}")
                    print(f"       ({episode.quality.value}, {episode.size_mb:.1f}MB)")
        print()
    
    def _generate_duplicate_report(self, detector: DuplicateDetector, output_file: str, format_type: str):
        """Generate and save duplicate report."""
        print(f"📋 Generating duplicate report...")
        
        if format_type == 'json':
            self._generate_json_report(detector, output_file)
        else:
            self._generate_text_report(detector, output_file)
    
    def _generate_text_report(self, detector, output_file: str):
        """Generate text format report."""
        # Ensure reports/tv directory exists
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Generate enhanced report
        report = detector.generate_enhanced_report()
        
        # Add runtime information
        end_time = time.time()
        start_time = getattr(self, '_start_time', end_time)
        runtime_seconds = end_time - start_time
        runtime_str = str(timedelta(seconds=int(runtime_seconds)))
        
        # Add runtime to end of report
        report += f"\n\nRUNTIME INFORMATION:\n"
        report += f"{'=' * 20}\n"
        report += f"Scan completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        report += f"Total runtime: {runtime_str}\n"
        
        output_path.write_text(report)
        
        print(f"✅ Text report saved to: {output_path.absolute()}")
        print(f"📄 Report size: {len(report)} characters")
        print(f"⏱️  Runtime: {runtime_str}")
    
    def _generate_json_report(self, detector: DuplicateDetector, output_file: str):
        """Generate JSON format report."""
        # Ensure reports/tv directory exists
        output_path = Path(output_file)
        if not output_file.endswith('.json'):
            output_path = output_path.with_suffix('.json')
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Calculate runtime
        end_time = time.time()
        start_time = getattr(self, '_start_time', end_time)
        runtime_seconds = end_time - start_time
        
        stats = detector.get_duplicate_statistics()
        
        json_data = {
            'metadata': {
                'tv_organizer_version': '0.1.0',
                'phase': 'Phase 0: Duplicate Detection',
                'scan_directories': detector.tv_directories,
                'total_episodes': len(detector.episodes),
                'scan_completed_at': datetime.now().isoformat(),
                'runtime_seconds': runtime_seconds,
                'runtime_formatted': str(timedelta(seconds=int(runtime_seconds)))
            },
            'statistics': stats,
            'duplicate_groups': []
        }
        
        for group in detector.duplicate_groups:
            group_data = {
                'show_name': group.show_name,
                'season': group.season,
                'episode': group.episode,
                'duplicate_count': group.duplicate_count,
                'total_size_mb': group.total_size_mb,
                'potential_space_saved_mb': group.potential_space_saved / (1024 * 1024),
                'recommended_action': group.recommended_action.value,
                'episodes': []
            }
            
            for episode in group.episodes:
                episode_data = {
                    'filename': episode.filename,
                    'file_path': str(episode.file_path),
                    'size_mb': episode.size_mb,
                    'quality': episode.quality.value,
                    'source': episode.source,
                    'is_recommended_keeper': episode == group.recommended_keeper
                }
                group_data['episodes'].append(episode_data)
            
            json_data['duplicate_groups'].append(group_data)
        
        with open(output_path, 'w') as f:
            json.dump(json_data, f, indent=2)
        
        runtime_str = str(timedelta(seconds=int(runtime_seconds)))
        print(f"✅ JSON report saved to: {output_path.absolute()}")
        print(f"📄 Report contains {len(json_data['duplicate_groups'])} duplicate groups")
        print(f"⏱️  Runtime: {runtime_str}")
    
    def run_resolve_command(self, args) -> int:
        """Run path resolution commands."""
        start_time = time.time()
        self._start_time = start_time  # Store for report generation
        start_datetime = datetime.now()
        
        print("🔍 TV File Organizer - Phase 2: Path Resolution")
        print("=" * 60)
        
        # Get directories
        directories = args.directories or config.tv_directories
        print(f"📁 TV Directories: {len(directories)}")
        for i, directory in enumerate(directories, 1):
            print(f"  {i}. {directory}")
        print()
        
        # Initialize path resolver
        print(f"🔍 Initializing Path Resolution Analysis")
        print("   ✅ Directory structure mapping enabled")
        print("   ✅ Show name fuzzy matching enabled")
        print("   ✅ Destination scoring enabled")
        print()
        
        # Initialize resolver
        resolver = PathResolver(directories)
        
        try:
            # Always scan first for analysis commands
            if args.analyze or args.scan or args.report or args.stats or args.show:
                print("🔍 Scanning TV directories...")
                episodes = resolver.scan_tv_directories()
                print(f"✅ Found {len(episodes)} total episodes")
                print(f"✅ Discovered {len(resolver.show_directories)} show directories")
                
                if args.analyze or args.scan or args.report or args.show:
                    print("🔍 Analyzing path resolutions...")
                    resolutions = resolver.resolve_episode_paths()
                    print(f"📋 Created {len(resolutions)} path resolutions")
                    
                    if resolutions:
                        plan = resolver.create_resolution_plan()
                        print(f"📊 Resolution plan: {plan.success_rate:.1f}% success rate")
                    print()
            
            # Show statistics
            if args.stats or args.analyze:
                stats = resolver.get_directory_statistics()
                self._print_resolve_stats(stats)
            
            # Show specific show
            if args.show:
                self._show_resolutions_for_show(resolver, args.show, args.confidence)
            
            # Show resolutions by confidence
            if args.scan and not args.show:
                self._show_resolutions_by_confidence(resolver, args.confidence)
            
            # Generate report
            if args.report or (args.analyze and not args.stats and not args.show):
                self._generate_resolve_report(resolver, args.output, args.format)
            
            return 0
            
        except Exception as e:
            print(f"❌ Error: {e}")
            if args.verbose:
                import traceback
                traceback.print_exc()
            return 1
    
    def _print_resolve_stats(self, stats: dict):
        """Print path resolution statistics."""
        print("📊 Directory Organization Statistics:")
        print(f"  • Total shows discovered: {stats['total_shows']}")
        print(f"  • Total episodes found: {stats['total_episodes']}")
        print(f"  • Organized episodes: {stats['organized_episodes']} ({stats['organization_percentage']:.1f}%)")
        print(f"  • Loose episodes: {stats['loose_episodes']}")
        print(f"  • Average organization score: {stats['average_show_organization_score']:.1f}/100")
        print(f"  • Shows needing attention: {stats['shows_needing_attention']}")
        print()
        
        if stats['tv_directory_usage']:
            print("📁 TV Directory Usage:")
            for tv_dir, show_count in stats['tv_directory_usage'].items():
                print(f"  • {tv_dir}: {show_count} shows")
            print()
    
    def _show_resolutions_for_show(self, resolver: PathResolver, show_name: str, confidence_filter: str):
        """Show path resolutions for a specific show."""
        print(f"🎬 Path Resolutions for '{show_name}':")
        print("-" * 50)
        
        # Find resolutions for this show
        show_resolutions = [
            r for r in resolver.resolutions 
            if show_name.lower() in ' '.join(r.show_names).lower()
        ]
        
        if not show_resolutions:
            print(f"✅ No path resolutions needed for '{show_name}'")
            return
        
        # Filter by confidence if specified
        if confidence_filter != 'all':
            confidence_map = {
                'high': ConfidenceLevel.HIGH,
                'medium': ConfidenceLevel.MEDIUM,
                'low': ConfidenceLevel.LOW
            }
            target_confidence = confidence_map.get(confidence_filter)
            if target_confidence:
                show_resolutions = [r for r in show_resolutions if r.confidence == target_confidence]
        
        if not show_resolutions:
            print(f"✅ No {confidence_filter} confidence resolutions for '{show_name}'")
            return
        
        for i, resolution in enumerate(show_resolutions, 1):
            print(f"\n{i}. {resolution.get_summary()}")
            print(f"   Resolution type: {resolution.resolution_type.value.replace('_', ' ').title()}")
            print(f"   Confidence: {resolution.confidence.value.upper()}")
            
            if resolution.primary_destination:
                print(f"   Destination: {resolution.primary_destination.path}")
                print(f"   Score: {resolution.primary_destination.total_score:.1f}/100")
            
            if resolution.reasoning:
                print("   Reasoning:")
                for reason in resolution.reasoning[:3]:  # Show first 3 reasons
                    print(f"     - {reason}")
            
            if resolution.warnings:
                print("   Warnings:")
                for warning in resolution.warnings[:2]:  # Show first 2 warnings
                    print(f"     ⚠️  {warning}")
        print()
    
    def _show_resolutions_by_confidence(self, resolver: PathResolver, confidence_filter: str):
        """Show path resolutions filtered by confidence level."""
        print(f"📋 Path Resolutions ({confidence_filter.title()} Confidence):")
        print("-" * 50)
        
        # Filter resolutions by confidence
        filtered_resolutions = resolver.resolutions
        if confidence_filter != 'all':
            confidence_map = {
                'high': ConfidenceLevel.HIGH,
                'medium': ConfidenceLevel.MEDIUM,
                'low': ConfidenceLevel.LOW
            }
            target_confidence = confidence_map.get(confidence_filter)
            if target_confidence:
                filtered_resolutions = [r for r in resolver.resolutions if r.confidence == target_confidence]
        
        if not filtered_resolutions:
            print(f"✅ No {confidence_filter} confidence resolutions found")
            return
        
        # Group by confidence for display
        by_confidence = {}
        for resolution in filtered_resolutions:
            conf = resolution.confidence.value
            if conf not in by_confidence:
                by_confidence[conf] = []
            by_confidence[conf].append(resolution)
        
        # Display each confidence group
        for confidence, resolutions in by_confidence.items():
            print(f"\n🎯 {confidence.upper()} CONFIDENCE ({len(resolutions)} resolutions):")
            
            for i, resolution in enumerate(resolutions[:5], 1):  # Show first 5
                print(f"  {i}. {resolution.get_summary()}")
                if resolution.primary_destination:
                    print(f"     → {resolution.primary_destination.path}")
            
            if len(resolutions) > 5:
                print(f"     ... and {len(resolutions) - 5} more")
        print()
    
    def _generate_resolve_report(self, resolver: PathResolver, output_file: str, format_type: str):
        """Generate and save path resolution report."""
        print(f"📋 Generating path resolution report...")
        
        if format_type == 'json':
            self._generate_resolve_json_report(resolver, output_file)
        else:
            self._generate_resolve_text_report(resolver, output_file)
    
    def _generate_resolve_text_report(self, resolver: PathResolver, output_file: str):
        """Generate text format path resolution report."""
        # Ensure reports/tv directory exists
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Generate comprehensive report
        report = resolver.generate_resolution_report()
        
        # Add detailed resolutions
        if resolver.resolutions:
            report += "\n\nDETAILED PATH RESOLUTIONS:\n"
            report += "=" * 30 + "\n\n"
            
            # Group by confidence
            by_confidence = {}
            for resolution in resolver.resolutions:
                conf = resolution.confidence.value
                if conf not in by_confidence:
                    by_confidence[conf] = []
                by_confidence[conf].append(resolution)
            
            for confidence in ['high', 'medium', 'low', 'uncertain']:
                if confidence in by_confidence:
                    resolutions = by_confidence[confidence]
                    report += f"{confidence.upper()} CONFIDENCE RESOLUTIONS ({len(resolutions)}):\n"
                    report += "-" * 40 + "\n"
                    
                    for i, resolution in enumerate(resolutions, 1):
                        report += f"\n{i}. {resolution.get_summary()}\n"
                        report += f"   Type: {resolution.resolution_type.value.replace('_', ' ').title()}\n"
                        
                        if resolution.primary_destination:
                            dest = resolution.primary_destination
                            report += f"   Destination: {dest.path}\n"
                            report += f"   Score: {dest.total_score:.1f}/100\n"
                            
                            if dest.requires_creation:
                                report += f"   Note: Requires directory creation\n"
                        
                        if resolution.reasoning:
                            report += f"   Reasoning:\n"
                            for reason in resolution.reasoning:
                                report += f"     - {reason}\n"
                        
                        if resolution.warnings:
                            report += f"   Warnings:\n"
                            for warning in resolution.warnings:
                                report += f"     ⚠️  {warning}\n"
                    
                    report += "\n"
        
        # Add runtime information
        end_time = time.time()
        start_time = getattr(self, '_start_time', end_time)
        runtime_seconds = end_time - start_time
        runtime_str = str(timedelta(seconds=int(runtime_seconds)))
        
        report += f"\nRUNTIME INFORMATION:\n"
        report += f"{'=' * 20}\n"
        report += f"Analysis completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        report += f"Total runtime: {runtime_str}\n"
        
        output_path.write_text(report)
        
        print(f"✅ Text report saved to: {output_path.absolute()}")
        print(f"📄 Report size: {len(report)} characters")
        print(f"⏱️  Runtime: {runtime_str}")
    
    def _generate_resolve_json_report(self, resolver: PathResolver, output_file: str):
        """Generate JSON format path resolution report."""
        # Ensure reports/tv directory exists
        output_path = Path(output_file)
        if not output_file.endswith('.json'):
            output_path = output_path.with_suffix('.json')
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Calculate runtime
        end_time = time.time()
        start_time = getattr(self, '_start_time', end_time)
        runtime_seconds = end_time - start_time
        
        stats = resolver.get_directory_statistics()
        
        json_data = {
            'metadata': {
                'tv_organizer_version': '0.2.0',
                'phase': 'Phase 2: Path Resolution',
                'scan_directories': resolver.tv_directories,
                'total_episodes': len(resolver.episodes),
                'total_shows': len(resolver.show_directories),
                'scan_completed_at': datetime.now().isoformat(),
                'runtime_seconds': runtime_seconds,
                'runtime_formatted': str(timedelta(seconds=int(runtime_seconds)))
            },
            'directory_statistics': stats,
            'show_directories': [],
            'path_resolutions': []
        }
        
        # Add show directories
        for show_dir in resolver.show_directories.values():
            show_data = {
                'show_name': show_dir.actual_name,
                'normalized_name': show_dir.normalized_name,
                'path': str(show_dir.path),
                'tv_base_directory': str(show_dir.tv_base_directory),
                'total_episodes': show_dir.total_episodes,
                'total_size_gb': show_dir.total_size_gb,
                'organization_score': show_dir.organization_score,
                'seasons_present': list(show_dir.seasons_present),
                'has_mixed_structure': show_dir.has_mixed_structure,
                'season_folders': [str(p) for p in show_dir.season_folders]
            }
            json_data['show_directories'].append(show_data)
        
        # Add path resolutions
        for resolution in resolver.resolutions:
            resolution_data = {
                'episodes': [
                    {
                        'filename': ep.filename,
                        'file_path': str(ep.file_path),
                        'show_name': ep.show_name,
                        'season': ep.season,
                        'episode': ep.episode,
                        'size_gb': ep.size_gb,
                        'quality': ep.quality.value,
                        'status': ep.status.value
                    }
                    for ep in resolution.episodes
                ],
                'resolution_type': resolution.resolution_type.value,
                'confidence': resolution.confidence.value,
                'episode_count': resolution.episode_count,
                'total_size_gb': resolution.total_size_gb,
                'show_names': list(resolution.show_names),
                'seasons_involved': list(resolution.seasons_involved),
                'is_executable': resolution.is_executable,
                'reasoning': resolution.reasoning,
                'warnings': resolution.warnings,
                'requires_user_confirmation': resolution.requires_user_confirmation,
                'estimated_time_seconds': resolution.estimated_time_seconds,
                'estimated_space_needed_gb': resolution.estimated_space_needed_gb
            }
            
            if resolution.primary_destination:
                dest = resolution.primary_destination
                resolution_data['primary_destination'] = {
                    'path': str(dest.path),
                    'destination_type': dest.destination_type.value,
                    'season_number': dest.season_number,
                    'match_score': dest.match_score,
                    'organization_score': dest.organization_score,
                    'space_score': dest.space_score,
                    'proximity_score': dest.proximity_score,
                    'total_score': dest.total_score,
                    'confidence_level': dest.confidence_level.value,
                    'requires_creation': dest.requires_creation,
                    'conflicts': dest.conflicts,
                    'available_space_gb': dest.available_space_gb
                }
            
            json_data['path_resolutions'].append(resolution_data)
        
        with open(output_path, 'w') as f:
            json.dump(json_data, f, indent=2)
        
        runtime_str = str(timedelta(seconds=int(runtime_seconds)))
        print(f"✅ JSON report saved to: {output_path.absolute()}")
        print(f"📄 Report contains {len(json_data['path_resolutions'])} path resolutions")
        print(f"⏱️  Runtime: {runtime_str}")
    
    def run_config_command(self, args) -> int:
        """Run configuration commands."""
        if args.show:
            print("🔧 TV File Organizer Configuration")
            print("=" * 40)
            print(f"TV Directories ({len(config.tv_directories)}):")
            for i, directory in enumerate(config.tv_directories, 1):
                print(f"  {i}. {directory}")
            
            print(f"\nVideo Extensions: {', '.join(list(config.video_extensions_set)[:10])}")
            if len(config.video_extensions_set) > 10:
                print(f"  ... and {len(config.video_extensions_set) - 10} more")
            
            print(f"Small Folder Threshold: {config.small_folder_threshold_mb} MB")
        
        return 0
    
    def run_status_command(self, args) -> int:
        """Run status command."""
        print("📊 TV File Organizer Status")
        print("=" * 30)
        print("Version: 0.2.0")
        print()
        print("Development Phases:")
        print("  ✅ Phase 0: Duplicate Detection - Complete")
        print("  🚧 Phase 1: Loose Episode Detection - Planned")
        print("  ✅ Phase 2: Path Resolution - Complete")
        print("  🚧 Phase 3: Organization Execution - Planned")
        print()
        print("Available Commands:")
        print("  • duplicates - Detect and analyze duplicate episodes")
        print("  • resolve - Analyze directory structure and determine optimal destinations")
        print("  • config - Show configuration")
        print("  • status - Show this status information")
        print()
        print("Coming Soon:")
        print("  • loose - Find episodes not properly organized")
        print("  • organize - Execute file organization")
        
        return 0
    
    def run_future_command(self, command_name: str) -> int:
        """Run placeholder for future commands."""
        phase_map = {
            'loose': 'Phase 1: Loose Episode Detection',
            'resolve': 'Phase 2: Path Resolution',
            'organize': 'Phase 3: Organization Execution'
        }
        
        phase = phase_map.get(command_name, f"Phase for {command_name}")
        
        print(f"🚧 {phase}")
        print("=" * 50)
        print(f"The '{command_name}' command is not yet implemented.")
        print()
        print("Current Status:")
        print("  ✅ Phase 0: Duplicate Detection - Available now")
        print(f"  🚧 {phase} - Coming soon")
        print()
        print("Available Commands:")
        print("  tv-organizer duplicates --scan --report")
        print("  tv-organizer resolve --analyze --report")
        print("  tv-organizer config --show")
        print("  tv-organizer status")
        
        return 0
    
    def _handle_deletion(self, detector: DuplicateDetector, args) -> int:
        """
        Handle deletion mode operations.
        
        Args:
            detector: DuplicateDetector instance with duplicates already found
            args: Parsed command line arguments
            
        Returns:
            Exit code (0 for success, 1 for error)
        """
        print("\n💥 DUPLICATE DELETION MODE")
        print("=" * 50)
        
        # Convert deletion mode string to enum
        mode_mapping = {
            'dry-run': DeletionMode.DRY_RUN,
            'trash': DeletionMode.TRASH,
            'permanent': DeletionMode.PERMANENT
        }
        
        deletion_mode = mode_mapping.get(args.mode)
        if not deletion_mode:
            print(f"❌ Invalid deletion mode: {args.mode}")
            print(f"   Valid modes: {', '.join(mode_mapping.keys())}")
            return 1
        
        print(f"🔧 Mode: {deletion_mode.value.upper()}")
        print(f"🎯 Minimum Confidence: {args.confidence}%")
        if args.force:
            print("⚠️  FORCE MODE: Confirmations will be skipped!")
        print()
        
        # Create deletion plan
        print("📋 Creating deletion plan...")
        try:
            plan = detector.create_deletion_plan(
                deletion_mode=deletion_mode,
                min_confidence_score=args.confidence
            )
        except Exception as e:
            print(f"❌ Error creating deletion plan: {e}")
            return 1
        
        # Show plan summary
        print(f"✅ Deletion plan created:")
        print(f"   Total operations: {plan.total_files}")
        print(f"   Safe operations: {len(plan.safe_operations)}")
        print(f"   Unsafe operations: {len(plan.unsafe_operations)}")
        print(f"   Estimated space to free: {plan.estimated_space_saved_mb:.1f} MB")
        print()
        
        # Show detailed plan information
        if plan.total_files == 0:
            print("ℹ️  No files found for deletion with current confidence threshold.")
            print(f"   Try lowering --confidence from {args.confidence} or check if duplicates exist.")
            return 0
        
        if len(plan.unsafe_operations) > 0:
            print(f"⚠️  {len(plan.unsafe_operations)} unsafe operations detected:")
            for i, op in enumerate(plan.unsafe_operations[:5], 1):
                print(f"   {i}. {op.episode.filename} - Safety issues:")
                for warning in op.safety_warnings:
                    print(f"      • {warning}")
            if len(plan.unsafe_operations) > 5:
                print(f"      ... and {len(plan.unsafe_operations) - 5} more")
            print()
        
        # For dry-run mode, just show what would be deleted
        if deletion_mode == DeletionMode.DRY_RUN:
            print("🔍 DRY RUN MODE - No files will be deleted")
            print("-" * 40)
            self._show_deletion_preview(plan)
            return 0
        
        # For actual deletion modes, require confirmation
        if not args.force:
            print("⚠️  DELETION CONFIRMATION REQUIRED")
            print("-" * 35)
            print(f"Mode: {deletion_mode.value.upper()}")
            print(f"Files to delete: {len(plan.safe_operations)}")
            print(f"Space to free: {plan.estimated_space_saved_mb:.1f} MB")
            print()
            
            if deletion_mode == DeletionMode.PERMANENT:
                print("🚨 WARNING: PERMANENT DELETION MODE")
                print("   Files will be PERMANENTLY DELETED and CANNOT be recovered!")
                print("   This operation is IRREVERSIBLE!")
                print()
            
            # Show preview of what will be deleted
            self._show_deletion_preview(plan, max_items=10)
            
            # Get user confirmation
            if not self._confirm_deletion_plan(plan, deletion_mode):
                print("❌ Deletion cancelled by user")
                return 0
        
        # Execute deletion plan
        print(f"\n🚀 Executing deletion plan with {len(plan.safe_operations)} operations...")
        print("-" * 50)
        
        # Create a progress callback
        def progress_callback(current: int, total: int, operation):
            percent = (current / total) * 100 if total > 0 else 0
            print(f"[{percent:5.1f}%] {operation.get_summary()}")
        
        try:
            # Execute the plan
            result_plan = detector.execute_deletion_plan(
                plan, 
                force=args.force, 
                progress_callback=progress_callback
            )
            
            # Show execution results
            print("\n✅ Deletion execution completed")
            print("=" * 35)
            
            status_summary = result_plan.get_status_summary()
            for status, count in status_summary.items():
                icon = {
                    'success': '✅',
                    'failed': '❌',
                    'skipped': '⏭️',
                    'cancelled': '🚫'
                }.get(status, '❓')
                print(f"  {icon} {status.title()}: {count}")
            
            print(f"\n📊 Final Statistics:")
            print(f"   Success rate: {result_plan.success_rate:.1f}%")
            if result_plan.execution_duration:
                print(f"   Execution time: {result_plan.execution_duration:.1f} seconds")
            
            # Generate deletion report
            report_path = f"reports/tv/deletion_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            self._save_deletion_report(detector, result_plan, report_path)
            
            return 0 if result_plan.success_rate > 80 else 1
            
        except Exception as e:
            print(f"❌ Error during deletion execution: {e}")
            if args.verbose:
                import traceback
                traceback.print_exc()
            return 1
    
    def _show_deletion_preview(self, plan: DeletionPlan, max_items: int = 20):
        """Show preview of files that will be deleted."""
        safe_ops = plan.safe_operations
        
        print(f"📋 FILES TO BE PROCESSED ({len(safe_ops)} files):")
        print("-" * 40)
        
        # Group by show for better organization
        by_show = {}
        for op in safe_ops:
            show = op.episode.show_name
            if show not in by_show:
                by_show[show] = []
            by_show[show].append(op)
        
        shown = 0
        for show, operations in sorted(by_show.items()):
            if shown >= max_items:
                break
                
            print(f"\n📺 {show} ({len(operations)} files):")
            for i, op in enumerate(operations[:5], 1):  # Max 5 per show
                if shown >= max_items:
                    break
                    
                print(f"   {i}. {op.episode.filename}")
                print(f"      Size: {op.episode.size_mb:.1f}MB | Reason: {op.reason}")
                shown += 1
            
            if len(operations) > 5:
                remaining = len(operations) - 5
                print(f"      ... and {remaining} more files")
        
        if len(safe_ops) > max_items:
            print(f"\n... and {len(safe_ops) - max_items} more files")
        
        print(f"\n💾 Total space to be freed: {plan.estimated_space_saved_mb:.1f} MB")
    
    def _confirm_deletion_plan(self, plan: DeletionPlan, deletion_mode: DeletionMode) -> bool:
        """Get user confirmation for deletion plan."""
        
        # Different confirmation phrases based on mode
        if deletion_mode == DeletionMode.PERMANENT:
            required_phrase = "PERMANENTLY DELETE"
            prompt = f"Type '{required_phrase}' to confirm PERMANENT deletion: "
        else:
            required_phrase = "DELETE FILES"
            prompt = f"Type '{required_phrase}' to confirm deletion: "
        
        print(f"\n⚠️  Confirmation required to proceed")
        print(f"   Type exactly: {required_phrase}")
        print(f"   Or press Ctrl+C to cancel")
        print()
        
        try:
            user_input = input(prompt).strip()
            return user_input == required_phrase
        except (KeyboardInterrupt, EOFError):
            return False
    
    def _save_deletion_report(self, detector: DuplicateDetector, plan: DeletionPlan, output_path: str):
        """Save deletion report to file."""
        try:
            # Ensure directory exists
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            
            # Generate report
            report = detector.generate_deletion_report(plan)
            
            # Save to file
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(report)
            
            print(f"\n📄 Deletion report saved: {output_path}")
            
        except Exception as e:
            print(f"⚠️  Warning: Could not save deletion report: {e}")
    
    def main(self, args: Optional[List[str]] = None) -> int:
        """Main CLI entry point."""
        parser = self.create_parser()
        parsed_args = parser.parse_args(args)
        
        # Setup verbose logging if requested
        if parsed_args.verbose:
            self._setup_logging(verbose=True)
        
        # Handle no command
        if not parsed_args.command:
            parser.print_help()
            return 0
        
        # Route to command handlers
        try:
            if parsed_args.command in ['duplicates', 'dup', 'd']:
                return self.run_duplicates_command(parsed_args)
            elif parsed_args.command in ['loose', 'l']:
                return self.run_future_command('loose')
            elif parsed_args.command in ['resolve', 'r']:
                return self.run_resolve_command(parsed_args)
            elif parsed_args.command in ['config', 'cfg']:
                return self.run_config_command(parsed_args)
            elif parsed_args.command in ['status', 'stat']:
                return self.run_status_command(parsed_args)
            elif parsed_args.command in ['organize', 'org', 'o']:
                return self.run_future_command(parsed_args.command)
            else:
                print(f"❌ Unknown command: {parsed_args.command}")
                parser.print_help()
                return 1
                
        except KeyboardInterrupt:
            print("\n⚠️  Operation cancelled by user")
            return 1
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            if parsed_args.verbose:
                import traceback
                traceback.print_exc()
            return 1


def main():
    """Entry point for standalone script."""
    cli = TVOrganizerCLI()
    return cli.main()


if __name__ == "__main__":
    sys.exit(main())