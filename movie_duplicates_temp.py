#\!/usr/bin/env python3
import sys
import argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--tv", action="store_true")
    parser.add_argument("--demo", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--custom", type=str)
    parser.add_argument("--delete", action="store_true")
    parser.add_argument("--folder-analysis-only", action="store_true")
    args = parser.parse_args()

    if args.tv:

