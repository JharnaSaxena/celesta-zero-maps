import json
import math
import heapq
from backend.config import MOCK_DATA_DIR

class EarthService:
    def __init__(self):
        self.elevation_data = None
        self.minerals_data = None
        self.danger_zones_data = None
        self.environment_data = None
        self._load_data()

    def _load_data(self):
        mapping = {
            "elevation": "elevation_data",
            "minerals": "minerals_data",
            "dangerZones": "danger_zones_data",
            "environment": "environment_data"
        }
        for filename, attr in mapping.items():
            path = MOCK_DATA_DIR / f"{filename}.json"
            if path.exists():
                with open(path, "r", encoding="utf-8") as f:
                    setattr(self, attr, json.load(f))

    def _haversine_distance(self, p1, p2):
        lat1, lon1 = math.radians(p1[0]), math.radians(p1[1])
        lat2, lon2 = math.radians(p2[0]), math.radians(p2[1])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        h = math.sin(dlat / 2.0) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2.0) ** 2
        return 6371000.0 * 2.0 * math.atan2(math.sqrt(h), math.sqrt(max(0.0, 1.0 - h)))

    def _inside_polygon(self, lat, lng, polygon):
        hit = False
        n = len(polygon)
        j = n - 1
        for i in range(n):
            a, b = polygon[i]
            c, d = polygon[j]
            if (b > lng) != (d > lng) and lat < (c - a) * (lng - b) / (d - b + 1e-12) + a:
                hit = not hit
            j = i
        return hit

    def _get_risk(self, p):
        severities = {"Low": 2, "Medium": 8, "High": 30}
        max_risk = 0
        for z in self.danger_zones_data:
            if self._inside_polygon(p[0], p[1], z["polygon"]):
                max_risk = max(max_risk, severities.get(z["severity"], 0))
        return max_risk

    def calculate_route(self, start_lat, start_lng, end_lat, end_lng, avoid_danger=True):
        if not self.elevation_data:
            return {"error": "Elevation dataset not loaded"}

        b = self.elevation_data["bounds"]
        values = self.elevation_data["values"]
        rows = len(values)
        cols = len(values[0])

        # Find nearest nodes
        def coord_for(r, c):
            return [
                b["south"] + (r / (rows - 1)) * (b["north"] - b["south"]),
                b["west"] + (c / (cols - 1)) * (b["east"] - b["west"])
            ]

        def nearest_rc(lat, lng):
            best_rc = (0, 0)
            best_dist = float("inf")
            for r in range(rows):
                for c in range(cols):
                    p = coord_for(r, c)
                    dist = math.hypot(p[0] - lat, p[1] - lng)
                    if dist < best_dist:
                        best_dist = dist
                        best_rc = (r, c)
            return best_rc

        start_r, start_c = nearest_rc(start_lat, start_lng)
        end_r, end_c = nearest_rc(end_lat, end_lng)
        start_id = start_r * cols + start_c
        end_id = end_r * cols + end_c

        # Dijkstra on 4-neighbor grid
        distances = {start_id: 0.0}
        previous = {}
        queue = [(0.0, start_id)]

        while queue:
            cost, curr_id = heapq.heappop(queue)
            if cost > distances.get(curr_id, float("inf")):
                continue

            if curr_id == end_id:
                break

            r = curr_id // cols
            c = curr_id % cols
            curr_coord = coord_for(r, c)
            curr_elev = values[r][c]
            curr_risk = self._get_risk(curr_coord)

            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nr, nc = r + dr, c + dc
                if 0 <= nr < rows and 0 <= nc < cols:
                    nid = nr * cols + nc
                    next_coord = coord_for(nr, nc)
                    next_elev = values[nr][nc]
                    next_risk = self._get_risk(next_coord)

                    meters = self._haversine_distance(curr_coord, next_coord)
                    rise = abs(next_elev - curr_elev)

                    mid = [(curr_coord[0] + next_coord[0]) / 2.0, (curr_coord[1] + next_coord[1]) / 2.0]
                    mid_risk = self._get_risk(mid)
                    danger = max(curr_risk, next_risk, mid_risk)

                    weight = meters + rise * 8.0 + (meters * danger if avoid_danger else 0.0)
                    next_cost = cost + weight

                    if next_cost < distances.get(nid, float("inf")):
                        distances[nid] = next_cost
                        previous[nid] = curr_id
                        heapq.heappush(queue, (next_cost, nid))

        # Reconstruct path
        path_ids = []
        at = end_id
        while at is not None:
            path_ids.append(at)
            at = previous.get(at)
        path_ids.reverse()

        path_coords = []
        total_meters = 0.0
        ascent_m = 0.0
        exposed_to_danger = False

        for i, pid in enumerate(path_ids):
            pr = pid // cols
            pc = pid % cols
            coord = coord_for(pr, pc)
            elev = values[pr][pc]
            path_coords.append({
                "latitude": coord[0],
                "longitude": coord[1],
                "elevation_m": elev
            })
            if self._get_risk(coord) > 0:
                exposed_to_danger = True

            if i > 0:
                prev_coord = [path_coords[i - 1]["latitude"], path_coords[i - 1]["longitude"]]
                prev_elev = path_coords[i - 1]["elevation_m"]
                seg_m = self._haversine_distance(prev_coord, coord)
                total_meters += seg_m
                diff_e = elev - prev_elev
                if diff_e > 0:
                    ascent_m += diff_e

        est_walk_min = round(total_meters / 4000.0 * 60.0 + ascent_m / 600.0 * 60.0)

        return {
            "distance_km": round(total_meters / 1000.0, 2),
            "distance_meters": round(total_meters, 1),
            "total_ascent_m": round(ascent_m, 1),
            "estimated_walking_time_minutes": est_walk_min,
            "danger_avoidance_enabled": avoid_danger,
            "crosses_danger_zone": exposed_to_danger,
            "waypoints": path_coords
        }

earth_service = EarthService()
