"""Media Auto-Organizer Package

An intelligent media file organization system that automatically classifies and moves
downloaded media files to appropriate Plex directories using AI and rule-based classification.

Key Components:
- AutoOrganizer: Main orchestrator class
- MediaDatabase: Interface to existing media database for TV show placement
- ClassificationDatabase: SQLite database for caching classifications
- BedrockClassifier: AI-powered classification using AWS Bedrock
- CLI: Command-line interface
"""

from .organizer import AutoOrganizer
from .models import MediaType, MediaFile, MoveResult, ClassificationResult

__version__ = "1.0.0"
__all__ = [
    "AutoOrganizer",
    "MediaType", 
    "MediaFile",
    "MoveResult",
    "ClassificationResult"
]