#\!/usr/bin/env python3
import argparse
import sys

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--tv", action="store_true")
    parser.add_argument("--demo", action="store_true") 
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()
    
    if args.tv:
        print("TV mode not fully implemented yet - directories would be scanned for organization")
    else:
        print("Movie duplicate scanning not implemented yet")

if __name__ == "__main__":
    main()
EOF < /dev/null
