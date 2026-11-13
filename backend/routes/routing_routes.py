import json
from flask import Blueprint, jsonify, request
from backend.database import get_db_connection
from backend.services.routing_service import routing_service

routing_bp = Blueprint("routing", __name__, url_prefix="/api/mars/routes")

@routing_bp.route("/plan", methods=["POST"])
def plan_route():
    """Calculates optimal rover traverse path between sites or coordinates."""
    data = request.get_json(silent=True) or {}
    mode = data.get("mode", "balanced").lower()

    from_site_id = data.get("from_site_id")
    to_site_id = data.get("to_site_id")

    from_x = data.get("from_x")
    from_z = data.get("from_z")
    to_x = data.get("to_x")
    to_z = data.get("to_z")

    # Resolve from site IDs if provided
    conn = get_db_connection()
    if from_site_id:
        row = conn.execute("SELECT x, z FROM sites WHERE id = ?", (from_site_id,)).fetchone()
        if not row:
            conn.close()
            return jsonify({"error": f"Origin site '{from_site_id}' not found"}), 404
        from_x, from_z = row["x"], row["z"]

    if to_site_id:
        row = conn.execute("SELECT x, z FROM sites WHERE id = ?", (to_site_id,)).fetchone()
        if not row:
            conn.close()
            return jsonify({"error": f"Destination site '{to_site_id}' not found"}), 404
        to_x, to_z = row["x"], row["z"]
    conn.close()

    if from_x is None or from_z is None or to_x is None or to_z is None:
        return jsonify({
            "error": "Must specify either ('from_site_id', 'to_site_id') or ('from_x', 'from_z', 'to_x', 'to_z')"
        }), 400

    try:
        from_x, from_z = float(from_x), float(from_z)
        to_x, to_z = float(to_x), float(to_z)
    except ValueError:
        return jsonify({"error": "Coordinates must be numeric"}), 400

    result = routing_service.calculate_route(from_x, from_z, to_x, to_z, mode=mode)
    if "error" in result:
        return jsonify(result), 400

    result["from_site_id"] = from_site_id
    result["to_site_id"] = to_site_id
    return jsonify(result)

@routing_bp.route("", methods=["GET"])
def list_saved_routes():
    """Retrieves list of saved mission traverses."""
    conn = get_db_connection()
    rows = conn.execute("SELECT id, name, from_site_id, to_site_id, mode, distance_km, min_margin, ascent_m, descent_m, est_sol_duration, created_at FROM routes ORDER BY id DESC").fetchall()
    conn.close()
    return jsonify({"count": len(rows), "routes": [dict(r) for r in rows]})

@routing_bp.route("/<int:route_id>", methods=["GET"])
def get_saved_route(route_id):
    """Retrieves full waypoints for a saved traverse."""
    conn = get_db_connection()
    row = conn.execute("SELECT * FROM routes WHERE id = ?", (route_id,)).fetchone()
    conn.close()

    if not row:
        return jsonify({"error": f"Route #{route_id} not found"}), 404

    data = dict(row)
    data["waypoints"] = json.loads(data["waypoints_json"])
    del data["waypoints_json"]
    return jsonify(data)

@routing_bp.route("/save", methods=["POST"])
def save_route():
    """Persists a calculated route to the database."""
    data = request.get_json(silent=True) or {}
    name = data.get("name")
    if not name:
        return jsonify({"error": "'name' is required"}), 400

    from_site_id = data.get("from_site_id")
    to_site_id = data.get("to_site_id")
    mode = data.get("mode", "balanced")
    dist_km = float(data.get("distance_km", 0.0))
    min_margin = int(data.get("min_margin", 0))
    ascent_m = float(data.get("ascent_m", 0.0))
    descent_m = float(data.get("descent_m", 0.0))
    est_sols = float(data.get("estimated_sols", 1.0))
    waypoints = data.get("waypoints", [])

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO routes (name, from_site_id, to_site_id, mode, distance_km, min_margin, ascent_m, descent_m, est_sol_duration, waypoints_json)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (name, from_site_id, to_site_id, mode, dist_km, min_margin, ascent_m, descent_m, est_sols, json.dumps(waypoints)))
    route_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return jsonify({"status": "Route saved", "route_id": route_id}), 201

@routing_bp.route("/<int:route_id>", methods=["DELETE"])
def delete_saved_route(route_id):
    """Deletes saved route."""
    conn = get_db_connection()
    conn.execute("DELETE FROM routes WHERE id = ?", (route_id,))
    conn.commit()
    conn.close()
    return jsonify({"status": "Route deleted", "route_id": route_id})
