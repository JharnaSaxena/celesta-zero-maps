import heapq
import math
from backend.config import TERRAIN_SIZE
from backend.services.terrain_service import terrain_service

class RoutingService:
    def __init__(self):
        self.terrain = terrain_service
        self.size = TERRAIN_SIZE

    def _get_neighbors(self, r, c):
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < self.size and 0 <= nc < self.size:
                yield self.terrain.grid[nr][nc]

    def _edge_weight(self, node_a, node_b, mode="balanced"):
        dx = node_b["x"] - node_a["x"]
        dz = node_b["z"] - node_a["z"]
        dh = node_b["height"] - node_a["height"]
        dist_3d = math.hypot(dx, dz, dh)
        min_margin = min(node_a["margin"], node_b["margin"])
        max_slope = max(node_a["slope"], node_b["slope"])

        if mode == "fastest" or mode == "shortest":
            return dist_3d

        elif mode == "safest":
            # Avoid critical terrain (< 40) with massive penalty, discourage caution
            penalty = 0.0
            if min_margin < 40:
                penalty += 150.0
            elif min_margin < 65:
                penalty += 15.0
            if max_slope > 14.0:
                penalty += (max_slope - 14.0) * 10.0
            margin_factor = 1.0 + ((100.0 - min_margin) / 10.0) ** 1.5
            return dist_3d * margin_factor + penalty + abs(dh) * 8.0

        elif mode == "energy":
            # Gravity climb work (m) + loose regolith rolling resistance
            climb = max(0.0, dh * 1000.0)
            avg_dust = (node_a["dust"] + node_b["dust"]) / 2.0
            dust_drag = 1.0 + (avg_dust / 50.0) * 0.4
            return dist_3d * dust_drag + climb * 0.05 + abs(dh) * 4.0

        else: # "balanced" - matches Terrascope client dijkstra
            margin_mod = 1.0 + (100.0 - min_margin) / 22.0
            return dist_3d * margin_mod + abs(dh) * 6.0

    def calculate_route(self, from_x, from_z, to_x, to_z, mode="balanced"):
        start_node = self.terrain.nearest_node(from_x, from_z)
        target_node = self.terrain.nearest_node(to_x, to_z)

        if not start_node or not target_node:
            return {"error": "Invalid start or destination coordinates"}

        if start_node["id"] == target_node["id"]:
            return {
                "distance_km": 0.0,
                "ascent_m": 0.0,
                "descent_m": 0.0,
                "est_drive_hours": 0.0,
                "est_sols": 0.0,
                "min_margin": start_node["margin"],
                "avg_margin": start_node["margin"],
                "risk_exposure": {"favorable_pct": 100.0 if start_node["margin"] >= 65 else 0.0, "caution_pct": 0.0, "critical_pct": 100.0 if start_node["margin"] < 40 else 0.0},
                "waypoints": [start_node],
                "turns": [],
                "warnings": []
            }

        start_id = start_node["id"]
        target_id = target_node["id"]

        # A* Priority Queue: (estimated_total_cost, current_cost, node_id)
        # Using Euclidean distance heuristic
        target_x, target_z, target_h = target_node["x"], target_node["z"], target_node["height"]

        def heuristic(node):
            if mode == "balanced" or mode == "fastest" or mode == "shortest":
                return math.hypot(target_x - node["x"], target_z - node["z"], target_h - node["height"])
            return 0.0 # pure Dijkstra for complex non-monotonic weights

        queue = [(heuristic(start_node), 0.0, start_id)]
        distances = {start_id: 0.0}
        previous = {}
        visited_nodes = 0

        found = False
        while queue:
            est_cost, cost, curr_id = heapq.heappop(queue)
            if cost > distances.get(curr_id, float("inf")):
                continue

            visited_nodes += 1
            if curr_id == target_id:
                found = True
                break

            curr_node = self.terrain.nodes[curr_id]
            r, c = curr_node["r"], curr_node["c"]

            for neighbor in self._get_neighbors(r, c):
                nid = neighbor["id"]
                weight = self._edge_weight(curr_node, neighbor, mode=mode)
                next_cost = cost + weight

                if next_cost < distances.get(nid, float("inf")):
                    distances[nid] = next_cost
                    previous[nid] = curr_id
                    heapq.heappush(queue, (next_cost + heuristic(neighbor), next_cost, nid))

        if not found:
            return {"error": "No viable route found between coordinates"}

        # Reconstruct path
        path_ids = []
        curr = target_id
        while curr is not None:
            path_ids.append(curr)
            curr = previous.get(curr)
        path_ids.reverse()

        path_nodes = [self.terrain.nodes[nid] for nid in path_ids]

        # Calculate metrics
        total_km = 0.0
        ascent_m = 0.0
        descent_m = 0.0
        min_margin = 100
        margin_sum = 0
        critical_count = 0
        caution_count = 0
        favorable_count = 0

        for i, node in enumerate(path_nodes):
            m = node["margin"]
            min_margin = min(min_margin, m)
            margin_sum += m
            if m >= 65:
                favorable_count += 1
            elif m >= 40:
                caution_count += 1
            else:
                critical_count += 1

            if i > 0:
                prev = path_nodes[i - 1]
                dh = (node["height"] - prev["height"]) * 1000.0
                seg_km = math.hypot(node["x"] - prev["x"], node["z"] - prev["z"], node["height"] - prev["height"])
                total_km += seg_km
                if dh > 0:
                    ascent_m += dh
                else:
                    descent_m += abs(dh)

        n_pts = len(path_nodes)
        avg_margin = margin_sum / max(1, n_pts)

        # Rover Speed & Mission Sol estimates:
        # Perseverance nominal drive speed ~120 meters/hour (0.12 km/h)
        # Average drive sol ~ 2.5 hours of driving = ~300 meters per sol
        drive_speed_kmh = 0.12
        drive_hours = total_km / drive_speed_kmh
        # Add climbing time penalty (1 hour per 100m climb)
        drive_hours += (ascent_m / 100.0) * 1.0
        estimated_sols = max(1.0, math.ceil(total_km / 0.35))

        # Generate navigational turns/directions
        turns = []
        for i in range(1, len(path_nodes)):
            n_curr = path_nodes[i]
            n_prev = path_nodes[i - 1]
            dx = n_curr["x"] - n_prev["x"]
            dz = n_curr["z"] - n_prev["z"]
            # Bearing in degrees (0 = North/+Z, 90 = East/+X)
            deg = (math.degrees(math.atan2(dx, dz)) + 360) % 360
            direction_name = self._cardinal(deg)
            if i == 1 or i % 5 == 0 or i == len(path_nodes) - 1:
                turns.append({
                    "step": len(turns) + 1,
                    "waypoint_index": i,
                    "heading_deg": round(deg, 1),
                    "cardinal": direction_name,
                    "elevation_m": round(n_curr["height"] * 1000.0, 1),
                    "slope_deg": round(n_curr["slope"], 1),
                    "margin": n_curr["margin"],
                    "instruction": f"Traverse {direction_name} at elev {round(n_curr['height']*1000)}m (margin {n_curr['margin']})"
                })

        warnings = []
        if critical_count > 0:
            warnings.append(f"Route intersects {critical_count} critical safety grid cells (margin < 40). Traversing hazardous terrain.")
        if any(n["slope"] > 16.0 for n in path_nodes):
            warnings.append("Route exceeds 16° slope at peak grades; rover traction assist and AutoNav caution advised.")

        return {
            "mode": mode,
            "start": {"x": start_node["x"], "z": start_node["z"], "id": start_node["id"]},
            "destination": {"x": target_node["x"], "z": target_node["z"], "id": target_node["id"]},
            "distance_km": round(total_km, 3),
            "ascent_m": round(ascent_m, 1),
            "descent_m": round(descent_m, 1),
            "min_margin": min_margin,
            "avg_margin": round(avg_margin, 1),
            "nodes_visited_in_search": visited_nodes,
            "path_length_nodes": n_pts,
            "estimated_drive_hours": round(drive_hours, 1),
            "estimated_sols": int(estimated_sols),
            "risk_exposure": {
                "favorable_pct": round(favorable_count / n_pts * 100.0, 1),
                "caution_pct": round(caution_count / n_pts * 100.0, 1),
                "critical_pct": round(critical_count / n_pts * 100.0, 1)
            },
            "warnings": warnings,
            "turn_instructions": turns,
            "waypoints": [
                {
                    "id": n["id"],
                    "r": n["r"],
                    "c": n["c"],
                    "x": n["x"],
                    "z": n["z"],
                    "height_m": round(n["height"] * 1000.0, 1),
                    "slope_deg": round(n["slope"], 1),
                    "margin": n["margin"]
                }
                for n in path_nodes
            ]
        }

    def _cardinal(self, deg):
        dirs = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
        ix = int((deg + 11.25) / 22.5) % 16
        return dirs[ix]

routing_service = RoutingService()
