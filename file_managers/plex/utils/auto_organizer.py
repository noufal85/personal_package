"""Auto-organizer for downloaded media files using AI classification and smart placement."""

import json
import os
import shutil
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, NamedTuple, Optional, Tuple, Union
from enum import Enum

import boto3
from botocore.exceptions import ClientError, NoCredentialsError

from ..config.config import config

# Load environment variables from .env file if available
def load_env_file():
    """Load environment variables from .env file in project root."""
    env_path = Path(__file__).parent.parent.parent.parent / ".env"
    if env_path.exists():
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()

# Load .env file on module import
load_env_file()


class MediaType(Enum):
    """Supported media types for classification."""
    MOVIE = "MOVIE"
    TV = "TV" 
    DOCUMENTARY = "DOCUMENTARY"
    STANDUP = "STANDUP"
    AUDIOBOOK = "AUDIOBOOK"
    OTHER = "OTHER"


class ClassificationResult(NamedTuple):
    """Result of AI classification."""
    media_type: MediaType
    confidence: float
    reasoning: Optional[str] = None


class MediaFile(NamedTuple):
    """Represents a media file to be organized."""
    path: Path
    size: int
    media_type: Optional[MediaType] = None
    target_directory: Optional[str] = None
    classification_source: Optional[str] = None  # "AI" or "Rule-based"


class MoveResult(NamedTuple):
    """Result of a file move operation."""
    success: bool
    source_path: Path
    target_path: Optional[Path] = None
    error: Optional[str] = None
    space_freed: int = 0


class BedrockClassifier:
    """AI-powered media classification using AWS Bedrock."""
    
    def __init__(self):
        self.region = config.bedrock_region
        self.model_id = config.bedrock_model_id
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self) -> None:
        """Initialize the Bedrock client."""
        try:
            self.client = boto3.client('bedrock-runtime', region_name=self.region)
        except NoCredentialsError:
            print("⚠️  AWS credentials not configured. AI classification will be disabled.")
            self.client = None
        except Exception as e:
            print(f"⚠️  Failed to initialize Bedrock client: {e}")
            self.client = None
    
    def classify_file(self, filename: str) -> ClassificationResult:
        """
        Classify a media file using AI.
        
        Args:
            filename: Name of the file to classify
            
        Returns:
            ClassificationResult with media type and confidence
        """
        if not self.client:
            # Fallback to rule-based classification
            return self._fallback_classification(filename)
        
        try:
            # Prepare the prompt
            prompt = config.bedrock_classification_prompt.format(filename=filename)
            
            # Prepare the request body based on model type
            if "anthropic" in config.bedrock_model_id:
                body = json.dumps({
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": config.bedrock_max_tokens,
                    "temperature": config.bedrock_temperature,
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ]
                })
            else:  # Llama or other models
                body = json.dumps({
                    "prompt": prompt,
                    "max_gen_len": config.bedrock_max_tokens,
                    "temperature": config.bedrock_temperature,
                    "top_p": 0.9
                })
            
            # Make the API call
            try:
                response = self.client.invoke_model(
                    body=body,
                    modelId=config.bedrock_model_id,
                    accept='application/json',
                    contentType='application/json'
                )
            except ClientError as e:
                if "inference profile" in str(e):
                    # Try with inference profile for newer models
                    profile_id = f"us.{config.bedrock_model_id}"
                    response = self.client.invoke_model(
                        body=body,
                        modelId=profile_id,
                        accept='application/json',
                        contentType='application/json'
                    )
                else:
                    raise
            
            # Parse the response based on model type
            response_body = json.loads(response['body'].read())
            if "anthropic" in config.bedrock_model_id:
                classification_text = response_body['content'][0]['text'].strip().upper()
            else:  # Llama or other models
                classification_text = response_body['generation'].strip().upper()
            
            # Map response to MediaType
            try:
                media_type = MediaType(classification_text)
                return ClassificationResult(media_type=media_type, confidence=0.9)
            except ValueError:
                # If the response doesn't match our enum, try to extract it
                for media_type in MediaType:
                    if media_type.value in classification_text:
                        return ClassificationResult(media_type=media_type, confidence=0.7)
                
                # Fallback to OTHER
                return ClassificationResult(media_type=MediaType.OTHER, confidence=0.1)
        
        except ClientError as e:
            print(f"⚠️  Bedrock API error: {e}")
            return self._fallback_classification(filename)
        except Exception as e:
            print(f"⚠️  Classification error: {e}")
            return self._fallback_classification(filename)
    
    def _fallback_classification(self, filename: str) -> ClassificationResult:
        """
        Fallback rule-based classification when AI is unavailable.
        
        Args:
            filename: Name of the file to classify
            
        Returns:
            ClassificationResult based on filename patterns
        """
        filename_lower = filename.lower()
        
        # TV show patterns (more specific patterns first)
        tv_patterns = [
            's0', 's1', 's2', 's3', 's4', 's5', 's6', 's7', 's8', 's9',
            'season', 'episode', 'e0', 'e1', 'e2', 'e3', 'e4', 'e5',
            'hdtv', 'tv.', '.tv.'
        ]
        
        # Documentary patterns
        doc_patterns = [
            'documentary', 'docu', 'bbc', 'nat geo', 'national geographic',
            'history channel', 'discovery', 'nova', 'frontline'
        ]
        
        # Stand-up patterns
        standup_patterns = [
            'standup', 'stand-up', 'comedy special', 'live at', 'comedy central',
            'netflix comedy', 'hbo comedy', 'chappelle', 'carlin', 'rock', 'burr',
            'sticks and stones', 'killed them softly', 'raw', 'delirious'
        ]
        
        # Check patterns in order of specificity
        if any(pattern in filename_lower for pattern in doc_patterns):
            return ClassificationResult(media_type=MediaType.DOCUMENTARY, confidence=0.7)
        elif any(pattern in filename_lower for pattern in standup_patterns):
            return ClassificationResult(media_type=MediaType.STANDUP, confidence=0.7)
        elif any(pattern in filename_lower for pattern in tv_patterns):
            return ClassificationResult(media_type=MediaType.TV, confidence=0.6)
        else:
            # Default to movie for video files
            return ClassificationResult(media_type=MediaType.MOVIE, confidence=0.4)


class AutoOrganizer:
    """Automatic media file organizer."""
    
    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run
        self.classifier = BedrockClassifier()
        self.downloads_dir = Path(config.downloads_directory)
        
    def scan_downloads(self) -> List[MediaFile]:
        """
        Scan the downloads directory for media files.
        
        Returns:
            List of MediaFile objects found
        """
        media_files = []
        
        if not self.downloads_dir.exists():
            print(f"⚠️  Downloads directory not found: {self.downloads_dir}")
            return media_files
        
        print(f"🔍 Scanning downloads directory: {self.downloads_dir}")
        
        for file_path in self.downloads_dir.rglob('*'):
            if file_path.is_file() and self._is_media_file(file_path):
                try:
                    size = file_path.stat().st_size
                    media_file = MediaFile(path=file_path, size=size)
                    media_files.append(media_file)
                except (OSError, PermissionError):
                    continue
        
        print(f"📁 Found {len(media_files)} media files")
        return media_files
    
    def _is_media_file(self, file_path: Path) -> bool:
        """Check if a file is a media file based on extension."""
        return file_path.suffix.lower() in config.video_extensions_set
    
    def classify_files(self, media_files: List[MediaFile]) -> List[MediaFile]:
        """
        Classify media files using AI.
        
        Args:
            media_files: List of MediaFile objects to classify
            
        Returns:
            List of MediaFile objects with classification
        """
        classified_files = []
        
        print(f"🤖 Classifying {len(media_files)} files using AI...")
        
        for i, media_file in enumerate(media_files, 1):
            print(f"[{i}/{len(media_files)}] Classifying: {media_file.path.name}")
            
            # Classify the file
            result = self.classifier.classify_file(media_file.path.name)
            
            # Get target directories for this media type
            target_dirs = config.get_directories_by_media_type(result.media_type.value)
            target_directory = target_dirs[0] if target_dirs else None
            
            # Determine classification source
            classification_source = "AI" if self.classifier.client else "Rule-based"
            
            # Update the media file with classification
            classified_file = media_file._replace(
                media_type=result.media_type,
                target_directory=target_directory,
                classification_source=classification_source
            )
            classified_files.append(classified_file)
            
            print(f"    Type: {result.media_type.value} ({classification_source}), Target: {target_directory}")
            
            # Small delay to avoid hitting API limits
            time.sleep(1.0)  # Increased delay for Bedrock rate limits
        
        return classified_files
    
    def organize_files(self, classified_files: List[MediaFile]) -> List[MoveResult]:
        """
        Organize classified files into appropriate directories.
        
        Args:
            classified_files: List of classified MediaFile objects
            
        Returns:
            List of MoveResult objects
        """
        results = []
        
        # Group files by media type
        files_by_type = {}
        for media_file in classified_files:
            if media_file.media_type not in files_by_type:
                files_by_type[media_file.media_type] = []
            files_by_type[media_file.media_type].append(media_file)
        
        print(f"📦 Organizing {len(classified_files)} files...")
        
        for media_type, files in files_by_type.items():
            print(f"\n📂 Processing {len(files)} {media_type.value} files:")
            
            if media_type == MediaType.OTHER or media_type == MediaType.AUDIOBOOK:
                print(f"    ⏭️  Skipping {media_type.value} files")
                continue
            
            for media_file in files:
                result = self._move_file(media_file)
                results.append(result)
        
        return results
    
    def _move_file(self, media_file: MediaFile) -> MoveResult:
        """
        Move a single file to its target directory.
        
        Args:
            media_file: MediaFile to move
            
        Returns:
            MoveResult indicating success/failure
        """
        if not media_file.target_directory:
            return MoveResult(
                success=False,
                source_path=media_file.path,
                error="No target directory configured"
            )
        
        # Get available target directories (with fallbacks)
        target_dirs = config.get_directories_by_media_type(media_file.media_type.value)
        
        for target_dir in target_dirs:
            target_path = Path(target_dir)
            
            # Create target directory if it doesn't exist
            if not target_path.exists():
                if not self.dry_run:
                    try:
                        target_path.mkdir(parents=True, exist_ok=True)
                    except OSError as e:
                        print(f"    ❌ Failed to create directory {target_path}: {e}")
                        continue
            
            # Check available space
            if not self._check_space(media_file.size, target_path):
                print(f"    ⚠️  Insufficient space in {target_path}, trying next directory...")
                continue
            
            # Determine final target path
            final_target = target_path / media_file.path.name
            
            # Handle filename conflicts
            if final_target.exists():
                final_target = self._resolve_filename_conflict(final_target)
            
            # Perform the move
            if self.dry_run:
                print(f"    📋 DRY RUN: Would move to {final_target}")
                return MoveResult(
                    success=True,
                    source_path=media_file.path,
                    target_path=final_target
                )
            else:
                try:
                    shutil.move(str(media_file.path), str(final_target))
                    print(f"    ✅ Moved to {final_target}")
                    return MoveResult(
                        success=True,
                        source_path=media_file.path,
                        target_path=final_target,
                        space_freed=media_file.size
                    )
                except Exception as e:
                    print(f"    ❌ Failed to move: {e}")
                    continue
        
        # If we get here, all target directories failed
        return MoveResult(
            success=False,
            source_path=media_file.path,
            error="All target directories failed (space or access issues)"
        )
    
    def _check_space(self, file_size: int, target_path: Path) -> bool:
        """
        Check if there's enough space in the target directory.
        
        Args:
            file_size: Size of file to move in bytes
            target_path: Target directory path
            
        Returns:
            True if there's enough space
        """
        try:
            stat = shutil.disk_usage(target_path)
            available_space = stat.free
            
            # Require at least 1GB buffer beyond file size
            required_space = file_size + (1024 * 1024 * 1024)  # 1GB buffer
            
            return available_space >= required_space
        except OSError:
            return False
    
    def _resolve_filename_conflict(self, target_path: Path) -> Path:
        """
        Resolve filename conflicts by adding a number suffix.
        
        Args:
            target_path: Original target path
            
        Returns:
            New path with conflict resolved
        """
        base_name = target_path.stem
        extension = target_path.suffix
        parent = target_path.parent
        
        counter = 1
        while True:
            new_name = f"{base_name}_{counter}{extension}"
            new_path = parent / new_name
            if not new_path.exists():
                return new_path
            counter += 1
    
    def generate_report(self, results: List[MoveResult], classified_files: List[MediaFile] = None) -> str:
        """
        Generate a report of the organization results.
        
        Args:
            results: List of MoveResult objects
            
        Returns:
            Path to the generated report file
        """
        timestamp = datetime.now().strftime(config.timestamp_format)
        report_path = config.get_reports_path() / f"auto_organizer_{timestamp}.txt"
        
        successful_moves = [r for r in results if r.success]
        failed_moves = [r for r in results if not r.success]
        total_space_freed = sum(r.space_freed for r in successful_moves)
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("🤖 AUTO-ORGANIZER REPORT\n")
            f.write("=" * 60 + "\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Mode: {'DRY RUN' if self.dry_run else 'EXECUTION'}\n")
            f.write(f"Total Files Processed: {len(results)}\n")
            f.write(f"Successful Moves: {len(successful_moves)}\n")
            f.write(f"Failed Moves: {len(failed_moves)}\n")
            f.write(f"Total Space Freed: {self._format_size(total_space_freed)}\n\n")
            
            if successful_moves:
                f.write("✅ SUCCESSFUL MOVES:\n")
                f.write("-" * 40 + "\n")
                for result in successful_moves:
                    # Find classification info for this file
                    classification_info = ""
                    media_type = "UNKNOWN"
                    if classified_files:
                        for classified_file in classified_files:
                            if str(classified_file.path) == str(result.source_path):
                                media_type = classified_file.media_type.value if classified_file.media_type else "UNKNOWN"
                                classification_info = f" ({classified_file.classification_source or 'Unknown'} Classification)"
                                break
                    
                    f.write(f"  {result.source_path.name}\n")
                    f.write(f"    FROM: {result.source_path}\n")
                    f.write(f"    TO:   {result.target_path if result.target_path else 'N/A'}\n")
                    f.write(f"    SIZE: {self._format_size(result.space_freed)}\n")
                    f.write(f"    TYPE: {media_type}{classification_info}\n\n")
            
            if failed_moves:
                f.write("❌ FAILED MOVES:\n")
                f.write("-" * 40 + "\n")
                for result in failed_moves:
                    # Find classification info for failed files too
                    classification_info = ""
                    media_type = "UNKNOWN"
                    intended_target = "Unknown"
                    if classified_files:
                        for classified_file in classified_files:
                            if str(classified_file.path) == str(result.source_path):
                                media_type = classified_file.media_type.value if classified_file.media_type else "UNKNOWN"
                                classification_info = f" ({classified_file.classification_source or 'Unknown'} Classification)"
                                intended_target = classified_file.target_directory or "Unknown"
                                break
                    
                    f.write(f"  {result.source_path.name}\n")
                    f.write(f"    FROM: {result.source_path}\n")
                    f.write(f"    INTENDED TARGET: {intended_target}\n")
                    f.write(f"    TYPE: {media_type}{classification_info}\n")
                    f.write(f"    ERROR: {result.error}\n\n")
        
        return str(report_path)
    
    def _format_size(self, size_bytes: int) -> str:
        """Format file size in human-readable format."""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} PB"
    
    def run_full_organization(self) -> str:
        """
        Run the complete organization workflow.
        
        Returns:
            Path to the generated report
        """
        print("🤖 MEDIA AUTO-ORGANIZER")
        print("=" * 50)
        print(f"Mode: {'DRY RUN' if self.dry_run else 'EXECUTION'}")
        print(f"Downloads Directory: {self.downloads_dir}")
        
        try:
            # Step 1: Scan for media files
            media_files = self.scan_downloads()
            if not media_files:
                print("📭 No media files found in downloads directory")
                return ""
            
            # Step 2: Classify files using AI
            classified_files = self.classify_files(media_files)
            
            # Step 3: Organize files
            results = self.organize_files(classified_files)
            
            # Step 4: Generate report
            report_path = self.generate_report(results, classified_files)
            print(f"\n📄 Report generated: {report_path}")
            
            # Step 5: Summary
            successful = sum(1 for r in results if r.success)
            failed = sum(1 for r in results if not r.success)
            print(f"\n📊 SUMMARY:")
            print(f"  Successful: {successful}")
            print(f"  Failed: {failed}")
            print(f"  Total: {len(results)}")
            
            if not self.dry_run and successful > 0:
                print(f"🎉 Successfully organized {successful} media files!")
            
            return report_path
            
        except KeyboardInterrupt:
            print("\n👋 Organization cancelled by user")
            return ""
        except Exception as e:
            print(f"❌ Error during organization: {e}")
            return ""


def main() -> None:
    """Main entry point for the auto-organizer."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Automatically organize downloaded media files using AI classification",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Downloads Directory: {config.downloads_directory}

Target Directories:
  Movies: {config.movie_directories}
  TV Shows: {config.tv_directories}  
  Documentaries: {config.documentary_directories}
  Stand-ups: {config.standup_directories}

Examples:
  # Dry run (preview mode - default)
  python -m file_managers.plex.utils.auto_organizer
  
  # Actually organize files
  python -m file_managers.plex.utils.auto_organizer --execute
  
  # Verbose output
  python -m file_managers.plex.utils.auto_organizer --verbose
        """
    )
    
    parser.add_argument(
        "--execute",
        action="store_true", 
        help="Actually move files (default: dry run mode)"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output"
    )
    
    args = parser.parse_args()
    
    try:
        organizer = AutoOrganizer(dry_run=not args.execute)
        
        if args.execute:
            print("⚠️  WARNING: Files will be moved to Plex directories!")
            print("⚠️  Make sure you have backups before proceeding!")
            confirm = input("\nType 'ORGANIZE' to proceed: ").strip()
            if confirm != "ORGANIZE":
                print("🚫 Organization cancelled")
                return
        
        report_path = organizer.run_full_organization()
        
        if report_path:
            print(f"\n📄 Detailed report saved to: {report_path}")
        
    except KeyboardInterrupt:
        print("\n👋 Organization cancelled by user")
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()