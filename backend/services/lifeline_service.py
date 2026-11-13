import math
from backend.config import (
    TIER_FAVORABLE_THRESHOLD,
    TIER_CAUTION_THRESHOLD,
    LIFELINE_WEIGHT_SLOPE,
    LIFELINE_WEIGHT_DUST,
    LIFELINE_WEIGHT_DISTANCE,
    LIFELINE_BASE_X,
    LIFELINE_BASE_Z
)
from backend.services.terrain_service import terrain_service

class LifelineService:
    def __init__(self):
        self.terrain = terrain_service

    def calculate_margin(self, slope_deg, dust_index, base_dist_km):
        raw = 100.0 - (LIFELINE_WEIGHT_SLOPE * slope_deg) - (LIFELINE_WEIGHT_DUST * dust_index) - (LIFELINE_WEIGHT_DISTANCE * base_dist_km)
        return max(0.0, min(100.0, raw))

    def evaluate_point(self, x, z):
        sample = self.terrain.sample_point(x, z)
        slope = sample["slope_deg"]
        dust = sample["dust_index"]
        dist = sample["base_distance_km"]
        elevation_km = sample["height_km"]

        margin = self.calculate_margin(slope, dust, dist)
        tier = self.terrain.get_tier(round(margin))

        # Scientific hazard details
        slope_risk = "Low" if slope < 6 else "Moderate" if slope < 14 else "High"
        dust_hazard = "Minimal" if dust < 30 else "Moderate" if dust < 48 else "High Dust Accumulation"
        # Atmospheric shielding factor based on elevation (deeper in crater = more column density)
        atmospheric_depth_g_cm2 = max(10.0, 20.0 - elevation_km * 3.5)
        radiation_risk = "Elevated" if elevation_km > 1.8 else "Nominal Martian Surface"

        # Rover mobility score (100 is smooth asphalt equivalent, 0 is impassable cliff)
        mobility_index = max(0.0, min(100.0, 100.0 - slope * 3.0 - (dust * 0.4)))

        # Solar insolation factor (loss due to atmospheric dust opacity)
        optical_depth_tau = 0.35 + (dust / 100.0) * 0.4
        solar_transmission_pct = round(math.exp(-optical_depth_tau) * 100, 1)

        recommendations = []
        if slope >= 15:
            recommendations.append("Slope exceeds 15°; high rollover hazard for automated wheeled rovers.")
        if dust >= 45:
            recommendations.append("High loose dust index; inspect for potential wheel sinkage and thermal degradation.")
        if dist > 20:
            recommendations.append("Distance from Aurora Base exceeds 20 km; UHF line-of-sight relay required.")
        if margin >= 65:
            recommendations.append("Favorable operational corridor; suitable for primary mission traverses.")

        return {
            "coordinates": {"x": round(x, 4), "z": round(z, 4)},
            "elevation": {"km": round(elevation_km, 3), "meters": sample["height_m"]},
            "lifeline_score": round(margin, 1),
            "tier": tier,
            "components": {
                "slope_deg": slope,
                "dust_index": dust,
                "base_distance_km": dist
            },
            "hazard_analysis": {
                "slope_risk": slope_risk,
                "dust_hazard": dust_hazard,
                "radiation_classification": radiation_risk,
                "mobility_index": round(mobility_index, 1),
                "atmospheric_depth_g_cm2": round(atmospheric_depth_g_cm2, 2),
                "solar_transmission_pct": solar_transmission_pct
            },
            "recommendations": recommendations
        }

    def evaluate_landing_zone(self, center_x, center_z, radius_km=1.5, num_test_points=16):
        """Evaluates landing ellipse suitability by sampling radial points."""
        points = []
        center_eval = self.evaluate_point(center_x, center_z)
        points.append(center_eval)

        # Ring 1 (half radius)
        for i in range(num_test_points // 2):
            angle = (2 * math.pi * i) / (num_test_points // 2)
            px = center_x + (radius_km * 0.5) * math.cos(angle)
            pz = center_z + (radius_km * 0.5) * math.sin(angle)
            points.append(self.evaluate_point(px, pz))

        # Ring 2 (outer perimeter)
        for i in range(num_test_points // 2):
            angle = (2 * math.pi * i) / (num_test_points // 2) + 0.3
            px = center_x + radius_km * math.cos(angle)
            pz = center_z + radius_km * math.sin(angle)
            points.append(self.evaluate_point(px, pz))

        margins = [p["lifeline_score"] for p in points]
        slopes = [p["components"]["slope_deg"] for p in points]
        max_slope = max(slopes)
        avg_margin = sum(margins) / len(margins)
        min_margin = min(margins)

        suitability = "OPTIMAL" if min_margin >= 60 and max_slope <= 8 else (
            "ACCEPTABLE" if min_margin >= 40 and max_slope <= 14 else "REJECTED"
        )

        return {
            "center": {"x": center_x, "z": center_z},
            "radius_km": radius_km,
            "points_sampled": len(points),
            "suitability": suitability,
            "metrics": {
                "avg_margin": round(avg_margin, 1),
                "min_margin": round(min_margin, 1),
                "max_slope_deg": round(max_slope, 2),
                "avg_slope_deg": round(sum(slopes) / len(slopes), 2)
            },
            "touchdown_safety_index": round(max(0, min(100, avg_margin * 0.7 + (20 - max_slope) * 1.5)), 1),
            "critical_points_count": sum(1 for p in points if p["tier"] == "Critical")
        }

lifeline_service = LifelineService()
