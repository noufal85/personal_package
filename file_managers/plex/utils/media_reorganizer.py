"""
Media reorganization analysis tool - MVP implementation.

This module identifies misplaced media files across Plex directories using
rule-based classification and generates actionable reports.
"""

import os
import json
import logging
import time
from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from datetime import datetime

from ..config.config import config
from .external_api import ExternalAPIClient


@dataclass
class MediaFile:
    """Represents a media file with metadata."""
    path: Path
    name: str
    size: int
    category: str  # Current location category


@dataclass
class MisplacedFile:
    """Represents a file that appears to be in the wrong category."""
    file: MediaFile
    current_category: str
    suggested_category: str
    suggested_path: str
    confidence: float
    reasoning: str
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "source_path": str(self.file.path),
            "current_category": self.current_category,
            "suggested_category": self.suggested_category,
            "suggested_path": self.suggested_path,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
            "file_size": self.file.size,
            "file_size_readable": self._format_file_size(self.file.size)
        }
    
    def _format_file_size(self, size_bytes: int) -> str:
        """Format file size in human-readable format."""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} PB"


class MediaReorganizationAnalyzer:
    """
    Media reorganization analysis tool.
    
    Analyzes media directories to identify misplaced files and generates
    reports with reorganization recommendations.
    """
    
    def __init__(self, rebuild_db: bool = False, min_confidence: float = 0.7, output_format: str = 'both', use_ai: bool = False, use_external_apis: bool = True, limit_files: Optional[int] = None):
        """Initialize the analyzer."""
        self.config = config
        self.min_confidence = min_confidence
        self.output_format = output_format
        self.use_ai = use_ai
        self.use_external_apis = use_external_apis
        self.rebuild_db = rebuild_db
        self.limit_files = limit_files
        self.misplaced_files: List[MisplacedFile] = []
        self.all_files: List[MediaFile] = []
        self.database_path = Path(__file__).parent.parent.parent.parent / 'database' / 'media_database.json'
        self.media_database = None
        
        # Initialize logging
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.logger = self._setup_logging()
        
        # Performance tracking
        self.start_time = time.time()
        self.classification_stats = {
            'cache_hits': 0,
            'ai_calls': 0,
            'ai_success': 0,
            'tv_pattern_detection': 0,
            'unclassified': 0,
            'ai_time': 0.0
        }
        
        # Video file extensions to consider
        self.video_extensions = {'.mkv', '.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm', '.m4v'}
        
        # Log initialization
        self.logger.info("="*60)
        self.logger.info(f"Media Reorganization Analysis Session Started: {self.session_id}")
        self.logger.info(f"Configuration: AI={use_ai}, External_APIs={use_external_apis}, Rebuild_DB={rebuild_db}")
        self.logger.info(f"Confidence_Threshold={min_confidence}, Output_Format={output_format}")
        
        # Initialize AI classifier if needed
        self.ai_classifier = None
        if self.use_ai:
            try:
                from .openai_classifier import OpenAIClassifier
                self.ai_classifier = OpenAIClassifier()
                print("✅ OpenAI classifier initialized successfully")
                self.logger.info("OpenAI classifier initialized successfully")
            except ImportError as e:
                print(f"⚠️  OpenAI classifier not available: {e}")
                print("   Falling back to rule-based classification only")
                self.logger.warning(f"OpenAI classifier not available: {e}")
                self.use_ai = False
        
        # Initialize external API client
        self.api_client = None
        if self.use_external_apis:
            try:
                self.api_client = ExternalAPIClient()
                print("✅ External API client initialized")
                self.logger.info("External API client initialized successfully")
            except Exception as e:
                print(f"⚠️  External APIs not available: {e}")
                self.logger.warning(f"External APIs not available: {e}")
                self.use_external_apis = False
    
    def _setup_logging(self) -> logging.Logger:
        """Set up comprehensive logging for the analysis session."""
        # Create logs directory
        logs_dir = Path("logs")
        logs_dir.mkdir(exist_ok=True)
        
        # Create logger
        logger = logging.getLogger(f"media_reorganizer_{self.session_id}")
        logger.setLevel(logging.DEBUG)
        
        # Remove existing handlers to avoid duplication
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
        
        # Create file handler for detailed logs
        log_file = logs_dir / f"media_reorganizer_{self.session_id}.log"
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        
        # Create console handler for important messages
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Create formatters
        detailed_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(funcName)-20s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_formatter = logging.Formatter(
            '%(levelname)-8s | %(message)s'
        )
        
        # Apply formatters
        file_handler.setFormatter(detailed_formatter)
        console_handler.setFormatter(console_formatter)
        
        # Add handlers
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        return logger
    
    def _log_classification_stats(self) -> None:
        """Log detailed classification statistics."""
        stats = self.classification_stats
        total_calls = stats['cache_hits'] + stats['ai_calls'] + stats['tv_pattern_detection'] + stats['unclassified']
        
        self.logger.info("="*40)
        self.logger.info("CLASSIFICATION STATISTICS")
        self.logger.info("="*40)
        self.logger.info(f"Total Classifications: {total_calls}")
        self.logger.info(f"Database Cache Hits: {stats['cache_hits']}")
        self.logger.info(f"TV Pattern Detection: {stats['tv_pattern_detection']}")
        self.logger.info(f"AI Classifications: {stats['ai_calls']} (Success: {stats['ai_success']})")
        self.logger.info(f"Unclassified: {stats['unclassified']}")
        
        if stats['ai_calls'] > 0:
            ai_success_rate = (stats['ai_success'] / stats['ai_calls']) * 100
            avg_ai_time = stats['ai_time'] / stats['ai_calls']
            self.logger.info(f"AI Success Rate: {ai_success_rate:.1f}%")
            self.logger.info(f"Average AI Time: {avg_ai_time:.3f}s per file")
        
        if stats['tv_pattern_detection'] > 0:
            self.logger.info(f"TV Pattern Detection: {stats['tv_pattern_detection']} episodes classified by pattern matching")
        
        self.logger.info("="*40)
        
    def run_analysis(self, args) -> int:
        """Main analysis workflow."""
        try:
            print("🔍 Media Reorganization Analysis")
            print("=" * 35)
            print("• Process: TV/Movie Database Cache → AI LLM → Unclassified")
            print(f"• Database rebuild: {'Yes' if self.rebuild_db else 'No'}")
            print("• Analysis only - generates actionable reports for moves")
            print()
            
            self.logger.info("Starting strict workflow: TV/Movie DB Cache → AI LLM → Unclassified")
            
            # Step 1: Load or rebuild database
            print("📂 Loading media database...")
            database_start = time.time()
            if not self._load_media_database():
                self.logger.error("Database loading failed")
                return 1
            database_time = time.time() - database_start
            self.logger.info(f"Database loaded in {database_time:.2f} seconds: {len(self.all_files):,} files")
            
            if not self.all_files:
                print("❌ No media files found to analyze")
                return 0
                
            print(f"📊 Database loaded: {len(self.all_files):,} media files")
            print()
            
            # Step 2: Analyze placements
            print("🔍 Analyzing file placements...")
            analysis_start = time.time()
            self.logger.info("Starting file placement analysis")
            self.misplaced_files = self._analyze_file_placements()
            analysis_time = time.time() - analysis_start
            
            self.logger.info(f"Analysis completed in {analysis_time:.2f} seconds: {len(self.misplaced_files)} misplaced files")
            self._log_classification_stats()
            
            if not self.misplaced_files:
                print("✅ No misplaced files detected!")
                self.logger.info("No misplaced files detected")
                return 0
                
            print(f"⚠️  Found {len(self.misplaced_files)} potentially misplaced files")
            print()
            
            # Step 3: Generate reports
            print("📝 Generating analysis reports...")
            report_start = time.time()
            report_paths = self._generate_reports()
            report_time = time.time() - report_start
            self.logger.info(f"Reports generated in {report_time:.2f} seconds")
            
            print(f"✅ Analysis complete!")
            for report_type, path in report_paths.items():
                if path:
                    print(f"📄 {report_type.title()} report: {path}")
                    self.logger.info(f"{report_type.title()} report saved to: {path}")
            print()
            
            # Step 4: Show summary
            self._show_summary()
            
            total_time = time.time() - self.start_time
            self.logger.info(f"Total analysis time: {total_time:.2f} seconds")
            self.logger.info("Analysis session completed successfully")
            
            # Print log file path
            log_file_path = Path("logs") / f"media_reorganizer_{self.session_id}.log"
            print(f"\n📄 Full session log: {log_file_path.absolute()}")
            self.logger.info(f"Session log file: {log_file_path.absolute()}")
            
            return 0
            
        except Exception as e:
            print(f"❌ Analysis failed: {e}")
            self.logger.error(f"Analysis failed: {e}", exc_info=True)
            return 1
    
    def _load_media_database(self) -> bool:
        """Load media files from the existing database."""
        try:
            if self.rebuild_db:
                print("   🔄 Database rebuild requested - delegating to media scanner...")
                print("   Please run: python -m file_managers.plex.cli.media_database_cli --rebuild")
                return False
            
            if not self.database_path.exists():
                print(f"   ❌ Database not found at {self.database_path}")
                print("   Please run: python -m file_managers.plex.cli.media_database_cli --rebuild")
                return False
                
            with open(self.database_path, 'r', encoding='utf-8') as f:
                self.media_database = json.load(f)
                
            # Convert database entries to MediaFile objects
            self.all_files = []
            
            # Load movies
            if 'movies' in self.media_database:
                movie_count = 0
                for movie_key, movie_data in self.media_database['movies'].items():
                    if self.limit_files and len(self.all_files) >= self.limit_files:
                        break
                    file_path = Path(movie_data['file_path'])
                    self.all_files.append(MediaFile(
                        path=file_path,
                        name=movie_data['file_name'],
                        size=movie_data['file_size'],
                        category="movies"
                    ))
                    movie_count += 1
                print(f"   📽️  Loaded {movie_count} movies")
                self.logger.info(f"Loaded {movie_count} movies from database")
            
            # Load TV episodes (only if not at limit)
            if 'tv_shows' in self.media_database and (not self.limit_files or len(self.all_files) < self.limit_files):
                total_episodes = 0
                show_count = len(self.media_database['tv_shows'])
                for show_key, show_data in self.media_database['tv_shows'].items():
                    if self.limit_files and len(self.all_files) >= self.limit_files:
                        break
                    episode_count = len(show_data.get('episodes', []))
                    self.logger.debug(f"Loading {episode_count} episodes for show: {show_key}")
                    for episode in show_data.get('episodes', []):
                        if self.limit_files and len(self.all_files) >= self.limit_files:
                            break
                        file_path = Path(episode['file_path'])
                        self.all_files.append(MediaFile(
                            path=file_path,
                            name=episode['file_name'],
                            size=episode['file_size'],
                            category="tv"
                        ))
                        total_episodes += 1
                print(f"   📺 Loaded {total_episodes} TV episodes from {show_count} shows")
                self.logger.info(f"Loaded {total_episodes} TV episodes from {show_count} shows")
            
            # Log if limit was applied
            if self.limit_files:
                print(f"   ⚠️  Applied file limit: {len(self.all_files)}/{self.limit_files} files loaded for testing")
                self.logger.info(f"File limit applied: {len(self.all_files)}/{self.limit_files} files loaded")
            
            return True
            
        except Exception as e:
            print(f"   ❌ Failed to load database: {e}")
            return False
    
    def _scan_directory(self, directory: str, category: str) -> List[MediaFile]:
        """Scan a single directory for media files."""
        files = []
        directory_path = Path(directory)
        
        try:
            for file_path in directory_path.rglob("*"):
                if (file_path.is_file() and 
                    file_path.suffix.lower() in self.video_extensions):
                    
                    try:
                        size = file_path.stat().st_size
                        files.append(MediaFile(
                            path=file_path,
                            name=file_path.name,
                            size=size,
                            category=category
                        ))
                    except (OSError, IOError):
                        # Skip files we can't access
                        continue
                        
        except (OSError, IOError) as e:
            print(f"⚠️  Warning: Could not access {directory}: {e}")
            
        return files
    
    def _analyze_file_placements(self) -> List[MisplacedFile]:
        """Analyze files using unified workflow: metadata cache → AI → rule-based fallback."""
        print("🔍 Starting strict classification workflow...")
        print("   Process: TV/Movie Database Cache → AI LLM → Unclassified")
        print(f"   Processing {len(self.all_files)} files...")
        
        return self._analyze_with_unified_workflow()
    
    def _analyze_with_rules(self) -> List[MisplacedFile]:
        """Analyze files using rule-based classification only."""
        misplaced = []
        
        print(f"   Processing {len(self.all_files)} files with rule-based classification...")
        
        for i, file in enumerate(self.all_files):
            if (i + 1) % 1000 == 0:  # Progress indicator every 1000 files
                print(f"   📊 Processed {i + 1}/{len(self.all_files)} files...")
                
            # Use enhanced classification method for consistent logging
            suggested_category, confidence, reasoning = self._classify_file_enhanced(file)
            
            # Check if file is misplaced
            if suggested_category != file.category and confidence >= self.min_confidence:
                suggested_path = self._suggest_target_directory(file, suggested_category)
                
                misplaced_file = MisplacedFile(
                    file=file,
                    current_category=file.category,
                    suggested_category=suggested_category,
                    suggested_path=suggested_path,
                    confidence=confidence,
                    reasoning=reasoning
                )
                misplaced.append(misplaced_file)
                
                # Log detailed information about misplaced file
                self.logger.info(f"MISPLACED FILE DETECTED:")
                self.logger.info(f"  File: {file.name}")
                self.logger.info(f"  Current: {file.category} -> Suggested: {suggested_category}")
                self.logger.info(f"  Confidence: {confidence:.2f}")
                self.logger.info(f"  Reasoning: {reasoning}")
                self.logger.info(f"  Size: {self._format_file_size(file.size)}")
                self.logger.info(f"  Path: {file.path}")
        
        return misplaced
    
    
    def _classify_file_unified(self, file: MediaFile) -> Tuple[str, float, str, str]:
        """Strict two-step classification: Database Cache → AI → Unclassified."""
        filename = file.name
        
        self.logger.debug(f"Classifying file: {filename} (Current category: {file.category})")
        
        # STEP 1: Check TV/Movie database cache ONLY
        cached_result = self._check_metadata_cache(file)
        if cached_result:
            category, confidence, reasoning = cached_result
            self.classification_stats['cache_hits'] += 1
            print(f"   🎯 DB CACHE: {filename} -> {category} (confidence: {confidence:.2f})")
            self.logger.info(f"DB CACHE HIT: {filename} -> {category} (confidence: {confidence:.2f}) | {reasoning}")
            return category, confidence, f"Database Cache: {reasoning}", "cache_hits"
        
        # STEP 1.5: Smart TV Episode Detection (skip individual episode AI processing)
        tv_show_result = self._check_tv_episode_pattern(file)
        if tv_show_result:
            category, confidence, reasoning = tv_show_result
            self.classification_stats['tv_pattern_detection'] += 1
            print(f"   📺 TV PATTERN: {filename} -> {category} (confidence: {confidence:.2f})")
            self.logger.info(f"TV PATTERN DETECTED: {filename} -> {category} (confidence: {confidence:.2f}) | {reasoning}")
            return category, confidence, f"TV Pattern: {reasoning}", "tv_pattern_detection"
        
        # STEP 2: AI classification for items not in database cache (skip TV episodes)
        if self.ai_classifier:
            ai_start = time.time()
            self.classification_stats['ai_calls'] += 1
            try:
                print(f"   🤖 AI LLM: Processing {filename}...")
                self.logger.debug(f"AI LLM processing: {filename}")
                ai_result = self.ai_classifier.classify_single(filename)
                ai_time = time.time() - ai_start
                self.classification_stats['ai_time'] += ai_time
                
                if ai_result:
                    self.classification_stats['ai_success'] += 1
                    category, confidence, reasoning = self._parse_ai_result(ai_result, file)
                    
                    # Accept any AI result (no confidence threshold)
                    print(f"   ✅ AI LLM: {filename} -> {category} (confidence: {confidence:.2f})")
                    self.logger.info(f"AI LLM CLASSIFIED: {filename} -> {category} (confidence: {confidence:.2f}) | {reasoning}")
                    return category, confidence, f"AI LLM: {reasoning}", "ai_classifications"
                else:
                    print(f"   ⚠️  AI LLM: No result for {filename}")
                    self.logger.warning(f"AI LLM returned no result for: {filename}")
            except Exception as e:
                ai_time = time.time() - ai_start
                self.classification_stats['ai_time'] += ai_time
                print(f"   ❌ AI LLM: Failed for {filename} - {e}")
                self.logger.error(f"AI LLM failed for {filename}: {e}")
        
        # STEP 3: Mark as unclassified (no rule-based fallback)
        print(f"   ❓ UNCLASSIFIED: {filename} (staying in {file.category})")
        self.logger.info(f"UNCLASSIFIED: {filename} - keeping in current category {file.category}")
        self.classification_stats['unclassified'] = self.classification_stats.get('unclassified', 0) + 1
        
        # Return current category with low confidence to indicate it's unclassified
        return file.category, 0.1, "Unclassified - no database match or AI result", "unclassified"
    
    def _check_metadata_cache(self, file: MediaFile) -> Optional[Tuple[str, float, str]]:
        """Check metadata enrichment cache for verified classification."""
        try:
            # Initialize metadata cache if not already done
            if not hasattr(self, '_metadata_cache'):
                from .metadata_enrichment import MetadataCache
                self._metadata_cache = MetadataCache()
            
            # Extract title and year from filename
            from .metadata_enrichment import MetadataEnricher
            enricher = MetadataEnricher()
            title, year = enricher.extract_title_and_year(file.name)
            
            # Check cache
            cached_metadata = self._metadata_cache.get_metadata(title, year)
            if cached_metadata:
                # Map metadata type to our categories
                media_type = cached_metadata.media_type
                confidence = cached_metadata.confidence
                reasoning = f"TMDB verified: {', '.join(cached_metadata.genres)}"
                
                self.logger.debug(f"Cache hit for {title} ({year}): {media_type} (confidence: {confidence:.2f})")
                return media_type, confidence, reasoning
                
            return None
            
        except Exception as e:
            self.logger.debug(f"Metadata cache check failed for {file.name}: {e}")
            return None
    
    def _check_tv_episode_pattern(self, file: MediaFile) -> Optional[Tuple[str, float, str]]:
        """Check if file matches TV episode patterns to avoid individual AI processing."""
        import re
        filename = file.name
        
        # TV episode patterns to match
        tv_patterns = [
            r'[Ss]\d{1,2}[Ee]\d{1,2}',  # S01E01, s1e2, etc.
            r'Season\s*\d+.*Episode\s*\d+',  # Season 1 Episode 1
            r'\d{1,2}x\d{1,2}',  # 1x01, 12x05, etc.
        ]
        
        # Check if filename matches TV episode patterns
        for pattern in tv_patterns:
            if re.search(pattern, filename, re.IGNORECASE):
                self.logger.debug(f"TV episode pattern detected in {filename}: {pattern}")
                return "TV", 0.9, f"TV episode pattern detected: {pattern}"
        
        # Check if file is in a TV-like directory structure
        path_parts = str(file.path).lower()
        tv_indicators = ['season', 'episode', 's01', 's02', 's03', 's04', 's05', 'complete series', 'tv series']
        
        for indicator in tv_indicators:
            if indicator in path_parts:
                self.logger.debug(f"TV directory structure detected for {filename}: {indicator}")
                return "TV", 0.8, f"TV directory structure: contains '{indicator}'"
        
        return None
    
    def _analyze_with_unified_workflow(self) -> List[MisplacedFile]:
        """Unified workflow: metadata cache → AI → rule-based fallback."""
        misplaced = []
        processing_stats = {
            'cache_hits': 0,
            'ai_classifications': 0,
            'tv_pattern_detection': 0,
            'unclassified': 0,
            'total_processed': 0
        }
        
        # Process all files with unified classification
        for i, file in enumerate(self.all_files):
            if (i + 1) % 100 == 0:  # Progress indicator
                print(f"   📊 Processed {i + 1}/{len(self.all_files)} files...")
                
            suggested_category, confidence, reasoning, method_used = self._classify_file_unified(file)
            processing_stats['total_processed'] += 1
            processing_stats[method_used] += 1
            
            # Check if file is misplaced
            if suggested_category != file.category and confidence >= self.min_confidence:
                suggested_path = self._suggest_target_directory(file, suggested_category)
                
                misplaced_file = MisplacedFile(
                    file=file,
                    current_category=file.category,
                    suggested_category=suggested_category,
                    suggested_path=suggested_path,
                    confidence=confidence,
                    reasoning=reasoning
                )
                misplaced.append(misplaced_file)
                
                # Log misplaced file details for actionable reporting
                self.logger.info(f"MISPLACED FILE: {file.name}")
                self.logger.info(f"  Source: {file.path}")
                self.logger.info(f"  Current: {file.category} → Suggested: {suggested_category}")
                self.logger.info(f"  Target: {suggested_path}")
                self.logger.info(f"  Confidence: {confidence:.2f} | Method: {method_used}")
                self.logger.info(f"  Reasoning: {reasoning}")
                self.logger.info(f"  Size: {self._format_file_size(file.size)}")
        
        # Log processing summary
        self.logger.info(f"📊 UNIFIED WORKFLOW SUMMARY:")
        self.logger.info(f"   Total files processed: {processing_stats['total_processed']:,}")
        self.logger.info(f"   Metadata cache hits: {processing_stats['cache_hits']:,}")
        self.logger.info(f"   AI classifications: {processing_stats['ai_classifications']:,}")
        self.logger.info(f"   TV pattern detection: {processing_stats['tv_pattern_detection']:,}")
        self.logger.info(f"   Unclassified: {processing_stats['unclassified']:,}")
        self.logger.info(f"   Misplaced files found: {len(misplaced):,}")
        
        print(f"   ✅ Processing complete: {len(misplaced)} misplaced files found")
        print(f"   📊 Methods used: {processing_stats['cache_hits']} cache, {processing_stats['ai_classifications']} AI, {processing_stats['tv_pattern_detection']} TV patterns, {processing_stats['unclassified']} unclassified")
        
        return misplaced
    
    def _classify_with_external_apis(self, title: str, file: MediaFile) -> Optional[Tuple[str, float, str]]:
        """Classify using external APIs (TMDB/TVDB)."""
        try:
            # Clean up title for API search
            clean_title = self._clean_title_for_api(title)
            
            # Try external API for movies
            if self.api_client and file.category == "movies":
                movie_results = self.api_client.search_movie(clean_title)
                if movie_results:
                    # Check if title suggests documentary in search results
                    for result in movie_results[:3]:  # Check top 3 results
                        if result.overview and 'document' in result.overview.lower():
                            return "documentaries", 0.8, f"External API identified as documentary: {clean_title}"
                    return "movies", 0.8, f"External API confirmed as movie: {clean_title}"
            
            # Try for TV shows
            if self.api_client and file.category == "tv":
                tv_results = self.api_client.search_tv_show(clean_title)
                if tv_results:
                    return "tv", 0.8, f"External API confirmed as TV series: {clean_title}"
            
            return None
            
        except Exception as e:
            print(f"   ⚠️  External API error: {e}")
            return None
    
    def _clean_title_for_api(self, title: str) -> str:
        """Clean title for external API search."""
        import re
        
        # Remove common patterns that interfere with search
        patterns_to_remove = [
            r'\(\d{4}\)',  # Year in parentheses
            r'\[.*?\]',     # Anything in square brackets
            r'\b(720p|1080p|2160p|4k)\b',  # Quality indicators
            r'\b(x264|x265|xvid|hevc)\b',  # Codecs
            r'\b(bluray|webrip|hdtv|dvdrip)\b',  # Sources
            r'\b(s\d+e\d+)\b',  # Season/episode patterns
            r'\.(mkv|mp4|avi|mov)$'  # File extensions
        ]
        
        clean = title
        for pattern in patterns_to_remove:
            clean = re.sub(pattern, '', clean, flags=re.IGNORECASE)
        
        # Clean up whitespace and special characters
        clean = re.sub(r'[._-]', ' ', clean)
        clean = re.sub(r'\s+', ' ', clean).strip()
        
        return clean
    
    def _get_ai_classifications(self, files: List[MediaFile]) -> List[Optional[dict]]:
        """Get AI classifications for a batch of files."""
        try:
            filenames = [file.name for file in files]
            
            # Call OpenAI classifier (returns list of dicts or None)
            results = self.ai_classifier.classify_batch(filenames)
            
            # Results are already in dict format from OpenAI classifier
            return results
            
        except Exception as e:
            print(f"   ⚠️  AI classification failed: {e}")
            return [None] * len(files)
    
    
    def _parse_ai_result(self, ai_result: dict, file: MediaFile) -> Tuple[str, float, str]:
        """Parse AI classification result."""
        try:
            category = ai_result.get('category', '').lower()
            confidence = float(ai_result.get('confidence', 0.7))
            reasoning = ai_result.get('reasoning', 'AI classification')
            
            # Map AI categories to our internal categories
            category_mapping = {
                'movie': 'movies',
                'tv': 'tv', 
                'documentary': 'documentaries',
                'standup': 'standup',
                'audiobook': 'audiobooks',  # Not used but here for completeness
                'other': file.category  # Keep in current category
            }
            
            mapped_category = category_mapping.get(category, file.category)
            return mapped_category, confidence, f"AI: {reasoning}"
            
        except Exception:
            # Parse error, fall back to rules
            suggested_category = self._classify_file_rule_based(file)
            confidence = self._calculate_confidence(file, suggested_category)
            reasoning = self._get_classification_reasoning(file, suggested_category) + " (AI parse error, rule fallback)"
            return suggested_category, confidence, reasoning
    
    def _classify_file_rule_based(self, file: MediaFile) -> str:
        """Classify file using enhanced rule-based patterns."""
        filename = file.name.lower()
        path_str = str(file.path).lower()
        
        # Enhanced documentary patterns (check first as they're more specific)
        documentary_patterns = [
            # Explicit documentary indicators
            'documentary', 'docu', 'documental', 'documentry',
            
            # Educational/nature content
            'national geographic', 'nat geo', 'natgeo', 'bbc', 'discovery',
            'nature', 'wildlife', 'planet earth', 'blue planet', 'cosmos',
            'history channel', 'history.com', 'biography', 'nova', 'frontline',
            
            # Documentary series/channels
            'pbs', 'hbo documentary', 'netflix documentary', 'vice',
            'smithsonian', 'cnn', 'msnbc documentary',
            
            # Common documentary keywords
            'investigation', 'expose', 'revealed', 'untold story',
            'behind the scenes', 'making of', 'the real', 'true story',
            'conspiracy', 'mystery', 'unsolved', 'crime documentary',
            
            # Science/educational
            'science', 'evolution', 'universe', 'space', 'quantum',
            'climate', 'environment', 'archaeology', 'anthropology'
        ]
        
        # Stand-up comedy patterns (check before TV patterns)
        standup_patterns = [
            'standup', 'stand-up', 'stand up', 'comedy special', 'live comedy',
            'comedy central', 'netflix comedy', 'hbo comedy', 'showtime comedy',
            
            # Famous comedians (helps identify their specials)
            'chappelle', 'carlin', 'pryor', 'murphy', 'rock', 'burr', 'hart',
            'amy schumer', 'tina fey', 'louis ck', 'bill hicks', 'robin williams',
            'jerry seinfeld', 'kevin hart', 'john mulaney', 'trevor noah',
            
            # Common special titles
            'live at', 'live from', 'sticks and stones', 'killed them softly',
            'raw', 'delirious', 'bigger and blacker', 'never scared'
        ]
        
        # Enhanced TV episode patterns
        tv_patterns = [
            # Season/Episode formats
            's0', 's1', 's2', 's3', 's4', 's5', 's6', 's7', 's8', 's9',  # S##
            'season', 'episode',
            'e0', 'e1', 'e2', 'e3', 'e4', 'e5', 'e6', 'e7', 'e8', 'e9',  # E##
            
            # Episode format variations  
            '1x0', '2x0', '3x0', '4x0', '5x0', '6x0', '7x0', '8x0', '9x0',  # ##x##
            '0x0',  # Special episodes
            
            # Common TV show indicators (but exclude movie parts)
            'part1', 'part2', 'part3', 'part 1', 'part 2', 'part 3',
        ]
        
        # Enhanced movie patterns 
        movie_patterns = [
            # Year indicators
            '(19', '(20',  # (1995), (2020)
            ' 19', ' 20',  # Space before year
            '.19', '.20',  # Dot before year
            
            # Quality/release indicators
            'bluray', 'blu-ray', 'dvdrip', 'webrip', 'hdtv', 'hdcam',
            'ts', 'cam', 'dvdscr', 'bdrip', 'brrip', 'hdtc',
            '1080p', '720p', '480p', '4k', 'uhd',
            'x264', 'x265', 'xvid', 'divx',
            
            # Movie-specific terms
            'directors cut', 'extended', 'unrated', 'theatrical',
            'criterion', 'remastered', 'restored'
        ]
        
        # Check for documentaries first (most specific)
        for pattern in documentary_patterns:
            if pattern in filename or pattern in path_str:
                return "documentaries"
        
        # Check for stand-up comedy second
        for pattern in standup_patterns:
            if pattern in filename or pattern in path_str:
                return "standup"
        
        # Check for TV patterns (more specific than movies)
        for pattern in tv_patterns:
            if pattern in filename:
                return "tv"
        
        # Check path for TV show structure (folders like "Show Name/Season 01/")
        if '/season' in path_str or 'season ' in path_str:
            return "tv"
            
        # Check for multi-part movie files (these are movies, not TV)
        if any(term in filename for term in ['cd1', 'cd2', 'disc1', 'disc2', 'part1', 'part2']) and not any(term in filename for term in tv_patterns):
            return "movies"
        
        # Check if it looks like a movie
        for pattern in movie_patterns:
            if pattern in filename:
                return "movies"
        
        # Special case: If file is in a folder named after a movie year pattern
        parent_folder = file.path.parent.name.lower()
        if any(pattern in parent_folder for pattern in ['(19', '(20', ' 19', ' 20']):
            return "movies"
            
        # Default classification based on current location
        # (conservative approach - only suggest changes for clear patterns)
        return file.category
    
    def _calculate_confidence(self, file: MediaFile, suggested_category: str) -> float:
        """Calculate enhanced confidence score for classification."""
        filename = file.name.lower()
        path_str = str(file.path).lower()
        
        if suggested_category == "documentaries":
            # Very high confidence documentary indicators
            if any(pattern in filename for pattern in ['documentary', 'docu']):
                return 0.95
            elif any(pattern in filename for pattern in ['national geographic', 'nat geo', 'bbc']):
                return 0.9
            elif any(pattern in filename for pattern in ['discovery', 'history channel', 'nova', 'frontline']):
                return 0.85
            else:
                return 0.8  # Other documentary keywords
                
        elif suggested_category == "standup":
            # Very high confidence standup indicators
            if any(pattern in filename for pattern in ['standup', 'stand-up', 'comedy special']):
                return 0.95
            elif any(pattern in filename for pattern in ['chappelle', 'carlin', 'rock', 'burr']):
                return 0.9  # Famous comedians
            else:
                return 0.8  # Other standup keywords
                
        elif suggested_category == "tv":
            # Very high confidence TV indicators
            if any(pattern in filename for pattern in ['s0', 's1', 's2', 's3', 's4']):
                if any(pattern in filename for pattern in ['e0', 'e1', 'e2', 'e3', 'e4']):
                    return 0.95  # Both season and episode indicators
                return 0.9  # Season indicator only
            
            if any(pattern in filename for pattern in ['season', 'episode']):
                return 0.9
                
            # High confidence TV indicators
            if any(pattern in filename for pattern in ['1x0', '2x0', '3x0', '4x0', '5x0']):
                return 0.85
                
            # Medium-high confidence
            if '/season' in path_str or 'season ' in path_str:
                return 0.8
                
        elif suggested_category == "movies":
            # Very high confidence movie indicators
            if any(pattern in filename for pattern in ['(19', '(20']) and any(pattern in filename for pattern in ['1080p', '720p', 'bluray', 'bdrip']):
                return 0.95  # Year + quality indicator
                
            # High confidence movie indicators
            if any(pattern in filename for pattern in ['(19', '(20']):
                return 0.85
                
            # Medium-high confidence
            if any(pattern in filename for pattern in ['bluray', 'bdrip', 'x264', 'x265']):
                return 0.8
                
            # Movie folder structure
            parent_folder = file.path.parent.name.lower()
            if any(pattern in parent_folder for pattern in ['(19', '(20']):
                return 0.8
                
        # Default medium confidence
        return 0.7
    
    def _suggest_target_directory(self, file: MediaFile, category: str) -> str:
        """Suggest target directory for misplaced file using proper config paths."""
        if category == "tv" or category == "TV":
            if self.config.tv_directories:
                return self.config.tv_directories[0]
        elif category == "movies":
            if self.config.movie_directories:
                return self.config.movie_directories[0]
        elif category == "documentaries":
            # Use dedicated documentary directory from config
            try:
                # Access documentaries config directly from the config object
                if hasattr(self.config, 'config_data') and 'documentaries' in self.config.config_data:
                    doc_dirs = self.config.config_data['documentaries']['directories']
                    if doc_dirs:
                        return doc_dirs[0]['path']
            except Exception:
                pass
            # Fallback to proper documentary mount
            return "/mnt/qnap/Media/Documentary/"
        elif category == "standup":
            # Use dedicated standup directory from config
            try:
                # Access standups config directly from the config object
                if hasattr(self.config, 'config_data') and 'standups' in self.config.config_data:
                    standup_dirs = self.config.config_data['standups']['directories']
                    if standup_dirs:
                        return standup_dirs[0]['path']
            except Exception:
                pass
            # Fallback to proper standup mount
            return "/mnt/qnap/Media/standups/"
        else:
            return str(file.path.parent)
    
    def _get_classification_reasoning(self, file: MediaFile, suggested_category: str) -> str:
        """Get human-readable reasoning for classification."""
        filename = file.name.lower()
        path_str = str(file.path).lower()
        
        if suggested_category == "tv":
            # Check for specific patterns and provide detailed reasoning
            if any(pattern in filename for pattern in ['s0', 's1', 's2', 's3', 's4']) and any(pattern in filename for pattern in ['e0', 'e1', 'e2', 'e3', 'e4']):
                return "Contains S##E## episode format (season and episode numbers)"
            elif any(pattern in filename for pattern in ['s0', 's1', 's2', 's3', 's4']):
                return "Contains season number indicator (S##)"
            elif 'season' in filename or 'episode' in filename:
                return "Contains explicit season/episode text"
            elif any(pattern in filename for pattern in ['1x0', '2x0', '3x0', '4x0', '5x0']):
                return "Contains ##x## episode format"
            elif '/season' in path_str or 'season ' in path_str:
                return "Located in season-based directory structure"
            else:
                return "TV show patterns detected in filename"
                
        elif suggested_category == "movies":
            # Check for movie-specific patterns
            if any(pattern in filename for pattern in ['(19', '(20']) and any(pattern in filename for pattern in ['1080p', '720p', 'bluray', 'bdrip']):
                return "Contains year and quality indicators typical of movie releases"
            elif any(pattern in filename for pattern in ['(19', '(20']):
                return "Contains year indicator in parentheses (movie format)"
            elif any(pattern in filename for pattern in ['bluray', 'bdrip', 'x264', 'x265', '1080p', '720p']):
                return "Contains video quality/codec indicators typical of movies"
            else:
                parent_folder = file.path.parent.name.lower()
                if any(pattern in parent_folder for pattern in ['(19', '(20']):
                    return "Located in movie-titled directory with year"
                return "Movie release patterns detected in filename"
                
        return "Rule-based analysis suggests different media type"
    
    def _generate_reports(self) -> Dict[str, Optional[str]]:
        """Generate actionable reports with move commands and categorized recommendations."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        reports_dir = Path("reports")
        reports_dir.mkdir(exist_ok=True)
        
        report_paths = {"text": None, "json": None}
        
        # Generate actionable text report
        if self.output_format in ['text', 'both']:
            txt_path = reports_dir / f"media_reorganization_actionable_{timestamp}.txt"
            report_paths["text"] = str(txt_path)
            
            with open(txt_path, 'w', encoding='utf-8') as f:
                f.write("ACTIONABLE MEDIA REORGANIZATION REPORT\n")
                f.write("=" * 50 + "\n")
                f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Session ID: {self.session_id}\n\n")
                
                # Executive Summary
                f.write("📊 SUMMARY\n")
                f.write("-" * 10 + "\n")
                f.write(f"Total Files Processed: {len(self.all_files):,}\n")
                f.write(f"Misplaced Files Found: {len(self.misplaced_files):,}\n")
                if self.all_files:
                    percentage = (len(self.misplaced_files) / len(self.all_files)) * 100
                    f.write(f"Misplacement Rate: {percentage:.1f}%\n")
                f.write(f"Classification Method: TV/Movie DB → AI → Rule-based\n")
                f.write(f"Minimum Confidence: {self.min_confidence}\n\n")
                
                # Categorize by confidence level for prioritization
                high_conf = [mf for mf in self.misplaced_files if mf.confidence >= 0.9]
                med_conf = [mf for mf in self.misplaced_files if 0.7 <= mf.confidence < 0.9]
                low_conf = [mf for mf in self.misplaced_files if mf.confidence < 0.7]
                
                f.write("🎯 RECOMMENDATIONS BY PRIORITY\n")
                f.write("-" * 30 + "\n")
                f.write(f"HIGH CONFIDENCE (≥0.9): {len(high_conf)} files - EXECUTE IMMEDIATELY\n")
                f.write(f"MEDIUM CONFIDENCE (0.7-0.9): {len(med_conf)} files - REVIEW & EXECUTE\n")
                f.write(f"LOW CONFIDENCE (<0.7): {len(low_conf)} files - MANUAL REVIEW REQUIRED\n\n")
                
                # High confidence moves (ready to execute)
                if high_conf:
                    f.write("🚀 HIGH CONFIDENCE MOVES (READY TO EXECUTE)\n")
                    f.write("=" * 45 + "\n")
                    for i, mf in enumerate(high_conf, 1):
                        f.write(f"{i}. {mf.file.name}\n")
                        f.write(f"   SOURCE: {mf.file.path}\n")
                        f.write(f"   TARGET: {mf.suggested_path}\n")
                        f.write(f"   CATEGORY: {mf.current_category} → {mf.suggested_category}\n")
                        f.write(f"   CONFIDENCE: {mf.confidence:.2f} | {mf.reasoning}\n")
                        f.write(f"   SIZE: {mf._format_file_size(mf.file.size)}\n")
                        
                        # Generate move command
                        source_escaped = str(mf.file.path).replace(' ', '\\ ')
                        target_escaped = mf.suggested_path.replace(' ', '\\ ')
                        f.write(f"   MOVE CMD: mv \"{mf.file.path}\" \"{mf.suggested_path}\"\n\n")
                
                # Medium confidence moves (review recommended)
                if med_conf:
                    f.write("⚠️  MEDIUM CONFIDENCE MOVES (REVIEW RECOMMENDED)\n")
                    f.write("=" * 50 + "\n")
                    for i, mf in enumerate(med_conf, 1):
                        f.write(f"{i}. {mf.file.name}\n")
                        f.write(f"   SOURCE: {mf.file.path}\n")
                        f.write(f"   TARGET: {mf.suggested_path}\n")
                        f.write(f"   CATEGORY: {mf.current_category} → {mf.suggested_category}\n")
                        f.write(f"   CONFIDENCE: {mf.confidence:.2f} | {mf.reasoning}\n")
                        f.write(f"   SIZE: {mf._format_file_size(mf.file.size)}\n")
                        f.write(f"   MOVE CMD: mv \"{mf.file.path}\" \"{mf.suggested_path}\"\n\n")
                
                # Low confidence moves (manual review required)
                if low_conf:
                    f.write("🔍 LOW CONFIDENCE MOVES (MANUAL REVIEW REQUIRED)\n")
                    f.write("=" * 50 + "\n")
                    for i, mf in enumerate(low_conf, 1):
                        f.write(f"{i}. {mf.file.name}\n")
                        f.write(f"   SOURCE: {mf.file.path}\n")
                        f.write(f"   TARGET: {mf.suggested_path}\n")
                        f.write(f"   CATEGORY: {mf.current_category} → {mf.suggested_category}\n")
                        f.write(f"   CONFIDENCE: {mf.confidence:.2f} | {mf.reasoning}\n")
                        f.write(f"   SIZE: {mf._format_file_size(mf.file.size)}\n")
                        f.write(f"   REVIEW: Manual verification needed before moving\n\n")
                
                # Usage instructions
                f.write("📝 USAGE INSTRUCTIONS\n")
                f.write("-" * 20 + "\n")
                f.write("1. Start with HIGH CONFIDENCE moves - these are very likely correct\n")
                f.write("2. Copy and paste MOVE CMD commands into terminal (with caution)\n")
                f.write("3. Review MEDIUM CONFIDENCE moves manually before executing\n")
                f.write("4. Manually verify all LOW CONFIDENCE moves\n")
                f.write("5. Always backup important files before bulk operations\n")
                f.write("6. Test with a few files first before batch operations\n\n")
                
                f.write("🔧 INTEGRATION WITH MOVE TOOL\n")
                f.write("-" * 30 + "\n")
                f.write(f"Use this JSON report with future move operations:\n")
                f.write(f"reports/media_reorganization_actionable_{timestamp}.json\n")
        
        # Generate actionable JSON report
        if self.output_format in ['json', 'both']:
            json_path = reports_dir / f"media_reorganization_actionable_{timestamp}.json"
            latest_json_path = reports_dir / "media_reorganization_latest.json"
            report_paths["json"] = str(json_path)
            
            json_data = self._generate_actionable_json_data()
            
            # Save timestamped version
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, indent=2, ensure_ascii=False)
            
            # Save latest version (no timestamp)
            with open(latest_json_path, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Latest report also saved to: {latest_json_path}")
        
        return report_paths
    
    def _generate_actionable_json_data(self) -> dict:
        """Generate actionable JSON report data for move operations."""
        # Calculate summary statistics
        total_size = sum(mf.file.size for mf in self.misplaced_files)
        
        # Categorize by confidence level
        high_conf = [mf for mf in self.misplaced_files if mf.confidence >= 0.9]
        med_conf = [mf for mf in self.misplaced_files if 0.7 <= mf.confidence < 0.9]
        low_conf = [mf for mf in self.misplaced_files if mf.confidence < 0.7]
        
        # Generate move operations for each category
        def create_move_operation(mf: MisplacedFile) -> dict:
            """Create a move operation dict from a misplaced file."""
            op = mf.to_dict()
            op.update({
                "move_command": f'mv "{mf.file.path}" "{mf.suggested_path}"',
                "operation_type": "file_move",
                "priority": "high" if mf.confidence >= 0.9 else "medium" if mf.confidence >= 0.7 else "low",
                "requires_review": mf.confidence < 0.9,
                "target_directory": str(Path(mf.suggested_path).parent),
                "filename": mf.file.name
            })
            return op
        
        # Group by category transitions
        by_category = {}
        for mf in self.misplaced_files:
            transition = f"{mf.current_category} → {mf.suggested_category}"
            if transition not in by_category:
                by_category[transition] = []
            by_category[transition].append(create_move_operation(mf))
        
        return {
            "report_metadata": {
                "report_type": "actionable_reorganization",
                "timestamp": datetime.now().isoformat(),
                "session_id": self.session_id,
                "tool_version": "v2.0 (Unified Workflow)",
                "classification_workflow": "TV/Movie DB → AI → Rule-based",
                "total_files_analyzed": len(self.all_files),
                "confidence_threshold": self.min_confidence
            },
            "execution_summary": {
                "total_misplaced_files": len(self.misplaced_files),
                "misplacement_rate_percent": round((len(self.misplaced_files) / len(self.all_files) * 100), 2) if self.all_files else 0,
                "total_size_bytes": total_size,
                "total_size_readable": self._format_file_size(total_size),
                "priority_breakdown": {
                    "high_confidence_moves": len(high_conf),
                    "medium_confidence_moves": len(med_conf),
                    "low_confidence_moves": len(low_conf)
                },
                "category_transitions": {
                    transition: len(files) for transition, files in by_category.items()
                }
            },
            "actionable_moves": {
                "high_confidence": {
                    "description": "Ready for immediate execution (>=0.9 confidence)",
                    "count": len(high_conf),
                    "operations": [create_move_operation(mf) for mf in high_conf]
                },
                "medium_confidence": {
                    "description": "Review recommended before execution (0.7-0.9 confidence)",
                    "count": len(med_conf),
                    "operations": [create_move_operation(mf) for mf in med_conf]
                },
                "low_confidence": {
                    "description": "Manual review required (<0.7 confidence)",
                    "count": len(low_conf),
                    "operations": [create_move_operation(mf) for mf in low_conf]
                }
            },
            "move_commands": {
                "bash_script_ready": [f'mv "{mf.file.path}" "{mf.suggested_path}"' for mf in high_conf],
                "review_required": [f'mv "{mf.file.path}" "{mf.suggested_path}"' for mf in med_conf + low_conf]
            },
            "usage_instructions": [
                "1. Execute 'high_confidence' moves first - these are very reliable",
                "2. Review 'medium_confidence' moves manually before execution",
                "3. Manually verify all 'low_confidence' moves",
                "4. Use 'move_commands.bash_script_ready' for bulk operations",
                "5. Always backup important files before bulk moves",
                "6. Verify target directories exist before moving files"
            ],
            "integration_ready": {
                "format_version": "2.0",
                "compatible_with": ["future_move_tool", "batch_operations", "manual_review"],
                "next_steps": "This report is ready for integration with move operations tool"
            }
        }
    
    def _show_summary(self):
        """Show summary of findings."""
        if not self.misplaced_files:
            return
            
        # Group by suggested category
        by_category = {}
        total_size = 0
        
        for mf in self.misplaced_files:
            transition = f"{mf.current_category} → {mf.suggested_category}"
            if transition not in by_category:
                by_category[transition] = []
            by_category[transition].append(mf)
            total_size += mf.file.size
        
        print("📊 SUMMARY BY CATEGORY")
        print("-" * 25)
        for transition, files in by_category.items():
            print(f"{transition}: {len(files)} files")
        
        print()
        print(f"💾 Total data to reorganize: {self._format_file_size(total_size)}")
        
    def _format_file_size(self, size_bytes: int) -> str:
        """Format file size in human-readable format."""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} PB"


def main():
    """CLI entry point for standalone usage."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Media Reorganization Analysis Tool")
    parser.add_argument('--limit', type=int, help='Limit number of files to process for testing (default: no limit)')
    parser.add_argument('--confidence', type=float, default=0.7, help='Minimum confidence threshold (default: 0.7)')
    parser.add_argument('--format', choices=['text', 'json', 'both'], default='both', help='Output format (default: both)')
    parser.add_argument('--ai', action='store_true', help='Enable AI classification')
    parser.add_argument('--rebuild-db', action='store_true', help='Force database rebuild')
    parser.add_argument('--no-external-apis', action='store_true', help='Disable external API usage')
    
    args = parser.parse_args()
    
    analyzer = MediaReorganizationAnalyzer(
        rebuild_db=args.rebuild_db,
        min_confidence=args.confidence,
        output_format=args.format,
        use_ai=args.ai,
        use_external_apis=not args.no_external_apis,
        limit_files=args.limit
    )
    
    return analyzer.run_analysis(args)


if __name__ == "__main__":
    exit(main())