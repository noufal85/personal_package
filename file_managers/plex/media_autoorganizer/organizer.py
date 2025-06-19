"""Main Auto-Organizer Class

This module contains the main AutoOrganizer class that orchestrates the entire
media organization workflow. It combines all the other components to provide
a complete media file organization solution.

Key Features:
- Intelligent TV episode placement using existing show locations
- Smart fallback logic for directory access issues
- Comprehensive file classification (AI + rule-based)
- Detailed reporting and logging
- Mount access verification
- Space management and conflict resolution
"""

import csv
import os
import random
import re
import shutil
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from ..config.config import config
from .ai_classifier import BedrockClassifier
from .classification_db import ClassificationDatabase
from .media_database import MediaDatabase
from .models import MediaFile, MediaType, MoveResult


class AutoOrganizer:
    """Automatic media file organizer with intelligent placement."""
    
    def __init__(self, dry_run: bool = True, use_ai: bool = True):
        """
        Initialize the AutoOrganizer.
        
        Args:
            dry_run: If True, only simulate moves without actually moving files
            use_ai: If True, use AI classification; otherwise use rule-based only
        """
        self.dry_run = dry_run
        self.use_ai = use_ai
        
        # Initialize AI classifier if requested
        if use_ai:
            try:
                self.classifier = BedrockClassifier()
            except RuntimeError as e:
                print(f"❌ Failed to initialize AI classifier: {e}")
                print("💡 Falling back to rule-based classification only")
                self.classifier = None
                self.use_ai = False
        else:
            print("🔧 Using rule-based classification only (AI disabled)")
            self.classifier = None
            
        self.downloads_dir = Path(config.downloads_directory)
        self.cache_file = self.downloads_dir / ".media_classification_cache.csv"
        
        # Initialize databases
        project_root = Path(__file__).parent.parent.parent.parent
        db_dir = project_root / "database"
        self.classification_db = ClassificationDatabase(db_dir / "media_classifications.db")
        self.media_db = MediaDatabase()
    
    def verify_mount_access(self) -> bool:
        """
        Verify all target directories are accessible and writable.
        
        Returns:
            True if all directories are accessible, False otherwise
        """
        print("🔍 Verifying mount access and directory permissions...")
        
        all_directories = [
            *config.movie_directories,
            *config.tv_directories,
            *config.documentary_directories,
            *config.standup_directories
        ]
        
        failed_dirs = []
        
        for directory in all_directories:
            dir_path = Path(directory)
            
            # Check if directory exists
            if not dir_path.exists():
                print(f"    ❌ Directory does not exist: {directory}")
                failed_dirs.append(directory)
                continue
            
            # Check if it's actually a directory
            if not dir_path.is_dir():
                print(f"    ❌ Path exists but is not a directory: {directory}")
                failed_dirs.append(directory)
                continue
            
            # Check write permissions
            if not os.access(dir_path, os.W_OK):
                print(f"    ❌ No write permission: {directory}")
                failed_dirs.append(directory)
                continue
            
            # Try to create a test file
            test_file = dir_path / ".access_test"
            try:
                test_file.touch()
                test_file.unlink()  # Remove test file
                print(f"    ✅ Accessible: {directory}")
            except Exception as e:
                print(f"    ❌ Cannot write to directory: {directory} ({e})")
                failed_dirs.append(directory)
        
        if failed_dirs:
            print(f"\n❌ MOUNT ACCESS VERIFICATION FAILED")
            print(f"   {len(failed_dirs)} directories are not accessible:")
            for failed_dir in failed_dirs:
                print(f"   - {failed_dir}")
            
            self._show_mount_help()
            return False
        else:
            print(f"\n✅ MOUNT ACCESS VERIFICATION PASSED")
            print(f"   All {len(all_directories)} target directories are accessible")
            return True
    
    def _show_mount_help(self) -> None:
        """Show mount commands to help user remount QNAP shares."""
        print("\n🔧 QNAP MOUNT REQUIRED")
        print("=" * 40)
        print("Please run these 3 commands to mount QNAP shares:")
        print()
        
        # Get QNAP configuration
        qnap_ip = config.nas_server_ip
        shares = config.nas_shares
        
        # Show only the essential mount commands
        for share in shares:
            share_name = share['name']
            mount_path = share['mount_path']
            print(f"sudo mount -t cifs //{qnap_ip}/{share_name} {mount_path} -o username=noufal85,uid=$(id -u),gid=$(id -g),iocharset=utf8,file_mode=0777,dir_mode=0777")
        
        print()
        print("💡 Run this script again after mounting")
    
    def scan_downloads(self) -> List[MediaFile]:
        """
        Scan the downloads directory for media files at parent level only.
        
        Returns:
            List of MediaFile objects found (only top-level items)
        """
        media_files = []
        
        if not self.downloads_dir.exists():
            print(f"⚠️  Downloads directory not found: {self.downloads_dir}")
            return media_files
        
        print(f"🔍 Scanning downloads directory (parent level only): {self.downloads_dir}")
        
        # Only scan direct children, not subdirectories
        for item_path in self.downloads_dir.iterdir():
            if item_path.is_file() and self._is_media_file(item_path):
                try:
                    size = item_path.stat().st_size
                    media_file = MediaFile(path=item_path, size=size)
                    media_files.append(media_file)
                    print(f"    📄 Found file: {item_path.name}")
                except (OSError, PermissionError):
                    continue
            elif item_path.is_dir():
                # For directories, classify by directory name, not contents
                try:
                    # Calculate directory size (for reporting)
                    total_size = sum(f.stat().st_size for f in item_path.rglob('*') if f.is_file())
                    media_file = MediaFile(path=item_path, size=total_size)
                    media_files.append(media_file)
                    print(f"    📁 Found directory: {item_path.name}")
                except (OSError, PermissionError):
                    continue
        
        print(f"📁 Found {len(media_files)} items (files and directories) at parent level")
        return media_files
    
    def _is_media_file(self, file_path: Path) -> bool:
        """Check if a file is a media file based on extension."""
        return file_path.suffix.lower() in config.video_extensions_set
    
    def classify_files(self, media_files: List[MediaFile]) -> List[MediaFile]:
        """
        Classify media files using cached, rule-based, and AI classification.
        
        Args:
            media_files: List of MediaFile objects to classify
            
        Returns:
            List of MediaFile objects with classification and target information
        """
        classified_files = []
        
        # Load classification cache
        cache = self._load_classification_cache()
        
        # Separate files into different processing categories
        db_cached_files = []
        csv_cached_files = []
        obvious_files = []
        ai_needed_files = []
        
        print(f"🔍 Pre-filtering {len(media_files)} files...")
        
        for media_file in media_files:
            filename = media_file.path.name
            filename_lower = filename.lower()
            
            # Check database first (highest priority)
            db_result = self.classification_db.get_classification(filename)
            if db_result:
                media_type_str, classification_source, confidence = db_result
                try:
                    media_type = MediaType(media_type_str)
                    db_cached_files.append((media_file, media_type, f"DB-{classification_source}"))
                    continue
                except ValueError:
                    # Invalid cached media type, re-classify
                    pass
            
            # Check CSV cache second
            if filename in cache:
                media_type_str, classification_source = cache[filename]
                try:
                    media_type = MediaType(media_type_str)
                    csv_cached_files.append((media_file, media_type, f"CSV-{classification_source}"))
                    # Also store in database for future use
                    self.classification_db.store_classification(filename, media_type_str, classification_source, 0.7)
                    continue
                except ValueError:
                    # Invalid cached media type, re-classify
                    pass
            
            # Very obvious TV patterns - no AI needed
            if any(pattern in filename_lower for pattern in ['s0', 's1', 's2', 's3', 's4', 's5', 's6', 's7', 's8', 's9', 'season', 'episode']):
                obvious_files.append((media_file, MediaType.TV, "Rule-based"))
            # Very obvious documentary patterns
            elif any(pattern in filename_lower for pattern in ['documentary', 'docu', 'bbc', 'nat geo', 'national geographic']):
                obvious_files.append((media_file, MediaType.DOCUMENTARY, "Rule-based"))
            # Very obvious standup patterns
            elif any(pattern in filename_lower for pattern in ['standup', 'stand-up', 'comedy special', 'chappelle', 'carlin']):
                obvious_files.append((media_file, MediaType.STANDUP, "Rule-based"))
            else:
                ai_needed_files.append(media_file)
        
        print(f"🗄️  {len(db_cached_files)} files loaded from database")
        print(f"💾 {len(csv_cached_files)} files loaded from CSV cache")
        print(f"📋 {len(obvious_files)} files pre-classified by rules")
        print(f"🤖 {len(ai_needed_files)} files need AI classification")
        
        # Process all categories
        classified_files.extend(self._process_cached_files(db_cached_files))
        classified_files.extend(self._process_cached_files(csv_cached_files))
        classified_files.extend(self._process_obvious_files(obvious_files))
        classified_files.extend(self._process_ai_files(ai_needed_files))
        
        # Save new classifications to cache
        new_classifications = [f for f in classified_files if not f.classification_source.startswith("Cached-")]
        if new_classifications:
            self._save_classification_cache(classified_files)
        
        return classified_files
    
    def _process_cached_files(self, cached_files: List[Tuple]) -> List[MediaFile]:
        """Process cached files and add target directory information."""
        processed_files = []
        
        for media_file, media_type, source in cached_files:
            # For TV shows, try to find existing show location
            target_directory = None
            show_name = None
            season = None
            episode = None
            
            if media_type == MediaType.TV:
                show_name, season, episode = self.media_db.extract_tv_info(media_file.path.name)
                if show_name:
                    existing_location = self.media_db.find_tv_show_location(show_name)
                    if existing_location:
                        target_directory = existing_location
            
            # Fall back to default directories if no specific location found
            if not target_directory:
                target_dirs = config.get_directories_by_media_type(media_type.value)
                target_directory = target_dirs[0] if target_dirs else None
            
            classified_file = media_file._replace(
                media_type=media_type,
                target_directory=target_directory,
                classification_source=source,
                show_name=show_name,
                season=season,
                episode=episode
            )
            processed_files.append(classified_file)
        
        return processed_files
    
    def _process_obvious_files(self, obvious_files: List[Tuple]) -> List[MediaFile]:
        """Process obviously classified files and store in database."""
        processed_files = []
        rule_based_entries = []
        
        for media_file, media_type, source in obvious_files:
            # For TV shows, try to find existing show location
            target_directory = None
            show_name = None
            season = None
            episode = None
            
            if media_type == MediaType.TV:
                show_name, season, episode = self.media_db.extract_tv_info(media_file.path.name)
                if show_name:
                    existing_location = self.media_db.find_tv_show_location(show_name)
                    if existing_location:
                        target_directory = existing_location
                        print(f"    📺 Found existing location for '{show_name}': {existing_location}")
                    else:
                        print(f"    📺 New show '{show_name}' - will use default TV directory")
            
            # Fall back to default directories if no specific location found
            if not target_directory:
                target_dirs = config.get_directories_by_media_type(media_type.value)
                target_directory = target_dirs[0] if target_dirs else None
            
            classified_file = media_file._replace(
                media_type=media_type,
                target_directory=target_directory,
                classification_source=source,
                show_name=show_name,
                season=season,
                episode=episode
            )
            processed_files.append(classified_file)
            
            # Prepare for database storage
            rule_based_entries.append((
                media_file.path.name,
                media_type.value,
                source,
                0.8  # High confidence for rule-based obvious patterns
            ))
        
        # Store rule-based classifications in database
        if rule_based_entries:
            self.classification_db.store_batch_classifications(rule_based_entries)
        
        return processed_files
    
    def _process_ai_files(self, ai_needed_files: List[MediaFile]) -> List[MediaFile]:
        """Process files that need AI classification."""
        processed_files = []
        
        if not ai_needed_files:
            return processed_files
        
        if self.use_ai and self.classifier:
            print(f"🤖 Starting batch AI classification for {len(ai_needed_files)} files...")
            
            # Process files in batches of 10
            batch_size = 10
            for batch_start in range(0, len(ai_needed_files), batch_size):
                batch_end = min(batch_start + batch_size, len(ai_needed_files))
                batch_files = ai_needed_files[batch_start:batch_end]
                batch_filenames = [f.path.name for f in batch_files]
                
                batch_num = (batch_start // batch_size) + 1
                total_batches = (len(ai_needed_files) + batch_size - 1) // batch_size
                
                print(f"📦 Batch {batch_num}/{total_batches}: Classifying {len(batch_files)} files...")
                
                # Classify the batch
                batch_results = self.classifier.classify_batch(batch_filenames)
                
                # Process batch results
                batch_db_entries = []
                for media_file, result in zip(batch_files, batch_results):
                    classified_file = self._create_classified_file(media_file, result, "AI-Batch")
                    processed_files.append(classified_file)
                    
                    # Prepare for database storage
                    batch_db_entries.append((
                        media_file.path.name,
                        result.media_type.value,
                        "AI-Batch",
                        result.confidence
                    ))
                    
                    show_info = f" ({classified_file.show_name})" if classified_file.show_name else ""
                    print(f"    {media_file.path.name} → {result.media_type.value}{show_info} (AI-Batch)")
                
                # Store batch results in database
                if batch_db_entries:
                    self.classification_db.store_batch_classifications(batch_db_entries)
                
                # Delay between batches with jitter
                if batch_num < total_batches:  # Don't delay after last batch
                    delay = 2.0 + random.uniform(0, 1)
                    print(f"⏳ Waiting {delay:.1f}s before next batch...")
                    time.sleep(delay)
        else:
            # Fallback to rule-based classification for all AI-needed files
            print(f"📋 Using rule-based classification for {len(ai_needed_files)} remaining files...")
            
            for media_file in ai_needed_files:
                # Use fallback classification (assumes movies by default)
                from .ai_classifier import BedrockClassifier
                dummy_classifier = BedrockClassifier.__new__(BedrockClassifier)  # Create instance without __init__
                result = dummy_classifier._fallback_classification(media_file.path.name)
                
                classified_file = self._create_classified_file(media_file, result, "Rule-based")
                processed_files.append(classified_file)
        
        return processed_files
    
    def _create_classified_file(self, media_file: MediaFile, result, classification_source: str) -> MediaFile:
        """Create a classified MediaFile with target directory and show information."""
        # For TV shows, try to find existing show location
        target_directory = None
        show_name = None
        season = None
        episode = None
        
        if result.media_type == MediaType.TV:
            show_name, season, episode = self.media_db.extract_tv_info(media_file.path.name)
            if show_name:
                existing_location = self.media_db.find_tv_show_location(show_name)
                if existing_location:
                    target_directory = existing_location
                    print(f"        📺 Found existing location for '{show_name}': {existing_location}")
                else:
                    print(f"        📺 New show '{show_name}' - will use default TV directory")
        
        # Fall back to default directories if no specific location found
        if not target_directory:
            target_dirs = config.get_directories_by_media_type(result.media_type.value)
            target_directory = target_dirs[0] if target_dirs else None
        
        return media_file._replace(
            media_type=result.media_type,
            target_directory=target_directory,
            classification_source=classification_source,
            show_name=show_name,
            season=season,
            episode=episode
        )
    
    def organize_files(self, classified_files: List[MediaFile]) -> List[MoveResult]:
        """
        Organize classified files into appropriate directories.
        
        Args:
            classified_files: List of classified MediaFile objects
            
        Returns:
            List of MoveResult objects
        """
        results = []
        
        # Group files by media type
        files_by_type = {}
        for media_file in classified_files:
            if media_file.media_type not in files_by_type:
                files_by_type[media_file.media_type] = []
            files_by_type[media_file.media_type].append(media_file)
        
        print(f"📦 Organizing {len(classified_files)} files...")
        
        for media_type, files in files_by_type.items():
            print(f"\n📂 Processing {len(files)} {media_type.value} items:")
            
            if media_type == MediaType.OTHER or media_type == MediaType.AUDIOBOOK:
                print(f"    ⏭️  Skipping {media_type.value} items (unclassified - will not be moved)")
                # Add failed results for unclassified items
                for media_file in files:
                    results.append(MoveResult(
                        success=False,
                        source_path=media_file.path,
                        error=f"Skipped - classified as {media_type.value}"
                    ))
                continue
            
            for media_file in files:
                result = self._move_file(media_file)
                results.append(result)
        
        return results
    
    def _move_file(self, media_file: MediaFile) -> MoveResult:
        """Move a single file to its target directory with intelligent placement."""
        if not media_file.target_directory:
            return MoveResult(
                success=False,
                source_path=media_file.path,
                error="No target directory configured"
            )
        
        # If we have a specific target directory (from existing show location), try it first
        if media_file.target_directory:
            result = self._try_move_to_directory(media_file, Path(media_file.target_directory))
            if result.success:
                return result
            elif "access" in result.error.lower() or "permission" in result.error.lower():
                # Mark this directory as failed and don't try it again for other files
                self.media_db.mark_directory_failed(media_file.target_directory)
        
        # For TV shows, try to create a new show directory in available TV directories
        if media_file.media_type == MediaType.TV and media_file.show_name:
            return self._create_tv_show_directory(media_file)
        
        # For movies or other media, try all available directories
        target_dirs = config.get_directories_by_media_type(media_file.media_type.value)
        
        for target_dir in target_dirs:
            # Skip directories we've already marked as failed for this move attempt
            if target_dir in self.media_db.failed_directories:
                print(f"    ⏭️  Skipping previously failed directory: {target_dir}")
                continue
                
            result = self._try_move_to_directory(media_file, Path(target_dir))
            if result.success:
                return result
            elif "access" in result.error.lower() or "permission" in result.error.lower():
                # Mark this directory as failed
                self.media_db.mark_directory_failed(target_dir)
        
        # If we get here, all target directories failed
        return MoveResult(
            success=False,
            source_path=media_file.path,
            error="All target directories failed (space or access issues)"
        )
    
    def _try_move_to_directory(self, media_file: MediaFile, target_path: Path) -> MoveResult:
        """Try to move a file to a specific directory."""
        # Check if target directory exists and is accessible
        if not target_path.exists():
            if not self.dry_run:
                try:
                    target_path.mkdir(parents=True, exist_ok=True)
                    print(f"    📁 Created directory: {target_path}")
                except OSError as e:
                    return MoveResult(
                        success=False,
                        source_path=media_file.path,
                        error=f"Failed to create directory {target_path}: {e}"
                    )
        elif not target_path.is_dir():
            return MoveResult(
                success=False,
                source_path=media_file.path,
                error=f"Target path exists but is not a directory: {target_path}"
            )
        elif not os.access(target_path, os.W_OK):
            return MoveResult(
                success=False,
                source_path=media_file.path,
                error=f"No write permission for directory: {target_path}"
            )
        
        # Check available space
        if not self._check_space(media_file.size, target_path):
            return MoveResult(
                success=False,
                source_path=media_file.path,
                error=f"Insufficient space in {target_path}"
            )
        
        # Determine final target path
        final_target = target_path / media_file.path.name
        
        # Handle filename conflicts
        if final_target.exists():
            final_target = self._resolve_filename_conflict(final_target)
        
        # Perform the move
        if self.dry_run:
            item_type = "directory" if media_file.path.is_dir() else "file"
            print(f"    📋 DRY RUN: Would move {item_type} to {final_target}")
            return MoveResult(
                success=True,
                source_path=media_file.path,
                target_path=final_target
            )
        else:
            try:
                if media_file.path.is_dir():
                    # Move entire directory
                    shutil.move(str(media_file.path), str(final_target))
                    print(f"    ✅ Moved directory to {final_target}")
                else:
                    # Move single file
                    shutil.move(str(media_file.path), str(final_target))
                    print(f"    ✅ Moved file to {final_target}")
                
                return MoveResult(
                    success=True,
                    source_path=media_file.path,
                    target_path=final_target,
                    space_freed=media_file.size
                )
            except Exception as e:
                return MoveResult(
                    success=False,
                    source_path=media_file.path,
                    error=f"Failed to move: {e}"
                )
    
    def _create_tv_show_directory(self, media_file: MediaFile) -> MoveResult:
        """Create a new TV show directory and move the episode there."""
        tv_dirs = config.get_directories_by_media_type("TV")
        
        for tv_base_dir in tv_dirs:
            # Skip directories we've already marked as failed
            if tv_base_dir in self.media_db.failed_directories:
                print(f"    ⏭️  Skipping previously failed TV directory: {tv_base_dir}")
                continue
            
            tv_base_path = Path(tv_base_dir)
            
            # Check if base TV directory is accessible
            if not tv_base_path.exists() or not tv_base_path.is_dir() or not os.access(tv_base_path, os.W_OK):
                print(f"    ❌ TV directory not accessible: {tv_base_path}")
                self.media_db.mark_directory_failed(tv_base_dir)
                continue
            
            # Check available space in base directory
            if not self._check_space(media_file.size, tv_base_path):
                print(f"    ⚠️  Insufficient space in TV directory: {tv_base_path}")
                continue
            
            # Create show directory
            show_dir_name = self._sanitize_show_name(media_file.show_name)
            show_path = tv_base_path / show_dir_name
            
            # Try to create and move to the show directory
            if not self.dry_run:
                try:
                    show_path.mkdir(exist_ok=True)
                    print(f"    📺 Created/found show directory: {show_path}")
                except OSError as e:
                    print(f"    ❌ Failed to create show directory {show_path}: {e}")
                    continue
            
            # Try to move the episode to the show directory
            result = self._try_move_to_directory(media_file, show_path)
            if result.success:
                if not self.dry_run:
                    print(f"    🎬 Created new show directory and moved episode")
                return result
        
        # If we get here, all TV directories failed
        return MoveResult(
            success=False,
            source_path=media_file.path,
            error="Failed to create show directory in any available TV directory"
        )
    
    def _sanitize_show_name(self, show_name: str) -> str:
        """Sanitize show name for use as directory name."""
        # Remove/replace invalid characters for filesystem
        sanitized = re.sub(r'[<>:"/\\|?*]', '', show_name)
        sanitized = re.sub(r'\s+', ' ', sanitized)  # Normalize spaces
        return sanitized.strip()
    
    def _check_space(self, file_size: int, target_path: Path) -> bool:
        """Check if there's enough space in the target directory."""
        try:
            stat = shutil.disk_usage(target_path)
            available_space = stat.free
            
            # Require at least 1GB buffer beyond file size
            required_space = file_size + (1024 * 1024 * 1024)  # 1GB buffer
            
            return available_space >= required_space
        except OSError:
            return False
    
    def _resolve_filename_conflict(self, target_path: Path) -> Path:
        """Resolve filename conflicts by adding a number suffix."""
        base_name = target_path.stem
        extension = target_path.suffix
        parent = target_path.parent
        
        counter = 1
        while True:
            new_name = f"{base_name}_{counter}{extension}"
            new_path = parent / new_name
            if not new_path.exists():
                return new_path
            counter += 1
    
    def _load_classification_cache(self) -> Dict[str, Tuple[str, str]]:
        """Load previously cached classifications."""
        cache = {}
        
        if not self.cache_file.exists():
            return cache
        
        try:
            with open(self.cache_file, 'r', newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    filename = row['filename']
                    media_type = row['media_type']
                    classification_source = row['classification_source']
                    cache[filename] = (media_type, classification_source)
            
            print(f"📋 Loaded {len(cache)} cached classifications from {self.cache_file}")
        except Exception as e:
            print(f"⚠️  Error loading classification cache: {e}")
        
        return cache
    
    def _save_classification_cache(self, classified_files: List[MediaFile]) -> None:
        """Save classifications to cache file."""
        try:
            with open(self.cache_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=['filename', 'media_type', 'classification_source', 'timestamp'])
                writer.writeheader()
                
                for media_file in classified_files:
                    writer.writerow({
                        'filename': media_file.path.name,
                        'media_type': media_file.media_type.value if media_file.media_type else 'UNKNOWN',
                        'classification_source': media_file.classification_source or 'Unknown',
                        'timestamp': datetime.now().isoformat()
                    })
            
            print(f"💾 Saved {len(classified_files)} classifications to cache")
        except Exception as e:
            print(f"⚠️  Error saving classification cache: {e}")
    
    def generate_report(self, results: List[MoveResult], classified_files: List[MediaFile] = None) -> str:
        """Generate a comprehensive report of the organization results."""
        timestamp = datetime.now().strftime(config.timestamp_format)
        report_path = config.get_reports_path() / f"auto_organizer_{timestamp}.txt"
        
        successful_moves = [r for r in results if r.success]
        failed_moves = [r for r in results if not r.success]
        total_space_freed = sum(r.space_freed for r in successful_moves)
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("🤖 AUTO-ORGANIZER REPORT\n")
            f.write("=" * 60 + "\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Mode: {'DRY RUN' if self.dry_run else 'EXECUTION'}\n")
            f.write(f"Total Files Processed: {len(results)}\n")
            f.write(f"Successful Moves: {len(successful_moves)}\n")
            f.write(f"Failed Moves: {len(failed_moves)}\n")
            f.write(f"Total Space Freed: {self._format_size(total_space_freed)}\n\n")
            
            if successful_moves:
                f.write("✅ SUCCESSFUL MOVES:\n")
                f.write("-" * 40 + "\n")
                for result in successful_moves:
                    # Find classification info for this file
                    classification_info = ""
                    media_type = "UNKNOWN"
                    show_info = ""
                    
                    if classified_files:
                        for classified_file in classified_files:
                            if str(classified_file.path) == str(result.source_path):
                                media_type = classified_file.media_type.value if classified_file.media_type else "UNKNOWN"
                                classification_info = f" ({classified_file.classification_source or 'Unknown'} Classification)"
                                
                                if classified_file.show_name:
                                    season_episode = ""
                                    if classified_file.season and classified_file.episode:
                                        season_episode = f" S{classified_file.season:02d}E{classified_file.episode:02d}"
                                    show_info = f" - {classified_file.show_name}{season_episode}"
                                break
                    
                    f.write(f"  {result.source_path.name}\n")
                    f.write(f"    FROM: {result.source_path}\n")
                    f.write(f"    TO:   {result.target_path if result.target_path else 'N/A'}\n")
                    f.write(f"    SIZE: {self._format_size(result.space_freed)}\n")
                    f.write(f"    TYPE: {media_type}{show_info}{classification_info}\n\n")
            
            if failed_moves:
                f.write("❌ FAILED MOVES:\n")
                f.write("-" * 40 + "\n")
                for result in failed_moves:
                    # Find classification info for failed files too
                    classification_info = ""
                    media_type = "UNKNOWN"
                    intended_target = "Unknown"
                    show_info = ""
                    
                    if classified_files:
                        for classified_file in classified_files:
                            if str(classified_file.path) == str(result.source_path):
                                media_type = classified_file.media_type.value if classified_file.media_type else "UNKNOWN"
                                classification_info = f" ({classified_file.classification_source or 'Unknown'} Classification)"
                                intended_target = classified_file.target_directory or "Unknown"
                                
                                if classified_file.show_name:
                                    season_episode = ""
                                    if classified_file.season and classified_file.episode:
                                        season_episode = f" S{classified_file.season:02d}E{classified_file.episode:02d}"
                                    show_info = f" - {classified_file.show_name}{season_episode}"
                                break
                    
                    f.write(f"  {result.source_path.name}\n")
                    f.write(f"    FROM: {result.source_path}\n")
                    f.write(f"    INTENDED TARGET: {intended_target}\n")
                    f.write(f"    TYPE: {media_type}{show_info}{classification_info}\n")
                    f.write(f"    ERROR: {result.error}\n\n")
        
        return str(report_path)
    
    def _format_size(self, size_bytes: int) -> str:
        """Format file size in human-readable format."""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} PB"
    
    def run_full_organization(self) -> str:
        """
        Run the complete organization workflow.
        
        Returns:
            Path to the generated report
        """
        print("🤖 MEDIA AUTO-ORGANIZER")
        print("=" * 50)
        print(f"Mode: {'DRY RUN' if self.dry_run else 'EXECUTION'}")
        print(f"Downloads Directory: {self.downloads_dir}")
        
        try:
            # Step 1: Scan for media files
            media_files = self.scan_downloads()
            if not media_files:
                print("📭 No media files found in downloads directory")
                return ""
            
            # Step 2: Classify files using AI
            classified_files = self.classify_files(media_files)
            
            # Step 3: Organize files
            results = self.organize_files(classified_files)
            
            # Step 4: Generate report
            report_path = self.generate_report(results, classified_files)
            print(f"\n📄 Report generated: {report_path}")
            
            # Step 5: Summary
            successful = sum(1 for r in results if r.success)
            failed = sum(1 for r in results if not r.success)
            print(f"\n📊 SUMMARY:")
            print(f"  Successful: {successful}")
            print(f"  Failed: {failed}")
            print(f"  Total: {len(results)}")
            
            if not self.dry_run and successful > 0:
                print(f"🎉 Successfully organized {successful} media files!")
            
            return report_path
            
        except KeyboardInterrupt:
            print("\n👋 Organization cancelled by user")
            return ""
        except Exception as e:
            print(f"❌ Error during organization: {e}")
            return ""