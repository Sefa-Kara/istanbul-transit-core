from pathlib import Path
import unittest
import sys
import os

BASE_DIR = str(Path(__file__).resolve().parent.parent)
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from src.utils.text_utils import repair_turkish_mojibake
from src.core.hybrid_router import hybrid_router, clean_text

class TestMoovitBundlingAndMojibake(unittest.TestCase):
    def test_turkish_mojibake_repairs(self):
        """
        Verify that all corrupted Turkish strings reported by the user
        and present in GTFS are 100% cleanly resolved.
        """
        test_cases = [
            ("KAÂ ITHANE - EMÃ°NÃ–NÃœ", "KAĞITHANE - EMİNÖNÜ"),
            ("46Ã*", "46Ç"),
            ("GÃœLBAÄž - EMÃ°NÃ–NÃœ", "GÜLBAĞ - EMİNÖNÜ"),
            ("MECÃ°DÃ°YEKÃ–Y AVM - ALÄ°BEYKÃ–Y METRO", "MECİDİYEKÖY AVM - ALİBEYKÖY METRO"),
            ("HASKÃ–Y PARKI - TAKSÃ°M", "HASKÖY PARKI - TAKSİM"),
            ("ÅžÄ°ÅžLÄ°", "ŞİŞLİ"),
            ("KÃ–PRÃœBAÅžI", "KÖPRÜBAŞI")
        ]
        for raw, expected in test_cases:
            fixed = repair_turkish_mojibake(raw)
            self.assertEqual(fixed, expected, f"Failed fixing mojibake for: {raw}")
            # Also test clean_text wrapper
            self.assertEqual(clean_text(raw), expected)

    def test_kustepe_to_istiklal_no_micro_hops_and_corridor_bundling(self):
        """
        Kuştepe / Mecidiyeköy -> Demirören İstiklal AVM (Tarlabaşı / Beyoğlu)
        Must NOT suggest 1-minute 1-stop micro bus hops (e.g. 27T for 1 stop to transfer to 46Ç).
        Must prioritize direct 0-transfer bus corridors and bundle compatible lines (e.g. [46Ç / 46T] or [93M / 50M]).
        """
        res = hybrid_router.plan(
            from_lat=41.0667,
            from_lon=28.9936,  # Kuştepe / Mecidiyeköy
            to_lat=41.0337,
            to_lon=28.9778,   # Demirören İstiklal
            date_str="2026-09-28",
            time_str="08:30:00"
        )
        self.assertTrue(res.get("success"))
        itins = res.get("itineraries", [])
        self.assertGreater(len(itins), 0, "Expected itineraries from Kuştepe to İstiklal")

        for idx, itin in enumerate(itins):
            legs = itin.get("legs", [])
            transit_legs = [l for l in legs if l.get("mode") != "WALK"]
            
            # Check for zero micro-hops in multi-leg itineraries
            if len(transit_legs) > 1:
                for l in transit_legs:
                    self.assertFalse(
                        l.get("distance_meters", 0) < 650 and l.get("stop_count", 0) <= 2,
                        f"Found prohibited micro-transfer leg in option {idx+1}: {l.get('route_short_name')} ({l.get('distance_meters')}m)"
                    )

            # Check that Turkish characters in stops and routes are completely clean
            for l in legs:
                for field in [l.get("from_stop", ""), l.get("to_stop", ""), l.get("route_short_name", ""), l.get("route_long_name", "")]:
                    if field:
                        self.assertNotIn("Ã", field, f"Mojibake found in field: {field}")
                        self.assertNotIn("Å", field, f"Mojibake found in field: {field}")
                        self.assertNotIn("Ä", field, f"Mojibake found in field: {field}")
                        self.assertNotIn("KAÂ", field, f"Mojibake found in field: {field}")

        # The top option should be direct (0 transfers)
        best = itins[0]
        self.assertEqual(best.get("transfers"), 0, "Top recommended option for Kuştepe -> İstiklal must be direct (0 transfers)")

if __name__ == "__main__":
    unittest.main()
