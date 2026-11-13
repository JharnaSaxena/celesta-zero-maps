# TerraScope Mars — Jezero Crater Operations Backend (JezeroOps)

A high-performance, scientific mission operations backend for the **TerraScope Explorer** at **Jezero Crater, Mars** (18.38°N, 77.58°E).

Provides real-time Martian Sol time calculations, 3D terrain elevation queries, LIFELINE operational safety scoring, multi-mode rover pathfinding (Dijkstra / A*), Perseverance rover telemetry simulation, MEDA weather tracking, rock core sample tube inventory, and In-Situ Resource Utilization (ISRU) assessments.

---

## Architecture Overview

```
Backend of Jezero Carter/
├── backend/
│   ├── config.py             # Mars scientific constants & model configurations
│   ├── database.py           # SQLite persistence (jezero.db) with auto-seeding
│   ├── app.py                # Flask application factory, CORS, and blueprint registration
│   ├── routes/
│   │   ├── system_routes.py    # Health checks, OpenAPI 3.0 spec, GeoJSON export
│   │   ├── terrain_routes.py   # 3D mesh queries, bilinear interpolation, elevation profile
│   │   ├── lifeline_routes.py  # LIFELINE safety scoring, landing ellipse evaluation
│   │   ├── sites_routes.py     # Mission POIs CRUD (Habitats, Resources, Science, Waypoints)
│   │   ├── routing_routes.py   # Multi-mode rover pathfinding (balanced, safest, fastest, energy)
│   │   ├── telemetry_routes.py # Rover subsystems, instruments, live SSE stream, commands
│   │   ├── weather_routes.py   # MEDA atmospheric measurements & 7-Sol forecasts
│   │   ├── minerals_routes.py  # Jezero mineral formations & ISRU harvesting feasibility
│   │   └── earth_routes.py     # Legacy Nandi Hills Earth prototype support
│   ├── services/
│   │   ├── terrain_service.py  # 65x65 synthetic mesh generation, bilinear interpolation
│   │   ├── lifeline_service.py # LIFELINE hazard math, radiation, and mobility scores
│   │   ├── routing_service.py  # Graph pathfinding, slope/margin weighting, turn guidance
│   │   ├── telemetry_service.py# Mars Sol clock, instruments (MOXIE, Mastcam-Z, SuperCam)
│   │   ├── weather_service.py  # MEDA diurnal temperature cycles, wind vectors, dust tau
│   │   └── earth_service.py    # Earth elevation graph with danger zone avoidance
│   └── static/
│       └── docs.html           # Interactive Swagger UI & Mars Mission Control Dashboard
├── data/
│   ├── jezero.db             # SQLite mission database
│   └── mock/                 # Precomputed fixtures (mars.json, elevation.json, etc.)
├── run_backend.py            # Single-command server starter
├── tests/
│   ├── test_backend.py       # Full pytest suite (10/10 tests)
│   └── mars_native.test.js   # Native Node test suite (4/4 tests)
└── src/services/
    └── apiClient.js          # Frontend integration client with graceful offline fallback
```

---

## Quickstart

### 1. Start the Backend Server
```bash
python run_backend.py
```
- **API Server:** `http://localhost:5000`
- **Interactive Swagger Documentation:** `http://localhost:5000/docs`
- **Health Endpoint:** `http://localhost:5000/api/health`

### 2. Run the Test Suites
Run the backend test suite:
```bash
python -m pytest tests/test_backend.py -v
```

---

## API Endpoints Reference

### 1. Mission & System
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Service uptime, database connectivity, and current Mars Sol |
| `GET` | `/api/info` | Jezero Crater coordinates, radius, and operational constants |
| `GET` | `/api/openapi.json` | Complete OpenAPI 3.0 JSON specification |
| `GET` | `/api/export/geojson` | Export all Jezero sites as RFC 7946 GeoJSON points |

### 2. Terrain & Elevation
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/mars/terrain` | Terrain mesh metadata (bounds, slope limits, safety counts) |
| `GET` | `/api/mars/terrain/sample?x=-5&z=5` | Bilinear interpolation of height, slope, and margin |
| `GET` | `/api/mars/terrain/nearest?x=-5&z=5` | Closest discrete mesh vertex |
| `POST` | `/api/mars/terrain/profile` | Elevation profile and cumulative ascent along waypoints |
| `GET` | `/api/mars/terrain/bbox` | Filter terrain vertices by bounding box |

### 3. LIFELINE Operational Safety Model
$$\text{margin} = \text{clamp}(100 - 2 \times \text{slope}^\circ - 0.32 \times \text{dust} - 1.1 \times \text{base\_dist}_{\text{km}}, 0, 100)$$

- **Favorable:** $\ge 65$
- **Caution:** $40 - 64$
- **Critical:** $< 40$

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/mars/lifeline/assess` | Comprehensive hazard analysis, mobility index, and solar transmission |
| `POST` | `/api/mars/lifeline/landing-zone` | Touchdown safety rating across a landing ellipse |
| `GET` | `/api/mars/lifeline/formula` | Model parameters, coefficients, and threshold definitions |

### 4. Mission Sites & Waypoints (CRUD)
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/mars/sites` | List sites with optional filters (`type`, `tier`, `search`) |
| `GET` | `/api/mars/sites/<id>` | Full intelligence dossier for a specific site |
| `POST` | `/api/mars/sites` | Register a new custom site or rover waypoint |
| `PUT` | `/api/mars/sites/<id>` | Update coordinates, type, or notes |
| `DELETE` | `/api/mars/sites/<id>` | Delete a custom site |

### 5. Rover Traverse Routing
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/mars/routes/plan` | Calculate route between sites or coordinates (`balanced`, `safest`, `fastest`, `energy`) |
| `GET` | `/api/mars/routes` | List saved mission traverses |
| `GET` | `/api/mars/routes/<id>` | Retrieve full waypoints and turns for a saved route |
| `POST` | `/api/mars/routes/save` | Persist a calculated traverse to the database |
| `DELETE` | `/api/mars/routes/<id>` | Delete a saved route |

### 6. Perseverance Rover Telemetry & Command
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/mars/telemetry/current` | Real-time rover subsystems, battery, RTG, instruments |
| `GET` | `/api/mars/telemetry/time` | Mars Sol clock and Local Mean Solar Time (LMST) at Jezero |
| `GET` | `/api/mars/telemetry/stream` | Server-Sent Events (SSE) live telemetry feed |
| `POST` | `/api/mars/telemetry/command` | Dispatch rover command (`DRIVE_TO`, `MOXIE_RUN`, `SUPERCAM_SHOTS`, `MASTCAM_PANORAMA`) |
| `GET` | `/api/mars/telemetry/samples` | Mars Sample Return cache status (rock core tubes, regolith, witness) |
| `GET` | `/api/mars/telemetry/orbiters` | UHF relay pass schedule (MRO, Odyssey, Trace Gas Orbiter) |

### 7. MEDA Weather & Climate
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/mars/weather/current` | Diurnal temperature, atmospheric pressure, wind vector, optical depth $\tau$ |
| `GET` | `/api/mars/weather/forecast` | 7-Sol atmospheric forecast and dust storm advisories |
| `GET` | `/api/mars/weather/history` | Historical sol measurements from the MEDA instrument |

### 8. Geology & In-Situ Resource Utilization (ISRU)
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/mars/minerals` | Major Jezero mineral formations (Clays, Olivine cumulates, Carbonates) |
| `GET` | `/api/mars/minerals/isru-assessment` | Water extraction potential and microwave sintering feasibility |

### 9. Earth Field Explorer Compatibility
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/earth/elevation` | 50×50 Nandi Hills elevation grid |
| `GET` | `/api/earth/minerals` | Mineral deposits |
| `GET` | `/api/earth/danger-zones` | Hazard zone polygons |
| `GET` | `/api/earth/environment` | Weather stations |
| `POST` | `/api/earth/route` | Dijkstra routing avoiding danger zones |

---

## Database Schema (`data/jezero.db`)

- **`sites`**: Site ID, name, category (`habitat`, `resource`, `science`), local $(x, z)$, latitude, longitude, notes, `is_custom`.
- **`routes`**: Saved traverses, distance, ascents, minimum margin, estimated sols, JSON waypoints.
- **`sample_cache`**: Core sample tubes, target geological features, sol collected, mineralogy, status (`sealed_onboard`, `depot_dropped`), mass.
- **`weather_logs`**: Sol records, temperatures, atmospheric pressure, wind speed/direction, opacity, UV index.
- **`rover_state`**: Rover position, odometry, battery state, RTG thermal output, MOXIE O2 cumulative production, SuperCam shots.
