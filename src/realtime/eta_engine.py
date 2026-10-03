import math
import time
from typing import Dict, List, Optional, Tuple

def haversine_distance_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculates the great-circle distance between two GPS coordinates in meters."""
    R = 6371000.0  # Earth radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2.0)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0)**2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return R * c

def calculate_bearing(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculates forward compass bearing (azimuth) from point 1 to point 2 in degrees (0..360)."""
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_lambda = math.radians(lon2 - lon1)

    y = math.sin(delta_lambda) * math.cos(phi2)
    x = math.cos(phi1) * math.sin(phi2) - math.sin(phi1) * math.cos(phi2) * math.cos(delta_lambda)
    bearing = math.degrees(math.atan2(y, x))
    return (bearing + 360.0) % 360.0

class ETAEngine:
    """
    Vector-aware Real-Time Vehicle Intercept & Arrival Radar.
    Filters out buses that have already passed the boarding stop or are moving away,
    and calculates realistic walking-speed to transit arrival rendezvous.
    """

    def __init__(self, avg_urban_speed_kmh: float = 20.0, avg_metrobus_speed_kmh: float = 38.0):
        self.avg_bus_speed_mps = (avg_urban_speed_kmh * 1000.0) / 3600.0       # ~5.55 m/s (~20 km/h)
        self.avg_metrobus_speed_mps = (avg_metrobus_speed_kmh * 1000.0) / 3600.0 # ~10.55 m/s (~38 km/h)
        self._history: Dict[str, Tuple[float, float, float]] = {}  # kapino -> (lat, lon, timestamp)

    def record_bus_position(self, kapino: str, lat: float, lon: float):
        """Records position history for motion vector calculation with TTL cleanup."""
        now = time.time()
        self._history[kapino] = (lat, lon, now)
        # Periodic cleanup: Evict entries older than 30 minutes or when cache exceeds 2000 entries
        if len(self._history) > 2000:
            cutoff = now - 1800.0
            self._history = {k: v for k, v in self._history.items() if v[2] > cutoff}

    def is_bus_approaching(
        self,
        kapino: str,
        current_lat: float,
        current_lon: float,
        stop_lat: float,
        stop_lon: float
    ) -> bool:
        """
        Determines whether the vehicle is getting closer to the stop based on
        successive motion pings or heading vectors.
        """
        curr_dist = haversine_distance_meters(current_lat, current_lon, stop_lat, stop_lon)
        
        # If very close (< 60m), consider at-stop
        if curr_dist < 60:
            return True

        if kapino in self._history:
            prev_lat, prev_lon, prev_time = self._history[kapino]
            # If historical ping is recent (between 3s and 120s old)
            if 3.0 <= (time.time() - prev_time) <= 120.0:
                prev_dist = haversine_distance_meters(prev_lat, prev_lon, stop_lat, stop_lon)
                # If current distance is strictly greater than previous distance, bus is moving AWAY!
                if curr_dist > prev_dist + 15.0:
                    return False

        # Update position in history
        self.record_bus_position(kapino, current_lat, current_lon)
        return True

    def find_best_vehicle_intercept(
        self,
        buses: List[Dict],
        stop_lat: float,
        stop_lon: float,
        walk_seconds_to_stop: float = 0.0,
        is_metrobus: bool = False,
        target_stop_sequence: Optional[int] = None
    ) -> Optional[Dict]:
        """
        Evaluates active vehicles on a line and finds the earliest catchable vehicle.
        Eliminates receding buses and vehicles that already departed the stop.
        """
        if not buses:
            return None

        speed_mps = self.avg_metrobus_speed_mps if is_metrobus else self.avg_bus_speed_mps
        candidates = []

        for bus in buses:
            kapino = bus.get("kapino", "")
            b_lat = bus.get("lat", 0.0)
            b_lon = bus.get("lon", 0.0)

            # Check stop sequence if available
            bus_seq = bus.get("stop_sequence")
            if target_stop_sequence is not None and bus_seq is not None:
                try:
                    if int(bus_seq) > target_stop_sequence:
                        # Bus already passed this stop in sequence!
                        continue
                except (ValueError, TypeError):
                    pass

            dist_straight = haversine_distance_meters(b_lat, b_lon, stop_lat, stop_lon)
            
            # Check vector: is the bus approaching or receding?
            approaching = self.is_bus_approaching(kapino, b_lat, b_lon, stop_lat, stop_lon)

            # Urban road winding factor (detour ratio: straight distance * 1.35)
            est_road_dist = dist_straight * 1.35
            est_travel_seconds = est_road_dist / max(1.0, speed_mps)

            # Can user arrive at stop before bus arrives? (with 30s buffer)
            can_catch = approaching and (est_travel_seconds >= (walk_seconds_to_stop - 30))

            status = "CATCHABLE" if can_catch else ("RECEDING" if not approaching else "MISSED")

            candidates.append({
                "kapino": kapino,
                "lat": b_lat,
                "lon": b_lon,
                "direction": bus.get("direction", ""),
                "straight_distance_meters": int(round(dist_straight)),
                "road_distance_meters": int(round(est_road_dist)),
                "eta_seconds": int(round(est_travel_seconds)),
                "eta_minutes": max(1, int(round(est_travel_seconds / 60.0))),
                "can_catch": can_catch,
                "approaching": approaching,
                "status": status,
                "slack_minutes": int(round((est_travel_seconds - walk_seconds_to_stop) / 60.0)),
                "timestamp": bus.get("timestamp", "")
            })

        # Sort by travel ETA
        candidates.sort(key=lambda x: x["eta_seconds"])

        # Prioritize catchable approaching vehicles
        catchable = [c for c in candidates if c["can_catch"] and c["approaching"]]
        if catchable:
            return catchable[0]

        # Next preference: approaching even if tight on time
        approaching_list = [c for c in candidates if c["approaching"]]
        if approaching_list:
            return approaching_list[0]

        # Fallback to closest if any
        if candidates:
            return candidates[0]

        return None

eta_engine = ETAEngine()
