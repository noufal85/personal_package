# Media Re-Organization Tool Implementation Plan

## 🎯 **Project Overview**

**Status**: Ready for Implementation  
**Priority**: Phase 4 Enhancement  
**Integration**: Unified CLI Extension  
**Timeline**: 10-15 hours development time  

### **Objective**
Implement a comprehensive media reorganization analysis tool that identifies misplaced files across Plex directories and generates actionable reports for manual correction. This tool will be integrated into the existing unified CLI system as `plex-cli files reorganize`.

---

## 📋 **Requirements Analysis**

### **Core Requirements**
1. **Analysis-Only Operation**: No file movement, only reporting
2. **AI-Powered Detection**: Use AWS Bedrock for intelligent classification
3. **Comprehensive Reporting**: Both human-readable and machine-readable formats
4. **CLI Integration**: Seamless integration with existing `plex-cli` interface
5. **Existing Component Reuse**: Leverage current infrastructure maximally

### **Technical Requirements**
- **Database Integration**: Use existing MediaDatabase with optional rebuild
- **AI Classification**: Reuse BedrockClassifier for batch processing
- **Report Generation**: Consistent with existing report formats
- **Configuration**: Use existing media_config.yaml structure
- **Error Handling**: Robust handling of network/API failures

### **User Experience Requirements**
- **Interactive Mode**: Menu-driven interface for ease of use
- **Direct Commands**: Power user command-line interface
- **Progress Feedback**: Real-time progress indicators for long operations
- **Clear Output**: Actionable reports with confidence scores

---

## 🏗️ **Architecture & Integration Design**

### **Integration with Unified CLI**

#### **Command Structure**
```bash
# New reorganization commands
plex-cli files reorganize                    # Interactive analysis
plex-cli files reorganize --rebuild-db       # Rebuild database first
plex-cli files reorganize --format json      # JSON output only
plex-cli files reorganize --confidence 0.8   # High confidence only
```

#### **Menu Integration**
```
📁 Files Menu
├── 1. Find duplicate movies/TV episodes
├── 2. Database management
├── 3. Auto-organize downloaded files
├── 4. Analyze misplaced media files        # NEW
├── b. Back to main menu
└── q. Quit
```

### **Component Reuse Strategy**

#### **Existing Components to Leverage**
```python
# Database & Configuration (100% reuse)
from file_managers.plex.utils.media_database import MediaDatabase
from file_managers.plex.config.config import MediaConfig

# AI Processing (100% reuse)
from file_managers.plex.media_autoorganizer.ai_classifier import BedrockClassifier

# File Scanning (80% reuse with extensions)
from file_managers.plex.utils.movie_scanner import scan_directory_for_movies
from file_managers.plex.utils.tv_scanner import scan_directory_for_tv_episodes

# Report Generation (90% reuse with new templates)
from file_managers.plex.utils.report_generator import get_reports_directory, generate_timestamp

# CLI Infrastructure (100% reuse)
from file_managers.cli.personal_cli import PlexCLI
```

#### **New Components to Develop**
```python
# New reorganization-specific components
class MediaReorganizationAnalyzer          # Core analysis engine
class MisplacedFile                        # Data structure for findings  
class ReorganizationReport                 # Specialized report generator
class ReorganizationPrompts                # LLM prompt templates
```

---

## 📊 **Implementation Phases**

### **Phase 1: CLI Integration & Foundation** 
**Duration**: 2-3 hours  
**Priority**: High  

#### **Tasks**
1. **Extend Unified CLI**
   - Add `reorganize` subcommand to files group
   - Implement argument parsing for all options
   - Add interactive menu option
   - Create help documentation

2. **Core Class Structure**
   ```python
   class MediaReorganizationAnalyzer:
       def __init__(self, config: MediaConfig, rebuild_db: bool = False):
           self.config = config
           self.media_db = MediaDatabase()
           self.classifier = BedrockClassifier()
           self.misplaced_files = []
   ```

3. **CLI Handler Integration**
   ```python
   # In personal_cli.py
   def _handle_files_reorganize(self, args) -> int:
       """Handle files reorganize command."""
       analyzer = MediaReorganizationAnalyzer(
           config=self.config,
           rebuild_db=args.rebuild_db
       )
       return analyzer.run_analysis(args)
   ```

#### **Deliverables**
- ✅ Command accessible via `plex-cli files reorganize`
- ✅ Interactive menu integration
- ✅ Argument parsing and validation
- ✅ Basic error handling structure

### **Phase 2: Media Analysis Engine**
**Duration**: 4-5 hours  
**Priority**: High  

#### **Tasks**
1. **Directory Scanning Enhancement**
   ```python
   def scan_all_media_directories(self) -> List[MediaFile]:
       """Scan all configured directories for media files."""
       all_files = []
       
       # Scan each directory type
       for movie_dir in self.config.movie_directories:
           files = self._scan_with_category(movie_dir, "movies")
           all_files.extend(files)
       
       # Similar for TV, documentaries, etc.
       return all_files
   ```

2. **AI-Powered Classification**
   ```python
   def analyze_file_placements(self, files: List[MediaFile]) -> List[MisplacedFile]:
       """Use AI to identify misplaced files."""
       # Batch process files for efficiency
       batches = self._create_batches(files, batch_size=50)
       misplaced = []
       
       for batch in batches:
           classifications = self.classifier.classify_batch(
               [f.name for f in batch],
               custom_prompt=self._create_reorganization_prompt()
           )
           misplaced.extend(self._identify_misplaced(batch, classifications))
       
       return misplaced
   ```

3. **Specialized LLM Prompts**
   ```python
   def _create_reorganization_prompt(self) -> str:
       return """
       Analyze these media filenames and determine if they are in the correct category.
       
       Categories:
       - MOVIE: Individual films
       - TV: TV series episodes (any format like S01E01, 1x01, etc.)
       - DOCUMENTARY: Documentary films or series
       - STANDUP: Stand-up comedy specials
       
       For each file, respond with:
       {
         "filename": "original_name",
         "category": "MOVIE|TV|DOCUMENTARY|STANDUP",
         "confidence": 0.0-1.0,
         "reasoning": "brief explanation"
       }
       """
   ```

#### **Deliverables**
- ✅ Complete directory scanning across all media types
- ✅ AI-powered misplacement detection
- ✅ Confidence scoring for recommendations
- ✅ Batch processing for performance

### **Phase 3: Analysis Logic & Validation**
**Duration**: 2-3 hours  
**Priority**: High  

#### **Tasks**
1. **Misplacement Detection Logic**
   ```python
   def _identify_misplaced(self, files: List[MediaFile], 
                          classifications: List[dict]) -> List[MisplacedFile]:
       """Compare current location vs AI classification."""
       misplaced = []
       
       for file, classification in zip(files, classifications):
           current_category = self._categorize_current_location(file.path)
           suggested_category = classification['category'].lower()
           confidence = classification['confidence']
           
           if current_category != suggested_category and confidence >= self.min_confidence:
               misplaced.append(MisplacedFile(
                   file=file,
                   current_category=current_category,
                   suggested_category=suggested_category,
                   confidence=confidence,
                   reasoning=classification['reasoning']
               ))
       
       return misplaced
   ```

2. **Directory Mapping Logic**
   ```python
   def _suggest_target_directory(self, file: MediaFile, category: str) -> str:
       """Suggest specific target directory for misplaced file."""
       category_mapping = {
           'movie': self.config.movie_directories[0],  # Primary movie dir
           'tv': self.config.tv_directories[0],        # Primary TV dir
           'documentary': self.config.documentary_directories[0],
           'standup': self.config.standup_directories[0]
       }
       
       base_dir = category_mapping.get(category)
       if category == 'tv':
           # For TV, suggest show-specific subdirectory
           show_name = self._extract_show_name(file.name)
           return f"{base_dir}/{show_name}/"
       
       return base_dir
   ```

3. **Validation & Quality Checks**
   - Cross-reference with existing database entries
   - Validate target directories exist and are writable
   - Flag suspicious patterns (e.g., entire show in wrong category)
   - Handle edge cases (multi-part movies, specials, etc.)

#### **Deliverables**
- ✅ Accurate misplacement detection with validation
- ✅ Specific directory suggestions for each file
- ✅ Quality checks and edge case handling
- ✅ Confidence-based filtering

### **Phase 4: Report Generation System**
**Duration**: 2-3 hours  
**Priority**: High  

#### **Tasks**
1. **Enhanced Report Templates**
   ```python
   class ReorganizationReport:
       def generate_text_report(self, misplaced_files: List[MisplacedFile]) -> str:
           """Generate comprehensive human-readable report."""
           sections = [
               self._generate_executive_summary(misplaced_files),
               self._generate_category_breakdown(misplaced_files),
               self._generate_detailed_findings(misplaced_files),
               self._generate_action_items(misplaced_files)
           ]
           return "\n\n".join(sections)
   ```

2. **JSON Report Structure**
   ```python
   def generate_json_report(self, misplaced_files: List[MisplacedFile]) -> dict:
       """Generate machine-readable report for potential automation."""
       return {
           "analysis_metadata": {
               "timestamp": datetime.now().isoformat(),
               "total_files_analyzed": self.total_files,
               "directories_scanned": self.scanned_directories,
               "ai_model_used": "anthropic.claude-3-5-sonnet"
           },
           "summary": {
               "total_misplaced": len(misplaced_files),
               "by_category": self._group_by_category(misplaced_files),
               "confidence_distribution": self._analyze_confidence(misplaced_files),
               "estimated_impact": self._calculate_impact(misplaced_files)
           },
           "findings": [file.to_dict() for file in misplaced_files],
           "recommendations": self._generate_recommendations(misplaced_files)
       }
   ```

3. **Report Integration**
   - Use existing report directory structure
   - Consistent timestamping with other reports
   - Both text and JSON formats generated simultaneously
   - Summary statistics and impact analysis

#### **Deliverables**
- ✅ Comprehensive text reports for human review
- ✅ Structured JSON reports for automation potential
- ✅ Executive summary with key statistics
- ✅ Actionable recommendations with priorities

### **Phase 5: Interactive Mode & Polish**
**Duration**: 1-2 hours  
**Priority**: Medium  

#### **Tasks**
1. **Interactive Mode Enhancement**
   ```python
   def _interactive_files_reorganize(self) -> None:
       """Interactive reorganization analysis."""
       print("🔍 Media Reorganization Analysis")
       print("-" * 35)
       print("This will analyze your media directories for misplaced files.")
       print("• Uses AI to identify files in wrong categories")
       print("• Generates reports with specific recommendations")
       print("• Analysis only - no files will be moved")
       print()
       
       # Database rebuild option
       rebuild = input("Rebuild database before analysis? (y/n): ").strip().lower() == 'y'
       
       # Confidence threshold
       confidence = self._get_confidence_threshold()
       
       # Run analysis
       self._run_reorganization_analysis(rebuild, confidence)
   ```

2. **Progress Indicators**
   ```python
   def _show_progress(self, current: int, total: int, operation: str):
       """Display progress for long-running operations."""
       percent = (current / total) * 100
       bar_length = 40
       filled_length = int(bar_length * current // total)
       bar = '█' * filled_length + '░' * (bar_length - filled_length)
       
       print(f"\r{operation}: [{bar}] {percent:.1f}% ({current}/{total})", end='')
       if current == total:
           print()  # New line when complete
   ```

3. **Enhanced Error Handling**
   - Network connectivity validation
   - AWS Bedrock API availability checks
   - Graceful degradation for partial failures
   - User-friendly error messages with recovery suggestions

#### **Deliverables**
- ✅ Polished interactive experience
- ✅ Real-time progress feedback
- ✅ Robust error handling
- ✅ Integration testing complete

---

## 🔧 **Technical Implementation Details**

### **Data Structures**

#### **MisplacedFile Class**
```python
@dataclass
class MisplacedFile:
    file: MediaFile
    current_category: str
    suggested_category: str
    suggested_path: str
    confidence: float
    reasoning: str
    file_size: int
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "source_path": str(self.file.path),
            "current_category": self.current_category,
            "suggested_category": self.suggested_category,
            "suggested_path": self.suggested_path,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
            "file_size": self.file_size,
            "file_size_readable": self._format_file_size(self.file_size)
        }
```

#### **Analysis Configuration**
```python
@dataclass
class AnalysisConfig:
    min_confidence: float = 0.7
    batch_size: int = 50
    max_retries: int = 3
    output_formats: List[str] = field(default_factory=lambda: ['text', 'json'])
    exclude_patterns: List[str] = field(default_factory=list)
```

### **Integration Points**

#### **CLI Argument Updates**
```python
# In _add_files_commands method
reorganize_parser = files_subparsers.add_parser(
    'reorganize',
    help='Analyze misplaced media files',
    description='Identify files in wrong directories using AI analysis'
)
reorganize_parser.add_argument('--rebuild-db', action='store_true',
                              help='Rebuild database before analysis')
reorganize_parser.add_argument('--format', choices=['text', 'json', 'both'],
                              default='both', help='Report output format')
reorganize_parser.add_argument('--confidence', type=float, default=0.7,
                              help='Minimum confidence threshold (0.0-1.0)')
reorganize_parser.add_argument('--dry-run', action='store_true', default=True,
                              help='Analysis only mode (default)')
```

#### **Help System Updates**
```python
def _get_help_epilog(self) -> str:
    # Add to existing help examples:
    """
    # Media reorganization analysis:
    plex-cli files reorganize                     # Interactive analysis
    plex-cli files reorganize --rebuild-db        # Rebuild database first
    plex-cli files reorganize --confidence 0.9    # High confidence only
    plex-cli files reorganize --format json       # JSON output only
    """
```

---

## 🧪 **Testing & Validation Strategy**

### **Unit Testing**
```python
# test_media_reorganizer.py
class TestMediaReorganizationAnalyzer:
    def test_directory_categorization(self):
        """Test current location categorization logic."""
        
    def test_misplacement_detection(self):
        """Test AI classification vs current location comparison."""
        
    def test_batch_processing(self):
        """Test efficient batch processing of large file sets."""
        
    def test_confidence_filtering(self):
        """Test confidence threshold filtering."""
```

### **Integration Testing**
- Test with existing media database
- Validate AI classifier integration
- Test report generation pipeline
- Verify CLI integration and argument handling

### **Performance Testing**
- Test with large file collections (15,000+ files)
- Measure AI batch processing performance
- Validate memory usage during analysis
- Test network failure recovery

### **User Acceptance Testing**
- Test interactive mode usability
- Validate report clarity and actionability
- Test with real misplaced files scenarios
- Gather feedback on confidence scoring accuracy

---

## 📅 **Implementation Timeline**

### **Week 1: Core Development**
- **Days 1-2**: Phase 1 - CLI Integration & Foundation (2-3 hours)
- **Days 3-4**: Phase 2 - Media Analysis Engine (4-5 hours)  
- **Day 5**: Phase 3 - Analysis Logic & Validation (2-3 hours)

### **Week 2: Completion & Polish**
- **Days 1-2**: Phase 4 - Report Generation System (2-3 hours)
- **Day 3**: Phase 5 - Interactive Mode & Polish (1-2 hours)
- **Days 4-5**: Testing, documentation, and integration (2-3 hours)

### **Total Estimated Time**: 13-19 hours
- **Core Development**: 10-15 hours
- **Testing & Polish**: 3-4 hours

---

## 📊 **Success Metrics**

### **Functional Success Criteria**
- ✅ **Accuracy**: >95% of identified misplacements are legitimate
- ✅ **Coverage**: Analyzes all configured media directories successfully
- ✅ **Performance**: Processes 15,000+ files within 10 minutes
- ✅ **Usability**: Generates clear, actionable reports requiring minimal interpretation
- ✅ **Reliability**: Handles network/API failures gracefully with useful fallbacks

### **Integration Success Criteria**
- ✅ **CLI Integration**: Seamless integration with existing `plex-cli` interface
- ✅ **Consistency**: Follows established patterns and conventions
- ✅ **Backward Compatibility**: Does not break any existing functionality
- ✅ **Documentation**: Complete help system and usage examples

### **User Experience Success Criteria**
- ✅ **Interactive Mode**: Intuitive workflow for non-technical users
- ✅ **Direct Commands**: Efficient interface for power users
- ✅ **Progress Feedback**: Clear indication of analysis progress
- ✅ **Error Handling**: Helpful error messages with recovery suggestions

---

## 🚨 **Risk Assessment & Mitigation**

### **Technical Risks**

#### **High Priority Risks**
1. **AI API Unavailability**
   - **Risk**: AWS Bedrock service outages or API key issues
   - **Mitigation**: Graceful degradation with rule-based fallback
   - **Detection**: Pre-flight API connectivity checks

2. **Large Dataset Performance**
   - **Risk**: Analysis timeout with very large media collections
   - **Mitigation**: Batch processing with progress indicators
   - **Detection**: Performance testing with 20,000+ file dataset

#### **Medium Priority Risks**
3. **False Positive Misplacements**
   - **Risk**: AI incorrectly categorizing properly placed files
   - **Mitigation**: Confidence thresholds and manual review flags
   - **Detection**: Validation against known correct placements

4. **Network Mount Issues**
   - **Risk**: Temporary network share unavailability
   - **Mitigation**: Per-directory error handling and retry logic
   - **Detection**: Pre-analysis mount accessibility checks

### **User Experience Risks**

#### **Low Priority Risks**
5. **Report Complexity**
   - **Risk**: Generated reports too complex for actionable use
   - **Mitigation**: Clear executive summaries and prioritized actions
   - **Detection**: User feedback during testing phase

6. **Analysis Time Expectations**
   - **Risk**: Users expecting immediate results for large collections
   - **Mitigation**: Clear time estimates and progress indicators
   - **Detection**: Performance testing with user scenario validation

---

## 🔗 **Dependencies & Prerequisites**

### **Existing Component Dependencies**
✅ **Available**: All required components exist and are stable
- `MediaDatabase` - Proven stable with current functionality
- `BedrockClassifier` - Working AI integration with batch processing
- `MediaConfig` - Stable configuration management
- `Report generators` - Consistent report formatting infrastructure

### **External Dependencies**
✅ **Stable**: All external dependencies are already integrated
- **AWS Bedrock API** - Already integrated and working
- **Network mounts** - Existing validation and error handling
- **File system access** - Proven stable across all existing tools

### **Configuration Prerequisites**
✅ **Complete**: All necessary configuration exists
- Media directory configuration in `media_config.yaml`
- AWS API credentials configured and tested
- Report output directory structure established

---

## 🚀 **Implementation Priority & Scheduling**

### **Priority Assessment**
**Priority Level**: **Medium-High** (Phase 4 Enhancement)

**Rationale**:
- **High Value**: Addresses real user pain point of misplaced media
- **Low Risk**: Leverages existing, proven components
- **Good ROI**: Moderate effort (10-15 hours) for significant user value
- **Fits Strategy**: Natural extension of existing media management capabilities

### **Optimal Implementation Timing**
**Recommended Timeline**: After current baseline stabilization

**Scheduling Considerations**:
1. **Immediate**: Can begin implementation immediately (all dependencies met)
2. **Parallel**: Can be developed in parallel with other Phase 4 features
3. **Standalone**: No dependencies on other pending features
4. **Testing Window**: Requires ~1 week for thorough testing

---

## 📋 **Next Steps & Action Items**

### **Immediate Actions (Ready to Start)**
1. **Implementation Kickoff**
   - [ ] Create feature branch: `feature/media-reorganization-tool`
   - [ ] Set up development environment with existing components
   - [ ] Create initial file structure and placeholder classes

2. **Phase 1 Development**
   - [ ] Extend CLI with reorganize subcommand
   - [ ] Implement basic argument parsing and validation
   - [ ] Add interactive menu integration
   - [ ] Create foundation classes and interfaces

### **Development Process**
1. **Iterative Development**: Implement phases sequentially with testing
2. **Component Reuse**: Maximize use of existing infrastructure
3. **User Feedback**: Test interactive mode early for usability validation
4. **Documentation**: Update help system and documentation concurrently

### **Quality Assurance**
1. **Code Review**: Follow existing code review processes
2. **Testing**: Comprehensive unit and integration testing
3. **Performance**: Validate with large dataset scenarios
4. **User Testing**: Test with actual misplaced files scenarios

---

## 📊 **Implementation Readiness Assessment**

### **Readiness Score: 95%** ✅

#### **Strengths (95%)**
- ✅ **Complete Dependencies**: All required components exist and are stable
- ✅ **Clear Requirements**: Well-defined specifications with concrete examples
- ✅ **Proven Architecture**: Leverages battle-tested existing infrastructure
- ✅ **Risk Mitigation**: Comprehensive risk assessment with mitigation strategies
- ✅ **Integration Path**: Clear integration path with existing CLI system

#### **Minor Gaps (5%)**
- ⚠️ **LLM Prompt Optimization**: May require iteration to optimize AI prompts
- ⚠️ **Performance Tuning**: Large dataset performance may need optimization
- ⚠️ **User Experience Polish**: Interactive mode may need refinement based on testing

### **Recommendation: PROCEED WITH IMPLEMENTATION**

The media reorganization tool represents a **high-value, low-risk enhancement** that naturally extends the existing unified CLI system. All technical prerequisites are met, and the implementation plan provides a clear, systematic approach to delivery.

---

*Implementation Plan Prepared: December 21, 2024*  
*Status: Ready for Development - All Dependencies Met* ✅  
*Estimated Completion: 2-3 weeks part-time development* 📅