"""External API integration for media metadata (TMDB, TVDB)."""

import os
import requests
import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import logging
from pathlib import Path

try:
    from dotenv import load_dotenv
    # Load .env file from project root
    env_path = Path(__file__).parent.parent.parent.parent / '.env'
    load_dotenv(env_path)
except ImportError:
    # python-dotenv not installed, continue without it
    pass

from ..config.config import config

logger = logging.getLogger(__name__)

@dataclass
class APIMediaResult:
    """Result from external API media search."""
    id: int
    title: str
    release_date: Optional[str]
    overview: Optional[str]
    poster_path: Optional[str]
    vote_average: Optional[float]
    media_type: str  # 'movie' or 'tv'

@dataclass
class APISeasonInfo:
    """Season information from external API."""
    season_number: int
    episode_count: int
    air_date: Optional[str]
    overview: Optional[str]

@dataclass
class APIShowDetails:
    """Detailed TV show information from external API."""
    id: int
    title: str
    total_seasons: int
    seasons: List[APISeasonInfo]
    status: str
    first_air_date: Optional[str]
    last_air_date: Optional[str]
    overview: Optional[str]

class ExternalAPIClient:
    """Client for external media APIs (TMDB, TVDB)."""
    
    def __init__(self, tmdb_api_key: Optional[str] = None, tvdb_api_key: Optional[str] = None):
        """
        Initialize API client.
        
        Args:
            tmdb_api_key: TMDB API key (optional, will try environment variable)
            tvdb_api_key: TVDB API key (optional, will try environment variable)
        """
        api_config = config.config.get('external_apis', {})
        
        # TMDB configuration
        self.tmdb_config = api_config.get('tmdb', {})
        self.tmdb_api_key = (
            tmdb_api_key or 
            os.getenv('TMDB_API_KEY') or 
            self.tmdb_config.get('api_key')
        )
        self.tmdb_base_url = self.tmdb_config.get('base_url', 'https://api.themoviedb.org/3')
        self.tmdb_delay = self.tmdb_config.get('rate_limit_delay', 0.25)
        self.tmdb_timeout = self.tmdb_config.get('timeout', 10)
        
        # TVDB configuration
        self.tvdb_config = api_config.get('tvdb', {})
        self.tvdb_api_key = (
            tvdb_api_key or 
            os.getenv('TVDB_API_KEY') or 
            self.tvdb_config.get('api_key')
        )
        self.tvdb_base_url = self.tvdb_config.get('base_url', 'https://api4.thetvdb.com/v4')
        self.tvdb_delay = self.tvdb_config.get('rate_limit_delay', 1.0)
        self.tvdb_timeout = self.tvdb_config.get('timeout', 10)
        self.tvdb_jwt_token = None
        self.tvdb_token_expiry = 0
        
        logger.info(f"TMDB API available: {bool(self.tmdb_api_key)}")
        logger.info(f"TVDB API available: {bool(self.tvdb_api_key)}")
    
    def search_movie(self, title: str, year: Optional[int] = None) -> List[APIMediaResult]:
        """
        Search for movies using external APIs.
        
        Args:
            title: Movie title to search for
            year: Optional year to filter results
            
        Returns:
            List of movie results
        """
        results = []
        
        # Try TMDB first
        if self.tmdb_api_key:
            try:
                tmdb_results = self._search_tmdb_movie(title, year)
                results.extend(tmdb_results)
            except Exception as e:
                logger.error(f"TMDB movie search failed: {e}")
        
        # If no results and TVDB is available, try it (though TVDB is primarily for TV)
        if not results and self.tvdb_api_key:
            logger.info("No TMDB results, TVDB doesn't handle movies well")
        
        return results[:10]  # Limit results
    
    def search_tv_show(self, title: str, year: Optional[int] = None) -> List[APIMediaResult]:
        """
        Search for TV shows using external APIs.
        
        Args:
            title: TV show title to search for
            year: Optional year to filter results
            
        Returns:
            List of TV show results
        """
        results = []
        
        # Try TMDB first
        if self.tmdb_api_key:
            try:
                tmdb_results = self._search_tmdb_tv(title, year)
                results.extend(tmdb_results)
            except Exception as e:
                logger.error(f"TMDB TV search failed: {e}")
        
        # Try TVDB if available
        if self.tvdb_api_key:
            try:
                tvdb_results = self._search_tvdb_tv(title, year)
                results.extend(tvdb_results)
            except Exception as e:
                logger.error(f"TVDB TV search failed: {e}")
        
        return results[:10]  # Limit results
    
    def get_tv_show_details(self, show_id: int, api_source: str = 'tmdb') -> Optional[APIShowDetails]:
        """
        Get detailed information about a TV show.
        
        Args:
            show_id: Show ID from the API
            api_source: Which API to use ('tmdb' or 'tvdb')
            
        Returns:
            Detailed show information or None if not found
        """
        if api_source == 'tmdb' and self.tmdb_api_key:
            return self._get_tmdb_tv_details(show_id)
        elif api_source == 'tvdb' and self.tvdb_api_key:
            return self._get_tvdb_tv_details(show_id)
        else:
            logger.error(f"API source '{api_source}' not available or configured")
            return None
    
    def _search_tmdb_movie(self, title: str, year: Optional[int] = None) -> List[APIMediaResult]:
        """Search TMDB for movies."""
        url = f"{self.tmdb_base_url}/search/movie"
        params = {
            'api_key': self.tmdb_api_key,
            'query': title,
            'language': self.tmdb_config.get('language', 'en-US')
        }
        
        if year:
            params['year'] = year
        
        response = requests.get(url, params=params, timeout=self.tmdb_timeout)
        time.sleep(self.tmdb_delay)
        
        if response.status_code != 200:
            raise Exception(f"TMDB API error: {response.status_code}")
        
        data = response.json()
        results = []
        
        for item in data.get('results', []):
            result = APIMediaResult(
                id=item['id'],
                title=item['title'],
                release_date=item.get('release_date'),
                overview=item.get('overview'),
                poster_path=item.get('poster_path'),
                vote_average=item.get('vote_average'),
                media_type='movie'
            )
            results.append(result)
        
        return results
    
    def _search_tmdb_tv(self, title: str, year: Optional[int] = None) -> List[APIMediaResult]:
        """Search TMDB for TV shows."""
        url = f"{self.tmdb_base_url}/search/tv"
        params = {
            'api_key': self.tmdb_api_key,
            'query': title,
            'language': self.tmdb_config.get('language', 'en-US')
        }
        
        if year:
            params['first_air_date_year'] = year
        
        response = requests.get(url, params=params, timeout=self.tmdb_timeout)
        time.sleep(self.tmdb_delay)
        
        if response.status_code != 200:
            raise Exception(f"TMDB API error: {response.status_code}")
        
        data = response.json()
        results = []
        
        for item in data.get('results', []):
            result = APIMediaResult(
                id=item['id'],
                title=item['name'],  # TV shows use 'name' instead of 'title'
                release_date=item.get('first_air_date'),
                overview=item.get('overview'),
                poster_path=item.get('poster_path'),
                vote_average=item.get('vote_average'),
                media_type='tv'
            )
            results.append(result)
        
        return results
    
    def _get_tvdb_jwt_token(self) -> Optional[str]:
        """Get JWT token for TVDB API authentication."""
        if not self.tvdb_api_key:
            return None
            
        # Check if we have a valid token
        current_time = time.time()
        if self.tvdb_jwt_token and current_time < self.tvdb_token_expiry:
            return self.tvdb_jwt_token
        
        # Get new token
        url = f"{self.tvdb_base_url}/login"
        data = {
            'apikey': self.tvdb_api_key
        }
        
        try:
            response = requests.post(url, json=data, timeout=self.tvdb_timeout)
            time.sleep(self.tvdb_delay)
            
            if response.status_code == 200:
                result = response.json()
                self.tvdb_jwt_token = result.get('data', {}).get('token')
                # TVDB tokens expire after 1 hour, set expiry for 50 minutes to be safe
                self.tvdb_token_expiry = current_time + (50 * 60)
                return self.tvdb_jwt_token
            else:
                logger.error(f"TVDB login failed: {response.status_code} - {response.text}")
                if response.status_code == 401:
                    logger.error("TVDB authentication failed - check if your TVDB_API_KEY is valid")
                return None
        except Exception as e:
            logger.error(f"TVDB login error: {e}")
            return None

    def _search_tvdb_tv(self, title: str, year: Optional[int] = None) -> List[APIMediaResult]:
        """Search TVDB for TV shows."""
        # Get JWT token for authentication
        jwt_token = self._get_tvdb_jwt_token()
        if not jwt_token:
            raise Exception("TVDB API error: Failed to authenticate")
        
        url = f"{self.tvdb_base_url}/search"
        params = {
            'query': title,
            'type': 'series'
        }
        
        headers = {
            'Authorization': f'Bearer {jwt_token}',
            'Content-Type': 'application/json'
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=self.tvdb_timeout)
        time.sleep(self.tvdb_delay)
        
        if response.status_code != 200:
            raise Exception(f"TVDB API error: {response.status_code}")
        
        data = response.json()
        results = []
        
        for item in data.get('data', []):
            # Filter by year if provided
            if year:
                first_aired = item.get('first_aired', '')
                if first_aired and not first_aired.startswith(str(year)):
                    continue
            
            result = APIMediaResult(
                id=item['tvdb_id'],
                title=item['name'],
                release_date=item.get('first_aired'),
                overview=item.get('overview'),
                poster_path=item.get('image_url'),
                vote_average=None,  # TVDB doesn't provide ratings in search
                media_type='tv'
            )
            results.append(result)
        
        return results
    
    def _get_tmdb_tv_details(self, show_id: int) -> Optional[APIShowDetails]:
        """Get detailed TV show information from TMDB."""
        url = f"{self.tmdb_base_url}/tv/{show_id}"
        params = {
            'api_key': self.tmdb_api_key,
            'language': self.tmdb_config.get('language', 'en-US')
        }
        
        response = requests.get(url, params=params, timeout=self.tmdb_timeout)
        time.sleep(self.tmdb_delay)
        
        if response.status_code != 200:
            return None
        
        data = response.json()
        
        # Get season information
        seasons = []
        for season_data in data.get('seasons', []):
            if season_data['season_number'] == 0:  # Skip specials
                continue
            
            season = APISeasonInfo(
                season_number=season_data['season_number'],
                episode_count=season_data['episode_count'],
                air_date=season_data.get('air_date'),
                overview=season_data.get('overview')
            )
            seasons.append(season)
        
        return APIShowDetails(
            id=data['id'],
            title=data['name'],
            total_seasons=len(seasons),
            seasons=seasons,
            status=data.get('status', 'Unknown'),
            first_air_date=data.get('first_air_date'),
            last_air_date=data.get('last_air_date'),
            overview=data.get('overview')
        )
    
    def _get_tvdb_tv_details(self, show_id: int) -> Optional[APIShowDetails]:
        """Get detailed TV show information from TVDB."""
        # Get JWT token for authentication
        jwt_token = self._get_tvdb_jwt_token()
        if not jwt_token:
            logger.error("Failed to get TVDB JWT token for details request")
            return None
        
        url = f"{self.tvdb_base_url}/series/{show_id}/extended"
        
        headers = {
            'Authorization': f'Bearer {jwt_token}',
            'Content-Type': 'application/json'
        }
        
        response = requests.get(url, headers=headers, timeout=self.tvdb_timeout)
        time.sleep(self.tvdb_delay)
        
        if response.status_code != 200:
            logger.error(f"TVDB series details failed: {response.status_code}")
            return None
        
        data = response.json().get('data', {})
        
        # TVDB provides seasons in the extended data
        seasons = []
        for season_data in data.get('seasons', []):
            if season_data.get('type', {}).get('name') == 'Official':
                season = APISeasonInfo(
                    season_number=season_data['number'],
                    episode_count=len(season_data.get('episodes', [])),
                    air_date=None,  # TVDB structure is different
                    overview=None
                )
                seasons.append(season)
        
        return APIShowDetails(
            id=data['id'],
            title=data['name'],
            total_seasons=len(seasons),
            seasons=seasons,
            status=data.get('status', {}).get('name', 'Unknown'),
            first_air_date=data.get('firstAired'),
            last_air_date=data.get('lastAired'),
            overview=data.get('overview')
        )
    
    def is_available(self) -> Dict[str, bool]:
        """Check which APIs are available."""
        return {
            'tmdb': bool(self.tmdb_api_key),
            'tvdb': bool(self.tvdb_api_key)
        }