#!/usr/bin/env python3
"""
Standalone CLI for TV File Organizer

This is a separate CLI interface for the TV File Organizer module.
It provides access to all phases of TV organization without being integrated
into the main plex-cli system.

Usage:
    python -m file_managers.plex.tv_organizer.cli.tv_organizer_cli [command] [options]
    
    Or using the standalone script:
    python tv_organizer.py [command] [options]
"""

import argparse
import sys
import logging
from pathlib import Path
from typing import Optional, List
import json

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from file_managers.plex.tv_organizer.core.duplicate_detector import DuplicateDetector
from file_managers.plex.tv_organizer.core.loose_episode_finder import LooseEpisodeFinder
from file_managers.plex.config.config import config


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
            version='TV Organizer v0.1.0 (Phase 0 Complete)'
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
        
        # Phase 1: Loose episode detection (placeholder)
        self._add_loose_commands(subparsers)
        
        # Phase 2: Path resolution (placeholder)
        self._add_resolve_commands(subparsers)
        
        # Phase 3: Organization execution (placeholder)
        self._add_organize_commands(subparsers)
        
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
            default='tv_duplicate_report.txt',
            help='Output file for duplicate report (default: tv_duplicate_report.txt)'
        )
        
        duplicates_parser.add_argument(
            '--format',
            choices=['text', 'json'],
            default='text',
            help='Output format for reports (default: text)'
        )
    
    def _add_loose_commands(self, subparsers):
        """Add loose episode detection commands (Phase 1 - placeholder)."""
        loose_parser = subparsers.add_parser(
            'loose',
            aliases=['l'],
            help='Phase 1: Find loose episodes (🚧 Coming Soon)',
            description='Identify episodes not properly organized in show folders'
        )
        
        loose_parser.add_argument(
            '--scan',
            action='store_true',
            help='🚧 Phase 1 - Not yet implemented'
        )
    
    def _add_resolve_commands(self, subparsers):
        """Add path resolution commands (Phase 2 - placeholder)."""
        resolve_parser = subparsers.add_parser(
            'resolve',
            aliases=['r'],
            help='Phase 2: Resolve episode paths (🚧 Coming Soon)',
            description='Determine correct destinations for loose episodes'
        )
        
        resolve_parser.add_argument(
            '--analyze',
            action='store_true',
            help='🚧 Phase 2 - Not yet implemented'
        )
    
    def _add_organize_commands(self, subparsers):
        """Add organization execution commands (Phase 3 - placeholder)."""
        organize_parser = subparsers.add_parser(
            'organize',
            aliases=['org', 'o'],
            help='Phase 3: Execute organization (🚧 Coming Soon)',
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
  # Phase 0: Duplicate Detection (Available)
  tv-organizer duplicates --scan --report         # Scan and generate report
  tv-organizer duplicates --stats                 # Show statistics only
  tv-organizer duplicates --show "Breaking Bad"   # Show duplicates for specific show
  tv-organizer dup --format json --output dups.json  # JSON format output
  
  # Phase 1-3: Future Commands (Coming Soon)
  tv-organizer loose --scan                       # 🚧 Phase 1 - Not implemented
  tv-organizer resolve --analyze                  # 🚧 Phase 2 - Not implemented  
  tv-organizer organize --dry-run                 # 🚧 Phase 3 - Not implemented
  
  # Utility Commands
  tv-organizer config --show                      # Show configuration
  tv-organizer status                             # Show status and phase info
  
  # Custom directories
  tv-organizer duplicates --scan --directories /path/to/tv1 /path/to/tv2

Phase Status:
  ✅ Phase 0: Duplicate Detection - Complete and tested
  🚧 Phase 1: Loose Episode Detection - Planned
  🚧 Phase 2: Path Resolution - Planned
  🚧 Phase 3: Organization Execution - Planned

Configuration:
  TV directories are loaded from: file_managers/plex/config/media_config.yaml
  Default directories: {directories}
        """.format(directories=', '.join(config.tv_directories))
    
    def run_duplicates_command(self, args) -> int:
        """Run duplicate detection commands."""
        print("🔍 TV File Organizer - Phase 0: Duplicate Detection")
        print("=" * 60)
        
        # Get directories
        directories = args.directories or config.tv_directories
        print(f"📁 TV Directories: {len(directories)}")
        for i, directory in enumerate(directories, 1):
            print(f"  {i}. {directory}")
        print()
        
        # Initialize detector
        detector = DuplicateDetector(directories)
        
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
    
    def _generate_text_report(self, detector: DuplicateDetector, output_file: str):
        """Generate text format report."""
        report = detector.generate_report()
        
        output_path = Path(output_file)
        output_path.write_text(report)
        
        print(f"✅ Text report saved to: {output_path.absolute()}")
        print(f"📄 Report size: {len(report)} characters")
    
    def _generate_json_report(self, detector: DuplicateDetector, output_file: str):
        """Generate JSON format report."""
        stats = detector.get_duplicate_statistics()
        
        json_data = {
            'metadata': {
                'tv_organizer_version': '0.1.0',
                'phase': 'Phase 0: Duplicate Detection',
                'scan_directories': detector.tv_directories,
                'total_episodes': len(detector.episodes)
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
        
        # Save JSON report
        output_path = Path(output_file)
        if not output_file.endswith('.json'):
            output_path = output_path.with_suffix('.json')
        
        with open(output_path, 'w') as f:
            json.dump(json_data, f, indent=2)
        
        print(f"✅ JSON report saved to: {output_path.absolute()}")
        print(f"📄 Report contains {len(json_data['duplicate_groups'])} duplicate groups")
    
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
        print("Version: 0.1.0")
        print()
        print("Development Phases:")
        print("  ✅ Phase 0: Duplicate Detection - Complete")
        print("  🚧 Phase 1: Loose Episode Detection - Planned")
        print("  🚧 Phase 2: Path Resolution - Planned")
        print("  🚧 Phase 3: Organization Execution - Planned")
        print()
        print("Available Commands:")
        print("  • duplicates - Detect and analyze duplicate episodes")
        print("  • config - Show configuration")
        print("  • status - Show this status information")
        print()
        print("Coming Soon:")
        print("  • loose - Find episodes not properly organized")
        print("  • resolve - Determine correct destinations")
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
        print("  tv-organizer config --show")
        print("  tv-organizer status")
        
        return 0
    
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
            elif parsed_args.command in ['config', 'cfg']:
                return self.run_config_command(parsed_args)
            elif parsed_args.command in ['status', 'stat']:
                return self.run_status_command(parsed_args)
            elif parsed_args.command in ['loose', 'l', 'resolve', 'r', 'organize', 'org', 'o']:
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