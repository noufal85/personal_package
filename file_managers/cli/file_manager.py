#!/usr/bin/env python3
"""Simple file management CLI tool."""

import argparse
import sys
from pathlib import Path

from ..utils.file_utils import find_files_by_extension, get_file_size_human


def main() -> None:
    """Main entry point for file manager CLI."""
    parser = argparse.ArgumentParser(description="Personal file management utilities")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Find command
    find_parser = subparsers.add_parser("find", help="Find files by extension")
    find_parser.add_argument("directory", help="Directory to search")
    find_parser.add_argument("extension", help="File extension to search for")
    
    # Size command
    size_parser = subparsers.add_parser("size", help="Get file size")
    size_parser.add_argument("file", help="File to get size for")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        if args.command == "find":
            files = find_files_by_extension(args.directory, args.extension)
            if files:
                print(f"Found {len(files)} files with extension '.{args.extension}':")
                for file_path in files:
                    print(f"  {file_path}")
            else:
                print(f"No files found with extension '.{args.extension}' in {args.directory}")
        
        elif args.command == "size":
            if not Path(args.file).exists():
                print(f"Error: File not found: {args.file}", file=sys.stderr)
                sys.exit(1)
            size = get_file_size_human(args.file)
            print(f"{args.file}: {size}")
    
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()