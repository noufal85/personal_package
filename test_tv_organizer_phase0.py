#!/usr/bin/env python3
"""
Test script for TV Organizer Phase 0: Duplicate Detection

This script tests the duplicate detection functionality of the new TV organizer module.
It's separate from the main CLI and safe to run for testing.
"""

import logging
import sys
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from file_managers.plex.tv_organizer.core.duplicate_detector import DuplicateDetector


def setup_logging():
    """Setup logging for the test."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def test_duplicate_detection():
    """Test the duplicate detection functionality."""
    print("🧪 Testing TV Organizer Phase 0: Duplicate Detection")
    print("=" * 60)
    
    # Initialize detector
    detector = DuplicateDetector()
    
    print(f"📁 Scanning {len(detector.tv_directories)} TV directories:")
    for i, directory in enumerate(detector.tv_directories, 1):
        print(f"  {i}. {directory}")
    print()
    
    try:
        # Phase 1: Scan all directories
        print("🔍 Phase 1: Scanning directories for episodes...")
        episodes = detector.scan_all_directories()
        print(f"✅ Found {len(episodes)} total episodes")
        
        if episodes:
            # Show sample episodes
            print("\n📺 Sample episodes found:")
            for i, episode in enumerate(episodes[:5], 1):
                print(f"  {i}. {episode}")
            if len(episodes) > 5:
                print(f"  ... and {len(episodes) - 5} more episodes")
        
        print()
        
        # Phase 2: Detect duplicates
        print("🔍 Phase 2: Detecting duplicates...")
        duplicate_groups = detector.detect_duplicates()
        
        if duplicate_groups:
            print(f"⚠️  Found {len(duplicate_groups)} duplicate groups")
            
            # Show statistics
            stats = detector.get_duplicate_statistics()
            print(f"\n📊 Duplicate Statistics:")
            print(f"  • Total duplicate files: {stats['total_duplicate_files']}")
            print(f"  • Space used by duplicates: {stats['total_space_used_gb']:.2f} GB")
            print(f"  • Potential space savings: {stats['potential_space_saved_gb']:.2f} GB")
            print(f"  • Space efficiency gain: {stats['space_efficiency']:.1f}%")
            
            # Show sample duplicate groups
            print(f"\n🔍 Sample duplicate groups:")
            for i, group in enumerate(duplicate_groups[:3], 1):
                print(f"  {i}. {group.get_summary()}")
                print(f"     Recommended: {group.recommended_action.value}")
                if group.recommended_keeper:
                    print(f"     Keep: {group.recommended_keeper.filename}")
                print(f"     Files: {group.duplicate_count}")
            
            if len(duplicate_groups) > 3:
                print(f"  ... and {len(duplicate_groups) - 3} more duplicate groups")
            
            # Generate full report
            print(f"\n📋 Generating full duplicate report...")
            report = detector.generate_report()
            
            # Save report to file
            report_file = Path("tv_duplicate_report.txt")
            report_file.write_text(report)
            print(f"✅ Report saved to: {report_file.absolute()}")
            
            # Show shows with duplicates
            shows_with_dups = detector.get_shows_with_duplicates()
            if shows_with_dups:
                print(f"\n📺 Shows with duplicates ({len(shows_with_dups)} total):")
                for show in sorted(shows_with_dups)[:10]:
                    show_groups = detector.get_duplicates_for_show(show)
                    total_duplicates = sum(g.duplicate_count for g in show_groups)
                    print(f"  • {show}: {len(show_groups)} groups, {total_duplicates} files")
                
                if len(shows_with_dups) > 10:
                    print(f"  ... and {len(shows_with_dups) - 10} more shows")
            
        else:
            print("✅ No duplicates found - all episodes are unique!")
        
        print(f"\n🎉 Phase 0 testing completed successfully!")
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


def main():
    """Main test function."""
    setup_logging()
    
    print("TV File Organizer - Phase 0 Test")
    print("This is a separate module for testing duplicate detection.")
    print("It will not modify any files - only analyze and report.\n")
    
    success = test_duplicate_detection()
    
    if success:
        print("\n✅ All tests passed! Phase 0 duplicate detection is working.")
        print("📋 Check the generated report file for detailed results.")
    else:
        print("\n❌ Tests failed. Check the error output above.")
        sys.exit(1)


if __name__ == "__main__":
    main()