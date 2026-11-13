from flask import Blueprint, jsonify, request
from backend.services.earth_service import earth_service

earth_bp = Blueprint("earth", __name__, url_prefix="/api/earth")

@earth_bp.route("/elevation", methods=["GET"])
def get_elevation():
    """Elevation grid and boundaries for Nandi Hills Earth prototype."""
    if not earth_service.elevation_data:
        return jsonify({"error": "Elevation data not available"}), 500
    return jsonify(earth_service.elevation_data)

@earth_bp.route("/minerals", methods=["GET"])
def get_minerals():
    """Mineral deposit locations and mineralogical compositions."""
    if not earth_service.minerals_data:
        return jsonify({"error": "Minerals data not available"}), 500
    return jsonify(earth_service.minerals_data)

@earth_bp.route("/danger-zones", methods=["GET"])
def get_danger_zones():
    """Simulated hazardous terrain polygons and risk severities."""
    if not earth_service.danger_zones_data:
        return jsonify({"error": "Danger zones data not available"}), 500
    return jsonify(earth_service.danger_zones_data)

@earth_bp.route("/environment", methods=["GET"])
def get_environment():
    """Environmental sensor stations (temperature, humidity, wind, AQI)."""
    if not earth_service.environment_data:
        return jsonify({"error": "Environment data not available"}), 500
    return jsonify(earth_service.environment_data)

@earth_bp.route("/route", methods=["POST"])
def plan_earth_route():
    """Calculates weighted route with optional danger zone avoidance."""
    data = request.get_json(silent=True) or {}
    start = data.get("start")
    end = data.get("end")
    avoid = bool(data.get("avoid_danger", True))

    if not start or not end or len(start) < 2 or len(end) < 2:
        return jsonify({"error": "Must provide 'start': [lat, lng] and 'end': [lat, lng]"}), 400

    try:
        s_lat, s_lng = float(start[0]), float(start[1])
        e_lat, e_lng = float(end[0]), float(end[1])
    except ValueError:
        return jsonify({"error": "Coordinates must be numbers"}), 400

    route_res = earth_service.calculate_route(s_lat, s_lng, e_lat, e_lng, avoid_danger=avoid)
    return jsonify(route_res)
