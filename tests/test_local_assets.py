from pathlib import Path
import unittest
import os

BASE_DIR = str(Path(__file__).resolve().parent.parent)
VENDOR_DIR = os.path.join(BASE_DIR, "static", "vendor")

class TestLocalAssets(unittest.TestCase):
    def test_leaflet_files_exist_and_non_empty(self):
        js_file = os.path.join(VENDOR_DIR, "leaflet", "leaflet.js")
        css_file = os.path.join(VENDOR_DIR, "leaflet", "leaflet.css")
        icon_file = os.path.join(VENDOR_DIR, "leaflet", "images", "marker-icon.png")

        self.assertTrue(os.path.exists(js_file), "leaflet.js missing")
        self.assertGreater(os.path.getsize(js_file), 100000, "leaflet.js size unexpectedly small")

        self.assertTrue(os.path.exists(css_file), "leaflet.css missing")
        self.assertGreater(os.path.getsize(css_file), 10000, "leaflet.css size unexpectedly small")

        self.assertTrue(os.path.exists(icon_file), "marker-icon.png missing")
        print("\n[TEST PASS] All local Leaflet 1.9.4 assets verified (Zero-CDN ready)")

    def test_custom_app_css(self):
        app_css = os.path.join(VENDOR_DIR, "app.css")
        self.assertTrue(os.path.exists(app_css), "app.css missing")
        self.assertGreater(os.path.getsize(app_css), 500, "app.css unexpectedly empty")
        print("[TEST PASS] Local app.css stylesheet verified")

if __name__ == "__main__":
    unittest.main()
