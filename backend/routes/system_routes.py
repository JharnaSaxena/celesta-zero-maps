import time
from datetime import datetime, timezone
from flask import Blueprint, jsonify, request
from backend.config import JEZERO_LAT, JEZERO_LON, JEZERO_RADIUS_KM, MARS_RADIUS_KM
from backend.database import get_db_connection
from backend.services.telemetry_service import telemetry_service

system_bp = Blueprint("system", __name__, url_prefix="/api")
START_TIME = time.time()

@system_bp.route("/health", methods=["GET"])
def health_check():
    """System health check and diagnostic status."""
    db_ok = False
    try:
        conn = get_db_connection()
        conn.execute("SELECT 1").fetchone()
        conn.close()
        db_ok = True
    except Exception:
        db_ok = False

    mars_time = telemetry_service.get_mars_time()

    return jsonify({
        "status": "healthy" if db_ok else "degraded",
        "service": "Jezero Crater Mission Operations Backend",
        "version": "2.4.0",
        "uptime_seconds": round(time.time() - START_TIME, 1),
        "database_connected": db_ok,
        "mars_sol": mars_time["current_sol"],
        "timestamp_utc": datetime.now(timezone.utc).isoformat()
    })

@system_bp.route("/info", methods=["GET"])
def mission_info():
    """Jezero Carter Mission specifications and constants."""
    return jsonify({
        "mission_name": "TerraScope Mars — Jezero Crater Operations",
        "target": {
            "body": "Mars",
            "region": "Jezero Crater, Syrtis Major Quadrangle",
            "coordinates": {
                "latitude_deg_north": JEZERO_LAT,
                "longitude_deg_east": JEZERO_LON
            },
            "crater_radius_km": JEZERO_RADIUS_KM,
            "mean_mars_radius_km": MARS_RADIUS_KM,
            "primary_outpost": {"name": "Aurora Base", "local_x": -5.0, "local_z": 5.0}
        },
        "endpoints": {
            "terrain": "/api/mars/terrain",
            "lifeline_safety": "/api/mars/lifeline/assess",
            "sites": "/api/mars/sites",
            "traverse_routing": "/api/mars/routes/plan",
            "rover_telemetry": "/api/mars/telemetry/current",
            "telemetry_stream": "/api/mars/telemetry/stream",
            "weather": "/api/mars/weather/current",
            "minerals_isru": "/api/mars/minerals",
            "earth_legacy": "/api/earth/elevation",
            "interactive_docs": "/docs",
            "openapi_spec": "/api/openapi.json"
        }
    })

@system_bp.route("/export/geojson", methods=["GET"])
def export_geojson():
    """Exports Jezero mission sites as a standard GeoJSON FeatureCollection."""
    conn = get_db_connection()
    rows = conn.execute("SELECT * FROM sites").fetchall()
    conn.close()

    features = []
    for r in rows:
        site = dict(r)
        features.append({
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [site["lon"], site["lat"], site["elevation"] * 1000.0]
            },
            "properties": {
                "id": site["id"],
                "name": site["name"],
                "type": site["type"],
                "local_x_km": site["x"],
                "local_z_km": site["z"],
                "note": site["note"],
                "is_custom": bool(site["is_custom"])
            }
        })

    return jsonify({
        "type": "FeatureCollection",
        "crs": {
            "type": "name",
            "properties": {"name": "urn:ogc:def:crs:OGC:1.3:CRS84"}
        },
        "features": features
    })

@system_bp.route("/openapi.json", methods=["GET"])
def openapi_spec():
    """OpenAPI 3.0 schema specification for interactive documentation."""
    spec = {
        "openapi": "3.0.3",
        "info": {
            "title": "Jezero Crater Operations & TerraScope API",
            "description": "Comprehensive Mars mission operations backend providing real-time telemetry, 3D terrain elevation queries, LIFELINE safety assessment, Dijkstra/A* rover pathfinding, MEDA weather intelligence, and rock core sample tracking.",
            "version": "2.4.0",
            "contact": {"name": "Jezero Carter Mission Operations", "url": "https://github.com/lokeshsp2010/Terrascope-explorer"}
        },
        "servers": [{"url": "/", "description": "Local Jezero Mission Server"}],
        "paths": {
            "/api/health": {
                "get": {
                    "summary": "System Health",
                    "description": "Checks system operational status and database connection.",
                    "responses": {"200": {"description": "System status"}}
                }
            },
            "/api/info": {
                "get": {
                    "summary": "Mission Overview",
                    "description": "Returns Jezero Carter coordinates, crater dimensions, and active endpoints.",
                    "responses": {"200": {"description": "Mission specifications"}}
                }
            },
            "/api/mars/terrain": {
                "get": {
                    "summary": "Terrain Summary",
                    "description": "Returns mesh grid statistics, elevation limits, and safety margin distribution.",
                    "responses": {"200": {"description": "Terrain metadata"}}
                }
            },
            "/api/mars/terrain/sample": {
                "get": {
                    "summary": "Sample Point Elevation & Margin",
                    "parameters": [
                        {"name": "x", "in": "query", "required": True, "schema": {"type": "number", "example": -5.0}},
                        {"name": "z", "in": "query", "required": True, "schema": {"type": "number", "example": 5.0}}
                    ],
                    "responses": {"200": {"description": "Bilinearly interpolated terrain point data"}}
                }
            },
            "/api/mars/terrain/profile": {
                "post": {
                    "summary": "Elevation Profile",
                    "requestBody": {
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "waypoints": {"type": "array", "items": {"type": "object"}},
                                        "samples": {"type": "integer", "default": 50}
                                    }
                                }
                            }
                        }
                    },
                    "responses": {"200": {"description": "Step-by-step elevation profile"}}
                }
            },
            "/api/mars/lifeline/assess": {
                "post": {
                    "summary": "LIFELINE Hazard Assessment",
                    "requestBody": {
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "x": {"type": "number", "example": -12.0},
                                        "z": {"type": "number", "example": -8.0}
                                    }
                                }
                            }
                        }
                    },
                    "responses": {"200": {"description": "Comprehensive hazard score, radiation, mobility, and recommendations"}}
                }
            },
            "/api/mars/lifeline/landing-zone": {
                "post": {
                    "summary": "Landing Zone Suitability Evaluation",
                    "requestBody": {
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "x": {"type": "number", "example": -5.0},
                                        "z": {"type": "number", "example": 5.0},
                                        "radius_km": {"type": "number", "default": 1.5}
                                    }
                                }
                            }
                        }
                    },
                    "responses": {"200": {"description": "Touchdown safety score and slope analysis"}}
                }
            },
            "/api/mars/sites": {
                "get": {
                    "summary": "List Mission Sites",
                    "parameters": [
                        {"name": "type", "in": "query", "schema": {"type": "string", "enum": ["habitat", "resource", "science"]}},
                        {"name": "tier", "in": "query", "schema": {"type": "string", "enum": ["Favorable", "Caution", "Critical"]}},
                        {"name": "search", "in": "query", "schema": {"type": "string"}}
                    ],
                    "responses": {"200": {"description": "List of mission places enriched with safety scores"}}
                },
                "post": {
                    "summary": "Create Custom Mission Site",
                    "requestBody": {
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "required": ["id", "name", "x", "z"],
                                    "properties": {
                                        "id": {"type": "string", "example": "C01"},
                                        "name": {"type": "string", "example": "Kodiak North Ridge"},
                                        "type": {"type": "string", "example": "science"},
                                        "x": {"type": "number", "example": -8.5},
                                        "z": {"type": "number", "example": -3.5},
                                        "note": {"type": "string"}
                                    }
                                }
                            }
                        }
                    },
                    "responses": {"201": {"description": "Site successfully registered"}}
                }
            },
            "/api/mars/routes/plan": {
                "post": {
                    "summary": "Plan Rover Traverse Route",
                    "requestBody": {
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "from_site_id": {"type": "string", "example": "H01"},
                                        "to_site_id": {"type": "string", "example": "S01"},
                                        "mode": {"type": "string", "enum": ["balanced", "safest", "fastest", "energy"], "default": "balanced"}
                                    }
                                }
                            }
                        }
                    },
                    "responses": {"200": {"description": "Optimal path, 3D distance, ascents, sol duration, and turn-by-turn guidance"}}
                }
            },
            "/api/mars/telemetry/current": {
                "get": {
                    "summary": "Current Rover Telemetry",
                    "parameters": [{"name": "rover", "in": "query", "schema": {"type": "string", "default": "Perseverance"}}],
                    "responses": {"200": {"description": "Full rover subsystems status, instruments, and power"}}
                }
            },
            "/api/mars/telemetry/time": {
                "get": {
                    "summary": "Mars Sol Clock at Jezero",
                    "responses": {"200": {"description": "Martian Sol number, LMST, and sun elevation angle"}}
                }
            },
            "/api/mars/telemetry/command": {
                "post": {
                    "summary": "Dispatch Rover Command",
                    "requestBody": {
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "required": ["command"],
                                    "properties": {
                                        "command": {"type": "string", "enum": ["DRIVE_TO", "MOXIE_RUN", "SUPERCAM_SHOTS", "MASTCAM_PANORAMA"]},
                                        "params": {"type": "object"}
                                    }
                                }
                            }
                        }
                    },
                    "responses": {"200": {"description": "Command outcome log"}}
                }
            },
            "/api/mars/telemetry/samples": {
                "get": {
                    "summary": "Mars Sample Return Tube Cache",
                    "responses": {"200": {"description": "Sealed rock core samples and delta sediment tubes"}}
                }
            },
            "/api/mars/weather/current": {
                "get": {
                    "summary": "Current Jezero Weather",
                    "responses": {"200": {"description": "Atmospheric pressure, min/max temperatures, wind vector, optical depth"}}
                }
            },
            "/api/mars/weather/forecast": {
                "get": {
                    "summary": "7-Sol Weather Forecast",
                    "responses": {"200": {"description": "Multi-sol predictions"}}
                }
            },
            "/api/mars/minerals": {
                "get": {
                    "summary": "Jezero Mineralogy Formations",
                    "responses": {"200": {"description": "Clay, carbonate, olivine deposits and ISRU feasibility"}}
                }
            },
            "/api/earth/elevation": {
                "get": {
                    "summary": "Earth Nandi Hills Elevation Grid",
                    "responses": {"200": {"description": "Elevation grid data"}}
                }
            },
            "/api/earth/route": {
                "post": {
                    "summary": "Earth Route Planner Avoiding Hazards",
                    "requestBody": {
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "required": ["start", "end"],
                                    "properties": {
                                        "start": {"type": "array", "items": {"type": "number"}, "example": [13.315, 77.635]},
                                        "end": {"type": "array", "items": {"type": "number"}, "example": [13.385, 77.705]},
                                        "avoid_danger": {"type": "boolean", "default": True}
                                    }
                                }
                            }
                        }
                    },
                    "responses": {"200": {"description": "Calculated Earth route"}}
                }
            }
        }
    }
    return jsonify(spec)
