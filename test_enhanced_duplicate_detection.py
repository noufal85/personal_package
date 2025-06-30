#!/usr/bin/env python3
"""
Test script for enhanced duplicate detection.

This script tests the enhanced duplicate detector that reduces false positives
by analyzing file content and filename patterns.
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
    """Test enhanced duplicate detection."""
    print("🧪 Testing Enhanced Duplicate Detection")
    print("=" * 50)
    print("Testing enhanced duplicate detection with false positive filtering")
    print()
    
    try:
        # Test enhanced detector
        print("🔍 Running Enhanced Duplicate Detection...")
        detector = DuplicateDetector()
        episodes = detector.scan_all_directories()
        duplicates = detector.detect_duplicates()
        
        print(f"✅ Results:")
        print(f"   Episodes: {len(episodes)}")
        print(f"   High-Confidence Duplicate Groups: {len(duplicates)}")
        
        stats = detector.get_duplicate_statistics()
        print(f"   Total Duplicate Files: {stats['total_duplicate_files']}")
        print(f"   Potential Savings: {stats['potential_space_saved_gb']:.2f} GB")
        print(f"   Space Efficiency: {stats['space_efficiency']:.1f}%")
        print()
        
        # Show sample duplicates with confidence scores
        if duplicates:
            print(f"📋 Sample High-Confidence Duplicates:")
            for i, group in enumerate(sorted(duplicates, 
                                           key=lambda g: g.metadata.get('confidence_score', 0), 
                                           reverse=True)[:5], 1):
                confidence = group.metadata.get('confidence_score', 0)
                has_versions = group.metadata.get('has_version_files', False)
                version_text = " (version files)" if has_versions else ""
                print(f"   {i}. {group.show_name} S{group.season:02d}E{group.episode:02d}: "
                      f"confidence {confidence:.2f}{version_text}")
        
        # Generate enhanced report
        print(f"\n📋 Generating Enhanced Report...")
        report = detector.generate_enhanced_report()
        
        # Save enhanced report
        report_file = Path("reports/tv/duplicate_report.txt")
        report_file.parent.mkdir(parents=True, exist_ok=True)
        report_file.write_text(report)
        print(f"✅ Enhanced report saved to: {report_file.absolute()}")
        
        print(f"\n🎉 Enhanced duplicate detection testing completed!")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main test function."""
    setup_logging()
    
    print("Enhanced Duplicate Detection Test")
    print("This test validates the enhanced duplicate detection functionality.")
    print("Features tested: content analysis, version detection, confidence scoring\n")
    
    success = test_duplicate_detection()
    
    if success:
        print("\n✅ Enhanced duplicate detection test completed successfully!")
        print("📋 Check the enhanced report file for improved results.")
    else:
        print("\n❌ Test failed. Check the error output above.")
        sys.exit(1)


if __name__ == "__main__":
    main()