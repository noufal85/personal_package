"""
Path Resolution data models for TV file organization Phase 2.

This module defines data structures for analyzing and resolving optimal
file placement destinations for TV episodes.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Optional, Set, Tuple
from enum import Enum

from .episode import Episode


class ResolutionType(Enum):
    """Type of path resolution needed."""
    MOVE_TO_EXISTING_SHOW = "move_to_existing_show"      # Move to existing show folder
    CREATE_NEW_SHOW = "create_new_show"                  # Create new show folder
    CONSOLIDATE_SEASONS = "consolidate_seasons"          # Move seasons to better location
    ORGANIZE_EPISODES = "organize_episodes"              # Organize loose episodes
    NO_ACTION_NEEDED = "no_action_needed"               # Already properly organized


class DestinationType(Enum):
    """Type of destination location."""
    SHOW_ROOT = "show_root"                             # Show folder root (for season folders)
    SEASON_FOLDER = "season_folder"                     # Specific season folder
    SHOW_SEASON_FOLDER = "show_season_folder"           # Show/Season structure


class ConfidenceLevel(Enum):
    """Confidence level for path resolution recommendations."""
    HIGH = "high"           # 90%+ confidence - safe to execute
    MEDIUM = "medium"       # 70-89% confidence - review recommended
    LOW = "low"            # 50-69% confidence - manual review required
    UNCERTAIN = "uncertain" # <50% confidence - do not execute


@dataclass
class ShowDirectory:
    """
    Represents a show directory found in the TV file system.
    """
    path: Path
    normalized_name: str
    actual_name: str
    tv_base_directory: Path
    season_folders: List[Path] = field(default_factory=list)
    loose_episodes: List[Episode] = field(default_factory=list)
    total_episodes: int = 0
    total_size_gb: float = 0.0
    seasons_present: Set[int] = field(default_factory=set)
    has_mixed_structure: bool = False  # True if has both season folders and loose episodes
    
    def __post_init__(self):
        """Calculate derived properties."""
        if not self.season_folders:
            self.season_folders = []
        if not self.loose_episodes:
            self.loose_episodes = []
        if not self.seasons_present:
            self.seasons_present = set()
    
    @property
    def show_name_variations(self) -> List[str]:
        """Get common variations of the show name for matching."""
        variations = [
            self.actual_name,
            self.normalized_name,
            self.actual_name.replace(' ', '.'),
            self.actual_name.replace(' ', '_'),
            self.actual_name.replace('.', ' '),
            self.actual_name.replace('_', ' '),
            self.actual_name.lower(),
            self.normalized_name.lower()
        ]
        return list(set(variations))  # Remove duplicates
    
    @property
    def organization_score(self) -> float:
        """
        Score how well-organized this show directory is (0-100).
        Higher scores indicate better organization.
        """
        if self.total_episodes == 0:
            return 0.0
        
        score = 0.0
        
        # Season folder organization (40 points max)
        if self.season_folders:
            organized_episodes = sum(1 for folder in self.season_folders 
                                   if folder.exists() and list(folder.glob('*.mkv')) + list(folder.glob('*.mp4')))
            if organized_episodes > 0:
                score += 40 * (organized_episodes / max(self.total_episodes, 1))
        
        # Consistent structure (30 points max)
        if not self.has_mixed_structure:
            score += 30
        
        # Season coverage (20 points max)
        if self.seasons_present:
            expected_seasons = max(self.seasons_present) if self.seasons_present else 1
            coverage = len(self.seasons_present) / expected_seasons
            score += 20 * coverage
        
        # Size indicates content (10 points max)
        if self.total_size_gb > 1.0:  # At least 1GB of content
            score += 10
        
        return min(100.0, score)


@dataclass
class PathDestination:
    """
    Represents a potential destination for an episode or group of episodes.
    """
    path: Path
    destination_type: DestinationType
    show_directory: Optional[ShowDirectory] = None
    season_number: Optional[int] = None
    
    # Scoring factors
    match_score: float = 0.0          # How well episode matches this destination (0-100)
    organization_score: float = 0.0   # How well-organized the destination is (0-100)
    space_score: float = 0.0          # Available space score (0-100)
    proximity_score: float = 0.0      # How close to related content (0-100)
    
    # Metadata
    requires_creation: bool = False    # Whether destination needs to be created
    conflicts: List[str] = field(default_factory=list)
    available_space_gb: Optional[float] = None
    estimated_episodes: int = 0
    
    @property
    def total_score(self) -> float:
        """Calculate weighted total score for this destination."""
        weights = {
            'match': 0.4,        # 40% - How well the episode matches
            'organization': 0.3,  # 30% - How well-organized the destination is
            'space': 0.2,        # 20% - Available space
            'proximity': 0.1     # 10% - Proximity to related content
        }
        
        return (
            self.match_score * weights['match'] +
            self.organization_score * weights['organization'] +
            self.space_score * weights['space'] +
            self.proximity_score * weights['proximity']
        )
    
    @property
    def confidence_level(self) -> ConfidenceLevel:
        """Determine confidence level based on total score and conflicts."""
        if self.conflicts:
            return ConfidenceLevel.LOW
        
        score = self.total_score
        if score >= 90:
            return ConfidenceLevel.HIGH
        elif score >= 70:
            return ConfidenceLevel.MEDIUM
        elif score >= 50:
            return ConfidenceLevel.LOW
        else:
            return ConfidenceLevel.UNCERTAIN


@dataclass
class PathResolution:
    """
    Represents a complete path resolution for an episode or group of episodes.
    """
    episodes: List[Episode]
    resolution_type: ResolutionType
    primary_destination: Optional[PathDestination] = None
    alternative_destinations: List[PathDestination] = field(default_factory=list)
    
    # Resolution metadata
    confidence: ConfidenceLevel = ConfidenceLevel.UNCERTAIN
    reasoning: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    estimated_time_seconds: float = 0.0
    estimated_space_needed_gb: float = 0.0
    
    # Conflict resolution
    requires_user_confirmation: bool = False
    blocking_issues: List[str] = field(default_factory=list)
    
    @property
    def episode_count(self) -> int:
        """Get the number of episodes in this resolution."""
        return len(self.episodes)
    
    @property
    def total_size_gb(self) -> float:
        """Get total size of all episodes in GB."""
        return sum(ep.size_gb for ep in self.episodes)
    
    @property
    def show_names(self) -> Set[str]:
        """Get unique show names involved in this resolution."""
        return {ep.show_name for ep in self.episodes}
    
    @property
    def seasons_involved(self) -> Set[int]:
        """Get unique seasons involved in this resolution."""
        return {ep.season for ep in self.episodes}
    
    @property
    def is_executable(self) -> bool:
        """Check if this resolution can be safely executed."""
        return (
            self.primary_destination is not None and
            not self.blocking_issues and
            self.confidence in [ConfidenceLevel.HIGH, ConfidenceLevel.MEDIUM]
        )
    
    def get_summary(self) -> str:
        """Get a human-readable summary of this resolution."""
        if not self.episodes:
            return "No episodes to resolve"
        
        if len(self.show_names) == 1:
            show = list(self.show_names)[0]
            if len(self.seasons_involved) == 1:
                season = list(self.seasons_involved)[0]
                return f"{show} Season {season} ({self.episode_count} episodes, {self.total_size_gb:.1f}GB)"
            else:
                seasons = sorted(self.seasons_involved)
                return f"{show} Seasons {seasons} ({self.episode_count} episodes, {self.total_size_gb:.1f}GB)"
        else:
            return f"Multiple shows ({len(self.show_names)} shows, {self.episode_count} episodes, {self.total_size_gb:.1f}GB)"


@dataclass
class ResolutionPlan:
    """
    A complete plan for resolving multiple path resolution items.
    """
    resolutions: List[PathResolution] = field(default_factory=list)
    execution_order: List[int] = field(default_factory=list)  # Indices into resolutions list
    
    # Plan metadata
    total_episodes: int = 0
    total_size_gb: float = 0.0
    estimated_duration_minutes: float = 0.0
    
    # Safety and validation
    high_confidence_count: int = 0
    medium_confidence_count: int = 0
    low_confidence_count: int = 0
    requires_review: bool = False
    
    def __post_init__(self):
        """Calculate derived statistics."""
        self.total_episodes = sum(r.episode_count for r in self.resolutions)
        self.total_size_gb = sum(r.total_size_gb for r in self.resolutions)
        self.estimated_duration_minutes = sum(r.estimated_time_seconds for r in self.resolutions) / 60
        
        # Count confidence levels
        confidence_counts = {
            ConfidenceLevel.HIGH: 0,
            ConfidenceLevel.MEDIUM: 0,
            ConfidenceLevel.LOW: 0,
            ConfidenceLevel.UNCERTAIN: 0
        }
        
        for resolution in self.resolutions:
            confidence_counts[resolution.confidence] += 1
        
        self.high_confidence_count = confidence_counts[ConfidenceLevel.HIGH]
        self.medium_confidence_count = confidence_counts[ConfidenceLevel.MEDIUM]
        self.low_confidence_count = confidence_counts[ConfidenceLevel.LOW]
        
        # Determine if review is needed
        self.requires_review = (
            self.low_confidence_count > 0 or
            confidence_counts[ConfidenceLevel.UNCERTAIN] > 0 or
            any(r.requires_user_confirmation for r in self.resolutions)
        )
    
    @property
    def executable_resolutions(self) -> List[PathResolution]:
        """Get resolutions that can be safely executed."""
        return [r for r in self.resolutions if r.is_executable]
    
    @property
    def success_rate(self) -> float:
        """Get the percentage of resolutions that are executable."""
        if not self.resolutions:
            return 0.0
        return (len(self.executable_resolutions) / len(self.resolutions)) * 100
    
    def get_summary(self) -> str:
        """Get a human-readable summary of the resolution plan."""
        executable = len(self.executable_resolutions)
        total = len(self.resolutions)
        
        return (f"Resolution Plan: {executable}/{total} executable "
                f"({self.total_episodes} episodes, {self.total_size_gb:.1f}GB, "
                f"{self.success_rate:.1f}% success rate)")