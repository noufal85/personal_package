"""Episode analysis and missing episode detection."""

import requests
import time
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass
import logging

from .media_searcher import MediaSearcher
from .external_api import ExternalAPIClient

logger = logging.getLogger(__name__)

@dataclass
class EpisodeInfo:
    """Information about a TV episode."""
    season: int
    episode: int
    title: str
    air_date: Optional[str] = None
    overview: Optional[str] = None

@dataclass
class SeasonInfo:
    """Information about a TV season."""
    season_number: int
    episode_count: int
    episodes: List[EpisodeInfo]
    air_date: Optional[str] = None

@dataclass
class ShowInfo:
    """Information about a TV show from external API."""
    title: str
    tmdb_id: int
    total_seasons: int
    seasons: List[SeasonInfo]
    status: str
    first_air_date: Optional[str] = None
    last_air_date: Optional[str] = None

@dataclass
class MissingEpisodeReport:
    """Report of missing episodes for a show."""
    show_title: str
    found_locally: bool
    local_seasons: Set[int]
    api_seasons: Set[int]
    missing_seasons: Set[int]
    missing_episodes: Dict[int, List[int]]  # season -> list of missing episode numbers
    total_missing: int
    completeness_percent: float

class EpisodeAnalyzer:
    """Analyzes episodes and finds missing ones using external APIs."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize episode analyzer.
        
        Args:
            api_key: TMDB API key (optional, uses free tier if not provided)
        """
        self.media_searcher = MediaSearcher()
        self.api_client = ExternalAPIClient(tmdb_api_key=api_key)
    
    def analyze_missing_episodes(self, show_title: str, season: Optional[int] = None) -> MissingEpisodeReport:
        """
        Analyze missing episodes for a TV show.
        
        Args:
            show_title: Name of the TV show
            season: Specific season to analyze (None for all seasons)
            
        Returns:
            MissingEpisodeReport with analysis results
        """
        # Get local collection info
        local_info = self.media_searcher.get_tv_show_seasons(show_title)
        
        if not local_info['found']:
            return MissingEpisodeReport(
                show_title=show_title,
                found_locally=False,
                local_seasons=set(),
                api_seasons=set(),
                missing_seasons=set(),
                missing_episodes={},
                total_missing=0,
                completeness_percent=0.0
            )
        
        # Get API info
        try:
            api_results = self.api_client.search_tv_show(show_title)
            if not api_results:
                logger.warning(f"Could not find show '{show_title}' in external APIs")
                return self._create_local_only_report(local_info)
            
            # Use the first (most relevant) result
            best_match = api_results[0]
            api_details = self.api_client.get_tv_show_details(best_match.id, 'tmdb')
            
            if not api_details:
                logger.warning(f"Could not get details for show '{show_title}' from API")
                return self._create_local_only_report(local_info)
            
            return self._compare_local_vs_api(local_info, api_details, season)
            
        except Exception as e:
            logger.error(f"Error analyzing episodes for '{show_title}': {e}")
            return self._create_local_only_report(local_info)
    
    
    def _compare_local_vs_api(self, local_info: Dict[str, Any], api_info: Any, target_season: Optional[int]) -> MissingEpisodeReport:
        """Compare local collection with API data to find missing episodes."""
        local_seasons = set(local_info['seasons'].keys())
        api_seasons = {s.season_number for s in api_info.seasons}
        
        # Filter to target season if specified
        if target_season is not None:
            local_seasons = {s for s in local_seasons if s == target_season}
            api_seasons = {s for s in api_seasons if s == target_season}
        
        missing_seasons = api_seasons - local_seasons
        missing_episodes = {}
        total_episodes_expected = 0
        total_episodes_found = 0
        
        # Check each season
        for season_info in api_info.seasons:
            season_num = season_info.season_number
            
            if target_season is not None and season_num != target_season:
                continue
            
            expected_episodes = set(range(1, season_info.episode_count + 1))
            total_episodes_expected += len(expected_episodes)
            
            if season_num in local_seasons:
                # Get local episodes for this season
                local_episodes = set()
                for ep_info in local_info['seasons'][season_num]:
                    if ep_info['episode'] is not None:
                        local_episodes.add(ep_info['episode'])
                
                total_episodes_found += len(local_episodes)
                missing_in_season = expected_episodes - local_episodes
                
                if missing_in_season:
                    missing_episodes[season_num] = sorted(list(missing_in_season))
            else:
                # Entire season is missing
                missing_episodes[season_num] = sorted(list(expected_episodes))
        
        total_missing = sum(len(episodes) for episodes in missing_episodes.values())
        completeness_percent = (total_episodes_found / total_episodes_expected * 100) if total_episodes_expected > 0 else 0
        
        return MissingEpisodeReport(
            show_title=api_info.title,
            found_locally=True,
            local_seasons=local_seasons,
            api_seasons=api_seasons,
            missing_seasons=missing_seasons,
            missing_episodes=missing_episodes,
            total_missing=total_missing,
            completeness_percent=completeness_percent
        )
    
    def _create_local_only_report(self, local_info: Dict[str, Any]) -> MissingEpisodeReport:
        """Create a report with only local information (no API data)."""
        local_seasons = set(local_info['seasons'].keys())
        
        return MissingEpisodeReport(
            show_title=local_info['show_title'],
            found_locally=True,
            local_seasons=local_seasons,
            api_seasons=set(),
            missing_seasons=set(),
            missing_episodes={},
            total_missing=0,
            completeness_percent=100.0  # Assume complete if no API data
        )
    
    def get_show_completeness_summary(self, show_title: str) -> Dict[str, Any]:
        """Get a summary of show completeness."""
        report = self.analyze_missing_episodes(show_title)
        
        return {
            'show_title': report.show_title,
            'found_locally': report.found_locally,
            'total_seasons_local': len(report.local_seasons),
            'total_seasons_expected': len(report.api_seasons),
            'missing_seasons': len(report.missing_seasons),
            'total_missing_episodes': report.total_missing,
            'completeness_percent': report.completeness_percent,
            'status': self._get_completeness_status(report.completeness_percent)
        }
    
    def _get_completeness_status(self, percent: float) -> str:
        """Get a human-readable status based on completeness percentage."""
        if percent >= 100:
            return "Complete"
        elif percent >= 90:
            return "Nearly Complete"
        elif percent >= 75:
            return "Mostly Complete"
        elif percent >= 50:
            return "Partially Complete"
        elif percent > 0:
            return "Incomplete"
        else:
            return "Not Found"