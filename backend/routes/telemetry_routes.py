import json
from flask import Blueprint, jsonify, request, Response
from backend.database import get_db_connection
from backend.services.telemetry_service import telemetry_service

telemetry_bp = Blueprint("telemetry", __name__, url_prefix="/api/mars/telemetry")

@telemetry_bp.route("/current", methods=["GET"])
def current_telemetry():
    """Current live telemetry snapshot for Mars surface assets."""
    rover = request.args.get("rover", "Perseverance")
    status = telemetry_service.get_rover_status(rover)
    return jsonify(status)

@telemetry_bp.route("/time", methods=["GET"])
def mars_clock():
    """Current Mars sol, mission sol, and Local Mean Solar Time (LMST) at Jezero."""
    clock_info = telemetry_service.get_mars_time()
    return jsonify(clock_info)

@telemetry_bp.route("/stream", methods=["GET"])
def live_telemetry_stream():
    """Server-Sent Events (SSE) continuous live telemetry feed."""
    return Response(
        telemetry_service.generate_telemetry_stream(),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

@telemetry_bp.route("/command", methods=["POST"])
def dispatch_command():
    """Dispatches telecommand to rover (Drive, MOXIE O2, SuperCam, Mastcam)."""
    data = request.get_json(silent=True) or {}
    rover_id = data.get("rover_id", "Perseverance")
    cmd = data.get("command")
    params = data.get("params", {})

    if not cmd:
        return jsonify({"error": "'command' field is required. E.g. DRIVE_TO, MOXIE_RUN, SUPERCAM_SHOTS, MASTCAM_PANORAMA"}), 400

    result = telemetry_service.execute_command(rover_id, cmd, params)
    status_code = 400 if "error" in result else 200
    return jsonify(result), status_code

@telemetry_bp.route("/samples", methods=["GET"])
def list_sample_cache():
    """Mars Sample Return cache status (Perseverance sealed and dropped sample tubes)."""
    conn = get_db_connection()
    rows = conn.execute("SELECT * FROM sample_cache ORDER BY sol_collected ASC").fetchall()
    conn.close()

    samples = []
    for r in rows:
        item = dict(r)
        item["minerals"] = json.loads(item["minerals_json"])
        del item["minerals_json"]
        samples.append(item)

    return jsonify({
        "total_tubes": len(samples),
        "onboard_tubes": sum(1 for s in samples if s["status"] == "sealed_onboard"),
        "depot_tubes": sum(1 for s in samples if s["status"] == "depot_dropped"),
        "total_mass_grams": round(sum(s["mass_grams"] for s in samples), 1),
        "samples": samples
    })

@telemetry_bp.route("/orbiters", methods=["GET"])
def orbiter_passes():
    """Orbital communication relay schedule over Jezero Crater."""
    status = telemetry_service.get_rover_status("Perseverance")
    return jsonify({"passes": status.get("orbiter_communications", [])})
