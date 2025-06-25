"""
Metadata Enrichment Tool for Media Classification

This tool queries external APIs (TMDB, TVDB) to gather accurate metadata
for media files and caches the results locally to improve classification
accuracy and avoid repeated API calls.
"""

import os
import json
import sqlite3
import time
import logging
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    # Load .env file from project root
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
class MediaMetadata:
    """Represents metadata for a media item."""
    title: str
    year: Optional[int]
    tmdb_id: Optional[int]
    tvdb_id: Optional[int]
    media_type: str  # movie, tv, documentary, standup, etc.
    genres: List[str]
    overview: str
    runtime: Optional[int]
    status: str
    original_language: str
    popularity: float
    vote_average: float
    api_source: str  # tmdb, tvdb
    last_updated: datetime
    confidence: float  # How confident we are in this classification
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        data['last_updated'] = self.last_updated.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'MediaMetadata':
        """Create instance from dictionary."""
        data['last_updated'] = datetime.fromisoformat(data['last_updated'])
        return cls(**data)


class MetadataCache:
    """SQLite-based cache for metadata."""
    
    def __init__(self, cache_file: str = "metadata_cache.db"):
        self.cache_path = Path(__file__).parent.parent.parent.parent / 'database' / cache_file
        self.cache_path.parent.mkdir(exist_ok=True)
        self._init_database()
    
    def _init_database(self):
        """Initialize the cache database."""
        conn = sqlite3.connect(str(self.cache_path))
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS metadata_cache (
                title_key TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                year INTEGER,
                tmdb_id INTEGER,
                tvdb_id INTEGER,
                media_type TEXT NOT NULL,
                genres TEXT,  -- JSON array
                overview TEXT,
                runtime INTEGER,
                status TEXT,
                original_language TEXT,
                popularity REAL,
                vote_average REAL,
                api_source TEXT,
                last_updated TEXT,
                confidence REAL,
                raw_response TEXT  -- Store full API response
            )
        ''')
        
        # Create index for faster lookups
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_title_year 
            ON metadata_cache (title, year)
        ''')
        
        conn.commit()
        conn.close()
    
    def get_metadata(self, title: str, year: Optional[int] = None) -> Optional[MediaMetadata]:
        """Get cached metadata for a title."""
        title_key = self._create_key(title, year)
        
        conn = sqlite3.connect(str(self.cache_path))
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT title, year, tmdb_id, tvdb_id, media_type, genres, overview,
                   runtime, status, original_language, popularity, vote_average,
                   api_source, last_updated, confidence
            FROM metadata_cache WHERE title_key = ?
        ''', (title_key,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return MediaMetadata(
                title=row[0],
                year=row[1],
                tmdb_id=row[2],
                tvdb_id=row[3],
                media_type=row[4],
                genres=json.loads(row[5]) if row[5] else [],
                overview=row[6] or "",
                runtime=row[7],
                status=row[8] or "",
                original_language=row[9] or "",
                popularity=row[10] or 0.0,
                vote_average=row[11] or 0.0,
                api_source=row[12] or "",
                last_updated=datetime.fromisoformat(row[13]),
                confidence=row[14] or 0.0
            )
        return None
    
    def store_metadata(self, metadata: MediaMetadata, raw_response: Dict = None):
        """Store metadata in cache."""
        title_key = self._create_key(metadata.title, metadata.year)
        
        conn = sqlite3.connect(str(self.cache_path))
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO metadata_cache 
            (title_key, title, year, tmdb_id, tvdb_id, media_type, genres, overview,
             runtime, status, original_language, popularity, vote_average,
             api_source, last_updated, confidence, raw_response)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            title_key, metadata.title, metadata.year, metadata.tmdb_id, metadata.tvdb_id,
            metadata.media_type, json.dumps(metadata.genres), metadata.overview,
            metadata.runtime, metadata.status, metadata.original_language,
            metadata.popularity, metadata.vote_average, metadata.api_source,
            metadata.last_updated.isoformat(), metadata.confidence,
            json.dumps(raw_response) if raw_response else None
        ))
        
        conn.commit()
        conn.close()
    
    def _create_key(self, title: str, year: Optional[int]) -> str:
        """Create a normalized key for title lookup."""
        # Normalize title: lowercase, remove special chars, collapse whitespace
        normalized = re.sub(r'[^\w\s]', '', title.lower())
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        return f"{normalized}_{year}" if year else normalized
    
    def get_stats(self) -> Dict:
        """Get cache statistics."""
        conn = sqlite3.connect(str(self.cache_path))
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM metadata_cache')
        total_items = cursor.fetchone()[0]
        
        cursor.execute('SELECT media_type, COUNT(*) FROM metadata_cache GROUP BY media_type')
        type_counts = dict(cursor.fetchall())
        
        cursor.execute('SELECT api_source, COUNT(*) FROM metadata_cache GROUP BY api_source')
        source_counts = dict(cursor.fetchall())
        
        conn.close()
        
        return {
            'total_items': total_items,
            'by_type': type_counts,
            'by_source': source_counts
        }


class APIClient:
    """Enhanced API client with retry logic and rate limiting."""
    
    def __init__(self):
        self.tmdb_api_key = os.getenv('TMDB_API_KEY')
        self.tvdb_api_key = os.getenv('TVDB_API_KEY')
        self.session = self._create_session()
        self.last_request_time = {}
        self.request_delay = 0.25  # 250ms between requests
        
    def _create_session(self) -> requests.Session:
        """Create a session with retry strategy."""
        session = requests.Session()
        
        # Retry strategy for rate limiting and temporary failures
        retry_strategy = Retry(
            total=5,
            backoff_factor=2,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        return session
    
    def _rate_limit(self, api_name: str):
        """Implement rate limiting."""
        now = time.time()
        if api_name in self.last_request_time:
            time_since_last = now - self.last_request_time[api_name]
            if time_since_last < self.request_delay:
                sleep_time = self.request_delay - time_since_last
                time.sleep(sleep_time)
        
        self.last_request_time[api_name] = time.time()
    
    def search_tmdb_movie(self, title: str, year: Optional[int] = None) -> Optional[Dict]:
        """Search for a movie on TMDB."""
        if not self.tmdb_api_key:
            return None
        
        self._rate_limit('tmdb')
        
        url = "https://api.themoviedb.org/3/search/movie"
        params = {
            'api_key': self.tmdb_api_key,
            'query': title,
            'include_adult': 'true'
        }
        
        if year:
            params['year'] = year
        
        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data['results']:
                # Return the first (most relevant) result
                return data['results'][0]
                
        except requests.RequestException as e:
            logging.error(f"TMDB movie search failed for '{title}': {e}")
        
        return None
    
    def search_tmdb_tv(self, title: str, year: Optional[int] = None) -> Optional[Dict]:
        """Search for a TV show on TMDB."""
        if not self.tmdb_api_key:
            return None
        
        self._rate_limit('tmdb')
        
        url = "https://api.themoviedb.org/3/search/tv"
        params = {
            'api_key': self.tmdb_api_key,
            'query': title,
            'include_adult': 'true'
        }
        
        if year:
            params['first_air_date_year'] = year
        
        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data['results']:
                return data['results'][0]
                
        except requests.RequestException as e:
            logging.error(f"TMDB TV search failed for '{title}': {e}")
        
        return None
    
    def get_tmdb_movie_details(self, movie_id: int) -> Optional[Dict]:
        """Get detailed movie information from TMDB."""
        if not self.tmdb_api_key:
            return None
        
        self._rate_limit('tmdb')
        
        url = f"https://api.themoviedb.org/3/movie/{movie_id}"
        params = {'api_key': self.tmdb_api_key}
        
        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
            
        except requests.RequestException as e:
            logging.error(f"TMDB movie details failed for ID {movie_id}: {e}")
        
        return None


class MetadataEnricher:
    """Main metadata enrichment orchestrator."""
    
    def __init__(self):
        self.cache = MetadataCache()
        self.api_client = APIClient()
        self.logger = self._setup_logging()
        self.database_path = Path(__file__).parent.parent.parent.parent / 'database' / 'media_database.json'
        
    def _setup_logging(self) -> logging.Logger:
        """Set up logging for the enrichment process."""
        logger = logging.getLogger('metadata_enrichment')
        
        # Clear any existing handlers to avoid duplicates
        logger.handlers.clear()
        logger.setLevel(logging.INFO)
        
        # Create logs directory
        logs_dir = Path(__file__).parent.parent.parent.parent / 'logs'
        logs_dir.mkdir(exist_ok=True)
        
        # Create file handler
        session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = logs_dir / f"metadata_enrichment_{session_id}.log"
        
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        
        # Create console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(funcName)-20s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        return logger
    
    def load_media_database(self) -> Dict:
        """Load the existing media database."""
        if not self.database_path.exists():
            self.logger.error(f"Media database not found at {self.database_path}")
            return {}
        
        try:
            with open(self.database_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"Failed to load media database: {e}")
            return {}
    
    def extract_title_and_year(self, filename: str) -> Tuple[str, Optional[int]]:
        """Extract clean title and year from filename."""
        # Remove file extension
        name = Path(filename).stem
        
        # Common patterns to remove
        patterns_to_remove = [
            r'\b\d{3,4}p\b',  # Resolution (720p, 1080p, etc.)
            r'\b(BluRay|WEB-?DL|WEBRip|HDTV|DVDRip|BRRip)\b',  # Source
            r'\b(x264|x265|H\.?264|H\.?265|HEVC)\b',  # Codec
            r'\b(AAC|AC3|DTS|DD|DDP)\b',  # Audio
            r'\b(5\.1|7\.1|2\.0)\b',  # Audio channels
            r'\b(PROPER|REPACK|EXTENDED|UNRATED|DIRECTOR.?S.?CUT)\b',  # Versions
            r'\[[^\]]*\]',  # Brackets content
            r'\([^)]*(?:rip|web|bluray|hdtv)[^)]*\)',  # Parentheses with quality info
        ]
        
        cleaned = name
        for pattern in patterns_to_remove:
            cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
        
        # Extract year (4 digits, typically 1900-2099)
        year_match = re.search(r'\b(19\d{2}|20\d{2})\b', cleaned)
        year = int(year_match.group(1)) if year_match else None
        
        # Remove year from title
        if year_match:
            cleaned = cleaned.replace(year_match.group(0), '')
        
        # Clean up title
        title = re.sub(r'[^\w\s]', ' ', cleaned)  # Replace special chars with spaces
        title = re.sub(r'\s+', ' ', title).strip()  # Collapse whitespace
        
        return title, year
    
    def classify_media_type(self, tmdb_data: Dict, search_type: str) -> Tuple[str, float]:
        """Classify media type based on TMDB data."""
        if not tmdb_data:
            return "unknown", 0.0
        
        genres = [g['name'].lower() for g in tmdb_data.get('genres', [])]
        title = tmdb_data.get('title', tmdb_data.get('name', '')).lower()
        overview = tmdb_data.get('overview', '').lower()
        
        # Documentary detection
        if 'documentary' in genres:
            return "documentaries", 0.95
        
        # Stand-up comedy detection (title-based only to avoid false positives)
        # Movies ABOUT comedians (like Joker) should not be classified as standup
        standup_keywords = ['stand-up', 'stand up', 'comedy special', 'live comedy', 'live at']
        if any(keyword in title for keyword in standup_keywords):
            return "standup", 0.90
        
        # Comedy detection for potential stand-up (EXTREMELY restrictive to avoid false positives)
        # DISABLED: Too many false positives with movies like Naked, Joker, etc.
        # Only rely on explicit title-based detection above
        # 
        # Examples of movies that should NOT be standup:
        # - Naked (2017): Comedy movie about time loops
        # - Joker (2019): Crime/Thriller about failed comedian
        # - Any scripted comedy film regardless of genre count
        #
        # If we want to re-enable this, we need better heuristics like:
        # - Runtime detection (standup specials usually 45-90 min)
        # - Performer name matching (known comedians)
        # - More specific keywords ("comedy special", "live performance")
        pass
        
        # Default classification based on search type
        if search_type == 'movie':
            return "movies", 0.85
        elif search_type == 'tv':
            return "tv", 0.85
        
        return "unknown", 0.0
    
    def _clean_title_for_search(self, title: str) -> str:
        """Clean title by removing technical suffixes and encoding info."""
        import re
        
        # Remove technical suffixes that appear at the end of titles
        # Be conservative - only remove clear technical patterns
        technical_patterns = [
            r'\s+(REMUX|Remux)\s+\w+$',        # " Remux decatora27"
            r'\s+(PRoDJi|TRF|BRUH|LAMA|NTG|HRA|MA)$',  # Release group tags
            r'\s+(DTSHD|DDP5|AVC|HDMA|AMZN)(\s+\w+)*$',  # Audio/video codecs
            r'\s+(IMAX)(\s+IMAX)*(\s+EAC3)*$', # IMAX variants
            r'\s+(EAC3|ATMOS|MP3)\s*(Atmos)*$', # Audio formats
            r'\s+CD\d+$',                      # CD1, CD2
            r'\s+Version\s+\w+$',              # "Version Uncut"
            r'\s+10Bit(\s+DD5)*(\s+\d+)*(\s+\w+)*$', # 10Bit encoding
        ]
        
        cleaned_title = title
        for pattern in technical_patterns:
            cleaned_title = re.sub(pattern, '', cleaned_title, flags=re.IGNORECASE).strip()
        
        # Remove extra whitespace
        cleaned_title = re.sub(r'\s+', ' ', cleaned_title).strip()
        
        # If we removed everything, return original title
        if not cleaned_title:
            return title
        
        return cleaned_title

    def enrich_title(self, title: str, year: Optional[int] = None) -> Optional[MediaMetadata]:
        """Enrich a single title with metadata."""
        # Check cache first
        cached = self.cache.get_metadata(title, year)
        if cached and (datetime.now() - cached.last_updated).days < 30:
            self.logger.debug(f"Using cached metadata for {title} ({year})")
            return cached
        
        self.logger.info(f"Enriching: {title} ({year})")
        
        # Clean title for API search
        clean_title = self._clean_title_for_search(title)
        if clean_title != title:
            self.logger.debug(f"Cleaned title: '{title}' -> '{clean_title}'")
        
        # Try movie search first
        movie_data = self.api_client.search_tmdb_movie(clean_title, year)
        if movie_data:
            # Get detailed information
            detailed_data = self.api_client.get_tmdb_movie_details(movie_data['id'])
            if detailed_data:
                movie_data.update(detailed_data)
            
            media_type, confidence = self.classify_media_type(movie_data, 'movie')
            
            metadata = MediaMetadata(
                title=title,
                year=year,
                tmdb_id=movie_data['id'],
                tvdb_id=None,
                media_type=media_type,
                genres=[g['name'] for g in movie_data.get('genres', [])],
                overview=movie_data.get('overview', ''),
                runtime=movie_data.get('runtime'),
                status=movie_data.get('status', ''),
                original_language=movie_data.get('original_language', ''),
                popularity=movie_data.get('popularity', 0.0),
                vote_average=movie_data.get('vote_average', 0.0),
                api_source='tmdb',
                last_updated=datetime.now(),
                confidence=confidence
            )
            
            self.cache.store_metadata(metadata, movie_data)
            self.logger.info(f"✓ Enriched {title} as {media_type} (confidence: {confidence:.2f})")
            return metadata
        
        # Try TV search if movie search failed
        tv_data = self.api_client.search_tmdb_tv(clean_title, year)
        if tv_data:
            media_type, confidence = self.classify_media_type(tv_data, 'tv')
            
            metadata = MediaMetadata(
                title=title,
                year=year,
                tmdb_id=tv_data['id'],
                tvdb_id=None,
                media_type=media_type,
                genres=[g['name'] for g in tv_data.get('genres', [])],
                overview=tv_data.get('overview', ''),
                runtime=tv_data.get('episode_run_time', [None])[0] if tv_data.get('episode_run_time') else None,
                status=tv_data.get('status', ''),
                original_language=tv_data.get('original_language', ''),
                popularity=tv_data.get('popularity', 0.0),
                vote_average=tv_data.get('vote_average', 0.0),
                api_source='tmdb',
                last_updated=datetime.now(),
                confidence=confidence
            )
            
            self.cache.store_metadata(metadata, tv_data)
            self.logger.info(f"✓ Enriched {title} as {media_type} (confidence: {confidence:.2f})")
            return metadata
        
        self.logger.warning(f"✗ No metadata found for {title} ({year})")
        return None
    
    def enrich_database(self, limit: Optional[int] = None, skip_cached: bool = True) -> Dict:
        """Enrich all titles in the media database."""
        self.logger.info("Starting metadata enrichment process")
        
        database = self.load_media_database()
        if not database:
            return {'error': 'Failed to load media database'}
        
        stats = {
            'total_processed': 0,
            'successful_enrichments': 0,
            'cache_hits': 0,
            'failed_enrichments': 0,
            'skipped': 0,
            'movies_not_found': [],
            'tv_not_found': [],
            'movies_found': [],
            'tv_found': [],
            'classification_changes': []
        }
        
        # Process movies
        movies_dict = database.get('movies', {})
        movies = list(movies_dict.values())
        self.logger.info(f"Processing {len(movies)} movies")
        
        for i, movie in enumerate(movies):
            if limit and stats['total_processed'] >= limit:
                break
            
            # Get the filename to extract title and year
            filename = movie.get('file_name') or movie.get('title', '')
            if not filename:
                self.logger.warning(f"Skipping movie with no filename: {movie}")
                stats['failed_enrichments'] += 1
                stats['total_processed'] += 1
                continue
                
            title, year = self.extract_title_and_year(filename)
            
            if skip_cached and self.cache.get_metadata(title, year):
                stats['cache_hits'] += 1
                stats['skipped'] += 1
                continue
            
            try:
                metadata = self.enrich_title(title, year)
                if metadata:
                    stats['successful_enrichments'] += 1
                    
                    # Track found movies with details
                    movie_info = {
                        'title': title,
                        'year': year,
                        'filename': filename,
                        'file_path': movie.get('file_path', ''),
                        'original_category': 'movies',
                        'enriched_type': metadata.media_type,
                        'confidence': metadata.confidence,
                        'genres': metadata.genres,
                        'tmdb_id': metadata.tmdb_id
                    }
                    stats['movies_found'].append(movie_info)
                    
                    # Track classification changes
                    if metadata.media_type != 'movies':
                        change_info = {
                            'title': title,
                            'year': year,
                            'filename': filename,
                            'from': 'movies',
                            'to': metadata.media_type,
                            'confidence': metadata.confidence,
                            'reasoning': f"TMDB classification: {', '.join(metadata.genres)}"
                        }
                        stats['classification_changes'].append(change_info)
                        self.logger.info(f"🔄 Classification change: {title} ({year}) movies → {metadata.media_type} (confidence: {metadata.confidence:.2f})")
                else:
                    stats['failed_enrichments'] += 1
                    
                    # Track movies not found in TMDB
                    not_found_info = {
                        'title': title,
                        'year': year,
                        'filename': filename,
                        'file_path': movie.get('file_path', ''),
                        'original_category': 'movies'
                    }
                    stats['movies_not_found'].append(not_found_info)
                    self.logger.warning(f"❌ Not found in TMDB: {title} ({year})")
                
                stats['total_processed'] += 1
                
                # Progress update
                if (i + 1) % 10 == 0:
                    self.logger.info(f"📊 Progress: {i + 1}/{len(movies)} movies processed")
                
            except Exception as e:
                self.logger.error(f"Error enriching '{title}' ({year}): {e}")
                self.logger.debug(f"Movie data structure: {movie}")
                stats['failed_enrichments'] += 1
                stats['total_processed'] += 1
        
        # Process TV shows (sample a few episodes per show)
        tv_shows_dict = database.get('tv_shows', {})
        if tv_shows_dict:
            self.logger.info(f"Processing TV shows from {len(tv_shows_dict)} shows")
            
            # Process a sample of TV shows (take first episode from each show)
            tv_processed = 0
            for show_name, show_data in tv_shows_dict.items():
                if limit and stats['total_processed'] >= limit:
                    break
                
                # Get first episode to represent the show
                episodes = show_data.get('episodes', [])
                if episodes:
                    episode = episodes[0]
                    filename = episode.get('file_name') or episode.get('title', '')
                    if filename:
                        title, year = self.extract_title_and_year(show_name)
                        
                        if skip_cached and self.cache.get_metadata(title, year):
                            stats['cache_hits'] += 1
                            stats['skipped'] += 1
                            continue
                        
                        try:
                            metadata = self.enrich_title(title, year)
                            if metadata:
                                stats['successful_enrichments'] += 1
                                
                                # Track found TV shows
                                tv_info = {
                                    'title': title,
                                    'year': year,
                                    'show_name': show_name,
                                    'original_category': 'tv',
                                    'enriched_type': metadata.media_type,
                                    'confidence': metadata.confidence,
                                    'genres': metadata.genres,
                                    'tmdb_id': metadata.tmdb_id,
                                    'episode_count': len(episodes)
                                }
                                stats['tv_found'].append(tv_info)
                                
                                # Track classification changes for TV
                                if metadata.media_type != 'tv':
                                    change_info = {
                                        'title': title,
                                        'year': year,
                                        'show_name': show_name,
                                        'from': 'tv',
                                        'to': metadata.media_type,
                                        'confidence': metadata.confidence,
                                        'reasoning': f"TMDB classification: {', '.join(metadata.genres)}"
                                    }
                                    stats['classification_changes'].append(change_info)
                                    self.logger.info(f"🔄 TV Classification change: {title} ({year}) tv → {metadata.media_type} (confidence: {metadata.confidence:.2f})")
                            else:
                                stats['failed_enrichments'] += 1
                                
                                # Track TV shows not found
                                not_found_info = {
                                    'title': title,
                                    'year': year,
                                    'show_name': show_name,
                                    'original_category': 'tv',
                                    'episode_count': len(episodes)
                                }
                                stats['tv_not_found'].append(not_found_info)
                                self.logger.warning(f"❌ TV show not found in TMDB: {title} ({year})")
                            
                            stats['total_processed'] += 1
                            tv_processed += 1
                            
                            # Progress update for TV
                            if tv_processed % 5 == 0:
                                self.logger.info(f"📺 TV Progress: {tv_processed} shows processed")
                                
                        except Exception as e:
                            self.logger.error(f"Error enriching TV show '{title}' ({year}): {e}")
                            stats['failed_enrichments'] += 1
                            stats['total_processed'] += 1
        
        # Generate summary report
        self._generate_enrichment_summary(stats)
        
        # Save detailed results for reorganizer integration
        self._save_enrichment_results(stats)
        
        self.logger.info("Metadata enrichment completed")
        self.logger.info(f"Stats: {stats}")
        
        return stats
    
    def _generate_enrichment_summary(self, stats: Dict) -> None:
        """Generate comprehensive summary of enrichment results."""
        self.logger.info("=" * 80)
        self.logger.info("METADATA ENRICHMENT SUMMARY REPORT")
        self.logger.info("=" * 80)
        
        # Overall statistics
        self.logger.info(f"📊 OVERALL STATISTICS:")
        self.logger.info(f"   Total items processed: {stats['total_processed']}")
        self.logger.info(f"   Successful enrichments: {stats['successful_enrichments']}")
        self.logger.info(f"   Failed enrichments: {stats['failed_enrichments']}")
        self.logger.info(f"   Cache hits: {stats['cache_hits']}")
        self.logger.info(f"   Success rate: {(stats['successful_enrichments'] / max(stats['total_processed'], 1)) * 100:.1f}%")
        self.logger.info("")
        
        # Movies summary
        movies_found = len(stats['movies_found'])
        movies_not_found = len(stats['movies_not_found'])
        if movies_found > 0 or movies_not_found > 0:
            self.logger.info(f"🎬 MOVIES SUMMARY:")
            self.logger.info(f"   Found in TMDB: {movies_found}")
            self.logger.info(f"   Not found in TMDB: {movies_not_found}")
            if movies_found > 0:
                self.logger.info(f"   Movie success rate: {(movies_found / (movies_found + movies_not_found)) * 100:.1f}%")
            self.logger.info("")
        
        # TV shows summary
        tv_found = len(stats['tv_found'])
        tv_not_found = len(stats['tv_not_found'])
        if tv_found > 0 or tv_not_found > 0:
            self.logger.info(f"📺 TV SHOWS SUMMARY:")
            self.logger.info(f"   Found in TMDB: {tv_found}")
            self.logger.info(f"   Not found in TMDB: {tv_not_found}")
            if tv_found > 0:
                self.logger.info(f"   TV success rate: {(tv_found / (tv_found + tv_not_found)) * 100:.1f}%")
            self.logger.info("")
        
        # Classification changes
        if stats['classification_changes']:
            self.logger.info(f"🔄 CLASSIFICATION CHANGES ({len(stats['classification_changes'])}):")
            for change in stats['classification_changes'][:10]:  # Show first 10
                title = change.get('title', 'Unknown')
                year = change.get('year', '')
                from_type = change.get('from', '')
                to_type = change.get('to', '')
                confidence = change.get('confidence', 0)
                self.logger.info(f"   • {title} ({year}): {from_type} → {to_type} (confidence: {confidence:.2f})")
            
            if len(stats['classification_changes']) > 10:
                self.logger.info(f"   ... and {len(stats['classification_changes']) - 10} more changes")
            self.logger.info("")
        
        # Movies not found (critical for reorganizer)
        if stats['movies_not_found']:
            self.logger.info(f"❌ MOVIES NOT FOUND IN TMDB ({len(stats['movies_not_found'])}):")
            self.logger.info("   These movies may need manual review or alternative classification:")
            for movie in stats['movies_not_found'][:20]:  # Show first 20
                title = movie.get('title', 'Unknown')
                year = movie.get('year', '')
                filename = movie.get('filename', '')
                self.logger.info(f"   • {title} ({year}) - {filename}")
            
            if len(stats['movies_not_found']) > 20:
                self.logger.info(f"   ... and {len(stats['movies_not_found']) - 20} more movies")
            self.logger.info("")
        
        # TV shows not found
        if stats['tv_not_found']:
            self.logger.info(f"❌ TV SHOWS NOT FOUND IN TMDB ({len(stats['tv_not_found'])}):")
            self.logger.info("   These TV shows may need manual review:")
            for show in stats['tv_not_found'][:15]:  # Show first 15
                title = show.get('title', 'Unknown')
                year = show.get('year', '')
                episode_count = show.get('episode_count', 0)
                self.logger.info(f"   • {title} ({year}) - {episode_count} episodes")
            
            if len(stats['tv_not_found']) > 15:
                self.logger.info(f"   ... and {len(stats['tv_not_found']) - 15} more shows")
            self.logger.info("")
        
        # Recommendations for reorganizer integration
        self.logger.info(f"💡 REORGANIZER INTEGRATION RECOMMENDATIONS:")
        if stats['classification_changes']:
            self.logger.info(f"   • {len(stats['classification_changes'])} items have verified classification changes")
            self.logger.info(f"   • Use these for high-confidence reorganization moves")
        
        if stats['movies_not_found'] or stats['tv_not_found']:
            total_not_found = len(stats['movies_not_found']) + len(stats['tv_not_found'])
            self.logger.info(f"   • {total_not_found} items not found in TMDB - use rule-based classification")
        
        if stats['successful_enrichments'] > 0:
            self.logger.info(f"   • Cache now contains {stats['successful_enrichments']} new verified classifications")
            self.logger.info(f"   • Run reorganizer with cached metadata for improved accuracy")
        
        self.logger.info("=" * 80)
    
    def _save_enrichment_results(self, stats: Dict) -> None:
        """Save detailed enrichment results to JSON file for reorganizer integration."""
        try:
            # Create reports directory
            reports_dir = Path(__file__).parent.parent.parent.parent / 'reports'
            reports_dir.mkdir(exist_ok=True)
            
            # Generate timestamped filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            json_file = reports_dir / f"metadata_enrichment_{timestamp}.json"
            
            # Prepare data for JSON serialization
            json_data = {
                'enrichment_session': {
                    'timestamp': timestamp,
                    'session_date': datetime.now().isoformat(),
                    'total_processed': stats['total_processed'],
                    'successful_enrichments': stats['successful_enrichments'],
                    'failed_enrichments': stats['failed_enrichments'],
                    'cache_hits': stats['cache_hits']
                },
                'movies': {
                    'found_count': len(stats['movies_found']),
                    'not_found_count': len(stats['movies_not_found']),
                    'found_items': stats['movies_found'],
                    'not_found_items': stats['movies_not_found']
                },
                'tv_shows': {
                    'found_count': len(stats['tv_found']),
                    'not_found_count': len(stats['tv_not_found']),
                    'found_items': stats['tv_found'],
                    'not_found_items': stats['tv_not_found']
                },
                'classification_changes': stats['classification_changes'],
                'reorganizer_recommendations': {
                    'high_confidence_moves': [
                        change for change in stats['classification_changes'] 
                        if change.get('confidence', 0) >= 0.8
                    ],
                    'items_needing_manual_review': stats['movies_not_found'] + stats['tv_not_found'],
                    'verified_classifications_count': stats['successful_enrichments']
                }
            }
            
            # Save to JSON file
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"📄 Detailed results saved to: {json_file}")
            self.logger.info(f"   • Use this file for reorganizer integration")
            self.logger.info(f"   • Contains {len(stats['classification_changes'])} verified classification changes")
            
            # Also save a simplified summary for quick reference
            summary_file = reports_dir / f"enrichment_summary_{timestamp}.txt"
            with open(summary_file, 'w', encoding='utf-8') as f:
                f.write(f"Metadata Enrichment Summary - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("=" * 70 + "\n\n")
                
                f.write(f"PROCESSING RESULTS:\n")
                f.write(f"Total items processed: {stats['total_processed']}\n")
                f.write(f"Successful enrichments: {stats['successful_enrichments']}\n")
                f.write(f"Failed enrichments: {stats['failed_enrichments']}\n")
                f.write(f"Success rate: {(stats['successful_enrichments'] / max(stats['total_processed'], 1)) * 100:.1f}%\n\n")
                
                f.write(f"MOVIES:\n")
                f.write(f"Found in TMDB: {len(stats['movies_found'])}\n")
                f.write(f"Not found in TMDB: {len(stats['movies_not_found'])}\n\n")
                
                f.write(f"TV SHOWS:\n")
                f.write(f"Found in TMDB: {len(stats['tv_found'])}\n")
                f.write(f"Not found in TMDB: {len(stats['tv_not_found'])}\n\n")
                
                f.write(f"CLASSIFICATION CHANGES:\n")
                for change in stats['classification_changes']:
                    title = change.get('title', 'Unknown')
                    year = change.get('year', '')
                    from_type = change.get('from', '')
                    to_type = change.get('to', '')
                    confidence = change.get('confidence', 0)
                    f.write(f"• {title} ({year}): {from_type} → {to_type} (confidence: {confidence:.2f})\n")
            
            self.logger.info(f"📄 Summary saved to: {summary_file}")
            
        except Exception as e:
            self.logger.error(f"Failed to save enrichment results: {e}")


def main():
    """CLI interface for metadata enrichment."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Enrich media metadata using external APIs")
    parser.add_argument('--limit', type=int, help='Limit number of items to process')
    parser.add_argument('--force', action='store_true', help='Force re-enrichment of cached items')
    parser.add_argument('--stats', action='store_true', help='Show cache statistics')
    parser.add_argument('--test', type=str, help='Test enrichment for a specific title')
    
    args = parser.parse_args()
    
    enricher = MetadataEnricher()
    
    if args.stats:
        stats = enricher.cache.get_stats()
        print("\nMetadata Cache Statistics:")
        print(f"Total items: {stats['total_items']}")
        print("\nBy type:")
        for media_type, count in stats['by_type'].items():
            print(f"  {media_type}: {count}")
        print("\nBy source:")
        for source, count in stats['by_source'].items():
            print(f"  {source}: {count}")
        return
    
    if args.test:
        title, year = enricher.extract_title_and_year(args.test)
        print(f"Testing enrichment for: {title} ({year})")
        metadata = enricher.enrich_title(title, year)
        if metadata:
            print(f"Result: {metadata.media_type} (confidence: {metadata.confidence:.2f})")
            print(f"Genres: {metadata.genres}")
            print(f"Overview: {metadata.overview[:100]}...")
        else:
            print("No metadata found")
        return
    
    # Run enrichment
    results = enricher.enrich_database(
        limit=args.limit,
        skip_cached=not args.force
    )
    
    print(f"\nEnrichment completed!")
    print(f"Results: {results}")


if __name__ == "__main__":
    main()