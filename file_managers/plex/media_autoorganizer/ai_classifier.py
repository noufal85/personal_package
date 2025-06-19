"""AI-Powered Media Classification

This module provides the BedrockClassifier class that uses AWS Bedrock for AI-powered
media file classification. It includes fallback rule-based classification when AI is
unavailable.

Key Features:
- AWS Bedrock integration for AI classification
- Batch processing for efficiency
- Intelligent throttling and retry logic
- Rule-based fallback classification
- Support for multiple AI models (Anthropic, Llama, etc.)
"""

import json
import os
import random
import time
from pathlib import Path
from typing import List

import boto3
from botocore.exceptions import ClientError, NoCredentialsError

from ..config.config import config
from .models import ClassificationResult, MediaType


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


class BedrockClassifier:
    """AI-powered media classification using AWS Bedrock."""
    
    def __init__(self):
        """Initialize the Bedrock classifier."""
        self.region = config.bedrock_region
        self.model_id = config.bedrock_model_id
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self) -> None:
        """Initialize the Bedrock client."""
        try:
            self.client = boto3.client('bedrock-runtime', region_name=self.region)
            # Test the client by making a simple API call
            self._test_model_access()
        except NoCredentialsError:
            print("❌ AWS credentials not configured. Cannot use AI classification.")
            raise RuntimeError("AWS credentials required for AI classification")
        except Exception as e:
            print(f"❌ Failed to initialize Bedrock client: {e}")
            raise RuntimeError(f"Bedrock client initialization failed: {e}")
    
    def _test_model_access(self) -> None:
        """Test if the model is accessible."""
        try:
            # Simple test classification
            test_prompt = "Test filename: example.mkv"
            
            if "anthropic" in self.model_id:
                body = json.dumps({
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 10,
                    "temperature": 0.1,
                    "messages": [{"role": "user", "content": test_prompt}]
                })
            else:
                body = json.dumps({
                    "prompt": test_prompt,
                    "max_gen_len": 10,
                    "temperature": 0.1,
                    "top_p": 0.9
                })
            
            response = self.client.invoke_model(
                body=body,
                modelId=self.model_id,
                accept='application/json',
                contentType='application/json'
            )
            print("✅ Bedrock model access verified")
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            print(f"❌ Model access test failed: {error_code}")
            print(f"   Model ID: {self.model_id}")
            print(f"   Region: {self.region}")
            print(f"   Message: {error_message}")
            
            if error_code == 'AccessDeniedException':
                raise RuntimeError(f"No access to model {self.model_id} in region {self.region}. Check model permissions in AWS Console.")
            elif error_code == 'ValidationException':
                raise RuntimeError(f"Invalid model ID {self.model_id} for region {self.region}")
            else:
                raise RuntimeError(f"Model access failed: {error_message} (Model: {self.model_id}, Region: {self.region})")
        except Exception as e:
            raise RuntimeError(f"Model access test failed: {e} (Model: {self.model_id}, Region: {self.region})")
    
    def classify_batch(self, filenames: List[str], max_retries: int = 3) -> List[ClassificationResult]:
        """
        Classify multiple files in a single batch request for efficiency.
        
        Args:
            filenames: List of filenames to classify
            max_retries: Maximum number of retry attempts
            
        Returns:
            List of ClassificationResult objects
        """
        if not self.client:
            return [self._fallback_classification(filename) for filename in filenames]
        
        batch_prompt = self._create_batch_prompt(filenames)
        
        for attempt in range(max_retries + 1):
            try:
                # Prepare the request body based on model type
                if "anthropic" in self.model_id:
                    body = json.dumps({
                        "anthropic_version": "bedrock-2023-05-31",
                        "max_tokens": config.bedrock_max_tokens * 2,  # More tokens for batch
                        "temperature": config.bedrock_temperature,
                        "messages": [
                            {
                                "role": "user",
                                "content": batch_prompt
                            }
                        ]
                    })
                else:  # Llama or other models
                    body = json.dumps({
                        "prompt": batch_prompt,
                        "max_gen_len": config.bedrock_max_tokens * 2,
                        "temperature": config.bedrock_temperature,
                        "top_p": 0.9
                    })
                
                # Make the API call
                response = self.client.invoke_model(
                    body=body,
                    modelId=self.model_id,
                    accept='application/json',
                    contentType='application/json'
                )
                
                # Parse the response
                response_body = json.loads(response['body'].read())
                if "anthropic" in self.model_id:
                    response_text = response_body['content'][0]['text'].strip()
                else:  # Llama or other models
                    response_text = response_body['generation'].strip()
                
                # Parse batch results
                return self._parse_batch_response(response_text, filenames)
                
            except ClientError as e:
                error_code = e.response['Error']['Code']
                if error_code == 'ThrottlingException' and attempt < max_retries:
                    # Exponential backoff with jitter
                    delay = (2 ** attempt) + random.uniform(0, 1)
                    print(f"⏳ Throttling detected, retrying in {delay:.1f} seconds (attempt {attempt + 1}/{max_retries + 1})")
                    time.sleep(delay)
                    continue
                else:
                    print(f"⚠️ Batch classification failed: {e}")
                    return [self._fallback_classification(filename) for filename in filenames]
            except Exception as e:
                print(f"⚠️ Batch classification error: {e}")
                return [self._fallback_classification(filename) for filename in filenames]
        
        # If all retries failed
        return [self._fallback_classification(filename) for filename in filenames]
    
    def _create_batch_prompt(self, filenames: List[str]) -> str:
        """Create a batch classification prompt."""
        files_list = "\n".join([f"{i+1}. {filename}" for i, filename in enumerate(filenames)])
        
        prompt = f"""Analyze the following {len(filenames)} filenames and classify each as one of these media types:
- MOVIE: Feature films, movies
- TV: TV series episodes, shows  
- DOCUMENTARY: Documentary films or series
- STANDUP: Stand-up comedy specials
- AUDIOBOOK: Audio books
- OTHER: Anything else

Files to classify:
{files_list}

Respond with a JSON array containing the classification for each file in order. Each entry should have "filename" and "type" fields.

Example response format:
[
  {{"filename": "The.Dark.Knight.2008.1080p.BluRay.mkv", "type": "MOVIE"}},
  {{"filename": "Game.of.Thrones.S01E01.720p.HDTV.mkv", "type": "TV"}},
  {{"filename": "Planet.Earth.Documentary.2006.1080p.mkv", "type": "DOCUMENTARY"}}
]

Response:"""
        return prompt
    
    def _parse_batch_response(self, response_text: str, filenames: List[str]) -> List[ClassificationResult]:
        """Parse the batch response JSON."""
        try:
            # Try to extract JSON from response
            json_start = response_text.find('[')
            json_end = response_text.rfind(']') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_text = response_text[json_start:json_end]
                classifications = json.loads(json_text)
                
                results = []
                for i, filename in enumerate(filenames):
                    if i < len(classifications):
                        try:
                            media_type_str = classifications[i].get('type', 'MOVIE').upper()
                            media_type = MediaType(media_type_str)
                            results.append(ClassificationResult(media_type=media_type, confidence=0.8))
                        except (ValueError, KeyError):
                            results.append(self._fallback_classification(filename))
                    else:
                        results.append(self._fallback_classification(filename))
                
                return results
            else:
                raise ValueError("No JSON array found in response")
                
        except (json.JSONDecodeError, ValueError, KeyError) as e:
            print(f"⚠️ Failed to parse batch response: {e}")
            # Fallback to individual classification
            return [self._fallback_classification(filename) for filename in filenames]
    
    def classify_file(self, filename: str) -> ClassificationResult:
        """
        Classify a single media file using AI.
        
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
            error_code = e.response['Error']['Code']
            if error_code == 'ThrottlingException':
                print(f"⚠️  Throttling detected for {filename}, using fallback classification")
                # Use fallback instead of retrying to avoid further throttling
                return self._fallback_classification(filename)
            else:
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