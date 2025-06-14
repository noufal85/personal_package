"""Interactive deletion manager for duplicate movies."""

import os
import sys
from pathlib import Path
from typing import List, Tuple

from .movie_scanner import DuplicateGroup, format_file_size


def print_duplicate_group_for_deletion(group: DuplicateGroup, group_number: int, total_groups: int) -> None:
    """Print a duplicate group in the same format as the report for deletion confirmation."""
    group_wasted = sum(movie.size for movie in group.files) - group.best_file.size
    
    print(f"\n{group_number}. {group.normalized_name.title()}")
    print(f"   Copies Found: {len(group.files)}")
    print(f"   Wasted Space: {format_file_size(group_wasted)}")
    print("-" * 60)
    
    # Sort files by size (largest first for easier comparison)
    sorted_files = sorted(group.files, key=lambda x: x.size, reverse=True)
    
    for j, movie in enumerate(sorted_files, 1):
        is_best = movie == group.best_file
        action = "🟢 KEEP" if is_best else "❌ DELETE CANDIDATE"
        
        print(f"  {j}. {movie.name}")
        print(f"     Size: {format_file_size(movie.size)} {action}")
        print(f"     Path: {movie.path.parent}")
        if movie.year:
            print(f"     Year: {movie.year}")
        print()
    
    print(f"   → RECOMMENDATION: Keep '{group.best_file.name}'")
    print(f"     Location: {group.best_file.path.parent}")


def get_deletion_choice() -> str:
    """Get user choice for deletion."""
    while True:
        print("\n" + "=" * 60)
        print("🗑️  DELETION OPTIONS:")
        print("  [d] - DELETE duplicate files (keep smallest)")
        print("  [x] - SKIP this group (no deletion)")
        print("  [q] - QUIT deletion mode")
        print("  [a] - DELETE ALL remaining duplicates (no more prompts)")
        print("=" * 60)
        
        choice = input("Enter your choice (d/x/q/a): ").lower().strip()
        
        if choice in ['d', 'x', 'q', 'a']:
            return choice
        
        print("❌ Invalid choice. Please enter 'd', 'x', 'q', or 'a'.")


def confirm_deletion(files_to_delete: List[Path]) -> bool:
    """Confirm deletion of specific files."""
    print(f"\n⚠️  FINAL CONFIRMATION")
    print(f"About to DELETE {len(files_to_delete)} files:")
    print("-" * 40)
    
    total_size = 0
    for file_path in files_to_delete:
        try:
            size = file_path.stat().st_size
            total_size += size
            print(f"  ❌ {file_path.name}")
            print(f"     Size: {format_file_size(size)}")
            print(f"     Path: {file_path.parent}")
        except Exception as e:
            print(f"  ❌ {file_path.name} (Error reading: {e})")
        print()
    
    print(f"Total space to recover: {format_file_size(total_size)}")
    print("\n" + "⚠️ " * 20)
    print("WARNING: THIS ACTION CANNOT BE UNDONE!")
    print("⚠️ " * 20)
    
    while True:
        confirm = input("\nType 'DELETE' to confirm, or 'cancel' to abort: ").strip()
        if confirm == "DELETE":
            return True
        elif confirm.lower() == "cancel":
            return False
        else:
            print("Please type exactly 'DELETE' to confirm or 'cancel' to abort.")


def delete_files_safely(files_to_delete: List[Path]) -> Tuple[int, int, List[str]]:
    """
    Safely delete files and return statistics.
    
    Returns:
        Tuple of (successful_deletions, failed_deletions, error_messages)
    """
    successful = 0
    failed = 0
    errors = []
    
    for file_path in files_to_delete:
        try:
            print(f"Deleting: {file_path.name}...")
            file_path.unlink()
            successful += 1
            print(f"✅ Deleted successfully")
        except FileNotFoundError:
            print(f"⚠️  File not found (already deleted?): {file_path.name}")
            errors.append(f"File not found: {file_path}")
            failed += 1
        except PermissionError:
            print(f"❌ Permission denied: {file_path.name}")
            errors.append(f"Permission denied: {file_path}")
            failed += 1
        except Exception as e:
            print(f"❌ Error deleting {file_path.name}: {e}")
            errors.append(f"Error deleting {file_path}: {e}")
            failed += 1
    
    return successful, failed, errors


def interactive_deletion_mode(duplicates: List[DuplicateGroup]) -> None:
    """
    Run interactive deletion mode for duplicate movies.
    
    Shows each duplicate group and asks for confirmation before deletion.
    """
    if not duplicates:
        print("✅ No duplicates found - nothing to delete!")
        return
    
    print("\n" + "🗑️ " * 20)
    print("INTERACTIVE DELETION MODE")
    print("🗑️ " * 20)
    print(f"\nFound {len(duplicates)} groups of duplicate movies.")
    print("You will be shown each group and can choose to:")
    print("  • Delete duplicates (keeping the smallest file)")
    print("  • Skip the group")
    print("  • Quit deletion mode")
    print("  • Delete all remaining duplicates")
    
    input("\nPress Enter to start review process...")
    
    # Sort duplicates by wasted space (biggest first)
    sorted_duplicates = sorted(duplicates, 
                             key=lambda x: sum(movie.size for movie in x.files) - x.best_file.size, 
                             reverse=True)
    
    files_to_delete = []
    auto_delete_all = False
    
    for i, group in enumerate(sorted_duplicates, 1):
        # Clear screen for each group
        os.system('cls' if os.name == 'nt' else 'clear')
        
        print(f"🎬 DUPLICATE REVIEW - Group {i} of {len(sorted_duplicates)}")
        print("=" * 80)
        
        # Show the group in report format
        print_duplicate_group_for_deletion(group, i, len(sorted_duplicates))
        
        # Get files that would be deleted (all except smallest)
        group_files_to_delete = [movie.path for movie in group.files if movie != group.best_file]
        
        if auto_delete_all:
            # Auto-delete mode - add to list without asking
            files_to_delete.extend(group_files_to_delete)
            print(f"\n🔄 AUTO-DELETE MODE: Added {len(group_files_to_delete)} files to deletion queue")
            continue
        
        # Get user choice
        choice = get_deletion_choice()
        
        if choice == 'd':
            # Delete this group
            files_to_delete.extend(group_files_to_delete)
            print(f"✅ Added {len(group_files_to_delete)} files to deletion queue")
            # Auto-continue for delete choice - no pause needed
            
        elif choice == 'x':
            # Skip this group
            print("⏭️  Skipped this group")
            # Pause only for skip choice
            if not auto_delete_all and i < len(sorted_duplicates):
                input(f"\nPress Enter to continue to next group... ({len(sorted_duplicates) - i} remaining)")
            
        elif choice == 'q':
            # Quit deletion mode
            print("🚪 Exiting deletion mode")
            break
            
        elif choice == 'a':
            # Auto-delete all remaining
            files_to_delete.extend(group_files_to_delete)
            auto_delete_all = True
            print(f"🔄 AUTO-DELETE MODE: Will delete all remaining duplicates")
            print(f"✅ Added {len(group_files_to_delete)} files to deletion queue")
            # Auto-continue for auto-delete - no pause needed
    
    # Final deletion phase
    if files_to_delete:
        os.system('cls' if os.name == 'nt' else 'clear')
        print("🎬 MOVIE DUPLICATE DELETION - FINAL STEP")
        print("=" * 80)
        
        if confirm_deletion(files_to_delete):
            print(f"\n🗑️  Starting deletion of {len(files_to_delete)} files...")
            print("-" * 60)
            
            successful, failed, errors = delete_files_safely(files_to_delete)
            
            print(f"\n" + "=" * 60)
            print("🎯 DELETION SUMMARY")
            print("=" * 60)
            print(f"✅ Successfully deleted: {successful} files")
            if failed > 0:
                print(f"❌ Failed to delete: {failed} files")
                print("\nErrors encountered:")
                for error in errors:
                    print(f"  • {error}")
            
            if successful > 0:
                # Calculate space recovered
                print(f"\n💾 Space recovered from successful deletions!")
                print("⚠️  Run the scanner again to see updated results.")
        else:
            print("🚫 Deletion cancelled - no files were deleted")
    else:
        print("\n✅ No files were marked for deletion")
    
    print(f"\n🎬 Deletion mode completed!")
    input("Press Enter to continue...")