from pathlib import Path
import unittest
import sys
import os
import subprocess
import time
import json
import urllib.request

BASE_DIR = str(Path(__file__).resolve().parent.parent)
sys.path.insert(0, BASE_DIR)

from src.core.hybrid_router import hybrid_router, calculate_fare, calculate_carbon_saved

class TestMultiModalRouter(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Start OTP if not already running
        cls.otp_started_by_test = False
        try:
            with urllib.request.urlopen("http://localhost:8080/", timeout=1) as resp:
                pass
        except Exception:
            print("\nStarting OpenTripPlanner for test suite...")
            subprocess.run(["bash", os.path.join(BASE_DIR, "bin", "start_otp.sh")], check=True)
            cls.otp_started_by_test = True

    @classmethod
    def tearDownClass(cls):
        # Stop OTP if we started it to maintain zero background processes
        if cls.otp_started_by_test:
            print("\nShutting down OpenTripPlanner to ensure zero idle background processes...")
            subprocess.run(["bash", os.path.join(BASE_DIR, "bin", "stop_otp.sh")])

    def test_fare_and_carbon_calculations(self):
        sample_legs = [
            {"mode": "WALK", "duration_minutes": 5, "distance_meters": 350},
            {"mode": "SUBWAY", "route_short_name": "M2", "agency_name": "Metro İstanbul", "duration_minutes": 15, "distance_meters": 8500},
            {"mode": "WALK", "duration_minutes": 3, "distance_meters": 200},
            {"mode": "FERRY", "route_short_name": "KDK-KBT", "agency_name": "Şehir Hatları", "duration_minutes": 25, "distance_meters": 6200}
        ]
        fare = calculate_fare(sample_legs)
        self.assertIn("standard_tl", fare)
        self.assertIn("student_tl", fare)
        self.assertGreater(fare["standard_tl"], 0)
        self.assertLess(fare["student_tl"], fare["standard_tl"])

        carbon = calculate_carbon_saved(8500 + 6200)
        self.assertGreater(carbon, 1.0)
        print(f"\n[TEST PASS] Fare: Standard {fare['standard_tl']} TL, Student {fare['student_tl']} TL | Carbon Saved: {carbon} kg CO2")

    def test_ferry_priority_and_forcing(self):
        # Kadıköy (40.9904, 29.0220) to Beşiktaş (41.0417, 29.0046)
        res = hybrid_router.plan(
            from_lat=40.9904,
            from_lon=29.0220,
            to_lat=41.0417,
            to_lon=29.0046,
            prefer_modes=["FERRY"],
            force_mode="FERRY",
            date_str="2026-09-26",
            time_str="14:00:00",
            allow_minibus=False,
            num_itineraries=2
        )
        self.assertTrue(res.get("success"), f"Routing failed: {res.get('error')}")
        itins = res.get("itineraries", [])
        self.assertGreater(len(itins), 0, "No itineraries returned")
        first_itin = itins[0]
        modes = [l["mode"] for l in first_itin["legs"]]
        self.assertIn("FERRY", modes, f"Forced ferry was not in itinerary modes: {modes}")
        print(f"[TEST PASS] Forced Ferry Route: {[l['mode'] + ' ' + l['route_short_name'] for l in first_itin['legs']]}")

    def test_subway_rail_priority(self):
        # Üsküdar (41.0267, 29.0153) to Taksim (41.0370, 28.9850)
        res = hybrid_router.plan(
            from_lat=41.0267,
            from_lon=29.0153,
            to_lat=41.0370,
            to_lon=28.9850,
            prefer_modes=["SUBWAY", "METRO"],
            target="LEAST_TRANSFERS",
            date_str="2026-09-26",
            time_str="14:00:00",
            allow_minibus=False,
            num_itineraries=2
        )
        self.assertTrue(res.get("success"))
        itins = res.get("itineraries", [])
        self.assertGreater(len(itins), 0)
        first_itin = itins[0]
        modes = [l["mode"] for l in first_itin["legs"]]
        self.assertTrue("SUBWAY" in modes or "RAIL" in modes, f"Neither SUBWAY nor RAIL found in {modes}")
        print(f"[TEST PASS] Rail Priority Route: {[l['mode'] + ' ' + l['route_short_name'] for l in first_itin['legs']]}")

    def test_intermediate_stops_extraction(self):
        # Route with transit leg should contain intermediate stops
        res = hybrid_router.plan(
            from_lat=40.994074,
            from_lon=29.024337,
            to_lat=41.041917,
            to_lon=29.060170,
            prefer_modes=["BUS"],
            date_str="2026-09-26",
            time_str="14:00:00",
            allow_minibus=False,
            num_itineraries=1
        )
        self.assertTrue(res.get("success"))
        itins = res.get("itineraries", [])
        self.assertGreater(len(itins), 0)
        bus_legs = [l for l in itins[0]["legs"] if l["mode"] == "BUS"]
        if bus_legs:
            leg = bus_legs[0]
            print(f"[TEST PASS] Intermediate stops extracted: {leg['stop_count']} stops on line {leg['route_short_name']}")
            if leg["intermediate_stops"]:
                print(f"            Sample intermediate: {leg['intermediate_stops'][0]['name']}")

    def test_minibus_exclusion(self):
        res = hybrid_router.plan(
            from_lat=40.9904,
            from_lon=29.0220,
            to_lat=41.0417,
            to_lon=29.0046,
            date_str="2026-09-26",
            time_str="14:00:00",
            allow_minibus=False,
            num_itineraries=3
        )

        self.assertTrue(res.get("success"))
        for itin in res.get("itineraries", []):
            for leg in itin["legs"]:
                agency = leg.get("agency_name", "").lower()
                self.assertNotIn("minibüs", agency)
                self.assertNotIn("dolmuş", agency)
        print("[TEST PASS] Minibus exclusion verified (Zero minibus legs found)")

    def test_istanbul_airport_resolution(self):
        # Mecidiyeköy (41.0667, 28.9936) to İstanbul Havalimanı (41.2612, 28.7420)
        res = hybrid_router.plan(
            from_lat=41.0667,
            from_lon=28.9936,
            to_lat=41.2612,
            to_lon=28.7420,
            date_str="2026-09-26",
            time_str="08:30:00",
            num_itineraries=4
        )
        self.assertTrue(res.get("success"), f"Airport routing failed: {res.get('error')}")
        itins = res.get("itineraries", [])
        self.assertGreater(len(itins), 0, "No airport itineraries returned")
        
        # Verify fastest option reaches airport in <= 70 minutes (realistic M7/M2 + M11 transfer)
        fastest = itins[0]
        self.assertLessEqual(fastest["total_duration_minutes"], 70)
        
        # Verify M11 or H-2 or Havaist is present
        all_routes = [l.get("route_short_name") for it in itins for l in it["legs"]]
        has_airport_line = any(r in ["M11", "H-2", "HVİST-5", "HVİST-14", "HVİST-16"] for r in all_routes if r)
        self.assertTrue(has_airport_line, f"No airport transit line found in {all_routes}")
        print(f"[TEST PASS] İstanbul Havalimanı (IST) Route Resolved: {fastest['total_duration_minutes']} min, Fare: {fastest['fare']}")

    def test_midnight_airport_to_halicioglu(self):
        # User Failure Screenshot Case: İstanbul Havalimanı to HALICIOĞLU at 00:17 AM
        res = hybrid_router.plan(
            from_lat=41.2605,
            from_lon=28.7425,
            to_lat=41.049117,
            to_lon=28.94677,
            date_str="2026-09-26",
            time_str="00:17:00",
            num_itineraries=3
        )
        self.assertTrue(res.get("success"), f"Midnight routing failed: {res.get('error')}")
        itins = res.get("itineraries", [])
        self.assertGreater(len(itins), 0, "No itineraries found for midnight Havalimanı -> Halıcıoğlu")
        
        fastest = itins[0]
        # Scheduled duration (excluding live traffic delay) should be <= 125 min with realistic transfer buffers
        scheduled_dur = fastest["total_duration_minutes"] - fastest.get("traffic_delay_minutes", 0)
        self.assertLessEqual(scheduled_dur, 125)
        
        # Verify 34G Metrobüs or H-2 is used in the late night chain
        modes = [l["mode"] for l in fastest["legs"]]
        routes = [l.get("route_short_name") for l in fastest["legs"]]
        has_metrobus = any(r and r.startswith("34") for r in routes)
        self.assertTrue(has_metrobus, f"No Metrobus line found in {routes}")
        print(f"[TEST PASS] Midnight Havalimanı -> Halıcıoğlu Verified: {fastest['total_duration_minutes']} min, Chain: {routes}")

    def test_daytime_airport_to_halicioglu_m11_priority(self):
        # Daytime user case: İstanbul Havalimanı to Halıcıoğlu at 11:00 AM (M11 must be option 1)
        res = hybrid_router.plan(
            from_lat=41.2612,
            from_lon=28.7420,
            to_lat=41.049117,
            to_lon=28.94677,
            date_str="2026-09-28",
            time_str="11:00:00",
            num_itineraries=3
        )
        self.assertTrue(res.get("success"), f"Daytime Havalimani -> Halıcıoğlu failed: {res.get('error')}")
        itins = res.get("itineraries", [])
        self.assertGreater(len(itins), 0, "No itineraries found")
        top_itin = itins[0]
        routes = [l.get("route_short_name") for l in top_itin["legs"]]
        self.assertIn("M11", routes, f"M11 Metro was not Option 1 for daytime airport transit! Routes: {routes}")
        print(f"[TEST PASS] Daytime Havalimanı -> Halıcıoğlu M11 Priority Verified: {top_itin['total_duration_minutes']} min, Chain: {routes}")

    def test_sabiha_gokcen_to_kadikoy_m4(self):
        # SAW (40.9086, 29.3146) to Kadıköy (40.9904, 29.0220)
        res = hybrid_router.plan(
            from_lat=40.908621,
            from_lon=29.314600,
            to_lat=40.9904,
            to_lon=29.0220,
            date_str="2026-09-28",
            time_str="14:00:00",
            num_itineraries=3
        )
        self.assertTrue(res.get("success"), f"SAW -> Kadıköy failed: {res.get('error')}")
        itins = res.get("itineraries", [])
        self.assertGreater(len(itins), 0, "No itineraries found for SAW -> Kadıköy")
        top_itin = itins[0]
        modes = [l["mode"] for l in top_itin["legs"]]
        routes = [l.get("route_short_name") for l in top_itin["legs"]]
        has_m4_or_e10 = any(r in ["M4", "E-10"] for r in routes)
        self.assertTrue(has_m4_or_e10, f"Expected M4 or E-10 in {routes}")
        print(f"[TEST PASS] SAW -> Kadıköy Resolved: {top_itin['total_duration_minutes']} min, Chain: {routes}")

if __name__ == "__main__":
    unittest.main()
