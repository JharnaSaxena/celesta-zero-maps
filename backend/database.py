import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from backend.config import DB_PATH, MOCK_DATA_DIR, LIFELINE_BASE_X, LIFELINE_BASE_Z

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    conn = get_db_connection()
    cursor = conn.cursor()

    # Sites table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sites (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        type TEXT NOT NULL,
        x REAL NOT NULL,
        z REAL NOT NULL,
        elevation REAL DEFAULT 0,
        lat REAL,
        lon REAL,
        note TEXT,
        is_custom INTEGER DEFAULT 0,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Saved mission routes
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS routes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        from_site_id TEXT,
        to_site_id TEXT,
        mode TEXT DEFAULT 'balanced',
        distance_km REAL NOT NULL,
        min_margin INTEGER NOT NULL,
        ascent_m REAL NOT NULL,
        descent_m REAL NOT NULL,
        est_sol_duration REAL NOT NULL,
        waypoints_json TEXT NOT NULL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Mars Perseverance Sample Return Cache
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sample_cache (
        tube_id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        sample_type TEXT NOT NULL,
        sol_collected INTEGER NOT NULL,
        target_feature TEXT NOT NULL,
        x REAL NOT NULL,
        z REAL NOT NULL,
        minerals_json TEXT NOT NULL,
        status TEXT NOT NULL,
        mass_grams REAL NOT NULL,
        notes TEXT
    )
    """)

    # Weather logs (MEDA sol-by-sol)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS weather_logs (
        sol INTEGER PRIMARY KEY,
        terrestrial_date TEXT NOT NULL,
        min_temp_c REAL NOT NULL,
        max_temp_c REAL NOT NULL,
        pressure_pa REAL NOT NULL,
        wind_speed_ms REAL NOT NULL,
        wind_direction TEXT NOT NULL,
        opacity_tau REAL NOT NULL,
        uv_index REAL NOT NULL,
        summary TEXT
    )
    """)

    # Rover state
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS rover_state (
        rover_id TEXT PRIMARY KEY,
        sol INTEGER NOT NULL,
        battery_pct REAL NOT NULL,
        rtg_power_w REAL NOT NULL,
        moxie_o2_g REAL NOT NULL,
        supercam_shots INTEGER NOT NULL,
        mastcam_photos INTEGER NOT NULL,
        odometry_m REAL NOT NULL,
        heading_deg REAL NOT NULL,
        current_x REAL NOT NULL,
        current_z REAL NOT NULL,
        current_elevation REAL NOT NULL,
        status TEXT NOT NULL,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    seed_defaults(conn)
    conn.close()

def seed_defaults(conn):
    cursor = conn.cursor()

    # Seed Sites if empty
    cursor.execute("SELECT COUNT(*) FROM sites")
    if cursor.fetchone()[0] == 0:
        # Core fictional sites matching Terrascope
        initial_sites = [
            ("H01", "Aurora base", "habitat", -5.0, 5.0, 0.42, 18.375, 77.565, "Flat crater-floor candidate near the simulated landing corridor. Assumes a sealed, shielded habitat.", 0),
            ("H02", "Haven terrace", "habitat", 9.0, 7.0, 0.85, 18.420, 77.610, "Secondary habitat candidate on a sheltered terrace. Engineering suitability is unverified.", 0),
            ("R01", "Hydrated mineral hub", "resource", -11.0, -4.0, 0.63, 18.355, 77.545, "Synthetic hydrated-mineral prospect. Resource concentration and extractability are invented.", 0),
            ("R02", "Regolith works", "resource", 8.0, 12.0, 0.51, 18.435, 77.605, "Mock feedstock staging site for construction research; no measured deposit data.", 0),
            ("R03", "Ice prospect", "resource", 15.0, -6.0, 1.12, 18.350, 77.630, "Fictional subsurface ice prospect, not evidence of accessible ice in Jezero.", 0),
            ("S01", "Delta archive", "science", -12.0, -8.0, 1.45, 18.340, 77.540, "Synthetic delta-inspired outcrop for sediment sampling and ancient-environment research.", 0),
            ("S02", "Crater rim station", "science", 16.0, 10.0, 2.30, 18.430, 77.635, "Elevated mock geological survey target on the crater rim.", 0),
            ("S03", "Basin core", "science", 2.0, -5.0, 0.35, 18.352, 77.590, "Simulated basin-floor core-sampling target; no claim of biological evidence.", 0),
            # Authentic Perseverance rover milestones in Jezero
            ("P01", "Octavia E. Butler Landing", "science", -4.2, 4.1, 0.38, 18.378, 77.568, "Actual Perseverance touchdown site on Sol 0 (February 18, 2021).", 0),
            ("P02", "Kodiak Butte", "science", -8.2, -3.1, 0.95, 18.358, 77.552, "Prominent delta remnant showing classic topset and foreset deltaic sedimentary beds.", 0),
            ("P03", "Belva Crater", "science", -1.5, -0.8, 0.29, 18.365, 77.575, "1-kilometer impact crater on the Jezero delta exposing ancient river gravel conglomerates.", 0),
            ("P04", "Three Forks Depot", "resource", -10.5, -5.8, 0.72, 18.348, 77.548, "Sample cache drop location on the delta front for the Mars Sample Return mission.", 0),
            ("P05", "Séítah Unit", "science", -5.5, 2.0, 0.31, 18.370, 77.560, "Ancient igneous olivine-rich rock unit representing the earliest crater floor formation.", 0),
        ]
        cursor.executemany("""
        INSERT INTO sites (id, name, type, x, z, elevation, lat, lon, note, is_custom)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, initial_sites)

    # Seed Sample Cache if empty
    cursor.execute("SELECT COUNT(*) FROM sample_cache")
    if cursor.fetchone()[0] == 0:
        samples = [
            ("ST-01", "Montdenier", "rock_core", 190, "Séítah South", -5.2, 2.2, json.dumps({"Olivine": 45, "Pyroxene": 30, "Carbonate": 15, "Other": 10}), "sealed_onboard", 10.2, "Basaltic rock core with olivine cumulates."),
            ("ST-02", "Salette", "rock_core", 204, "Séítah South", -5.3, 2.1, json.dumps({"Olivine": 42, "Pyroxene": 33, "Carbonate": 17, "Other": 8}), "sealed_onboard", 11.5, "Paired sample to Montdenier."),
            ("ST-03", "Coulettes", "rock_core", 262, "Delta Front", -9.5, -4.8, json.dumps({"Smectite": 38, "Quartz": 12, "Sulfate": 28, "Carbonate": 22}), "depot_dropped", 12.1, "Fine-grained mudstone with clay minerals, deposited in ancient lake waters."),
            ("ST-04", "Robine", "rock_core", 280, "Wildcat Ridge", -10.1, -5.4, json.dumps({"Smectite": 42, "Aromatic Organics": 5, "Sulfate": 35, "Carbonate": 18}), "depot_dropped", 9.8, "High concentration of aromatics and sulfates."),
            ("ST-05", "Malay", "regolith", 320, "Delta Top", -11.2, -6.7, json.dumps({"Silicate": 50, "Iron Oxide": 25, "Perchlorate": 2, "Plagioclase": 23}), "sealed_onboard", 14.3, "Loose Martian regolith and wind-blown dust sample."),
            ("ST-06", "Crosswind", "witness", 4, "Landing Site", -4.2, 4.1, json.dumps({"Clean Witness": 100}), "sealed_onboard", 8.0, "Witness tube to capture terrestrial contamination baseline.")
        ]
        cursor.executemany("""
        INSERT INTO sample_cache (tube_id, name, sample_type, sol_collected, target_feature, x, z, minerals_json, status, mass_grams, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, samples)

    # Seed Weather Logs (MEDA simulated sol records)
    cursor.execute("SELECT COUNT(*) FROM weather_logs")
    if cursor.fetchone()[0] == 0:
        weather_data = [
            (1000, "2023-12-12", -78.5, -16.2, 748.2, 8.4, "ENE", 0.38, 4.2, "Clear Martian skies, diurnal dust devil activity near delta scarp."),
            (1001, "2023-12-13", -79.1, -15.8, 747.8, 9.1, "ENE", 0.40, 4.1, "Mild morning frost detected by MEDA thermal infrared sensor."),
            (1002, "2023-12-14", -77.9, -14.9, 750.1, 7.6, "NE", 0.36, 4.3, "Optimal solar insolation, low atmospheric dust opacity."),
            (1003, "2023-12-15", -76.8, -14.2, 752.4, 11.2, "E", 0.45, 3.9, "Gusty afternoon winds up to 18 m/s off western crater rim."),
            (1004, "2023-12-16", -80.2, -17.5, 745.0, 6.8, "ENE", 0.35, 4.4, "Cold night, high thermal inertia measured on boulder field."),
            (1005, "2023-12-17", -77.4, -15.1, 749.5, 8.0, "NE", 0.37, 4.2, "Favorable conditions for autonomous traverse drive."),
            (1006, "2023-12-18", -78.0, -15.6, 748.9, 8.7, "ENE", 0.39, 4.1, "Stable air pressure, low particulate concentration.")
        ]
        cursor.executemany("""
        INSERT INTO weather_logs (sol, terrestrial_date, min_temp_c, max_temp_c, pressure_pa, wind_speed_ms, wind_direction, opacity_tau, uv_index, summary)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, weather_data)

    # Seed Rover State
    cursor.execute("SELECT COUNT(*) FROM rover_state")
    if cursor.fetchone()[0] == 0:
        rovers = [
            ("Perseverance", 1006, 92.4, 108.5, 122.4, 4820, 24150, 31420.5, 248.5, -4.5, 3.8, 0.40, "Nominal"),
            ("Ingenuity", 72, 88.0, 0.0, 0.0, 0, 360, 17200.0, 192.0, -4.8, 3.5, 0.41, "Completed Historic 72 Flights")
        ]
        cursor.executemany("""
        INSERT INTO rover_state (rover_id, sol, battery_pct, rtg_power_w, moxie_o2_g, supercam_shots, mastcam_photos, odometry_m, heading_deg, current_x, current_z, current_elevation, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, rovers)

    conn.commit()
