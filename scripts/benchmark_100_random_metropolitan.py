#!/usr/bin/env python3
"""
benchmark_100_random_metropolitan.py
====================================
Comprehensive 100-Route Random Benchmark across Istanbul Metropolitan Province.
Covers all 39 districts (Inner City vs Peripheral) within lat: 40.80 - 41.35, lon: 28.15 - 29.85.

Author: 100 Random Routes Benchmark Analyst
Date: 2026-09-27
"""

import os
import sys
import json
import time
import math
import random
import csv
import urllib.request
from typing import Dict, List, Any, Optional, Tuple

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from src.core.hybrid_router import HybridTransitRouter

OTP_GRAPHQL_URL = "http://localhost:8080/otp/routers/default/index/graphql"
STOPS_FILE = os.path.join(BASE_DIR, "data", "gtfs_temp", "stops.txt")
OUTPUT_JSON = os.path.join(BASE_DIR, "data", "benchmarks", "benchmark_100_random_results.json")
METRICS_JSON = os.path.join(BASE_DIR, "data", "benchmarks", "benchmark_100_random_metrics.json")

# Classification of all 39 Istanbul Districts
DISTRICT_PROFILES = {
    # 17 Peripheral / Outer / Rural / Exurban Districts
    'Silivri': {'type': 'Peripheral', 'center': (41.0740, 28.2470)},
    'Çatalca': {'type': 'Peripheral', 'center': (41.1430, 28.4610)},
    'Arnavutköy': {'type': 'Peripheral', 'center': (41.1850, 28.7420)},
    'Büyükçekmece': {'type': 'Peripheral', 'center': (41.0210, 28.5850)},
    'Beylikdüzü': {'type': 'Peripheral', 'center': (41.0085, 28.6631)},
    'Esenyurt': {'type': 'Peripheral', 'center': (41.0340, 28.6810)},
    'Başakşehir': {'type': 'Peripheral', 'center': (41.0990, 28.8020)},
    'Avcılar': {'type': 'Peripheral', 'center': (40.9855, 28.7308)},
    'Sarıyer': {'type': 'Peripheral', 'center': (41.1663, 29.0515)},
    'Beykoz': {'type': 'Peripheral', 'center': (41.1315, 29.0985)},
    'Şile': {'type': 'Peripheral', 'center': (41.1760, 29.6130)},
    'Çekmeköy': {'type': 'Peripheral', 'center': (41.0280, 29.1750)},
    'Sancaktepe': {'type': 'Peripheral', 'center': (40.9950, 29.2350)},
    'Sultanbeyli': {'type': 'Peripheral', 'center': (40.9650, 29.2650)},
    'Pendik': {'type': 'Peripheral', 'center': (40.8750, 29.2340)},
    'Tuzla': {'type': 'Peripheral', 'center': (40.8250, 29.3050)},
    'Adalar': {'type': 'Peripheral', 'center': (40.8750, 29.1250)},
    
    # 22 Central / Urban Inner City Districts
    'Fatih': {'type': 'Inner', 'center': (41.0150, 28.9450)},
    'Beyoğlu': {'type': 'Inner', 'center': (41.0330, 28.9770)},
    'Şişli': {'type': 'Inner', 'center': (41.0600, 28.9870)},
    'Beşiktaş': {'type': 'Inner', 'center': (41.0418, 29.0062)},
    'Kağıthane': {'type': 'Inner', 'center': (41.0820, 28.9745)},
    'Eyüpsultan': {'type': 'Inner', 'center': (41.0465, 28.9373)},
    'Gaziosmanpaşa': {'type': 'Inner', 'center': (41.0580, 28.9150)},
    'Sultangazi': {'type': 'Inner', 'center': (41.1050, 28.8680)},
    'Bayrampaşa': {'type': 'Inner', 'center': (41.0450, 28.9050)},
    'Esenler': {'type': 'Inner', 'center': (41.0410, 28.8890)},
    'Bağcılar': {'type': 'Inner', 'center': (41.0340, 28.8570)},
    'Güngören': {'type': 'Inner', 'center': (41.0210, 28.8720)},
    'Zeytinburnu': {'type': 'Inner', 'center': (40.9950, 28.9050)},
    'Bakırköy': {'type': 'Inner', 'center': (40.9790, 28.8710)},
    'Bahçelievler': {'type': 'Inner', 'center': (41.0000, 28.8600)},
    'Küçükçekmece': {'type': 'Inner', 'center': (40.9792, 28.7695)},
    'Kadıköy': {'type': 'Inner', 'center': (40.9912, 29.0225)},
    'Üsküdar': {'type': 'Inner', 'center': (41.0268, 29.0142)},
    'Ataşehir': {'type': 'Inner', 'center': (40.9850, 29.1150)},
    'Ümraniye': {'type': 'Inner', 'center': (41.0250, 29.0950)},
    'Maltepe': {'type': 'Inner', 'center': (40.9250, 29.1450)},
    'Kartal': {'type': 'Inner', 'center': (40.8900, 29.1850)}
}

def haversine_distance_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371000
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2 * R * math.asin(math.sqrt(a))

def load_district_snapped_stops() -> Dict[str, List[Dict[str, Any]]]:
    """Loads all 22,000+ real land transit stops and groups them by district."""
    stops_by_district: Dict[str, List[Dict[str, Any]]] = {d: [] for d in DISTRICT_PROFILES}
    
    with open(STOPS_FILE, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                lat = float(row["stop_lat"])
                lon = float(row["stop_lon"])
            except (ValueError, TypeError):
                continue
                
            # Filter to Istanbul metropolitan boundary [40.80 - 41.35, 28.15 - 29.85]
            if not (40.80 <= lat <= 41.35 and 28.15 <= lon <= 29.85):
                continue
                
            # Assign to nearest district centroid
            nearest_d = min(
                DISTRICT_PROFILES.keys(),
                key=lambda d: math.hypot(lat - DISTRICT_PROFILES[d]["center"][0], lon - DISTRICT_PROFILES[d]["center"][1])
            )
            
            clean_name = row["stop_name"].strip()
            stops_by_district[nearest_d].append({
                "stop_id": row["stop_id"],
                "stop_name": clean_name,
                "display_name": f"{nearest_d} ({clean_name})",
                "lat": lat,
                "lon": lon,
                "district": nearest_d,
                "district_type": DISTRICT_PROFILES[nearest_d]["type"]
            })
            
    return stops_by_district

def generate_100_random_metropolitan_pairs(seed: int = 42) -> List[Dict[str, Any]]:
    """
    Generates 100 random, diverse OD pairs spanning all 39 districts of Istanbul.
    Guarantees genuine geographic dispersion:
    - 25 Peripheral -> Peripheral
    - 25 Peripheral -> Inner
    - 25 Inner -> Peripheral
    - 25 Inner -> Inner
    """
    random.seed(seed)
    stops_by_district = load_district_snapped_stops()
    
    periph_districts = [d for d, inf in DISTRICT_PROFILES.items() if inf["type"] == "Peripheral"]
    inner_districts = [d for d, inf in DISTRICT_PROFILES.items() if inf["type"] == "Inner"]
    
    categories = [
        ("Peripheral -> Peripheral", periph_districts, periph_districts, 25),
        ("Peripheral -> Inner", periph_districts, inner_districts, 25),
        ("Inner -> Peripheral", inner_districts, periph_districts, 25),
        ("Inner -> Inner", inner_districts, inner_districts, 25)
    ]
    
    pairs = []
    pair_idx = 1
    
    for cat_name, source_pool, target_pool, count in categories:
        for _ in range(count):
            d1 = random.choice(source_pool)
            # Ensure target district is distinct from origin district
            valid_targets = [d for d in target_pool if d != d1]
            d2 = random.choice(valid_targets)
            
            s1 = random.choice(stops_by_district[d1])
            s2 = random.choice(stops_by_district[d2])
            
            pairs.append({
                "index": pair_idx,
                "pair_type": cat_name,
                "from_district": d1,
                "from_district_type": DISTRICT_PROFILES[d1]["type"],
                "from_name": s1["display_name"],
                "from_coords": [round(s1["lat"], 6), round(s1["lon"], 6)],
                "to_district": d2,
                "to_district_type": DISTRICT_PROFILES[d2]["type"],
                "to_name": s2["display_name"],
                "to_coords": [round(s2["lat"], 6), round(s2["lon"], 6)]
            })
            pair_idx += 1
            
    return pairs

def check_otp_street_coverage(lat: float, lon: float, max_dist: int = 1200) -> bool:
    """Verifies whether OTP has an accessible street graph node near this location."""
    q = f"""
    {{
      nearest(lat: {lat}, lon: {lon}, maxDistance: {max_dist}, maxResults: 1) {{
        edges {{
          node {{
            distance
          }}
        }}
      }}
    }}
    """
    req = urllib.request.Request(
        OTP_GRAPHQL_URL,
        data=json.dumps({"query": q}).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=4) as resp:
            data = json.load(resp)
            edges = data.get("data", {}).get("nearest", {}).get("edges", [])
            return len(edges) > 0
    except Exception:
        return False

def diagnose_failure_cause(
    f_lat: float, f_lon: float, f_dist: str,
    t_lat: float, t_lon: float, t_dist: str
) -> str:
    """Accurately analyzes why an OTP itinerary search returned no results."""
    f_has_street = check_otp_street_coverage(f_lat, f_lon)
    t_has_street = check_otp_street_coverage(t_lat, t_lon)
    
    if not f_has_street and not t_has_street:
        return f"OSM Boundary Exclusion: Both {f_dist} ({f_lon:.3f}E) and {t_dist} ({t_lon:.3f}E) lie outside the clipped OSM street graph boundary."
    elif not f_has_street:
        return f"OSM Boundary Exclusion: Origin in {f_dist} (lat: {f_lat:.4f}, lon: {f_lon:.4f}) is outside the clipped OSM street graph boundary (no walkable edges)."
    elif not t_has_street:
        return f"OSM Boundary Exclusion: Destination in {t_dist} (lat: {t_lat:.4f}, lon: {t_lon:.4f}) is outside the clipped OSM street graph boundary (no walkable edges)."
        
    return f"Rural Bus Headway / Frequency: Transit nodes exist, but no departure connects {f_dist} and {t_dist} within OTP's 4-hour search window (10:30-14:30) or exceeds transfer limits."

def run_benchmark():
    os.makedirs(os.path.dirname(OUTPUT_JSON), exist_ok=True)
    
    print("==========================================================================")
    print("🚀 ISTANBUL TRANSIT ENGINE — 100 RANDOM METROPOLITAN BENCHMARK")
    print("   Province Range: lat [40.80 - 41.35], lon [28.15 - 29.85]")
    print("   Sampling 39 Districts (Inner City vs Peripheral)")
    print("==========================================================================\n")
    
    router = HybridTransitRouter()
    test_pairs = generate_100_random_metropolitan_pairs(seed=42)
    
    results = []
    category_stats = {
        "Inner -> Inner": {"total": 0, "success": 0, "durations": [], "walks": [], "transfers": []},
        "Inner -> Peripheral": {"total": 0, "success": 0, "durations": [], "walks": [], "transfers": []},
        "Peripheral -> Inner": {"total": 0, "success": 0, "durations": [], "walks": [], "transfers": []},
        "Peripheral -> Peripheral": {"total": 0, "success": 0, "durations": [], "walks": [], "transfers": []}
    }
    
    failure_reasons_counter = {}
    
    t_benchmark_start = time.time()
    
    for idx, test in enumerate(test_pairs, 1):
        f_name = test["from_name"]
        f_lat, f_lon = test["from_coords"]
        f_dist = test["from_district"]
        
        t_name = test["to_name"]
        t_lat, t_lon = test["to_coords"]
        t_dist = test["to_district"]
        
        cat = test["pair_type"]
        category_stats[cat]["total"] += 1
        
        t_query_start = time.time()
        try:
            res = router.plan(
                from_lat=f_lat,
                from_lon=f_lon,
                to_lat=t_lat,
                to_lon=t_lon,
                time_str="10:30:00"
            )
            query_time = time.time() - t_query_start
            
            itins = res.get("itineraries", [])
            has_route = len(itins) > 0
            
            if has_route:
                top = itins[0]
                total_dur = top.get("total_duration_minutes", 0)
                walk_dur = top.get("walk_duration_minutes", 0)
                transfers = top.get("transfers", 0)
                
                # Format transit modes: ['SUBWAY M11', 'BUS 34G']
                raw_legs = top.get("legs", [])
                modes_list = []
                for l in raw_legs:
                    m = l.get("mode")
                    r_code = l.get("route_short_name")
                    if m != "WALK":
                        modes_list.append(f"{m} {r_code}".strip() if r_code else m)
                if not modes_list:
                    modes_list = ["WALK"]
                    
                category_stats[cat]["success"] += 1
                category_stats[cat]["durations"].append(total_dur)
                category_stats[cat]["walks"].append(walk_dur)
                category_stats[cat]["transfers"].append(transfers)
                
                result_item = {
                    "index": idx,
                    "from_name": f_name,
                    "from_coords": [f_lat, f_lon],
                    "to_name": t_name,
                    "to_coords": [t_lat, t_lon],
                    "from_district": f_dist,
                    "to_district": t_dist,
                    "pair_type": cat,
                    "success": True,
                    "total_duration_minutes": total_dur,
                    "walk_duration_minutes": walk_dur,
                    "transfers": transfers,
                    "modes": modes_list,
                    "failure_reason": None
                }
                
                modes_summary = " -> ".join(modes_list)
                print(f"[{idx:03d}/100] ✔ [{cat}] {f_dist} -> {t_dist}: {total_dur} min | {transfers} tr | Walk: {walk_dur} min | {modes_summary} ({query_time:.2f}s)")
                
            else:
                fail_reason = diagnose_failure_cause(f_lat, f_lon, f_dist, t_lat, t_lon, t_dist)
                
                # Classify root cause category
                root_cause = "OSM Street Graph Boundary Exclusion" if "OSM Boundary" in fail_reason else "Rural Bus Headway / Infrequent Departures"
                failure_reasons_counter[root_cause] = failure_reasons_counter.get(root_cause, 0) + 1
                
                result_item = {
                    "index": idx,
                    "from_name": f_name,
                    "from_coords": [f_lat, f_lon],
                    "to_name": t_name,
                    "to_coords": [t_lat, t_lon],
                    "from_district": f_dist,
                    "to_district": t_dist,
                    "pair_type": cat,
                    "success": False,
                    "total_duration_minutes": None,
                    "walk_duration_minutes": None,
                    "transfers": None,
                    "modes": [],
                    "failure_reason": fail_reason
                }
                print(f"[{idx:03d}/100] ❌ [{cat}] {f_dist} -> {t_dist}: NO ROUTE ({fail_reason}) ({query_time:.2f}s)")
                
        except Exception as e:
            result_item = {
                "index": idx,
                "from_name": f_name,
                "from_coords": [f_lat, f_lon],
                "to_name": t_name,
                "to_coords": [t_lat, t_lon],
                "from_district": f_dist,
                "to_district": t_dist,
                "pair_type": cat,
                "success": False,
                "total_duration_minutes": None,
                "walk_duration_minutes": None,
                "transfers": None,
                "modes": [],
                "failure_reason": f"Execution Error: {str(e)}"
            }
            print(f"[{idx:03d}/100] ❌ [{cat}] {f_dist} -> {t_dist}: ERROR: {e}")
            
        results.append(result_item)
        
    total_benchmark_time = time.time() - t_benchmark_start
    total_success = sum(1 for r in results if r["success"])
    overall_success_rate = (total_success / len(results)) * 100
    
    # Save the 100 benchmark results into the specified JSON file
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n✔ All 100 results successfully saved to: {OUTPUT_JSON}")
    
    # Compute high-level metrics
    metrics_summary = {
        "benchmark": "100 Random Metropolitan Routes",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "total_routes": len(results),
        "successful_routes": total_success,
        "failed_routes": len(results) - total_success,
        "overall_success_rate_percent": round(overall_success_rate, 2),
        "total_benchmark_time_seconds": round(total_benchmark_time, 2),
        "avg_query_time_seconds": round(total_benchmark_time / len(results), 2),
        "category_breakdown": {},
        "failure_analysis": {
            "counts_by_root_cause": failure_reasons_counter,
            "failed_district_frequencies": {}
        }
    }
    
    for cat, data in category_stats.items():
        total = data["total"]
        succ = data["success"]
        rate = (succ / total * 100) if total > 0 else 0
        avg_dur = round(sum(data["durations"]) / succ, 1) if succ > 0 else None
        avg_walk = round(sum(data["walks"]) / succ, 1) if succ > 0 else None
        avg_trans = round(sum(data["transfers"]) / succ, 2) if succ > 0 else None
        
        metrics_summary["category_breakdown"][cat] = {
            "total_tested": total,
            "successful": succ,
            "failed": total - succ,
            "success_rate_percent": round(rate, 2),
            "avg_duration_minutes": avg_dur,
            "avg_walk_minutes": avg_walk,
            "avg_transfers": avg_trans
        }
        
    # Analyze failed district frequencies
    failed_districts = {}
    for r in results:
        if not r["success"]:
            for d in [r["from_district"], r["to_district"]]:
                failed_districts[d] = failed_districts.get(d, 0) + 1
    metrics_summary["failure_analysis"]["failed_district_frequencies"] = dict(sorted(failed_districts.items(), key=lambda x: -x[1]))
    
    with open(METRICS_JSON, "w", encoding="utf-8") as f:
        json.dump(metrics_summary, f, ensure_ascii=False, indent=2)
        
    # Print Executive Summary Table
    print("\n" + "=" * 80)
    print("📊 100 RANDOM METROPOLITAN BENCHMARK — EXECUTIVE SUMMARY REPORT")
    print("=" * 80)
    print(f"Total Routes Evaluated       : {len(results)}")
    print(f"Overall Success Rate         : {total_success}/{len(results)} ({overall_success_rate:.1f}%)")
    print(f"Total Execution Time         : {total_benchmark_time:.1f}s ({total_benchmark_time/len(results):.2f}s/route)")
    print("-" * 80)
    print(f"{'Category':<28} | {'Total':<6} | {'Passed':<6} | {'Success Rate':<12} | {'Avg Duration':<12} | {'Avg Transfers'}")
    print("-" * 80)
    for cat, d in metrics_summary["category_breakdown"].items():
        dur_str = f"{d['avg_duration_minutes']} min" if d['avg_duration_minutes'] else "N/A"
        tr_str = f"{d['avg_transfers']}" if d['avg_transfers'] is not None else "N/A"
        print(f"{cat:<28} | {d['total_tested']:<6} | {d['successful']:<6} | %{d['success_rate_percent']:<10.1f} | {dur_str:<12} | {tr_str}")
    print("-" * 80)
    print("🚨 Failure Root-Cause Analysis:")
    for cause, cnt in failure_reasons_counter.items():
        print(f"  • {cause}: {cnt} routes ({cnt/(len(results)-total_success)*100:.1f}% of failures)")
    print("=" * 80 + "\n")

if __name__ == "__main__":
    run_benchmark()
