"""
Unit and Integration Tests for Mobile PWA Transformation.
Verifies Web App Manifest, Service Worker, Responsive Stylesheet, and Static Assets.
"""
import json
import os
import unittest
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"


class TestPWAIntegration(unittest.TestCase):

    def test_01_manifest_json_validity(self):
        """Verifies that static/manifest.json is valid JSON with mandatory PWA fields."""
        manifest_path = STATIC_DIR / "manifest.json"
        self.assertTrue(manifest_path.exists(), "manifest.json does not exist")

        with open(manifest_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.assertEqual(data.get("display"), "standalone")
        self.assertEqual(data.get("orientation"), "portrait-primary")
        self.assertIn("name", data)
        self.assertIn("short_name", data)
        self.assertIn("theme_color", data)
        self.assertIn("background_color", data)

        icons = data.get("icons", [])
        self.assertGreaterEqual(len(icons), 3, "Manifest must provide at least 192, 512, and SVG icons")

        # Verify each referenced icon physically exists
        for icon in icons:
            icon_rel = icon["src"].lstrip("/")
            icon_path = STATIC_DIR / icon_rel
            self.assertTrue(icon_path.exists(), f"Icon referenced in manifest does not exist: {icon_rel}")
            self.assertGreater(icon_path.stat().st_size, 100, f"Icon is abnormally small or empty: {icon_rel}")

        print("\n[TEST PASS] manifest.json successfully validated with all required PWA parameters.")

    def test_02_service_worker_asset(self):
        """Verifies that static/sw.js exists, contains caching strategy and lifecycle events."""
        sw_path = STATIC_DIR / "sw.js"
        self.assertTrue(sw_path.exists(), "sw.js does not exist")
        content = sw_path.read_text(encoding="utf-8")

        self.assertIn("addEventListener('install'", content)
        self.assertIn("addEventListener('activate'", content)
        self.assertIn("addEventListener('fetch'", content)
        self.assertIn("CACHE_NAME", content)
        self.assertIn("PRECACHE_ASSETS", content)
        print("[TEST PASS] Service Worker (sw.js) lifecycle and caching directives verified.")

    def test_03_index_html_pwa_and_mobile_markup(self):
        """Verifies that index.html includes iOS Safari meta, manifest link, sheet handle, and FABs."""
        html_path = STATIC_DIR / "index.html"
        self.assertTrue(html_path.exists(), "index.html does not exist")
        content = html_path.read_text(encoding="utf-8")

        # PWA & iOS Safari tags
        self.assertIn('rel="manifest"', content)
        self.assertIn('name="apple-mobile-web-app-capable"', content)
        self.assertIn('name="apple-mobile-web-app-status-bar-style"', content)
        self.assertIn('rel="apple-touch-icon"', content)
        self.assertIn('viewport-fit=cover', content)

        # Mobile Bottom Sheet & Touch UI markers
        self.assertIn('sheetHandle', content)
        self.assertIn('sheet-bar', content)
        self.assertIn('mobile-fab-container', content)
        self.assertIn('mobileLocateFab', content)
        self.assertIn('setSheetSnap', content)
        self.assertIn('serviceWorker.register', content)
        print("[TEST PASS] index.html includes full iOS/Android PWA tags and mobile sheet DOM.")

    def test_04_app_css_mobile_responsiveness(self):
        """Verifies that app.css defines safe areas, bottom sheet snap positions, and FAB styles."""
        css_path = STATIC_DIR / "vendor" / "app.css"
        self.assertTrue(css_path.exists(), "app.css does not exist")
        css_text = css_path.read_text(encoding="utf-8")

        self.assertIn("safe-area-inset-top", css_text)
        self.assertIn("safe-area-inset-bottom", css_text)
        self.assertIn(".sheet-peek", css_text)
        self.assertIn(".sheet-half", css_text)
        self.assertIn(".sheet-full", css_text)
        self.assertIn(".mobile-fab", css_text)
        print("[TEST PASS] vendor/app.css responsive swipeable sheet rules verified.")


if __name__ == "__main__":
    unittest.main()
