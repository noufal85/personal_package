"""Tests for file utility functions."""

import tempfile
from pathlib import Path

import pytest

from file_managers.utils.file_utils import (
    find_files_by_extension,
    get_file_size_human,
    safe_copy,
)


def test_safe_copy():
    """Test safe file copying."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        src_file = temp_path / "source.txt"
        dst_file = temp_path / "dest.txt"
        
        # Create source file
        src_file.write_text("test content")
        
        # Test successful copy
        assert safe_copy(str(src_file), str(dst_file))
        assert dst_file.exists()
        assert dst_file.read_text() == "test content"
        
        # Test overwrite protection
        assert not safe_copy(str(src_file), str(dst_file), overwrite=False)
        
        # Test overwrite allowed
        src_file.write_text("new content")
        assert safe_copy(str(src_file), str(dst_file), overwrite=True)
        assert dst_file.read_text() == "new content"


def test_find_files_by_extension():
    """Test finding files by extension."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create test files
        (temp_path / "file1.txt").write_text("content")
        (temp_path / "file2.py").write_text("content")
        (temp_path / "subdir").mkdir()
        (temp_path / "subdir" / "file3.txt").write_text("content")
        
        # Find .txt files
        txt_files = find_files_by_extension(str(temp_path), "txt")
        assert len(txt_files) == 2
        
        # Find .py files
        py_files = find_files_by_extension(str(temp_path), ".py")
        assert len(py_files) == 1


def test_get_file_size_human():
    """Test human-readable file size formatting."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_file:
        temp_file.write("a" * 1024)  # 1KB
        temp_file.flush()
        
        size_str = get_file_size_human(temp_file.name)
        assert "1.0 KB" in size_str
        
        Path(temp_file.name).unlink()  # Clean up