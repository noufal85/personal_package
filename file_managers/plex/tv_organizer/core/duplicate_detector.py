"""
Phase 0: Duplicate Detection

Identifies duplicate TV episodes across all configured TV directories.
Handles various filename formats, quality indicators, and provides recommendations.
"""

import logging
from pathlib import Path
from typing import List, Dict, Set, Optional, Tuple
from collections import defaultdict
import re

from ..models.episode import Episode, Quality, EpisodeStatus
from ..models.duplicate import DuplicateGroup, DuplicateAction
from ...utils.tv_scanner import extract_tv_info_from_filename, is_video_file
from ...config.config import config


class DuplicateDetector:
    """
    Detects duplicate TV episodes across multiple directories.
    
    Phase 0 of the TV File Organizer project.
    """
    
    def __init__(self, tv_directories: Optional[List[str]] = None):
        """
        Initialize the duplicate detector.
        
        Args:
            tv_directories: List of TV directories to scan. If None, uses config.
        """
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
        # This is a simplified version for Phase 0
        # More detailed status detection will be in Phase 1
        
        parent_name = file_path.parent.name.lower()
        
        # Check if in a season folder
        if re.search(r'season\s+\d+', parent_name) or re.search(r's\d+', parent_name):
            return EpisodeStatus.ORGANIZED
        
        # Check if in root TV directory
        if file_path.parent in [Path(d) for d in self.tv_directories]:
            return EpisodeStatus.LOOSE_ROOT
        
        # Default to loose for now
        return EpisodeStatus.LOOSE_GENERIC
    
    def detect_duplicates(self) -> List[DuplicateGroup]:
        """
        Detect duplicate episodes from the scanned episodes.
        
        Returns:
            List of duplicate groups found
        """
        if not self.episodes:
            self.logger.warning("No episodes loaded. Run scan_all_directories() first.")
            return []
        
        self.logger.info("Detecting duplicates...")
        
        # Group episodes by show/season/episode
        episode_groups = defaultdict(list)
        
        for episode in self.episodes:
            episode_id = episode.episode_id
            episode_groups[episode_id].append(episode)
        
        # Find groups with duplicates
        self.duplicate_groups.clear()
        duplicate_count = 0
        
        for episode_id, episodes in episode_groups.items():
            if len(episodes) > 1:
                # Create duplicate group
                first_episode = episodes[0]
                duplicate_group = DuplicateGroup(
                    show_name=first_episode.show_name,
                    season=first_episode.season,
                    episode=first_episode.episode,
                    episodes=episodes
                )
                
                # Analyze the duplicates
                duplicate_group.analyze_duplicates()
                
                self.duplicate_groups.append(duplicate_group)
                duplicate_count += len(episodes)
        
        self.logger.info(f"Found {len(self.duplicate_groups)} duplicate groups "
                        f"containing {duplicate_count} total files")
        
        return self.duplicate_groups
    
    def get_duplicate_statistics(self) -> Dict[str, any]:
        """
        Get statistics about detected duplicates.
        
        Returns:
            Dictionary with duplicate statistics
        """
        if not self.duplicate_groups:
            return {
                'total_duplicate_groups': 0,
                'total_duplicate_files': 0,
                'total_space_used': 0,
                'potential_space_saved': 0,
                'space_efficiency': 0.0
            }
        
        total_files = sum(group.duplicate_count for group in self.duplicate_groups)
        total_space = sum(group.total_size for group in self.duplicate_groups)
        potential_saved = sum(group.potential_space_saved for group in self.duplicate_groups)
        
        space_efficiency = (potential_saved / total_space * 100) if total_space > 0 else 0
        
        return {
            'total_duplicate_groups': len(self.duplicate_groups),
            'total_duplicate_files': total_files,
            'total_space_used': total_space,
            'total_space_used_gb': total_space / (1024**3),
            'potential_space_saved': potential_saved,
            'potential_space_saved_gb': potential_saved / (1024**3),
            'space_efficiency': space_efficiency
        }
    
    def generate_report(self) -> str:
        """
        Generate a comprehensive duplicate detection report.
        
        Returns:
            Formatted report string
        """
        if not self.duplicate_groups:
            return "No duplicates detected."
        
        stats = self.get_duplicate_statistics()
        
        report = []
        report.append("TV EPISODE DUPLICATE DETECTION REPORT")
        report.append("=" * 50)
        report.append("")
        
        # Summary statistics
        report.append("SUMMARY:")
        report.append(f"  Total Episodes Scanned: {len(self.episodes)}")
        report.append(f"  Duplicate Groups Found: {stats['total_duplicate_groups']}")
        report.append(f"  Total Duplicate Files: {stats['total_duplicate_files']}")
        report.append(f"  Space Used by Duplicates: {stats['total_space_used_gb']:.2f} GB")
        report.append(f"  Potential Space Savings: {stats['potential_space_saved_gb']:.2f} GB")
        report.append(f"  Space Efficiency Gain: {stats['space_efficiency']:.1f}%")
        report.append("")
        
        # Detailed duplicate groups
        report.append("DUPLICATE GROUPS:")
        report.append("-" * 30)
        
        # Sort by potential space savings (largest first)
        sorted_groups = sorted(
            self.duplicate_groups,
            key=lambda g: g.potential_space_saved,
            reverse=True
        )
        
        for i, group in enumerate(sorted_groups, 1):
            report.append(f"\n{i}. {group.get_summary()}")
            report.append(f"   Action: {group.recommended_action.value}")
            
            if group.recommended_keeper:
                report.append(f"   Keep: {group.recommended_keeper.filename}")
                report.append(f"         ({group.recommended_keeper.quality.value}, "
                            f"{group.recommended_keeper.size_mb:.1f}MB)")
            
            if group.recommended_removals:
                report.append("   Remove:")
                for episode in group.recommended_removals:
                    report.append(f"     - {episode.filename}")
                    report.append(f"       ({episode.quality.value}, {episode.size_mb:.1f}MB)")
            
            if group.analysis_notes:
                report.append("   Notes:")
                for note in group.analysis_notes:
                    report.append(f"     • {note}")
        
        return "\n".join(report)
    
    def get_shows_with_duplicates(self) -> Set[str]:
        """
        Get a set of show names that have duplicates.
        
        Returns:
            Set of show names with duplicate episodes
        """
        return {group.show_name for group in self.duplicate_groups}
    
    def get_duplicates_for_show(self, show_name: str) -> List[DuplicateGroup]:
        """
        Get all duplicate groups for a specific show.
        
        Args:
            show_name: Name of the show
            
        Returns:
            List of duplicate groups for the show
        """
        return [group for group in self.duplicate_groups 
                if group.show_name.lower() == show_name.lower()]