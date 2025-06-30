"""JSON-based media database for fast query performance."""

import json
import os
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, asdict
import logging
from datetime import datetime

from .movie_scanner import scan_directory_for_movies, MovieFile
from .tv_scanner import scan_directory_for_tv_episodes, TVEpisode, group_episodes_by_show
from ..config.config import config

logger = logging.getLogger(__name__)

@dataclass
class DatabaseStats:
    """Statistics about the media database."""
    movies_count: int
    tv_shows_count: int 
    tv_episodes_count: int
    total_files: int
    total_size_bytes: int
    last_updated: str
    build_time_seconds: float
    directories_scanned: List[str]

@dataclass
class MovieEntry:
    """Movie entry in the database."""
    title: str
    normalized_title: str
    year: Optional[int]
    file_path: str
    file_name: str
    file_size: int
    directory: str
    last_modified: float
    
@dataclass 
class TVEpisodeEntry:
    """TV episode entry in the database."""
    show_name: str
    normalized_show_name: str
    season: int
    episode: int
    title: Optional[str]
    file_path: str
    file_name: str
    file_size: int
    directory: str
    last_modified: float

@dataclass
class TVShowEntry:
    """TV show summary entry in the database."""
    name: str
    normalized_name: str
    total_episodes: int
    seasons: List[int]
    total_size: int
    directories: Set[str]
    episodes: List[TVEpisodeEntry]

class MediaDatabase:
    """JSON-based media database for fast media queries."""
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize the media database.
        
        Args:
            db_path: Optional custom path for database file
        """
        if db_path:
            self.db_path = Path(db_path)
        else:
            # Store database in database directory
            project_root = Path(__file__).parent.parent.parent.parent
            database_dir = project_root / "database"
            database_dir.mkdir(exist_ok=True)
            self.db_path = database_dir / "media_database.json"
        
        self.data: Dict[str, Any] = {}
        self._load_database()
    
    def _load_database(self) -> None:
        """Load database from JSON file."""
        if self.db_path.exists():
            try:
                with open(self.db_path, 'r', encoding='utf-8') as f:
                    self.data = json.load(f)
                logger.info(f"Loaded media database from {self.db_path}")
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"Failed to load database: {e}. Starting with empty database.")
                self.data = self._get_empty_database()
        else:
            logger.info("Database file not found. Starting with empty database.")
            self.data = self._get_empty_database()
    
    def _get_empty_database(self) -> Dict[str, Any]:
        """Create empty database structure."""
        return {
            "version": "1.0",
            "created_at": datetime.now().isoformat(),
            "stats": {
                "movies_count": 0,
                "tv_shows_count": 0,
                "tv_episodes_count": 0,
                "total_files": 0,
                "total_size_bytes": 0,
                "last_updated": "",
                "build_time_seconds": 0.0,
                "directories_scanned": []
            },
            "movies": {},  # normalized_title: MovieEntry
            "tv_shows": {},  # normalized_name: TVShowEntry  
            "search_index": {
                "movie_titles": {},  # normalized_title -> original_title
                "tv_titles": {},     # normalized_name -> original_name
                "all_titles": {}     # for general search
            }
        }
    
    def rebuild_database(self, force: bool = False) -> DatabaseStats:
        """
        Rebuild the entire media database.
        
        Args:
            force: Force rebuild even if database seems current
            
        Returns:
            DatabaseStats with information about the built database
        """
        start_time = time.time()
        logger.info("Starting media database rebuild...")
        
        # Initialize new database
        self.data = self._get_empty_database()
        
        # Scan all directories
        movie_dirs = config.movie_directories
        tv_dirs = config.tv_directories
        all_dirs = movie_dirs + tv_dirs
        
        # Scan movies
        logger.info(f"Scanning {len(movie_dirs)} movie directories...")
        total_movies = 0
        for movie_dir in movie_dirs:
            if os.path.exists(movie_dir):
                movies = scan_directory_for_movies(movie_dir)
                total_movies += len(movies)
                self._add_movies_to_database(movies)
                logger.info(f"Added {len(movies)} movies from {movie_dir}")
        
        # Scan TV shows  
        logger.info(f"Scanning {len(tv_dirs)} TV directories...")
        total_episodes = 0
        for tv_dir in tv_dirs:
            if os.path.exists(tv_dir):
                episodes = scan_directory_for_tv_episodes(tv_dir)
                total_episodes += len(episodes) 
                self._add_tv_episodes_to_database(episodes)
                logger.info(f"Added {len(episodes)} TV episodes from {tv_dir}")
        
        # Build search indices
        self._build_search_indices()
        
        # Update stats
        build_time = time.time() - start_time
        stats = self._calculate_stats(all_dirs, build_time)
        self.data["stats"] = asdict(stats)
        
        # Save database
        self._save_database()
        
        logger.info(f"Database rebuild completed in {build_time:.2f} seconds")
        logger.info(f"Movies: {stats.movies_count}, TV Shows: {stats.tv_shows_count}, Episodes: {stats.tv_episodes_count}")
        
        return stats
    
    def _add_movies_to_database(self, movies: List[MovieFile]) -> None:
        """Add movies to the database."""
        for movie in movies:
            # Create movie entry
            entry = MovieEntry(
                title=movie.name,
                normalized_title=movie.normalized_name,
                year=int(movie.year) if movie.year and movie.year.isdigit() else None,
                file_path=str(movie.path),
                file_name=movie.name,
                file_size=movie.size,
                directory=str(movie.path.parent),
                last_modified=movie.path.stat().st_mtime
            )
            
            # Use normalized title as key for easy lookup
            self.data["movies"][movie.normalized_name] = asdict(entry)
    
    def _add_tv_episodes_to_database(self, episodes: List[TVEpisode]) -> None:
        """Add TV episodes to the database."""
        # Group episodes by show
        show_groups = group_episodes_by_show(episodes)
        
        for show_group in show_groups:
            show_name = show_group.show_name
            normalized_name = show_name.lower().strip()
            
            # Create episode entries
            episode_entries = []
            directories = set()
            
            for episode in show_group.episodes:
                episode_entry = TVEpisodeEntry(
                    show_name=episode.show_name,
                    normalized_show_name=normalized_name,
                    season=episode.season,
                    episode=episode.episode,
                    title=None,  # Could extract from filename in future
                    file_path=str(episode.path),
                    file_name=episode.name,
                    file_size=episode.size,
                    directory=str(episode.path.parent),
                    last_modified=episode.path.stat().st_mtime
                )
                episode_entries.append(episode_entry)
                directories.add(str(episode.path.parent))
            
            # Create show entry
            show_entry = TVShowEntry(
                name=show_name,
                normalized_name=normalized_name,
                total_episodes=len(episode_entries),
                seasons=sorted(list(set(ep.season for ep in episode_entries))),
                total_size=sum(ep.file_size for ep in episode_entries),
                directories=directories,
                episodes=episode_entries
            )
            
            # Convert to dict for JSON serialization
            show_dict = asdict(show_entry)
            show_dict["directories"] = list(directories)  # Convert set to list
            
            self.data["tv_shows"][normalized_name] = show_dict
    
    def _build_search_indices(self) -> None:
        """Build search indices for fast lookups."""
        # Movie title index
        movie_titles = {}
        for normalized_title, movie in self.data["movies"].items():
            movie_titles[normalized_title] = movie["title"]
        
        # TV show title index  
        tv_titles = {}
        for normalized_name, show in self.data["tv_shows"].items():
            tv_titles[normalized_name] = show["name"]
        
        # Combined index for general searches
        all_titles = {}
        all_titles.update(movie_titles)
        all_titles.update(tv_titles)
        
        self.data["search_index"] = {
            "movie_titles": movie_titles,
            "tv_titles": tv_titles,
            "all_titles": all_titles
        }
    
    def _calculate_stats(self, directories: List[str], build_time: float) -> DatabaseStats:
        """Calculate database statistics."""
        movies_count = len(self.data["movies"])
        tv_shows_count = len(self.data["tv_shows"])
        
        # Count total episodes
        tv_episodes_count = sum(
            show["total_episodes"] for show in self.data["tv_shows"].values()
        )
        
        total_files = movies_count + tv_episodes_count
        
        # Calculate total size
        total_size = sum(movie["file_size"] for movie in self.data["movies"].values())
        total_size += sum(show["total_size"] for show in self.data["tv_shows"].values())
        
        return DatabaseStats(
            movies_count=movies_count,
            tv_shows_count=tv_shows_count,
            tv_episodes_count=tv_episodes_count,
            total_files=total_files,
            total_size_bytes=total_size,
            last_updated=datetime.now().isoformat(),
            build_time_seconds=round(build_time, 2),
            directories_scanned=directories
        )
    
    def _save_database(self) -> None:
        """Save database to JSON file."""
        try:
            with open(self.db_path, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
            logger.info(f"Database saved to {self.db_path}")
        except IOError as e:
            logger.error(f"Failed to save database: {e}")
            raise
    
    def search_movies(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Search for movies in the database.
        
        Args:
            query: Search query
            limit: Maximum results to return
            
        Returns:
            List of movie matches
        """
        query_normalized = query.lower().strip()
        matches = []
        
        for normalized_title, movie in self.data["movies"].items():
            # Calculate similarity score
            score = self._calculate_similarity(normalized_title, query_normalized)
            if score > 0.15:  # Lower threshold for movie series
                movie_match = movie.copy()
                movie_match["confidence"] = score
                movie_match["media_type"] = "movie"
                matches.append(movie_match)
        
        # Sort by confidence and return top results
        matches.sort(key=lambda x: x["confidence"], reverse=True)
        return matches[:limit]
    
    def search_tv_shows(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Search for TV shows in the database.
        
        Args:
            query: Search query  
            limit: Maximum results to return
            
        Returns:
            List of TV show matches
        """
        query_normalized = query.lower().strip()
        matches = []
        
        # Use lower threshold for TV searches to handle partial matches
        threshold = 0.3 if len(query_normalized) <= 4 else 0.35
        
        for normalized_name, show in self.data["tv_shows"].items():
            # Calculate similarity score with enhanced matching
            score = self._calculate_tv_similarity(normalized_name, query_normalized)
            if score > threshold:
                show_match = show.copy()
                show_match["confidence"] = score
                show_match["media_type"] = "tv"
                matches.append(show_match)
        
        # Sort by confidence and return top results
        matches.sort(key=lambda x: x["confidence"], reverse=True)
        return matches[:limit]
    
    def get_tv_show_details(self, show_name: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a TV show.
        
        Args:
            show_name: TV show name
            
        Returns:
            TV show details or None if not found
        """
        normalized_name = show_name.lower().strip()
        
        # Direct lookup first
        if normalized_name in self.data["tv_shows"]:
            return self.data["tv_shows"][normalized_name]
        
        # Fuzzy search as fallback
        matches = self.search_tv_shows(show_name, limit=1)
        if matches:
            show_name = matches[0]["normalized_name"]
            return self.data["tv_shows"].get(show_name)
        
        return None
    
    def get_stats(self) -> DatabaseStats:
        """Get database statistics."""
        stats_dict = self.data.get("stats", {})
        return DatabaseStats(**stats_dict) if stats_dict else DatabaseStats(0, 0, 0, 0, 0, "", 0.0, [])
    
    def is_current(self, max_age_hours: int = 24) -> bool:
        """
        Check if database is current.
        
        Args:
            max_age_hours: Maximum age in hours to consider current
            
        Returns:
            True if database is current
        """
        stats = self.get_stats()
        if not stats.last_updated:
            return False
        
        try:
            last_updated = datetime.fromisoformat(stats.last_updated)
            age_hours = (datetime.now() - last_updated).total_seconds() / 3600
            return age_hours <= max_age_hours
        except (ValueError, TypeError):
            return False
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two strings."""
        if not text1 or not text2:
            return 0.0
        
        # Exact match
        if text1 == text2:
            return 1.0
        
        # Substring match (higher score for movie series)
        if text1 in text2 or text2 in text1:
            shorter = min(len(text1), len(text2))
            longer = max(len(text1), len(text2))
            # Give higher score if shorter text is significant portion
            ratio = shorter / longer
            if ratio > 0.6:  # e.g., "john wick" in "john wick chapter 2"
                return 0.95
            else:
                return ratio * 0.9
        
        # Word overlap scoring (improved for movie series)
        words1 = set(text1.split())
        words2 = set(text2.split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        # Boost score if query words are all present in target
        if words1.issubset(words2):
            return min(0.9, intersection / len(words2))
        
        return intersection / union if union > 0 else 0.0
    
    def _calculate_tv_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate similarity for TV shows with enhanced partial matching.
        
        Args:
            text1: Target show name (from database)
            text2: Search query
            
        Returns:
            Similarity score between 0.0 and 1.0
        """
        if not text1 or not text2:
            return 0.0
        
        # Exact match
        if text1 == text2:
            return 1.0
        
        # Substring match - check if query is contained in show name
        if text2 in text1:
            # For short queries (like "kin"), give a good score if it's a significant match
            if len(text2) <= 4:
                # Check if it's at word boundaries for better relevance
                words1 = text1.split()
                for word in words1:
                    if text2 in word:
                        # Higher score if query makes up significant portion of a word
                        word_ratio = len(text2) / len(word)
                        if word_ratio >= 0.5:  # e.g., "kin" in "king" or "vikings"
                            return 0.8
                        else:
                            return 0.6
                # Fallback for general substring match
                return 0.5
            else:
                # For longer queries, use length-based scoring
                ratio = len(text2) / len(text1)
                return min(0.9, ratio * 1.2)
        
        # Check if show name contains query as substring
        if text1 in text2:
            ratio = len(text1) / len(text2)
            return min(0.8, ratio * 1.1)
        
        # Word-level matching
        words1 = set(text1.split())
        words2 = set(text2.split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        # Boost score if all query words are present in target
        if words2.issubset(words1):
            return min(0.9, intersection / len(words1))
        
        # Check for partial word matches within the words
        partial_matches = 0
        for query_word in words2:
            for target_word in words1:
                if len(query_word) >= 3 and query_word in target_word:
                    partial_matches += 0.5
                elif len(target_word) >= 3 and target_word in query_word:
                    partial_matches += 0.3
        
        # Combine exact word matches with partial matches
        word_score = intersection / union if union > 0 else 0.0
        partial_score = min(partial_matches / len(words2), 0.7)
        
        return max(word_score, partial_score)
    
    def get_all_movies(self) -> List[MovieEntry]:
        """
        Get all movies as MovieEntry objects.
        
        Returns:
            List of MovieEntry objects
        """
        movies = []
        for movie_data in self.data["movies"].values():
            movie = MovieEntry(**movie_data)
            movies.append(movie)
        return movies
    
    def get_all_tv_episodes(self) -> List[TVEpisodeEntry]:
        """
        Get all TV episodes as TVEpisodeEntry objects.
        
        Returns:
            List of TVEpisodeEntry objects
        """
        episodes = []
        for show_data in self.data["tv_shows"].values():
            for episode_data in show_data["episodes"]:
                episode = TVEpisodeEntry(**episode_data)
                episodes.append(episode)
        return episodes