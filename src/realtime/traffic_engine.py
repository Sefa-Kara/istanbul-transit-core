import time
import math
from typing import Dict, List, Optional, Tuple

class TrafficEngine:
    """
    Zero-cost Dynamic Istanbul Traffic Congestion Engine (FCD + Peak-Hour Modeler).
    Differentiates grade-separated transit (Metro, Marmaray, Metrobüs, Vapur) from 
    surface buses and highway coaches stuck in Istanbul traffic jams.
    """

    # Major Istanbul congested corridors (lat_min, lat_max, lon_min, lon_max, name, peak_severity)
    CORRIDORS = [
        {"name": "15 Temmuz Şehitler Köprüsü & Çevre Yolu", "lat": (41.040, 41.055), "lon": (29.020, 29.048), "peak": 2.5},
        {"name": "Fatih Sultan Mehmet Köprüsü (FSM)", "lat": (41.082, 41.096), "lon": (29.045, 29.075), "peak": 2.3},
        {"name": "Büyükdere Caddesi (Şişli - Maslak)", "lat": (41.060, 41.115), "lon": (28.990, 29.025), "peak": 2.0},
        {"name": "D-100 Haliç - Mecidiyeköy Arter", "lat": (41.035, 41.070), "lon": (28.930, 28.995), "peak": 1.9},
        {"name": "D-100 Anadolu Yakası (Kadıköy - Kartal)", "lat": (40.890, 41.000), "lon": (29.040, 29.230), "peak": 1.8},
        {"name": "TEM Mahmutbey - Gaziosmanpaşa", "lat": (41.050, 41.090), "lon": (28.790, 28.870), "peak": 2.1},
        {"name": "Bağdat Caddesi & Sahil Koridoru", "lat": (40.950, 40.990), "lon": (29.030, 29.110), "peak": 1.6},
    ]

    def __init__(self):
        # In-memory FCD corridor observations (updated via live telemetry)
        self._corridor_fcd: Dict[str, Dict] = {}

    def get_corridor_tcc(self, lat: float, lon: float, timestamp_sec: Optional[float] = None) -> Tuple[float, str]:
        """
        Returns Traffic Congestion Coefficient (TCC >= 1.0) and description label for a coordinate.
        TCC = 1.0 (Free flow) up to 2.5 (Severe gridlock).
        """
        now = time.localtime(timestamp_sec if timestamp_sec else time.time())
        hour = now.tm_hour + (now.tm_min / 60.0)
        is_weekday = now.tm_wday < 5

        # Check if point falls into any known high-density corridor
        matched_corridor = None
        for c in self.CORRIDORS:
            if c["lat"][0] <= lat <= c["lat"][1] and c["lon"][0] <= lon <= c["lon"][1]:
                matched_corridor = c
                break

        # Check if live FCD telemetry exists for this corridor (< 3 minutes old)
        if matched_corridor and matched_corridor["name"] in self._corridor_fcd:
            fcd = self._corridor_fcd[matched_corridor["name"]]
            if time.time() - fcd["time"] < 180:
                avg_speed = fcd["avg_speed_kmh"]
                if avg_speed < 12.0:
                    return (2.4, "Kilit Trafik (FCD: <12 km/s)")
                elif avg_speed < 22.0:
                    return (1.8, "Yoğun Trafik (FCD: ~18 km/s)")
                elif avg_speed < 35.0:
                    return (1.3, "Orta Akıcı (FCD: ~30 km/s)")
                else:
                    return (1.05, "Açık Yol (FCD)")

        # Baseline Peak-Hour Statistical Model (Istanbul traffic patterns)
        peak_factor = matched_corridor["peak"] if matched_corridor else 1.5

        if is_weekday:
            # Morning Peak: 07:30 - 09:30 (Max at 08:30)
            if 7.5 <= hour <= 9.5:
                intensity = 1.0 - abs(hour - 8.5) / 1.0
                tcc = 1.0 + (peak_factor - 1.0) * intensity
                return (round(tcc, 2), "Sabah Zirvesi (Yoğun Trafik)")
            # Evening Peak: 17:00 - 19:45 (Max at 18:30)
            elif 17.0 <= hour <= 19.75:
                intensity = 1.0 - abs(hour - 18.5) / 1.375
                tcc = 1.0 + (peak_factor - 1.0) * intensity
                return (round(tcc, 2), "Akşam Zirvesi (Aşırı Yoğun)")
            # Midday: 10:00 - 16:30
            elif 10.0 <= hour <= 16.5:
                return (1.2, "Normal Gün İçi Trafiği")
            # Night: 22:30 - 06:30
            elif hour >= 22.5 or hour <= 6.5:
                return (1.0, "Gece Açık Yol")
            else:
                return (1.1, "Hafif Trafik")
        else:
            # Weekend afternoon rush (14:00 - 20:00)
            if 14.0 <= hour <= 20.0:
                return (1.35, "Hafta Sonu Yoğunluğu")
            elif hour >= 23.0 or hour <= 7.0:
                return (1.0, "Gece Açık Yol")
            else:
                return (1.15, "Akıcı")

    def update_fcd_telemetry(self, corridor_name: str, bus_speeds_kmh: List[float]):
        """Ingests live speed readings from İETT buses in a corridor."""
        if not bus_speeds_kmh:
            return
        valid_speeds = [s for s in bus_speeds_kmh if 3.0 <= s <= 90.0]
        if not valid_speeds:
            return
        avg_speed = sum(valid_speeds) / len(valid_speeds)
        self._corridor_fcd[corridor_name] = {
            "time": time.time(),
            "avg_speed_kmh": avg_speed,
            "sample_count": len(valid_speeds)
        }

    def evaluate_leg_traffic(self, mode: str, route_name: str, start_lat: float, start_lon: float, end_lat: float, end_lon: float, scheduled_sec: int) -> Dict:
        """
        Applies multimodal physics:
        - Rail (Metro, Marmaray, Tram): TCC = 1.0 (Grade-separated, immune to traffic)
        - Ferry: TCC = 1.0 (Sea lane, immune to traffic)
        - Metrobüs: TCC = 1.05 (Dedicated busway with minor station queuing)
        - Surface Bus / Coach: Affected by corridor TCC
        """
        norm_mode = mode.upper()
        norm_name = route_name.upper()

        if norm_mode in ("SUBWAY", "TRAM", "RAIL", "FERRY") or "METRO" in norm_name and "METROBÜS" not in norm_name and "METROBUS" not in norm_name:
            if "METROBÜS" not in norm_name and "METROBUS" not in norm_name:
                return {
                    "tcc": 1.0,
                    "status": "Raylı / Deniz Ulaşımı (Trafikten Muaf)",
                    "delay_seconds": 0,
                    "adjusted_duration_seconds": scheduled_sec,
                    "is_surface_traffic": False
                }

        if "METROBÜS" in norm_name or "METROBUS" in norm_name:
            # Metrobüs has physical concrete barriers separating it from D-100 traffic
            return {
                "tcc": 1.05,
                "status": "Metrobüs Özel Yolu (Trafikten İzole)",
                "delay_seconds": int(scheduled_sec * 0.05),
                "adjusted_duration_seconds": int(scheduled_sec * 1.05),
                "is_surface_traffic": False
            }

        # Surface Bus: Calculate midpoint TCC
        mid_lat = (start_lat + end_lat) / 2.0
        mid_lon = (start_lon + end_lon) / 2.0
        tcc, status = self.get_corridor_tcc(mid_lat, mid_lon)

        adjusted_sec = int(round(scheduled_sec * tcc))
        delay_sec = max(0, adjusted_sec - scheduled_sec)

        return {
            "tcc": tcc,
            "status": status,
            "delay_seconds": delay_sec,
            "adjusted_duration_seconds": adjusted_sec,
            "is_surface_traffic": True
        }

# Singleton instance
traffic_engine = TrafficEngine()
