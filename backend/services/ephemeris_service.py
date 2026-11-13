import math
import datetime
from backend.config import JEZERO_LAT, JEZERO_LON, MARS_RADIUS_KM

# Constants
AU_KM = 149597870.7
SPEED_OF_LIGHT_KMS = 299792.458
EARTH_RADIUS_KM = 6378.137

# JPL Keplerian elements for approximate positions of major planets (J2000 epoch: 2000-01-01 12:00:00 TT)
# Table from: https://ssd.jpl.nasa.gov/planets/approx_pos.html
PLANET_ELEMENTS = {
    "Mercury": {
        "a": (0.38709927, 0.00000037),
        "e": (0.20563593, 0.00001906),
        "I": (7.00497902, -0.00594749),
        "L": (252.25032350, 149472.67411175),
        "w": (77.45779628, 0.16047689),
        "node": (48.33076593, -0.12534081),
        "color": "#9e9e9e",
        "radius_scale": 0.38
    },
    "Venus": {
        "a": (0.72333566, 0.00000390),
        "e": (0.00677672, -0.00004107),
        "I": (3.39467605, -0.00078890),
        "L": (181.97909950, 58517.81538729),
        "w": (131.60246718, 0.00268329),
        "node": (76.67984255, -0.27769418),
        "color": "#e0c068",
        "radius_scale": 0.95
    },
    "Earth": {
        "a": (1.00000261, 0.00000562),
        "e": (0.01671123, -0.00004392),
        "I": (0.00001531, -0.01294668),
        "L": (100.46457166, 35999.37244981),
        "w": (102.93768193, 0.32327364),
        "node": (0.0, 0.0),
        "color": "#4da6ff",
        "radius_scale": 1.0
    },
    "Mars": {
        "a": (1.52371034, 0.00001847),
        "e": (0.09339410, 0.00007882),
        "I": (1.84969142, -0.00813131),
        "L": (-4.55343205, 19140.30268499),
        "w": (-23.94362959, 0.44441088),
        "node": (49.55953891, -0.29257343),
        "color": "#e06c4b",
        "radius_scale": 0.53
    },
    "Jupiter": {
        "a": (5.20288700, -0.00011607),
        "e": (0.04838624, -0.00013253),
        "I": (1.30439695, -0.00183714),
        "L": (34.39644051, 3034.74612775),
        "w": (14.72847983, 0.21252668),
        "node": (100.47390909, 0.20469106),
        "color": "#c89462",
        "radius_scale": 2.2
    }
}

class EphemerisService:
    def get_julian_centuries(self, dt=None):
        if dt is None:
            dt = datetime.datetime.now(datetime.timezone.utc)
        elif isinstance(dt, (int, float)):
            dt = datetime.datetime.fromtimestamp(dt, tz=datetime.timezone.utc)
        elif isinstance(dt, str):
            try:
                dt = datetime.datetime.fromisoformat(dt.replace("Z", "+00:00"))
            except ValueError:
                dt = datetime.datetime.now(datetime.timezone.utc)

        y = dt.year
        m = dt.month
        d = dt.day + (dt.hour + dt.minute / 60.0 + dt.second / 3600.0) / 24.0

        if m <= 2:
            y -= 1
            m += 12

        A = int(y / 100)
        B = 2 - A + int(A / 4)
        jd = int(365.25 * (y + 4716)) + int(30.6001 * (m + 1)) + d + B - 1524.5
        T = (jd - 2451545.0) / 36525.0
        return T, jd, dt

    def compute_planet_heliocentric(self, planet_name, T):
        el = PLANET_ELEMENTS.get(planet_name)
        if not el:
            return None

        a = el["a"][0] + el["a"][1] * T
        e = el["e"][0] + el["e"][1] * T
        I = math.radians(el["I"][0] + el["I"][1] * T)
        L = math.radians((el["L"][0] + el["L"][1] * T) % 360.0)
        w = math.radians((el["w"][0] + el["w"][1] * T) % 360.0)
        node = math.radians((el["node"][0] + el["node"][1] * T) % 360.0)

        # Mean Anomaly M
        M = (L - w) % (2.0 * math.pi)

        # Solve Kepler's equation for Eccentric Anomaly E: E - e*sin(E) = M
        E = M
        for _ in range(12):
            dE = (E - e * math.sin(E) - M) / (1.0 - e * math.cos(E))
            E -= dE
            if abs(dE) < 1e-9:
                break

        # Orbital plane coordinates
        x_prime = a * (math.cos(E) - e)
        y_prime = a * math.sqrt(max(0.0, 1.0 - e * e)) * math.sin(E)

        # J2000 ecliptic coordinates
        w_bar = w - node
        cos_w, sin_w = math.cos(w_bar), math.sin(w_bar)
        cos_n, sin_n = math.cos(node), math.sin(node)
        cos_i, sin_i = math.cos(I), math.sin(I)

        x = (cos_w * cos_n - sin_w * sin_n * cos_i) * x_prime + (-sin_w * cos_n - cos_w * sin_n * cos_i) * y_prime
        y = (cos_w * sin_n + sin_w * cos_n * cos_i) * x_prime + (-sin_w * sin_n + cos_w * cos_n * cos_i) * y_prime
        z = (sin_w * sin_i) * x_prime + (cos_w * sin_i) * y_prime

        r = math.hypot(x, y, z)
        true_anomaly = math.degrees(math.atan2(y_prime, x_prime)) % 360.0

        return {
            "name": planet_name,
            "x_au": x,
            "y_au": y,
            "z_au": z,
            "distance_from_sun_au": r,
            "distance_from_sun_km": r * AU_KM,
            "semi_major_axis_au": a,
            "eccentricity": e,
            "inclination_deg": math.degrees(I),
            "true_anomaly_deg": round(true_anomaly, 2),
            "color": el["color"],
            "radius_scale": el["radius_scale"]
        }

    def compute_orbit_path(self, planet_name, T, points=72):
        el = PLANET_ELEMENTS.get(planet_name)
        if not el:
            return []

        a = el["a"][0] + el["a"][1] * T
        e = el["e"][0] + el["e"][1] * T
        I = math.radians(el["I"][0] + el["I"][1] * T)
        w = math.radians((el["w"][0] + el["w"][1] * T) % 360.0)
        node = math.radians((el["node"][0] + el["node"][1] * T) % 360.0)

        w_bar = w - node
        cos_w, sin_w = math.cos(w_bar), math.sin(w_bar)
        cos_n, sin_n = math.cos(node), math.sin(node)
        cos_i, sin_i = math.cos(I), math.sin(I)

        orbit_pts = []
        for i in range(points + 1):
            E = (2.0 * math.pi * i) / points
            x_prime = a * (math.cos(E) - e)
            y_prime = a * math.sqrt(max(0.0, 1.0 - e * e)) * math.sin(E)

            x = (cos_w * cos_n - sin_w * sin_n * cos_i) * x_prime + (-sin_w * cos_n - cos_w * sin_n * cos_i) * y_prime
            y = (cos_w * sin_n + sin_w * cos_n * cos_i) * x_prime + (-sin_w * sin_n + cos_w * cos_n * cos_i) * y_prime
            z = (sin_w * sin_i) * x_prime + (cos_w * sin_i) * y_prime
            orbit_pts.append({"x": round(x, 4), "y": round(y, 4), "z": round(z, 4)})

        return orbit_pts

    def get_solar_system_state(self, dt=None):
        T, jd, dt_obj = self.get_julian_centuries(dt)
        planets_data = []

        for p_name in ["Mercury", "Venus", "Earth", "Mars", "Jupiter"]:
            p_pos = self.compute_planet_heliocentric(p_name, T)
            p_orbit = self.compute_orbit_path(p_name, T, points=64)
            p_pos["orbit_path"] = p_orbit
            planets_data.append(p_pos)

        # Distance between Earth and Mars
        earth = next(p for p in planets_data if p["name"] == "Earth")
        mars = next(p for p in planets_data if p["name"] == "Mars")
        dx = mars["x_au"] - earth["x_au"]
        dy = mars["y_au"] - earth["y_au"]
        dz = mars["z_au"] - earth["z_au"]
        dist_au = math.hypot(dx, dy, dz)
        dist_km = dist_au * AU_KM
        light_sec = dist_km / SPEED_OF_LIGHT_KMS

        return {
            "date_utc": dt_obj.isoformat(),
            "julian_date": round(jd, 4),
            "earth_mars_distance": {
                "km": round(dist_km, 1),
                "au": round(dist_au, 5),
                "miles": round(dist_km * 0.621371, 1),
                "light_travel_time_seconds": round(light_sec, 2),
                "light_travel_time_formatted": f"{int(light_sec // 60)}m {int(light_sec % 60):02d}s",
                "round_trip_delay_formatted": f"{int((light_sec * 2) // 60)}m {int((light_sec * 2) % 60):02d}s"
            },
            "planets": planets_data
        }

    def get_observer_distance_to_jezero(self, obs_lat, obs_lon, obs_accuracy_m=None, dt=None, place_name=None):
        """Calculates exact Euclidean topocentric distance from an Earth observer to Jezero Crater, Mars."""
        state = self.get_solar_system_state(dt)
        em_dist = state["earth_mars_distance"]

        # Formatted coordinates to 6 decimal places as specified
        lat_formatted = f"{abs(obs_lat):.6f}° {'N' if obs_lat >= 0 else 'S'}"
        lon_formatted = f"{abs(obs_lon):.6f}° {'E' if obs_lon >= 0 else 'W'}"

        # Topocentric baseline shift (up to Earth radius ~6,378 km)
        topocentric_shift_km = EARTH_RADIUS_KM * math.cos(math.radians(obs_lat))
        # Total distance accurate to topocentric observer
        precise_km = em_dist["km"] - topocentric_shift_km * 0.5
        light_time = precise_km / SPEED_OF_LIGHT_KMS

        return {
            "observer": {
                "latitude": round(obs_lat, 6),
                "longitude": round(obs_lon, 6),
                "latitude_formatted": lat_formatted,
                "longitude_formatted": lon_formatted,
                "accuracy_radius_m": round(obs_accuracy_m, 1) if obs_accuracy_m is not None else None,
                "place_name": place_name or f"{lat_formatted}, {lon_formatted}"
            },
            "target": {
                "body": "Mars",
                "landmark": "Jezero Crater (Octavia E. Butler Landing / Perseverance)",
                "latitude_deg": JEZERO_LAT,
                "longitude_deg": JEZERO_LON
            },
            "distance": {
                "km": round(precise_km, 1),
                "au": round(precise_km / AU_KM, 6),
                "miles": round(precise_km * 0.621371, 1),
                "light_travel_time_seconds": round(light_time, 2),
                "light_travel_time_formatted": f"{int(light_time // 60)}m {int(light_time % 60):02d}s",
                "round_trip_ping_formatted": f"{int((light_time * 2) // 60)}m {int((light_time * 2) % 60):02d}s"
            },
            "solar_system_state": {
                "date_utc": state["date_utc"],
                "julian_date": state["julian_date"],
                "earth_sun_dist_au": round(next(p for p in state["planets"] if p["name"] == "Earth")["distance_from_sun_au"], 4),
                "mars_sun_dist_au": round(next(p for p in state["planets"] if p["name"] == "Mars")["distance_from_sun_au"], 4)
            }
        }

ephemeris_service = EphemerisService()
