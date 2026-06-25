"""
WSGI entry point for deploying the MyShubhLife voice-bot backend on PythonAnywhere.

HOW TO USE (see PYTHONANYWHERE_DEPLOY.md for the full walkthrough):
1. Upload the whole `shubhlife/` folder to your PythonAnywhere account,
   e.g. to /home/<username>/shubhlife
2. On the PythonAnywhere "Web" tab, open the WSGI configuration file
   (e.g. /var/www/<username>_pythonanywhere_com_wsgi.py).
3. DELETE its contents and paste the contents of THIS file instead.
4. Set USERNAME below to your actual PythonAnywhere username.
5. Click "Reload" on the Web tab.

The Flask app object lives in functions/server.py as `app`; WSGI needs it
exposed as `application`.

NOTE: This file auto-discovers where `server.py` actually lives, so it works
even if the upload/unzip created a different folder layout (a very common
cause of `ModuleNotFoundError: No module named 'server'`).
"""

import os
import sys

# --- EDIT THIS: your PythonAnywhere username ---
USERNAME = "ddlsandeep"

HOME = f"/home/{USERNAME}"

# Candidate locations for the folder that CONTAINS server.py.
# We try each one and use the first that actually has server.py in it.
_CANDIDATES = [
    f"{HOME}/shubhlife/functions",          # expected layout
    f"{HOME}/shubhlife/shubhlife/functions",  # double-nested zip
    f"{HOME}/functions",                     # functions/ uploaded directly
    f"{HOME}/shubhlife",                     # server.py at shubhlife root
    HOME,                                    # server.py uploaded to home
]


def _find_functions_dir():
    """Return the first candidate dir that contains server.py."""
    for path in _CANDIDATES:
        if os.path.isfile(os.path.join(path, "server.py")):
            return path

    # Fall back to a shallow walk of the home directory so we still find it
    # even if it was placed somewhere unexpected.
    for root, dirs, files in os.walk(HOME):
        # Skip hidden/virtualenv noise to keep this fast.
        dirs[:] = [d for d in dirs if not d.startswith(".") and d != "site-packages"]
        if "server.py" in files:
            return root
        # Don't descend too deep.
        if root.count(os.sep) - HOME.count(os.sep) >= 4:
            dirs[:] = []
    return None


PROJECT_FUNCTIONS_DIR = _find_functions_dir()

if PROJECT_FUNCTIONS_DIR is None:
    raise RuntimeError(
        "Could not locate server.py under "
        f"{HOME}. Make sure you uploaded the project there and that "
        f"USERNAME is set correctly (currently '{USERNAME}'). "
        f"Looked in: {_CANDIDATES}"
    )

if PROJECT_FUNCTIONS_DIR not in sys.path:
    sys.path.insert(0, PROJECT_FUNCTIONS_DIR)

# server.py defines `app`; PythonAnywhere's WSGI loader looks for `application`.
from server import app as application
