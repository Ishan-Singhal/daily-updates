#!/usr/bin/env python3
"""Regenerate dashboard/index.html from data/predictions.json and data/track_record.json."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fetchers.dashboard import build_dashboard

if __name__ == "__main__":
    path = build_dashboard()
    print(f"Dashboard written to {path}")
