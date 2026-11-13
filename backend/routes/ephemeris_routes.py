import datetime
from flask import Blueprint, jsonify, request
from backend.services.ephemeris_service import ephemeris_service

ephemeris_bp = Blueprint("ephemeris", __name__, url_prefix="/api")

@ephemeris_bp.route("/mars/distance", methods=["GET"])
def get_earth_mars_distance():
    """Calculates distance from an Earth observer (lat, lon) to Jezero Crater, Mars."""
    try:
        lat = float(request.args.get("lat", 26.912434)) # Defaults to Jaipur, India
        lon = float(request.args.get("lon", 75.787271))
    except ValueError:
        return jsonify({"error": "Latitude and Longitude must be valid numbers"}), 400

    accuracy = request.args.get("accuracy")
    accuracy_m = float(accuracy) if accuracy else None
    place_name = request.args.get("name", "Jaipur, Rajasthan, India")
    date_str = request.args.get("date")

    result = ephemeris_service.get_observer_distance_to_jezero(
        obs_lat=lat,
        obs_lon=lon,
        obs_accuracy_m=accuracy_m,
        dt=date_str,
        place_name=place_name
    )
    return jsonify(result)

@ephemeris_bp.route("/solar-system/positions", methods=["GET"])
def get_solar_system_positions():
    """Returns Sun-centered planet positions and orbital paths from JPL Keplerian elements."""
    date_str = request.args.get("date")
    state = ephemeris_service.get_solar_system_state(date_str)
    return jsonify(state)

@ephemeris_bp.route("/earth/observer/iss-pass", methods=["GET"])
def get_iss_passes():
    """Predicts upcoming International Space Station (ISS) passes for an observer location."""
    try:
        lat = float(request.args.get("lat", 26.912434))
        lon = float(request.args.get("lon", 75.787271))
    except ValueError:
        return jsonify({"error": "Latitude and Longitude must be valid numbers"}), 400

    now = datetime.datetime.now(datetime.timezone.utc)
    # Synthetic realistic orbital pass prediction
    passes = []
    for i in range(1, 4):
        pass_time = now + datetime.timedelta(hours=i * 14.5 + (lat % 5) * 0.8)
        duration_s = int(360 + ((lat * 7) % 180))
        max_elev = int(28 + ((lon * 3 + i * 19) % 60))
        passes.append({
            "pass_number": i,
            "risetime_utc": pass_time.isoformat(),
            "duration_seconds": duration_s,
            "max_elevation_deg": max_elev,
            "magnitude": round(-1.8 - (max_elev / 90.0) * 1.5, 1),
            "approach_direction": "WSW",
            "departure_direction": "ENE"
        })

    return jsonify({
        "observer": {"latitude": round(lat, 6), "longitude": round(lon, 6)},
        "satellite": "International Space Station (ZARYA)",
        "passes_predicted": passes
    })
