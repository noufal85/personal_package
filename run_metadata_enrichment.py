#!/usr/bin/env python3
"""
Convenience script for running the metadata enrichment tool.

This script provides an easy way to enrich your media database with
accurate metadata from external APIs (TMDB, TVDB).
"""

import sys
from file_managers.plex.utils.metadata_enrichment import main

if __name__ == "__main__":
    print("🎬 Media Metadata Enrichment Tool")
    print("=================================")
    print()
    print("This tool queries external APIs to get accurate metadata for your media files.")
    print("Results are cached locally to avoid repeated API calls.")
    print()
    
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⏹️  Enrichment cancelled by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)