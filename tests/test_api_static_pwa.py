"""
Verifies FastAPI routing for PWA entry points (/manifest.json, /sw.js, /icons/...).
"""
import unittest
from fastapi.testclient import TestClient
from src.api.main import app

class TestAPIStaticPWA(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_manifest_endpoint(self):
        resp = self.client.get("/manifest.json")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("standalone", resp.text)
        print("[TEST PASS] /manifest.json returns 200 OK with standalone display mode.")

    def test_service_worker_endpoint(self):
        resp = self.client.get("/sw.js")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("addEventListener", resp.text)
        print("[TEST PASS] /sw.js returns 200 OK with Service Worker code.")

    def test_pwa_icons_endpoint(self):
        resp = self.client.get("/icons/icon-192.png")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.headers.get("content-type"), "image/png")
        print("[TEST PASS] /icons/icon-192.png returns 200 OK image/png.")

    def test_index_html_root_endpoint(self):
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("apple-mobile-web-app-capable", resp.text)
        print("[TEST PASS] / returns 200 OK with PWA-enabled index.html.")

if __name__ == "__main__":
    unittest.main()
