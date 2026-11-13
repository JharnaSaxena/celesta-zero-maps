from flask import Blueprint, jsonify, request
from backend.services.weather_service import weather_service

weather_bp = Blueprint("weather", __name__, url_prefix="/api/mars/weather")

@weather_bp.route("/current", methods=["GET"])
def current_weather():
    """Current sol environmental measurements at Jezero Crater."""
    return jsonify(weather_service.get_current_weather())

@weather_bp.route("/forecast", methods=["GET"])
def weather_forecast():
    """7-Sol atmospheric and dust forecast."""
    sols = int(request.args.get("sols", 7))
    return jsonify(weather_service.get_forecast(num_sols=sols))

@weather_bp.route("/history", methods=["GET"])
def weather_history():
    """Historical sol weather records from MEDA instrument logs."""
    limit = int(request.args.get("limit", 30))
    records = weather_service.get_history(limit=limit)
    return jsonify({"count": len(records), "records": records})
