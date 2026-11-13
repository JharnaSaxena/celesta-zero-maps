import os
import sys
from pathlib import Path

# Ensure workspace root is in sys.path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from backend.app import app
from backend.config import SERVER_HOST, SERVER_PORT, DEBUG

if __name__ == "__main__":
    print("=" * 70)
    print("  TERRASCOPE MARS — JEZERO CRATER FULL-STACK MISSION OPERATIONS")
    print("=" * 70)
    print(f"  • 3D Mars Explorer UI:  http://localhost:{SERVER_PORT}")
    print(f"  • Earth Explorer UI:    http://localhost:{SERVER_PORT}/earth.html")
    print(f"  • Interactive API Docs: http://localhost:{SERVER_PORT}/docs")
    print(f"  • Mars Clock Telemetry: http://localhost:{SERVER_PORT}/api/mars/telemetry/time")
    print(f"  • API Health Check:     http://localhost:{SERVER_PORT}/api/health")
    print("=" * 70)
    print("  Server is running! Open http://localhost:5000 in your browser.")
    print("  Press Ctrl+C to stop.\n")
    app.run(host=SERVER_HOST, port=SERVER_PORT, debug=DEBUG)
