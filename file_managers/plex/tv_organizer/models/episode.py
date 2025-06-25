"""
Episode data model for TV file organization.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Dict, Any
from enum import Enum


class EpisodeStatus(Enum):
    """Status of episode organization."""
    ORGANIZED = "organized"          # Properly placed in show/season folder
    LOOSE_ROOT = "loose_root"        # In TV root directory
    LOOSE_GENERIC = "loose_generic"  # In generic folder (Downloads, etc.)
    LOOSE_EPISODE_FOLDER = "loose_episode_folder"  # In individual episode folder
    LOOSE_SEASON_FOLDER = "loose_season_folder"    # Season folder outside show
    MISNAMED_FOLDER = "misnamed_folder"            # In incorrectly named folder
    DUPLICATE = "duplicate"          # Duplicate of another episode


class Quality(Enum):
    """Video quality levels for comparison."""
    SD_480P = "480p"
    HD_720P = "720p"
    FHD_1080P = "1080p"
    UHD_4K = "4K"
    UHD_8K = "8K"
    UNKNOWN = "unknown"


@dataclass
class Episode:
    """
    Represents a TV episode file with metadata and organization status.
    """
    # File information
    file_path: Path
    file_size: int
    file_extension: str
    
    # Episode metadata
    show_name: str
    season: int
    episode: int
    episode_title: Optional[str] = None
    
    # Organization status
    status: EpisodeStatus = EpisodeStatus.LOOSE_ROOT
    current_location_type: str = "unknown"
    
    # Quality and format information
    quality: Quality = Quality.UNKNOWN
    resolution: Optional[str] = None
    codec: Optional[str] = None
    source: Optional[str] = None  # WEB-DL, BluRay, HDTV, etc.
    
    # Additional metadata
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
    
    @property
    def filename(self) -> str:
        """Get the filename without path."""
        return self.file_path.name
    
    @property
    def parent_folder(self) -> Path:
        """Get the parent folder path."""
        return self.file_path.parent
    
    @property
    def episode_id(self) -> str:
        """Get a unique identifier for this episode (show + season + episode)."""
        return f"{self.show_name.lower()}:s{self.season:02d}e{self.episode:02d}"
    
    @property
    def size_mb(self) -> float:
        """Get file size in MB."""
        return self.file_size / (1024 * 1024)
    
    @property
    def size_gb(self) -> float:
        """Get file size in GB."""
        return self.file_size / (1024 * 1024 * 1024)
    
    def is_same_episode(self, other: 'Episode') -> bool:
        """
        Check if this represents the same episode as another Episode.
        
        Args:
            other: Another Episode instance
            
        Returns:
            True if they represent the same episode (same show/season/episode)
        """
        return (
            self.show_name.lower() == other.show_name.lower() and
            self.season == other.season and
            self.episode == other.episode
        )
    
    def is_better_quality_than(self, other: 'Episode') -> bool:
        """
        Compare quality with another episode of the same show/season/episode.
        
        Args:
            other: Another Episode instance
            
        Returns:
            True if this episode has better quality than the other
        """
        if not self.is_same_episode(other):
            return False
        
        # Quality comparison order (higher is better)
        quality_order = {
            Quality.UHD_8K: 5,
            Quality.UHD_4K: 4,
            Quality.FHD_1080P: 3,
            Quality.HD_720P: 2,
            Quality.SD_480P: 1,
            Quality.UNKNOWN: 0
        }
        
        my_quality = quality_order.get(self.quality, 0)
        other_quality = quality_order.get(other.quality, 0)
        
        if my_quality != other_quality:
            return my_quality > other_quality
        
        # If quality is the same, prefer larger file size
        return self.file_size > other.file_size
    
    def get_quality_score(self) -> int:
        """Get a numeric score for quality comparison."""
        quality_scores = {
            Quality.UHD_8K: 50,
            Quality.UHD_4K: 40,
            Quality.FHD_1080P: 30,
            Quality.HD_720P: 20,
            Quality.SD_480P: 10,
            Quality.UNKNOWN: 0
        }
        
        base_score = quality_scores.get(self.quality, 0)
        
        # Add bonus for file size (larger is generally better)
        size_bonus = min(10, int(self.size_gb))  # Up to 10 points for size
        
        return base_score + size_bonus
    
    def __str__(self) -> str:
        """String representation of the episode."""
        return f"{self.show_name} S{self.season:02d}E{self.episode:02d} ({self.quality.value}, {self.size_mb:.1f}MB)"
    
    def __repr__(self) -> str:
        """Detailed representation of the episode."""
        return (f"Episode(show='{self.show_name}', season={self.season}, episode={self.episode}, "
                f"quality={self.quality.value}, size={self.size_mb:.1f}MB, "
                f"status={self.status.value}, path='{self.file_path}')")