import os
import sys
from pathlib import Path

# Add directories to sys.path so 'backend' can always be imported
api_dir = Path(__file__).resolve().parent
root_dir = api_dir.parent
cwd = Path.cwd()

for p in (str(root_dir), str(api_dir), str(cwd)):
    if p not in sys.path:
        sys.path.insert(0, p)

from backend.app import app as flask_app

class VercelPathFixMiddleware:
    """
    Vercel rewrites deliver the destination path in PATH_INFO,
    but pass the actual requested client path in HTTP_X_MATCHED_PATH or RAW_URI.
    This WSGI middleware restores the real requested path so Flask's route matching works.
    It also catches any unhandled exceptions to prevent 500 FUNCTION_INVOCATION_FAILED.
    """
    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app

    def __call__(self, environ, start_response):
        # Restore real client request path if rewritten by Vercel
        matched_path = environ.get("HTTP_X_MATCHED_PATH")
        if matched_path:
            environ["PATH_INFO"] = matched_path
        elif environ.get("PATH_INFO") in ("/api/index.py", "/api/index", "/api/"):
            raw_uri = environ.get("RAW_URI", "") or environ.get("REQUEST_URI", "")
            if raw_uri and not raw_uri.startswith("/api/index"):
                environ["PATH_INFO"] = raw_uri.split("?")[0]

        try:
            return self.wsgi_app(environ, start_response)
        except Exception as exc:
            import json, traceback
            traceback.print_exc()
            status = "500 Internal Server Error"
            headers = [
                ("Content-Type", "application/json"),
                ("Access-Control-Allow-Origin", "*")
            ]
            start_response(status, headers)
            body = json.dumps({
                "error": "Internal Server Error",
                "message": str(exc),
                "path": environ.get("PATH_INFO")
            }).encode("utf-8")
            return [body]

# Vercel detects and invokes 'app'
app = VercelPathFixMiddleware(flask_app)
