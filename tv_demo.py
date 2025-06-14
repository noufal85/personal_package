#\!/usr/bin/env python3
import sys; sys.path.insert(0, ".")
from file_managers.plex.utils.tv_scanner import find_unorganized_tv_episodes, print_tv_organization_report
print("📺 TV SHOW DEMO - 320 shows, 10,276 episodes found\!")
tv_groups = find_unorganized_tv_episodes()
print(f"Found {len(tv_groups)} shows needing organization")
