# 🌌 Celesta — TerraScope Mars Jezero Crater & Planetary Operations

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-2.3%2B-green.svg)](https://flask.palletsprojects.com/)
[![REST API](https://img.shields.io/badge/OpenAPI-3.0-orange.svg)](http://localhost:5000/docs)
[![Vercel Ready](https://img.shields.io/badge/Deploy-Vercel-black.svg)](https://vercel.com)
[![License](https://img.shields.io/badge/License-MIT-lightgrey.svg)](LICENSE)

**Celesta** is a comprehensive planetary exploration and mission operations suite featuring high-resolution 3D visualization of Mars' **Jezero Crater** (`18.38°N, 77.58°E`), a unified Python Flask backend, topocentric Earth-to-Mars ephemeris calculations, and real-time mission telemetry.

---

## 🌟 Key Features

### 🔴 3D Mars Jezero Crater Explorer
- **Ray-Cast Mars Globe**: Interactive 3D spherical rendering with procedural terrain relief, smooth orbital panning, and seamless zoom into Jezero Crater.
- **65 × 65 High-Resolution Jezero Mesh**: 8,192 triangles modeling a 50 × 50 km Jezero terrain with accurate elevation profiles, slope calculations, and synthetic surface texture.
- **LIFELINE Safety Assessment**: Real-time terrain traversability scoring:
  $$\text{margin} = \text{clamp}(100 - 2 \cdot \text{slope}^\circ - 0.32 \cdot \text{dust\_index} - 1.1 \cdot \text{base\_dist\_km}, 0, 100)$$
  Categorizes terrain into *Favorable* ($\ge 65$), *Caution* ($40\text{--}64$), and *Critical* ($< 40$).
- **Multi-Criteria Rover Routing**: Dijkstra pathfinding supporting **Balanced**, **Safest**, **Fastest**, and **Energy-Conserving** traversal modes with real-time elevation profile inspection.

### 🌍 Earth Observer & Solar System View
- **Topocentric Distance Calculation**: Calculates true distance between the observer's exact location on Earth (e.g. Jaipur, Tamil Nadu, Delhi, London) and Jezero Crater on Mars in both kilometers and Astronomical Units (AU).
- **Communication Latency**: Computes one-way light travel time and round-trip delay in real-time.
- **Precision Geolocation**: Captures browser GPS coordinates formatted to 6 decimal places with accuracy radius indicator and optional local storage persistence.
- **ISS Pass Predictor**: Estimates next visible International Space Station passes over observer coordinates.
- **Keplerian Solar System Canvas**: Sun-centered orbital simulation plotting Mercury, Venus, Earth, Mars, and Jupiter using NASA JPL orbital elements, complete with an interactive ephemeris date scrubber.

### ⚡ Unified Single-Port Architecture
- **Single Server on Port 5000**: Serves the 3D Mars client (`/`), Earth Field prototype (`/earth`), Interactive Swagger API Documentation (`/docs`), and all RESTful API endpoints from a single lightweight Flask instance.
- **Zero Heavy Frontend Bundlers**: Native ES module architecture running smoothly in any browser without requiring `npm run build` or Vite dev servers.

---

## 🚀 Quick Start (Local Run)

### Prerequisites
- **Python 3.10+**
- Optional: Node.js 18+ (for running JavaScript unit tests)

### 1. Launch on Windows (1-Click)
Double-click:
```cmd
start_all.bat
```
This automatically installs any missing dependencies, starts the backend server, and opens `http://localhost:5000` in your default browser.

### 2. Manual Command Line Startup
```bash
# 1. Clone the repository
git clone https://github.com/JharnaSaxena/celesta-zero-maps.git
cd celesta-zero-maps

# 2. Install Python dependencies
pip install -r requirements.txt

# 3. Start the unified server
python run_backend.py
```

Open your browser to:
- **Mars Jezero Explorer UI**: [http://localhost:5000](http://localhost:5000)
- **Interactive Swagger Docs**: [http://localhost:5000/docs](http://localhost:5000/docs)
- **Earth Field Prototype**: [http://localhost:5000/earth](http://localhost:5000/earth)

---

## ☁️ How to Deploy to Vercel

The project is pre-configured with `vercel.json` and `api/index.py` for **zero-configuration serverless deployment** on [Vercel](https://vercel.com). Both the frontend static assets (served via Vercel Edge CDN) and Python Flask API endpoints (served via AWS Serverless Functions) work out of the box.

### Method 1: Deploy via Vercel Web Dashboard (Recommended)

1. Go to [https://vercel.com/new](https://vercel.com/new).
2. Sign in with your GitHub account.
3. Search for and select repository: `JharnaSaxena/celesta-zero-maps`.
4. Under **Project Settings**:
   - **Framework Preset**: Leave as *Other* (or *Vite/Python*).
   - **Root Directory**: `./` (default).
   - **Build Command**: Leave empty (no build step needed).
   - **Output Directory**: Leave empty.
5. Click **Deploy**.
6. Within 60 seconds, your site is live with a secure HTTPS URL (e.g., `https://celesta-zero-maps.vercel.app`)!

### Method 2: Deploy using Vercel CLI

1. Install the Vercel CLI:
   ```bash
   npm install -g vercel
   ```
2. Log in and deploy from project directory:
   ```bash
   vercel
   ```
3. To deploy directly to production:
   ```bash
   vercel --prod
   ```

---

## 📡 API Reference Overview

The backend exposes RESTful endpoints with full CORS support. Visit `/docs` for the interactive Swagger UI.

| Category | Endpoint | Method | Description |
| :--- | :--- | :---: | :--- |
| **System** | `/api/health` | `GET` | Server health check and operational status |
| **System** | `/api/openapi.json` | `GET` | OpenAPI 3.0 specification |
| **Ephemeris** | `/api/mars/distance` | `GET` | Topocentric Earth-to-Mars distance & light-time delay |
| **Ephemeris** | `/api/solar-system/positions` | `GET` | Keplerian planet coordinates & orbital tracks |
| **Ephemeris** | `/api/earth/observer/iss-pass`| `GET` | ISS visible pass prediction for observer coords |
| **Terrain** | `/api/mars/terrain/mesh` | `GET` | 65×65 Jezero elevation vertices & polygon data |
| **Terrain** | `/api/mars/terrain/sample` | `GET` | Bilinear elevation interpolation at $(x, z)$ |
| **LIFELINE** | `/api/mars/lifeline/assess` | `GET` | Terrain safety margins & traversability tier |
| **Routing** | `/api/mars/routes/plan` | `POST` | Dijkstra pathfinding between waypoints |
| **Sites** | `/api/mars/sites` | `GET` | Jezero scientific, habitat, and resource sites |
| **Telemetry**| `/api/mars/telemetry/time` | `GET` | Live Martian Sol, MTC, and LST clock |
| **Telemetry**| `/api/mars/telemetry/rover` | `GET` | Real-time rover telemetry and battery level |
| **Weather** | `/api/mars/weather/current` | `GET` | MEDA Jezero meteorological conditions |

---

## 🧪 Testing

### Backend Unit Tests (Pytest)
```bash
python -m pytest tests/test_backend.py -v
```
Verifies health check, terrain sampling, LIFELINE scoring algorithms, rover routing, ephemeris calculations, and database initialization.

### Frontend Native Tests (Node)
```bash
node --test tests/mars_native.test.js
```
Validates mathematical models, PRNG seed reproducibility, Dijkstra bounds, and score thresholds.

---

## 📂 Repository Structure

```text
├── api/                       # Vercel serverless function entrypoint
│   ├── index.py               # WSGI bridge connecting Vercel to Flask app
│   └── requirements.txt       # Dependencies for Vercel Python runtime
├── backend/                   # Python mission operations backend
│   ├── app.py                 # Core Flask application & static routing
│   ├── config.py              # Mars constants & server configuration
│   ├── database.py            # SQLite schema, migration & queries
│   ├── routes/                # Modular REST API blueprints
│   │   ├── ephemeris_routes.py
│   │   ├── lifeline_routes.py
│   │   ├── routing_routes.py
│   │   ├── sites_routes.py
│   │   ├── system_routes.py
│   │   ├── telemetry_routes.py
│   │   ├── terrain_routes.py
│   │   └── weather_routes.py
│   ├── services/              # Scientific calculation engines
│   │   ├── ephemeris_service.py
│   │   ├── lifeline_service.py
│   │   └── routing_service.py
│   └── static/
│       └── docs.html          # Interactive Swagger 3.0 API Documentation
├── data/                      # Fixtures and terrain datasets
│   ├── mock/                  # Mars & Earth digital elevation models
├── public/                    # Textures and panorama assets
│   └── mars/                  # Perseverance 360° panoramas & surface maps
├── src/                       # Frontend application modules
│   ├── components/            # EarthObserver.js & SolarSystemView.js
│   ├── mars/                  # 3D spherical globe & mesh renderer
│   ├── services/apiClient.js  # Client connecting UI to Flask REST API
│   └── main.js                # Application state & event loop
├── tests/                     # Automated test suites
├── index.html                 # 3D Mars Jezero Crater Explorer
├── earth.html                 # Earth Prototype Explorer
├── requirements.txt           # Python package requirements
├── vercel.json                # Vercel deployment configuration
├── start_all.bat              # 1-click Windows startup script
└── README.md                  # Project documentation
```

---

## 📄 License
This project is open-source under the MIT License.
