"""Centralized configuration management for Plex media tools."""

import os
import yaml
from pathlib import Path
from typing import List, Dict, Any, Optional


class MediaConfig:
    """Centralized configuration for media management tools."""
    
    _instance = None
    _config = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MediaConfig, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._config is None:
            self._load_config()
    
    def _load_config(self) -> None:
        """Load configuration from YAML file."""
        config_dir = Path(__file__).parent
        config_file = config_dir / "media_config.yaml"
        
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                self._config = yaml.safe_load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"Configuration file not found: {config_file}")
        except yaml.YAMLError as e:
            raise ValueError(f"Error parsing configuration file: {e}")
    
    @property
    def config(self) -> Dict[str, Any]:
        """Get the full configuration dictionary."""
        return self._config
    
    # NAS Configuration
    @property
    def nas_server_ip(self) -> str:
        """Get NAS server IP address."""
        return self._config.get('nas', {}).get('server_ip', '192.168.1.27')
    
    @property
    def nas_mount_point(self) -> str:
        """Get NAS mount point."""
        return self._config.get('nas', {}).get('mount_point', '/mnt/qnap')
    
    @property
    def nas_shares(self) -> List[Dict[str, str]]:
        """Get NAS share configuration."""
        return self._config.get('nas', {}).get('shares', [])
    
    # Movie Configuration
    @property
    def movie_directories(self) -> List[str]:
        """Get list of movie directory paths."""
        directories = self._config.get('movies', {}).get('directories', [])
        return [d['path'] for d in directories]
    
    @property
    def movie_directories_full(self) -> List[Dict[str, Any]]:
        """Get full movie directory configuration with metadata."""
        return self._config.get('movies', {}).get('directories', [])
    
    # TV Configuration
    @property
    def tv_directories(self) -> List[str]:
        """Get list of TV directory paths."""
        directories = self._config.get('tv', {}).get('directories', [])
        return [d['path'] for d in directories]
    
    @property
    def tv_directories_full(self) -> List[Dict[str, Any]]:
        """Get full TV directory configuration with metadata."""
        return self._config.get('tv', {}).get('directories', [])
    
    # Documentary Configuration
    @property
    def documentary_directories(self) -> List[str]:
        """Get list of documentary directory paths."""
        directories = self._config.get('documentaries', {}).get('directories', [])
        return [d['path'] for d in directories]
    
    @property
    def documentary_directories_full(self) -> List[Dict[str, Any]]:
        """Get full documentary directory configuration with metadata."""
        return self._config.get('documentaries', {}).get('directories', [])
    
    # Stand-up Configuration
    @property
    def standup_directories(self) -> List[str]:
        """Get list of stand-up directory paths."""
        directories = self._config.get('standups', {}).get('directories', [])
        return [d['path'] for d in directories]
    
    @property
    def standup_directories_full(self) -> List[Dict[str, Any]]:
        """Get full stand-up directory configuration with metadata."""
        return self._config.get('standups', {}).get('directories', [])
    
    # Downloads Configuration
    @property
    def downloads_directory(self) -> str:
        """Get downloads directory path."""
        return self._config.get('downloads', {}).get('directory', '/mnt/d/Completed/')
    
    @property
    def downloads_windows_path(self) -> str:
        """Get downloads Windows path."""
        return self._config.get('downloads', {}).get('windows_path', 'D:\\Completed\\')
    
    # Settings
    @property
    def video_extensions(self) -> List[str]:
        """Get list of supported video file extensions."""
        return self._config.get('settings', {}).get('video_extensions', [
            '.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.m4v', '.mpg', '.mpeg', '.webm', '.ts'
        ])
    
    @property
    def video_extensions_set(self) -> set:
        """Get set of supported video file extensions for fast lookup."""
        return set(self.video_extensions)
    
    @property
    def small_folder_threshold_mb(self) -> int:
        """Get small folder threshold in MB."""
        return self._config.get('settings', {}).get('small_folder_threshold_mb', 100)
    
    @property
    def small_folder_threshold_bytes(self) -> int:
        """Get small folder threshold in bytes."""
        return self.small_folder_threshold_mb * 1024 * 1024
    
    # Report Settings
    @property
    def reports_directory(self) -> str:
        """Get reports directory path."""
        return self._config.get('settings', {}).get('reports', {}).get('directory', 'reports')
    
    @property
    def report_formats(self) -> List[str]:
        """Get supported report formats."""
        return self._config.get('settings', {}).get('reports', {}).get('formats', ['txt', 'json'])
    
    @property
    def timestamp_format(self) -> str:
        """Get timestamp format for report filenames."""
        return self._config.get('settings', {}).get('reports', {}).get('timestamp_format', '%Y%m%d_%H%M%S')
    
    # Safety Settings
    @property
    def create_backups(self) -> bool:
        """Whether to create backups before deletion."""
        return self._config.get('safety', {}).get('create_backups', True)
    
    @property
    def backup_directory(self) -> str:
        """Get backup directory path."""
        return self._config.get('safety', {}).get('backup_directory', 'backups')
    
    @property
    def require_confirmation(self) -> bool:
        """Whether to require confirmation for destructive operations."""
        return self._config.get('safety', {}).get('require_confirmation', True)
    
    @property
    def confirmation_phrases(self) -> Dict[str, str]:
        """Get confirmation phrases for different operations."""
        return self._config.get('safety', {}).get('confirmation_phrases', {
            'delete': 'DELETE FILES',
            'move': 'MOVE FILES',
            'execute': 'EXECUTE'
        })
    
    @property
    def default_dry_run(self) -> bool:
        """Whether operations should default to dry run mode."""
        return self._config.get('safety', {}).get('default_dry_run', True)
    
    # Bedrock Configuration
    @property
    def bedrock_region(self) -> str:
        """Get AWS Bedrock region."""
        return self._config.get('bedrock', {}).get('region', 'us-east-1')
    
    @property
    def bedrock_model_id(self) -> str:
        """Get Bedrock model ID from environment variable or config file."""
        # Check environment variable first
        env_model_id = os.getenv('BEDROCK_MODEL_ID')
        if env_model_id:
            return env_model_id
        
        # Fallback to config file
        return self._config.get('bedrock', {}).get('model_id', 'anthropic.claude-3-haiku-20240307-v1:0')
    
    @property
    def bedrock_max_tokens(self) -> int:
        """Get Bedrock max tokens."""
        return self._config.get('bedrock', {}).get('max_tokens', 1000)
    
    @property
    def bedrock_temperature(self) -> float:
        """Get Bedrock temperature."""
        return self._config.get('bedrock', {}).get('temperature', 0.1)
    
    @property
    def bedrock_classification_prompt(self) -> str:
        """Get Bedrock classification prompt template."""
        return self._config.get('bedrock', {}).get('classification_prompt', '')
    
    # Utility Methods
    def get_reports_path(self) -> Path:
        """Get the full path to the reports directory."""
        # Get project root (go up 4 levels from this config file)
        project_root = Path(__file__).parent.parent.parent.parent
        return project_root / self.reports_directory
    
    def get_backup_path(self) -> Path:
        """Get the full path to the backup directory."""
        project_root = Path(__file__).parent.parent.parent.parent
        return project_root / self.backup_directory
    
    def get_directory_by_priority(self, media_type: str) -> Optional[str]:
        """Get the highest priority directory for a media type."""
        if media_type == 'movies':
            directories = self.movie_directories_full
        elif media_type == 'tv':
            directories = self.tv_directories_full
        else:
            return None
        
        if not directories:
            return None
        
        # Sort by priority (lower number = higher priority)
        sorted_dirs = sorted(directories, key=lambda x: x.get('priority', 999))
        return sorted_dirs[0]['path']
    
    def validate_directories(self, media_type: str) -> List[str]:
        """Validate and return existing directories for a media type."""
        if media_type == 'movies':
            directories = self.movie_directories
        elif media_type == 'tv':
            directories = self.tv_directories
        elif media_type == 'documentaries':
            directories = self.documentary_directories
        elif media_type == 'standups':
            directories = self.standup_directories
        else:
            return []
        
        valid_dirs = []
        for directory in directories:
            if Path(directory).exists():
                valid_dirs.append(directory)
        
        return valid_dirs
    
    def get_directories_by_media_type(self, media_type: str) -> List[str]:
        """Get directories for a specific media type."""
        if media_type.upper() == 'MOVIE':
            return self.movie_directories
        elif media_type.upper() == 'TV':
            return self.tv_directories
        elif media_type.upper() == 'DOCUMENTARY':
            return self.documentary_directories
        elif media_type.upper() == 'STANDUP':
            return self.standup_directories
        else:
            return []


# Global config instance
config = MediaConfig()

# Convenience functions for backward compatibility
def get_movie_directories() -> List[str]:
    """Get movie directories for backward compatibility."""
    return config.movie_directories

def get_tv_directories() -> List[str]:
    """Get TV directories for backward compatibility."""
    return config.tv_directories

def get_video_extensions() -> set:
    """Get video extensions set for backward compatibility."""
    return config.video_extensions_set

def get_small_folder_threshold() -> int:
    """Get small folder threshold in bytes for backward compatibility."""
    return config.small_folder_threshold_bytes