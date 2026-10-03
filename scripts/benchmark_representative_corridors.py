import sys
import time
import json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.core.hybrid_router import hybrid_router

REPRESENTATIVE_PAIRS = [
    # 1. European Urban Corridors
    {"name": "Kuştepe -> Taksim", "from": (41.0667, 28.9880), "to": (41.0370, 28.9850), "type": "Urban"},
    {"name": "Mecidiyeköy -> Eminönü", "from": (41.0667, 28.9936), "to": (41.0175, 28.9733), "type": "Urban"},
    {"name": "Beşiktaş -> Sarıyer", "from": (41.0422, 29.0067), "to": (41.1663, 29.0500), "type": "Urban"},
    {"name": "Bakırköy -> Aksaray", "from": (40.9780, 28.8720), "to": (41.0102, 28.9500), "type": "Urban"},
    
    # 2. Asian Urban Corridors
    {"name": "Kadıköy -> Bostancı", "from": (40.9904, 29.0253), "to": (40.9525, 29.0945), "type": "Urban"},
    {"name": "Üsküdar -> Ümraniye", "from": (41.0267, 29.0153), "to": (41.0250, 29.0960), "type": "Urban"},
    {"name": "Kadıköy -> Pendik", "from": (40.9904, 29.0253), "to": (40.8785, 29.2330), "type": "Suburban"},
    {"name": "Maltepe -> Kartal", "from": (40.9250, 29.1300), "to": (40.8900, 29.1900), "type": "Suburban"},

    # 3. Intercontinental / Cross-Bosphorus Corridors
    {"name": "Kuştepe -> Sabiha Gökçen (SAW)", "from": (41.0667, 28.9950), "to": (40.9086, 29.3146), "type": "Airport Express"},
    {"name": "Kadıköy -> Mecidiyeköy", "from": (40.9904, 29.0253), "to": (41.0667, 28.9936), "type": "Cross-Bosphorus"},
    {"name": "Üsküdar -> Taksim", "from": (41.0267, 29.0153), "to": (41.0370, 28.9850), "type": "Cross-Bosphorus"},
    {"name": "Beşiktaş -> Kadıköy", "from": (41.0422, 29.0067), "to": (40.9904, 29.0253), "type": "Cross-Bosphorus"},

    # 4. Airport Corridors
    {"name": "İstanbul Havalimanı (IST) -> Halıcıoğlu", "from": (41.2612, 28.7420), "to": (41.0485, 28.9455), "type": "Airport Express"},
    {"name": "İstanbul Havalimanı (IST) -> Kadıköy", "from": (41.2612, 28.7420), "to": (40.9904, 29.0253), "type": "Airport Express"},
    {"name": "Sabiha Gökçen (SAW) -> Kadıköy", "from": (40.9086, 29.3146), "to": (40.9904, 29.0253), "type": "Airport Express"},
    {"name": "Taksim -> İstanbul Havalimanı (IST)", "from": (41.0370, 28.9850), "to": (41.2612, 28.7420), "type": "Airport Express"},

    # 5. Suburban & Rapid Transit Spines
    {"name": "Beylikdüzü -> Mecidiyeköy", "from": (41.0010, 28.6430), "to": (41.0667, 28.9936), "type": "Rapid Transit"},
    {"name": "Başakşehir -> Yenikapı", "from": (41.0950, 28.8050), "to": (41.0055, 28.9505), "type": "Rapid Transit"},
    {"name": "Kartal -> Yenikapı (Marmaray)", "from": (40.8900, 29.1900), "to": (41.0055, 28.9505), "type": "Suburban Rail"},
    {"name": "Halkalı -> Ayrılık Çeşmesi", "from": (41.0180, 28.7660), "to": (41.0001, 29.0303), "type": "Suburban Rail"}
]

def run_benchmark():
    results = []
    print(f"Starting Multi-Corridor Benchmark across {len(REPRESENTATIVE_PAIRS)} pairs...\n")
    
    t0_all = time.time()
    for idx, pair in enumerate(REPRESENTATIVE_PAIRS, 1):
        t0 = time.time()
        res = hybrid_router.plan(
            from_lat=pair["from"][0],
            from_lon=pair["from"][1],
            to_lat=pair["to"][0],
            to_lon=pair["to"][1],
            date_str="2026-09-28",
            time_str="08:30:00",
            num_itineraries=4
        )
        elapsed = round(time.time() - t0, 3)
        itins = res.get("itineraries", [])
        
        has_duplicate = False
        chain_sigs = []
        bundled_lines_found = []
        
        for it in itins:
            t_legs = [l for l in it.get("legs", []) if l.get("mode") != "WALK"]
            sig = tuple((l.get("mode"), l.get("route_short_name"), l.get("from_stop"), l.get("to_stop")) for l in t_legs)
            if sig in chain_sigs:
                has_duplicate = True
            chain_sigs.append(sig)
            
            for l in t_legs:
                if l.get("bundled_routes") and len(l.get("bundled_routes")) > 1:
                    bundled_lines_found.append(l.get("bundled_routes"))
        
        first_opt = itins[0] if itins else {}
        results.append({
            "index": idx,
            "corridor": pair["name"],
            "type": pair["type"],
            "success": len(itins) > 0,
            "itineraries_count": len(itins),
            "has_duplicate_cards": has_duplicate,
            "best_duration_min": first_opt.get("total_duration_minutes"),
            "best_transfers": first_opt.get("transfers"),
            "best_walk_min": first_opt.get("walk_duration_minutes"),
            "bundled_corridors_count": len(bundled_lines_found),
            "sample_bundle": bundled_lines_found[0] if bundled_lines_found else None,
            "latency_seconds": elapsed
        })
        
        status = "✅ PASS" if (len(itins) > 0 and not has_duplicate) else "❌ FAIL"
        b_info = f" | Bundled: {bundled_lines_found[0]}" if bundled_lines_found else ""
        print(f"[{status}] #{idx:02d} {pair['name']:<40} -> {len(itins)} opts, best: {first_opt.get('total_duration_minutes')}m ({elapsed}s){b_info}")
        
    total_time = round(time.time() - t0_all, 2)
    success_rate = (sum(1 for r in results if r["success"] and not r["has_duplicate_cards"]) / len(results)) * 100.0
    
    summary = {
        "benchmark": "Representative Multi-Corridor Benchmark",
        "total_pairs": len(results),
        "success_rate_percent": success_rate,
        "zero_duplicate_rate_percent": 100.0 if not any(r["has_duplicate_cards"] for r in results) else 0.0,
        "total_elapsed_seconds": total_time,
        "avg_latency_seconds": round(total_time / len(results), 3),
        "results": results
    }
    
    out_file = Path("data/benchmarks/representative_corridors_benchmark.json")
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
        
    print(f"\n==========================================")
    print(f"Benchmark Complete in {total_time}s")
    print(f"Success Rate: {success_rate}%")
    print(f"Zero-Duplicate Rate: {summary['zero_duplicate_rate_percent']}%")
    print(f"Saved to: {out_file}")

if __name__ == "__main__":
    run_benchmark()
