import json
import pytest
from backend.app import create_app
from backend.database import init_db

@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client

def test_system_health(client):
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "healthy"
    assert data["database_connected"] is True
    assert "mars_sol" in data

def test_mission_info(client):
    res = client.get("/api/info")
    assert res.status_code == 200
    data = res.get_json()
    assert data["target"]["body"] == "Mars"
    assert data["target"]["region"] == "Jezero Crater, Syrtis Major Quadrangle"
    assert data["target"]["coordinates"]["latitude_deg_north"] == 18.38

def test_openapi_spec(client):
    res = client.get("/api/openapi.json")
    assert res.status_code == 200
    data = res.get_json()
    assert data["openapi"] == "3.0.3"
    assert "/api/mars/routes/plan" in data["paths"]

def test_terrain_endpoints(client):
    # Summary
    res = client.get("/api/mars/terrain")
    assert res.status_code == 200
    data = res.get_json()
    assert data["size"] == 65
    assert data["total_nodes"] == 4225
    assert data["safety_distribution"]["favorable"] > 0

    # Point sample
    res = client.get("/api/mars/terrain/sample?x=-5&z=5")
    assert res.status_code == 200
    sample = res.get_json()
    assert "height_m" in sample
    assert "slope_deg" in sample
    assert "margin" in sample
    assert sample["base_distance_km"] == 0.0

    # Nearest
    res = client.get("/api/mars/terrain/nearest?x=-5.1&z=4.9")
    assert res.status_code == 200
    nearest = res.get_json()
    assert "id" in nearest

    # Profile
    res = client.post("/api/mars/terrain/profile", json={
        "waypoints": [{"x": -5, "z": 5}, {"x": -12, "z": -8}],
        "samples": 20
    })
    assert res.status_code == 200
    profile = res.get_json()
    assert profile["total_distance_km"] > 0
    assert len(profile["profile"]) > 0

def test_lifeline_assessment(client):
    res = client.post("/api/mars/lifeline/assess", json={"x": -12, "z": -8})
    assert res.status_code == 200
    data = res.get_json()
    assert "lifeline_score" in data
    assert data["tier"] in ["Favorable", "Caution", "Critical"]
    assert "hazard_analysis" in data
    assert "mobility_index" in data["hazard_analysis"]

    # Landing zone test
    lz_res = client.post("/api/mars/lifeline/landing-zone", json={"x": -5, "z": 5, "radius_km": 1.0})
    assert lz_res.status_code == 200
    lz_data = lz_res.get_json()
    assert lz_data["suitability"] in ["OPTIMAL", "ACCEPTABLE", "REJECTED"]
    assert "touchdown_safety_index" in lz_data

def test_sites_crud(client):
    # List sites
    res = client.get("/api/mars/sites")
    assert res.status_code == 200
    data = res.get_json()
    assert data["count"] >= 8

    # Filter habitat
    hab_res = client.get("/api/mars/sites?type=habitat")
    assert hab_res.status_code == 200
    hab_data = hab_res.get_json()
    assert all(s["type"] == "habitat" for s in hab_data["sites"])

    # Detail
    site_res = client.get("/api/mars/sites/H01")
    assert site_res.status_code == 200
    site_data = site_res.get_json()
    assert site_data["name"] == "Aurora base"
    assert "margin" in site_data

    # Create Custom Site
    custom_id = "TEST-SITE-01"
    create_res = client.post("/api/mars/sites", json={
        "id": custom_id,
        "name": "Delta Research Outpost",
        "type": "science",
        "x": -10.5,
        "z": -7.2,
        "note": "Automated atmospheric testing station."
    })
    assert create_res.status_code == 201

    # Update Site
    upd_res = client.put(f"/api/mars/sites/{custom_id}", json={
        "name": "Delta Research Outpost (Updated)",
        "type": "science",
        "note": "Updated solar array positioning."
    })
    assert upd_res.status_code == 200
    assert upd_res.get_json()["site"]["name"] == "Delta Research Outpost (Updated)"

    # Delete Custom Site
    del_res = client.delete(f"/api/mars/sites/{custom_id}")
    assert del_res.status_code == 200

def test_traverse_routing(client):
    # Plan balanced route from Aurora base (H01) to Delta archive (S01)
    res = client.post("/api/mars/routes/plan", json={
        "from_site_id": "H01",
        "to_site_id": "S01",
        "mode": "balanced"
    })
    assert res.status_code == 200
    route = res.get_json()
    assert route["distance_km"] > 0
    assert len(route["waypoints"]) >= 2
    assert "estimated_drive_hours" in route
    assert "estimated_sols" in route
    assert len(route["turn_instructions"]) > 0

    # Plan safest route
    safe_res = client.post("/api/mars/routes/plan", json={
        "from_x": -5.0, "from_z": 5.0,
        "to_x": -12.0, "to_z": -8.0,
        "mode": "safest"
    })
    assert safe_res.status_code == 200
    assert safe_res.get_json()["distance_km"] > 0

    # Save route
    save_res = client.post("/api/mars/routes/save", json={
        "name": "Expedition to Delta Archive",
        "from_site_id": "H01",
        "to_site_id": "S01",
        "distance_km": route["distance_km"],
        "min_margin": route["min_margin"],
        "ascent_m": route["ascent_m"],
        "descent_m": route["descent_m"],
        "estimated_sols": route["estimated_sols"],
        "waypoints": route["waypoints"]
    })
    assert save_res.status_code == 201
    route_id = save_res.get_json()["route_id"]

    # Retrieve saved route
    get_res = client.get(f"/api/mars/routes/{route_id}")
    assert get_res.status_code == 200
    assert get_res.get_json()["name"] == "Expedition to Delta Archive"

    # Cleanup route
    del_route = client.delete(f"/api/mars/routes/{route_id}")
    assert del_route.status_code == 200

def test_telemetry_and_rover(client):
    # Rover status
    res = client.get("/api/mars/telemetry/current?rover=Perseverance")
    assert res.status_code == 200
    data = res.get_json()
    assert data["rover_id"] == "Perseverance"
    assert "power" in data
    assert "instruments" in data
    assert "moxie" in data["instruments"]
    assert "mastcam_z" in data["instruments"]

    # Mars time
    time_res = client.get("/api/mars/telemetry/time")
    assert time_res.status_code == 200
    assert time_res.get_json()["current_sol"] >= 1000

    # Command dispatch: MOXIE O2 run
    cmd_res = client.post("/api/mars/telemetry/command", json={
        "rover_id": "Perseverance",
        "command": "MOXIE_RUN",
        "params": {"grams": 5.5}
    })
    assert cmd_res.status_code == 200
    assert "MOXIE" in cmd_res.get_json()["log"]

    # Sample cache tubes
    samp_res = client.get("/api/mars/telemetry/samples")
    assert samp_res.status_code == 200
    samp_data = samp_res.get_json()
    assert samp_data["total_tubes"] >= 6
    assert samp_data["total_mass_grams"] > 0

def test_weather_and_minerals(client):
    # Current weather
    w_res = client.get("/api/mars/weather/current")
    assert w_res.status_code == 200
    w_data = w_res.get_json()
    assert "current_temp_c" in w_data
    assert "atmospheric_pressure_pa" in w_data

    # Forecast
    fc_res = client.get("/api/mars/weather/forecast?sols=7")
    assert fc_res.status_code == 200
    assert len(fc_res.get_json()["forecast"]) == 7

    # Minerals
    m_res = client.get("/api/mars/minerals")
    assert m_res.status_code == 200
    assert m_res.get_json()["count"] >= 4

    # ISRU Assessment
    isru_res = client.get("/api/mars/minerals/isru-assessment?x=-11.5&z=-6.5")
    assert isru_res.status_code == 200
    isru_data = isru_res.get_json()
    assert isru_data["within_deposit_boundary"] is True
    assert "water_yield_liters_per_tonne_regolith" in isru_data["isru_harvesting_metrics"]

def test_earth_prototype_endpoints(client):
    # Elevation
    el_res = client.get("/api/earth/elevation")
    assert el_res.status_code == 200
    assert "values" in el_res.get_json()

    # Route with hazard avoidance
    route_res = client.post("/api/earth/route", json={
        "start": [13.315, 77.635],
        "end": [13.385, 77.705],
        "avoid_danger": True
    })
    assert route_res.status_code == 200
    r_data = route_res.get_json()
    assert r_data["distance_km"] > 0
    assert len(r_data["waypoints"]) > 0


def test_ephemeris_and_distance(client):
    # Test distance from Jaipur, Rajasthan, India
    res = client.get("/api/mars/distance?lat=26.912434&lon=75.787271&name=Jaipur&accuracy=15.5")
    assert res.status_code == 200
    data = res.get_json()
    assert data["observer"]["latitude"] == 26.912434
    assert data["observer"]["longitude"] == 75.787271
    assert data["observer"]["accuracy_radius_m"] == 15.5
    assert data["distance"]["km"] > 50000000 # Distance to Mars > 50M km
    assert data["distance"]["au"] > 0.3
    assert "light_travel_time_formatted" in data["distance"]

    # Test Solar system state
    ss_res = client.get("/api/solar-system/positions")
    assert ss_res.status_code == 200
    ss_data = ss_res.get_json()
    assert len(ss_data["planets"]) == 5
    assert "earth_mars_distance" in ss_data

    # Test ISS pass prediction
    iss_res = client.get("/api/earth/observer/iss-pass?lat=26.912434&lon=75.787271")
    assert iss_res.status_code == 200
    assert len(iss_res.get_json()["passes_predicted"]) == 3
