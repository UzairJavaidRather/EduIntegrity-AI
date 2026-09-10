"""
conftest.py — pytest configuration for EduIntegrity AI backend tests.

This file is automatically loaded by pytest before running any tests.

What it does here:
  Adds the backend/ directory to Python's sys.path so that imports like
  `from app.services.extractor import ...` work when running pytest from
  the backend/ directory.

  Without this, pytest cannot find the `app` package because it's not
  installed as a package — it's just a directory.
"""

import sys
from pathlib import Path

# Add the backend/ directory to the Python path
# Path(__file__).parent is the backend/ directory (where conftest.py lives)
sys.path.insert(0, str(Path(__file__).parent))
