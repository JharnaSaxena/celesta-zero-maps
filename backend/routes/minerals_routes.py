from flask import Blueprint, jsonify, request
from backend.services.terrain_service import terrain_service

minerals_bp = Blueprint("minerals", __name__, url_prefix="/api/mars/minerals")

JEZERO_MINERAL_REGIONS = [
    {
        "id": "M01",
        "name": "Jezero Delta Front Clay Deposit",
        "primary_mineral": "Fe/Mg Smectite Clay (Nontronite/Saponite)",
        "center_x": -11.5,
        "center_z": -6.5,
        "radius_km": 4.5,
        "composition_pct": {"Smectite Clays": 42, "Hydrated Silica": 18, "Carbonates": 20, "Basaltic Sand": 20},
        "isru_potential": {
            "water_extraction_wt_pct": 7.5,
            "pottery_brick_sintering": "Excellent",
            "biosignature_preservation_index": "Highest Priority"
        },
        "description": "Fine-grained sedimentary mudstones deposited where ancient river emptied into Jezero paleolake ~3.7 billion years ago."
    },
    {
        "id": "M02",
        "name": "Séítah Olivine Cumulate Formation",
        "primary_mineral": "Forsteritic Olivine & Augite Pyroxene",
        "center_x": -5.0,
        "center_z": 1.8,
        "radius_km": 3.0,
        "composition_pct": {"Olivine": 55, "Augite Pyroxene": 25, "Plagioclase": 12, "Iron Oxides": 8},
        "isru_potential": {
            "water_extraction_wt_pct": 0.4,
            "pottery_brick_sintering": "Moderate",
            "biosignature_preservation_index": "Igneous Baseline"
        },
        "description": "Coarse-grained olivine-rich igneous rock representing solidified thick magma lake or volcanic intrusion on early crater floor."
    },
    {
        "id": "M03",
        "name": "Marginal Carbonate Ring",
        "primary_mineral": "Magnesite & Hydrated Sulfates",
        "center_x": 7.5,
        "center_z": 8.5,
        "radius_km": 5.0,
        "composition_pct": {"Magnesium Carbonate": 38, "Calcium Sulfate (Gypsum)": 28, "Silicates": 34},
        "isru_potential": {
            "water_extraction_wt_pct": 5.8,
            "pottery_brick_sintering": "Good (Binder component)",
            "biosignature_preservation_index": "High (Stromatolite analog targets)"
        },
        "description": "Precipitated chemical sedimentary units along ancient bathtub-ring shoreline of Jezero crater lake."
    },
    {
        "id": "M04",
        "name": "Northern Crater Rim Feedstock",
        "primary_mineral": "Impact Melt Breccia & Anorthosite",
        "center_x": 14.0,
        "center_z": 9.0,
        "radius_km": 6.0,
        "composition_pct": {"Anorthosite": 44, "Impact Melt Glass": 30, "Pyroxene": 26},
        "isru_potential": {
            "water_extraction_wt_pct": 0.8,
            "pottery_brick_sintering": "Superior (High glass content enables microwave sintering)",
            "biosignature_preservation_index": "Low"
        },
        "description": "High-silica impact melt breccia formed during the giant Isidis Basin impact event that created the host bedrock."
    }
]

@minerals_bp.route("", methods=["GET"])
def list_minerals():
    """Lists geological mineral formations and ISRU resource targets in Jezero Crater."""
    return jsonify({
        "count": len(JEZERO_MINERAL_REGIONS),
        "target_crater": "Jezero (18.38°N, 77.58°E)",
        "datasets_integrated": ["CRISM (Compact Reconnaissance Imaging Spectrometer)", "SuperCam LIBS", "PIXL XRF"],
        "formations": JEZERO_MINERAL_REGIONS
    })

@minerals_bp.route("/isru-assessment", methods=["GET"])
def isru_analysis():
    """Calculates In-Situ Resource Utilization (ISRU) feasibility for given coordinates."""
    try:
        x = float(request.args.get("x", -11.0))
        z = float(request.args.get("z", -4.0))
    except ValueError:
        return jsonify({"error": "Coordinates 'x' and 'z' must be numeric"}), 400

    sample = terrain_service.sample_point(x, z)

    # Find closest mineral formation
    closest = None
    min_dist = float("inf")
    for region in JEZERO_MINERAL_REGIONS:
        dist = ((region["center_x"] - x)**2 + (region["center_z"] - z)**2)**0.5
        if dist < min_dist:
            min_dist = dist
            closest = region

    is_within = min_dist <= closest["radius_km"]

    return jsonify({
        "coordinates": {"x": x, "z": z},
        "terrain_elevation_m": sample["height_m"],
        "nearest_mineral_deposit": closest["name"],
        "distance_to_deposit_center_km": round(min_dist, 2),
        "within_deposit_boundary": is_within,
        "estimated_composition": closest["composition_pct"] if is_within else {"Undifferentiated Regolith": 70, "Basalt": 30},
        "isru_harvesting_metrics": {
            "water_yield_liters_per_tonne_regolith": round(closest["isru_potential"]["water_extraction_wt_pct"] * 10 if is_within else 15.0, 1),
            "sintering_feasibility": closest["isru_potential"]["pottery_brick_sintering"] if is_within else "Moderate",
            "trafficability_risk": "Favorable" if sample["slope_deg"] < 10 else "High Slope Constraint"
        }
    })
