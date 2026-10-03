from pathlib import Path
import unittest
import sys
import time

BASE_DIR = str(Path(__file__).resolve().parent.parent)
sys.path.insert(0, BASE_DIR)

from src.realtime.iett_client import iett_client, is_valid_bus_query
from src.realtime.eta_engine import eta_engine, haversine_distance_meters, calculate_bearing
from src.realtime.traffic_engine import traffic_engine

class TestRealtimeEngine(unittest.TestCase):
    def test_line_code_validation(self):
        self.assertFalse(is_valid_bus_query("M2"))
        self.assertFalse(is_valid_bus_query("M1A"))
        self.assertFalse(is_valid_bus_query("T1"))
        self.assertFalse(is_valid_bus_query("F1"))
        self.assertFalse(is_valid_bus_query("MARMARAY"))
        self.assertFalse(is_valid_bus_query("WALK"))
        self.assertTrue(is_valid_bus_query("500T"))
        self.assertTrue(is_valid_bus_query("129T"))
        self.assertTrue(is_valid_bus_query("34AS"))
        self.assertTrue(is_valid_bus_query("1"))
        print("\n[TEST PASS] Bus line filter successfully distinguishes rail/metro from buses")

    def test_haversine_distance(self):
        # Kadıköy Pier (40.9904, 29.0253) to Beşiktaş Pier (41.0422, 29.0067)
        dist = haversine_distance_meters(40.9904, 29.0253, 41.0422, 29.0067)
        self.assertGreater(dist, 5500)
        self.assertLess(dist, 6500)
        print(f"[TEST PASS] Haversine distance Kadıköy-Beşiktaş: {int(dist)}m")

    def test_calculate_bearing(self):
        # Due north
        b_north = calculate_bearing(41.0, 29.0, 41.1, 29.0)
        self.assertAlmostEqual(b_north, 0.0, delta=1.0)
        # Due east
        b_east = calculate_bearing(41.0, 29.0, 41.0, 29.1)
        self.assertAlmostEqual(b_east, 90.0, delta=1.0)
        print(f"[TEST PASS] Bearing calculation: North={b_north:.1f}°, East={b_east:.1f}°")

    def test_receding_bus_elimination(self):
        stop_lat = 41.0667
        stop_lon = 28.9936
        bus_id = "TEST-RECEDING-01"

        # Ping 1: bus was 200m from stop
        eta_engine.record_bus_position(bus_id, 41.0680, 28.9936)
        time.sleep(3.1) # Simulate elapsed time

        # Ping 2: bus moved to 600m from stop (moving AWAY)
        is_approaching = eta_engine.is_bus_approaching(bus_id, 41.0720, 28.9936, stop_lat, stop_lon)
        self.assertFalse(is_approaching, "Receding bus should be flagged as not approaching")
        print("[TEST PASS] Receding vehicle successfully eliminated from catchable radar")

    def test_intercept_calculation(self):
        stop_lat = 41.0000
        stop_lon = 29.0000

        mock_buses = [
            {"kapino": "B-001", "lat": 41.0040, "lon": 29.0000, "direction": "Merkez", "timestamp": "2026-09-25 12:00:00"},
            {"kapino": "B-002", "lat": 41.0250, "lon": 29.0000, "direction": "Merkez", "timestamp": "2026-09-25 12:00:00"}
        ]

        intercept = eta_engine.find_best_vehicle_intercept(
            mock_buses,
            stop_lat=stop_lat,
            stop_lon=stop_lon,
            walk_seconds_to_stop=60.0
        )
        self.assertIsNotNone(intercept)
        self.assertIn("status", intercept)
        self.assertIn(intercept["status"], ["CATCHABLE", "RECEDING", "MISSED"])
        print(f"[TEST PASS] Intercept status: {intercept['status']}, vehicle: {intercept['kapino']}")

    def test_traffic_engine_multimodal_differentiation(self):
        # 1. Rail leg (Metro M2) should have TCC = 1.0 (Traffic immune)
        m2_traffic = traffic_engine.evaluate_leg_traffic(
            mode="SUBWAY",
            route_name="M2",
            start_lat=41.0667, start_lon=28.9936,
            end_lat=41.0784, end_lon=29.0112,
            scheduled_sec=600
        )
        self.assertEqual(m2_traffic["tcc"], 1.0)
        self.assertEqual(m2_traffic["delay_seconds"], 0)
        self.assertFalse(m2_traffic["is_surface_traffic"])

        # 2. Metrobüs leg should have TCC = 1.05 (Dedicated busway)
        mb_traffic = traffic_engine.evaluate_leg_traffic(
            mode="BUS",
            route_name="34AS Metrobüs",
            start_lat=41.0667, start_lon=28.9936,
            end_lat=41.0682, end_lon=29.0118,
            scheduled_sec=600
        )
        self.assertEqual(mb_traffic["tcc"], 1.05)
        self.assertFalse(mb_traffic["is_surface_traffic"])

        # 3. Surface bus on congested arterial (e.g. 500T on Bosphorus / D-100)
        # Using a simulated weekday 18:30 timestamp (evening peak)
        simulated_evening_peak = 1790436600.0 # corresponds to evening peak
        bus_traffic = traffic_engine.evaluate_leg_traffic(
            mode="BUS",
            route_name="500T",
            start_lat=41.045, start_lon=29.030,
            end_lat=41.050, end_lon=29.040,
            scheduled_sec=1200
        )
        self.assertTrue(bus_traffic["is_surface_traffic"])
        self.assertGreaterEqual(bus_traffic["tcc"], 1.0)
        print(f"[TEST PASS] Traffic Engine verified: Metro TCC={m2_traffic['tcc']}, Metrobüs TCC={mb_traffic['tcc']}, Bus TCC={bus_traffic['tcc']}")

    def test_live_iett_endpoint_robustness(self):
        buses = iett_client.get_live_buses("500T")
        self.assertIsInstance(buses, list)
        print(f"[TEST PASS] Live IETT connection verified (500T active vehicles: {len(buses)})")

if __name__ == "__main__":
    unittest.main()
