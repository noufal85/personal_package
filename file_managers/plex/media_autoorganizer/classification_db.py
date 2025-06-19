"""Classification Database

This module provides the ClassificationDatabase class that manages a SQLite database
for caching media file classifications to avoid repeated AI/rule-based analysis.

Key Features:
- SQLite database for persistent classification storage
- Efficient lookups by filename
- Batch operations for performance
- Statistics and management functions
"""

import sqlite3
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class ClassificationDatabase:
    """SQLite database for storing media classifications."""
    
    def __init__(self, db_path: Path):
        """
        Initialize the classification database.
        
        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()
    
    def _init_database(self) -> None:
        """Initialize the database with required tables."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS classifications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filename TEXT NOT NULL UNIQUE,
                    media_type TEXT NOT NULL,
                    classification_source TEXT NOT NULL,
                    confidence REAL DEFAULT 0.0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create index for faster lookups
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_filename 
                ON classifications (filename)
            """)
            
            conn.commit()
    
    def get_classification(self, filename: str) -> Optional[Tuple[str, str, float]]:
        """
        Get cached classification for a filename.
        
        Args:
            filename: Name of the file to look up
            
        Returns:
            Tuple of (media_type, classification_source, confidence) or None
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT media_type, classification_source, confidence 
                FROM classifications 
                WHERE filename = ?
            """, (filename,))
            
            row = cursor.fetchone()
            return row if row else None
    
    def store_classification(self, filename: str, media_type: str, 
                           classification_source: str, confidence: float = 0.0) -> None:
        """
        Store or update a classification in the database.
        
        Args:
            filename: Name of the file
            media_type: Classified media type
            classification_source: Source of classification (AI, Rule-based, etc.)
            confidence: Confidence score (0.0 to 1.0)
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO classifications 
                (filename, media_type, classification_source, confidence, updated_at)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (filename, media_type, classification_source, confidence))
            
            conn.commit()
    
    def store_batch_classifications(self, classifications: List[Tuple[str, str, str, float]]) -> None:
        """
        Store multiple classifications in batch for better performance.
        
        Args:
            classifications: List of (filename, media_type, classification_source, confidence) tuples
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.executemany("""
                INSERT OR REPLACE INTO classifications 
                (filename, media_type, classification_source, confidence, updated_at)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, classifications)
            
            conn.commit()
    
    def get_stats(self) -> Dict[str, int]:
        """
        Get database statistics.
        
        Returns:
            Dictionary with database statistics including total count and breakdowns by type/source
        """
        with sqlite3.connect(self.db_path) as conn:
            # Total classifications
            total = conn.execute("SELECT COUNT(*) FROM classifications").fetchone()[0]
            
            # By media type
            type_counts = conn.execute("""
                SELECT media_type, COUNT(*) 
                FROM classifications 
                GROUP BY media_type
            """).fetchall()
            
            # By source
            source_counts = conn.execute("""
                SELECT classification_source, COUNT(*) 
                FROM classifications 
                GROUP BY classification_source
            """).fetchall()
            
            return {
                'total': total,
                'by_type': dict(type_counts),
                'by_source': dict(source_counts)
            }
    
    def clear_database(self) -> None:
        """Clear all classifications from database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM classifications")
            conn.commit()