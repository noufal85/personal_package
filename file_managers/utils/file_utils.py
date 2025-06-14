"""File utility functions."""

import os
import shutil
from pathlib import Path
from typing import List, Optional


def safe_copy(src: str, dst: str, overwrite: bool = False) -> bool:
    """Safely copy a file with optional overwrite protection."""
    src_path = Path(src)
    dst_path = Path(dst)
    
    if not src_path.exists():
        raise FileNotFoundError(f"Source file not found: {src}")
    
    if dst_path.exists() and not overwrite:
        return False
    
    dst_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src_path, dst_path)
    return True


def find_files_by_extension(directory: str, extension: str) -> List[Path]:
    """Find all files with a specific extension in a directory tree."""
    directory_path = Path(directory)
    if not directory_path.is_dir():
        raise NotADirectoryError(f"Not a directory: {directory}")
    
    pattern = f"*.{extension.lstrip('.')}"
    return list(directory_path.rglob(pattern))


def get_file_size_human(file_path: str) -> str:
    """Get human-readable file size."""
    size = os.path.getsize(file_path)
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} PB"