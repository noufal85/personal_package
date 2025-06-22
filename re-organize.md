# Media Re-Organization Tool Implementation Plan

## Overview

A utility to identify misplaced media files in Plex directories and generate actionable reports showing where files should be correctly placed. Uses existing media database and AWS Bedrock LLM for intelligent analysis.

## Objectives

- **Single-use utility**: Not designed for repeated use, focused on solving current misplaced content issues
- **Leverage existing infrastructure**: Reuse media database, AWS Bedrock integration, and report generation
- **Actionable intelligence**: Generate clear reports showing source → target mappings
- **Safe operation**: Analysis-only tool with no file movement capabilities

## Architecture & Reusable Components

### Core Dependencies
```python
# Database & Configuration
from file_managers.plex.utils.media_database import MediaDatabase
from file_managers.plex.config.config import config

# AI Processing
from file_managers.plex.media_autoorganizer.ai_classifier import BedrockClassifier

# File Scanning
from file_managers.plex.utils.movie_scanner import scan_directory_for_movies
from file_managers.plex.utils.tv_scanner import scan_directory_for_tv_episodes

# Report Generation
from file_managers.plex.utils.report_generator import get_reports_directory, generate_timestamp

# Data Models
from file_managers.plex.media_autoorganizer.models import MediaType, MediaFile
```

### Key Reusable Components

1. **MediaDatabase** (`file_managers/plex/utils/media_database.py`)
   - Existing database interface with rebuild capability
   - Methods: `rebuild_database()`, `get_all_movies()`, `get_all_tv_episodes()`

2. **BedrockClassifier** (`file_managers/plex/media_autoorganizer/ai_classifier.py`)
   - Batch LLM processing with `classify_batch(filenames)`
   - AWS Bedrock integration already configured

3. **Report Generators** (`file_managers/plex/utils/report_generator.py`)
   - Templates for text and JSON report generation
   - Consistent formatting and directory management

4. **File Scanners** (`file_managers/plex/utils/movie_scanner.py`, `tv_scanner.py`)
   - Robust directory scanning with metadata extraction
   - File normalization and categorization

## Implementation Phases

## Phase 1: Core Framework Setup
**Duration**: 2-3 hours
**Status**: Foundation Development

### Deliverables
- [ ] Create main tool class `MediaReorganizationAnalyzer`
- [ ] Implement database initialization with rebuild flag support
- [ ] Setup directory scanning across all configured media paths
- [ ] Establish basic file collection and metadata extraction

### Key Tasks
1. **Tool Structure**
   ```python
   class MediaReorganizationAnalyzer:
       def __init__(self, rebuild_db=False):
           self.media_db = MediaDatabase()
           self.classifier = BedrockClassifier()
           self.config = config
   ```

2. **Directory Scanning**
   - Collect files from all movie, TV, documentary, and standup directories
   - Extract metadata using existing scanner utilities
   - Build comprehensive file inventory

3. **Database Integration**
   - Optional database rebuild with `--rebuild-db` flag
   - Load existing media database for reference comparison

### Success Criteria
- Tool can scan all configured directories
- Database loads successfully (with optional rebuild)
- File inventory is collected with proper metadata

---

## Phase 2: LLM Analysis Engine
**Duration**: 3-4 hours
**Status**: AI Integration

### Deliverables
- [ ] Implement batch LLM processing for misplaced file detection
- [ ] Create intelligent prompts for media categorization analysis
- [ ] Develop logic to compare current vs. ideal file placements
- [ ] Handle LLM response parsing and validation

### Key Tasks
1. **Batch Processing Setup**
   ```python
   def analyze_file_placements(self, files):
       # Extract filenames for LLM analysis
       filenames = [f.name for f in files]
       
       # Batch classify with custom prompt for reorganization
       classifications = self.classifier.classify_batch(
           filenames, 
           custom_prompt=self._create_reorganization_prompt()
       )
   ```

2. **Custom LLM Prompts**
   - Design prompts specifically for misplacement detection
   - Include context about existing directory structure
   - Request structured responses for automated parsing

3. **Analysis Logic**
   - Compare current file locations with LLM suggestions
   - Identify files in wrong directories or incorrectly categorized
   - Cross-reference with existing media database entries

4. **Response Processing**
   - Parse LLM JSON responses for reorganization suggestions
   - Validate suggestions against actual directory structure
   - Handle edge cases and parsing errors

### Success Criteria
- LLM successfully analyzes file batches
- Misplaced files are accurately identified
- Suggestions are validated and actionable

---

## Phase 3: Intelligent Analysis & Matching
**Duration**: 2-3 hours
**Status**: Logic Implementation

### Deliverables
- [ ] Implement misplacement detection algorithms
- [ ] Create directory matching and suggestion logic
- [ ] Develop confidence scoring for reorganization recommendations
- [ ] Handle special cases and edge scenarios

### Key Tasks
1. **Misplacement Detection**
   ```python
   def detect_misplaced_files(self, files, llm_classifications):
       misplaced = []
       for file, classification in zip(files, llm_classifications):
           current_location = self._categorize_current_location(file.path)
           suggested_location = classification.media_type
           
           if current_location != suggested_location:
               misplaced.append(MisplacedFile(file, current_location, suggested_location))
   ```

2. **Directory Matching**
   - Map current file locations to media type categories
   - Suggest specific target directories based on content type
   - Handle multiple valid destination options

3. **Confidence Scoring**
   - Assign confidence levels to reorganization suggestions
   - Factor in LLM confidence, filename clarity, and existing patterns
   - Flag uncertain cases for manual review

4. **Special Case Handling**
   - Multi-part movies split across directories
   - TV shows with scattered seasons
   - Duplicate content in multiple locations
   - Files with ambiguous naming

### Success Criteria
- Accurate misplacement detection with minimal false positives
- Sensible directory suggestions with confidence scores
- Special cases are handled gracefully

---

## Phase 4: Report Generation System
**Duration**: 2-3 hours
**Status**: Output Implementation

### Deliverables
- [ ] Generate comprehensive text reports for human review
- [ ] Create structured JSON reports for potential automation
- [ ] Implement summary statistics and impact analysis
- [ ] Design actionable file movement recommendations

### Key Tasks
1. **Text Report Generation**
   ```python
   def generate_reorganization_report(self, misplaced_files):
       timestamp = generate_timestamp()
       report_path = get_reports_directory() / f"media_reorganization_{timestamp}.txt"
       
       # Generate human-readable report with sections:
       # - Executive Summary
       # - Misplaced Files by Category
       # - Recommended Actions
       # - Impact Analysis
   ```

2. **Report Sections**
   - **Executive Summary**: Total files analyzed, misplaced count, space impact
   - **Detailed Findings**: File-by-file source → target mappings
   - **Category Analysis**: Misplacements grouped by media type
   - **Action Items**: Prioritized list of reorganization tasks

3. **JSON Report Structure**
   ```json
   {
     "analysis_timestamp": "2025-01-21T10:30:00",
     "summary": {
       "total_files": 15420,
       "misplaced_files": 342,
       "categories_affected": ["movies", "tv", "documentaries"]
     },
     "misplaced_files": [
       {
         "source_path": "/mnt/qnap/plex/Movie/Breaking Bad S01E01.mkv",
         "target_category": "tv",
         "suggested_path": "/mnt/qnap/plex/TV/Breaking Bad/Season 01/",
         "confidence": 0.95,
         "file_size": "1.2GB"
       }
     ],
     "recommendations": [...] 
   }
   ```

4. **Impact Analysis**
   - Calculate total space involved in reorganization
   - Estimate time required for manual reorganization
   - Identify high-impact quick wins

### Success Criteria
- Reports are clear, actionable, and well-organized
- JSON format enables potential future automation
- Summary statistics provide project scope understanding

---

## Phase 5: CLI Interface & Integration
**Duration**: 1-2 hours
**Status**: User Interface

### Deliverables
- [ ] Create command-line interface with proper argument handling
- [ ] Integrate with existing CLI structure and conventions
- [ ] Implement progress indicators and status reporting
- [ ] Add validation and error handling

### Key Tasks
1. **CLI Implementation**
   ```python
   # file_managers/plex/utils/media_reorganizer.py
   def main():
       parser = argparse.ArgumentParser(description="Analyze misplaced media files")
       parser.add_argument('--rebuild-db', action='store_true', 
                          help='Rebuild media database before analysis')
       parser.add_argument('--output-format', choices=['text', 'json', 'both'],
                          default='both', help='Report output format')
       parser.add_argument('--confidence-threshold', type=float, default=0.7,
                          help='Minimum confidence for suggestions')
   ```

2. **Progress Reporting**
   - Directory scanning progress
   - LLM batch processing status
   - Report generation updates

3. **Error Handling**
   - Network mount accessibility checks
   - AWS Bedrock connectivity validation
   - Graceful degradation for partial failures

4. **Integration Points**
   - Follow existing module patterns
   - Use consistent configuration management
   - Maintain compatibility with existing utilities

### Success Criteria
- CLI is intuitive and follows project conventions
- Progress feedback keeps users informed
- Errors are handled gracefully with helpful messages

---

## Usage Examples

### Basic Analysis
```bash
# Standard analysis with existing database
python -m file_managers.plex.utils.media_reorganizer

# Analysis with fresh database rebuild
python -m file_managers.plex.utils.media_reorganizer --rebuild-db

# Generate only JSON report
python -m file_managers.plex.utils.media_reorganizer --output-format json
```

### Expected Output Structure
```
Media Reorganization Analysis Report
====================================
Generated: 2025-01-21 10:30:15

EXECUTIVE SUMMARY
-----------------
Total Files Analyzed: 15,420
Misplaced Files Found: 342 (2.2%)
Categories Affected: Movies, TV Shows, Documentaries
Estimated Reorganization Impact: 2.1TB

CRITICAL MISPLACEMENTS (High Confidence)
----------------------------------------
[TV] Breaking Bad Season 1-5 episodes in Movie directory
  Source: /mnt/qnap/plex/Movie/Breaking Bad/
  Target: /mnt/qnap/plex/TV/Breaking Bad/
  Impact: 156 files, 85GB

[MOVIES] Individual movie files scattered in TV directories
  Source: /mnt/qnap/plex/TV/Inception (2010).mkv
  Target: /mnt/qnap/plex/Movie/Inception (2010)/
  Impact: 23 files, 47GB

DETAILED RECOMMENDATIONS
------------------------
[List of specific file movements with confidence scores]

SUMMARY ACTIONS
---------------
1. Move 156 Breaking Bad episodes to TV directory
2. Relocate 23 individual movies from TV to Movie directories
3. Review 12 uncertain classifications manually
4. Consolidate 8 duplicate movie folders

Reports saved to: reports/media_reorganization_20250121_103015.txt|.json
```

## File Structure

```
file_managers/plex/utils/
└── media_reorganizer.py          # Main reorganization tool
    ├── MediaReorganizationAnalyzer  # Core analysis class
    ├── MisplacedFile               # Data structure for findings
    ├── ReorganizationReport        # Report generation class
    └── main()                      # CLI entry point
```

## Success Metrics

- **Accuracy**: >95% of identified misplacements are legitimate
- **Coverage**: Analyzes all configured media directories
- **Performance**: Processes 15,000+ files within 10 minutes
- **Usability**: Generates actionable reports requiring minimal interpretation
- **Reliability**: Handles network mount issues and LLM failures gracefully

## Risk Mitigation

1. **Analysis-Only Operation**: Tool only generates reports, never moves files
2. **Confidence Scoring**: Low-confidence suggestions flagged for manual review
3. **Existing Component Reuse**: Leverages battle-tested code for core operations
4. **Comprehensive Logging**: Detailed logs for troubleshooting and audit trails
5. **Graceful Degradation**: Continues operation even with partial directory access

## Future Considerations

While this is designed as a one-time utility, the framework could be extended for:
- Automated reorganization with user approval workflows
- Continuous monitoring for new misplaced files
- Integration with Plex library management APIs
- Advanced ML models for better categorization accuracy

---

**Implementation Timeline**: 10-15 hours total development time
**Primary Developer**: Single developer implementation
**Dependencies**: Existing codebase components, AWS Bedrock access
**Deliverable**: Complete reorganization analysis tool with comprehensive reports