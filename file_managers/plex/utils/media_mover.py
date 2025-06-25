"""
Media File Mover - Interactive file moving based on reorganization analysis.

This module reads the output from media_reorganizer and performs interactive moves
of misplaced files to their correct locations with user confirmation.
"""

import os
import json
import shutil
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass

from ..config.config import config


@dataclass
class MoveOperation:
    """Represents a file move operation."""
    source_path: str
    target_path: str
    current_category: str
    suggested_category: str
    confidence: float
    reasoning: str
    file_size: int
    file_size_readable: str


class MediaMover:
    """
    Interactive media file mover based on reorganization analysis.
    
    Reads JSON output from media_reorganizer and performs interactive moves
    with user confirmation for each operation.
    """
    
    def __init__(self, dry_run: bool = False):
        """Initialize the media mover."""
        self.config = config
        self.dry_run = dry_run
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.logger = self._setup_logging()
        
        # Statistics
        self.stats = {
            'total_operations': 0,
            'moves_completed': 0,
            'moves_skipped': 0,
            'moves_failed': 0,
            'total_size_moved': 0
        }
        
        # Video file extensions to verify we're working with media files
        self.video_extensions = {'.mkv', '.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm', '.m4v'}
        
        # Cached moves for batch execution
        self.approved_moves = []
        self.cached_decisions_file = Path(f"cache/move_decisions_{self.session_id}.json")
        
    def _setup_logging(self) -> logging.Logger:
        """Setup logging for the mover session."""
        # Create logs directory
        logs_dir = Path("logs")
        logs_dir.mkdir(exist_ok=True)
        
        # Create logger
        logger = logging.getLogger(f"media_mover_{self.session_id}")
        logger.setLevel(logging.DEBUG)
        
        # Remove existing handlers to avoid duplication
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
        
        # Create file handler
        log_file = logs_dir / f"media_mover_{self.session_id}.log"
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        
        # Create console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(funcName)-20s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # Add handlers
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        self.log_file_path = log_file
        logger.info("=" * 60)
        logger.info(f"Media Mover Session Started: {self.session_id}")
        logger.info(f"Dry Run Mode: {'ON' if self.dry_run else 'OFF'}")
        logger.info("=" * 60)
        
        return logger
    
    def _save_approved_moves_cache(self) -> None:
        """Save approved moves to cache file for potential re-execution."""
        try:
            # Create cache directory
            cache_dir = Path("cache")
            cache_dir.mkdir(exist_ok=True)
            
            # Prepare cache data
            cache_data = {
                "session_id": self.session_id,
                "timestamp": datetime.now().isoformat(),
                "dry_run": self.dry_run,
                "total_approved": len(self.approved_moves),
                "approved_moves": []
            }
            
            for operation in self.approved_moves:
                source_item, target_item, move_type = self._determine_move_operation(operation)
                
                move_data = {
                    "source_path": str(source_item),
                    "target_path": str(target_item),
                    "move_type": move_type,
                    "operation_data": {
                        "source_path": operation.source_path,
                        "target_path": operation.target_path,
                        "current_category": operation.current_category,
                        "suggested_category": operation.suggested_category,
                        "confidence": operation.confidence,
                        "reasoning": operation.reasoning,
                        "file_size": operation.file_size,
                        "file_size_readable": operation.file_size_readable
                    }
                }
                cache_data["approved_moves"].append(move_data)
            
            # Save to cache file
            with open(self.cached_decisions_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Saved {len(self.approved_moves)} approved moves to cache: {self.cached_decisions_file}")
            
        except Exception as e:
            self.logger.error(f"Failed to save approved moves cache: {e}")
    
    def _execute_approved_moves(self) -> None:
        """Execute all approved moves in batch."""
        if not self.approved_moves:
            print("\n🚨 No moves were approved for execution")
            return
        
        print(f"\n🚀 EXECUTING {len(self.approved_moves)} APPROVED MOVES")
        print("=" * 60)
        
        # Save cache before execution
        self._save_approved_moves_cache()
        
        success_count = 0
        failed_count = 0
        
        for i, operation in enumerate(self.approved_moves, 1):
            print(f"\n🔄 [{i}/{len(self.approved_moves)}] Executing move...")
            print(f"   {operation.source_path}")
            print(f"   → {self._determine_target_file_path(operation)}")
            
            # Perform the actual move
            success, result_msg = self._perform_move(operation)
            
            if success:
                print(f"   ✅ {result_msg}")
                self.logger.info(f"Move successful: {operation.source_path} -> {result_msg}")
                success_count += 1
                self.stats['moves_completed'] += 1
                self.stats['total_size_moved'] += operation.file_size
            else:
                print(f"   ❌ {result_msg}")
                self.logger.error(f"Move failed: {operation.source_path} - {result_msg}")
                failed_count += 1
                self.stats['moves_failed'] += 1
        
        print(f"\n🏆 BATCH EXECUTION COMPLETE")
        print(f"   ✅ Successful: {success_count}")
        print(f"   ❌ Failed: {failed_count}")
        
        if success_count > 0:
            total_size_gb = sum(op.file_size for op in self.approved_moves if self._move_was_successful(op)) / (1024**3)
            print(f"   💾 Data moved: {total_size_gb:.2f} GB")
    
    def _move_was_successful(self, operation: MoveOperation) -> bool:
        """Check if a move operation was successful (for statistics)."""
        # This is a simple check - in a real implementation, you might want to
        # track this more precisely during execution
        return True  # Simplified for now
    
    def _get_corrected_target_path(self, operation: MoveOperation) -> str:
        """Get corrected target path using proper config mount points."""
        category = operation.suggested_category.lower()
        
        # Use proper config directories instead of subdirectories
        if category == 'documentaries':
            # Use dedicated documentary directory from config
            try:
                if hasattr(self.config, 'config_data') and 'documentaries' in self.config.config_data:
                    doc_dirs = self.config.config_data['documentaries']['directories']
                    if doc_dirs:
                        return doc_dirs[0]['path']
            except Exception:
                pass
            # Fallback to Movies directory with Documentary subdirectory
            return "/mnt/qnap/Media/Documentary/"
            
        elif category == 'standup':
            # Use dedicated standup directory from config
            try:
                if hasattr(self.config, 'config_data') and 'standups' in self.config.config_data:
                    standup_dirs = self.config.config_data['standups']['directories']
                    if standup_dirs:
                        return standup_dirs[0]['path']
            except Exception:
                pass
            # Fallback to standup mount
            return "/mnt/qnap/Media/standups/"
            
        elif category == 'tv':
            if self.config.tv_directories:
                return self.config.tv_directories[0]
            return "/mnt/qnap/plex/TV/"
            
        elif category == 'movies':
            if self.config.movie_directories:
                return self.config.movie_directories[0]
            return "/mnt/qnap/plex/Movie/"
        
        # For other categories, use the original target path
        return operation.target_path
    
    def _determine_tv_move_operation(self, source_path: Path, target_base: Path) -> Tuple[Path, Path, str]:
        """Determine TV episode move operation with existing show folder detection."""
        # Extract show name and episode info from filename
        show_info = self._extract_tv_show_info(source_path.name)
        
        if show_info:
            show_name, year, season, episode = show_info
            
            # Look for existing show folder in target TV directory
            existing_show_folder = self._find_existing_tv_show_folder(target_base, show_name, year)
            
            if existing_show_folder:
                # Move to existing show folder structure
                season_folder = existing_show_folder / f"Season {season}"
                target_file_path = season_folder / source_path.name
                return source_path, target_file_path, "tv_episode_to_existing_show"
            else:
                # Create new show folder structure
                new_show_folder = target_base / f"{show_name} ({year})" if year else target_base / show_name
                season_folder = new_show_folder / f"Season {season}"
                target_file_path = season_folder / source_path.name
                return source_path, target_file_path, "tv_episode_to_new_show"
        
        # Fallback: move just the file
        target_file_path = target_base / source_path.name
        return source_path, target_file_path, "file"
    
    def _extract_tv_show_info(self, filename: str) -> Optional[Tuple[str, Optional[str], int, int]]:
        """Extract show name, year, season, and episode from filename."""
        import re
        
        # Common TV episode patterns
        patterns = [
            # Sugar.2024.S01E06.1080p.WEB.h264-ETHEL.mkv
            r'^(.+?)\.?(\d{4})\.?[Ss](\d{1,2})[Ee](\d{1,2})',
            # Sugar (2024) S01E06
            r'^(.+?)\s*\((\d{4})\)\s*[Ss](\d{1,2})[Ee](\d{1,2})',
            # Sugar S01E06
            r'^(.+?)\s*[Ss](\d{1,2})[Ee](\d{1,2})',
            # Sugar 2024 S01E06
            r'^(.+?)\s*(\d{4})\s*[Ss](\d{1,2})[Ee](\d{1,2})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, filename, re.IGNORECASE)
            if match:
                groups = match.groups()
                if len(groups) == 4:  # show, year, season, episode
                    show_name = groups[0].replace('.', ' ').strip()
                    year = groups[1] if groups[1] else None
                    season = int(groups[2])
                    episode = int(groups[3])
                    return show_name, year, season, episode
                elif len(groups) == 3:  # show, season, episode (no year)
                    show_name = groups[0].replace('.', ' ').strip()
                    season = int(groups[1])
                    episode = int(groups[2])
                    return show_name, None, season, episode
        
        return None
    
    def _find_existing_tv_show_folder(self, tv_base_dir: Path, show_name: str, year: Optional[str]) -> Optional[Path]:
        """Find existing TV show folder that matches the show name."""
        if not tv_base_dir.exists():
            return None
        
        show_name_clean = show_name.lower().replace(' ', '').replace('.', '')
        
        try:
            for item in tv_base_dir.iterdir():
                if item.is_dir():
                    folder_name_clean = item.name.lower().replace(' ', '').replace('.', '').replace('(', '').replace(')', '')
                    
                    # Check for exact or close matches
                    if show_name_clean in folder_name_clean or folder_name_clean.startswith(show_name_clean):
                        # If we have a year, prefer folders with matching year
                        if year and year in item.name:
                            return item
                        # Or if no year match found, use the first match
                        elif not year:
                            return item
                        # Store as potential match if no better match found
                        else:
                            # Keep looking for year match, but remember this as fallback
                            potential_match = item
            
            # Return potential match if no exact year match found
            if year and 'potential_match' in locals():
                return potential_match
                
        except Exception as e:
            self.logger.warning(f"Error searching for existing TV show folder: {e}")
        
        return None
    
    def load_reorganization_report(self, report_path: str) -> List[MoveOperation]:
        """Load move operations from reorganization JSON report."""
        try:
            report_file = Path(report_path)
            
            if not report_file.exists():
                raise FileNotFoundError(f"Report file not found: {report_path}")
            
            if not report_file.suffix.lower() == '.json':
                raise ValueError("Report file must be a JSON file")
            
            with open(report_file, 'r', encoding='utf-8') as f:
                report_data = json.load(f)
            
            # Extract move operations from report
            move_operations = []
            
            # Handle new actionable_moves structure
            if 'actionable_moves' in report_data:
                for confidence_level in ['high_confidence', 'medium_confidence', 'low_confidence']:
                    if confidence_level in report_data['actionable_moves']:
                        operations = report_data['actionable_moves'][confidence_level].get('operations', [])
                        for file_data in operations:
                            move_op = MoveOperation(
                                source_path=file_data['source_path'],
                                target_path=file_data['suggested_path'],
                                current_category=file_data['current_category'],
                                suggested_category=file_data['suggested_category'],
                                confidence=file_data['confidence'],
                                reasoning=file_data['reasoning'],
                                file_size=file_data['file_size'],
                                file_size_readable=file_data['file_size_readable']
                            )
                            move_operations.append(move_op)
            
            # Handle legacy misplaced_files structure (fallback)
            elif 'misplaced_files' in report_data:
                for file_data in report_data['misplaced_files']:
                    move_op = MoveOperation(
                        source_path=file_data['source_path'],
                        target_path=file_data['suggested_path'],
                        current_category=file_data['current_category'],
                        suggested_category=file_data['suggested_category'],
                        confidence=file_data['confidence'],
                        reasoning=file_data['reasoning'],
                        file_size=file_data['file_size'],
                        file_size_readable=file_data['file_size_readable']
                    )
                    move_operations.append(move_op)
            
            self.logger.info(f"Loaded {len(move_operations)} move operations from {report_path}")
            return move_operations
            
        except Exception as e:
            self.logger.error(f"Failed to load reorganization report: {e}")
            raise
    
    def _validate_paths(self, operation: MoveOperation) -> Tuple[bool, str]:
        """Validate source and target paths for a move operation."""
        source_path = Path(operation.source_path)
        
        # Check if source file exists
        if not source_path.exists():
            return False, f"Source file not found: {source_path}"
        
        # Check if source is a media file
        if source_path.suffix.lower() not in self.video_extensions:
            return False, f"Not a media file: {source_path.suffix}"
        
        # Check if source is accessible
        if not os.access(source_path, os.R_OK):
            return False, f"Source file not readable: {source_path}"
        
        # Validate target directory
        target_path = Path(operation.target_path)
        target_dir = target_path.parent if target_path.suffix else target_path
        
        # Check if target directory exists or can be created
        if not target_dir.exists():
            try:
                if not self.dry_run:
                    target_dir.mkdir(parents=True, exist_ok=True)
                    self.logger.info(f"Created target directory: {target_dir}")
            except Exception as e:
                return False, f"Cannot create target directory {target_dir}: {e}"
        
        # Check if target directory is writable
        if target_dir.exists() and not os.access(target_dir, os.W_OK):
            return False, f"Target directory not writable: {target_dir}"
        
        return True, "Paths validated successfully"
    
    def _determine_move_operation(self, operation: MoveOperation) -> Tuple[Path, Path, str]:
        """Determine what to move (file vs folder) and target path."""
        source_path = Path(operation.source_path)
        
        # Fix target path to use proper config mount points
        corrected_target = self._get_corrected_target_path(operation)
        target_base = Path(corrected_target)
        
        # Special handling for TV episodes
        if operation.suggested_category.lower() == 'tv':
            return self._determine_tv_move_operation(source_path, target_base)
        
        # Check if we should move the entire folder instead of just the file
        source_folder = source_path.parent
        source_folder_name = source_folder.name
        
        # Move the folder if:
        # 1. The file is the only/main video file in its folder
        # 2. The folder name looks like a movie/show title (contains year, title, etc.)
        should_move_folder = self._should_move_folder(source_path, source_folder)
        
        if should_move_folder:
            # Move the entire folder to proper target directory
            target_folder_path = target_base / source_folder_name
            return source_folder, target_folder_path, "folder"
        else:
            # Move just the file
            target_file_path = target_base / source_path.name
            return source_path, target_file_path, "file"
    
    def _should_move_folder(self, file_path: Path, folder_path: Path) -> bool:
        """Determine if we should move the entire folder instead of just the file."""
        try:
            # Don't move folder if it's a root media directory
            folder_name = folder_path.name.lower()
            if folder_name in ['movie', 'movies', 'tv', 'shows', 'documentary', 'documentaries', 'standup', 'standups']:
                return False
            
            # Count video files in the folder
            video_files = []
            for item in folder_path.iterdir():
                if item.is_file() and item.suffix.lower() in self.video_extensions:
                    video_files.append(item)
            
            # Move folder if:
            # 1. Only one video file (the current one)
            # 2. Multiple video files but folder name suggests it's a single title (contains year, etc.)
            if len(video_files) == 1:
                return True
            elif len(video_files) <= 3:  # Small number of files, likely a movie with extras
                # Check if folder name looks like a movie title (contains year)
                import re
                if re.search(r'\(?\b(19|20)\d{2}\)?', folder_name):
                    return True
            
            return False
            
        except Exception:
            # If we can't determine, default to moving just the file
            return False
    
    def _perform_move(self, operation: MoveOperation) -> Tuple[bool, str]:
        """Perform the actual move operation (file or folder)."""
        try:
            # Determine what to move and where
            source_item, target_item, move_type = self._determine_move_operation(operation)
            
            # Check if target already exists
            if target_item.exists():
                return False, f"Target {move_type} already exists: {target_item}"
            
            if self.dry_run:
                self.logger.info(f"DRY RUN: Would move {move_type} {source_item} -> {target_item}")
                return True, f"Dry run - {move_type} move would succeed"
            
            # Perform the actual move
            self.logger.info(f"Moving {move_type}: {source_item} -> {target_item}")
            shutil.move(str(source_item), str(target_item))
            
            # Verify the move succeeded
            if target_item.exists() and not source_item.exists():
                self.stats['total_size_moved'] += operation.file_size
                return True, f"Successfully moved {move_type} to {target_item}"
            else:
                return False, f"Move operation failed - {move_type} verification failed"
                
        except Exception as e:
            return False, f"Move failed: {e}"
    
    def _determine_target_file_path(self, operation: MoveOperation) -> str:
        """Determine the actual target path for display purposes."""
        source_item, target_item, move_type = self._determine_move_operation(operation)
        return str(target_item)
    
    def _get_user_decision(self, operation: MoveOperation, operation_num: int, total_ops: int) -> str:
        """Get user decision for a move operation."""
        print()
        print("=" * 80)
        print(f"📋 MOVE OPERATION {operation_num}/{total_ops}")
        print("=" * 80)
        print(f"📁 Source: {operation.source_path}")
        print(f"📂 Target: {self._determine_target_file_path(operation)}")
        print(f"📊 Size: {operation.file_size_readable}")
        print(f"🔄 Category: {operation.current_category} → {operation.suggested_category}")
        print(f"🎯 Confidence: {operation.confidence:.2f}")
        print(f"💡 Reasoning: {operation.reasoning}")
        print()
        print("Options:")
        print("  y - Yes, approve this move")
        print("  s - Skip this file")
        print("  q - Quit and execute approved moves")
        print("  a - Approve all remaining files")
        print("  x - Cancel all (quit without executing)")
        print()
        
        while True:
            choice = input("Your choice (y/s/q/a/x): ").strip().lower()
            if choice in ['y', 's', 'q', 'a', 'x']:
                return choice
            print("Invalid choice. Please enter 'y', 's', 'q', 'a', or 'x'.")
    
    def run_interactive_moves(self, report_path: str) -> bool:
        """Run interactive move operations based on reorganization report."""
        try:
            print("🚚 Media File Mover")
            print("=" * 30)
            print(f"📊 Report: {report_path}")
            print(f"🔄 Mode: {'DRY RUN' if self.dry_run else 'LIVE MOVES'}")
            print(f"📋 Session: {self.session_id}")
            print(f"🏁 Process: Decision phase → Batch execution")
            print()
            
            # Load move operations
            move_operations = self.load_reorganization_report(report_path)
            
            if not move_operations:
                print("✅ No files need to be moved!")
                return True
            
            print(f"🎯 Found {len(move_operations)} files to potentially move")
            print("🔍 Starting decision phase - approve moves for batch execution")
            print()
            
            self.stats['total_operations'] = len(move_operations)
            auto_approve = False
            
            # Process each move operation
            for i, operation in enumerate(move_operations, 1):
                self.logger.debug(f"Processing operation {i}: {operation.source_path}")
                
                # Validate paths
                valid, validation_msg = self._validate_paths(operation)
                if not valid:
                    print(f"❌ Skipping {operation.source_path}: {validation_msg}")
                    self.logger.warning(f"Validation failed for {operation.source_path}: {validation_msg}")
                    self.stats['moves_skipped'] += 1
                    continue
                
                # Get user decision (unless auto-approve is enabled)
                if not auto_approve:
                    decision = self._get_user_decision(operation, i, len(move_operations))
                    
                    if decision == 'q':
                        print("\n🏁 Finishing decisions and executing approved moves...")
                        break
                    elif decision == 'x':
                        print("\n❌ Cancelled by user - no moves will be executed")
                        return True
                    elif decision == 's':
                        print("⏭️  Skipped")
                        self.stats['moves_skipped'] += 1
                        continue
                    elif decision == 'a':
                        auto_approve = True
                        print("🚀 Auto-approving all remaining moves...")
                
                # Cache the approved move instead of executing immediately
                if decision == 'y' or auto_approve:
                    self.approved_moves.append(operation)
                    print("✅ Approved for execution")
                    self.logger.info(f"Move approved: {operation.source_path}")
                else:
                    self.stats['moves_skipped'] += 1
            
            # Execute all approved moves in batch
            if self.approved_moves:
                self._execute_approved_moves()
            
            # Show final summary
            self._show_summary()
            return True
            
        except Exception as e:
            print(f"❌ Move operation failed: {e}")
            self.logger.error(f"Move operation failed: {e}", exc_info=True)
            return False
    
    def _show_summary(self) -> None:
        """Show final move operation summary."""
        print()
        print("=" * 60)
        print("📊 MOVE OPERATION SUMMARY")
        print("=" * 60)
        print(f"Total operations: {self.stats['total_operations']}")
        print(f"✅ Moves completed: {self.stats['moves_completed']}")
        print(f"⏭️  Moves skipped: {self.stats['moves_skipped']}")
        print(f"❌ Moves failed: {self.stats['moves_failed']}")
        print(f"📋 Approved for execution: {len(self.approved_moves)}")
        
        if self.stats['total_size_moved'] > 0:
            size_gb = self.stats['total_size_moved'] / (1024**3)
            print(f"💾 Total data moved: {size_gb:.2f} GB")
        
        print(f"📄 Session log: {self.log_file_path}")
        
        if self.approved_moves and self.cached_decisions_file.exists():
            print(f"🗃️ Cached decisions: {self.cached_decisions_file}")
            print("   Use this cache to re-execute the same moves later")
        
        print()
        
        # Log summary
        self.logger.info("=" * 60)
        self.logger.info("MOVE OPERATION SUMMARY")
        self.logger.info("=" * 60)
        for key, value in self.stats.items():
            self.logger.info(f"{key}: {value}")
        self.logger.info(f"approved_moves: {len(self.approved_moves)}")
        self.logger.info("=" * 60)


    def execute_cached_moves(self, cache_file_path: str) -> bool:
        """Execute moves from a previously saved cache file."""
        try:
            cache_file = Path(cache_file_path)
            if not cache_file.exists():
                print(f"❌ Cache file not found: {cache_file_path}")
                return False
            
            with open(cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            print("🚚 Media File Mover - Cache Execution")
            print("=" * 40)
            print(f"🗃️ Cache file: {cache_file_path}")
            print(f"📋 Original session: {cache_data.get('session_id', 'Unknown')}")
            print(f"📅 Created: {cache_data.get('timestamp', 'Unknown')}")
            print(f"🔄 Mode: {'DRY RUN' if self.dry_run else 'LIVE MOVES'}")
            print(f"🎯 Cached moves: {cache_data.get('total_approved', 0)}")
            print()
            
            # Confirm execution
            if not self.dry_run:
                confirm = input("Execute these cached moves? (yes/no): ").strip().lower()
                if confirm not in ['yes', 'y']:
                    print("❌ Execution cancelled")
                    return False
            
            # Recreate move operations from cache
            cached_moves = cache_data.get('approved_moves', [])
            success_count = 0
            failed_count = 0
            
            for i, move_data in enumerate(cached_moves, 1):
                source_path = Path(move_data['source_path'])
                target_path = Path(move_data['target_path'])
                move_type = move_data['move_type']
                
                print(f"\n🔄 [{i}/{len(cached_moves)}] Executing cached move...")
                print(f"   {source_path}")
                print(f"   → {target_path}")
                print(f"   Type: {move_type}")
                
                # Validate source still exists
                if not source_path.exists():
                    print(f"   ❌ Source no longer exists: {source_path}")
                    failed_count += 1
                    continue
                
                # Execute the move
                try:
                    if self.dry_run:
                        print(f"   🌫️ DRY RUN: Would move {move_type}")
                        success_count += 1
                    else:
                        # Create target directory if needed
                        target_dir = target_path.parent
                        target_dir.mkdir(parents=True, exist_ok=True)
                        
                        # Perform the move
                        shutil.move(str(source_path), str(target_path))
                        
                        if target_path.exists():
                            print(f"   ✅ Successfully moved {move_type}")
                            success_count += 1
                        else:
                            print(f"   ❌ Move failed - target not found")
                            failed_count += 1
                            
                except Exception as e:
                    print(f"   ❌ Move failed: {e}")
                    failed_count += 1
            
            print(f"\n🏆 CACHE EXECUTION COMPLETE")
            print(f"   ✅ Successful: {success_count}")
            print(f"   ❌ Failed: {failed_count}")
            
            return failed_count == 0
            
        except Exception as e:
            print(f"❌ Failed to execute cached moves: {e}")
            return False


def main():
    """CLI entry point for standalone usage."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Interactive Media File Mover")
    parser.add_argument('report', nargs='?', help='Path to reorganization JSON report file')
    parser.add_argument('--dry-run', action='store_true', help='Preview moves without actually moving files')
    parser.add_argument('--execute-cache', help='Execute moves from a cached decisions file')
    parser.add_argument('--list-cache', action='store_true', help='List available cached decision files')
    
    args = parser.parse_args()
    
    mover = MediaMover(dry_run=args.dry_run)
    
    if args.list_cache:
        # Use the same list function as the CLI
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
        
        return 0
    elif args.execute_cache:
        success = mover.execute_cached_moves(args.execute_cache)
    elif args.report:
        success = mover.run_interactive_moves(args.report)
    else:
        parser.print_help()
        return 1
    
    return 0 if success else 1


if __name__ == "__main__":
    exit(main())