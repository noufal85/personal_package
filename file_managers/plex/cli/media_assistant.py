"""AI-powered media search and analysis CLI."""

import argparse
import sys
import os
from typing import Dict, List, Any, Optional
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

from ..utils.ai_query_processor import AIQueryProcessor, QueryType, QueryIntent
from ..utils.media_searcher import MediaSearcher, SearchResult
from ..utils.episode_analyzer import EpisodeAnalyzer, MissingEpisodeReport
from ..utils.external_api import ExternalAPIClient
from ..utils.media_database import MediaDatabase

# Configure logging
logging.basicConfig(level=logging.WARNING, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

class MediaAssistant:
    """AI-powered media search and analysis assistant."""
    
    def __init__(self, tmdb_api_key: Optional[str] = None, verbose: bool = False, use_database: bool = True):
        """
        Initialize the media assistant.
        
        Args:
            tmdb_api_key: Optional TMDB API key
            verbose: Enable verbose output
            use_database: Whether to use cached database for faster searches
        """
        if verbose:
            logging.getLogger().setLevel(logging.INFO)
        
        self.query_processor = AIQueryProcessor()
        self.media_searcher = MediaSearcher(use_database=use_database)
        self.episode_analyzer = EpisodeAnalyzer(api_key=tmdb_api_key)
        self.api_client = ExternalAPIClient(tmdb_api_key=tmdb_api_key)
        
        # Check API availability and show status
        api_status = self.api_client.is_available()
        self._show_api_status(api_status, use_database)
    
    def _show_api_status(self, api_status: Dict[str, bool], use_database: bool = True) -> None:
        """Show API configuration status to user."""
        if not any(api_status.values()):
            print("⚠️  No external API keys configured. Some features may be limited.")
            print("   Configure API keys in .env file for full functionality:")
            print("   • TMDB_API_KEY for movie/TV metadata")
            print("   • TVDB_API_KEY for additional TV data")
            print("   • AWS credentials for enhanced AI processing")
        else:
            configured_apis = [name.upper() for name, available in api_status.items() if available]
            print(f"✅ External APIs configured: {', '.join(configured_apis)}")
        
        # Show database status
        if use_database:
            database = MediaDatabase()
            if database.is_current():
                stats = database.get_stats()
                print(f"💾 Database cache: {stats.movies_count} movies, {stats.tv_shows_count} TV shows")
            else:
                print("⚠️  Database cache is outdated. Use --rebuild-db to refresh.")
        else:
            print("🔍 Using filesystem search (database disabled)")
        print()
    
    def process_query(self, query: str) -> None:
        """
        Process a natural language query and provide results.
        
        Args:
            query: Natural language query from user
        """
        print(f"🔍 Processing: \"{query}\"")
        print()
        
        # Parse the query intent
        intent = self.query_processor.process_query(query)
        
        if intent.confidence < 0.5:
            print(f"⚠️  I'm not confident about understanding your query (confidence: {intent.confidence:.1%})")
            print(f"   Interpreted as: {intent.query_type.value} for '{intent.media_title}'")
            print()
        
        # Route to appropriate handler
        if intent.query_type == QueryType.SEARCH_MOVIE:
            self._handle_movie_search(intent)
        elif intent.query_type == QueryType.SEARCH_TV:
            self._handle_tv_search(intent)
        elif intent.query_type == QueryType.COUNT_MOVIES:
            self._handle_movie_count(intent)
        elif intent.query_type == QueryType.COUNT_SEASONS:
            self._handle_season_count(intent)
        elif intent.query_type == QueryType.MISSING_EPISODES:
            self._handle_missing_episodes(intent)
        else:
            self._handle_general_info(intent)
    
    def _handle_movie_search(self, intent: QueryIntent) -> None:
        """Handle movie search queries."""
        result = self.media_searcher.search_movies(intent.media_title)
        
        if not result.matches:
            print(f"❌ No movies found matching '{intent.media_title}'")
            
            # Try external API suggestion
            if self.api_client.is_available()['tmdb']:
                print("\n🌐 Searching external database...")
                api_results = self.api_client.search_movie(intent.media_title)
                if api_results:
                    print(f"   Found {len(api_results)} possible matches in TMDB:")
                    for i, movie in enumerate(api_results[:3], 1):
                        year = f" ({movie.release_date[:4]})" if movie.release_date else ""
                        print(f"   {i}. {movie.title}{year}")
            return
        
        print(f"🎬 Found {result.total_found} movie(s) matching '{intent.media_title}':")
        print()
        
        for i, match in enumerate(result.matches[:5], 1):  # Show top 5 matches
            year_str = f" ({match.year})" if match.year else ""
            size_str = self._format_file_size(match.file_size) if match.file_size else ""
            confidence_str = f" [{match.confidence:.1%} match]" if match.confidence < 0.95 else ""
            
            print(f"{i}. {match.title}{year_str}{confidence_str}")
            print(f"   📁 {match.path}")
            if size_str:
                print(f"   📊 {size_str}")
            print()
    
    def _handle_tv_search(self, intent: QueryIntent) -> None:
        """Handle TV show search queries."""
        result = self.media_searcher.search_tv_shows(intent.media_title)
        
        if not result.matches:
            print(f"❌ No TV shows found matching '{intent.media_title}'")
            
            # Try external API suggestion
            if self.api_client.is_available()['tmdb']:
                print("\n🌐 Searching external database...")
                api_results = self.api_client.search_tv_show(intent.media_title)
                if api_results:
                    print(f"   Found {len(api_results)} possible matches in TMDB:")
                    for i, show in enumerate(api_results[:3], 1):
                        year = f" ({show.release_date[:4]})" if show.release_date else ""
                        print(f"   {i}. {show.title}{year}")
            return
        
        # Get season summary
        season_info = self.media_searcher.get_tv_show_seasons(intent.media_title)
        
        print(f"📺 Found '{season_info['show_title']}'")
        print(f"   Seasons: {season_info['total_seasons']}")
        print(f"   Episodes: {season_info['total_episodes']}")
        print()
        
        # Show season breakdown
        if season_info['seasons']:
            print("📋 Season breakdown:")
            for season_num in sorted(season_info['seasons'].keys()):
                episodes = season_info['seasons'][season_num]
                episode_range = self._get_episode_range(episodes)
                print(f"   Season {season_num}: {len(episodes)} episodes {episode_range}")
            print()
        
        # Show some file paths
        print("📁 Sample files:")
        unique_paths = set()
        for match in result.matches[:3]:
            unique_paths.add(os.path.dirname(match.path))
        
        for path in list(unique_paths)[:3]:
            print(f"   {path}")
    
    def _handle_movie_count(self, intent: QueryIntent) -> None:
        """Handle movie counting queries."""
        result = self.media_searcher.search_movies(intent.media_title, fuzzy=True)
        
        if not result.matches:
            print(f"❌ No movies found matching '{intent.media_title}'")
            return
        
        # Filter for movies that contain the search term (for series)
        series_matches = []
        search_terms = intent.media_title.lower().split()
        
        for match in result.matches:
            title_words = match.title.lower().split()
            # Check if all search terms are in the movie title
            if all(term in ' '.join(title_words) for term in search_terms):
                series_matches.append(match)
        
        if not series_matches:
            series_matches = result.matches  # Fallback to all matches
        
        print(f"🎬 Found {len(series_matches)} movie(s) in the '{intent.media_title}' series:")
        print()
        
        # Sort by year if available, otherwise by title
        sorted_matches = sorted(series_matches, key=lambda x: (x.year or 0, x.title))
        
        for i, match in enumerate(sorted_matches, 1):
            year_str = f" ({match.year})" if match.year else ""
            size_str = self._format_file_size(match.file_size) if match.file_size else ""
            
            print(f"{i}. {match.title}{year_str}")
            print(f"   📁 {match.path}")
            if size_str:
                print(f"   📊 {size_str}")
            print()
        
        # Summary
        total_size = sum(match.file_size for match in series_matches if match.file_size)
        print(f"📊 Total: {len(series_matches)} movies")
        if total_size:
            print(f"   Combined size: {self._format_file_size(total_size)}")
    
    def _handle_season_count(self, intent: QueryIntent) -> None:
        """Handle season count queries."""
        season_info = self.media_searcher.get_tv_show_seasons(intent.media_title)
        
        if not season_info['found']:
            print(f"❌ TV show '{intent.media_title}' not found in your collection")
            return
        
        print(f"📺 {season_info['show_title']}")
        print(f"   You have {season_info['total_seasons']} season(s)")
        print(f"   Total episodes: {season_info['total_episodes']}")
        print()
        
        if season_info['seasons']:
            for season_num in sorted(season_info['seasons'].keys()):
                episodes = season_info['seasons'][season_num]
                episode_range = self._get_episode_range(episodes)
                print(f"   Season {season_num}: {len(episodes)} episodes {episode_range}")
    
    def _handle_missing_episodes(self, intent: QueryIntent) -> None:
        """Handle missing episode analysis."""
        target_season = intent.additional_params.get('season')
        
        print(f"🔍 Analyzing missing episodes for '{intent.media_title}'")
        if target_season:
            print(f"   Focusing on Season {target_season}")
        print()
        
        report = self.episode_analyzer.analyze_missing_episodes(intent.media_title, target_season)
        
        if not report.found_locally:
            print(f"❌ '{intent.media_title}' not found in your collection")
            return
        
        print(f"📺 {report.show_title}")
        print(f"   Completeness: {report.completeness_percent:.1f}%")
        
        if report.total_missing == 0:
            print("   ✅ Collection appears complete!")
        else:
            print(f"   ❌ Missing {report.total_missing} episode(s)")
            
            if report.missing_seasons:
                print(f"   Missing entire seasons: {sorted(report.missing_seasons)}")
            
            for season_num, missing_episodes in report.missing_episodes.items():
                if missing_episodes:
                    episodes_str = self._format_episode_list(missing_episodes)
                    print(f"   Season {season_num}: Missing episodes {episodes_str}")
        
        print()
        print(f"📊 Your collection: {len(report.local_seasons)} seasons")
        if report.api_seasons:
            print(f"   Expected total: {len(report.api_seasons)} seasons")
    
    def _handle_general_info(self, intent: QueryIntent) -> None:
        """Handle general information queries."""
        # Check if we should search both movie and TV
        if intent.additional_params.get('search_both'):
            self._search_both_types(intent.media_title)
        else:
            print(f"🤔 I'm not sure how to handle that query about '{intent.media_title}'")
            print("   Try asking something like:")
            print("   • Do I have the movie 'The Batman'?")
            print("   • How many seasons of 'Breaking Bad' do I have?")
            print("   • Am I missing any episodes for 'Game of Thrones'?")
    
    def _search_both_types(self, title: str) -> None:
        """Search both movies and TV shows for a title."""
        print(f"🔍 Searching for '{title}' in both movies and TV shows...")
        print()
        
        # Search movies
        movie_result = self.media_searcher.search_movies(title)
        tv_result = self.media_searcher.search_tv_shows(title)
        
        found_something = False
        
        # Show movie results if any
        if movie_result.matches:
            found_something = True
            print(f"🎬 Found {len(movie_result.matches)} movie(s):")
            for i, match in enumerate(movie_result.matches[:3], 1):
                year_str = f" ({match.year})" if match.year else ""
                confidence_str = f" [{match.confidence:.1%} match]" if match.confidence < 0.95 else ""
                print(f"   {i}. {match.title}{year_str}{confidence_str}")
                print(f"      📁 {match.path}")
            print()
        
        # Show TV results if any
        if tv_result.matches:
            found_something = True
            season_info = self.media_searcher.get_tv_show_seasons(title)
            if season_info['found']:
                print(f"📺 Found TV show: '{season_info['show_title']}'")
                print(f"   Seasons: {season_info['total_seasons']}")
                print(f"   Episodes: {season_info['total_episodes']}")
                print()
        
        if not found_something:
            print(f"❌ No movies or TV shows found matching '{title}'")
            
            # Try external API suggestion
            if self.api_client.is_available()['tmdb']:
                print("\n🌐 Searching external database...")
                movie_results = self.api_client.search_movie(title)
                tv_results = self.api_client.search_tv_show(title)
                
                if movie_results:
                    print(f"   Found {len(movie_results)} possible movies in TMDB:")
                    for i, movie in enumerate(movie_results[:2], 1):
                        year = f" ({movie.release_date[:4]})" if movie.release_date else ""
                        print(f"   🎬 {i}. {movie.title}{year}")
                
                if tv_results:
                    print(f"   Found {len(tv_results)} possible TV shows in TMDB:")
                    for i, show in enumerate(tv_results[:2], 1):
                        year = f" ({show.release_date[:4]})" if show.release_date else ""
                        print(f"   📺 {i}. {show.title}{year}")
    
    def _get_episode_range(self, episodes: List[Dict]) -> str:
        """Get a formatted episode range string."""
        episode_nums = [ep['episode'] for ep in episodes if ep['episode'] is not None]
        if not episode_nums:
            return ""
        
        episode_nums.sort()
        if len(episode_nums) == 1:
            return f"(E{episode_nums[0]})"
        elif episode_nums == list(range(episode_nums[0], episode_nums[-1] + 1)):
            return f"(E{episode_nums[0]}-E{episode_nums[-1]})"
        else:
            return f"(E{episode_nums[0]}...E{episode_nums[-1]}, {len(episode_nums)} total)"
    
    def _format_episode_list(self, episodes: List[int]) -> str:
        """Format a list of episode numbers for display."""
        if len(episodes) <= 5:
            return ", ".join(f"E{ep}" for ep in episodes)
        else:
            return f"E{episodes[0]}-E{episodes[-1]} ({len(episodes)} episodes)"
    
    def _format_file_size(self, size_bytes: int) -> str:
        """Format file size in human-readable format."""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} PB"

def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="AI-powered media search and analysis for your Plex collection",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s "Do I have the movie The Batman?"
  %(prog)s "How many seasons of Breaking Bad do I have?"
  %(prog)s "Am I missing episodes for Game of Thrones season 8?"
  %(prog)s --interactive

Environment Variables (or .env file):
  TMDB_API_KEY         - The Movie Database API key for enhanced features
  TVDB_API_KEY         - TV Database API key for additional TV metadata  
  AWS_ACCESS_KEY_ID    - AWS access key for Bedrock AI processing
  AWS_SECRET_ACCESS_KEY - AWS secret key for Bedrock AI processing
  BEDROCK_MODEL_ID     - Override default Bedrock model (optional)
        """
    )
    
    parser.add_argument(
        'query',
        nargs='?',
        help='Natural language query about your media collection'
    )
    
    parser.add_argument(
        '-i', '--interactive',
        action='store_true',
        help='Start interactive mode'
    )
    
    parser.add_argument(
        '--tmdb-key',
        help='TMDB API key (overrides environment variable)'
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose output'
    )
    
    parser.add_argument(
        '--rebuild-db',
        action='store_true',
        help='Rebuild the media database cache before starting'
    )
    
    parser.add_argument(
        '--no-db',
        action='store_true',
        help='Disable database caching (use filesystem search only)'
    )
    
    args = parser.parse_args()
    
    # Handle database rebuild
    if args.rebuild_db:
        print("🔄 Rebuilding media database...")
        database = MediaDatabase()
        stats = database.rebuild_database()
        
        print(f"✅ Database rebuilt successfully!")
        print(f"   📊 Movies: {stats.movies_count}")
        print(f"   📺 TV Shows: {stats.tv_shows_count}")
        print(f"   🎬 Episodes: {stats.tv_episodes_count}")
        print(f"   ⏱️  Build time: {stats.build_time_seconds}s")
        print(f"   💾 Total size: {stats.total_size_bytes / (1024**3):.1f} GB")
        print()
        
        if not args.query and not args.interactive:
            return  # Exit after rebuild if no other action requested
    
    if not args.query and not args.interactive and not args.rebuild_db:
        parser.print_help()
        return
    
    # Initialize assistant
    assistant = MediaAssistant(
        tmdb_api_key=args.tmdb_key,
        verbose=args.verbose,
        use_database=not args.no_db
    )
    
    if args.interactive:
        # Interactive mode
        print("🎬 Plex Media Assistant - Interactive Mode")
        print("Ask questions about your media collection in natural language.")
        print("Examples:")
        print("  • Do I have the movie 'Inception'?")
        print("  • How many seasons of 'The Office' do I have?")
        print("  • Am I missing episodes for 'Breaking Bad'?")
        print()
        print("Type 'quit' or 'exit' to leave.")
        print()
        
        while True:
            try:
                query = input("❓ Your question: ").strip()
                if query.lower() in ['quit', 'exit', 'q']:
                    print("Goodbye! 👋")
                    break
                
                if query:
                    print()
                    assistant.process_query(query)
                    print()
            except KeyboardInterrupt:
                print("\nGoodbye! 👋")
                break
            except EOFError:
                break
    else:
        # Single query mode
        assistant.process_query(args.query)

if __name__ == '__main__':
    main()