import math
import random
from datetime import datetime, timezone
from backend.database import get_db_connection
from backend.services.telemetry_service import telemetry_service

class WeatherService:
    def get_current_weather(self):
        time_info = telemetry_service.get_mars_time()
        current_sol = time_info["current_sol"]

        conn = get_db_connection()
        row = conn.execute("SELECT * FROM weather_logs ORDER BY sol DESC LIMIT 1").fetchone()
        conn.close()

        base = dict(row) if row else {
            "sol": current_sol,
            "min_temp_c": -78.0,
            "max_temp_c": -15.0,
            "pressure_pa": 748.5,
            "wind_speed_ms": 7.5,
            "wind_direction": "ENE",
            "opacity_tau": 0.38,
            "uv_index": 4.2,
            "summary": "Clear Martian skies, diurnal dust devil activity near delta scarp."
        }

        # Calculate current instantaneous temperature based on sun elevation
        sun_elev = time_info["sun_elevation_deg"]
        temp_range = base["max_temp_c"] - base["min_temp_c"]
        if sun_elev > 0:
            instant_temp = base["min_temp_c"] + temp_range * (math.sin(math.radians(sun_elev)) ** 0.8)
        else:
            instant_temp = base["min_temp_c"] - abs(sun_elev) * 0.1

        # Check for dust storm or dust devil advisory
        advisories = []
        if base["opacity_tau"] > 0.8:
            advisories.append("REGIONAL DUST STORM ALERT: Atmospheric opacity elevated; reduced solar transmission.")
        if base["wind_speed_ms"] > 14.0:
            advisories.append("HIGH WIND WARNING: Gale-force gusts recorded off Jezero crater rim.")
        if not advisories:
            advisories.append("NOMINAL WEATHER: Safe operational window for rover traverse and EVA simulations.")

        return {
            "location": "Jezero Crater, Mars (18.38°N, 77.58°E)",
            "sol": current_sol,
            "mars_time": time_info["local_solar_time"],
            "current_temp_c": round(instant_temp, 1),
            "diurnal_min_temp_c": base["min_temp_c"],
            "diurnal_max_temp_c": base["max_temp_c"],
            "atmospheric_pressure_pa": base["pressure_pa"],
            "wind": {
                "speed_ms": base["wind_speed_ms"],
                "speed_kmh": round(base["wind_speed_ms"] * 3.6, 1),
                "direction": base["wind_direction"]
            },
            "atmospheric_opacity_tau": base["opacity_tau"],
            "uv_radiation_index": base["uv_index"],
            "advisories": advisories,
            "sensor_suite": "MEDA (Mars Environmental Dynamics Analyzer)"
        }

    def get_forecast(self, num_sols=7):
        current = self.get_current_weather()
        start_sol = current["sol"]

        forecast = []
        random.seed(start_sol)

        for i in range(1, num_sols + 1):
            sol_num = start_sol + i
            temp_variation = random.uniform(-2.5, 2.5)
            min_temp = round(current["diurnal_min_temp_c"] + temp_variation, 1)
            max_temp = round(current["diurnal_max_temp_c"] + temp_variation * 0.8, 1)
            press = round(current["atmospheric_pressure_pa"] + random.uniform(-4.0, 4.0), 1)
            wind = round(max(3.0, current["wind"]["speed_ms"] + random.uniform(-2.0, 3.5)), 1)
            tau = round(max(0.25, current["atmospheric_opacity_tau"] + random.uniform(-0.05, 0.08)), 2)

            conditions = "Clear & Dry"
            if tau > 0.5:
                conditions = "Hazy with Atmospheric Dust"
            elif wind > 10.0:
                conditions = "Breezy / Afternoon Gusts"

            forecast.append({
                "sol": sol_num,
                "conditions": conditions,
                "min_temp_c": min_temp,
                "max_temp_c": max_temp,
                "pressure_pa": press,
                "wind_speed_ms": wind,
                "opacity_tau": tau,
                "solar_suitability": "High" if tau < 0.45 else "Moderate"
            })

        return {
            "forecast_generated_for_sol": start_sol,
            "period_sols": num_sols,
            "forecast": forecast
        }

    def get_history(self, limit=30):
        conn = get_db_connection()
        rows = conn.execute("SELECT * FROM weather_logs ORDER BY sol DESC LIMIT ?", (limit,)).fetchall()
        conn.close()
        return [dict(r) for r in rows]

weather_service = WeatherService()
