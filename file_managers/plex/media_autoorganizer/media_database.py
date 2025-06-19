"""Media Database Interface

This module provides the MediaDatabase class that interfaces with the prebuilt
JSON media database to find existing TV show locations and extract show information
from filenames.

Key Features:
- Fuzzy matching for TV show names
- Show location detection from existing media database
- Episode information extraction from filenames
- Failed directory tracking to avoid repeated access attempts
"""

import json
import re
from pathlib import Path
from typing import Dict, Optional, Set, Tuple

from .models import MediaType


class MediaDatabase:
    """Interface to the prebuilt media database for show location detection."""
    
    def __init__(self):
        """Initialize the media database interface."""
        self.database_path = Path(__file__).parent.parent.parent.parent / "database" / "media_database.json"
        self.media_data = None
        self.tv_shows = {}
        self.failed_directories: Set[str] = set()  # Track directories with access issues
        self._load_database()
    
    def _load_database(self) -> None:
        """Load the media database JSON file."""
        try:
            if self.database_path.exists():
                with open(self.database_path, 'r', encoding='utf-8') as f:
                    self.media_data = json.load(f)
                    self.tv_shows = self.media_data.get('tv_shows', {})
                print(f"📚 Loaded media database with {len(self.tv_shows)} TV shows")
            else:
                print(f"⚠️ Media database not found at {self.database_path}")
        except Exception as e:
            print(f"❌ Error loading media database: {e}")
            self.tv_shows = {}
    
    def find_tv_show_location(self, show_name: str) -> Optional[str]:
        """
        Find the existing directory for a TV show.
        
        Args:
            show_name: Name of the TV show to find
            
        Returns:
            Path to the show's directory, or None if not found
        """
        if not self.tv_shows:
            return None
        
        # Normalize the show name for comparison
        normalized_input = self._normalize_show_name(show_name)
        
        # First try exact match
        if normalized_input in self.tv_shows:
            return self._get_best_directory(self.tv_shows[normalized_input])
        
        # Try fuzzy matching
        for normalized_name, show_data in self.tv_shows.items():
            if self._shows_match(normalized_input, normalized_name):
                return self._get_best_directory(show_data)
        
        return None
    
    def _normalize_show_name(self, name: str) -> str:
        """
        Normalize show name for comparison.
        
        Args:
            name: Raw show name
            
        Returns:
            Normalized show name for comparison
        """
        # Remove year, parentheses, and common variations
        name = re.sub(r'\(\d{4}\)', '', name)  # Remove (2023) etc
        name = re.sub(r'\d{4}', '', name)      # Remove standalone years
        name = re.sub(r'[^\w\s]', '', name)    # Remove special characters
        name = ' '.join(name.split())          # Normalize whitespace
        return name.lower().strip()
    
    def _shows_match(self, name1: str, name2: str) -> bool:
        """
        Check if two show names match using fuzzy logic.
        
        Args:
            name1: First show name (normalized)
            name2: Second show name (normalized)
            
        Returns:
            True if the names match using fuzzy logic
        """
        # Direct match
        if name1 == name2:
            return True
        
        # Check if one contains the other
        if name1 in name2 or name2 in name1:
            return True
        
        # Word-by-word matching for multi-word titles
        words1 = set(name1.split())
        words2 = set(name2.split())
        
        # If most words match, consider it a match
        if len(words1) > 1 and len(words2) > 1:
            intersection = words1.intersection(words2)
            union = words1.union(words2)
            similarity = len(intersection) / len(union)
            return similarity >= 0.6
        
        return False
    
    def _get_best_directory(self, show_data: Dict) -> Optional[str]:
        """
        Get the best available directory for a show, avoiding failed ones.
        
        Args:
            show_data: Show data from the database
            
        Returns:
            Best available directory path
        """
        directories = show_data.get('directories', [])
        if not directories:
            return None
        
        # Filter out failed directories
        available_dirs = [d for d in directories if d not in self.failed_directories]
        
        if not available_dirs:
            # All directories failed, try the first one again (maybe issue resolved)
            available_dirs = directories[:1]
        
        # Return the first available directory (they're usually ordered by preference)
        return available_dirs[0]
    
    def mark_directory_failed(self, directory: str) -> None:
        """
        Mark a directory as failed/inaccessible.
        
        Args:
            directory: Directory path to mark as failed
        """
        self.failed_directories.add(directory)
        print(f"🚫 Marked directory as failed: {directory}")
    
    def extract_tv_info(self, filename: str) -> Tuple[Optional[str], Optional[int], Optional[int]]:
        """
        Extract show name, season, and episode from filename.
        
        This method uses various regex patterns to extract TV show information
        from common filename formats.
        
        Args:
            filename: Name of the file to analyze
            
        Returns:
            Tuple of (show_name, season, episode) or (None, None, None)
        """
        # Common TV show patterns
        patterns = [
            # Show.Name.S01E01.Title.mkv
            r'(.+?)\.S(\d+)E(\d+)',
            # Show Name - S01E01 - Title.mkv  
            r'(.+?)\s*-\s*S(\d+)E(\d+)',
            # Show.Name.1x01.Title.mkv
            r'(.+?)\.(\d+)x(\d+)',
            # Show Name (2023) S01E01.mkv
            r'(.+?)\s*(?:\(\d{4}\))?\s*S(\d+)E(\d+)',
            # [Group] Show Name - 01 [Season 1].mkv (anime style)
            r'(?:\[.+?\])?\s*(.+?)\s*-\s*(\d+)\s*(?:\[Season\s*(\d+)\])?',
        ]
        
        filename_clean = filename.replace('_', ' ')
        
        for pattern in patterns:
            match = re.search(pattern, filename_clean, re.IGNORECASE)
            if match:
                show_name = match.group(1).replace('.', ' ').strip()
                season = int(match.group(2)) if match.group(2) else 1
                episode = int(match.group(3)) if match.group(3) else None
                
                # Clean up show name
                show_name = re.sub(r'\s+', ' ', show_name)  # Normalize spaces
                show_name = show_name.strip()
                
                return show_name, season, episode
        
        return None, None, None