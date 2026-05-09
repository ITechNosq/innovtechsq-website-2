import sys
import os

# Add the app directory to path
sys.path.append(os.getcwd())

try:
    from app.core.config import settings
    print(f"DEBUG: Loaded Username: '{settings.ADMIN_USERNAME}'")
    print(f"DEBUG: Loaded Password: '{settings.ADMIN_PASSWORD}'")
    print(f"DEBUG: CORS Origins: {settings.get_cors_origins()}")
except Exception as e:
    print(f"ERROR: {e}")
