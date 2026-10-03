import unittest
import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from src.core.hybrid_router import HybridTransitRouter

class TestScenicAndDirectRouting(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.router = HybridTransitRouter()

    def test_01_altinbas_to_mecidiyekoy_141m_direct(self):
        """Altınbaş Üniversitesi -> Mecidiyeköy must return direct 141M with 0 transfers as Option 1."""
        res = self.router.plan(
            from_lat=41.058309, from_lon=28.820361,
            to_lat=41.0667, to_lon=28.9936,
            target="FASTEST",
            date_str="2026-09-28",
            time_str="10:30:00",
            num_itineraries=4
        )
        self.assertTrue(res["success"])
        itins = res["itineraries"]
        self.assertGreater(len(itins), 0, "No itineraries returned for Altınbaş -> Mecidiyeköy")

        top_itin = itins[0]
        transit_legs = [l for l in top_itin["legs"] if l.get("mode") != "WALK"]
        self.assertEqual(len(transit_legs), 1, f"Expected 0-transfer single transit leg, got {len(transit_legs)}")
        self.assertEqual(transit_legs[0]["route_short_name"], "141M", "Top route must be direct 141M")
        self.assertLessEqual(top_itin["walk_duration_minutes"], 5, "Walk duration should be minimal near bus stop")

    def test_02_altinbas_to_mecidiyekoy_scenic_waterway(self):
        """Inland points Altınbaş -> Mecidiyeköy with SCENIC_WATER must synthesize a ferry leg on the Bosphorus."""
        res = self.router.plan(
            from_lat=41.058309, from_lon=28.820361,
            to_lat=41.0667, to_lon=28.9936,
            target="SCENIC_WATER",
            prefer_ferry=True,
            force_ferry=True,
            date_str="2026-09-28",
            time_str="10:30:00",
            num_itineraries=4
        )
        self.assertTrue(res["success"])
        itins = res["itineraries"]
        self.assertGreater(len(itins), 0)

        top_itin = itins[0]
        modes = [l["mode"] for l in top_itin["legs"]]
        self.assertIn("FERRY", modes, f"Scenic waterway route must contain a FERRY leg, got modes: {modes}")
        self.assertTrue(top_itin.get("is_scenic_detour"), "Scenic route must be flagged with is_scenic_detour")
        self.assertIsNotNone(top_itin.get("scenic_badge"))

    def test_03_coastal_ferry_eminonu_to_kadikoy(self):
        """Coastal ferry crossing Eminönü -> Kadıköy must directly use FERRY without detour synthesis."""
        res = self.router.plan(
            from_lat=41.018268, from_lon=28.973107,
            to_lat=40.9912, to_lon=29.0225,
            target="SCENIC_WATER",
            date_str="2026-09-28",
            time_str="11:00:00"
        )
        self.assertTrue(res["success"])
        itins = res["itineraries"]
        self.assertGreater(len(itins), 0)
        modes = [l["mode"] for l in itins[0]["legs"]]
        self.assertIn("FERRY", modes)

if __name__ == "__main__":
    unittest.main()
