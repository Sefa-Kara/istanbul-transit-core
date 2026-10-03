import urllib.request
import json
import re
import math
from datetime import datetime
from typing import Dict, List, Any, Optional

from src.realtime.iett_client import iett_client
from src.realtime.eta_engine import eta_engine
from src.realtime.traffic_engine import traffic_engine
from src.utils.text_utils import repair_turkish_mojibake

from src.config import OTP_GRAPHQL_URL

def get_peripheral_connector_info(lat: float, lon: float) -> Optional[Dict[str, Any]]:
    """
    Returns synthetic peripheral gateway connector data for rural Istanbul borders
    (Silivri, Çatalca, Şile, Tuzla) replacing 0-min teleportation with real suburban legs.
    """
    # Silivri (Western rural border)
    if lon < 28.38:
        return {
            "region": "silivri",
            "gateway_coords": (41.0150, 28.6410),
            "gateway_name": "TÜYAP Metrobüs",
            "origin_name": "Silivri Otogar",
            "route_short_name": "303A",
            "route_long_name": "Silivri - Avcılar / TÜYAP Metrobüs",
            "duration_sec": 4080,  # 68 min
            "distance_m": 32000
        }
    # Çatalca (North-western rural border - Çatalca center is at 41.14N, 28.46E)
    if lon < 28.54 and lat > 41.08:
        return {
            "region": "catalca",
            "gateway_coords": (41.0150, 28.6410),
            "gateway_name": "TÜYAP Metrobüs",
            "origin_name": "Çatalca Merkez",
            "route_short_name": "401",
            "route_long_name": "Çatalca - TÜYAP Metrobüs",
            "duration_sec": 2520,  # 42 min
            "distance_m": 21000
        }
    # Şile / Ağva (Eastern Black Sea rural border)
    if lon > 29.45 and lat > 41.05:
        return {
            "region": "sile",
            "gateway_coords": (41.0280, 29.1750),
            "gateway_name": "Ümraniye Tepeüstü Hub",
            "origin_name": "Şile Terminal",
            "route_short_name": "139A",
            "route_long_name": "Şile - Ümraniye / Üsküdar",
            "duration_sec": 4800,  # 80 min
            "distance_m": 52000
        }
    # Tuzla / Çayırova border (South-eastern border)
    if lon > 29.2800 and lat < 40.8500:
        return {
            "region": "tuzla",
            "gateway_coords": (40.8800, 29.2320),
            "gateway_name": "Tavşantepe Metro İstasyonu",
            "origin_name": "Tuzla Şifa Mahallesi",
            "route_short_name": "130Ş",
            "route_long_name": "Tuzla - Kartal / Kadıköy",
            "duration_sec": 1680,  # 28 min
            "distance_m": 14000
        }
    return None

def find_nearest_accessible_stop(lat: float, lon: float, max_dist_m: float = 1400.0) -> Optional[Dict[str, Any]]:
    """
    Locates the best GTFS transit stop/hub in SQLite within max_dist_m,
    prioritizing major rail/metrobus hubs to shield against OSM pedestrian barrier degeneration
    and prevent routing to isolated local school bus stops.
    """
    try:
        from src.core.search_engine import search_engine
        cur = search_engine.conn.cursor()
        dlat = max_dist_m / 111000.0
        dlon = max_dist_m / (111000.0 * 0.76)
        cur.execute('''
            SELECT stop_id, name, lat, lon, trip_count
            FROM stops
            WHERE lat BETWEEN ? AND ?
              AND lon BETWEEN ? AND ?
              AND trip_count >= 3
        ''', (lat - dlat, lat + dlat, lon - dlon, lon + dlon))
        rows = cur.fetchall()
        if not rows:
            return None

        def rank_key(r):
            sid, name, s_lat, s_lon, tc = r
            d = math.hypot(lat - s_lat, (lon - s_lon) * 0.76) * 111000.0
            name_u = name.upper()
            if any(k in name_u for k in ("METROBÜS", "METRO", "MARMARAY", "TRAMVAY", "VAPUR", "İSKELE")):
                hub_bonus = 950.0
            elif tc >= 500:
                hub_bonus = 400.0
            else:
                hub_bonus = 0.0
            return (d - hub_bonus) if d <= max_dist_m else 999999.0

        best = min(rows, key=rank_key)
        best_d = math.hypot(lat - best[2], (lon - best[3]) * 0.76) * 111000.0
        if best_d <= max_dist_m:
            return {"stop_id": best[0], "name": best[1], "lat": best[2], "lon": best[3], "distance_m": int(best_d), "trips": best[4]}
        return None
    except Exception:
        return None


def clean_text(text: Optional[str]) -> str:
    return repair_turkish_mojibake(text)

def calculate_fare(legs: List[Dict[str, Any]]) -> Dict[str, float]:
    """
    Computes estimated 2026 Istanbulkart fare based on transit legs.
    - Standard Metro/Tram/Bus: 27.50 base, 19.50 transfer 1, 15.00 transfer 2, 9.50 transfer 3+
    - Marmaray: ~35.00 avg (distance-based 27.50 - 59.00)
    - Metrobus: ~32.00 avg (stop-count based 27.50 - 45.00)
    - Ferry: ~35.00 avg
    - Havaist Airport Shuttles: ~200.00 TL fixed
    - M11 Airport Metro: 27.50 TL
    - Student: ~50% discount on municipal lines
    """
    transit_legs = [l for l in legs if l.get("mode") != "WALK"]
    if not transit_legs:
        return {"standard_tl": 0.0, "student_tl": 0.0}

    total_std = 0.0
    transfer_index = 0

    for l in transit_legs:
        mode = l.get("mode")
        short_name = (l.get("route_short_name") or "").upper()
        agency = (l.get("agency_name") or "").lower()

        if "havaist" in agency or short_name.startswith("HVIST") or short_name.startswith("HVİST"):
            cost = 200.00
            transfer_index = 0
        elif "marmaray" in short_name.lower() or "marmaray" in agency:
            cost = 35.00
            transfer_index = 0
        elif short_name.startswith("34") and len(short_name) <= 4:
            cost = 32.00
            transfer_index = 0
        elif mode == "FERRY" or "turyol" in agency or "dentur" in agency:
            cost = 35.00
            transfer_index = 0
        else:
            if transfer_index == 0:
                cost = 27.50
            elif transfer_index == 1:
                cost = 19.50
            elif transfer_index == 2:
                cost = 15.00
            else:
                cost = 9.50
            transfer_index += 1

        total_std += cost

    total_student = round(total_std * 0.49, 2)
    return {
        "standard_tl": round(total_std, 2),
        "student_tl": total_student
    }

def calculate_carbon_saved(total_transit_distance_meters: int) -> float:
    """
    Average car in Istanbul emits ~140g CO2/km.
    Public transit net saving: ~110g CO2/km (0.11 kg CO2/km).
    """
    km = total_transit_distance_meters / 1000.0
    return round(km * 0.11, 2)

class HybridTransitRouter:
    def plan(
        self,
        from_lat: float,
        from_lon: float,
        to_lat: float,
        to_lon: float,
        prefer_modes: Optional[List[str]] = None,
        avoid_modes: Optional[List[str]] = None,
        force_mode: Optional[str] = None,
        allow_minibus: bool = False,
        target: str = "FASTEST",
        time_type: str = "DEPART_NOW",
        date_str: Optional[str] = None,
        time_str: Optional[str] = None,
        num_itineraries: int = 4,
        prefer_ferry: bool = False,
        force_ferry: bool = False
    ) -> Dict[str, Any]:
        # Save raw original user coordinates
        raw_from_lat, raw_from_lon = from_lat, from_lon
        raw_to_lat, raw_to_lon = to_lat, to_lon
        straight_km = math.hypot(from_lat - to_lat, (from_lon - to_lon) * 0.76) * 111.0

        # Peripheral Gateway Connectors (Silivri, Çatalca, Şile, Tuzla)
        from_peri = get_peripheral_connector_info(from_lat, from_lon)
        to_peri = get_peripheral_connector_info(to_lat, to_lon)

        # Edge Case: Both endpoints in the same peripheral region and close by (< 18 km)
        if from_peri and to_peri and from_peri["region"] == to_peri["region"] and straight_km < 18.0:
            local_dur_sec = max(600, int(straight_km * 160) + 300)
            local_dist_m = int(straight_km * 1000)
            local_bus_name = "300G" if from_peri["region"] == "silivri" else ("402" if from_peri["region"] == "catalca" else "139")
            synth_itinerary = {
                "option_id": 1,
                "total_duration_minutes": max(10, local_dur_sec // 60),
                "traffic_delay_minutes": 2,
                "walk_duration_minutes": 5,
                "transfers": 0,
                "fare": {"standard_tl": 27.50, "student_tl": 13.50},
                "co2_saved_kg": round(straight_km * 0.11, 2),
                "is_scenic_detour": False,
                "scenic_badge": None,
                "scenic_description": None,
                "legs": [
                    {
                        "step": 1,
                        "mode": "WALK",
                        "duration_minutes": 3,
                        "distance_meters": 200,
                        "from_stop": "Başlangıç Konumu",
                        "to_stop": f"{from_peri['origin_name']} Durağı",
                        "from_coords": {"lat": raw_from_lat, "lon": raw_from_lon},
                        "to_coords": {"lat": raw_from_lat, "lon": raw_from_lon},
                        "route_short_name": "",
                        "route_long_name": "",
                        "agency_name": "",
                        "stop_count": 0,
                        "intermediate_stops": []
                    },
                    {
                        "step": 2,
                        "mode": "BUS",
                        "duration_minutes": max(7, (local_dur_sec // 60) - 5),
                        "distance_meters": local_dist_m,
                        "from_stop": f"{from_peri['origin_name']} Durağı",
                        "to_stop": f"{to_peri['origin_name']} Durağı",
                        "from_coords": {"lat": raw_from_lat, "lon": raw_from_lon},
                        "to_coords": {"lat": raw_to_lat, "lon": raw_to_lon},
                        "route_short_name": local_bus_name,
                        "route_long_name": f"{from_peri['origin_name']} - {to_peri['origin_name']} Yerel Hat",
                        "agency_name": "İETT",
                        "stop_count": max(3, int(straight_km * 1.5)),
                        "intermediate_stops": []
                    },
                    {
                        "step": 3,
                        "mode": "WALK",
                        "duration_minutes": 2,
                        "distance_meters": 150,
                        "from_stop": f"{to_peri['origin_name']} Durağı",
                        "to_stop": "Hedef Konum",
                        "from_coords": {"lat": raw_to_lat, "lon": raw_to_lon},
                        "to_coords": {"lat": raw_to_lat, "lon": raw_to_lon},
                        "route_short_name": "",
                        "route_long_name": "",
                        "agency_name": "",
                        "stop_count": 0,
                        "intermediate_stops": []
                    }
                ]
            }
            return {
                "success": True,
                "count": 1,
                "notice": f"{from_peri['region'].capitalize()} bölgesi yerel ring hattı ({local_bus_name}) ile doğrudan erişim sağlandı.",
                "filters": {
                    "minibus_allowed": allow_minibus,
                    "target": target,
                    "prefer_modes": prefer_modes or [],
                    "avoid_modes": avoid_modes or [],
                    "force_mode": force_mode
                },
                "itineraries": [synth_itinerary]
            }

        # Route via peripheral gateways where applicable
        if from_peri:
            from_lat, from_lon = from_peri["gateway_coords"]
        if to_peri:
            to_lat, to_lon = to_peri["gateway_coords"]

        # Sabiha Gökçen Havalimanı (SAW) Airport Terminal Pinning (Inside OSM road network)
        if 40.8800 <= from_lat <= 40.9400 and from_lon >= 29.2800:
            from_lat, from_lon = 40.908621, 29.284000
        elif from_lon > 29.2846 or (from_lat < 40.9000 and from_lon > 29.2320):
            if from_lat > 41.0000:
                from_lat, from_lon = 41.0280, 29.1750  # Çekmeköy hub
            else:
                from_lat, from_lon = 40.8800, 29.2320  # Tavşantepe / Pendik hub

        if 40.8800 <= to_lat <= 40.9400 and to_lon >= 29.2800:
            to_lat, to_lon = 40.908621, 29.284000
        elif to_lon > 29.2846 or (to_lat < 40.9000 and to_lon > 29.2320):
            if to_lat > 41.0000:
                to_lat, to_lon = 41.0280, 29.1750  # Çekmeköy hub
            else:
                to_lat, to_lon = 40.8800, 29.2320  # Tavşantepe / Pendik hub

        # Latitude boundaries clamping
        if from_lat > 41.2850:
            from_lat = 41.2850
        if to_lat > 41.2850:
            to_lat = 41.2850
        if from_lat < 40.8200:
            from_lat = 40.8200
        if to_lat < 40.8200:
            to_lat = 40.8200

        now = datetime.now()
        if not date_str:
            date_str = now.strftime("%Y-%m-%d")
        if not time_str:
            time_str = now.strftime("%H:%M:00")

        try:
            target_dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M:%S")
            target_epoch_ms = target_dt.timestamp() * 1000.0
        except Exception:
            target_epoch_ms = now.timestamp() * 1000.0

        # Normalize prefer / avoid / force lists
        prefer_list = list(prefer_modes or [])
        if prefer_ferry and "FERRY" not in prefer_list:
            prefer_list.append("FERRY")
        
        avoid_list = list(avoid_modes or [])
        effective_force = force_mode.upper() if force_mode else ("FERRY" if force_ferry else None)

        # Mode weights dictionary
        weights = {
            "FERRY": 1.0,
            "SUBWAY": 1.0,
            "RAIL": 1.0,
            "TRAM": 1.0,
            "BUS": 1.0
        }

        # Optimization targets
        transfer_penalty = 300
        walk_reluctance = 2.2

        target_upper = target.upper()
        if target_upper == "LEAST_TRANSFERS":
            transfer_penalty = 1800
            walk_reluctance = 2.0
        elif target_upper == "LEAST_WALKING":
            walk_reluctance = 6.0
            transfer_penalty = 200
        elif target_upper == "SCENIC_WATER":
            weights["FERRY"] = 0.02
            weights["SUBWAY"] = 1.8
            weights["BUS"] = 2.2

        # Apply preferred modes
        for m in prefer_list:
            mu = m.upper()
            if mu == "FERRY":
                weights["FERRY"] = 0.05
            elif mu in ("SUBWAY", "METRO"):
                weights["SUBWAY"] = 0.08
                weights["RAIL"] = 0.08
                weights["TRAM"] = 0.25
                weights["BUS"] = 1.8
            elif mu == "MARMARAY":
                weights["SUBWAY"] = 0.06
                weights["RAIL"] = 0.06
            elif mu in ("BUS", "METROBUS"):
                weights["BUS"] = 0.15

        # Apply avoided modes
        for m in avoid_list:
            mu = m.upper()
            if mu == "FERRY":
                weights["FERRY"] = 15.0
            elif mu in ("SUBWAY", "METRO"):
                weights["SUBWAY"] = 15.0
                weights["RAIL"] = 15.0
            elif mu in ("BUS", "METROBUS"):
                weights["BUS"] = 15.0

        # Apply forced mode penalization for competing modes
        if effective_force:
            target_mu = effective_force.upper()
            if target_mu not in prefer_list:
                prefer_list.append(target_mu)
            for m in weights:
                if m != target_mu and not (target_mu in ("SUBWAY", "METRO") and m in ("SUBWAY", "RAIL")):
                    weights[m] = 10.0

        weight_clause = f'modeWeight: {{ FERRY: {weights["FERRY"]}, SUBWAY: {weights["SUBWAY"]}, RAIL: {weights["RAIL"]}, TRAM: {weights["TRAM"]}, BUS: {weights["BUS"]} }}'
        arrive_by_clause = "arriveBy: true" if time_type.upper() == "ARRIVE_BY" else ""
        banned_clause = 'banned: { agencies: "1:37,1:19" }' if not allow_minibus else ""
        fetch_count = max(num_itineraries * 8, 36)

        def query_otp_plan(f_lat, f_lon, t_lat, t_lon, d_str, t_str, w_clause=weight_clause, f_count=fetch_count, w_reluctance=walk_reluctance, t_penalty=transfer_penalty):
            q = f"""
            {{
              plan(
                from: {{lat: {f_lat}, lon: {f_lon}}}
                to: {{lat: {t_lat}, lon: {t_lon}}}
                date: "{d_str}"
                time: "{t_str}"
                numItineraries: {f_count}
                searchWindow: 14400
                maxWalkDistance: 2200
                minTransferTime: 300
                boardSlack: 120
                alightSlack: 60
                waitReluctance: 2.0
                walkReluctance: {w_reluctance}
                transferPenalty: {t_penalty}
                {arrive_by_clause}
                {banned_clause}
                {w_clause}
                transportModes: [{{mode: WALK}}, {{mode: TRANSIT}}]
              ) {{
                itineraries {{
                  startTime
                  endTime
                  duration
                  waitingTime
                  walkTime
                  legs {{
                    mode
                    startTime
                    endTime
                    duration
                    distance
                    legGeometry {{ points }}
                    from {{ name lat lon }}
                    to {{ name lat lon }}
                    route {{ shortName longName agency {{ name }} }}
                    intermediatePlaces {{ name lat lon }}
                  }}
                }}
              }}
            }}
            """
            rq = urllib.request.Request(
                OTP_GRAPHQL_URL,
                data=json.dumps({"query": q}).encode("utf-8"),
                headers={"Content-Type": "application/json", "User-Agent": "HybridTransitRouter/2.0"}
            )
            try:
                with urllib.request.urlopen(rq, timeout=12) as rsp:
                    data = json.load(rsp)
                    return (data.get("data") or {}).get("plan", {}).get("itineraries", [])
            except Exception:
                return []

        raw_itineraries = query_otp_plan(from_lat, from_lon, to_lat, to_lon, date_str, time_str)

        # Anti-Walk Degeneration Shield (Handles OSM barriers like Sefaköy)
        is_pure_walk = False
        if raw_itineraries:
            first_legs = raw_itineraries[0].get("legs", [])
            transit_count = sum(1 for l in first_legs if l.get("mode") != "WALK")
            if transit_count == 0 and straight_km >= 2.0:
                is_pure_walk = True

        if (not raw_itineraries or is_pure_walk) and straight_km >= 1.5:
            nearest_from = find_nearest_accessible_stop(raw_from_lat, raw_from_lon, max_dist_m=1200)
            nearest_to = find_nearest_accessible_stop(raw_to_lat, raw_to_lon, max_dist_m=1200)

            if nearest_from and nearest_to:
                shield_itins = query_otp_plan(
                    nearest_from["lat"], nearest_from["lon"],
                    nearest_to["lat"], nearest_to["lon"],
                    date_str, time_str
                )
                valid_shield_itins = [it for it in shield_itins if any(l.get("mode") != "WALK" for l in it.get("legs", []))]
                if valid_shield_itins:
                    walk_from_sec = int(nearest_from["distance_m"] / 1.1)
                    walk_to_sec = int(nearest_to["distance_m"] / 1.1)
                    for sit in valid_shield_itins:
                        pre_walk = {
                            "mode": "WALK",
                            "duration": walk_from_sec,
                            "distance": nearest_from["distance_m"],
                            "legGeometry": {"points": ""},
                            "from": {"name": "Başlangıç Konumu", "lat": raw_from_lat, "lon": raw_from_lon},
                            "to": {"name": nearest_from["name"], "lat": nearest_from["lat"], "lon": nearest_from["lon"]},
                            "route": {},
                            "intermediatePlaces": []
                        }
                        post_walk = {
                            "mode": "WALK",
                            "duration": walk_to_sec,
                            "distance": nearest_to["distance_m"],
                            "legGeometry": {"points": ""},
                            "from": {"name": nearest_to["name"], "lat": nearest_to["lat"], "lon": nearest_to["lon"]},
                            "to": {"name": "Hedef Konum", "lat": raw_to_lat, "lon": raw_to_lon},
                            "route": {},
                            "intermediatePlaces": []
                        }
                        sit["legs"] = [pre_walk] + sit.get("legs", []) + [post_walk]
                        sit["duration"] = sit.get("duration", 0) + walk_from_sec + walk_to_sec
                        sit["walkTime"] = sit.get("walkTime", 0) + walk_from_sec + walk_to_sec
                    raw_itineraries = valid_shield_itins

        # Havaist HVL-7 (Başakşehir) & HVL-3 (Sultangazi) Express Airport Synthesizer
        is_ist_airport = (41.2400 <= from_lat <= 41.2850 and 28.7100 <= from_lon <= 28.7650) or (41.2400 <= to_lat <= 41.2850 and 28.7100 <= to_lon <= 28.7650)
        is_basaksehir = (41.0750 <= from_lat <= 41.1350 and 28.7750 <= from_lon <= 28.8450) or (41.0750 <= to_lat <= 41.1350 and 28.7750 <= to_lon <= 28.8450)
        is_sultangazi = (41.0850 <= from_lat <= 41.1400 and 28.8450 <= from_lon <= 28.9100) or (41.0850 <= to_lat <= 41.1400 and 28.8450 <= to_lon <= 28.9100)

        if is_ist_airport and (is_basaksehir or is_sultangazi):
            hvl_route = "HVL-7" if is_basaksehir else "HVL-3"
            hvl_from_name = "Başakşehir Metrokent" if is_basaksehir else "Sultangazi Cebeci"
            hvl_dur = 1680 if is_basaksehir else 2280
            hvl_dist = 24000 if is_basaksehir else 29000
            hvl_is_departing = 41.2400 <= to_lat <= 41.2850
            hvl_itin = {
                "duration": hvl_dur + 300,
                "walkTime": 300,
                "legs": [
                    {
                        "mode": "WALK",
                        "duration": 300,
                        "distance": 250,
                        "legGeometry": {"points": ""},
                        "from": {"name": "Başlangıç Konumu", "lat": raw_from_lat, "lon": raw_from_lon},
                        "to": {"name": hvl_from_name if hvl_is_departing else "İstanbul Havalimanı Otobüs Peronları", "lat": from_lat, "lon": from_lon},
                        "route": {},
                        "intermediatePlaces": []
                    },
                    {
                        "mode": "BUS",
                        "duration": hvl_dur,
                        "distance": hvl_dist,
                        "legGeometry": {"points": ""},
                        "from": {"name": hvl_from_name if hvl_is_departing else "İstanbul Havalimanı Otobüs Peronları", "lat": from_lat, "lon": from_lon},
                        "to": {"name": "İstanbul Havalimanı Otobüs Peronları" if hvl_is_departing else hvl_from_name, "lat": to_lat, "lon": to_lon},
                        "route": {"shortName": hvl_route, "longName": f"{hvl_from_name} - İstanbul Havalimanı HAVAİST", "agency": {"name": "HAVAİST"}},
                        "intermediatePlaces": []
                    }
                ]
            }
            raw_itineraries = [hvl_itin] + raw_itineraries

        # Attach Peripheral Gateway Connectors (Replaces 0-min teleportation with real 303A, 401, 139A, 130Ş)
        if from_peri:
            for it in raw_itineraries:
                p_leg = {
                    "mode": "BUS",
                    "duration": from_peri["duration_sec"],
                    "distance": from_peri["distance_m"],
                    "legGeometry": {"points": ""},
                    "from": {"name": from_peri["origin_name"], "lat": raw_from_lat, "lon": raw_from_lon},
                    "to": {"name": from_peri["gateway_name"], "lat": from_peri["gateway_coords"][0], "lon": from_peri["gateway_coords"][1]},
                    "route": {"shortName": from_peri["route_short_name"], "longName": from_peri["route_long_name"], "agency": {"name": "İETT"}},
                    "intermediatePlaces": []
                }
                it["legs"] = [p_leg] + it.get("legs", [])
                it["duration"] = it.get("duration", 0) + from_peri["duration_sec"]

        if to_peri:
            for it in raw_itineraries:
                p_leg = {
                    "mode": "BUS",
                    "duration": to_peri["duration_sec"],
                    "distance": to_peri["distance_m"],
                    "legGeometry": {"points": ""},
                    "from": {"name": to_peri["gateway_name"], "lat": to_peri["gateway_coords"][0], "lon": to_peri["gateway_coords"][1]},
                    "to": {"name": to_peri["origin_name"], "lat": raw_to_lat, "lon": raw_to_lon},
                    "route": {"shortName": to_peri["route_short_name"], "longName": to_peri["route_long_name"], "agency": {"name": "İETT"}},
                    "intermediatePlaces": []
                }
                it["legs"] = it.get("legs", []) + [p_leg]
                it["duration"] = it.get("duration", 0) + to_peri["duration_sec"]

        # Multimodal Scenic Waypoint Synthesizer (Via-Routing)
        # When user asks for "SCENIC_WATER" / "Boğaz Yolu" or forced ferry, but direct route is landlocked
        is_scenic_requested = (target_upper == "SCENIC_WATER" or prefer_ferry or force_ferry)
        has_ferry_direct = any(any(leg.get("mode") == "FERRY" for leg in itin.get("legs", [])) for itin in raw_itineraries)

        # Rule 1: Trips under 3.0 km bypass scenic detour to prevent absurd loops on short hops
        scenic_synthesized_itin = None
        if is_scenic_requested and not has_ferry_direct and straight_km >= 3.0:
            scenic_corridors = [
                ("Eminönü - Üsküdar Vapuru", 41.018268, 28.973107, "Eminönü İskelesi", 41.0268, 29.0142, "Üsküdar İskelesi"),
                ("Beşiktaş - Üsküdar Vapuru", 41.0418, 29.0062, "Beşiktaş İskelesi", 41.0268, 29.0142, "Üsküdar İskelesi"),
                ("Eyüpsultan - Üsküdar Haliç Hattı", 41.046555, 28.937347, "Eyüp İskelesi", 41.0268, 29.0142, "Üsküdar İskelesi"),
                ("Karaköy - Kadıköy Vapuru", 41.0223, 28.9778, "Karaköy İskelesi", 40.9912, 29.0225, "Kadıköy İskelesi"),
                ("Kabataş - Kadıköy Vapuru", 41.0360, 28.9935, "Kabataş İskelesi", 40.9912, 29.0225, "Kadıköy İskelesi"),
            ]
            # Pick corridor that minimizes detour distance
            def corridor_dist(c):
                d1 = math.hypot(from_lat - c[1], from_lon - c[2])
                d2 = math.hypot(c[4] - to_lat, c[5] - to_lon)
                return d1 + d2

            sorted_corridors = sorted(scenic_corridors, key=corridor_dist)

            for candidate in sorted_corridors[:2]:
                c_name, p1_lat, p1_lon, p1_name, p2_lat, p2_lon, p2_name = candidate
                p1_itins = query_otp_plan(from_lat, from_lon, p1_lat, p1_lon, date_str, time_str, f_count=1)
                p2_ferry_weight = 'modeWeight: { FERRY: 0.01, SUBWAY: 10.0, RAIL: 10.0, TRAM: 10.0, BUS: 10.0 }'
                p2_itins = query_otp_plan(p1_lat, p1_lon, p2_lat, p2_lon, date_str, time_str, w_clause=p2_ferry_weight, f_count=2)
                p3_itins = query_otp_plan(p2_lat, p2_lon, to_lat, to_lon, date_str, time_str, f_count=1)

                if p1_itins and p2_itins and p3_itins:
                    ferry_itin = next((it for it in p2_itins if any(l.get("mode") == "FERRY" for l in it.get("legs", []))), None)
                    if ferry_itin:
                        merged_legs = list(p1_itins[0].get("legs", [])) + list(ferry_itin.get("legs", [])) + list(p3_itins[0].get("legs", []))
                        merged_duration = p1_itins[0].get("duration", 0) + ferry_itin.get("duration", 0) + p3_itins[0].get("duration", 0)
                        merged_walk = p1_itins[0].get("walkTime", 0) + ferry_itin.get("walkTime", 0) + p3_itins[0].get("walkTime", 0)

                        cand_itin = {
                            "duration": merged_duration,
                            "walkTime": merged_walk,
                            "legs": merged_legs,
                            "is_scenic_detour": True,
                            "scenic_badge": "🌊 Boğaz & Vapur Deneyimi (Özel Manzaralı Rota)",
                            "scenic_description": f"Karasal noktalar arasında yolculuğunuz, isteğiniz doğrultusunda {c_name} ile birleştirildi."
                        }
                        if not scenic_synthesized_itin or cand_itin["duration"] < scenic_synthesized_itin["duration"]:
                            scenic_synthesized_itin = cand_itin

        # Filter or prioritize forced mode
        mode_fallback_notice = None
        if effective_force:
            target_mode = "SUBWAY" if effective_force in ("METRO", "SUBWAY") else effective_force
            matching_itins = [
                itin for itin in raw_itineraries
                if any(leg.get("mode") == target_mode or (target_mode == "SUBWAY" and leg.get("mode") in ("SUBWAY", "RAIL")) for leg in itin.get("legs", []))
            ]
            if matching_itins:
                raw_itineraries = matching_itins
            else:
                mode_fallback_notice = f"Seçtiğiniz saatte ({time_str[:5]}) doğrudan {effective_force} seferi bulunmadığı için en hızlı alternatif toplu taşıma hatları gösterilmektedir."

        if scenic_synthesized_itin:
            raw_itineraries = [scenic_synthesized_itin] + raw_itineraries

        # --- TRAFFIC-FIRST PARETO RANKING ---
        # Evaluate traffic delays across ALL candidate itineraries BEFORE ranking/filtering
        for itin in raw_itineraries:
            legs = itin.get("legs", [])
            total_traffic_delay_sec = 0
            adjusted_legs_info = []
            cumulative_walk_sec = 0.0
            total_transit_dist = 0

            for leg in legs:
                mode = leg.get("mode")
                leg_dur = leg.get("duration", 0)
                leg_dist = int(round(leg.get("distance", 0)))
                from_d = leg.get("from") or {}
                to_d = leg.get("to") or {}
                r_d = leg.get("route") or {}

                s_name = clean_text(r_d.get("shortName"))
                l_name = clean_text(r_d.get("longName"))
                leg_from_lat = from_d.get("lat")
                leg_from_lon = from_d.get("lon")
                leg_to_lat = to_d.get("lat")
                leg_to_lon = to_d.get("lon")

                if mode == "WALK":
                    cumulative_walk_sec += leg_dur
                else:
                    total_transit_dist += leg_dist

                traffic_info = None
                adj_dur = leg_dur
                if mode != "WALK" and leg_from_lat and leg_from_lon and leg_to_lat and leg_to_lon:
                    traffic_info = traffic_engine.evaluate_leg_traffic(
                        mode=mode,
                        route_name=s_name or l_name,
                        start_lat=leg_from_lat,
                        start_lon=leg_from_lon,
                        end_lat=leg_to_lat,
                        end_lon=leg_to_lon,
                        scheduled_sec=leg_dur
                    )
                    adj_dur = traffic_info["adjusted_duration_seconds"]
                    total_traffic_delay_sec += traffic_info["delay_seconds"]

                adjusted_legs_info.append({
                    "traffic_info": traffic_info,
                    "adjusted_duration_sec": adj_dur
                })

            transit_count = sum(1 for leg in legs if leg.get("mode") != "WALK")
            transfers = max(0, transit_count - 1)
            walk_time = itin.get("walkTime", 0)
            real_total_duration = sum(info["adjusted_duration_sec"] for info in adjusted_legs_info) + walk_time

            itin["_precomputed_traffic_delay_sec"] = total_traffic_delay_sec
            itin["_precomputed_legs_info"] = adjusted_legs_info
            itin["_real_total_duration"] = real_total_duration

            # Calculate initial curb wait time (Moovit / Google Maps door-to-door parity)
            start_ms = itin.get("startTime") or target_epoch_ms
            initial_curb_wait_sec = max(0, int((start_ms - target_epoch_ms) / 1000.0))
            itin["_initial_curb_wait_sec"] = initial_curb_wait_sec
            door_to_door_duration = real_total_duration + initial_curb_wait_sec

            # Moovit Single-Seat Ride Bonus (-360s if 0 transfers)
            single_seat_bonus = 360 if transfers == 0 and transit_count > 0 else 0

            # Preferred Mode Bonus:
            # - 1500s bonus for having preferred mode
            # - Additional 500s bonus per preferred transit leg
            mode_pref_bonus = 0
            if prefer_list:
                pref_legs_count = 0
                for leg in legs:
                    m = leg.get("mode")
                    if m != "WALK":
                        if m in prefer_list or (m in ("SUBWAY", "RAIL") and any(p in ("SUBWAY", "METRO", "MARMARAY", "RAIL") for p in prefer_list)):
                            pref_legs_count += 1
                if pref_legs_count > 0:
                    mode_pref_bonus = 1500 + (pref_legs_count * 500)

            # Mode & Vehicle Breakdown:
            # Distinguish Surface Street Buses from Grade-Separated Metrobüs (34x) and Rail (Subway/Tram/Marmaray)
            surface_bus_count = sum(1 for leg in legs if leg.get("mode") == "BUS" and not (leg.get("route", {}).get("shortName") or "").startswith("34"))
            subway_count = sum(1 for leg in legs if leg.get("mode") in ("SUBWAY", "RAIL", "TRAM"))
            metrobus_count = sum(1 for leg in legs if leg.get("mode") == "BUS" and (leg.get("route", {}).get("shortName") or "").startswith("34"))
            rail_count = subway_count + metrobus_count

            # Count consecutive surface bus-to-bus transfers (the highest-risk transfer type in Istanbul)
            transit_legs_seq = [l for l in legs if l.get("mode") != "WALK"]
            surface_bus_transfers = 0
            for i in range(len(transit_legs_seq) - 1):
                l1 = transit_legs_seq[i]
                l2 = transit_legs_seq[i+1]
                is_l1_sbus = l1.get("mode") == "BUS" and not (l1.get("route", {}).get("shortName") or "").startswith("34")
                is_l2_sbus = l2.get("mode") == "BUS" and not (l2.get("route", {}).get("shortName") or "").startswith("34")
                if is_l1_sbus and is_l2_sbus:
                    surface_bus_transfers += 1

            # Bus Fragility Penalty:
            # - Multi-surface bus chaining penalty (+900s per bus above 1)
            # - Surface bus-to-bus transfer penalty (+720s per consecutive bus transfer)
            bus_fragility_penalty = 0
            if surface_bus_count >= 2:
                bus_fragility_penalty = (surface_bus_count - 1) * 900 + (surface_bus_transfers * 720)
            elif surface_bus_count == 1 and surface_bus_transfers > 0:
                bus_fragility_penalty = 400

            rail_backbone_bonus = (subway_count * 600) + (metrobus_count * 350)

            # Realistic Transfer Disutility:
            # In transit economics, each transfer carries a base perceived cost of 720s (12m).
            # Transferring between 2 surface buses adds another 480s (8m).
            transfer_penalty = (transfers * 720) + (surface_bus_transfers * 480)

            if target_upper == "LEAST_TRANSFERS":
                score = (transfers * 12000) + door_to_door_duration + (walk_time * 1.2) - (mode_pref_bonus * 6) + bus_fragility_penalty - rail_backbone_bonus
            elif target_upper == "LEAST_WALKING":
                score = (walk_time * 8.0) + door_to_door_duration + transfer_penalty - mode_pref_bonus + bus_fragility_penalty - rail_backbone_bonus
            else:
                # FASTEST / BALANCED (Moovit standard: true door-to-door arrival time + transfer penalty + walk penalty - direct bonus)
                score = door_to_door_duration + transfer_penalty + (walk_time * 1.8) + bus_fragility_penalty - single_seat_bonus - mode_pref_bonus - rail_backbone_bonus

            if itin.get("is_scenic_detour"):
                score = -1000000.0

            itin["_pareto_score"] = score
            itin["_surface_bus_transfers"] = surface_bus_transfers

        # --- MOOVIT-GRADE GENERALIZED TRANSFER DOMINANCE & PRUNING ---
        filtered_itineraries = []
        direct_itineraries = [it for it in raw_itineraries if sum(1 for l in it.get("legs", []) if l.get("mode") != "WALK") <= 1]

        # Compute minimum door-to-door duration for each transfer count
        min_d2d_by_transfer = {}
        for it in raw_itineraries:
            t_cnt = max(0, sum(1 for l in it.get("legs", []) if l.get("mode") != "WALK") - 1)
            d2d_val = it.get("_real_total_duration", 999999) + it.get("_initial_curb_wait_sec", 0)
            if t_cnt not in min_d2d_by_transfer or d2d_val < min_d2d_by_transfer[t_cnt]:
                min_d2d_by_transfer[t_cnt] = d2d_val

        for itin in raw_itineraries:
            if itin.get("is_scenic_detour"):
                filtered_itineraries.append(itin)
                continue

            legs = itin.get("legs", [])
            transit_legs = [l for l in legs if l.get("mode") != "WALK"]
            num_transit = len(transit_legs)
            transfers_count = max(0, num_transit - 1)

            # Rule 1: Micro-hop detection
            # A micro-hop is a transit leg of <= 650m or <= 160s or <= 1 intermediate stop
            # made as part of a multi-leg journey (e.g. 27T for 1 stop before transferring to 46Ç)
            has_micro_hop = False
            if num_transit > 1:
                for tl in transit_legs:
                    t_dist = tl.get("distance", 0)
                    t_dur = tl.get("duration", 0)
                    t_stops = len(tl.get("intermediatePlaces") or [])
                    if (t_dist < 650 or t_dur < 160) and t_stops <= 1:
                        has_micro_hop = True
                        break

            if has_micro_hop:
                continue

            # Rule 2: Generalized Multi-Criteria Transfer Dominance
            # A route with more transfers is only acceptable if it provides significant, genuine time savings:
            # - Extra surface bus transfer requires >= 12 minutes (720s) door-to-door savings
            # - Extra rail/metrobüs transfer requires >= 8 minutes (480s) door-to-door savings
            # Routes that add transfers to save a trivial 1-5 minutes (spurious micro-optimization) are pruned.
            is_transfer_dominated = False
            itin_d2d = itin.get("_real_total_duration", 0) + itin.get("_initial_curb_wait_sec", 0)
            has_sbus_tr = itin.get("_surface_bus_transfers", 0) > 0

            for fewer_tr in range(transfers_count):
                if fewer_tr in min_d2d_by_transfer:
                    fewer_d2d = min_d2d_by_transfer[fewer_tr]
                    saved_sec = fewer_d2d - itin_d2d
                    extra_transfers = transfers_count - fewer_tr
                    required_savings_sec = extra_transfers * (720 if has_sbus_tr else 480)

                    if saved_sec < required_savings_sec:
                        is_transfer_dominated = True
                        break

            if is_transfer_dominated:
                continue

            # Rule 3: Phantom Bus-to-Bus Transfer Elimination
            # In Istanbul traffic, transfers between two surface buses with < 240s gap fail 80%+ of the time.
            has_phantom_bus_transfer = False
            for leg_idx in range(len(transit_legs) - 1):
                l_curr = transit_legs[leg_idx]
                l_next = transit_legs[leg_idx + 1]
                if l_curr.get("mode") == "BUS" and l_next.get("mode") == "BUS":
                    t_end = l_curr.get("endTime") or 0
                    t_start = l_next.get("startTime") or 0
                    if t_start and t_end and 0 <= (t_start - t_end) < 240000:
                        has_phantom_bus_transfer = True
                        break

            if has_phantom_bus_transfer and (direct_itineraries or any(any(l.get("mode") in ("SUBWAY", "RAIL", "TRAM") for l in other.get("legs", [])) for other in raw_itineraries)):
                continue

            filtered_itineraries.append(itin)

        if filtered_itineraries:
            raw_itineraries = filtered_itineraries

        raw_itineraries.sort(key=lambda it: it.get("_pareto_score", 999999))
        if scenic_synthesized_itin and is_scenic_requested:
            other_itins = [it for it in raw_itineraries if it is not scenic_synthesized_itin]
            raw_itineraries = [scenic_synthesized_itin] + other_itins
        raw_itineraries = raw_itineraries[:36]
        processed_itineraries = []

        for idx, itin in enumerate(raw_itineraries, 1):
            base_duration_min = int(itin.get("duration", 0) // 60)
            walk_time_min = int(itin.get("walkTime", 0) // 60)
            legs = itin.get("legs", [])
            transit_count = sum(1 for leg in legs if leg.get("mode") != "WALK")
            transfers = max(0, transit_count - 1)

            processed_legs = []
            cumulative_walk_seconds = 0.0
            total_transit_distance_meters = 0
            precomputed_info = itin.get("_precomputed_legs_info") or []
            total_traffic_delay_seconds = itin.get("_precomputed_traffic_delay_sec", 0)

            for l_idx, leg in enumerate(legs, 1):
                mode = leg.get("mode")
                leg_duration_sec = leg.get("duration", 0)
                leg_dist_meters = int(round(leg.get("distance", 0)))
                from_data = leg.get("from") or {}
                to_data = leg.get("to") or {}
                route_data = leg.get("route") or {}

                from_name = clean_text(from_data.get("name"))
                to_name = clean_text(to_data.get("name"))
                leg_from_lat = from_data.get("lat")
                leg_from_lon = from_data.get("lon")
                leg_to_lat = to_data.get("lat")
                leg_to_lon = to_data.get("lon")

                short_name = clean_text(route_data.get("shortName"))
                long_name = clean_text(route_data.get("longName"))
                agency_name = clean_text((route_data.get("agency") or {}).get("name"))

                if mode == "WALK":
                    cumulative_walk_seconds += leg_duration_sec
                else:
                    total_transit_distance_meters += leg_dist_meters

                # Use Precomputed Traffic Congestion Info
                if l_idx - 1 < len(precomputed_info):
                    traffic_info = precomputed_info[l_idx - 1]["traffic_info"]
                    adjusted_duration_sec = precomputed_info[l_idx - 1]["adjusted_duration_sec"]
                else:
                    traffic_info = None
                    adjusted_duration_sec = leg_duration_sec

                leg_duration_min = max(1, int(round(adjusted_duration_sec / 60.0)))

                # Intermediate stops
                raw_intermediates = leg.get("intermediatePlaces") or []
                intermediate_stops = []
                for p in raw_intermediates:
                    p_name = clean_text(p.get("name"))
                    if p_name and p.get("lat") and p.get("lon"):
                        intermediate_stops.append({
                            "name": p_name,
                            "lat": p.get("lat"),
                            "lon": p.get("lon")
                        })

                leg_obj = {
                    "step": l_idx,
                    "mode": mode,
                    "duration_minutes": leg_duration_min,
                    "distance_meters": leg_dist_meters,
                    "from_stop": from_name,
                    "to_stop": to_name,
                    "from_coords": {"lat": leg_from_lat, "lon": leg_from_lon},
                    "to_coords": {"lat": leg_to_lat, "lon": leg_to_lon},
                    "route_short_name": short_name,
                    "route_long_name": long_name,
                    "agency_name": agency_name,
                    "stop_count": len(intermediate_stops) + 1 if mode != "WALK" else 0,
                    "intermediate_stops": intermediate_stops,
                    "polyline": (leg.get("legGeometry") or {}).get("points"),
                    "traffic": traffic_info,
                    "realtime": None
                }

                # Real-time enrichment for bus and metrobus legs
                if mode == "BUS" and short_name and leg_from_lat and leg_from_lon:
                    live_buses = iett_client.get_live_buses(short_name)
                    is_metrobus = short_name.startswith("34") and len(short_name) <= 4
                    intercept = eta_engine.find_best_vehicle_intercept(
                        live_buses,
                        stop_lat=leg_from_lat,
                        stop_lon=leg_from_lon,
                        walk_seconds_to_stop=cumulative_walk_seconds,
                        is_metrobus=is_metrobus
                    )

                    if intercept:
                        status = intercept["status"]
                        eta_m = intercept["eta_minutes"]
                        dist_m = intercept["road_distance_meters"]
                        kapino = intercept["kapino"]
                        
                        if status == "CATCHABLE":
                            msg = f"Araç {kapino} ~{dist_m}m mesafede, {eta_m} dk sonra durakta. Rahatça yetişebilirsiniz!"
                        elif status == "RECEDING":
                            msg = f"En yakın araç {kapino} duraktan uzaklaşıyor. Lütfen sonraki seferi bekleyin."
                        else:
                            msg = f"En yakın araç {kapino} ({eta_m} dk sonra) yetişmek için çok yakın. Bir sonraki aracı bekleyin."

                        leg_obj["realtime"] = {
                            "active_buses_count": len(live_buses),
                            "target_vehicle": kapino,
                            "target_vehicle_lat": intercept["lat"],
                            "target_vehicle_lon": intercept["lon"],
                            "eta_minutes": eta_m,
                            "distance_meters": dist_m,
                            "status": status,
                            "message": msg
                        }
                    elif live_buses:
                        leg_obj["realtime"] = {
                            "active_buses_count": len(live_buses),
                            "target_vehicle": None,
                            "status": "MONITORING",
                            "message": f"Hatta {len(live_buses)} aktif araç seferde."
                        }

                processed_legs.append(leg_obj)

            fare_estimate = calculate_fare(processed_legs)
            carbon_saved = calculate_carbon_saved(total_transit_distance_meters)
            traffic_delay_min = int(round(total_traffic_delay_seconds / 60.0))
            curb_wait_sec = itin.get("_initial_curb_wait_sec", 0)
            curb_wait_min = int(round(curb_wait_sec / 60.0))
            journey_duration_min = base_duration_min + traffic_delay_min
            door_to_door_min = journey_duration_min + curb_wait_min

            # Dynamic Scenic Badge Assignment for all itineraries
            scenic_badge = itin.get("scenic_badge")
            scenic_desc = itin.get("scenic_description")
            if not scenic_badge and (target_upper == "SCENIC_WATER" or prefer_ferry or force_ferry):
                ferry_leg = next((l for l in processed_legs if l.get("mode") == "FERRY"), None)
                if ferry_leg:
                    scenic_badge = "🚢 Boğaz & Vapur Keyfi (Şehir Hatları)"
                    scenic_desc = f"{ferry_leg.get('route_short_name') or 'Vapur'} ile eşsiz Boğaz ve deniz manzarası."
                else:
                    coastal_lines = {"BN1", "15", "15F", "15KÇ", "15ŞN", "22", "22RE", "25E", "16D", "4"}
                    coastal_leg = next((l for l in processed_legs if l.get("route_short_name") in coastal_lines), None)
                    if coastal_leg:
                        scenic_badge = f"🌊 Sahil & Boğaz Kıyısı Yolu ({coastal_leg.get('route_short_name')})"
                        scenic_desc = f"{coastal_leg.get('route_short_name')} hattı ile sahil şeridi boyunca panoramik yolculuk."
                    else:
                        bridge_lines = {"34G", "34AS", "34BZ", "34A", "522", "129T", "251", "500T", "121A"}
                        bridge_leg = next((l for l in processed_legs if l.get("route_short_name") in bridge_lines), None)
                        if bridge_leg:
                            scenic_badge = f"🌉 Boğaziçi Köprü Panoraması ({bridge_leg.get('route_short_name')})"
                            scenic_desc = f"{bridge_leg.get('route_short_name')} ile Boğaziçi köprü geçişi ve panoramik İstanbul manzarası."
                        else:
                            t5_leg = next((l for l in processed_legs if l.get("route_short_name") == "T5"), None)
                            if t5_leg:
                                scenic_badge = "🌿 Haliç Kıyısı & Tarihi Yarımada (T5 Tramvayı)"
                                scenic_desc = "T5 Haliç tramvayı ile sahil boyunca tarihi Haliç manzarası."

            processed_itineraries.append({
                "option_id": idx,
                "total_duration_minutes": journey_duration_min,
                "door_to_door_minutes": door_to_door_min,
                "curb_wait_minutes": curb_wait_min,
                "in_vehicle_minutes": max(1, base_duration_min - walk_time_min),
                "traffic_delay_minutes": traffic_delay_min,
                "walk_duration_minutes": walk_time_min,
                "transfers": transfers,
                "fare": fare_estimate,
                "co2_saved_kg": carbon_saved,
                "is_scenic_detour": itin.get("is_scenic_detour", False),
                "scenic_badge": scenic_badge,
                "scenic_description": scenic_desc,
                "legs": processed_legs
            })

        # --- TEMPORAL CLONE DEDUPLICATION & MOOVIT-GRADE CORRIDOR LINE BUNDLING ---
        bundled_itineraries = []
        merged_indices = set()

        # Step 1: Deduplicate identical transit chains (e.g. subsequent departures of the same line sequence)
        chain_seen = set()
        for idx_it, it in enumerate(processed_itineraries):
            t_legs = [l for l in it.get("legs", []) if l.get("mode") != "WALK"]
            if not t_legs:
                continue
            chain_sig = tuple((l.get("mode"), l.get("route_short_name"), l.get("from_stop"), l.get("to_stop")) for l in t_legs)
            if chain_sig in chain_seen:
                merged_indices.add(idx_it)
            else:
                chain_seen.add(chain_sig)

        # Step 2: Corridor line clustering for single transit legs (and shared corridors)
        for i in range(len(processed_itineraries)):
            if i in merged_indices:
                continue
            base_it = processed_itineraries[i]
            base_legs = base_it.get("legs", [])
            base_transit = [l for l in base_legs if l.get("mode") != "WALK"]

            if len(base_transit) == 1:
                b_leg = base_transit[0]
                b_mode = b_leg.get("mode")
                b_fc = b_leg.get("from_coords") or {}
                b_tc = b_leg.get("to_coords") or {}
                b_from_lat, b_from_lon = b_fc.get("lat") or 0.0, b_fc.get("lon") or 0.0
                b_to_lat, b_to_lon = b_tc.get("lat") or 0.0, b_tc.get("lon") or 0.0

                initial_routes = b_leg.get("bundled_routes") or ([b_leg.get("route_short_name")] if b_leg.get("route_short_name") else [])
                bundled_routes = list(initial_routes)

                for j in range(i + 1, len(processed_itineraries)):
                    if j in merged_indices:
                        continue
                    cand_it = processed_itineraries[j]
                    cand_transit = [l for l in cand_it.get("legs", []) if l.get("mode") != "WALK"]
                    if len(cand_transit) == 1:
                        c_leg = cand_transit[0]
                        c_mode = c_leg.get("mode")
                        if c_mode != b_mode:
                            continue
                        c_fc = c_leg.get("from_coords") or {}
                        c_tc = c_leg.get("to_coords") or {}
                        c_from_lat, c_from_lon = c_fc.get("lat") or 0.0, c_fc.get("lon") or 0.0
                        c_to_lat, c_to_lon = c_tc.get("lat") or 0.0, c_tc.get("lon") or 0.0

                        d_from = math.hypot(b_from_lat - c_from_lat, (b_from_lon - c_from_lon) * 0.76) * 111000.0
                        d_to = math.hypot(b_to_lat - c_to_lat, (b_to_lon - c_to_lon) * 0.76) * 111000.0
                        same_from = (b_leg.get("from_stop") == c_leg.get("from_stop")) or d_from < 450.0
                        same_to = (b_leg.get("to_stop") == c_leg.get("to_stop")) or d_to < 450.0

                        if same_from and same_to:
                            cand_routes = c_leg.get("bundled_routes") or ([c_leg.get("route_short_name")] if c_leg.get("route_short_name") else [])
                            for r in cand_routes:
                                if r and r not in bundled_routes:
                                    bundled_routes.append(r)
                            merged_indices.add(j)

                if len(bundled_routes) > 1:
                    b_leg["bundled_routes"] = bundled_routes
                    if len(bundled_routes) <= 3:
                        b_leg["route_short_name"] = " / ".join(bundled_routes)
                    else:
                        b_leg["route_short_name"] = f"{bundled_routes[0]} / {bundled_routes[1]} +{len(bundled_routes)-2}"
                    b_leg["alternative_lines_notice"] = f"Alternatif Hatlar: {', '.join(bundled_routes)} (Ortak Koridor)"
                    b_leg["route_long_name"] = f"Ortak Koridor: {', '.join(bundled_routes)}"

            bundled_itineraries.append(base_it)

        processed_itineraries = bundled_itineraries[:num_itineraries]

        return {
            "success": True,
            "count": len(processed_itineraries),
            "notice": mode_fallback_notice,
            "filters": {
                "minibus_allowed": allow_minibus,
                "target": target,
                "prefer_modes": prefer_list,
                "avoid_modes": avoid_list,
                "force_mode": effective_force
            },
            "itineraries": processed_itineraries
        }

hybrid_router = HybridTransitRouter()
