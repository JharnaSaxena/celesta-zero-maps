from flask import Blueprint, jsonify, request
from backend.database import get_db_connection
from backend.services.terrain_service import terrain_service

sites_bp = Blueprint("sites", __name__, url_prefix="/api/mars/sites")

def enrich_site(site_dict):
    """Enriches site record with live terrain model margin, slope, and elevation."""
    x = site_dict["x"]
    z = site_dict["z"]
    sample = terrain_service.sample_point(x, z)
    site_dict["elevation_m"] = sample["height_m"]
    site_dict["slope_deg"] = sample["slope_deg"]
    site_dict["dust_index"] = sample["dust_index"]
    site_dict["base_distance_km"] = sample["base_distance_km"]
    site_dict["margin"] = sample["margin"]
    site_dict["tier"] = sample["tier"]
    return site_dict

@sites_bp.route("", methods=["GET"])
def list_sites():
    """Lists Jezero mission sites with filtering by type, tier, or search query."""
    category = request.args.get("type")
    tier_filter = request.args.get("tier")
    query = request.args.get("search", "").strip().lower()

    conn = get_db_connection()
    rows = conn.execute("SELECT * FROM sites ORDER BY id ASC").fetchall()
    conn.close()

    results = []
    for r in rows:
        site = enrich_site(dict(r))

        if category and site["type"].lower() != category.lower():
            continue
        if tier_filter and site["tier"].lower() != tier_filter.lower():
            continue
        if query:
            searchable = f"{site['id']} {site['name']} {site['type']} {site.get('note', '')}".lower()
            if query not in searchable:
                continue

        results.append(site)

    return jsonify({"count": len(results), "sites": results})

@sites_bp.route("/<site_id>", methods=["GET"])
def get_site(site_id):
    """Fetches full intelligence for a specific site."""
    conn = get_db_connection()
    row = conn.execute("SELECT * FROM sites WHERE id = ?", (site_id,)).fetchone()
    conn.close()

    if not row:
        return jsonify({"error": f"Site '{site_id}' not found"}), 404

    site = enrich_site(dict(row))
    return jsonify(site)

@sites_bp.route("", methods=["POST"])
def create_site():
    """Adds a new custom mission waypoint or landing candidate."""
    data = request.get_json(silent=True) or {}
    site_id = data.get("id")
    name = data.get("name")
    site_type = data.get("type", "science")

    if not site_id or not name:
        return jsonify({"error": "Fields 'id' and 'name' are required"}), 400

    try:
        x = float(data.get("x", 0.0))
        z = float(data.get("z", 0.0))
    except ValueError:
        return jsonify({"error": "'x' and 'z' must be numeric coordinates"}), 400

    sample = terrain_service.sample_point(x, z)
    elev = sample["height_km"]
    note = data.get("note", "Custom operational waypoint.")

    # Calculate approximate Jezero latitude/longitude from local x,z
    # Local span is 50 km centered at lat 18.38, lon 77.58
    # 1 deg lat ~ 59.2 km on Mars; 1 deg lon ~ 56.1 km at 18.38°N
    approx_lat = 18.38 + (z / 59.2)
    approx_lon = 77.58 + (x / 56.1)

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
        INSERT INTO sites (id, name, type, x, z, elevation, lat, lon, note, is_custom)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
        """, (site_id, name, site_type, x, z, elev, approx_lat, approx_lon, note))
        conn.commit()
    except Exception as e:
        conn.close()
        return jsonify({"error": f"Could not create site: {str(e)}"}), 400
    conn.close()

    created = enrich_site({
        "id": site_id, "name": name, "type": site_type,
        "x": x, "z": z, "elevation": elev, "lat": approx_lat, "lon": approx_lon,
        "note": note, "is_custom": 1
    })
    return jsonify({"status": "Site created", "site": created}), 201

@sites_bp.route("/<site_id>", methods=["PUT"])
def update_site(site_id):
    """Updates custom or existing site details."""
    data = request.get_json(silent=True) or {}
    conn = get_db_connection()
    row = conn.execute("SELECT * FROM sites WHERE id = ?", (site_id,)).fetchone()
    if not row:
        conn.close()
        return jsonify({"error": f"Site '{site_id}' not found"}), 404

    current = dict(row)
    name = data.get("name", current["name"])
    site_type = data.get("type", current["type"])
    note = data.get("note", current["note"])
    x = float(data.get("x", current["x"]))
    z = float(data.get("z", current["z"]))

    conn.execute("""
    UPDATE sites
    SET name = ?, type = ?, note = ?, x = ?, z = ?
    WHERE id = ?
    """, (name, site_type, note, x, z, site_id))
    conn.commit()
    conn.close()

    updated = enrich_site({
        "id": site_id, "name": name, "type": site_type, "x": x, "z": z,
        "elevation": current["elevation"], "lat": current["lat"], "lon": current["lon"],
        "note": note, "is_custom": current["is_custom"]
    })
    return jsonify({"status": "Site updated", "site": updated})

@sites_bp.route("/<site_id>", methods=["DELETE"])
def delete_site(site_id):
    """Deletes custom site."""
    conn = get_db_connection()
    row = conn.execute("SELECT is_custom FROM sites WHERE id = ?", (site_id,)).fetchone()
    if not row:
        conn.close()
        return jsonify({"error": f"Site '{site_id}' not found"}), 404

    if row["is_custom"] == 0:
        conn.close()
        return jsonify({"error": "Cannot delete core mission site"}), 403

    conn.execute("DELETE FROM sites WHERE id = ?", (site_id,))
    conn.commit()
    conn.close()
    return jsonify({"status": "Site deleted", "site_id": site_id})
