# Plex CLI - Complete Implementation Plan

## 🎯 Project Overview

Centralize all media management features into a unified, interactive command-line interface with intelligent search and duplicate detection capabilities.

---

## 📋 Phase 1: Core Media Management (Enhanced Scope)

### **Goal**: Complete media management foundation with AI-powered search

### **Features to Implement:**

#### 1. Database Management
- **Database rebuild**: Full media database reconstruction
- **Database status**: Show age, statistics, and health
- **Auto-prompting**: Suggest rebuilds when database is stale (>24h)
- **Statistics display**: Movies, TV shows, episodes, total size, build time

#### 2. Duplicate Detection  
- **Movie duplicates**: Database-based duplicate detection for movies
- **TV duplicates**: Database-based duplicate detection for TV episodes
- **Cross-media search**: Find duplicates across both movie and TV collections
- **Quality identification**: Identify best file (largest size) to keep
- **Space savings**: Calculate potential storage recovery
- **Interactive selection**: Choose duplicate types (movies, TV, or all)

#### 3. AI-Powered Movie Search
- **Natural language queries**: "Do I have the movie The Batman?"
- **Fuzzy matching**: Handle typos and variations in movie titles
- **Year disambiguation**: Handle movies with same names from different years
- **Series detection**: Find all movies in a franchise/series
- **External suggestions**: TMDB integration for movies not found locally

#### 4. AI-Powered TV Search  
- **Natural language queries**: "How many seasons of Breaking Bad do I have?"
- **Season analysis**: Detailed breakdown of available seasons and episodes
- **Missing episode detection**: "Am I missing episodes for Game of Thrones season 8?"
- **Show completeness**: Calculate percentage of complete seasons/shows
- **External verification**: TVDB integration for episode count verification

#### 5. Interactive Menu System
- **Default interactive mode**: Menu-driven navigation when no arguments
- **Hierarchical menus**: Main → Files → Specific operations
- **Direct command support**: Power users can use direct commands
- **User-friendly prompts**: Clear options and input validation

### **Implementation Architecture:**

#### Database Layer
- **Existing**: `file_managers/plex/utils/media_database.py`
- **Integration**: Expose rebuild and status through CLI
- **Enhancement**: Add age tracking and statistics display

#### Duplicate Detection
- **Existing**: `file_managers/plex/utils/movie_scanner.py` (movies only)
- **New**: Create TV episode duplicate detection using same patterns
- **Integration**: Create unified duplicate detector using database
- **Display**: Format results with space savings and quality indicators

#### AI-Powered Search
- **Existing**: `file_managers/plex/cli/media_assistant.py` (fully implemented)
- **Integration**: Expose through unified CLI interface
- **Components**:
  - `ai_query_processor.py` - Natural language understanding (AWS Bedrock)
  - `media_searcher.py` - Database search with fuzzy matching
  - `episode_analyzer.py` - Missing episode analysis
  - `external_api.py` - TMDB/TVDB integration

#### CLI Integration Points
- **Database commands**: `plex-cli files database --rebuild/--status`
- **Duplicate commands**: `plex-cli files duplicates --type movies/tv/all`
- **Search commands**: `plex-cli search "Do I have Batman?"`
- **Interactive menus**: Guided access to all features

### **Technical Requirements:**

#### Dependencies
- **AWS Bedrock**: For natural language query processing
- **External APIs**: TMDB and TVDB API keys (optional but recommended)
- **Database**: JSON-based media database (existing)
- **Configuration**: Environment variables for API keys

#### Configuration Setup
```bash
# Required for full AI functionality
export TMDB_API_KEY="your_tmdb_key"
export TVDB_API_KEY="your_tvdb_key"  
export AWS_ACCESS_KEY_ID="your_aws_key"
export AWS_SECRET_ACCESS_KEY="your_aws_secret"
```

#### Fallback Behavior
- **No AI**: Pattern-based query processing
- **No external APIs**: Local database search only
- **No database**: Filesystem-based operations

---

## 📋 Phase 2: Advanced Media Operations

### **Goal**: Advanced media management and organization features

### **Features:**

#### 1. TV Episode Organization
- **Episode moving**: Organize loose episodes into proper show folders
- **Season folder creation**: Create proper season directory structures  
- **Cleanup operations**: Remove empty/small folders after moves
- **Dry run mode**: Preview changes before execution

#### 2. Advanced Movie Management
- **Movie organization**: Move movies to proper directory structures
- **Quality upgrades**: Identify and manage quality upgrades
- **Collection management**: Group movie series and franchises

#### 3. Report Generation
- **Movie reports**: Comprehensive movie collection analysis
- **TV reports**: TV show completeness and organization reports
- **Duplicate reports**: Detailed duplicate analysis with recommendations
- **Space analysis**: Storage usage and optimization reports

#### 4. Batch Operations
- **Bulk duplicate removal**: Remove duplicates based on criteria
- **Batch organization**: Process multiple files/shows at once
- **Progress tracking**: Show progress for long-running operations

### **Implementation Requirements:**
- **Existing**: `file_managers/plex/utils/tv_mover.py`
- **Existing**: `file_managers/plex/utils/report_generator.py`
- **Integration**: Expose through unified CLI with interactive menus

---

## 📋 Phase 3: Intelligent Auto-Organization

### **Goal**: AI-powered automatic file organization

### **Features:**

#### 1. Smart File Classification
- **AI classification**: Use AWS Bedrock to classify media files
- **Multi-type support**: Movies, TV, documentaries, stand-ups, audiobooks
- **Intelligent placement**: Auto-place files in correct directories
- **Conflict resolution**: Handle filename conflicts intelligently

#### 2. Download Integration
- **Download monitoring**: Watch download directories for new files
- **Auto-processing**: Automatically classify and move new downloads
- **Quality assessment**: Choose best location based on file quality

#### 3. Advanced Organization
- **Series detection**: Automatically detect and group TV series
- **Season organization**: Create proper season folders automatically
- **Metadata extraction**: Use filenames to extract show/movie information

### **Implementation Requirements:**
- **Existing**: `file_managers/plex/media_autoorganizer/` (complete implementation)
- **Integration**: Expose through unified CLI interface
- **Enhancement**: Add progress tracking and interactive options

---

## 📋 Phase 4: Configuration and Polish

### **Goal**: User experience improvements and advanced configuration

### **Features:**

#### 1. Configuration Management
- **API key management**: Secure storage and validation of API keys
- **Directory configuration**: Easy management of media directory paths
- **Setting optimization**: Performance and behavior tuning
- **Backup management**: Configuration backup and restore

#### 2. Advanced CLI Features
- **Command shortcuts**: Aliases for common operations (e.g., `plex-cli m d` for movie duplicates)
- **Command completion**: Tab completion for commands and paths
- **History management**: Command history and favorites
- **Customizable prompts**: User-configurable interactive prompts

#### 3. Performance Optimizations
- **Caching improvements**: Enhanced database caching strategies
- **Parallel processing**: Multi-threaded operations for large collections
- **Progressive loading**: Streaming results for large datasets
- **Memory optimization**: Efficient memory usage for large collections

#### 4. Integration Features
- **Plex integration**: Direct integration with Plex Media Server APIs
- **External tool integration**: Support for additional media tools
- **Notification system**: Progress notifications for long operations

---

## 🚀 Implementation Strategy

### Phase 1 Priority (Immediate)
1. **Integrate existing media assistant** into unified CLI
2. **Create TV duplicate detection** (pattern similar to movies)  
3. **Enhance database management** with CLI exposure
4. **Create interactive menus** for all Phase 1 features
5. **Test and validate** all core functionality

### Phase 2-4 Approach
- **Incremental integration**: Add one feature group at a time
- **Backward compatibility**: Maintain existing CLI interfaces during transition
- **User feedback**: Gather feedback after each phase
- **Performance testing**: Validate performance with large media collections

### Success Metrics
- **Phase 1**: Complete media search and duplicate detection via unified CLI
- **Phase 2**: Advanced operations accessible through interactive interface  
- **Phase 3**: Fully automated media organization pipeline
- **Phase 4**: Production-ready, user-friendly media management suite

---

## 🔧 Technical Architecture

### CLI Structure
```
plex-cli (interactive by default)
├── files
│   ├── find           # File operations
│   ├── size
│   ├── duplicates     # Phase 1: Database-based duplicate detection
│   └── database       # Phase 1: Database management
├── search             # Phase 1: AI-powered natural language search
├── organize           # Phase 3: Auto-organization
├── reports            # Phase 2: Report generation  
└── config             # Phase 4: Configuration management
```

### Data Flow
1. **Input**: User query (interactive menu or direct command)
2. **Processing**: AI query understanding → Database search → Result formatting
3. **Output**: Structured results with actionable information
4. **Action**: Optional follow-up operations (delete duplicates, organize files, etc.)

### Key Integration Points
- **Existing Media Assistant**: Full AI search capabilities ready for integration
- **Existing Database System**: Fast cached media database ready for CLI exposure
- **Existing Duplicate Detection**: Movie duplicates ready, TV duplicates to be created
- **Existing Auto-Organizer**: Complete AI classification system ready for integration

---

## 📈 Expected Outcomes

### Phase 1 Deliverables
- **Unified CLI**: Single entry point for all media operations
- **AI Search**: Natural language movie and TV search
- **Duplicate Management**: Fast, comprehensive duplicate detection
- **Database Operations**: Easy database management and monitoring
- **Interactive Experience**: User-friendly menu-driven interface

### Long-term Vision
- **Complete Media Management**: Single tool for all Plex media operations
- **AI-Powered Intelligence**: Natural language interface for all operations
- **Automated Workflows**: Hands-off media organization and maintenance
- **Production Ready**: Robust, fast, and reliable media management solution