"""
Root WSGI entry point.

The actual Flask app lives in functions/server.py. This shim exposes it as
`app` at the repo root so the conventional `gunicorn app:app` start command
(Render's default for Python services) works without extra configuration.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "functions"))

from server import app  # noqa: E402  (path must be set before this import)

__all__ = ["app"]
