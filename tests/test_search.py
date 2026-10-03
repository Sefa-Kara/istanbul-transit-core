from pathlib import Path
import unittest
import sys

BASE_DIR = str(Path(__file__).resolve().parent.parent)
sys.path.insert(0, BASE_DIR)

from src.core.search_engine import search_engine, normalize_tr

class TestSearchEngine(unittest.TestCase):
    def test_turkish_normalization(self):
        self.assertEqual(normalize_tr("KADIKÖY"), "kadikoy")
        self.assertEqual(normalize_tr("BEŞİKTAŞ"), "besiktas")
        self.assertEqual(normalize_tr("Üsküdar"), "uskudar")
        self.assertEqual(normalize_tr("Şişli"), "sisli")
        print("\n[TEST PASS] Turkish diacritics normalization verified")

    def test_poi_and_stop_searches(self):
        test_queries = [
            ("kadikoy", "Kadıköy"),
            ("zorlu", "Zorlu Center"),
            ("ayasofya", "Ayasofya"),
            ("sabiha", "Sabiha Gökçen"),
            ("eminonu", "Eminönü"),
            ("cevahır", "Cevahir"),
            ("bogazici", "Boğaziçi")
        ]

        for query, expected_snippet in test_queries:
            results = search_engine.search(query, limit=5)
            self.assertGreater(len(results), 0, f"Query '{query}' returned no results")
            first = results[0]
            self.assertIn("lat", first)
            self.assertIn("lon", first)
            self.assertTrue(40.5 <= first["lat"] <= 41.6, f"Invalid latitude: {first['lat']}")
            self.assertTrue(28.0 <= first["lon"] <= 30.0, f"Invalid longitude: {first['lon']}")
            
            titles = [r["title"].lower() for r in results]
            has_match = any(normalize_tr(expected_snippet) in normalize_tr(t) for t in titles)
            self.assertTrue(has_match, f"Expected '{expected_snippet}' in results for '{query}', got: {titles}")

        print(f"[TEST PASS] Successfully searched and validated {len(test_queries)} landmark/stop queries")

    def test_empty_and_short_queries(self):
        self.assertEqual(search_engine.search("", limit=5), [])
        self.assertEqual(search_engine.search("a", limit=5), [])
        print("[TEST PASS] Empty and short query guards verified")

    def test_commercial_shop_geocoding(self):
        # Testing user's explicit case: "sefaköy boston drink & dessert"
        results = search_engine.search("sefaköy boston drink & dessert", limit=3)
        self.assertGreater(len(results), 0, "No results for Sefaköy Boston Drink & Dessert")
        top = results[0]
        self.assertIn("boston", top["title"].lower())
        self.assertAlmostEqual(top["lat"], 41.0050, delta=0.03)
        self.assertAlmostEqual(top["lon"], 28.7985, delta=0.03)
        print(f"[TEST PASS] Commercial venue resolved: {top['title']} at ({top['lat']}, {top['lon']})")

if __name__ == "__main__":
    unittest.main()
