"""Pytest configuration and fixtures for SAATH test suite."""

import sys
from pathlib import Path

# Ensure api directory is on sys.path
api_path = Path(__file__).resolve().parent.parent / "api"
if str(api_path) not in sys.path:
    sys.path.insert(0, str(api_path))
