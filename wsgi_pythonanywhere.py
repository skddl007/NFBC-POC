"""
WSGI entry point for deploying the MyShubhLife voice-bot backend on PythonAnywhere.

HOW TO USE (see PYTHONANYWHERE_DEPLOY.md for the full walkthrough):
1. Upload the whole `shubhlife/` folder to your PythonAnywhere account,
   e.g. to /home/<username>/shubhlife
2. On the PythonAnywhere "Web" tab, open the WSGI configuration file
   (e.g. /var/www/<username>_pythonanywhere_com_wsgi.py).
3. DELETE its contents and paste the contents of THIS file instead.
4. Replace <username> below with your actual PythonAnywhere username.
5. Click "Reload" on the Web tab.

The Flask app object lives in functions/server.py as `app`; WSGI needs it
exposed as `application`.
"""

import sys

# --- EDIT THIS: your PythonAnywhere username ---
USERNAME = "yourusername"

# Path to the folder that CONTAINS server.py (the functions/ directory).
PROJECT_FUNCTIONS_DIR = f"/home/{USERNAME}/shubhlife/functions"

if PROJECT_FUNCTIONS_DIR not in sys.path:
    sys.path.insert(0, PROJECT_FUNCTIONS_DIR)

# server.py defines `app`; PythonAnywhere's WSGI loader looks for `application`.
from server import app as application
