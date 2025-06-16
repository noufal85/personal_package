"""AI-powered query processor for natural language media search requests."""

import boto3
import json
import re
import os
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
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

class QueryType(Enum):
    """Types of media queries that can be processed."""
    SEARCH_MOVIE = "search_movie"
    SEARCH_TV = "search_tv"
    COUNT_MOVIES = "count_movies"
    COUNT_SEASONS = "count_seasons"
    MISSING_EPISODES = "missing_episodes"
    GENERAL_INFO = "general_info"

@dataclass
class QueryIntent:
    """Represents the parsed intent from a natural language query."""
    query_type: QueryType
    media_title: str
    additional_params: Dict[str, Any]
    confidence: float

class AIQueryProcessor:
    """Processes natural language queries about media collections using AI."""
    
    def __init__(self):
        """Initialize the AI query processor with Bedrock configuration."""
        self.bedrock_client = None
        self._initialize_bedrock()
    
    def _initialize_bedrock(self) -> None:
        """Initialize AWS Bedrock client."""
        try:
            # Use AWS credentials from environment if available
            bedrock_kwargs = {
                'service_name': 'bedrock-runtime',
                'region_name': os.getenv('AWS_DEFAULT_REGION', config.bedrock_region)
            }
            
            # Add credentials if provided in environment
            if os.getenv('AWS_ACCESS_KEY_ID') and os.getenv('AWS_SECRET_ACCESS_KEY'):
                bedrock_kwargs.update({
                    'aws_access_key_id': os.getenv('AWS_ACCESS_KEY_ID'),
                    'aws_secret_access_key': os.getenv('AWS_SECRET_ACCESS_KEY')
                })
            
            self.bedrock_client = boto3.client(**bedrock_kwargs)
            
            # Allow model override from environment
            self.model_id = os.getenv('BEDROCK_MODEL_ID', config.bedrock_model_id)
            self.max_tokens = config.bedrock_max_tokens
            self.temperature = config.bedrock_temperature
            
            logger.info(f"Bedrock initialized with model: {self.model_id}")
        except Exception as e:
            logger.warning(f"Failed to initialize Bedrock client: {e}")
            self.bedrock_client = None
    
    def process_query(self, user_query: str) -> QueryIntent:
        """
        Process a natural language query and extract intent.
        
        Args:
            user_query: Natural language query from user
            
        Returns:
            QueryIntent object with parsed information
        """
        if self.bedrock_client:
            return self._process_with_ai(user_query)
        else:
            return self._process_with_patterns(user_query)
    
    def _process_with_ai(self, user_query: str) -> QueryIntent:
        """Process query using AI (Bedrock)."""
        prompt = self._build_query_analysis_prompt(user_query)
        
        try:
            response = self.bedrock_client.invoke_model(
                modelId=self.model_id,
                body=json.dumps({
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": self.max_tokens,
                    "temperature": self.temperature,
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ]
                })
            )
            
            response_body = json.loads(response['body'].read())
            ai_response = response_body['content'][0]['text']
            
            return self._parse_ai_response(ai_response)
            
        except Exception as e:
            logger.error(f"AI processing failed: {e}")
            return self._process_with_patterns(user_query)
    
    def _build_query_analysis_prompt(self, user_query: str) -> str:
        """Build prompt for AI query analysis."""
        return f"""
Analyze this natural language query about a media collection and extract the intent:

Query: "{user_query}"

Important guidelines:
- If the query explicitly mentions "movie" or "film", use search_movie
- If the query explicitly mentions "TV", "show", "series", "season", or "episode", use search_tv
- For ambiguous queries, consider these patterns:
  * Names ending in "bot", "diaries", "chronicles" are usually TV shows
  * Single names like "Batman", "Spider-man" could be either - use general_info with search_both: true
  * Franchises like "John Wick", "Fast & Furious" are usually movies
  * Titles with "The [Name] Diaries" or "[Name] Chronicles" are usually TV shows

Determine:
1. Query Type (one of: search_movie, search_tv, count_movies, count_seasons, missing_episodes, general_info)
2. Media Title (extract the movie/TV show name)
3. Additional Parameters (any specific details like season numbers, episode ranges, etc.)
4. Confidence (0.0-1.0 for how confident you are in the analysis)

Respond in JSON format:
{{
    "query_type": "search_movie|search_tv|count_movies|count_seasons|missing_episodes|general_info",
    "media_title": "extracted title",
    "additional_params": {{}},
    "confidence": 0.0-1.0
}}

Examples:
- "Do I have the movie The Batman?" → {{"query_type": "search_movie", "media_title": "The Batman", "additional_params": {{}}, "confidence": 0.95}}
- "Do I have murder bot?" → {{"query_type": "search_tv", "media_title": "Murder Bot", "additional_params": {{}}, "confidence": 0.8}}
- "Do I have Batman?" → {{"query_type": "general_info", "media_title": "Batman", "additional_params": {{"search_both": true}}, "confidence": 0.7}}
- "How many John Wick movies do I have?" → {{"query_type": "count_movies", "media_title": "John Wick", "additional_params": {{}}, "confidence": 0.95}}
- "How many seasons of Sugar do I have?" → {{"query_type": "count_seasons", "media_title": "Sugar", "additional_params": {{}}, "confidence": 0.9}}
- "Am I missing episodes for Breaking Bad season 3?" → {{"query_type": "missing_episodes", "media_title": "Breaking Bad", "additional_params": {{"season": 3}}, "confidence": 0.85}}
"""
    
    def _parse_ai_response(self, ai_response: str) -> QueryIntent:
        """Parse AI response into QueryIntent."""
        try:
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                return QueryIntent(
                    query_type=QueryType(data['query_type']),
                    media_title=data['media_title'],
                    additional_params=data.get('additional_params', {}),
                    confidence=data.get('confidence', 0.5)
                )
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.error(f"Failed to parse AI response: {e}")
        
        # Fallback to pattern matching
        return self._process_with_patterns(ai_response)
    
    def _process_with_patterns(self, user_query: str) -> QueryIntent:
        """Fallback pattern-based query processing."""
        query_lower = user_query.lower()
        
        # Pattern matching for different query types
        if any(phrase in query_lower for phrase in ['do i have', 'have i got', 'is there']):
            if 'movie' in query_lower:
                return self._extract_movie_search(user_query)
            elif 'tv' in query_lower or 'show' in query_lower or 'series' in query_lower:
                return self._extract_tv_search(user_query)
            else:
                # Use AI/heuristics to determine if it's likely a TV show or movie
                return self._determine_media_type_and_search(user_query)
        
        elif any(phrase in query_lower for phrase in ['how many seasons', 'seasons do i have', 'seasons of']):
            return self._extract_season_count(user_query)
        
        elif any(phrase in query_lower for phrase in ['how many', 'count']) and any(phrase in query_lower for phrase in ['movie', 'film']):
            return self._extract_movie_count(user_query)
        
        elif any(phrase in query_lower for phrase in ['missing episodes', 'missing from', 'incomplete']):
            return self._extract_missing_episodes(user_query)
        
        else:
            # General search - try to determine if movie or TV
            if 'movie' in query_lower or self._looks_like_movie_query(query_lower):
                return self._extract_movie_search(user_query)
            else:
                return self._extract_tv_search(user_query)
    
    def _looks_like_movie_query(self, query: str) -> bool:
        """Heuristic to determine if query is about a movie."""
        movie_indicators = [
            'film', 'movie', 'cinema', 
            # Common movie franchises
            'batman', 'spider-man', 'avengers', 'john wick', 'mission impossible',
            'fast furious', 'jurassic', 'star wars', 'lord of the rings'
        ]
        return any(indicator in query for indicator in movie_indicators)
    
    def _looks_like_tv_query(self, query: str) -> bool:
        """Heuristic to determine if query is about a TV show."""
        tv_indicators = [
            'series', 'show', 'season', 'episode', 'episodes',
            # Common TV show patterns
            'bot', 'diaries', 'chronicles', 'adventures of',
            # Known TV genres/formats
            'mystery', 'detective', 'drama series', 'comedy series'
        ]
        return any(indicator in query for indicator in tv_indicators)
    
    def _determine_media_type_and_search(self, user_query: str) -> QueryIntent:
        """Determine if query is about TV or movie using heuristics and title matching."""
        title = self._extract_title_from_quotes(user_query)
        if not title:
            title = self._extract_title_pattern_based(user_query)
        
        # Use heuristics first
        if self._looks_like_tv_query(user_query.lower()):
            return self._extract_tv_search(user_query)
        elif self._looks_like_movie_query(user_query.lower()):
            return self._extract_movie_search(user_query)
        
        # For ambiguous cases, search both and return the better match
        # This will be handled by the media assistant to search both types
        return QueryIntent(
            query_type=QueryType.GENERAL_INFO,
            media_title=title,
            additional_params={'search_both': True},
            confidence=0.6
        )
    
    def _extract_movie_search(self, query: str) -> QueryIntent:
        """Extract movie title from search query."""
        title = self._extract_title_from_quotes(query)
        if not title:
            title = self._extract_title_pattern_based(query)
        
        return QueryIntent(
            query_type=QueryType.SEARCH_MOVIE,
            media_title=title,
            additional_params={},
            confidence=0.7
        )
    
    def _extract_tv_search(self, query: str) -> QueryIntent:
        """Extract TV show title from search query."""
        title = self._extract_title_from_quotes(query)
        if not title:
            title = self._extract_title_pattern_based(query)
        
        return QueryIntent(
            query_type=QueryType.SEARCH_TV,
            media_title=title,
            additional_params={},
            confidence=0.7
        )
    
    def _extract_season_count(self, query: str) -> QueryIntent:
        """Extract TV show for season counting."""
        title = self._extract_title_from_quotes(query)
        if not title:
            # Look for pattern like "seasons of [title]"
            match = re.search(r'seasons of (.+?)(?:\?|$)', query, re.IGNORECASE)
            if match:
                title = match.group(1).strip()
        
        return QueryIntent(
            query_type=QueryType.COUNT_SEASONS,
            media_title=title or "unknown",
            additional_params={},
            confidence=0.8
        )
    
    def _extract_movie_count(self, query: str) -> QueryIntent:
        """Extract movie series for counting."""
        title = self._extract_title_from_quotes(query)
        if not title:
            # Look for patterns like "how many [title] movies"
            patterns = [
                r'how many (.+?) movies',
                r'count (.+?) movies',
                r'how many (.+?) films'
            ]
            for pattern in patterns:
                match = re.search(pattern, query, re.IGNORECASE)
                if match:
                    title = match.group(1).strip()
                    break
        
        return QueryIntent(
            query_type=QueryType.COUNT_MOVIES,
            media_title=title or "unknown", 
            additional_params={},
            confidence=0.8
        )
    
    def _extract_missing_episodes(self, query: str) -> QueryIntent:
        """Extract TV show and season for missing episode check."""
        title = self._extract_title_from_quotes(query)
        additional_params = {}
        
        # Look for season number
        season_match = re.search(r'season (\d+)', query, re.IGNORECASE)
        if season_match:
            additional_params['season'] = int(season_match.group(1))
        
        if not title:
            # Try to extract from patterns like "missing episodes for [title]"
            match = re.search(r'(?:missing episodes for|episodes for) (.+?)(?:\s+season|\?|$)', query, re.IGNORECASE)
            if match:
                title = match.group(1).strip()
        
        return QueryIntent(
            query_type=QueryType.MISSING_EPISODES,
            media_title=title or "unknown",
            additional_params=additional_params,
            confidence=0.7
        )
    
    def _extract_title_from_quotes(self, query: str) -> Optional[str]:
        """Extract title from quotes in the query."""
        quote_patterns = [
            r"'([^']+)'",  # Single quotes
            r'"([^"]+)"',  # Double quotes
        ]
        
        for pattern in quote_patterns:
            match = re.search(pattern, query)
            if match:
                return match.group(1).strip()
        
        return None
    
    def _extract_title_pattern_based(self, query: str) -> str:
        """Extract title using pattern-based heuristics."""
        # Remove common query words
        stop_words = ['do', 'i', 'have', 'the', 'movie', 'tv', 'show', 'series', 'how', 'many', 'seasons', 'of']
        words = query.split()
        
        # Find the longest sequence of capitalized words or words after "the"
        title_words = []
        for word in words:
            clean_word = re.sub(r'[^\w\s]', '', word)
            if clean_word.lower() not in stop_words and len(clean_word) > 1:
                title_words.append(word)
        
        return ' '.join(title_words).strip() if title_words else "unknown"