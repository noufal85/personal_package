"""
OMDB Rating Fetcher - Fetch movie ratings and build database for quality management.

This utility fetches ratings from OMDB API for movies in the collection and stores
them in a local database for future operations like deleting badly rated movies.
"""

import os
import json
import sqlite3
import time
import logging
import re
import requests
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Load environment variables
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent.parent.parent.parent / '.env'
    load_dotenv(env_path)
except ImportError:
    # dotenv not available, try to load manually
    env_path = Path(__file__).parent.parent.parent.parent / '.env'
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                if '=' in line and not line.strip().startswith('#'):
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value

from ..config.config import config


@dataclass
class MovieRating:
    """Represents a movie with OMDB ratings."""
    title: str
    year: Optional[int]
    imdb_id: Optional[str]
    imdb_rating: Optional[float]
    rotten_tomatoes: Optional[int]  # Percentage
    metacritic: Optional[int]       # Score out of 100
    omdb_plot: Optional[str]
    omdb_genre: Optional[str]
    omdb_director: Optional[str]
    omdb_runtime: Optional[str]
    file_path: str
    file_size: int
    last_updated: datetime
    api_source: str = "omdb"
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        data['last_updated'] = self.last_updated.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'MovieRating':
        """Create instance from dictionary."""
        data['last_updated'] = datetime.fromisoformat(data['last_updated'])
        return cls(**data)
    
    def get_quality_score(self) -> float:
        """Calculate overall quality score from available ratings."""
        scores = []
        
        if self.imdb_rating is not None:
            # Convert IMDB 0-10 to 0-100
            scores.append(self.imdb_rating * 10)
        
        if self.rotten_tomatoes is not None:
            scores.append(self.rotten_tomatoes)
        
        if self.metacritic is not None:
            scores.append(self.metacritic)
        
        return sum(scores) / len(scores) if scores else 0.0
    
    def is_badly_rated(self, imdb_threshold: float = 5.0, rt_threshold: int = 30, meta_threshold: int = 40) -> bool:
        """Check if movie is badly rated based on thresholds."""
        bad_ratings = 0
        total_ratings = 0
        
        if self.imdb_rating is not None:
            total_ratings += 1
            if self.imdb_rating < imdb_threshold:
                bad_ratings += 1
        
        if self.rotten_tomatoes is not None:
            total_ratings += 1
            if self.rotten_tomatoes < rt_threshold:
                bad_ratings += 1
        
        if self.metacritic is not None:
            total_ratings += 1
            if self.metacritic < meta_threshold:
                bad_ratings += 1
        
        # Consider badly rated if majority of available ratings are bad
        return total_ratings > 0 and (bad_ratings / total_ratings) >= 0.5


class OMDBRatingDatabase:
    """SQLite database for movie ratings."""
    
    def __init__(self, db_file: str = "movie_ratings.db"):
        self.db_path = Path(__file__).parent.parent.parent.parent / 'database' / db_file
        self.db_path.parent.mkdir(exist_ok=True)
        self._init_database()
    
    def _init_database(self):
        """Initialize the ratings database."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS movie_ratings (
                title_key TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                year INTEGER,
                imdb_id TEXT,
                imdb_rating REAL,
                rotten_tomatoes INTEGER,
                metacritic INTEGER,
                omdb_plot TEXT,
                omdb_genre TEXT,
                omdb_director TEXT,
                omdb_runtime TEXT,
                file_path TEXT NOT NULL,
                file_size INTEGER NOT NULL,
                last_updated TEXT NOT NULL,
                api_source TEXT DEFAULT 'omdb'
            )
        ''')
        
        # Create indexes for faster queries
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_imdb_rating ON movie_ratings(imdb_rating)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_quality_score ON movie_ratings(imdb_rating, rotten_tomatoes, metacritic)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_last_updated ON movie_ratings(last_updated)')
        
        conn.commit()
        conn.close()
    
    def get_rating(self, title: str, year: Optional[int] = None) -> Optional[MovieRating]:
        """Get rating from database."""
        title_key = self._generate_title_key(title, year)
        
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM movie_ratings WHERE title_key = ?
        ''', (title_key,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            # Convert tuple to MovieRating
            columns = ['title_key', 'title', 'year', 'imdb_id', 'imdb_rating', 'rotten_tomatoes', 
                      'metacritic', 'omdb_plot', 'omdb_genre', 'omdb_director', 'omdb_runtime',
                      'file_path', 'file_size', 'last_updated', 'api_source']
            data = dict(zip(columns, result))
            
            # Remove title_key and convert types
            del data['title_key']
            data['last_updated'] = datetime.fromisoformat(data['last_updated'])
            
            return MovieRating(**data)
        
        return None
    
    def save_rating(self, rating: MovieRating) -> None:
        """Save rating to database."""
        title_key = self._generate_title_key(rating.title, rating.year)
        
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO movie_ratings 
            (title_key, title, year, imdb_id, imdb_rating, rotten_tomatoes, metacritic,
             omdb_plot, omdb_genre, omdb_director, omdb_runtime, file_path, file_size, 
             last_updated, api_source)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            title_key, rating.title, rating.year, rating.imdb_id, rating.imdb_rating,
            rating.rotten_tomatoes, rating.metacritic, rating.omdb_plot, rating.omdb_genre,
            rating.omdb_director, rating.omdb_runtime, rating.file_path, rating.file_size,
            rating.last_updated.isoformat(), rating.api_source
        ))
        
        conn.commit()
        conn.close()
    
    def get_badly_rated_movies(self, imdb_threshold: float = 5.0, rt_threshold: int = 30, 
                             meta_threshold: int = 40) -> List[MovieRating]:
        """Get all badly rated movies."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM movie_ratings')
        results = cursor.fetchall()
        conn.close()
        
        badly_rated = []
        for result in results:
            columns = ['title_key', 'title', 'year', 'imdb_id', 'imdb_rating', 'rotten_tomatoes', 
                      'metacritic', 'omdb_plot', 'omdb_genre', 'omdb_director', 'omdb_runtime',
                      'file_path', 'file_size', 'last_updated', 'api_source']
            data = dict(zip(columns, result))
            del data['title_key']
            data['last_updated'] = datetime.fromisoformat(data['last_updated'])
            
            rating = MovieRating(**data)
            if rating.is_badly_rated(imdb_threshold, rt_threshold, meta_threshold):
                badly_rated.append(rating)
        
        return badly_rated
    
    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM movie_ratings')
        total_movies = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM movie_ratings WHERE imdb_rating IS NOT NULL')
        with_imdb = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM movie_ratings WHERE rotten_tomatoes IS NOT NULL')
        with_rt = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM movie_ratings WHERE metacritic IS NOT NULL')
        with_meta = cursor.fetchone()[0]
        
        cursor.execute('SELECT AVG(imdb_rating) FROM movie_ratings WHERE imdb_rating IS NOT NULL')
        avg_imdb = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'total_movies': total_movies,
            'with_imdb_rating': with_imdb,
            'with_rotten_tomatoes': with_rt,
            'with_metacritic': with_meta,
            'average_imdb_rating': round(avg_imdb, 2) if avg_imdb else None,
            'database_path': str(self.db_path)
        }
    
    def _generate_title_key(self, title: str, year: Optional[int]) -> str:
        """Generate unique key for title and year."""
        clean_title = re.sub(r'[^\w\s]', '', title.lower()).strip()
        clean_title = re.sub(r'\s+', ' ', clean_title)
        return f"{clean_title}_{year or 0}"


class OMDBRatingFetcher:
    """Fetches movie ratings from OMDB API."""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('OMDB_API_KEY', '42df6e0e')
        self.base_url = "http://www.omdbapi.com/"
        self.session = requests.Session()
        self.database = OMDBRatingDatabase()
        
        # Setup session with retry strategy
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 0.1  # 10 requests per second max
        
        # Setup logging
        self.logger = self._setup_logging()
        
        # Stats
        self.stats = {
            'api_calls': 0,
            'successful_fetches': 0,
            'failed_fetches': 0,
            'cache_hits': 0,
            'rate_limited': 0
        }
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging for the rating fetcher."""
        session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        logger = logging.getLogger(f"omdb_rating_fetcher_{session_id}")
        
        if logger.handlers:
            return logger
        
        logger.setLevel(logging.INFO)
        
        # Create logs directory
        logs_dir = Path("logs")
        logs_dir.mkdir(exist_ok=True)
        
        # File handler
        log_file = logs_dir / f"omdb_rating_fetcher_{session_id}.log"
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(funcName)-20s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        self.log_file_path = log_file
        logger.info("=" * 60)
        logger.info(f"OMDB Rating Fetcher Session Started: {session_id}")
        logger.info(f"API Key: {self.api_key[:8]}..." if self.api_key else "No API key")
        logger.info("=" * 60)
        
        return logger
    
    def _rate_limit(self):
        """Enforce rate limiting."""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_request_interval:
            sleep_time = self.min_request_interval - elapsed
            time.sleep(sleep_time)
        self.last_request_time = time.time()
    
    def _extract_title_and_year(self, filename: str) -> Tuple[str, Optional[int]]:
        """Extract movie title and year from filename."""
        # Remove file extension
        name = Path(filename).stem
        
        # Look for year pattern (4 digits in parentheses or standalone)
        year_match = re.search(r'\b(19|20)\d{2}\b', name)
        year = int(year_match.group()) if year_match else None
        
        # Remove year and quality indicators
        title = re.sub(r'\b(19|20)\d{2}\b', '', name)
        title = re.sub(r'\b(720p|1080p|2160p|4K|HD|BluRay|WEB-DL|WEBRip|HDTV|DVDRip)\b', '', title, flags=re.IGNORECASE)
        title = re.sub(r'\b(x264|x265|HEVC|DTS|AC3|AAC|MP3)\b', '', title, flags=re.IGNORECASE)
        title = re.sub(r'[._-]', ' ', title)
        title = re.sub(r'\s+', ' ', title).strip()
        
        # Remove common release group patterns
        title = re.sub(r'\b(RARBG|YIFY|aXXo|FGT|SPARKS|FLEET|NTG|TRF|BRUH|PRoDJi)\b', '', title, flags=re.IGNORECASE)
        title = re.sub(r'\s+', ' ', title).strip()
        
        return title, year
    
    def fetch_rating(self, title: str, year: Optional[int] = None, imdb_id: Optional[str] = None) -> Optional[MovieRating]:
        """Fetch rating from OMDB API."""
        # Check cache first
        cached = self.database.get_rating(title, year)
        if cached:
            # Check if cache is recent (less than 30 days old)
            if datetime.now() - cached.last_updated < timedelta(days=30):
                self.stats['cache_hits'] += 1
                self.logger.debug(f"Cache hit for {title} ({year})")
                return cached
        
        self._rate_limit()
        self.stats['api_calls'] += 1
        
        # Prepare API parameters
        params = {'apikey': self.api_key}
        
        if imdb_id:
            params['i'] = imdb_id
        else:
            params['t'] = title
            if year:
                params['y'] = str(year)
        
        try:
            self.logger.debug(f"API request for {title} ({year})")
            response = self.session.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('Response') == 'False':
                self.logger.warning(f"OMDB API returned error for {title}: {data.get('Error')}")
                self.stats['failed_fetches'] += 1
                return None
            
            # Parse rating data
            imdb_rating = None
            if data.get('imdbRating') and data['imdbRating'] != 'N/A':
                try:
                    imdb_rating = float(data['imdbRating'])
                except ValueError:
                    pass
            
            rotten_tomatoes = None
            metacritic = None
            
            # Parse Ratings array
            for rating in data.get('Ratings', []):
                source = rating.get('Source', '')
                value = rating.get('Value', '')
                
                if 'Rotten Tomatoes' in source and '%' in value:
                    try:
                        rotten_tomatoes = int(value.replace('%', ''))
                    except ValueError:
                        pass
                elif 'Metacritic' in source and '/' in value:
                    try:
                        metacritic = int(value.split('/')[0])
                    except ValueError:
                        pass
            
            rating_obj = MovieRating(
                title=data.get('Title', title),
                year=int(data.get('Year', year or 0)) if data.get('Year') and data['Year'] != 'N/A' else year,
                imdb_id=data.get('imdbID'),
                imdb_rating=imdb_rating,
                rotten_tomatoes=rotten_tomatoes,
                metacritic=metacritic,
                omdb_plot=data.get('Plot') if data.get('Plot') != 'N/A' else None,
                omdb_genre=data.get('Genre') if data.get('Genre') != 'N/A' else None,
                omdb_director=data.get('Director') if data.get('Director') != 'N/A' else None,
                omdb_runtime=data.get('Runtime') if data.get('Runtime') != 'N/A' else None,
                file_path="",  # Will be set by caller
                file_size=0,   # Will be set by caller
                last_updated=datetime.now()
            )
            
            self.stats['successful_fetches'] += 1
            self.logger.info(f"Successfully fetched rating for {title}: IMDB={imdb_rating}, RT={rotten_tomatoes}%, Meta={metacritic}")
            
            return rating_obj
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"API request failed for {title}: {e}")
            self.stats['failed_fetches'] += 1
            return None
        except Exception as e:
            self.logger.error(f"Error processing rating for {title}: {e}")
            self.stats['failed_fetches'] += 1
            return None
    
    def fetch_ratings_for_movies(self, movie_files: List[Dict[str, Any]], progress_callback=None) -> Dict[str, Any]:
        """Fetch ratings for a list of movie files."""
        total_movies = len(movie_files)
        processed = 0
        
        self.logger.info(f"Starting rating fetch for {total_movies} movies")
        
        for i, movie in enumerate(movie_files):
            if progress_callback:
                progress_callback(i + 1, total_movies, movie.get('file_name', 'Unknown'))
            
            filename = movie.get('file_name', '')
            file_path = movie.get('file_path', '')
            file_size = movie.get('file_size', 0)
            
            if not filename:
                continue
            
            title, year = self._extract_title_and_year(filename)
            
            if not title:
                self.logger.warning(f"Could not extract title from: {filename}")
                continue
            
            # Fetch rating
            rating = self.fetch_rating(title, year)
            
            if rating:
                # Set file info
                rating.file_path = file_path
                rating.file_size = file_size
                
                # Save to database
                self.database.save_rating(rating)
                processed += 1
                
                print(f"   ✅ {title} ({year}): IMDB={rating.imdb_rating or 'N/A'}, RT={rating.rotten_tomatoes or 'N/A'}%, Meta={rating.metacritic or 'N/A'}")
            else:
                print(f"   ❌ {title} ({year}): No rating found")
            
            # Small delay to be nice to the API
            time.sleep(0.1)
        
        # Generate summary
        summary = {
            'total_movies': total_movies,
            'processed': processed,
            'success_rate': (processed / total_movies * 100) if total_movies > 0 else 0,
            'stats': self.stats.copy(),
            'log_file': str(self.log_file_path)
        }
        
        self.logger.info(f"Rating fetch completed: {processed}/{total_movies} movies processed ({summary['success_rate']:.1f}% success rate)")
        self.logger.info(f"API Stats: {self.stats['api_calls']} calls, {self.stats['successful_fetches']} successful, {self.stats['cache_hits']} cache hits")
        
        return summary
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get rating database statistics."""
        return self.database.get_stats()