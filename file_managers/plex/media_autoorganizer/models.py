"""Data models for the Media Auto-Organizer.

This module contains all the data structures used throughout the auto-organizer:
- Enums for media types
- NamedTuples for structured data
- Type definitions for better code clarity
"""

from enum import Enum
from pathlib import Path
from typing import NamedTuple, Optional


class MediaType(Enum):
    """Supported media types for classification."""
    MOVIE = "MOVIE"
    TV = "TV" 
    DOCUMENTARY = "DOCUMENTARY"
    STANDUP = "STANDUP"
    AUDIOBOOK = "AUDIOBOOK"
    OTHER = "OTHER"


class MediaFile(NamedTuple):
    """Represents a media file to be organized."""
    path: Path
    size: int
    media_type: Optional[MediaType] = None
    target_directory: Optional[str] = None
    classification_source: Optional[str] = None  # "AI" or "Rule-based"
    show_name: Optional[str] = None  # For TV episodes, the detected show name
    season: Optional[int] = None  # For TV episodes, the detected season
    episode: Optional[int] = None  # For TV episodes, the detected episode


class ClassificationResult(NamedTuple):
    """Result of AI classification."""
    media_type: MediaType
    confidence: float
    reasoning: Optional[str] = None


class MoveResult(NamedTuple):
    """Result of a file move operation."""
    success: bool
    source_path: Path
    target_path: Optional[Path] = None
    error: Optional[str] = None
    space_freed: int = 0