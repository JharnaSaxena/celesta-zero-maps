from flask import Blueprint, jsonify, request
from backend.services.terrain_service import terrain_service

terrain_bp = Blueprint("terrain", __name__, url_prefix="/api/mars/terrain")

@terrain_bp.route("", methods=["GET"])
def get_terrain_summary():
    """Returns terrain metadata and stats."""
    return jsonify({
        "size": terrain_service.size,
        "span_km": terrain_service.span_km,
        "seed": terrain_service.seed,
        "total_nodes": len(terrain_service.nodes),
        "elevation_bounds": {
            "min_km": round(min(n["height"] for n in terrain_service.nodes), 4),
            "max_km": round(max(n["height"] for n in terrain_service.nodes), 4)
        },
        "slope_bounds": {
            "min_deg": round(min(n["slope"] for n in terrain_service.nodes), 2),
            "max_deg": round(max(n["slope"] for n in terrain_service.nodes), 2)
        },
        "safety_distribution": {
            "favorable": sum(1 for n in terrain_service.nodes if n["margin"] >= 65),
            "caution": sum(1 for n in terrain_service.nodes if 40 <= n["margin"] < 65),
            "critical": sum(1 for n in terrain_service.nodes if n["margin"] < 40)
        }
    })

@terrain_bp.route("/nodes", methods=["GET"])
def get_all_nodes():
    """Returns all 4,225 mesh nodes or a downsampled subset."""
    step = int(request.args.get("step", 1))
    if step <= 1:
        return jsonify({"nodes": terrain_service.nodes, "count": len(terrain_service.nodes)})
    
    subsampled = [n for n in terrain_service.nodes if (n["r"] % step == 0 and n["c"] % step == 0)]
    return jsonify({"nodes": subsampled, "count": len(subsampled), "step": step})

@terrain_bp.route("/sample", methods=["GET"])
def sample_coordinate():
    """Bilinear interpolation at given continuous x and z coordinates."""
    try:
        x = float(request.args.get("x", 0.0))
        z = float(request.args.get("z", 0.0))
    except ValueError:
        return jsonify({"error": "Query parameters 'x' and 'z' must be valid numbers"}), 400

    result = terrain_service.sample_point(x, z)
    return jsonify(result)

@terrain_bp.route("/nearest", methods=["GET"])
def nearest_grid_node():
    """Finds closest mesh vertex to coordinate (x, z)."""
    try:
        x = float(request.args.get("x", 0.0))
        z = float(request.args.get("z", 0.0))
    except ValueError:
        return jsonify({"error": "Query parameters 'x' and 'z' must be valid numbers"}), 400

    node = terrain_service.nearest_node(x, z)
    return jsonify(node)

@terrain_bp.route("/profile", methods=["POST"])
def elevation_profile():
    """Generates an elevation profile between a sequence of waypoints."""
    data = request.get_json(silent=True) or {}
    waypoints = data.get("waypoints", [])
    samples = int(data.get("samples", 50))

    if len(waypoints) < 2:
        return jsonify({"error": "Must provide at least 2 waypoints in body: [{'x': 0, 'z': 0}, ...]"}), 400

    profile = terrain_service.get_elevation_profile(waypoints, samples=samples)
    return jsonify(profile)

@terrain_bp.route("/bbox", methods=["GET"])
def bounding_box_query():
    """Returns terrain nodes inside a bounding box."""
    try:
        min_x = float(request.args.get("min_x", -10))
        max_x = float(request.args.get("max_x", 10))
        min_z = float(request.args.get("min_z", -10))
        max_z = float(request.args.get("max_z", 10))
    except ValueError:
        return jsonify({"error": "Bounding box parameters must be numeric"}), 400

    result = terrain_service.get_bounding_box(min_x, max_x, min_z, max_z)
    return jsonify(result)
