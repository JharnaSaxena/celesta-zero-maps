import os
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
MOCK_DATA_DIR = DATA_DIR / "mock"
DB_PATH = os.environ.get("JEZERO_DB_PATH", str(DATA_DIR / "jezero.db"))

# Mars & Jezero Crater Scientific Constants
JEZERO_LAT = 18.38       # Degrees North
JEZERO_LON = 77.58       # Degrees East (Syrtis Major quadrangle)
JEZERO_RADIUS_KM = 22.5  # Approximate crater radius in km
MARS_RADIUS_KM = 3389.5  # Mean equatorial radius
MARS_GRAVITY_MSS = 3.721 # Surface gravity m/s^2

# Sol time: 1 Martian Sol = 24 hours, 39 minutes, 35.244 seconds (88,775.244 s)
SOL_DURATION_SECONDS = 88775.244

# Terrain Model Parameters (Matching synthetic Jezero dataset)
TERRAIN_SIZE = 65
TERRAIN_SPAN_KM = 50.0
TERRAIN_SEED = 20261110

# LIFELINE Safety Thresholds & Model
LIFELINE_WEIGHT_SLOPE = 2.0
LIFELINE_WEIGHT_DUST = 0.32
LIFELINE_WEIGHT_DISTANCE = 1.1
LIFELINE_BASE_X = -5.0
LIFELINE_BASE_Z = 5.0

TIER_FAVORABLE_THRESHOLD = 65
TIER_CAUTION_THRESHOLD = 40

# Server Configuration
SERVER_HOST = os.environ.get("HOST", "0.0.0.0")
SERVER_PORT = int(os.environ.get("PORT", "5000"))
DEBUG = os.environ.get("DEBUG", "False").lower() in ("true", "1")
