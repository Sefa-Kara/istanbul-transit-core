from pathlib import Path
import unittest
import sys
import os

BASE_DIR = str(Path(__file__).resolve().parent.parent)
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from src.core.hybrid_router import hybrid_router

class TestSAWDirectRouting(unittest.TestCase):
    def test_kustepe_to_sabiha_gokcen_direct_m4(self):
        """
        Kuştepe / Mecidiyeköy -> Sabiha Gökçen Havalimanı M4
        Must route via Metrobüs (34G) -> Ünalan -> M4 Metro directly to Sabiha Gökçen Havalimanı.
        Must NOT tell the passenger to get off at Pendik and take a municipal bus to Pendik Devlet Hastanesi!
        """
        res = hybrid_router.plan(
            from_lat=41.0667,
            from_lon=28.9936,  # Mecidiyeköy / Kuştepe
            to_lat=40.908621,
            to_lon=29.284000,  # Sabiha Gökçen Havalimanı M4
            date_str="2026-09-28",
            time_str="08:30:00"
        )
        self.assertTrue(res.get("success"), "Routing call failed")
        itins = res.get("itineraries", [])
        self.assertGreater(len(itins), 0, "No itineraries returned for SAW")

        best = itins[0]
        legs = best.get("legs", [])
        transit_legs = [l for l in legs if l.get("mode") != "WALK"]

        print(f"\n[SAW TEST] Selected Itinerary: {best.get('total_duration_minutes')} min, {best.get('transfers')} transfers")
        for l in transit_legs:
            print(f"  -> {l.get('mode')} {l.get('route_short_name')} from '{l.get('from_stop')}' to '{l.get('to_stop')}'")

        # Must contain M4 Metro leg
        m4_leg = next((l for l in transit_legs if "M4" in (l.get("route_short_name") or "")), None)
        self.assertIsNotNone(m4_leg, "M4 Metro line missing from SAW route")
        
        # M4 destination stop must be Sabiha Gökçen Havalimanı M4
        self.assertIn("Sabiha Gökçen", m4_leg.get("to_stop", ""), "M4 must terminate at Sabiha Gökçen Havalimanı")

        # Crucial: Zero municipal bus transfers after M4!
        # The user specifically complained: 'metrodan inip bir de otobüse binmemi söylüyor bu ne alaka ya'
        m4_idx = transit_legs.index(m4_leg)
        post_m4_transit = transit_legs[m4_idx + 1:]
        self.assertEqual(len(post_m4_transit), 0, f"No transit legs allowed after M4 arrival at airport! Found: {post_m4_transit}")

    def test_reverse_saw_to_mecidiyekoy(self):
        """
        Sabiha Gökçen Havalimanı M4 -> Mecidiyeköy Metrobüs
        Must board M4 directly at SAW and connect to Metrobüs at Ünalan.
        """
        res = hybrid_router.plan(
            from_lat=40.908621,
            from_lon=29.284000,  # Sabiha Gökçen Havalimanı M4
            to_lat=41.0667,
            to_lon=28.9936,    # Mecidiyeköy
            date_str="2026-09-28",
            time_str="14:00:00"
        )
        self.assertTrue(res.get("success"))
        itins = res.get("itineraries", [])
        self.assertGreater(len(itins), 0)

        best = itins[0]
        transit_legs = [l for l in best.get("legs", []) if l.get("mode") != "WALK"]
        self.assertGreater(len(transit_legs), 0)
        first_transit = transit_legs[0]
        self.assertEqual(first_transit.get("mode"), "SUBWAY")
        self.assertIn("M4", first_transit.get("route_short_name", ""))
        self.assertIn("Sabiha Gökçen", first_transit.get("from_stop", ""))

if __name__ == "__main__":
    unittest.main()
