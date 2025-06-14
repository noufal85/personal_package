"""Tests for movie scanner utilities."""

import tempfile
from pathlib import Path

import pytest

from file_managers.utils.movie_scanner import (
    MovieFile,
    normalize_movie_name,
    extract_year_from_filename,
    scan_directory_for_movies,
    find_duplicate_movies,
    format_file_size,
)


def test_normalize_movie_name():
    """Test movie name normalization."""
    test_cases = [
        ("The.Matrix.1999.1080p.BluRay.x264-GROUP", "the matrix 1999"),
        ("Inception (2010) [1080p] {YIFY}", "inception 2010"),
        ("Avatar.2009.EXTENDED.720p.BRRip.XviD.AC3-FLAWL3SS", "avatar 2009"),
        ("Movie Title - Release Group", "movie title"),
        ("Some_Movie_Title_2020_4K_UHD.mkv", "some movie title 2020 4k uhd"),
        ("Film.Title.REPACK.PROPER.DC.UNRATED.mkv", "film title"),
    ]
    
    for input_name, expected in test_cases:
        result = normalize_movie_name(input_name)
        assert result == expected, f"Expected '{expected}', got '{result}' for input '{input_name}'"


def test_extract_year_from_filename():
    """Test year extraction from filenames."""
    test_cases = [
        ("The Matrix 1999 1080p", "1999"),
        ("Inception (2010) BluRay", "2010"),
        ("Old Movie 1985 DVDRip", "1985"),
        ("Future Movie 2025 4K", "2025"),
        ("No Year Movie BluRay", ""),
        ("Movie 12345 Invalid Year", ""),
    ]
    
    for filename, expected in test_cases:
        result = extract_year_from_filename(filename)
        assert result == expected, f"Expected '{expected}', got '{result}' for '{filename}'"


def test_format_file_size():
    """Test file size formatting."""
    test_cases = [
        (1024, "1.0 KB"),
        (1024 * 1024, "1.0 MB"),
        (1024 * 1024 * 1024, "1.0 GB"),
        (1536 * 1024 * 1024, "1.5 GB"),
        (500, "500.0 B"),
    ]
    
    for size_bytes, expected in test_cases:
        result = format_file_size(size_bytes)
        assert result == expected, f"Expected '{expected}', got '{result}' for {size_bytes} bytes"


def test_scan_directory_for_movies():
    """Test scanning directory for movie files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create test movie files
        movie_files = [
            "The Matrix 1999.mp4",
            "Inception 2010.mkv",
            "Avatar 2009.avi",
            "Not A Movie.txt",  # Should be ignored
            "subdir/Nested Movie 2020.mov",
        ]
        
        for file_path in movie_files:
            full_path = temp_path / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text("dummy content")
        
        # Scan directory
        movies = scan_directory_for_movies(str(temp_path))
        
        # Should find 4 movie files (excluding .txt)
        assert len(movies) == 4
        
        # Check that all found files are MovieFile objects
        for movie in movies:
            assert isinstance(movie, MovieFile)
            assert movie.path.exists()
            assert movie.size > 0
            assert movie.name
            assert movie.normalized_name


def test_find_duplicate_movies():
    """Test finding duplicate movies across directories."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create two directories with duplicate movies
        dir1 = temp_path / "dir1"
        dir2 = temp_path / "dir2"
        dir1.mkdir()
        dir2.mkdir()
        
        # Create duplicate movies with different quality/size
        (dir1 / "The Matrix 1999 1080p.mp4").write_text("a" * 1000)  # Smaller
        (dir2 / "The.Matrix.1999.720p.BluRay.x264.mkv").write_text("a" * 2000)  # Larger
        
        # Create unique movie
        (dir1 / "Unique Movie 2020.mp4").write_text("unique content")
        
        # Find duplicates
        duplicates = find_duplicate_movies([str(dir1), str(dir2)])
        
        # Should find one duplicate group
        assert len(duplicates) == 1
        
        duplicate_group = duplicates[0]
        assert len(duplicate_group.files) == 2
        
        # Smallest file should be the one with less content
        assert duplicate_group.smallest_file.size == 1000
        assert "1080p" in duplicate_group.smallest_file.name


def test_scan_nonexistent_directory():
    """Test scanning a non-existent directory."""
    with pytest.raises(FileNotFoundError):
        scan_directory_for_movies("/nonexistent/directory")