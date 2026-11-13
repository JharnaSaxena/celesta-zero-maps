from flask import Blueprint, jsonify, request
from backend.services.lifeline_service import lifeline_service

lifeline_bp = Blueprint("lifeline", __name__, url_prefix="/api/mars/lifeline")

@lifeline_bp.route("/assess", methods=["POST", "GET"])
def assess_hazard():
    """Calculates comprehensive LIFELINE score and multi-factor hazard assessment."""
    if request.method == "POST":
        data = request.get_json(silent=True) or {}
        x = float(data.get("x", 0.0))
        z = float(data.get("z", 0.0))
    else:
        try:
            x = float(request.args.get("x", 0.0))
            z = float(request.args.get("z", 0.0))
        except ValueError:
            return jsonify({"error": "Parameters 'x' and 'z' must be numeric"}), 400

    assessment = lifeline_service.evaluate_point(x, z)
    return jsonify(assessment)

@lifeline_bp.route("/landing-zone", methods=["POST"])
def evaluate_landing_zone():
    """Evaluates suitability of a landing zone / habitat site within a radius."""
    data = request.get_json(silent=True) or {}
    center_x = float(data.get("x", -5.0))
    center_z = float(data.get("z", 5.0))
    radius_km = float(data.get("radius_km", 1.5))
    samples = int(data.get("samples", 16))

    result = lifeline_service.evaluate_landing_zone(center_x, center_z, radius_km, samples)
    return jsonify(result)

@lifeline_bp.route("/formula", methods=["GET"])
def formula_spec():
    """Returns LIFELINE mathematical model documentation and thresholds."""
    return jsonify({
        "model_name": "LIFELINE Operational Margin",
        "formula": "margin = clamp(100 - (2 * slope_deg) - (0.32 * dust_index) - (1.1 * base_distance_km), 0, 100)",
        "coefficients": {
            "slope_weight": 2.0,
            "dust_weight": 0.32,
            "base_distance_weight": 1.1,
            "reference_base": {"name": "Aurora Base", "x": -5.0, "z": 5.0}
        },
        "thresholds": {
            "favorable": {"min": 65, "max": 100, "status": "Low risk, optimal operational traverse corridor"},
            "caution": {"min": 40, "max": 64, "status": "Moderate risk, requires driver monitoring or AutoNav caution"},
            "critical": {"min": 0, "max": 39, "status": "High risk, hazardous steep slopes or loose dust"}
        }
    })
