import json
import math
from pathlib import Path
from backend.config import (
    TERRAIN_SIZE,
    TERRAIN_SPAN_KM,
    TERRAIN_SEED,
    MOCK_DATA_DIR,
    LIFELINE_BASE_X,
    LIFELINE_BASE_Z,
    TIER_FAVORABLE_THRESHOLD,
    TIER_CAUTION_THRESHOLD
)

class TerrainService:
    def __init__(self):
        self.size = TERRAIN_SIZE
        self.span_km = TERRAIN_SPAN_KM
        self.seed = TERRAIN_SEED
        self.nodes = []
        self.grid = []
        self._load_or_generate()

    def _load_or_generate(self):
        mars_json_path = MOCK_DATA_DIR / "mars.json"
        if mars_json_path.exists():
            with open(mars_json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.nodes = data.get("nodes", [])
        else:
            self.nodes = self.generate_terrain(self.seed)

        # Build 2D grid matrix for fast r, c indexing
        self.grid = [[None for _ in range(self.size)] for _ in range(self.size)]
        for n in self.nodes:
            r = n.get("r", 0)
            c = n.get("c", 0)
            if 0 <= r < self.size and 0 <= c < self.size:
                self.grid[r][c] = n

    def generate_terrain(self, seed=TERRAIN_SEED):
        state = seed & 0xFFFFFFFF
        def rand():
            nonlocal state
            state = (state + 0x6D2B79F5) & 0xFFFFFFFF
            t = state
            t = (t ^ (t >> 15)) & 0xFFFFFFFF
            t = ((t * (t | 1)) & 0xFFFFFFFF)
            t = (t ^ (t + (((t ^ (t >> 7)) * (t | 61)) & 0xFFFFFFFF))) & 0xFFFFFFFF
            return ((t ^ (t >> 14)) & 0xFFFFFFFF) / 4294967296.0

        nodes = []
        for r in range(self.size):
            for c in range(self.size):
                x = (c / (self.size - 1)) * self.span_km - (self.span_km / 2.0)
                z = (r / (self.size - 1)) * self.span_km - (self.span_km / 2.0)
                d = math.hypot(x, z)
                a = math.atan2(z, x)
                rim = 2.05 * math.exp(-(((d - 19.5) / 2.2) ** 2)) * (1.0 + 0.18 * math.sin(a * 9) + 0.09 * math.cos(a * 17))
                floor = 0.27 * math.sin(x * 0.31) * math.cos(z * 0.27)
                delta = 1.25 * math.exp(-((x + 12) ** 2 / 29.0 + (z + 7) ** 2 / 50.0)) * (0.65 + 0.35 * math.sin(z * 1.1 + x * 0.6))
                small = 0.4 * math.exp(-(((math.hypot(x - 9, z + 11) - 3) / 0.8) ** 2))
                height = 0.25 + rim + floor + delta + small + (rand() - 0.5) * 0.1
                nodes.append({
                    "id": r * self.size + c,
                    "r": r,
                    "c": c,
                    "x": round(x, 4),
                    "z": round(z, 4),
                    "height": height,
                    "dust": int(round(15 + 45 * rand())),
                    "slope": 0.0
                })

        for n in nodes:
            r, c = n["r"], n["c"]
            right = nodes[r * self.size + min(self.size - 1, c + 1)]
            left = nodes[r * self.size + max(0, c - 1)]
            up = nodes[max(0, r - 1) * self.size + c]
            down = nodes[min(self.size - 1, r + 1) * self.size + c]
            denom_c = max(1e-5, (right["c"] - left["c"]) * self.span_km / (self.size - 1))
            denom_r = max(1e-5, (down["r"] - up["r"]) * self.span_km / (self.size - 1))
            dx = (right["height"] - left["height"]) / denom_c
            dz = (down["height"] - up["height"]) / denom_r
            slope = math.atan(math.hypot(dx, dz)) * 180.0 / math.pi
            n["slope"] = slope
            n["baseDistance"] = math.hypot(n["x"] - LIFELINE_BASE_X, n["z"] - LIFELINE_BASE_Z)
            margin = int(round(max(0.0, min(100.0, 100.0 - n["slope"] * 2.0 - n["dust"] * 0.32 - n["baseDistance"] * 1.1))))
            n["margin"] = margin

        return nodes

    def get_tier(self, margin):
        if margin >= TIER_FAVORABLE_THRESHOLD:
            return "Favorable"
        elif margin >= TIER_CAUTION_THRESHOLD:
            return "Caution"
        return "Critical"

    def nearest_node(self, x, z):
        best = None
        best_dist = float("inf")
        # Direct grid approximation for speed:
        approx_c = int(round((x + self.span_km / 2.0) / self.span_km * (self.size - 1)))
        approx_r = int(round((z + self.span_km / 2.0) / self.span_km * (self.size - 1)))
        r_min = max(0, approx_r - 2)
        r_max = min(self.size - 1, approx_r + 2)
        c_min = max(0, approx_c - 2)
        c_max = min(self.size - 1, approx_c + 2)

        for r in range(r_min, r_max + 1):
            for c in range(c_min, c_max + 1):
                node = self.grid[r][c]
                if node:
                    dist = math.hypot(node["x"] - x, node["z"] - z)
                    if dist < best_dist:
                        best_dist = dist
                        best = node

        if best is not None:
            return best

        # Fallback to full search if out of grid bounds
        for node in self.nodes:
            dist = math.hypot(node["x"] - x, node["z"] - z)
            if dist < best_dist:
                best_dist = dist
                best = node
        return best

    def sample_point(self, x, z):
        """Bilinearly interpolates elevation, slope, dust, and margin at coordinate (x, z)."""
        half = self.span_km / 2.0
        # Check boundary
        clamped_x = max(-half, min(half, x))
        clamped_z = max(-half, min(half, z))

        norm_c = (clamped_x + half) / self.span_km * (self.size - 1)
        norm_r = (clamped_z + half) / self.span_km * (self.size - 1)

        c0 = int(math.floor(norm_c))
        c1 = min(self.size - 1, c0 + 1)
        r0 = int(math.floor(norm_r))
        r1 = min(self.size - 1, r0 + 1)

        fx = norm_c - c0
        fz = norm_r - r0

        n00 = self.grid[r0][c0]
        n10 = self.grid[r0][c1]
        n01 = self.grid[r1][c0]
        n11 = self.grid[r1][c1]

        def bilerp(field):
            v0 = n00[field] * (1 - fx) + n10[field] * fx
            v1 = n01[field] * (1 - fx) + n11[field] * fx
            return v0 * (1 - fz) + v1 * fz

        height = bilerp("height")
        slope = bilerp("slope")
        dust = bilerp("dust")
        base_dist = math.hypot(clamped_x - LIFELINE_BASE_X, clamped_z - LIFELINE_BASE_Z)
        margin = max(0.0, min(100.0, 100.0 - slope * 2.0 - dust * 0.32 - base_dist * 1.1))

        return {
            "x": round(x, 4),
            "z": round(z, 4),
            "height_km": round(height, 4),
            "height_m": round(height * 1000.0, 1),
            "slope_deg": round(slope, 2),
            "dust_index": round(dust, 1),
            "base_distance_km": round(base_dist, 2),
            "margin": round(margin, 1),
            "tier": self.get_tier(round(margin, 1)),
            "nearest_node_id": self.nearest_node(x, z)["id"]
        }

    def get_elevation_profile(self, waypoints, samples=50):
        """Generates an elevation & hazard profile along ordered waypoints."""
        if not waypoints or len(waypoints) < 2:
            return {"error": "At least two waypoints required for profile"}

        profile_points = []
        total_dist_km = 0.0
        ascent_m = 0.0
        descent_m = 0.0

        # Subdivide segment by segment
        segments = []
        for i in range(len(waypoints) - 1):
            p1 = waypoints[i]
            p2 = waypoints[i + 1]
            seg_len = math.hypot(p2["x"] - p1["x"], p2["z"] - p1["z"])
            segments.append((p1, p2, seg_len))
            total_dist_km += seg_len

        if total_dist_km == 0:
            total_dist_km = 1e-6

        curr_km = 0.0
        prev_sample = None

        for p1, p2, seg_len in segments:
            seg_samples = max(2, int(round((seg_len / total_dist_km) * samples)))
            for s in range(seg_samples):
                t = s / float(seg_samples - 1) if seg_samples > 1 else 0
                sample_x = p1["x"] + (p2["x"] - p1["x"]) * t
                sample_z = p1["z"] + (p2["z"] - p1["z"]) * t
                sample_data = self.sample_point(sample_x, sample_z)

                dist_from_start = curr_km + (seg_len * t)
                point_entry = {
                    "distance_from_start_km": round(dist_from_start, 3),
                    "x": sample_data["x"],
                    "z": sample_data["z"],
                    "height_m": sample_data["height_m"],
                    "slope_deg": sample_data["slope_deg"],
                    "margin": sample_data["margin"],
                    "tier": sample_data["tier"]
                }
                profile_points.append(point_entry)

                if prev_sample is not None:
                    diff = point_entry["height_m"] - prev_sample["height_m"]
                    if diff > 0:
                        ascent_m += diff
                    else:
                        descent_m += abs(diff)
                prev_sample = point_entry
            curr_km += seg_len

        return {
            "total_distance_km": round(total_dist_km, 3),
            "total_ascent_m": round(ascent_m, 1),
            "total_descent_m": round(descent_m, 1),
            "min_elevation_m": min(p["height_m"] for p in profile_points),
            "max_elevation_m": max(p["height_m"] for p in profile_points),
            "min_margin": min(p["margin"] for p in profile_points),
            "profile": profile_points
        }

    def get_bounding_box(self, min_x, max_x, min_z, max_z):
        filtered = [
            n for n in self.nodes
            if min_x <= n["x"] <= max_x and min_z <= n["z"] <= max_z
        ]
        return {
            "count": len(filtered),
            "bounds": {"min_x": min_x, "max_x": max_x, "min_z": min_z, "max_z": max_z},
            "nodes": filtered
        }

terrain_service = TerrainService()
