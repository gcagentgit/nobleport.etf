"""
Shared test configuration.

Point the backend at an isolated, throwaway SQLite database before any
backend module imports settings, so tests never touch a real database.
"""

import os
import tempfile

_TEST_DB = os.path.join(tempfile.gettempdir(), "nobleport_test.db")
os.environ.setdefault(
    "NOBLEPORT_DATABASE_URL", f"sqlite+aiosqlite:///{_TEST_DB}"
)
