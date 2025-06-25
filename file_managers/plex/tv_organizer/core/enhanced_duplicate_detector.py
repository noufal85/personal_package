"""
Enhanced Duplicate Detection for TV File Organizer

Addresses issues with false positive duplicate detection by implementing:
1. Content-based differentiation (different episode titles)
2. Version detection (files with _1, _2 suffixes)
3. Better filename parsing for complex patterns
4. Confidence scoring for duplicate detection
"""

import re
import logging
from pathlib import Path
from typing import List, Dict, Set, Optional, Tuple
from collections import defaultdict

from ..models.episode import Episode, Quality, EpisodeStatus
from ..models.duplicate import DuplicateGroup, DuplicateAction
from .duplicate_detector import DuplicateDetector


class EnhancedDuplicateDetector(DuplicateDetector):
    """
    Enhanced duplicate detector that reduces false positives by considering
    episode content and filename patterns.
    """
    
    def __init__(self, tv_directories: Optional[List[str]] = None):
        """Initialize the enhanced duplicate detector."""
        super().__init__(tv_directories)
        
        # Patterns for detecting file versions (true duplicates)
        self.version_patterns = [
            r'_(\d+)\.(?:mkv|mp4|avi)$',  # filename_1.mkv, filename_2.mkv
            r'_(\d+)$',                    # filename_1, filename_2
            r'\((\d+)\)\.(?:mkv|mp4|avi)$', # filename(1).mkv, filename(2).mkv
            r'\((\d+)\)$',                 # filename(1), filename(2)
            r'\.(\d+)\.(?:mkv|mp4|avi)$',  # filename.1.mkv, filename.2.mkv
        ]
        
        # Patterns for multi-episode files (should not be duplicates)
        self.multi_episode_patterns = [
            r'S\d+E\d+.*S\d+E\d+',        # S01E01-S01E02, S01E01 S01E02
            r'E\d+-E\d+',                 # E01-E02
            r'Episodes?\s+\d+-\d+',       # Episodes 1-2
        ]
        
        # Words that indicate different content (not duplicates)
        self.content_differentiators = {
            # Geographic/location terms
            'alaska', 'boston', 'dubai', 'tokyo', 'hong kong', 'iceland', 'venice',
            'transatlantic', 'panama', 'gotthard', 'cooper river', 'oakland',
            
            # Engineering/construction terms  
            'tunnel', 'bridge', 'airport', 'stadium', 'platform', 'excavator',
            'dam', 'cable car', 'subway', 'pyramid', 'resort', 'barriers',
            
            # Generic differentiators
            'part 1', 'part 2', 'part i', 'part ii', 'chapter', 'volume',
            'disc 1', 'disc 2', 'cd1', 'cd2'
        }
    
    def _extract_content_signature(self, filename: str) -> str:
        """
        Extract a content signature from filename to detect different episodes.
        
        Args:
            filename: The filename to analyze
            
        Returns:
            Content signature for comparison
        """
        # Remove common prefixes and suffixes
        content = filename.lower()
        
        # Remove file extension
        content = Path(content).stem
        
        # Remove version indicators
        for pattern in self.version_patterns:
            content = re.sub(pattern, '', content)
        
        # Remove quality indicators
        quality_terms = ['720p', '1080p', '4k', 'hdtv', 'webrip', 'bluray', 'x264', 'x265', 'hevc']
        for term in quality_terms:
            content = content.replace(term, '')
        
        # Remove common separators and normalize
        content = re.sub(r'[._-]+', ' ', content)
        content = ' '.join(content.split())  # Normalize whitespace
        
        return content
    
    def _detect_file_version(self, filename: str) -> Optional[int]:
        """
        Detect if this filename has a version number (indicating true duplicate).
        
        Args:
            filename: The filename to analyze
            
        Returns:
            Version number if detected, None otherwise
        """
        for pattern in self.version_patterns:
            match = re.search(pattern, filename.lower())
            if match:
                return int(match.group(1))
        return None
    
    def _is_multi_episode_file(self, filename: str) -> bool:
        """
        Check if this filename represents multiple episodes.
        
        Args:
            filename: The filename to analyze
            
        Returns:
            True if this appears to be a multi-episode file
        """
        for pattern in self.multi_episode_patterns:
            if re.search(pattern, filename, re.IGNORECASE):
                return True
        return False
    
    def _has_content_differences(self, filenames: List[str]) -> bool:
        """
        Check if filenames have significant content differences.
        
        Args:
            filenames: List of filenames to compare
            
        Returns:
            True if files have different content (not duplicates)
        """
        if len(filenames) < 2:
            return False
        
        content_signatures = [self._extract_content_signature(f) for f in filenames]
        
        # Check for content differentiator words
        for signature in content_signatures:
            words = set(signature.split())
            if any(diff in words for diff in self.content_differentiators):
                # If any file has differentiator words, check if others do too
                other_signatures = [s for s in content_signatures if s != signature]
                for other in other_signatures:
                    other_words = set(other.split())
                    # If one has differentiators and another doesn't, they're different
                    if not any(diff in other_words for diff in self.content_differentiators):
                        return True
                    # If they have different differentiators, they're different
                    signature_diffs = words & self.content_differentiators
                    other_diffs = other_words & self.content_differentiators
                    if signature_diffs != other_diffs:
                        return True
        
        # Check for significantly different content signatures
        unique_signatures = set(content_signatures)
        if len(unique_signatures) > 1:
            # Calculate similarity between signatures
            for i, sig1 in enumerate(content_signatures):
                for sig2 in content_signatures[i+1:]:
                    words1 = set(sig1.split())
                    words2 = set(sig2.split())
                    
                    if not words1 or not words2:
                        continue
                    
                    # Jaccard similarity
                    intersection = len(words1 & words2)
                    union = len(words1 | words2)
                    similarity = intersection / union if union > 0 else 0
                    
                    # If similarity is very low, these are different episodes
                    if similarity < 0.3:
                        return True
        
        return False
    
    def detect_duplicates(self) -> List[DuplicateGroup]:
        """
        Enhanced duplicate detection with content analysis.
        
        Returns:
            List of duplicate groups with reduced false positives
        """
        if not self.episodes:
            self.logger.warning("No episodes loaded. Run scan_all_directories() first.")
            return []
        
        self.logger.info("Detecting duplicates with enhanced analysis...")
        
        # Group episodes by show/season/episode (initial grouping)
        episode_groups = defaultdict(list)
        
        for episode in self.episodes:
            episode_id = episode.episode_id
            episode_groups[episode_id].append(episode)
        
        # Filter out false positives and create duplicate groups
        self.duplicate_groups.clear()
        total_groups_checked = 0
        false_positives_filtered = 0
        
        for episode_id, episodes in episode_groups.items():
            total_groups_checked += 1
            
            if len(episodes) < 2:
                continue  # No duplicates
            
            # Extract filenames for analysis
            filenames = [ep.filename for ep in episodes]
            
            # Check for multi-episode files (not duplicates)
            if any(self._is_multi_episode_file(f) for f in filenames):
                self.logger.debug(f"Skipping multi-episode file group: {episode_id}")
                false_positives_filtered += 1
                continue
            
            # Check for content differences (not duplicates)
            if self._has_content_differences(filenames):
                self.logger.debug(f"Skipping content-different group: {episode_id}")
                false_positives_filtered += 1
                continue
            
            # Check for version files (true duplicates)
            versions = [self._detect_file_version(f) for f in filenames]
            has_versions = any(v is not None for v in versions)
            
            if has_versions:
                self.logger.debug(f"Confirmed version duplicates: {episode_id}")
            
            # Create duplicate group for confirmed duplicates
            first_episode = episodes[0]
            duplicate_group = DuplicateGroup(
                show_name=first_episode.show_name,
                season=first_episode.season,
                episode=first_episode.episode,
                episodes=episodes
            )
            
            # Enhanced analysis
            duplicate_group.analyze_duplicates()
            
            # Add metadata about detection confidence
            confidence_score = self._calculate_confidence_score(episodes, has_versions)
            duplicate_group.metadata['confidence_score'] = confidence_score
            duplicate_group.metadata['has_version_files'] = has_versions
            duplicate_group.metadata['analysis_method'] = 'enhanced'
            
            if confidence_score >= 0.7:  # Only include high-confidence duplicates
                self.duplicate_groups.append(duplicate_group)
            else:
                self.logger.debug(f"Low confidence duplicate filtered: {episode_id} (score: {confidence_score:.2f})")
                false_positives_filtered += 1
        
        self.logger.info(f"Enhanced duplicate detection complete:")
        self.logger.info(f"  Total groups checked: {total_groups_checked}")
        self.logger.info(f"  False positives filtered: {false_positives_filtered}")
        self.logger.info(f"  High-confidence duplicates: {len(self.duplicate_groups)}")
        
        return self.duplicate_groups
    
    def _calculate_confidence_score(self, episodes: List[Episode], has_versions: bool) -> float:
        """
        Calculate confidence score for duplicate detection.
        
        Args:
            episodes: List of episodes in the group
            has_versions: Whether version files were detected
            
        Returns:
            Confidence score between 0.0 and 1.0
        """
        score = 0.0
        
        # Base score for having multiple files
        score += 0.3
        
        # High score for version files
        if has_versions:
            score += 0.5
        
        # Score based on filename similarity
        filenames = [ep.filename for ep in episodes]
        if len(filenames) >= 2:
            # Calculate average filename similarity
            similarities = []
            for i, f1 in enumerate(filenames):
                for f2 in filenames[i+1:]:
                    sig1 = self._extract_content_signature(f1)
                    sig2 = self._extract_content_signature(f2)
                    words1 = set(sig1.split())
                    words2 = set(sig2.split())
                    
                    if words1 and words2:
                        intersection = len(words1 & words2)
                        union = len(words1 | words2)
                        similarity = intersection / union if union > 0 else 0
                        similarities.append(similarity)
            
            if similarities:
                avg_similarity = sum(similarities) / len(similarities)
                score += avg_similarity * 0.3
        
        # Score based on file sizes (similar sizes = more likely duplicates)
        sizes = [ep.file_size for ep in episodes]
        if len(sizes) >= 2:
            size_variance = max(sizes) / min(sizes) if min(sizes) > 0 else 1
            # Lower variance = higher score
            size_score = 1.0 / size_variance if size_variance > 1 else 1.0
            score += size_score * 0.2
        
        return min(score, 1.0)  # Cap at 1.0
    
    def generate_enhanced_report(self) -> str:
        """
        Generate enhanced duplicate detection report with confidence scores.
        
        Returns:
            Formatted report string with confidence information
        """
        if not self.duplicate_groups:
            return "No high-confidence duplicates detected."
        
        # Get statistics
        stats = self.get_duplicate_statistics()
        
        report = []
        report.append("ENHANCED TV EPISODE DUPLICATE DETECTION REPORT")
        report.append("=" * 55)
        report.append("")
        
        # Summary statistics
        report.append("SUMMARY:")
        report.append(f"  Total Episodes Scanned: {len(self.episodes)}")
        report.append(f"  High-Confidence Duplicate Groups: {stats['total_duplicate_groups']}")
        report.append(f"  Total Duplicate Files: {stats['total_duplicate_files']}")
        report.append(f"  Space Used by Duplicates: {stats['total_space_used_gb']:.2f} GB")
        report.append(f"  Potential Space Savings: {stats['potential_space_saved_gb']:.2f} GB")
        report.append(f"  Space Efficiency Gain: {stats['space_efficiency']:.1f}%")
        report.append("")
        
        # Filter information
        report.append("ENHANCED FILTERING:")
        report.append("  ✅ Multi-episode files excluded")
        report.append("  ✅ Content-different files excluded")
        report.append("  ✅ Low-confidence matches excluded")
        report.append("  ✅ Version files prioritized")
        report.append("")
        
        # Detailed duplicate groups
        report.append("HIGH-CONFIDENCE DUPLICATE GROUPS:")
        report.append("-" * 40)
        
        # Sort by confidence score (highest first)
        sorted_groups = sorted(
            self.duplicate_groups,
            key=lambda g: g.metadata.get('confidence_score', 0),
            reverse=True
        )
        
        for i, group in enumerate(sorted_groups, 1):
            confidence = group.metadata.get('confidence_score', 0)
            has_versions = group.metadata.get('has_version_files', False)
            
            report.append(f"\n{i}. {group.get_summary()}")
            report.append(f"   Confidence: {confidence:.2f} {'(Version Files)' if has_versions else ''}")
            report.append(f"   Action: {group.recommended_action.value}")
            
            if group.recommended_keeper:
                report.append(f"   Keep: {group.recommended_keeper.filename}")
                report.append(f"         ({group.recommended_keeper.quality.value}, "
                            f"{group.recommended_keeper.size_mb:.1f}MB)")
            
            if group.recommended_removals:
                report.append("   Remove:")
                for episode in group.recommended_removals:
                    version = self._detect_file_version(episode.filename)
                    version_text = f" (v{version})" if version else ""
                    report.append(f"     - {episode.filename}{version_text}")
                    report.append(f"       ({episode.quality.value}, {episode.size_mb:.1f}MB)")
            
            if group.analysis_notes:
                report.append("   Notes:")
                for note in group.analysis_notes:
                    report.append(f"     • {note}")
        
        return "\n".join(report)