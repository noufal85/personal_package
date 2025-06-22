"""Database-based duplicate detection for movies and TV episodes."""

from typing import List, Dict, NamedTuple, Set
from collections import defaultdict
from pathlib import Path
import re

from .media_database import MediaDatabase, MovieEntry, TVEpisodeEntry
from .movie_scanner import normalize_movie_name


class MovieDuplicateFile(NamedTuple):
    """Represents a movie file for duplicate detection."""
    path: str
    size: int
    title: str
    year: int
    normalized_title: str


class TVDuplicateFile(NamedTuple):
    """Represents a TV episode file for duplicate detection."""
    path: str
    size: int
    show_name: str
    season: int
    episode: int
    normalized_show_name: str


class MovieDuplicateGroup(NamedTuple):
    """Represents a group of duplicate movies."""
    normalized_name: str
    files: List[MovieDuplicateFile]
    best_file: MovieDuplicateFile  # Largest file (best quality)


class TVDuplicateGroup(NamedTuple):
    """Represents a group of duplicate TV episodes."""
    show_name: str
    season: int
    episode: int
    files: List[TVDuplicateFile]
    best_file: TVDuplicateFile  # Largest file (best quality)


class DuplicateDetector:
    """Database-based duplicate detection for movies and TV episodes."""
    
    def __init__(self, database: MediaDatabase):
        """
        Initialize duplicate detector with database.
        
        Args:
            database: MediaDatabase instance to use for detection
        """
        self.database = database
    
    def find_movie_duplicates(self) -> List[MovieDuplicateGroup]:
        """
        Find duplicate movies using database entries.
        
        Returns:
            List of MovieDuplicateGroup objects containing duplicates
        """
        # Get all movies from database
        all_movies = self.database.get_all_movies()
        
        if not all_movies:
            return []
        
        # Group movies by normalized title + year
        grouped_movies = defaultdict(list)
        
        for movie in all_movies:
            # Create a key combining normalized title and year
            key = f"{movie.normalized_title}_{movie.year or 'unknown'}"
            
            movie_file = MovieDuplicateFile(
                path=movie.file_path,
                size=movie.file_size,
                title=movie.title,
                year=movie.year or 0,
                normalized_title=movie.normalized_title
            )
            grouped_movies[key].append(movie_file)
        
        # Find groups with more than one file (duplicates)
        duplicate_groups = []
        for key, files in grouped_movies.items():
            if len(files) > 1:
                # Sort by file size (descending) to identify best quality
                files.sort(key=lambda f: f.size, reverse=True)
                best_file = files[0]  # Largest file
                
                # Create normalized name for display
                normalized_name = f"{files[0].title} ({files[0].year})" if files[0].year else files[0].title
                
                duplicate_group = MovieDuplicateGroup(
                    normalized_name=normalized_name,
                    files=files,
                    best_file=best_file
                )
                duplicate_groups.append(duplicate_group)
        
        # Sort by normalized name for consistent output
        duplicate_groups.sort(key=lambda g: g.normalized_name)
        
        return duplicate_groups
    
    def find_tv_duplicates(self) -> List[TVDuplicateGroup]:
        """
        Find duplicate TV episodes using database entries.
        
        Returns:
            List of TVDuplicateGroup objects containing duplicates
        """
        # Get all TV episodes from database
        all_episodes = self.database.get_all_tv_episodes()
        
        if not all_episodes:
            return []
        
        # Group episodes by show + season + episode
        grouped_episodes = defaultdict(list)
        
        for episode in all_episodes:
            # Create a key combining show, season, and episode
            key = f"{episode.normalized_show_name}_S{episode.season:02d}E{episode.episode:02d}"
            
            episode_file = TVDuplicateFile(
                path=episode.file_path,
                size=episode.file_size,
                show_name=episode.show_name,
                season=episode.season,
                episode=episode.episode,
                normalized_show_name=episode.normalized_show_name
            )
            grouped_episodes[key].append(episode_file)
        
        # Find groups with more than one file (duplicates)
        duplicate_groups = []
        for key, files in grouped_episodes.items():
            if len(files) > 1:
                # Sort by file size (descending) to identify best quality
                files.sort(key=lambda f: f.size, reverse=True)
                best_file = files[0]  # Largest file
                
                duplicate_group = TVDuplicateGroup(
                    show_name=files[0].show_name,
                    season=files[0].season,
                    episode=files[0].episode,
                    files=files,
                    best_file=best_file
                )
                duplicate_groups.append(duplicate_group)
        
        # Sort by show name, then season, then episode for consistent output
        duplicate_groups.sort(key=lambda g: (g.show_name, g.season, g.episode))
        
        return duplicate_groups
    
    def get_duplicate_stats(self) -> Dict[str, int]:
        """
        Get statistics about duplicates in the database.
        
        Returns:
            Dictionary with duplicate statistics
        """
        movie_duplicates = self.find_movie_duplicates()
        tv_duplicates = self.find_tv_duplicates()
        
        movie_duplicate_files = sum(len(group.files) - 1 for group in movie_duplicates)
        tv_duplicate_files = sum(len(group.files) - 1 for group in tv_duplicates)
        
        movie_wasted_space = sum(
            sum(f.size for f in group.files if f != group.best_file)
            for group in movie_duplicates
        )
        
        tv_wasted_space = sum(
            sum(f.size for f in group.files if f != group.best_file)
            for group in tv_duplicates
        )
        
        return {
            'movie_duplicate_groups': len(movie_duplicates),
            'movie_duplicate_files': movie_duplicate_files,
            'tv_duplicate_groups': len(tv_duplicates),
            'tv_duplicate_files': tv_duplicate_files,
            'total_duplicate_groups': len(movie_duplicates) + len(tv_duplicates),
            'total_duplicate_files': movie_duplicate_files + tv_duplicate_files,
            'movie_wasted_space_bytes': movie_wasted_space,
            'tv_wasted_space_bytes': tv_wasted_space,
            'total_wasted_space_bytes': movie_wasted_space + tv_wasted_space,
        }