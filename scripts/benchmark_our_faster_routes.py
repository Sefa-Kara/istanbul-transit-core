#!/usr/bin/env python3
"""
benchmark_our_faster_routes.py
================================================================================
İstanbul Transit Core vs. Moovit Canlı Teşhis & Doğrulama Scripti

Bu script, önceki 100'lük benchmark testinde bizim motorumuzun Moovit'ten
"daha hızlı" çıktığı rotaları ŞU ANKİ GERÇEK SAATTE yeniden sorgular.
Amacı:
1. Şu anki saatte durakta bekleme süresinin (curb wait) rotaya nasıl etki ettiğini,
2. Hızlı görünmemizin gerçek sebebini (Direkt hat mı? Trafik farkı mı? Bekleme süresi mi?),
3. Moovit'in metro/metrobüs tercihine karşılık bizim motorun neden otobüs veya raylı sistem seçtiğini
şeffafça ve adli bir titizlikle ortaya koymaktır.
================================================================================
"""

import sys
import os
import json
import time
import math
import argparse
from datetime import datetime
from pathlib import Path

# Add project root to path
BASE_DIR = str(Path(__file__).resolve().parent.parent)
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from src.core.hybrid_router import hybrid_router

BENCHMARK_FILE = os.path.join(BASE_DIR, "data", "benchmarks", "benchmark_live_3way_100_results.json")
OUTPUT_FILE = os.path.join(BASE_DIR, "data", "benchmarks", "faster_routes_live_audit.json")

def diagnose_reason(our_it, moov_res):
    """
    Analyzes the mathematical and structural difference between our route and Moovit.
    """
    our_lines = [leg.get("route_short_name") or leg.get("mode") for leg in our_it.get("legs", []) if leg.get("mode") != "WALK"]
    moov_lines = moov_res.get("lines", [])
    
    our_tr = our_it.get("transfers", 0)
    moov_tr = max(0, len(moov_lines) - 1)
    
    our_wait = our_it.get("curb_wait_minutes", 0)
    our_traffic = our_it.get("traffic_delay_minutes", 0)
    our_walk = our_it.get("walk_duration_minutes", 0)
    
    has_our_rail = any(l.get("mode") in ("SUBWAY", "RAIL", "TRAM") for l in our_it.get("legs", []))
    has_our_mb = any(l.get("mode") == "BUS" and (l.get("route_short_name") or "").startswith("34") for l in our_it.get("legs", []))
    
    has_moov_rail = any("M" in str(x) or "B1" in str(x) or "T" in str(x) for x in moov_lines)
    has_moov_mb = any("34" in str(x) for x in moov_lines)
    
    reasons = []
    
    # 1. Transfer Difference
    if our_tr < moov_tr:
        reasons.append(f"Daha Az Aktarma (Biz: {our_tr} aktarma vs Moovit: {moov_tr} aktarma - Konforlu Rota)")
    elif our_tr > moov_tr:
        reasons.append(f"Fazladan Aktarma (Biz: {our_tr} aktarma vs Moovit: {moov_tr} aktarma - Dikkat!)")
    else:
        reasons.append(f"Eşit Aktarma Sayısı ({our_tr} aktarma)")
        
    # 2. Mode Strategy
    if (has_our_rail or has_our_mb) and not (has_moov_rail or has_moov_mb):
        reasons.append("Biz Raylı/Metrobüs omurgası kullandık, Moovit karayolu otobüslerine kaldı")
    elif not (has_our_rail or has_our_mb) and (has_moov_rail or has_moov_mb):
        reasons.append("Moovit Raylı/Metrobüs seçti, biz karayolu ekspres otobüsü tercih ettik")
    elif (has_our_rail or has_our_mb) and (has_moov_rail or has_moov_mb):
        reasons.append("İki sistem de Raylı Sistem / Metrobüs omurgasında birleşti")
        
    # 3. Wait / Headway impact
    if our_wait >= 10:
        reasons.append(f"Şu anki saatte durakta {our_wait} dk bekleme süresi var (Seyrek hat)")
    elif our_wait <= 3:
        reasons.append(f"Araç hemen geliyor (Durakta bekleme sadece {our_wait} dk - Sık sefer)")

    return " | ".join(reasons)

def main():
    parser = argparse.ArgumentParser(description="İstanbul Transit Core - Moovit'ten Hızlı Olduğumuz Rotaların Canlı Teşhisi")
    parser.add_argument("--limit", type=int, default=15, help="Test edilecek maksimum rota sayısı (varsayılan: 15, tümü için 0)")
    parser.add_argument("--all", action="store_true", help="54 rotanın tamamını test et")
    args = parser.parse_args()

    if not os.path.exists(BENCHMARK_FILE):
        print(f"❌ HATA: Benchmark dosyası bulunamadı: {BENCHMARK_FILE}")
        sys.exit(1)

    with open(BENCHMARK_FILE, "r", encoding="utf-8") as f:
        all_benchmarks = json.load(f)

    # Filter only routes where our engine was previously faster
    faster_candidates = []
    for item in all_benchmarks:
        our = item.get("our_engine", {})
        moov = item.get("moovit", {})
        if our.get("success") and moov.get("success"):
            if our.get("duration_min", 0) < moov.get("duration_min", 0):
                faster_candidates.append(item)

    total_available = len(faster_candidates)
    limit = total_available if args.all or args.limit == 0 else min(args.limit, total_available)
    selected_items = faster_candidates[:limit]

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print("=" * 90)
    print(f"🚀 İSTANBUL TRANSİT CORE - CANLI ZAMANLI ADLİ TEŞHİS TESTİ")
    print(f"🕒 Test Başlama Saati : {now_str} (Bugünkü gerçek canlı saat ve İETT trafiğiyle)")
    print(f"📊 Toplam Hızlı Rota  : {total_available} rotadan ilk {limit} tanesi test ediliyor")
    print("=" * 90)

    results = []
    still_faster_count = 0
    now_slower_count = 0
    equal_count = 0

    for idx, item in enumerate(selected_items, 1):
        corr = item["corridor"]
        km = item.get("straight_km", 0)
        fc = item["from_coords"]
        tc = item["to_coords"]
        f_lat, f_lon = (fc[0], fc[1]) if isinstance(fc, list) else (fc["lat"], fc["lon"])
        t_lat, t_lon = (tc[0], tc[1]) if isinstance(tc, list) else (tc["lat"], tc["lon"])
        
        moov_res = item.get("moovit", {})
        moov_dur = moov_res.get("duration_min", 0)
        moov_lines = moov_res.get("lines", [])

        # Live query on current clock
        t0 = time.time()
        plan_res = hybrid_router.plan(f_lat, f_lon, t_lat, t_lon, num_itineraries=2)
        elapsed = time.time() - t0

        itins = plan_res.get("itineraries", [])
        if not itins:
            print(f"\n[{idx}/{limit}] ❌ {corr} ({km} km): Rota bulunamadı!")
            continue

        best = itins[0]
        our_d2d = best.get("door_to_door_minutes", 0)
        our_tot = best.get("total_duration_minutes", 0)
        our_wait = best.get("curb_wait_minutes", 0)
        our_in_veh = best.get("in_vehicle_minutes", 0)
        our_walk = best.get("walk_duration_minutes", 0)
        our_traffic = best.get("traffic_delay_minutes", 0)
        our_tr = best.get("transfers", 0)
        our_lines = [leg.get("route_short_name") or leg.get("mode") for leg in best.get("legs", []) if leg.get("mode") != "WALK"]

        delta = our_d2d - moov_dur
        diagnosis = diagnose_reason(best, moov_res)

        status_icon = "🟢" if delta < 0 else ("🔴" if delta > 0 else "⚪")
        if delta < 0:
            still_faster_count += 1
            verdict = f"HÂLÂ DAHA HIZLIYIZ (-{abs(delta)} dk)"
        elif delta > 0:
            now_slower_count += 1
            verdict = f"MOOVIT ŞU AN DAHA HIZLI (+{delta} dk)"
        else:
            equal_count += 1
            verdict = "TAM BAŞA BAŞ (0 dk)"

        print(f"\n[{idx}/{limit}] {status_icon} Koridor: {corr} ({km} km)")
        print(f"     ┌─ 🚗 BİZİM MOTOR (CANLI) : Kapıdan Kapıya {our_d2d} dk | {verdict}")
        print(f"     │  ├─ Net Seyahat Süresi  : {our_in_veh} dk araç içi + {our_walk} dk yürüme")
        print(f"     │  ├─ Durakta Bekleme     : {our_wait} dk (İlk aracın durağa geliş payı)")
        print(f"     │  ├─ Trafik Gecikmesi    : +{our_traffic} dk (Canlı İETT FCD verisi)")
        print(f"     │  ├─ Aktarma Sayısı      : {our_tr} aktarma")
        print(f"     │  └─ Seçilen Hatlar      : {our_lines}")
        print(f"     ├─ 📱 MOOVIT (BENCHMARK)  : {moov_dur} dk ({max(0, len(moov_lines)-1)} aktarma) | Hatlar: {moov_lines}")
        print(f"     └─ 🔍 TEŞHİS VE NEDEN     : {diagnosis}")

        results.append({
            "corridor": corr,
            "straight_km": km,
            "our_door_to_door_min": our_d2d,
            "our_in_vehicle_min": our_in_veh,
            "our_curb_wait_min": our_wait,
            "our_traffic_delay_min": our_traffic,
            "our_transfers": our_tr,
            "our_lines": our_lines,
            "moovit_duration_min": moov_dur,
            "moovit_lines": moov_lines,
            "delta_min": delta,
            "diagnosis": diagnosis
        })

    print("\n" + "=" * 90)
    print("📈 CANLI TEST İSTATİSTİK ÖZETİ")
    print("=" * 90)
    print(f"✔ Toplam Test Edilen Rota : {len(results)}")
    print(f"🟢 Hâlâ Moovit'ten Hızlı   : {still_faster_count} rota")
    print(f"🔴 Bekleme/Trafikle Geride : {now_slower_count} rota")
    print(f"⚪ Tam Eşit (Başa Baş)     : {equal_count} rota")
    
    with open(OUTPUT_FILE, "w", encoding="utf-8") as out_f:
        json.dump(results, out_f, indent=2, ensure_ascii=False)
    print(f"\n💾 Detaylı canlı teşhis raporu kaydedildi: {OUTPUT_FILE}")
    print("=" * 90)

if __name__ == "__main__":
    main()
