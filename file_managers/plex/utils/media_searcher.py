"""Media search functionality for finding movies and TV shows in the collection."""

import os
import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from difflib import SequenceMatcher
import logging

from ..config.config import config
from .media_database import MediaDatabase

logger = logging.getLogger(__name__)

@dataclass
class MediaMatch:
    """Represents a media file match."""
    title: str
    path: str
    media_type: str  # 'movie' or 'tv'
    confidence: float
    season: Optional[int] = None
    episode: Optional[int] = None
    year: Optional[int] = None
    file_size: Optional[int] = None

@dataclass
class SearchResult:
    """Results from a media search."""
    query: str
    matches: List[MediaMatch]
    total_found: int
    search_type: str

class MediaSearcher:
    """Searches for media files in the configured directories."""
    
    def __init__(self, use_database: bool = True):
        """
        Initialize the media searcher with configuration.
        
        Args:
            use_database: Whether to use cached database for faster searches
        """
        self.video_extensions = config.video_extensions_set
        self.use_database = use_database
        self.database = MediaDatabase() if use_database else None
    
    def search_movies(self, title: str, fuzzy: bool = True) -> SearchResult:
        """
        Search for movies by title.
        
        Args:
            title: Movie title to search for
            fuzzy: Whether to use fuzzy matching
            
        Returns:
            SearchResult with found movies
        """
        if self.use_database and self.database:
            # Use cached database for fast search
            matches = self._search_movies_from_database(title)
        else:
            # Fall back to filesystem search
            matches = []
            movie_dirs = config.movie_directories_full
            
            for dir_config in movie_dirs:
                dir_path = dir_config['path']
                if os.path.exists(dir_path):
                    matches.extend(self._search_directory_for_movies(dir_path, title, fuzzy))
        
        # Sort by confidence score
        matches.sort(key=lambda x: x.confidence, reverse=True)
        
        return SearchResult(
            query=title,
            matches=matches,
            total_found=len(matches),
            search_type="movie"
        )
    
    def search_tv_shows(self, title: str, fuzzy: bool = True) -> SearchResult:
        """
        Search for TV shows by title.
        
        Args:
            title: TV show title to search for
            fuzzy: Whether to use fuzzy matching
            
        Returns:
            SearchResult with found TV shows
        """
        if self.use_database and self.database:
            # Use cached database for fast search
            matches = self._search_tv_shows_from_database(title)
        else:
            # Fall back to filesystem search
            matches = []
            tv_dirs = config.tv_directories_full
            
            for dir_config in tv_dirs:
                dir_path = dir_config['path']
                if os.path.exists(dir_path):
                    matches.extend(self._search_directory_for_tv(dir_path, title, fuzzy))
        
        # Sort by confidence score
        matches.sort(key=lambda x: x.confidence, reverse=True)
        
        return SearchResult(
            query=title,
            matches=matches,
            total_found=len(matches),
            search_type="tv"
        )
    
    def get_tv_show_seasons(self, title: str) -> Dict[str, Any]:
        """
        Get season information for a TV show.
        
        Args:
            title: TV show title
            
        Returns:
            Dictionary with season information
        """
        if self.use_database and self.database:
            # Use cached database for fast lookup
            show_details = self.database.get_tv_show_details(title)
            if show_details:
                return {
                    'show_title': show_details['name'],
                    'found': True,
                    'show_paths': show_details['directories'],
                    'seasons': self._format_seasons_from_database(show_details['episodes']),
                    'total_seasons': len(show_details['seasons']),
                    'total_episodes': show_details['total_episodes']
                }
            else:
                return {
                    'show_title': title,
                    'found': False,
                    'seasons': {},
                    'total_seasons': 0,
                    'total_episodes': 0
                }
        else:
            # Fall back to filesystem search
            search_result = self.search_tv_shows(title, fuzzy=True)
            
            if not search_result.matches:
                return {
                    'show_title': title,
                    'found': False,
                    'seasons': {},
                    'total_seasons': 0,
                    'total_episodes': 0
                }
            
            # Group episodes by season
            seasons = {}
            show_paths = set()
            
            for match in search_result.matches:
                show_paths.add(os.path.dirname(match.path))
                if match.season is not None:
                    if match.season not in seasons:
                        seasons[match.season] = []
                    seasons[match.season].append({
                        'episode': match.episode,
                        'path': match.path,
                        'file_size': match.file_size
                    })
            
            # Sort episodes within each season
            for season_num in seasons:
                seasons[season_num].sort(key=lambda x: x['episode'] or 0)
            
            total_episodes = sum(len(episodes) for episodes in seasons.values())
            
            return {
                'show_title': search_result.matches[0].title,
                'found': True,
                'show_paths': list(show_paths),
                'seasons': seasons,
                'total_seasons': len(seasons),
                'total_episodes': total_episodes
            }
    
    def _search_directory_for_movies(self, directory: str, title: str, fuzzy: bool) -> List[MediaMatch]:
        """Search a directory for movie files."""
        matches = []
        
        try:
            for root, dirs, files in os.walk(directory):
                for file in files:
                    if self._is_video_file(file):
                        file_path = os.path.join(root, file)
                        match = self._match_movie_file(file_path, title, fuzzy)
                        if match:
                            matches.append(match)
        except Exception as e:
            logger.error(f"Error searching directory {directory}: {e}")
        
        return matches
    
    def _search_directory_for_tv(self, directory: str, title: str, fuzzy: bool) -> List[MediaMatch]:
        """Search a directory for TV show files."""
        matches = []
        
        try:
            for root, dirs, files in os.walk(directory):
                for file in files:
                    if self._is_video_file(file):
                        file_path = os.path.join(root, file)
                        match = self._match_tv_file(file_path, title, fuzzy)
                        if match:
                            matches.append(match)
        except Exception as e:
            logger.error(f"Error searching directory {directory}: {e}")
        
        return matches
    
    def _is_video_file(self, filename: str) -> bool:
        """Check if a file is a video file based on extension."""
        _, ext = os.path.splitext(filename.lower())
        return ext in self.video_extensions
    
    def _match_movie_file(self, file_path: str, target_title: str, fuzzy: bool) -> Optional[MediaMatch]:
        """Check if a movie file matches the target title."""
        filename = os.path.basename(file_path)
        
        # Extract movie title and year from filename
        title, year = self._extract_movie_info(filename)
        
        # Calculate confidence score
        confidence = self._calculate_similarity(title, target_title)
        
        # Apply threshold
        threshold = 0.6 if fuzzy else 0.9
        if confidence < threshold:
            return None
        
        try:
            file_size = os.path.getsize(file_path)
        except OSError:
            file_size = None
        
        return MediaMatch(
            title=title,
            path=file_path,
            media_type='movie',
            confidence=confidence,
            year=year,
            file_size=file_size
        )
    
    def _match_tv_file(self, file_path: str, target_title: str, fuzzy: bool) -> Optional[MediaMatch]:
        """Check if a TV file matches the target title."""
        filename = os.path.basename(file_path)
        
        # Extract TV show info from filename
        title, season, episode, year = self._extract_tv_info(file_path)
        
        # Calculate confidence score
        confidence = self._calculate_similarity(title, target_title)
        
        # Apply threshold
        threshold = 0.6 if fuzzy else 0.9
        if confidence < threshold:
            return None
        
        try:
            file_size = os.path.getsize(file_path)
        except OSError:
            file_size = None
        
        return MediaMatch(
            title=title,
            path=file_path,
            media_type='tv',
            confidence=confidence,
            season=season,
            episode=episode,
            year=year,
            file_size=file_size
        )
    
    def _extract_movie_info(self, filename: str) -> Tuple[str, Optional[int]]:
        """Extract movie title and year from filename."""
        # Remove file extension
        name, _ = os.path.splitext(filename)
        
        # Extract year (4 digits in parentheses or standalone)
        year_match = re.search(r'\(?(\d{4})\)?', name)
        year = int(year_match.group(1)) if year_match else None
        
        # Remove year and common suffixes from title
        if year_match:
            name = name[:year_match.start()].strip()
        
        # Clean up common patterns
        name = re.sub(r'\b(REPACK|PROPER|REAL|UNRATED|EXTENDED|DIRECTORS?.CUT)\b', '', name, flags=re.IGNORECASE)
        name = re.sub(r'\b(720p|1080p|2160p|4K|HDR|BluRay|WEB-DL|WEBRip|DVDRip)\b.*', '', name, flags=re.IGNORECASE)
        name = re.sub(r'[._-]+', ' ', name).strip()
        
        return name, year
    
    def _extract_tv_info(self, file_path: str) -> Tuple[str, Optional[int], Optional[int], Optional[int]]:
        """Extract TV show title, season, episode, and year from file path."""
        filename = os.path.basename(file_path)
        directory = os.path.dirname(file_path)
        
        # Try to get show name from directory structure
        path_parts = directory.split(os.sep)
        show_name = None
        
        # Look for show name in path (usually the parent directory of seasons)
        for part in reversed(path_parts):
            if not re.match(r'^Season \d+$', part, re.IGNORECASE):
                show_name = part
                break
        
        # Extract season and episode from filename
        season, episode = self._extract_season_episode(filename)
        
        # If no season found in filename, try directory name
        if season is None:
            for part in path_parts:
                season_match = re.search(r'Season (\d+)', part, re.IGNORECASE)
                if season_match:
                    season = int(season_match.group(1))
                    break
        
        # Extract year
        year_match = re.search(r'(\d{4})', filename)
        year = int(year_match.group(1)) if year_match else None
        
        # Clean up show name
        if show_name:
            show_name = re.sub(r'[._-]+', ' ', show_name).strip()
        else:
            # Fallback to filename parsing
            name, _ = os.path.splitext(filename)
            # Remove season/episode info
            name = re.sub(r'[Ss]\d+[Ee]\d+.*', '', name)
            name = re.sub(r'[._-]+', ' ', name).strip()
            show_name = name
        
        return show_name or "Unknown", season, episode, year
    
    def _extract_season_episode(self, filename: str) -> Tuple[Optional[int], Optional[int]]:
        """Extract season and episode numbers from filename."""
        # Common patterns: S01E01, s01e01, 1x01, Season 1 Episode 1, etc.
        patterns = [
            r'[Ss](\d+)[Ee](\d+)',           # S01E01
            r'(\d+)x(\d+)',                   # 1x01
            r'Season (\d+) Episode (\d+)',    # Season 1 Episode 1
            r'[Ss]eason (\d+)[Ee]pisode (\d+)', # Season 1Episode 1
        ]
        
        for pattern in patterns:
            match = re.search(pattern, filename, re.IGNORECASE)
            if match:
                return int(match.group(1)), int(match.group(2))
        
        return None, None
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two strings."""
        if not text1 or not text2:
            return 0.0
        
        # Normalize strings
        text1 = text1.lower().strip()
        text2 = text2.lower().strip()
        
        # Exact match gets highest score
        if text1 == text2:
            return 1.0
        
        # Check if one is contained in the other
        if text1 in text2 or text2 in text1:
            return 0.9
        
        # Use sequence matcher for fuzzy matching
        return SequenceMatcher(None, text1, text2).ratio()
    
    def _search_movies_from_database(self, title: str) -> List[MediaMatch]:
        """Search for movies using the cached database."""
        db_matches = self.database.search_movies(title)
        matches = []
        
        for db_match in db_matches:
            match = MediaMatch(
                title=db_match['title'],
                path=db_match['file_path'],
                media_type='movie',
                confidence=db_match['confidence'],
                year=db_match.get('year'),
                file_size=db_match.get('file_size')
            )
            matches.append(match)
        
        return matches
    
    def _search_tv_shows_from_database(self, title: str) -> List[MediaMatch]:
        """Search for TV shows using the cached database."""
        db_matches = self.database.search_tv_shows(title)
        matches = []
        
        for db_match in db_matches:
            # For TV shows, create matches for each episode
            for episode in db_match.get('episodes', []):
                match = MediaMatch(
                    title=db_match['name'],
                    path=episode['file_path'],
                    media_type='tv',
                    confidence=db_match['confidence'],
                    season=episode.get('season'),
                    episode=episode.get('episode'),
                    file_size=episode.get('file_size')
                )
                matches.append(match)
        
        return matches
    
    def _format_seasons_from_database(self, episodes: List[Dict]) -> Dict[int, List[Dict]]:
        """Format episodes from database into seasons structure."""
        seasons = {}
        
        for episode in episodes:
            season_num = episode['season']
            if season_num not in seasons:
                seasons[season_num] = []
            
            seasons[season_num].append({
                'episode': episode['episode'],
                'path': episode['file_path'],
                'file_size': episode['file_size']
            })
        
        # Sort episodes within each season
        for season_num in seasons:
            seasons[season_num].sort(key=lambda x: x['episode'] or 0)
        
        return seasons