"""
OpenAI-based Media Classification

This module provides the OpenAIClassifier class that uses OpenAI's API for AI-powered
media file classification. It serves as a replacement for AWS Bedrock with better
batch processing and more reliable classification results.

Key Features:
- OpenAI GPT-4 integration for accurate classification
- Efficient batch processing with title grouping
- Robust error handling and retry logic
- Support for documentaries, stand-up comedy, and edge cases
- Fallback rule-based classification
"""

import json
import os
import time
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import openai
from openai import OpenAI

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


class OpenAIClassifier:
    """AI-powered media classification using OpenAI's API."""
    
    def __init__(self):
        """Initialize the OpenAI classifier."""
        self.api_key = os.getenv('OPENAI_API_KEY')
        self.model = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')
        self.client = None
        
        if self.api_key:
            try:
                self.client = OpenAI(api_key=self.api_key)
                print("✅ OpenAI client initialized successfully")
                # Test the connection
                self._test_connection()
            except Exception as e:
                print(f"❌ Failed to initialize OpenAI client: {e}")
                self.client = None
        else:
            print("⚠️  OPENAI_API_KEY not found in environment variables")
    
    def _test_connection(self):
        """Test the OpenAI API connection."""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "Test"}],
                max_tokens=5
            )
            print(f"✅ OpenAI API connection verified (model: {self.model})")
        except Exception as e:
            print(f"❌ OpenAI API test failed: {e}")
            self.client = None
    
    def classify_batch(self, filenames: List[str], max_retries: int = 3) -> List[Optional[Dict]]:
        """
        Classify multiple files in a single batch request for efficiency.
        
        Args:
            filenames: List of filenames to classify
            max_retries: Maximum number of retry attempts
            
        Returns:
            List of classification dictionaries with category, confidence, reasoning
        """
        if not self.client:
            print("   ⚠️  OpenAI client not available, using rule-based fallback")
            return [None] * len(filenames)
        
        # Group filenames by likely titles for better batching
        grouped_files = self._group_files_by_title(filenames)
        
        all_results = []
        
        for group_title, file_list in grouped_files.items():
            print(f"   🤖 Classifying group: {group_title} ({len(file_list)} files)")
            
            # Create batch prompt for this group
            batch_prompt = self._create_batch_prompt(file_list)
            
            # Attempt classification with retries
            for attempt in range(max_retries + 1):
                try:
                    response = self.client.chat.completions.create(
                        model=self.model,
                        messages=[
                            {"role": "system", "content": "You are an expert media file classifier for Plex media servers. Analyze filenames and classify them accurately."},
                            {"role": "user", "content": batch_prompt}
                        ],
                        max_tokens=4000,
                        temperature=0.1  # Low temperature for consistent results
                    )
                    
                    # Parse the response
                    response_text = response.choices[0].message.content
                    group_results = self._parse_batch_response(response_text, file_list)
                    all_results.extend(group_results)
                    break
                    
                except Exception as e:
                    if attempt < max_retries:
                        wait_time = (2 ** attempt) + (0.1 * (attempt + 1))
                        print(f"   ⚠️  Attempt {attempt + 1} failed, retrying in {wait_time:.1f}s: {e}")
                        time.sleep(wait_time)
                    else:
                        print(f"   ❌ All attempts failed for group {group_title}: {e}")
                        # Add None results for this group
                        all_results.extend([None] * len(file_list))
        
        return all_results
    
    def _group_files_by_title(self, filenames: List[str]) -> Dict[str, List[str]]:
        """Group filenames by likely series/movie titles for better batch processing."""
        groups = {}
        
        for filename in filenames:
            # Extract likely title from filename
            title = self._extract_title(filename)
            
            if title not in groups:
                groups[title] = []
            groups[title].append(filename)
        
        return groups
    
    def _extract_title(self, filename: str) -> str:
        """Extract the likely title from a filename for grouping."""
        # Remove file extension
        name = filename.lower().replace('.mkv', '').replace('.mp4', '').replace('.avi', '')
        
        # Common patterns to identify title boundaries
        separators = [
            ' s0', ' s1', ' s2', ' s3', ' s4', ' s5',  # Season indicators
            ' (19', ' (20',  # Year indicators
            ' 1080p', ' 720p', ' 480p',  # Quality indicators
            ' bluray', ' webrip', ' hdtv', ' dvdrip',  # Source indicators
            ' x264', ' x265', ' xvid'  # Codec indicators
        ]
        
        # Find the first separator to identify where title likely ends
        min_pos = len(name)
        for sep in separators:
            pos = name.find(sep)
            if pos != -1 and pos < min_pos:
                min_pos = pos
        
        # Extract title up to the separator
        title = name[:min_pos] if min_pos < len(name) else name
        
        # Clean up the title
        title = title.replace('.', ' ').replace('_', ' ').replace('-', ' ')
        title = ' '.join(title.split())  # Normalize whitespace
        
        return title[:50] if title else "unknown"  # Limit length
    
    def _create_batch_prompt(self, filenames: List[str]) -> str:
        """Create a batch classification prompt for a group of related files."""
        files_list = "\n".join([f"{i+1}. {filename}" for i, filename in enumerate(filenames)])
        
        prompt = f"""Analyze the following {len(filenames)} media filenames and classify each into the correct category for a Plex media server.

Categories:
- MOVIE: Feature films, individual movies
- TV: TV series episodes, shows (any episode format like S01E01, 1x01, etc.)
- DOCUMENTARY: Documentary films or documentary series (educational content)
- STANDUP: Stand-up comedy specials and comedy shows

Files to classify:
{files_list}

For each file, determine:
1. The correct category based on filename patterns and content clues
2. Confidence level (0.5-1.0) based on how certain you are
3. Brief reasoning for the classification

Respond with a JSON array containing exactly {len(filenames)} entries in the same order as the input files.

Example response format:
[
  {{"filename": "The.Dark.Knight.2008.1080p.BluRay.mkv", "category": "MOVIE", "confidence": 0.9, "reasoning": "Movie title with year indicator"}},
  {{"filename": "Game.of.Thrones.S01E01.720p.HDTV.mkv", "category": "TV", "confidence": 0.95, "reasoning": "TV series with S01E01 episode format"}},
  {{"filename": "Planet.Earth.Documentary.2006.1080p.mkv", "category": "DOCUMENTARY", "confidence": 0.9, "reasoning": "Educational documentary content"}}
]

Pay special attention to:
- TV episodes that might be misplaced in movie folders
- Movies that might be in TV folders
- Documentary content (often has educational keywords, nature themes, historical content)
- Stand-up comedy specials vs regular TV shows
- Multi-part movies vs TV episodes

Response (JSON array only):"""
        
        return prompt
    
    def _parse_batch_response(self, response_text: str, filenames: List[str]) -> List[Optional[Dict]]:
        """Parse the batch response JSON."""
        try:
            # Clean up response text - sometimes there's extra text before/after JSON
            response_text = response_text.strip()
            
            # Find JSON array in the response
            start_idx = response_text.find('[')
            end_idx = response_text.rfind(']') + 1
            
            if start_idx == -1 or end_idx == 0:
                raise ValueError("No JSON array found in response")
            
            json_text = response_text[start_idx:end_idx]
            results = json.loads(json_text)
            
            # Validate and convert results
            parsed_results = []
            for i, result in enumerate(results):
                if i >= len(filenames):
                    break
                    
                if isinstance(result, dict):
                    category = result.get('category', '').upper()
                    confidence = float(result.get('confidence', 0.7))
                    reasoning = result.get('reasoning', 'AI classification')
                    
                    # Validate category
                    valid_categories = ['MOVIE', 'TV', 'DOCUMENTARY', 'STANDUP']
                    if category not in valid_categories:
                        category = 'MOVIE'  # Default fallback
                    
                    # Ensure confidence is in valid range
                    confidence = max(0.5, min(1.0, confidence))
                    
                    parsed_results.append({
                        'category': category.lower(),
                        'confidence': confidence,
                        'reasoning': reasoning
                    })
                else:
                    parsed_results.append(None)
            
            # Ensure we have results for all input files
            while len(parsed_results) < len(filenames):
                parsed_results.append(None)
            
            return parsed_results[:len(filenames)]
            
        except Exception as e:
            print(f"   ❌ Failed to parse batch response: {e}")
            print(f"   Response text: {response_text[:200]}...")
            return [None] * len(filenames)
    
    def classify_single(self, filename: str) -> Optional[Dict]:
        """Classify a single file (convenience method)."""
        results = self.classify_batch([filename])
        return results[0] if results else None


def test_classifier():
    """Test the OpenAI classifier with sample filenames."""
    classifier = OpenAIClassifier()
    
    test_files = [
        "The.Dark.Knight.2008.1080p.BluRay.x264.mkv",
        "Game.of.Thrones.S01E01.Winter.Is.Coming.720p.HDTV.mkv",
        "Planet.Earth.Documentary.2006.1080p.BluRay.mkv",
        "Dave.Chappelle.Sticks.and.Stones.2019.1080p.NF.WEB-DL.mkv",
        "Breaking.Bad.S01E02.Cat.in.the.Bag.720p.BluRay.mkv"
    ]
    
    print("Testing OpenAI classifier...")
    results = classifier.classify_batch(test_files)
    
    for filename, result in zip(test_files, results):
        if result:
            print(f"✅ {filename}")
            print(f"   Category: {result['category']}")
            print(f"   Confidence: {result['confidence']}")
            print(f"   Reasoning: {result['reasoning']}")
        else:
            print(f"❌ {filename} - Classification failed")
        print()


if __name__ == "__main__":
    test_classifier()