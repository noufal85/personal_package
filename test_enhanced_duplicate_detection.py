#!/usr/bin/env python3
"""
Test script to compare original vs enhanced duplicate detection.

This script tests the new enhanced duplicate detector that reduces false positives
by analyzing file content and filename patterns.
"""

import logging
import sys
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from file_managers.plex.tv_organizer.core.duplicate_detector import DuplicateDetector
from file_managers.plex.tv_organizer.core.enhanced_duplicate_detector import EnhancedDuplicateDetector


def setup_logging():
    """Setup logging for the test."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def test_duplicate_detection_comparison():
    """Compare original vs enhanced duplicate detection."""
    print("🧪 Testing Enhanced Duplicate Detection")
    print("=" * 50)
    print("Comparing original vs enhanced duplicate detection to reduce false positives")
    print()
    
    try:
        # Test with original detector
        print("🔍 Running Original Duplicate Detection...")
        original_detector = DuplicateDetector()
        original_episodes = original_detector.scan_all_directories()
        original_duplicates = original_detector.detect_duplicates()
        
        print(f"✅ Original Results:")
        print(f"   Episodes: {len(original_episodes)}")
        print(f"   Duplicate Groups: {len(original_duplicates)}")
        
        original_stats = original_detector.get_duplicate_statistics()
        print(f"   Total Duplicate Files: {original_stats['total_duplicate_files']}")
        print(f"   Potential Savings: {original_stats['potential_space_saved_gb']:.2f} GB")
        print()
        
        # Test with enhanced detector
        print("🔍 Running Enhanced Duplicate Detection...")
        enhanced_detector = EnhancedDuplicateDetector()
        enhanced_episodes = enhanced_detector.scan_all_directories()
        enhanced_duplicates = enhanced_detector.detect_duplicates()
        
        print(f"✅ Enhanced Results:")
        print(f"   Episodes: {len(enhanced_episodes)}")
        print(f"   High-Confidence Duplicate Groups: {len(enhanced_duplicates)}")
        
        enhanced_stats = enhanced_detector.get_duplicate_statistics()
        print(f"   Total Duplicate Files: {enhanced_stats['total_duplicate_files']}")
        print(f"   Potential Savings: {enhanced_stats['potential_space_saved_gb']:.2f} GB")
        print()
        
        # Compare results
        print("📊 Comparison Results:")
        groups_filtered = len(original_duplicates) - len(enhanced_duplicates)
        files_filtered = original_stats['total_duplicate_files'] - enhanced_stats['total_duplicate_files']
        savings_diff = original_stats['potential_space_saved_gb'] - enhanced_stats['potential_space_saved_gb']
        
        print(f"   Duplicate groups filtered: {groups_filtered}")
        print(f"   False positive files filtered: {files_filtered}")
        print(f"   Savings reduction: {savings_diff:.2f} GB")
        print(f"   False positive rate: {(groups_filtered / len(original_duplicates) * 100):.1f}%" if original_duplicates else "N/A")
        print()
        
        # Check specific problematic cases
        print("🔍 Checking Specific Problematic Cases:")
        
        # Check Extreme Engineering
        extreme_groups_original = [g for g in original_duplicates if 'extreme engineering' in g.show_name.lower()]
        extreme_groups_enhanced = [g for g in enhanced_duplicates if 'extreme engineering' in g.show_name.lower()]
        
        print(f"   Extreme Engineering groups - Original: {len(extreme_groups_original)}, Enhanced: {len(extreme_groups_enhanced)}")
        
        if extreme_groups_original and not extreme_groups_enhanced:
            print("   ✅ Successfully filtered Extreme Engineering false positives")
        elif extreme_groups_original and extreme_groups_enhanced:
            print("   ⚠️  Some Extreme Engineering groups still detected")
        
        # Check Mr Robot
        robot_groups_original = [g for g in original_duplicates if 'robot' in g.show_name.lower()]
        robot_groups_enhanced = [g for g in enhanced_duplicates if 'robot' in g.show_name.lower()]
        
        print(f"   Mr Robot groups - Original: {len(robot_groups_original)}, Enhanced: {len(robot_groups_enhanced)}")
        
        # Show sample enhanced duplicates with confidence scores
        if enhanced_duplicates:
            print(f"\n📋 Sample High-Confidence Duplicates:")
            for i, group in enumerate(sorted(enhanced_duplicates, 
                                           key=lambda g: g.metadata.get('confidence_score', 0), 
                                           reverse=True)[:5], 1):
                confidence = group.metadata.get('confidence_score', 0)
                has_versions = group.metadata.get('has_version_files', False)
                version_text = " (version files)" if has_versions else ""
                print(f"   {i}. {group.show_name} S{group.season:02d}E{group.episode:02d}: "
                      f"confidence {confidence:.2f}{version_text}")
        
        # Generate enhanced report
        print(f"\n📋 Generating Enhanced Report...")
        enhanced_report = enhanced_detector.generate_enhanced_report()
        
        # Save enhanced report
        report_file = Path("tv_enhanced_duplicate_report.txt")
        report_file.write_text(enhanced_report)
        print(f"✅ Enhanced report saved to: {report_file.absolute()}")
        
        print(f"\n🎉 Enhanced duplicate detection testing completed!")
        print(f"📈 Improvement: {groups_filtered} false positive groups filtered out")
        
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
    print("This test compares original vs enhanced duplicate detection")
    print("to identify and filter out false positive duplicates.\n")
    
    success = test_duplicate_detection_comparison()
    
    if success:
        print("\n✅ Enhanced duplicate detection test completed successfully!")
        print("📋 Check the enhanced report file for improved results.")
    else:
        print("\n❌ Test failed. Check the error output above.")
        sys.exit(1)


if __name__ == "__main__":
    main()