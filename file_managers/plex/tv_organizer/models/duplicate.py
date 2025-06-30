"""
Duplicate detection models for TV file organization.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum
from pathlib import Path
from datetime import datetime

from .episode import Episode


class DuplicateAction(Enum):
    """Recommended action for duplicate episodes."""
    KEEP_LARGEST = "keep_largest"
    KEEP_BEST_QUALITY = "keep_best_quality"
    KEEP_NEWEST = "keep_newest"
    KEEP_FIRST = "keep_first"
    MANUAL_REVIEW = "manual_review"


@dataclass
class DuplicateGroup:
    """
    Represents a group of duplicate episodes (same show/season/episode).
    """
    # Episode identification
    show_name: str
    season: int
    episode: int
    
    # Duplicate episodes
    episodes: List[Episode]
    
    # Analysis results
    recommended_action: DuplicateAction = DuplicateAction.KEEP_BEST_QUALITY
    recommended_keeper: Optional[Episode] = None
    recommended_removals: List[Episode] = None
    
    # Space savings
    potential_space_saved: int = 0  # bytes
    
    # Additional analysis
    analysis_notes: List[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.recommended_removals is None:
            self.recommended_removals = []
        if self.analysis_notes is None:
            self.analysis_notes = []
        if self.metadata is None:
            self.metadata = {}
    
    @property
    def episode_id(self) -> str:
        """Get unique identifier for this episode."""
        return f"{self.show_name.lower()}:s{self.season:02d}e{self.episode:02d}"
    
    @property
    def duplicate_count(self) -> int:
        """Get the number of duplicate episodes."""
        return len(self.episodes)
    
    @property
    def total_size(self) -> int:
        """Get total size of all duplicates in bytes."""
        return sum(ep.file_size for ep in self.episodes)
    
    @property
    def total_size_mb(self) -> float:
        """Get total size of all duplicates in MB."""
        return self.total_size / (1024 * 1024)
    
    @property
    def total_size_gb(self) -> float:
        """Get total size of all duplicates in GB."""
        return self.total_size / (1024 * 1024 * 1024)
    
    def analyze_duplicates(self) -> None:
        """
        Analyze the duplicate episodes and determine recommended actions.
        """
        if len(self.episodes) < 2:
            return
        
        # Sort episodes by quality score (highest first)
        sorted_episodes = sorted(
            self.episodes,
            key=lambda ep: ep.get_quality_score(),
            reverse=True
        )
        
        best_episode = sorted_episodes[0]
        others = sorted_episodes[1:]
        
        # Check if there's a clear quality winner
        quality_scores = [ep.get_quality_score() for ep in self.episodes]
        unique_scores = set(quality_scores)
        
        if len(unique_scores) == 1:
            # All have same quality score, use size as tiebreaker
            self.recommended_action = DuplicateAction.KEEP_LARGEST
            largest_episode = max(self.episodes, key=lambda ep: ep.file_size)
            self.recommended_keeper = largest_episode
            self.recommended_removals = [ep for ep in self.episodes if ep != largest_episode]
            self.analysis_notes.append("All episodes have similar quality, keeping largest file")
        else:
            # Clear quality difference
            self.recommended_action = DuplicateAction.KEEP_BEST_QUALITY
            self.recommended_keeper = best_episode
            self.recommended_removals = others
            self.analysis_notes.append(f"Keeping best quality: {best_episode.quality.value}")
        
        # Calculate potential space savings
        if self.recommended_keeper:
            self.potential_space_saved = sum(
                ep.file_size for ep in self.recommended_removals
            )
        
        # Add analysis notes
        self._add_quality_analysis()
        self._add_size_analysis()
        self._add_location_analysis()
    
    def _add_quality_analysis(self) -> None:
        """Add quality-related analysis notes."""
        qualities = [ep.quality.value for ep in self.episodes]
        unique_qualities = set(qualities)
        
        if len(unique_qualities) > 1:
            quality_list = ", ".join(sorted(unique_qualities))
            self.analysis_notes.append(f"Quality variations: {quality_list}")
        
        # Check for source variations
        sources = [ep.source for ep in self.episodes if ep.source]
        if len(set(sources)) > 1:
            source_list = ", ".join(sorted(set(sources)))
            self.analysis_notes.append(f"Source variations: {source_list}")
    
    def _add_size_analysis(self) -> None:
        """Add size-related analysis notes."""
        sizes = [ep.file_size for ep in self.episodes]
        min_size = min(sizes)
        max_size = max(sizes)
        
        if max_size > min_size * 2:  # Significant size difference
            min_mb = min_size / (1024 * 1024)
            max_mb = max_size / (1024 * 1024)
            self.analysis_notes.append(
                f"Significant size difference: {min_mb:.1f}MB to {max_mb:.1f}MB"
            )
    
    def _add_location_analysis(self) -> None:
        """Add location-related analysis notes."""
        folders = [ep.parent_folder for ep in self.episodes]
        unique_folders = set(folders)
        
        if len(unique_folders) > 1:
            self.analysis_notes.append(
                f"Episodes in {len(unique_folders)} different folders"
            )
    
    def get_summary(self) -> str:
        """Get a summary string for this duplicate group."""
        return (
            f"{self.show_name} S{self.season:02d}E{self.episode:02d}: "
            f"{self.duplicate_count} duplicates, "
            f"{self.total_size_mb:.1f}MB total, "
            f"{self.potential_space_saved / (1024 * 1024):.1f}MB can be saved"
        )
    
    def __str__(self) -> str:
        """String representation of the duplicate group."""
        return self.get_summary()
    
    def __repr__(self) -> str:
        """Detailed representation of the duplicate group."""
        return (
            f"DuplicateGroup(show='{self.show_name}', season={self.season}, "
            f"episode={self.episode}, duplicates={self.duplicate_count}, "
            f"action={self.recommended_action.value})"
        )


class DeletionMode(Enum):
    """Deletion mode options."""
    DRY_RUN = "dry_run"           # Preview only, no actual deletion
    TRASH = "trash"               # Move to system trash/recycle bin
    PERMANENT = "permanent"       # Permanent deletion (dangerous)


class DeletionStatus(Enum):
    """Status of a deletion operation."""
    PENDING = "pending"           # Queued for deletion
    SKIPPED = "skipped"           # Skipped due to safety check
    SUCCESS = "success"           # Successfully deleted
    FAILED = "failed"             # Failed to delete
    CANCELLED = "cancelled"       # User cancelled


class SafetyCheck(Enum):
    """Safety check types."""
    FILE_EXISTS = "file_exists"           # File exists and is accessible
    FILE_NOT_LOCKED = "file_not_locked"   # File is not in use
    SUFFICIENT_SPACE = "sufficient_space"  # Enough space for operation
    USER_CONFIRMATION = "user_confirmation" # User confirmed deletion
    SIZE_REASONABLE = "size_reasonable"    # File size is reasonable for deletion


@dataclass
class DeletionOperation:
    """
    Represents a single file deletion operation with safety checks.
    """
    episode: Episode
    deletion_mode: DeletionMode
    reason: str                                    # Why this file is being deleted
    
    # Safety checks
    safety_checks: Dict[SafetyCheck, bool] = field(default_factory=dict)
    safety_warnings: List[str] = field(default_factory=list)
    
    # Operation tracking
    status: DeletionStatus = DeletionStatus.PENDING
    timestamp: Optional[datetime] = None
    backup_location: Optional[Path] = None         # Where file was moved (for trash mode)
    error_message: Optional[str] = None
    
    # User interaction
    requires_confirmation: bool = True
    user_confirmed: bool = False
    
    def __post_init__(self):
        """Initialize safety checks."""
        if not self.safety_checks:
            self.safety_checks = {check: False for check in SafetyCheck}
    
    @property
    def is_safe_to_delete(self) -> bool:
        """Check if all safety requirements are met."""
        required_checks = [
            SafetyCheck.FILE_EXISTS,
            SafetyCheck.FILE_NOT_LOCKED,
            SafetyCheck.SIZE_REASONABLE
        ]
        
        # If requires confirmation, check that too
        if self.requires_confirmation:
            required_checks.append(SafetyCheck.USER_CONFIRMATION)
        
        return all(self.safety_checks.get(check, False) for check in required_checks)
    
    @property
    def can_execute(self) -> bool:
        """Check if operation can be executed."""
        return (
            self.status == DeletionStatus.PENDING and
            self.is_safe_to_delete
        )
    
    def add_safety_warning(self, warning: str) -> None:
        """Add a safety warning."""
        if warning not in self.safety_warnings:
            self.safety_warnings.append(warning)
    
    def get_summary(self) -> str:
        """Get a summary of this deletion operation."""
        status_icon = {
            DeletionStatus.PENDING: "⏳",
            DeletionStatus.SKIPPED: "⏭️",
            DeletionStatus.SUCCESS: "✅",
            DeletionStatus.FAILED: "❌",
            DeletionStatus.CANCELLED: "🚫"
        }.get(self.status, "❓")
        
        return (
            f"{status_icon} {self.episode.filename} "
            f"({self.episode.size_mb:.1f}MB) - {self.reason}"
        )


@dataclass
class DeletionPlan:
    """
    A complete plan for deleting duplicate files with safety validation.
    """
    operations: List[DeletionOperation] = field(default_factory=list)
    deletion_mode: DeletionMode = DeletionMode.DRY_RUN
    
    # Plan statistics
    total_files: int = 0
    total_size_mb: float = 0.0
    estimated_space_saved_mb: float = 0.0
    
    # Safety and validation
    requires_user_confirmation: bool = True
    confirmation_phrase: str = "DELETE DUPLICATES"
    
    # Execution tracking
    execution_start: Optional[datetime] = None
    execution_end: Optional[datetime] = None
    
    def __post_init__(self):
        """Calculate plan statistics."""
        self.total_files = len(self.operations)
        self.total_size_mb = sum(op.episode.size_mb for op in self.operations)
        self.estimated_space_saved_mb = self.total_size_mb
    
    @property
    def safe_operations(self) -> List[DeletionOperation]:
        """Get operations that are safe to execute."""
        return [op for op in self.operations if op.is_safe_to_delete]
    
    @property
    def unsafe_operations(self) -> List[DeletionOperation]:
        """Get operations that are not safe to execute."""
        return [op for op in self.operations if not op.is_safe_to_delete]
    
    @property
    def success_rate(self) -> float:
        """Get percentage of successful operations."""
        if not self.operations:
            return 0.0
        
        successful = len([op for op in self.operations if op.status == DeletionStatus.SUCCESS])
        return (successful / len(self.operations)) * 100
    
    @property
    def is_executable(self) -> bool:
        """Check if plan can be executed."""
        return (
            len(self.safe_operations) > 0 and
            self.deletion_mode != DeletionMode.DRY_RUN
        )
    
    @property
    def execution_duration(self) -> Optional[float]:
        """Get execution duration in seconds."""
        if self.execution_start and self.execution_end:
            return (self.execution_end - self.execution_start).total_seconds()
        return None
    
    def add_operation(self, operation: DeletionOperation) -> None:
        """Add a deletion operation to the plan."""
        self.operations.append(operation)
        self.total_files += 1
        self.total_size_mb += operation.episode.size_mb
        self.estimated_space_saved_mb = self.total_size_mb
    
    def get_summary(self) -> str:
        """Get a summary of the deletion plan."""
        safe_count = len(self.safe_operations)
        return (
            f"Deletion Plan: {safe_count}/{self.total_files} safe operations, "
            f"{self.estimated_space_saved_mb:.1f}MB to be freed, "
            f"Mode: {self.deletion_mode.value}"
        )
    
    def get_status_summary(self) -> Dict[str, int]:
        """Get count of operations by status."""
        status_counts = {}
        for status in DeletionStatus:
            count = len([op for op in self.operations if op.status == status])
            if count > 0:
                status_counts[status.value] = count
        return status_counts