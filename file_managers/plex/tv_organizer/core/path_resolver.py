"""
Path Resolver for TV File Organizer Phase 2.

This module implements intelligent path resolution for TV episodes,
determining optimal destinations for file organization.
"""

import re
import shutil
import logging
from pathlib import Path
from typing import List, Dict, Set, Optional, Tuple
from collections import defaultdict
import difflib

from ..models.episode import Episode, EpisodeStatus
from ..models.path_resolution import (
    ShowDirectory, PathDestination, PathResolution, ResolutionPlan,
    ResolutionType, DestinationType, ConfidenceLevel
)
from ...utils.tv_scanner import extract_tv_info_from_filename, is_video_file
from ...config.config import config


class PathResolver:
    """
    Intelligent path resolver that analyzes TV directory structures
    and determines optimal destinations for episode organization.
    """
    
    def __init__(self, tv_directories: Optional[List[str]] = None):
        """Initialize the path resolver."""
        self.tv_directories = tv_directories or config.tv_directories
        self.logger = logging.getLogger(__name__)
        
        # Discovered show directories
        self.show_directories: Dict[str, ShowDirectory] = {}
        self.show_name_index: Dict[str, List[ShowDirectory]] = defaultdict(list)
        
        # Analysis results
        self.episodes: List[Episode] = []
        self.resolutions: List[PathResolution] = []
        
        # Configuration
        self.min_free_space_gb = 1.0  # Minimum free space to leave on disk
        self.similarity_threshold = 0.8  # Minimum similarity for show name matching
        
        # Season folder patterns
        self.season_patterns = [
            r'^Season\s+(\d+)$',
            r'^Season\s+(\d+)\s+',
            r'^S(\d+)$',
            r'^S(\d+)\s+',
            r'^(\d+)$',  # Just a number
        ]
    
    def scan_tv_directories(self) -> List[Episode]:
        """
        Scan TV directories and build comprehensive directory structure map.
        
        Returns:
            List of all episodes found
        """
        self.logger.info(f"Scanning {len(self.tv_directories)} TV directories for path resolution")
        
        self.episodes.clear()
        self.show_directories.clear()
        self.show_name_index.clear()
        
        for tv_dir in self.tv_directories:
            tv_path = Path(tv_dir)
            if not tv_path.exists():
                self.logger.warning(f"TV directory does not exist: {tv_dir}")
                continue
                
            self.logger.info(f"Scanning TV directory: {tv_dir}")
            self._scan_tv_directory(tv_path)
        
        self.logger.info(f"Found {len(self.show_directories)} show directories")
        self.logger.info(f"Found {len(self.episodes)} total episodes")
        
        return self.episodes
    
    def _scan_tv_directory(self, tv_path: Path):
        """Scan a single TV directory for show folders and episodes."""
        for item in tv_path.iterdir():
            if not item.is_dir():
                # Check for loose video files in TV root
                if is_video_file(item):
                    episode = self._create_episode_from_file(item)
                    if episode:
                        episode.status = EpisodeStatus.LOOSE_ROOT
                        self.episodes.append(episode)
                continue
            
            # Check if this looks like a show directory
            show_dir = self._analyze_show_directory(item, tv_path)
            if show_dir:
                normalized_name = self._normalize_show_name(show_dir.actual_name)
                self.show_directories[normalized_name] = show_dir
                
                # Add to name index for fuzzy matching
                for variation in show_dir.show_name_variations:
                    self.show_name_index[variation.lower()].append(show_dir)
    
    def _analyze_show_directory(self, show_path: Path, tv_base: Path) -> Optional[ShowDirectory]:
        """Analyze a potential show directory."""
        show_name = show_path.name
        normalized_name = self._normalize_show_name(show_name)
        
        show_dir = ShowDirectory(
            path=show_path,
            normalized_name=normalized_name,
            actual_name=show_name,
            tv_base_directory=tv_base
        )
        
        episodes_found = []
        season_folders = []
        seasons_present = set()
        
        # Scan contents of show directory
        for item in show_path.iterdir():
            if item.is_file() and is_video_file(item):
                # Loose episode in show root
                episode = self._create_episode_from_file(item)
                if episode:
                    episode.status = EpisodeStatus.ORGANIZED  # In show folder
                    episodes_found.append(episode)
                    seasons_present.add(episode.season)
                    show_dir.has_mixed_structure = True
                    
            elif item.is_dir():
                # Check if this is a season folder
                season_num = self._detect_season_folder(item.name)
                if season_num is not None:
                    season_folders.append(item)
                    seasons_present.add(season_num)
                    
                    # Scan season folder for episodes
                    for ep_file in item.iterdir():
                        if ep_file.is_file() and is_video_file(ep_file):
                            episode = self._create_episode_from_file(ep_file)
                            if episode:
                                episode.status = EpisodeStatus.ORGANIZED
                                episodes_found.append(episode)
                                seasons_present.add(episode.season)
        
        # Only consider this a show directory if it has episodes
        if episodes_found:
            show_dir.season_folders = season_folders
            show_dir.loose_episodes = [ep for ep in episodes_found if ep.status != EpisodeStatus.ORGANIZED]
            show_dir.total_episodes = len(episodes_found)
            show_dir.total_size_gb = sum(ep.size_gb for ep in episodes_found)
            show_dir.seasons_present = seasons_present
            
            # Add episodes to master list
            self.episodes.extend(episodes_found)
            
            return show_dir
        
        return None
    
    def _detect_season_folder(self, folder_name: str) -> Optional[int]:
        """Detect if a folder name represents a season folder."""
        for pattern in self.season_patterns:
            match = re.search(pattern, folder_name, re.IGNORECASE)
            if match:
                try:
                    return int(match.group(1))
                except (ValueError, IndexError):
                    continue
        
        return None
    
    def _create_episode_from_file(self, file_path: Path) -> Optional[Episode]:
        """Create an Episode object from a video file."""
        try:
            tv_info = extract_tv_info_from_filename(file_path.name)
            if not tv_info:
                return None
            
            file_size = file_path.stat().st_size
            
            # tv_info is a tuple (show_name, season, episode)
            show_name, season, episode_num = tv_info
            
            episode = Episode(
                file_path=file_path,
                file_size=file_size,
                file_extension=file_path.suffix,
                show_name=show_name,
                season=season,
                episode=episode_num,
                episode_title=None,
            )
            
            # Set quality and source from filename
            episode.quality = self._detect_quality(file_path.name)
            episode.source = self._detect_source(file_path.name)
            
            return episode
            
        except Exception as e:
            self.logger.warning(f"Failed to create episode from {file_path}: {e}")
            return None
    
    def _detect_quality(self, filename: str):
        """Detect video quality from filename."""
        from ..models.episode import Quality
        
        filename_lower = filename.lower()
        
        if any(pattern in filename_lower for pattern in ['2160p', '4k', 'uhd']):
            return Quality.UHD_4K
        elif '1080p' in filename_lower:
            return Quality.FHD_1080P
        elif '720p' in filename_lower:
            return Quality.HD_720P
        elif '480p' in filename_lower:
            return Quality.SD_480P
        else:
            return Quality.UNKNOWN
    
    def _detect_source(self, filename: str) -> Optional[str]:
        """Detect video source from filename."""
        filename_lower = filename.lower()
        
        sources = {
            'BluRay': ['bluray', 'blu-ray', 'bdrip', 'brrip'],
            'WEB-DL': ['web-dl', 'webdl'],
            'WEBRip': ['webrip', 'web-rip'],
            'HDTV': ['hdtv'],
            'DVDRip': ['dvdrip', 'dvd-rip']
        }
        
        for source, patterns in sources.items():
            if any(pattern in filename_lower for pattern in patterns):
                return source
        
        return None
    
    def _normalize_show_name(self, name: str) -> str:
        """Normalize show name for matching."""
        # Remove common prefixes/suffixes
        name = re.sub(r'^\[.*?\]\s*', '', name)  # Remove [prefix]
        name = re.sub(r'\s*\(\d{4}\).*$', '', name)  # Remove (year) and everything after
        
        # Normalize spacing and punctuation
        name = re.sub(r'[._-]+', ' ', name)
        name = re.sub(r'\s+', ' ', name)
        name = name.strip()
        
        return name
    
    def find_show_matches(self, episode: Episode) -> List[Tuple[ShowDirectory, float]]:
        """
        Find show directories that could match an episode.
        
        Returns:
            List of (ShowDirectory, similarity_score) tuples, sorted by score
        """
        episode_show = self._normalize_show_name(episode.show_name)
        matches = []
        
        # Check all show directories
        for show_dir in self.show_directories.values():
            # Check exact match first
            if episode_show.lower() == show_dir.normalized_name.lower():
                matches.append((show_dir, 1.0))
                continue
            
            # Check fuzzy similarity
            similarity = difflib.SequenceMatcher(None, 
                                                episode_show.lower(), 
                                                show_dir.normalized_name.lower()).ratio()
            
            if similarity >= self.similarity_threshold:
                matches.append((show_dir, similarity))
            
            # Also check against variations
            for variation in show_dir.show_name_variations:
                var_similarity = difflib.SequenceMatcher(None, 
                                                        episode_show.lower(), 
                                                        variation.lower()).ratio()
                if var_similarity >= self.similarity_threshold:
                    matches.append((show_dir, var_similarity))
                    break
        
        # Sort by similarity score (highest first) and remove duplicates
        seen_dirs = set()
        unique_matches = []
        for show_dir, score in sorted(matches, key=lambda x: x[1], reverse=True):
            if show_dir.path not in seen_dirs:
                unique_matches.append((show_dir, score))
                seen_dirs.add(show_dir.path)
        
        return unique_matches
    
    def resolve_episode_paths(self, episodes: Optional[List[Episode]] = None) -> List[PathResolution]:
        """
        Resolve optimal paths for a list of episodes.
        
        Args:
            episodes: Episodes to resolve (defaults to all scanned episodes)
            
        Returns:
            List of path resolutions
        """
        if episodes is None:
            episodes = self.episodes
        
        self.logger.info(f"Resolving paths for {len(episodes)} episodes")
        self.resolutions.clear()
        
        # Group episodes that need resolution
        episodes_needing_resolution = [
            ep for ep in episodes 
            if ep.status in [EpisodeStatus.LOOSE_ROOT, EpisodeStatus.LOOSE_GENERIC]
        ]
        
        self.logger.info(f"{len(episodes_needing_resolution)} episodes need path resolution")
        
        # Group episodes by show for batch processing
        episodes_by_show = defaultdict(list)
        for episode in episodes_needing_resolution:
            normalized_show = self._normalize_show_name(episode.show_name)
            episodes_by_show[normalized_show].append(episode)
        
        # Resolve each show's episodes
        for show_name, show_episodes in episodes_by_show.items():
            self.logger.info(f"Resolving {len(show_episodes)} episodes for show: {show_name}")
            show_resolutions = self._resolve_show_episodes(show_episodes)
            self.resolutions.extend(show_resolutions)
        
        return self.resolutions
    
    def _resolve_show_episodes(self, episodes: List[Episode]) -> List[PathResolution]:
        """Resolve path for episodes from a single show."""
        resolutions = []
        
        if not episodes:
            return resolutions
        
        # Find matching show directories
        sample_episode = episodes[0]
        show_matches = self.find_show_matches(sample_episode)
        
        if show_matches:
            # We have existing show directory(ies)
            best_match, similarity = show_matches[0]
            
            # Group episodes by season
            episodes_by_season = defaultdict(list)
            for episode in episodes:
                episodes_by_season[episode.season].append(episode)
            
            # Create resolution for each season
            for season, season_episodes in episodes_by_season.items():
                resolution = self._create_existing_show_resolution(
                    season_episodes, best_match, season, similarity
                )
                resolutions.append(resolution)
        
        else:
            # No existing show directory - need to create new one
            # Group by season for organization
            episodes_by_season = defaultdict(list)
            for episode in episodes:
                episodes_by_season[episode.season].append(episode)
            
            for season, season_episodes in episodes_by_season.items():
                resolution = self._create_new_show_resolution(season_episodes, season)
                resolutions.append(resolution)
        
        return resolutions
    
    def _create_existing_show_resolution(self, episodes: List[Episode], 
                                       show_dir: ShowDirectory, season: int,
                                       similarity: float) -> PathResolution:
        """Create resolution for episodes going to existing show directory."""
        
        # Determine best destination within the show
        destination = self._find_best_season_destination(episodes, show_dir, season)
        
        # Create resolution
        resolution = PathResolution(
            episodes=episodes,
            resolution_type=ResolutionType.MOVE_TO_EXISTING_SHOW,
            primary_destination=destination
        )
        
        # Set confidence based on similarity and destination quality
        if similarity >= 0.95 and destination.total_score >= 80:
            resolution.confidence = ConfidenceLevel.HIGH
        elif similarity >= 0.85 and destination.total_score >= 60:
            resolution.confidence = ConfidenceLevel.MEDIUM
        elif similarity >= 0.8 and destination.total_score >= 40:
            resolution.confidence = ConfidenceLevel.LOW
        else:
            resolution.confidence = ConfidenceLevel.UNCERTAIN
        
        # Add reasoning
        resolution.reasoning.append(f"Found existing show directory: {show_dir.actual_name}")
        resolution.reasoning.append(f"Show name similarity: {similarity:.1%}")
        resolution.reasoning.append(f"Destination score: {destination.total_score:.1f}")
        
        # Check for conflicts
        if destination.conflicts:
            resolution.warnings.extend(destination.conflicts)
            resolution.requires_user_confirmation = True
        
        # Estimate time and space
        resolution.estimated_space_needed_gb = sum(ep.size_gb for ep in episodes)
        resolution.estimated_time_seconds = len(episodes) * 2.0  # ~2 seconds per episode
        
        return resolution
    
    def _find_best_season_destination(self, episodes: List[Episode], 
                                    show_dir: ShowDirectory, season: int) -> PathDestination:
        """Find the best destination for episodes within a show directory."""
        destinations = []
        
        # Option 1: Existing season folder
        season_folder = self._find_season_folder(show_dir, season)
        if season_folder:
            dest = PathDestination(
                path=season_folder,
                destination_type=DestinationType.SEASON_FOLDER,
                show_directory=show_dir,
                season_number=season
            )
            dest.match_score = 90  # High match - correct season folder
            dest.organization_score = 80  # Good organization
            dest.space_score = self._calculate_space_score(season_folder)
            dest.proximity_score = 90  # Very close to related content
            destinations.append(dest)
        
        # Option 2: Create new season folder
        new_season_path = show_dir.path / f"Season {season:02d}"
        dest = PathDestination(
            path=new_season_path,
            destination_type=DestinationType.SEASON_FOLDER,
            show_directory=show_dir,
            season_number=season,
            requires_creation=True
        )
        dest.match_score = 85  # Good match - correct show, new season folder
        dest.organization_score = 85  # Good organization when created
        dest.space_score = self._calculate_space_score(show_dir.path)
        dest.proximity_score = 95  # Very close to related content
        destinations.append(dest)
        
        # Option 3: Show root (if show has mixed structure)
        if show_dir.has_mixed_structure:
            dest = PathDestination(
                path=show_dir.path,
                destination_type=DestinationType.SHOW_ROOT,
                show_directory=show_dir,
                season_number=season
            )
            dest.match_score = 75  # Good match but less organized
            dest.organization_score = 60  # Mixed structure is less ideal
            dest.space_score = self._calculate_space_score(show_dir.path)
            dest.proximity_score = 80  # Close to related content
            destinations.append(dest)
        
        # Return the best destination
        return max(destinations, key=lambda d: d.total_score)
    
    def _find_season_folder(self, show_dir: ShowDirectory, season: int) -> Optional[Path]:
        """Find existing season folder for a specific season."""
        for folder in show_dir.season_folders:
            detected_season = self._detect_season_folder(folder.name)
            if detected_season == season:
                return folder
        return None
    
    def _calculate_space_score(self, path: Path) -> float:
        """Calculate space availability score for a destination."""
        try:
            stat = shutil.disk_usage(path)
            free_gb = stat.free / (1024**3)
            
            if free_gb >= 100:
                return 100.0
            elif free_gb >= 50:
                return 80.0
            elif free_gb >= 20:
                return 60.0
            elif free_gb >= 10:
                return 40.0
            elif free_gb >= 5:
                return 20.0
            else:
                return 0.0
                
        except Exception:
            return 50.0  # Default score if can't determine space
    
    def _create_new_show_resolution(self, episodes: List[Episode], season: int) -> PathResolution:
        """Create resolution for episodes that need a new show directory."""
        
        # Find best TV directory for new show
        best_tv_dir = self._find_best_tv_directory_for_new_show(episodes)
        
        # Create show directory path
        sample_episode = episodes[0]
        show_name = self._normalize_show_name(sample_episode.show_name)
        new_show_path = best_tv_dir / show_name
        
        # Create destination
        if len(set(ep.season for ep in episodes)) == 1:
            # Single season - can create season folder
            season_path = new_show_path / f"Season {season:02d}"
            destination = PathDestination(
                path=season_path,
                destination_type=DestinationType.SEASON_FOLDER,
                season_number=season,
                requires_creation=True
            )
            destination.match_score = 80  # Good match for new show
            destination.organization_score = 90  # Will be well organized
        else:
            # Multiple seasons - create in show root
            destination = PathDestination(
                path=new_show_path,
                destination_type=DestinationType.SHOW_ROOT,
                requires_creation=True
            )
            destination.match_score = 75  # Good match but mixed seasons
            destination.organization_score = 70  # Less organized
        
        destination.space_score = self._calculate_space_score(best_tv_dir)
        destination.proximity_score = 50  # No existing related content
        
        # Create resolution
        resolution = PathResolution(
            episodes=episodes,
            resolution_type=ResolutionType.CREATE_NEW_SHOW,
            primary_destination=destination
        )
        
        # Set confidence - lower for new shows
        if destination.total_score >= 75:
            resolution.confidence = ConfidenceLevel.MEDIUM
        elif destination.total_score >= 60:
            resolution.confidence = ConfidenceLevel.LOW
        else:
            resolution.confidence = ConfidenceLevel.UNCERTAIN
        
        # Add reasoning
        resolution.reasoning.append(f"No existing show directory found for: {show_name}")
        resolution.reasoning.append(f"Will create new show directory in: {best_tv_dir}")
        resolution.reasoning.append(f"Destination score: {destination.total_score:.1f}")
        
        # New show creation requires confirmation
        resolution.requires_user_confirmation = True
        
        # Estimate time and space
        resolution.estimated_space_needed_gb = sum(ep.size_gb for ep in episodes)
        resolution.estimated_time_seconds = len(episodes) * 3.0  # ~3 seconds per episode (includes creation)
        
        return resolution
    
    def _find_best_tv_directory_for_new_show(self, episodes: List[Episode]) -> Path:
        """Find the best TV base directory for creating a new show folder."""
        best_dir = None
        best_score = 0
        
        for tv_dir in self.tv_directories:
            tv_path = Path(tv_dir)
            if not tv_path.exists():
                continue
            
            score = 0
            
            # Space availability (50% of score)
            space_score = self._calculate_space_score(tv_path)
            score += space_score * 0.5
            
            # Number of shows in directory (25% - prefer directories with more shows)
            show_count = len([d for d in tv_path.iterdir() if d.is_dir()])
            show_score = min(100, show_count * 5)  # 5 points per show, max 100
            score += show_score * 0.25
            
            # Directory preference (25% - prefer first directory in config)
            preference_score = 100 - (self.tv_directories.index(tv_dir) * 20)
            score += max(0, preference_score) * 0.25
            
            if score > best_score:
                best_score = score
                best_dir = tv_path
        
        return best_dir or Path(self.tv_directories[0])
    
    def create_resolution_plan(self, resolutions: Optional[List[PathResolution]] = None) -> ResolutionPlan:
        """
        Create an execution plan for path resolutions.
        
        Args:
            resolutions: Resolutions to plan (defaults to all current resolutions)
            
        Returns:
            Complete resolution plan
        """
        if resolutions is None:
            resolutions = self.resolutions
        
        plan = ResolutionPlan(resolutions=resolutions)
        
        # Create execution order (prioritize high confidence, then by size)
        resolution_scores = []
        for i, resolution in enumerate(resolutions):
            confidence_score = {
                ConfidenceLevel.HIGH: 100,
                ConfidenceLevel.MEDIUM: 75,
                ConfidenceLevel.LOW: 50,
                ConfidenceLevel.UNCERTAIN: 25
            }.get(resolution.confidence, 0)
            
            # Combine confidence with inverse size (smaller operations first)
            size_score = max(0, 100 - resolution.total_size_gb)
            total_score = confidence_score * 0.7 + size_score * 0.3
            
            resolution_scores.append((i, total_score))
        
        # Sort by score (highest first)
        plan.execution_order = [i for i, score in sorted(resolution_scores, key=lambda x: x[1], reverse=True)]
        
        return plan
    
    def get_directory_statistics(self) -> Dict:
        """Get statistics about discovered TV directory structure."""
        total_shows = len(self.show_directories)
        total_episodes = len(self.episodes)
        
        # Organization levels
        organized_episodes = len([ep for ep in self.episodes if ep.status == EpisodeStatus.ORGANIZED])
        loose_episodes = total_episodes - organized_episodes
        
        # Show organization scores
        org_scores = [show.organization_score for show in self.show_directories.values()]
        avg_organization = sum(org_scores) / len(org_scores) if org_scores else 0
        
        # TV directory usage
        tv_dir_usage = {}
        for tv_dir in self.tv_directories:
            shows_in_dir = len([s for s in self.show_directories.values() 
                              if str(s.tv_base_directory) == tv_dir])
            tv_dir_usage[tv_dir] = shows_in_dir
        
        return {
            'total_shows': total_shows,
            'total_episodes': total_episodes,
            'organized_episodes': organized_episodes,
            'loose_episodes': loose_episodes,
            'organization_percentage': (organized_episodes / total_episodes * 100) if total_episodes > 0 else 0,
            'average_show_organization_score': avg_organization,
            'tv_directory_usage': tv_dir_usage,
            'shows_needing_attention': len([s for s in self.show_directories.values() if s.organization_score < 70])
        }
    
    def generate_resolution_report(self) -> str:
        """Generate a comprehensive path resolution report."""
        stats = self.get_directory_statistics()
        
        report = []
        report.append("TV FILE ORGANIZER - PATH RESOLUTION ANALYSIS")
        report.append("=" * 60)
        report.append("")
        
        # Directory overview
        report.append("DIRECTORY STRUCTURE OVERVIEW:")
        report.append("-" * 30)
        report.append(f"Total TV Shows: {stats['total_shows']}")
        report.append(f"Total Episodes: {stats['total_episodes']}")
        report.append(f"Organized Episodes: {stats['organized_episodes']} ({stats['organization_percentage']:.1f}%)")
        report.append(f"Loose Episodes: {stats['loose_episodes']}")
        report.append(f"Average Organization Score: {stats['average_show_organization_score']:.1f}/100")
        report.append("")
        
        # TV directory usage
        report.append("TV DIRECTORY USAGE:")
        report.append("-" * 20)
        for tv_dir, show_count in stats['tv_directory_usage'].items():
            report.append(f"  {tv_dir}: {show_count} shows")
        report.append("")
        
        # Resolution summary
        if self.resolutions:
            report.append("PATH RESOLUTION SUMMARY:")
            report.append("-" * 25)
            confidence_counts = defaultdict(int)
            for resolution in self.resolutions:
                confidence_counts[resolution.confidence] += 1
            
            for confidence, count in confidence_counts.items():
                report.append(f"  {confidence.value.title()}: {count} resolutions")
            
            total_episodes_to_resolve = sum(r.episode_count for r in self.resolutions)
            total_size_to_resolve = sum(r.total_size_gb for r in self.resolutions)
            
            report.append(f"  Total Episodes to Resolve: {total_episodes_to_resolve}")
            report.append(f"  Total Size to Resolve: {total_size_to_resolve:.1f} GB")
            report.append("")
        
        # Show directories that need attention
        needs_attention = [s for s in self.show_directories.values() if s.organization_score < 70]
        if needs_attention:
            report.append("SHOWS NEEDING ATTENTION (Organization Score < 70):")
            report.append("-" * 50)
            for show in sorted(needs_attention, key=lambda s: s.organization_score):
                report.append(f"  {show.actual_name}: {show.organization_score:.1f}/100 "
                            f"({show.total_episodes} episodes)")
            report.append("")
        
        return "\n".join(report)