from pathlib import Path
import unittest
import os
import sys
import json
import urllib.request

BASE_DIR = str(Path(__file__).resolve().parent.parent)
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from src.core.hybrid_router import hybrid_router

class TestEdgeCasesAndScenicRouting(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.router = hybrid_router
        cls.report_path = os.path.join(BASE_DIR, "data", "benchmarks", "edge_cases_and_scenic_report.json")

    def test_01_benchmark_report_exists_and_valid(self):
        """Verify edge_cases_and_scenic_report.json exists and contains complete structure."""
        self.assertTrue(os.path.exists(self.report_path), f"Report not found at {self.report_path}")
        with open(self.report_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        self.assertIn("metadata", data)
        self.assertIn("section_1_peripheral_endpoints", data)
        self.assertIn("section_2_expanded_scenic_routes", data)
        self.assertIn("section_3_modal_preference_extremes", data)
        self.assertIn("section_4_excessive_walk_audit", data)
        self.assertIn("recommendations_and_architecture", data)
        
        # Verify 7 peripheral endpoints investigated
        p_res = data["section_1_peripheral_endpoints"]["results"]
        self.assertEqual(len(p_res), 7)
        regions = {r["region"] for r in p_res}
        expected_regions = {"Silivri", "Çatalca", "Şile & Ağva", "Hadımköy", "Kemerburgaz & Göktürk", "Polonezköy", "Tuzla Deri OSB"}
        self.assertEqual(regions, expected_regions)

    def test_02_interchange_walk_times_realistic(self):
        """Interchange walk times at core transfer stations must be realistic (<= 9.5 min) and not absurd (30+ min)."""
        # Ayrılık Çeşmesi M4 to Marmaray
        res = self.router.plan(
            from_lat=41.0002, from_lon=29.0308,
            to_lat=41.0006, to_lon=29.0302,
            target="LEAST_WALKING",
            date_str="2026-09-28", time_str="12:00:00",
            num_itineraries=1
        )
        self.assertTrue(res["success"])
        it = res["itineraries"][0]
        self.assertLessEqual(it["walk_duration_minutes"], 5.0, "Ayrılık Çeşmesi M4<->Marmaray walk exceeds 5 min")

        # Üsküdar M5 to Marmaray
        res = self.router.plan(
            from_lat=41.0267, from_lon=29.0153,
            to_lat=41.0258, to_lon=29.0142,
            target="LEAST_WALKING",
            date_str="2026-09-28", time_str="12:00:00",
            num_itineraries=1
        )
        self.assertTrue(res["success"])
        it = res["itineraries"][0]
        self.assertLessEqual(it["walk_duration_minutes"], 5.0, "Üsküdar M5<->Marmaray walk exceeds 5 min")

    def test_03_coastal_corridor_bn1_and_bosphorus(self):
        """Bakırköy Sahil -> Eminönü should use direct BN1 along the Marmara shoreline."""
        res = self.router.plan(
            from_lat=40.9750, from_lon=28.8720,
            to_lat=41.0182, to_lon=28.9731,
            target="FASTEST",
            date_str="2026-09-28", time_str="11:00:00",
            num_itineraries=3
        )
        self.assertTrue(res["success"])
        itins = res["itineraries"]
        routes = [l.get("route_short_name") for it in itins for l in it["legs"] if l.get("route_short_name")]
        self.assertIn("BN1", routes, f"BN1 coastal bus should be available in itineraries: {routes}")

    def test_04_bridge_crossing_metrobüs(self):
        """Mecidiyeköy -> Altunizade across 15 Temmuz Bridge must return Metrobüs (34G/34AS/34Z)."""
        res = self.router.plan(
            from_lat=41.0667, from_lon=28.9936,
            to_lat=41.0215, to_lon=29.0416,
            target="FASTEST",
            date_str="2026-09-28", time_str="11:00:00",
            num_itineraries=2
        )
        self.assertTrue(res["success"])
        itins = res["itineraries"]
        routes = [l.get("route_short_name") for it in itins for l in it["legs"] if l.get("route_short_name")]
        has_metrobus = any(r and r.startswith("34") for r in routes)
        self.assertTrue(has_metrobus, f"Expected Metrobüs crossing 15 Temmuz Bridge, got: {routes}")

    def test_05_modal_preference_extremes_ferry(self):
        """Göztepe -> Beşiktaş with prefer_modes=['FERRY'] must elevate ferry option to top option."""
        res = self.router.plan(
            from_lat=40.9856, from_lon=29.0543,
            to_lat=41.0417, to_lon=29.0046,
            prefer_modes=["FERRY"],
            date_str="2026-09-28", time_str="10:30:00",
            num_itineraries=2
        )
        self.assertTrue(res["success"])
        top = res["itineraries"][0]
        modes = [l["mode"] for l in top["legs"]]
        self.assertIn("FERRY", modes, f"Option 1 must include FERRY when preferred, got modes: {modes}")

if __name__ == "__main__":
    unittest.main()
