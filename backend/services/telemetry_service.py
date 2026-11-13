import json
import math
import time
from datetime import datetime, timezone
from backend.config import JEZERO_LAT, JEZERO_LON, SOL_DURATION_SECONDS
from backend.database import get_db_connection

# Perseverance touchdown UTC: 2021-02-18 20:55:00 UTC
LANDING_UTC_TS = 1613681700.0

class TelemetryService:
    def __init__(self):
        self.landing_ts = LANDING_UTC_TS

    def get_mars_time(self):
        now_ts = time.time()
        elapsed_sec = now_ts - self.landing_ts
        sol = int(elapsed_sec // SOL_DURATION_SECONDS)
        sol_seconds = elapsed_sec % SOL_DURATION_SECONDS

        # Convert to Mars Local Mean Solar Time (LMST) at Jezero Crater (77.58°E)
        # 360 degrees = 24 Mars hours -> 1 degree = 4 Mars minutes
        lon_offset_sec = (JEZERO_LON / 360.0) * SOL_DURATION_SECONDS
        local_sol_sec = (sol_seconds + lon_offset_sec) % SOL_DURATION_SECONDS

        hours = int(local_sol_sec // 3698.9685)
        mins = int((local_sol_sec % 3698.9685) // 61.649)
        secs = int((local_sol_sec % 61.649) / 1.027)

        # Solar elevation angle approximation at Jezero
        hour_angle = (local_sol_sec / SOL_DURATION_SECONDS) * 2.0 * math.pi - math.pi
        sun_elevation = max(-90.0, min(90.0, math.degrees(math.asin(math.cos(hour_angle) * math.cos(math.radians(JEZERO_LAT))))))

        return {
            "current_sol": sol,
            "mission_day": sol + 1,
            "local_solar_time": f"{hours:02d}:{mins:02d}:{secs:02d} LMST",
            "hours": hours,
            "minutes": mins,
            "sun_elevation_deg": round(sun_elevation, 1),
            "is_daylight": sun_elevation > 0,
            "earth_utc": datetime.now(timezone.utc).isoformat()
        }

    def get_rover_status(self, rover_id="Perseverance"):
        conn = get_db_connection()
        row = conn.execute("SELECT * FROM rover_state WHERE rover_id = ?", (rover_id,)).fetchone()
        conn.close()

        if not row:
            return {"error": f"Rover {rover_id} not found"}

        data = dict(row)
        time_info = self.get_mars_time()

        # Dynamic live instrument simulation based on solar time
        is_day = time_info["is_daylight"]
        sun_elev = time_info["sun_elevation_deg"]

        instruments = {
            "moxie": {
                "name": "Mars Oxygen ISRU Experiment",
                "status": "Standby" if not is_day else "Ready for Run",
                "total_o2_produced_grams": data["moxie_o2_g"],
                "production_rate_g_per_hr": 6.4 if is_day else 0.0,
                "soxe_cell_temp_c": 798.2 if is_day else 24.0,
                "power_draw_watts": 300.0 if is_day else 5.0
            },
            "mastcam_z": {
                "name": "Mastcam-Z Multispectral Stereo Camera",
                "status": "Nominal",
                "total_photos_taken": data["mastcam_photos"],
                "azimuth_deg": 142.5,
                "elevation_deg": -8.2,
                "active_filter_left": "L1 (Clear)",
                "active_filter_right": "R1 (Clear)",
                "zoom_focal_length_mm": 110.0
            },
            "supercam": {
                "name": "SuperCam Laser & Spectrometer",
                "status": "Armed",
                "total_laser_shots": data["supercam_shots"],
                "last_target": "Séítah coarse grain outcrop",
                "microphone_status": "Listening (wind audio recorded)"
            },
            "pixl": {
                "name": "Planetary Instrument for X-ray Lithochemistry",
                "status": "Idle on Arm",
                "sensor_head_temp_c": -42.1,
                "scans_completed": 84
            },
            "rimfax": {
                "name": "Radar Imager for Mars' Subsurface Experiment",
                "status": "Continuous Ground Sounding Active",
                "depth_penetration_m": 8.7,
                "bandwidth_mhz": "150 - 1200",
                "dielectric_permittivity": 3.4
            },
            "meda": {
                "name": "Mars Environmental Dynamics Analyzer",
                "status": "Operational",
                "air_temp_c": round(-65.0 + max(0, sun_elev) * 0.9, 1),
                "ground_temp_c": round(-75.0 + max(0, sun_elev) * 1.2, 1),
                "pressure_pa": 748.5,
                "relative_humidity_pct": 3.2,
                "wind_speed_ms": 7.4
            }
        }

        # Active communication orbiter pass windows
        orbiters = [
            {
                "name": "Mars Reconnaissance Orbiter (MRO)",
                "pass_status": "Approaching AOS (Acquisition of Signal)",
                "next_pass_in_minutes": 24,
                "duration_minutes": 14,
                "max_elevation_deg": 68.2,
                "frequency_band": "UHF (Electra Transceiver)",
                "bandwidth_kbps": 2048
            },
            {
                "name": "ESA Trace Gas Orbiter (TGO)",
                "pass_status": "Scheduled",
                "next_pass_in_minutes": 142,
                "duration_minutes": 11,
                "max_elevation_deg": 52.0,
                "frequency_band": "UHF",
                "bandwidth_kbps": 1024
            },
            {
                "name": "2001 Mars Odyssey (ODY)",
                "pass_status": "Scheduled",
                "next_pass_in_minutes": 310,
                "duration_minutes": 9,
                "max_elevation_deg": 38.5,
                "frequency_band": "UHF",
                "bandwidth_kbps": 256
            }
        ]

        return {
            "rover_id": data["rover_id"],
            "sol": time_info["current_sol"],
            "mars_time": time_info,
            "status": data["status"],
            "power": {
                "battery_pct": round(data["battery_pct"], 1),
                "rtg_thermal_power_watts": round(data["rtg_power_w"], 1),
                "bus_voltage_v": 32.4,
                "power_state": "Optimal RTG Power"
            },
            "mobility": {
                "total_odometry_meters": round(data["odometry_m"], 1),
                "heading_deg": round(data["heading_deg"], 1),
                "position": {
                    "x_km": data["current_x"],
                    "z_km": data["current_z"],
                    "elevation_km": data["current_elevation"]
                },
                "hazcam_status": "Clear",
                "drive_motor_temps_c": [ -12.4, -11.8, -13.1, -12.9, -11.5, -12.0 ]
            },
            "instruments": instruments,
            "orbiter_communications": orbiters
        }

    def execute_command(self, rover_id, command_type, params=None):
        params = params or {}
        conn = get_db_connection()
        cursor = conn.cursor()

        row = cursor.execute("SELECT * FROM rover_state WHERE rover_id = ?", (rover_id,)).fetchone()
        if not row:
            conn.close()
            return {"error": f"Rover {rover_id} not found"}

        current = dict(row)
        log_entry = ""

        if command_type == "DRIVE_TO":
            target_x = float(params.get("x", current["current_x"]))
            target_z = float(params.get("z", current["current_z"]))
            drive_m = math.hypot(target_x - current["current_x"], target_z - current["current_z"]) * 1000.0
            new_odo = current["odometry_m"] + drive_m
            new_heading = (math.degrees(math.atan2(target_x - current["current_x"], target_z - current["current_z"])) + 360) % 360
            cursor.execute("""
            UPDATE rover_state
            SET current_x = ?, current_z = ?, odometry_m = ?, heading_deg = ?, status = 'Traverse Completed'
            WHERE rover_id = ?
            """, (target_x, target_z, new_odo, new_heading, rover_id))
            log_entry = f"Navigated {round(drive_m, 1)}m to ({target_x}, {target_z})"

        elif command_type == "MOXIE_RUN":
            o2_generated = float(params.get("grams", 6.0))
            new_o2 = current["moxie_o2_g"] + o2_generated
            cursor.execute("""
            UPDATE rover_state
            SET moxie_o2_g = ?, status = 'MOXIE Extraction Finished'
            WHERE rover_id = ?
            """, (new_o2, rover_id))
            log_entry = f"MOXIE completed oxygen synthesis: +{o2_generated}g O2 produced."

        elif command_type == "SUPERCAM_SHOTS":
            shots = int(params.get("shots", 30))
            new_shots = current["supercam_shots"] + shots
            cursor.execute("""
            UPDATE rover_state
            SET supercam_shots = ?, status = 'SuperCam Laser Fired'
            WHERE rover_id = ?
            """, (new_shots, rover_id))
            log_entry = f"SuperCam fired {shots} laser pulses on rock target."

        elif command_type == "MASTCAM_PANORAMA":
            frames = int(params.get("frames", 142))
            new_photos = current["mastcam_photos"] + frames
            cursor.execute("""
            UPDATE rover_state
            SET mastcam_photos = ?, status = 'Panorama Stitched'
            WHERE rover_id = ?
            """, (new_photos, rover_id))
            log_entry = f"Mastcam-Z acquired 360° panorama ({frames} images)."

        else:
            conn.close()
            return {"error": f"Unknown command: {command_type}"}

        conn.commit()
        conn.close()

        return {
            "status": "Command Dispatched and Executed",
            "rover_id": rover_id,
            "command": command_type,
            "log": log_entry,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    def generate_telemetry_stream(self):
        """Yields Server-Sent Events (SSE) telemetry updates."""
        while True:
            status = self.get_rover_status("Perseverance")
            yield f"data: {json.dumps(status)}\n\n"
            time.sleep(2.5)

telemetry_service = TelemetryService()
