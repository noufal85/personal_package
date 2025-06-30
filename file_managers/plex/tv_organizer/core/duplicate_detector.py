"""
Enhanced Duplicate Detection for TV File Organizer

Addresses issues with false positive duplicate detection by implementing:
1. Content-based differentiation (different episode titles)
2. Version detection (files with _1, _2 suffixes)
3. Better filename parsing for complex patterns
4. Confidence scoring for duplicate detection
"""

import re
import os
import shutil
import logging
from pathlib import Path
from typing import List, Dict, Set, Optional, Tuple
from collections import defaultdict
from datetime import datetime

from ..models.episode import Episode, Quality, EpisodeStatus
from ..models.duplicate import (
    DuplicateGroup, DuplicateAction, DeletionOperation, DeletionPlan,
    DeletionMode, DeletionStatus, SafetyCheck
)
from ...utils.tv_scanner import extract_tv_info_from_filename, is_video_file
from ...config.config import config


class DuplicateDetector:
    """
    Enhanced duplicate detector that reduces false positives by considering
    episode content and filename patterns.
    """
    
    def __init__(self, tv_directories: Optional[List[str]] = None):
        """Initialize the enhanced duplicate detector."""
        self.tv_directories = tv_directories or config.tv_directories
        self.logger = logging.getLogger(__name__)
        
        # Results storage
        self.episodes: List[Episode] = []
        self.duplicate_groups: List[DuplicateGroup] = []
        
        # Quality detection patterns
        self.quality_patterns = {
            Quality.UHD_8K: [r'8k', r'4320p'],
            Quality.UHD_4K: [r'4k', r'2160p', r'uhd'],
            Quality.FHD_1080P: [r'1080p', r'fhd'],
            Quality.HD_720P: [r'720p', r'hd'],
            Quality.SD_480P: [r'480p', r'sd']
        }
        
        # Source detection patterns
        self.source_patterns = {
            'BluRay': [r'bluray', r'blu-ray', r'bdrip', r'brrip'],
            'WEB-DL': [r'web-dl', r'webdl'],
            'WEBRip': [r'webrip', r'web-rip'],
            'HDTV': [r'hdtv'],
            'DVDRip': [r'dvdrip', r'dvd-rip'],
            'CAM': [r'cam', r'camrip'],
            'TS': [r'\bts\b', r'telesync']
        }
        
        # Patterns for detecting file versions (true duplicates)
        self.version_patterns = [
            r'_(\d+)\.(?:mkv|mp4|avi)$',  # filename_1.mkv, filename_2.mkv
            r'_(\d+)$',                    # filename_1, filename_2
            r'\((\d+)\)\.(?:mkv|mp4|avi)$', # filename(1).mkv, filename(2).mkv
            r'\((\d+)\)$',                 # filename(1), filename(2)
            r'\.(\d+)\.(?:mkv|mp4|avi)$',  # filename.1.mkv, filename.2.mkv
        ]
        
        # Patterns for multi-episode files (should not be duplicates)
        self.multi_episode_patterns = [
            r'S\d+E\d+.*S\d+E\d+',        # S01E01-S01E02, S01E01 S01E02
            r'E\d+-E\d+',                 # E01-E02
            r'Episodes?\s+\d+-\d+',       # Episodes 1-2
        ]
        
        # Words that indicate different content (not duplicates)
        self.content_differentiators = {
            # Geographic/location terms
            'alaska', 'boston', 'dubai', 'tokyo', 'hong kong', 'iceland', 'venice',
            'transatlantic', 'panama', 'gotthard', 'cooper river', 'oakland',
            
            # Engineering/construction terms  
            'tunnel', 'bridge', 'airport', 'stadium', 'platform', 'excavator',
            'dam', 'cable car', 'subway', 'pyramid', 'resort', 'barriers',
            
            # Generic differentiators
            'part 1', 'part 2', 'part i', 'part ii', 'chapter', 'volume',
            'disc 1', 'disc 2', 'cd1', 'cd2'
        }
    
    def scan_all_directories(self) -> List[Episode]:
        """
        Scan all TV directories and build episode database.
        
        Returns:
            List of all episodes found
        """
        self.logger.info(f"Starting duplicate detection scan of {len(self.tv_directories)} directories")
        self.episodes.clear()
        
        for directory in self.tv_directories:
            self.logger.info(f"Scanning directory: {directory}")
            episodes_in_dir = self._scan_directory(directory)
            self.episodes.extend(episodes_in_dir)
            self.logger.info(f"Found {len(episodes_in_dir)} episodes in {directory}")
        
        self.logger.info(f"Total episodes found: {len(self.episodes)}")
        return self.episodes
    
    def _scan_directory(self, directory: str) -> List[Episode]:
        """
        Scan a single directory for TV episodes.
        
        Args:
            directory: Directory path to scan
            
        Returns:
            List of episodes found in the directory
        """
        episodes = []
        directory_path = Path(directory)
        
        if not directory_path.exists():
            self.logger.warning(f"Directory does not exist: {directory}")
            return episodes
        
        try:
            # Recursively find all video files
            for file_path in directory_path.rglob('*'):
                if file_path.is_file() and is_video_file(file_path):
                    episode = self._create_episode_from_file(file_path)
                    if episode:
                        episodes.append(episode)
        
        except Exception as e:
            self.logger.error(f"Error scanning directory {directory}: {e}")
        
        return episodes
    
    def _create_episode_from_file(self, file_path: Path) -> Optional[Episode]:
        """
        Create an Episode object from a video file.
        
        Args:
            file_path: Path to the video file
            
        Returns:
            Episode object or None if not a valid TV episode
        """
        try:
            # Extract TV show information
            tv_info = extract_tv_info_from_filename(file_path.name)
            if not tv_info:
                return None
            
            show_name, season, episode_num = tv_info
            
            # Get file information
            file_size = file_path.stat().st_size
            file_extension = file_path.suffix.lower()
            
            # Detect quality and source
            quality = self._detect_quality(file_path.name)
            source = self._detect_source(file_path.name)
            
            # Create episode object
            episode = Episode(
                file_path=file_path,
                file_size=file_size,
                file_extension=file_extension,
                show_name=show_name,
                season=season,
                episode=episode_num,
                quality=quality,
                source=source,
                status=self._determine_episode_status(file_path)
            )
            
            return episode
            
        except Exception as e:
            self.logger.warning(f"Error processing file {file_path}: {e}")
            return None
    
    def _detect_quality(self, filename: str) -> Quality:
        """
        Detect video quality from filename.
        
        Args:
            filename: The filename to analyze
            
        Returns:
            Detected quality level
        """
        filename_lower = filename.lower()
        
        for quality, patterns in self.quality_patterns.items():
            for pattern in patterns:
                if re.search(pattern, filename_lower):
                    return quality
        
        return Quality.UNKNOWN
    
    def _detect_source(self, filename: str) -> Optional[str]:
        """
        Detect video source from filename.
        
        Args:
            filename: The filename to analyze
            
        Returns:
            Detected source or None
        """
        filename_lower = filename.lower()
        
        for source, patterns in self.source_patterns.items():
            for pattern in patterns:
                if re.search(pattern, filename_lower):
                    return source
        
        return None
    
    def _determine_episode_status(self, file_path: Path) -> EpisodeStatus:
        """
        Determine the organization status of an episode.
        
        Args:
            file_path: Path to the episode file
            
        Returns:
            Episode organization status
        """
        # For now, all episodes are considered organized
        # Future phases will implement loose episode detection
        return EpisodeStatus.ORGANIZED
    
    def _extract_content_signature(self, filename: str) -> str:
        """
        Extract a content signature from filename to detect different episodes.
        
        Args:
            filename: The filename to analyze
            
        Returns:
            Content signature for comparison
        """
        # Remove common prefixes and suffixes
        content = filename.lower()
        
        # Remove file extension
        content = Path(content).stem
        
        # Remove version indicators
        for pattern in self.version_patterns:
            content = re.sub(pattern, '', content)
        
        # Remove quality indicators
        quality_terms = ['720p', '1080p', '4k', 'hdtv', 'webrip', 'bluray', 'x264', 'x265', 'hevc']
        for term in quality_terms:
            content = content.replace(term, '')
        
        # Remove common separators and normalize
        content = re.sub(r'[._-]+', ' ', content)
        content = ' '.join(content.split())  # Normalize whitespace
        
        return content
    
    def _detect_file_version(self, filename: str) -> Optional[int]:
        """
        Detect if this filename has a version number (indicating true duplicate).
        
        Args:
            filename: The filename to analyze
            
        Returns:
            Version number if detected, None otherwise
        """
        for pattern in self.version_patterns:
            match = re.search(pattern, filename.lower())
            if match:
                return int(match.group(1))
        return None
    
    def _is_multi_episode_file(self, filename: str) -> bool:
        """
        Check if this filename represents multiple episodes.
        
        Args:
            filename: The filename to analyze
            
        Returns:
            True if this appears to be a multi-episode file
        """
        for pattern in self.multi_episode_patterns:
            if re.search(pattern, filename, re.IGNORECASE):
                return True
        return False
    
    def _has_content_differences(self, filenames: List[str]) -> bool:
        """
        Check if filenames have significant content differences.
        
        Args:
            filenames: List of filenames to compare
            
        Returns:
            True if files have different content (not duplicates)
        """
        if len(filenames) < 2:
            return False
        
        content_signatures = [self._extract_content_signature(f) for f in filenames]
        
        # Check for content differentiator words
        for signature in content_signatures:
            words = set(signature.split())
            if any(diff in words for diff in self.content_differentiators):
                # If any file has differentiator words, check if others do too
                other_signatures = [s for s in content_signatures if s != signature]
                for other in other_signatures:
                    other_words = set(other.split())
                    # If one has differentiators and another doesn't, they're different
                    if not any(diff in other_words for diff in self.content_differentiators):
                        return True
                    # If they have different differentiators, they're different
                    signature_diffs = words & self.content_differentiators
                    other_diffs = other_words & self.content_differentiators
                    if signature_diffs != other_diffs:
                        return True
        
        # Check for significantly different content signatures
        unique_signatures = set(content_signatures)
        if len(unique_signatures) > 1:
            # Calculate similarity between signatures
            for i, sig1 in enumerate(content_signatures):
                for sig2 in content_signatures[i+1:]:
                    words1 = set(sig1.split())
                    words2 = set(sig2.split())
                    
                    if not words1 or not words2:
                        continue
                    
                    # Jaccard similarity
                    intersection = len(words1 & words2)
                    union = len(words1 | words2)
                    similarity = intersection / union if union > 0 else 0
                    
                    # If similarity is very low, these are different episodes
                    if similarity < 0.3:
                        return True
        
        return False
    
    def detect_duplicates(self) -> List[DuplicateGroup]:
        """
        Enhanced duplicate detection with content analysis.
        
        Returns:
            List of duplicate groups with reduced false positives
        """
        if not self.episodes:
            self.logger.warning("No episodes loaded. Run scan_all_directories() first.")
            return []
        
        self.logger.info("Detecting duplicates with enhanced analysis...")
        
        # Group episodes by show/season/episode (initial grouping)
        episode_groups = defaultdict(list)
        
        for episode in self.episodes:
            episode_id = episode.episode_id
            episode_groups[episode_id].append(episode)
        
        # Filter out false positives and create duplicate groups
        self.duplicate_groups.clear()
        total_groups_checked = 0
        false_positives_filtered = 0
        
        for episode_id, episodes in episode_groups.items():
            total_groups_checked += 1
            
            if len(episodes) < 2:
                continue  # No duplicates
            
            # Extract filenames for analysis
            filenames = [ep.filename for ep in episodes]
            
            # Check for multi-episode files (not duplicates)
            if any(self._is_multi_episode_file(f) for f in filenames):
                self.logger.debug(f"Skipping multi-episode file group: {episode_id}")
                false_positives_filtered += 1
                continue
            
            # Check for content differences (not duplicates)
            if self._has_content_differences(filenames):
                self.logger.debug(f"Skipping content-different group: {episode_id}")
                false_positives_filtered += 1
                continue
            
            # Check for version files (true duplicates)
            versions = [self._detect_file_version(f) for f in filenames]
            has_versions = any(v is not None for v in versions)
            
            if has_versions:
                self.logger.debug(f"Confirmed version duplicates: {episode_id}")
            
            # Create duplicate group for confirmed duplicates
            first_episode = episodes[0]
            duplicate_group = DuplicateGroup(
                show_name=first_episode.show_name,
                season=first_episode.season,
                episode=first_episode.episode,
                episodes=episodes
            )
            
            # Enhanced analysis
            duplicate_group.analyze_duplicates()
            
            # Add metadata about detection confidence
            confidence_score = self._calculate_confidence_score(episodes, has_versions)
            duplicate_group.metadata['confidence_score'] = confidence_score
            duplicate_group.metadata['has_version_files'] = has_versions
            duplicate_group.metadata['analysis_method'] = 'enhanced'
            
            if confidence_score >= 0.7:  # Only include high-confidence duplicates
                self.duplicate_groups.append(duplicate_group)
            else:
                self.logger.debug(f"Low confidence duplicate filtered: {episode_id} (score: {confidence_score:.2f})")
                false_positives_filtered += 1
        
        self.logger.info(f"Enhanced duplicate detection complete:")
        self.logger.info(f"  Total groups checked: {total_groups_checked}")
        self.logger.info(f"  False positives filtered: {false_positives_filtered}")
        self.logger.info(f"  High-confidence duplicates: {len(self.duplicate_groups)}")
        
        return self.duplicate_groups
    
    def _calculate_confidence_score(self, episodes: List[Episode], has_versions: bool) -> float:
        """
        Calculate confidence score for duplicate detection.
        
        Args:
            episodes: List of episodes in the group
            has_versions: Whether version files were detected
            
        Returns:
            Confidence score between 0.0 and 1.0
        """
        score = 0.0
        
        # Base score for having multiple files
        score += 0.3
        
        # High score for version files
        if has_versions:
            score += 0.5
        
        # Score based on filename similarity
        filenames = [ep.filename for ep in episodes]
        if len(filenames) >= 2:
            # Calculate average filename similarity
            similarities = []
            for i, f1 in enumerate(filenames):
                for f2 in filenames[i+1:]:
                    sig1 = self._extract_content_signature(f1)
                    sig2 = self._extract_content_signature(f2)
                    words1 = set(sig1.split())
                    words2 = set(sig2.split())
                    
                    if words1 and words2:
                        intersection = len(words1 & words2)
                        union = len(words1 | words2)
                        similarity = intersection / union if union > 0 else 0
                        similarities.append(similarity)
            
            if similarities:
                avg_similarity = sum(similarities) / len(similarities)
                score += avg_similarity * 0.3
        
        # Score based on file sizes (similar sizes = more likely duplicates)
        sizes = [ep.file_size for ep in episodes]
        if len(sizes) >= 2:
            size_variance = max(sizes) / min(sizes) if min(sizes) > 0 else 1
            # Lower variance = higher score
            size_score = 1.0 / size_variance if size_variance > 1 else 1.0
            score += size_score * 0.2
        
        return min(score, 1.0)  # Cap at 1.0
    
    def generate_enhanced_report(self) -> str:
        """
        Generate enhanced duplicate detection report with confidence scores.
        
        Returns:
            Formatted report string with confidence information
        """
        if not self.duplicate_groups:
            return "No high-confidence duplicates detected."
        
        # Get statistics
        stats = self.get_duplicate_statistics()
        
        report = []
        report.append("ENHANCED TV EPISODE DUPLICATE DETECTION REPORT")
        report.append("=" * 55)
        report.append("")
        
        # Summary statistics
        report.append("SUMMARY:")
        report.append(f"  Total Episodes Scanned: {len(self.episodes)}")
        report.append(f"  High-Confidence Duplicate Groups: {stats['total_duplicate_groups']}")
        report.append(f"  Total Duplicate Files: {stats['total_duplicate_files']}")
        report.append(f"  Space Used by Duplicates: {stats['total_space_used_gb']:.2f} GB")
        report.append(f"  Potential Space Savings: {stats['potential_space_saved_gb']:.2f} GB")
        report.append(f"  Space Efficiency Gain: {stats['space_efficiency']:.1f}%")
        report.append("")
        
        # Filter information
        report.append("ENHANCED FILTERING:")
        report.append("  ✅ Multi-episode files excluded")
        report.append("  ✅ Content-different files excluded")
        report.append("  ✅ Low-confidence matches excluded")
        report.append("  ✅ Version files prioritized")
        report.append("")
        
        # Detailed duplicate groups
        report.append("HIGH-CONFIDENCE DUPLICATE GROUPS:")
        report.append("-" * 40)
        
        # Sort by confidence score (highest first)
        sorted_groups = sorted(
            self.duplicate_groups,
            key=lambda g: g.metadata.get('confidence_score', 0),
            reverse=True
        )
        
        for i, group in enumerate(sorted_groups, 1):
            confidence = group.metadata.get('confidence_score', 0)
            has_versions = group.metadata.get('has_version_files', False)
            
            report.append(f"\n{i}. {group.get_summary()}")
            report.append(f"   Confidence: {confidence:.2f} {'(Version Files)' if has_versions else ''}")
            report.append(f"   Action: {group.recommended_action.value}")
            
            if group.recommended_keeper:
                report.append(f"   Keep: {group.recommended_keeper.filename}")
                report.append(f"         ({group.recommended_keeper.quality.value}, "
                            f"{group.recommended_keeper.size_mb:.1f}MB)")
            
            if group.recommended_removals:
                report.append("   Remove:")
                for episode in group.recommended_removals:
                    version = self._detect_file_version(episode.filename)
                    version_text = f" (v{version})" if version else ""
                    report.append(f"     - {episode.filename}{version_text}")
                    report.append(f"       ({episode.quality.value}, {episode.size_mb:.1f}MB)")
            
            if group.analysis_notes:
                report.append("   Notes:")
                for note in group.analysis_notes:
                    report.append(f"     • {note}")
        
        return "\n".join(report)
    
    def generate_report(self) -> str:
        """
        Generate standard duplicate detection report.
        
        Returns:
            Formatted report string
        """
        return self.generate_enhanced_report()
    
    def get_duplicate_statistics(self) -> Dict:
        """
        Get comprehensive statistics about duplicates found.
        
        Returns:
            Dictionary with duplicate statistics
        """
        if not self.duplicate_groups:
            return {
                'total_duplicate_groups': 0,
                'total_duplicate_files': 0,
                'total_space_used': 0,
                'total_space_used_gb': 0.0,
                'potential_space_saved': 0,
                'potential_space_saved_gb': 0.0,
                'space_efficiency': 0.0
            }
        
        total_duplicate_files = sum(len(group.episodes) for group in self.duplicate_groups)
        total_space_used = sum(group.total_size for group in self.duplicate_groups)
        potential_space_saved = sum(group.potential_space_saved for group in self.duplicate_groups)
        
        space_efficiency = (potential_space_saved / total_space_used * 100) if total_space_used > 0 else 0
        
        return {
            'total_duplicate_groups': len(self.duplicate_groups),
            'total_duplicate_files': total_duplicate_files,
            'total_space_used': total_space_used,
            'total_space_used_gb': total_space_used / (1024**3),
            'potential_space_saved': potential_space_saved,
            'potential_space_saved_gb': potential_space_saved / (1024**3),
            'space_efficiency': space_efficiency
        }
    
    def get_duplicates_for_show(self, show_name: str) -> List[DuplicateGroup]:
        """
        Get duplicate groups for a specific show.
        
        Args:
            show_name: Name of the show to search for
            
        Returns:
            List of duplicate groups for the specified show
        """
        show_name_lower = show_name.lower()
        return [
            group for group in self.duplicate_groups
            if show_name_lower in group.show_name.lower()
        ]
    
    # ===== DELETION FUNCTIONALITY =====
    
    def create_deletion_plan(self, 
                           deletion_mode: DeletionMode = DeletionMode.DRY_RUN,
                           specific_groups: Optional[List[DuplicateGroup]] = None,
                           min_confidence_score: float = 80.0) -> DeletionPlan:
        """
        Create a plan for deleting duplicate files.
        
        Args:
            deletion_mode: How to handle deletions (dry_run, trash, permanent)
            specific_groups: Specific groups to delete from (None = all groups)
            min_confidence_score: Minimum confidence score for safe deletion
            
        Returns:
            DeletionPlan with all operations and safety checks
        """
        self.logger.info(f"Creating deletion plan with mode: {deletion_mode.value}")
        
        plan = DeletionPlan(deletion_mode=deletion_mode)
        groups_to_process = specific_groups or self.duplicate_groups
        
        for group in groups_to_process:
            if not group.recommended_removals:
                continue
            
            # Only include high-confidence removals
            group_confidence = self._calculate_group_confidence(group)
            if group_confidence < min_confidence_score:
                self.logger.debug(f"Skipping group {group.episode_id} - confidence {group_confidence:.1f} < {min_confidence_score}")
                continue
            
            # Create deletion operations for recommended removals
            for episode in group.recommended_removals:
                reason = self._get_deletion_reason(group, episode)
                operation = DeletionOperation(
                    episode=episode,
                    deletion_mode=deletion_mode,
                    reason=reason,
                    requires_confirmation=(deletion_mode != DeletionMode.DRY_RUN)
                )
                
                # Run safety checks
                self._run_safety_checks(operation)
                plan.add_operation(operation)
        
        self.logger.info(f"Created deletion plan with {len(plan.operations)} operations")
        return plan
    
    def _calculate_group_confidence(self, group: DuplicateGroup) -> float:
        """Calculate confidence score for a duplicate group."""
        confidence = 50.0  # Base confidence
        
        # Higher confidence for clear quality differences
        if group.recommended_action == DuplicateAction.KEEP_BEST_QUALITY:
            quality_scores = [ep.get_quality_score() for ep in group.episodes]
            if len(set(quality_scores)) > 1:
                confidence += 30.0
        
        # Higher confidence for significant size differences
        sizes = [ep.file_size for ep in group.episodes]
        max_size = max(sizes)
        min_size = min(sizes)
        if max_size > min_size * 1.5:  # 50% size difference
            confidence += 20.0
        
        # Lower confidence for same quality episodes
        qualities = [ep.quality for ep in group.episodes]
        if len(set(qualities)) == 1:
            confidence -= 10.0
        
        # Higher confidence for clear source differences
        sources = [ep.source for ep in group.episodes if ep.source]
        if len(set(sources)) > 1:
            confidence += 10.0
        
        return min(100.0, confidence)
    
    def _get_deletion_reason(self, group: DuplicateGroup, episode: Episode) -> str:
        """Get human-readable reason for deleting this episode."""
        if group.recommended_keeper:
            keeper = group.recommended_keeper
            if episode.quality != keeper.quality:
                return f"Lower quality ({episode.quality.value} vs {keeper.quality.value})"
            elif episode.file_size < keeper.file_size:
                size_diff = (keeper.file_size - episode.file_size) / (1024 * 1024)
                return f"Smaller file ({size_diff:.1f}MB smaller)"
            elif episode.source and keeper.source and episode.source != keeper.source:
                return f"Lower quality source ({episode.source} vs {keeper.source})"
        
        return "Duplicate episode"
    
    def _run_safety_checks(self, operation: DeletionOperation) -> None:
        """Run all safety checks on a deletion operation."""
        episode = operation.episode
        
        # Check if file exists and is accessible
        try:
            if episode.file_path.exists() and episode.file_path.is_file():
                operation.safety_checks[SafetyCheck.FILE_EXISTS] = True
            else:
                operation.add_safety_warning("File does not exist or is not accessible")
        except Exception as e:
            operation.add_safety_warning(f"Cannot access file: {e}")
        
        # Check if file is not locked/in use
        try:
            # Try to open file in exclusive mode briefly
            with open(episode.file_path, 'r+b') as f:
                operation.safety_checks[SafetyCheck.FILE_NOT_LOCKED] = True
        except (PermissionError, OSError):
            operation.add_safety_warning("File appears to be in use or locked")
        except Exception:
            # File might not exist, that's handled by FILE_EXISTS check
            pass
        
        # Check if file size is reasonable (not suspiciously small/large)
        if episode.size_mb > 0.1:  # At least 100KB
            if episode.size_mb < 50000:  # Less than 50GB (reasonable for TV)
                operation.safety_checks[SafetyCheck.SIZE_REASONABLE] = True
            else:
                operation.add_safety_warning(f"File is very large: {episode.size_mb:.1f}MB")
        else:
            operation.add_safety_warning(f"File is very small: {episode.size_mb:.1f}MB")
        
        # User confirmation will be handled during execution
        if not operation.requires_confirmation:
            operation.safety_checks[SafetyCheck.USER_CONFIRMATION] = True
    
    def execute_deletion_plan(self, plan: DeletionPlan, 
                            force: bool = False,
                            progress_callback: Optional[callable] = None) -> DeletionPlan:
        """
        Execute a deletion plan.
        
        Args:
            plan: The deletion plan to execute
            force: Skip user confirmations (dangerous!)
            progress_callback: Function to call with progress updates
            
        Returns:
            Updated deletion plan with execution results
        """
        if plan.deletion_mode == DeletionMode.DRY_RUN:
            self.logger.info("Dry run mode - no files will be deleted")
            return plan
        
        if not plan.is_executable:
            self.logger.warning("Plan is not executable - no safe operations found")
            return plan
        
        self.logger.info(f"Executing deletion plan with {len(plan.safe_operations)} operations")
        plan.execution_start = datetime.now()
        
        try:
            executed = 0
            for i, operation in enumerate(plan.operations):
                if progress_callback:
                    progress_callback(i, len(plan.operations), operation)
                
                if not operation.can_execute:
                    operation.status = DeletionStatus.SKIPPED
                    continue
                
                # Handle user confirmation
                if operation.requires_confirmation and not force:
                    if not self._confirm_deletion(operation):
                        operation.status = DeletionStatus.CANCELLED
                        operation.user_confirmed = False
                        continue
                    operation.user_confirmed = True
                    operation.safety_checks[SafetyCheck.USER_CONFIRMATION] = True
                
                # Execute the deletion
                success = self._execute_single_deletion(operation)
                if success:
                    operation.status = DeletionStatus.SUCCESS
                    executed += 1
                else:
                    operation.status = DeletionStatus.FAILED
                
                operation.timestamp = datetime.now()
        
        except KeyboardInterrupt:
            self.logger.info("Deletion interrupted by user")
            for op in plan.operations:
                if op.status == DeletionStatus.PENDING:
                    op.status = DeletionStatus.CANCELLED
        
        finally:
            plan.execution_end = datetime.now()
            
        self.logger.info(f"Deletion plan completed - {executed} files processed")
        return plan
    
    def _confirm_deletion(self, operation: DeletionOperation) -> bool:
        """
        Get user confirmation for deletion (this would be overridden in CLI).
        Default implementation for safety.
        """
        return False  # Default to not delete for safety
    
    def _execute_single_deletion(self, operation: DeletionOperation) -> bool:
        """Execute a single file deletion operation."""
        try:
            episode = operation.episode
            
            if operation.deletion_mode == DeletionMode.TRASH:
                # Move to system trash if available
                if self._move_to_trash(episode.file_path):
                    operation.backup_location = self._get_trash_location()
                    self.logger.info(f"Moved to trash: {episode.filename}")
                    return True
                else:
                    operation.error_message = "Failed to move to trash"
                    return False
            
            elif operation.deletion_mode == DeletionMode.PERMANENT:
                # Permanent deletion
                episode.file_path.unlink()
                self.logger.info(f"Permanently deleted: {episode.filename}")
                return True
            
        except Exception as e:
            operation.error_message = str(e)
            self.logger.error(f"Failed to delete {episode.filename}: {e}")
            return False
        
        return False
    
    def _move_to_trash(self, file_path: Path) -> bool:
        """Move file to system trash/recycle bin."""
        try:
            # Try using send2trash if available (safer)
            try:
                import send2trash
                send2trash.send2trash(str(file_path))
                return True
            except ImportError:
                pass
            
            # Fallback: move to a local trash folder
            trash_dir = file_path.parent / '.trash'
            trash_dir.mkdir(exist_ok=True)
            
            # Generate unique name if file already exists in trash
            trash_path = trash_dir / file_path.name
            counter = 1
            while trash_path.exists():
                stem = file_path.stem
                suffix = file_path.suffix
                trash_path = trash_dir / f"{stem}_{counter}{suffix}"
                counter += 1
            
            shutil.move(str(file_path), str(trash_path))
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to move to trash: {e}")
            return False
    
    def _get_trash_location(self) -> Optional[Path]:
        """Get the location where files are moved to trash."""
        # This is a simplified implementation
        return None
    
    def generate_deletion_report(self, plan: DeletionPlan) -> str:
        """Generate a comprehensive deletion report."""
        report = []
        report.append("TV FILE ORGANIZER - DUPLICATE DELETION REPORT")
        report.append("=" * 60)
        report.append("")
        
        # Plan summary
        report.append("DELETION PLAN SUMMARY:")
        report.append("-" * 20)
        report.append(f"Mode: {plan.deletion_mode.value.upper()}")
        report.append(f"Total Operations: {plan.total_files}")
        report.append(f"Safe Operations: {len(plan.safe_operations)}")
        report.append(f"Estimated Space Saved: {plan.estimated_space_saved_mb:.1f} MB")
        
        if plan.execution_duration:
            report.append(f"Execution Time: {plan.execution_duration:.1f} seconds")
        
        report.append("")
        
        # Status summary
        status_summary = plan.get_status_summary()
        if status_summary:
            report.append("OPERATION STATUS SUMMARY:")
            report.append("-" * 25)
            for status, count in status_summary.items():
                report.append(f"  {status.title()}: {count}")
            report.append("")
        
        # Detailed operations
        if plan.operations:
            report.append("DETAILED OPERATIONS:")
            report.append("-" * 20)
            
            for status in DeletionStatus:
                ops_with_status = [op for op in plan.operations if op.status == status]
                if ops_with_status:
                    report.append(f"\n{status.value.upper()} ({len(ops_with_status)}):")
                    for op in ops_with_status[:10]:  # Limit to first 10 per status
                        report.append(f"  {op.get_summary()}")
                        if op.error_message:
                            report.append(f"    Error: {op.error_message}")
                        if op.safety_warnings:
                            for warning in op.safety_warnings:
                                report.append(f"    Warning: {warning}")
                    
                    if len(ops_with_status) > 10:
                        report.append(f"  ... and {len(ops_with_status) - 10} more")
        
        return "\n".join(report)