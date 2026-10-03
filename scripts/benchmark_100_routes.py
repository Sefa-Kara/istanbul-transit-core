import urllib.request
import json
import time
import os
import sys
from typing import Dict, List, Any

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

OTP_URL = "http://localhost:8080/otp/routers/default/index/graphql"

BENCHMARK_PAIRS = [
    # 1. User's explicit test case
    {"name": "Altınbaş Üniversitesi -> Mecidiyeköy (141M Direct Test)", "from": (41.058309, 28.820361), "to": (41.0667, 28.9936), "must_direct": True, "check_line": "141M"},
    
    # 2. Inland to Inland Scenic Detour Test
    {"name": "Altınbaş Üniversitesi -> Mecidiyeköy (Manzaralı Boğaz/Vapur Testi)", "from": (41.058309, 28.820361), "to": (41.0667, 28.9936), "scenic_test": True},
    
    # 3. Airport Corridors
    {"name": "Mecidiyeköy -> İstanbul Havalimanı (IST)", "from": (41.0667, 28.9936), "to": (41.2583, 28.7428)},
    {"name": "Kadıköy -> İstanbul Havalimanı (IST)", "from": (40.9912, 29.0225), "to": (41.2583, 28.7428)},
    {"name": "Taksim -> İstanbul Havalimanı (IST)", "from": (41.0369, 28.9850), "to": (41.2583, 28.7428)},
    {"name": "Halıcıoğlu -> İstanbul Havalimanı (IST)", "from": (41.0485, 28.9455), "to": (41.2583, 28.7428)},
    
    # 4. Metrobüs Backbone
    {"name": "Beylikdüzü Sondurak -> Söğütlüçeşme", "from": (41.0223, 28.6272), "to": (40.9915, 29.0376)},
    {"name": "Avcılar Merkez -> Mecidiyeköy", "from": (40.9855, 28.7308), "to": (41.0667, 28.9936)},
    {"name": "Sefaköy -> Zincirlikuyu", "from": (40.9955, 28.8078), "to": (41.0682, 29.0118)},
    {"name": "Cevizlibağ -> Altunizade", "from": (41.0165, 28.9168), "to": (41.0285, 29.0495)},
    {"name": "Topkapı -> Uzunçayır", "from": (41.0225, 28.9282), "to": (41.0025, 29.0585)},
    
    # 5. Intercontinental & Ferry Corridors
    {"name": "Eminönü -> Kadıköy (Deniz/Vapur)", "from": (41.018268, 28.973107), "to": (40.9912, 29.0225)},
    {"name": "Beşiktaş -> Üsküdar (Deniz/Vapur)", "from": (41.0418, 29.0062), "to": (41.0268, 29.0142)},
    {"name": "Kabataş -> Kadıköy (Deniz/Vapur)", "from": (41.0360, 28.9935), "to": (40.9912, 29.0225)},
    {"name": "Bostancı -> Beşiktaş", "from": (40.9525, 29.0940), "to": (41.0418, 29.0062)},
    {"name": "Sarıyer -> Beykoz", "from": (41.1663, 29.0515), "to": (41.1315, 29.0985)},
    
    # 6. Marmaray Corridors
    {"name": "Halkalı -> Gebze (Tam Marmaray Aksı)", "from": (40.9980, 28.7720), "to": (40.7985, 29.4320)},
    {"name": "Bakırköy -> Bostancı", "from": (40.9790, 28.8710), "to": (40.9525, 29.0940)},
    {"name": "Yenikapı -> Söğütlüçeşme", "from": (41.0050, 28.9520), "to": (40.9915, 29.0376)},
    {"name": "Zeytinburnu -> Kartal", "from": (41.0052, 28.8955), "to": (40.8900, 29.1850)},
    
    # 7. Metro Trunk Lines (M1, M2, M3, M4, M5, M7, M8, M9)
    {"name": "Hacıosman -> Yenikapı (M2)", "from": (41.1400, 29.0320), "to": (41.0050, 28.9520)},
    {"name": "Mahmutbey -> Yıldız (M7)", "from": (41.0560, 28.8320), "to": (41.0520, 29.0110)},
    {"name": "Kirazlı -> Bakırköy Sahil (M3)", "from": (41.0330, 28.8420), "to": (40.9740, 28.8750)},
    {"name": "Kadıköy -> Sabiha Gökçen Havalimanı (M4)", "from": (40.9912, 29.0225), "to": (40.9050, 29.3140)},
    {"name": "Üsküdar -> Çekmeköy (M5)", "from": (41.0268, 29.0142), "to": (41.0280, 29.1750)},
    {"name": "Bostancı -> Parseller (M8)", "from": (40.9525, 29.0940), "to": (41.0320, 29.1320)},
    {"name": "Ataköy -> İkitelli Sanayi (M9)", "from": (40.9850, 28.8650), "to": (41.0690, 28.7990)},

    # 8. Dense Suburban & Transits across all districts
    {"name": "Sefaköy -> Beşiktaş", "from": (40.9955, 28.8078), "to": (41.0418, 29.0062)},
    {"name": "Esenyurt -> Taksim", "from": (41.0340, 28.6810), "to": (41.0369, 28.9850)},
    {"name": "Başakşehir -> Levent", "from": (41.0990, 28.8020), "to": (41.0760, 29.0130)},
    {"name": "Bağcılar -> Eminönü", "from": (41.0340, 28.8570), "to": (41.0182, 28.9731)},
    {"name": "Güngören -> Maslak", "from": (41.0210, 28.8720), "to": (41.1110, 29.0220)},
    {"name": "Esenler -> Kadıköy", "from": (41.0410, 28.8890), "to": (40.9912, 29.0225)},
    {"name": "Gaziosmanpaşa -> Şişli", "from": (41.0580, 28.9150), "to": (41.0600, 28.9870)},
    {"name": "Sultangazi -> Mecidiyeköy", "from": (41.1050, 28.8680), "to": (41.0667, 28.9936)},
    {"name": "Eyüpsultan -> Üsküdar", "from": (41.0465, 28.9373), "to": (41.0268, 29.0142)},
    {"name": "Kağıthane -> Kadıköy", "from": (41.0820, 28.9745), "to": (40.9912, 29.0225)},
    {"name": "Beyoğlu -> Beykoz", "from": (41.0330, 28.9770), "to": (41.1315, 29.0985)},
    {"name": "Fatih -> Kartal", "from": (41.0150, 28.9450), "to": (40.8900, 29.1850)},
    {"name": "Zeytinburnu -> Ataşehir", "from": (40.9950, 28.9050), "to": (40.9850, 29.1150)},
    {"name": "Bakırköy -> Ümraniye", "from": (40.9790, 28.8710), "to": (41.0250, 29.0950)},
    {"name": "Küçükçekmece -> Maltepe", "from": (40.9792, 28.7695), "to": (40.9250, 29.1450)},
    {"name": "Avcılar -> Pendik", "from": (40.9855, 28.7308), "to": (40.8750, 29.2340)},
    {"name": "Beylikdüzü -> Sarıyer", "from": (41.0085, 28.6631), "to": (41.1663, 29.0515)},
    {"name": "Büyükçekmece -> Taksim", "from": (41.0210, 28.5850), "to": (41.0369, 28.9850)},
    {"name": "Silivri -> Yenikapı", "from": (41.0740, 28.2470), "to": (41.0050, 28.9520)},
    {"name": "Çatalca -> Otogar", "from": (41.1430, 28.4610), "to": (41.0400, 28.8950)},
    {"name": "Arnavutköy -> Gayrettepe", "from": (41.1850, 28.7420), "to": (41.0683, 29.0117)},
    {"name": "Sarıyer -> Kadıköy", "from": (41.1663, 29.0515), "to": (40.9912, 29.0225)},
    {"name": "Beykoz -> Taksim", "from": (41.1315, 29.0985), "to": (41.0369, 28.9850)},
    {"name": "Üsküdar -> Başakşehir", "from": (41.0268, 29.0142), "to": (41.0990, 28.8020)},
    {"name": "Kadıköy -> Beylikdüzü", "from": (40.9912, 29.0225), "to": (41.0085, 28.6631)},
    {"name": "Ataşehir -> Mecidiyeköy", "from": (40.9850, 29.1150), "to": (41.0667, 28.9936)},
    {"name": "Ümraniye -> Levent", "from": (41.0250, 29.0950), "to": (41.0760, 29.0130)},
    {"name": "Çekmeköy -> Beşiktaş", "from": (41.0280, 29.1750), "to": (41.0418, 29.0062)},
    {"name": "Sancaktepe -> Kadıköy", "from": (40.9950, 29.2350), "to": (40.9912, 29.0225)},
    {"name": "Sultanbeyli -> Üsküdar", "from": (40.9650, 29.2650), "to": (41.0268, 29.0142)},
    {"name": "Maltepe -> Beşiktaş", "from": (40.9250, 29.1450), "to": (41.0418, 29.0062)},
    {"name": "Kartal -> Taksim", "from": (40.8900, 29.1850), "to": (41.0369, 28.9850)},
    {"name": "Pendik -> Mecidiyeköy", "from": (40.8750, 29.2340), "to": (41.0667, 28.9936)},
    {"name": "Tuzla -> Kadıköy", "from": (40.8250, 29.3050), "to": (40.9912, 29.0225)},
    {"name": "Tuzla -> Yenikapı", "from": (40.8250, 29.3050), "to": (41.0050, 28.9520)},
    {"name": "Şile -> Üsküdar", "from": (41.1760, 29.6130), "to": (41.0268, 29.0142)},
]

# Generate synthetic diverse coordinate pairs across Istanbul's grid to reach exactly 100 tests
base_lats = [40.96, 40.99, 41.02, 41.05, 41.08, 41.11]
base_lons = [28.65, 28.75, 28.85, 28.95, 29.05, 29.15, 29.25]
pair_idx = 1
for i in range(len(base_lats)):
    for j in range(len(base_lons)):
        if len(BENCHMARK_PAIRS) >= 100:
            break
        f_lat = base_lats[i]
        f_lon = base_lons[j]
        # target another point across the city
        t_lat = base_lats[(i + 3) % len(base_lats)]
        t_lon = base_lons[(j + 4) % len(base_lons)]
        BENCHMARK_PAIRS.append({
            "name": f"Şehirlerarası Grid #{pair_idx} ({f_lat:.2f},{f_lon:.2f} -> {t_lat:.2f},{t_lon:.2f})",
            "from": (f_lat, f_lon),
            "to": (t_lat, t_lon)
        })
        pair_idx += 1

print(f"Toplam {len(BENCHMARK_PAIRS)} test konum çifti hazırlandı.")

def run_benchmark():
    from src.core.hybrid_router import HybridTransitRouter
    router = HybridTransitRouter()
    
    print("\n=======================================================")
    print(f"🚀 100 KONUM ÇİFTİ İSTANBUL TRANSIT BENCHMARK TESTİ")
    print(f"=======================================================\n")
    
    results = []
    success_count = 0
    scenic_success = 0
    direct_141m_passed = False
    
    t_start = time.time()
    
    for idx, test in enumerate(BENCHMARK_PAIRS, 1):
        name = test["name"]
        f_lat, f_lon = test["from"]
        t_lat, t_lon = test["to"]
        is_scenic = test.get("scenic_test", False)
        
        target = "SCENIC_WATER" if is_scenic else "FASTEST"
        prefer_ferry = is_scenic
        
        try:
            res = router.plan(
                from_lat=f_lat, from_lon=f_lon,
                to_lat=t_lat, to_lon=t_lon,
                target=target,
                prefer_ferry=prefer_ferry,
                force_ferry=is_scenic,
                time_str="10:30:00"
            )
            
            itins = res.get("itineraries", [])
            has_route = len(itins) > 0
            
            if has_route:
                success_count += 1
                top_itin = itins[0]
                dur_min = top_itin.get("duration_minutes", 0)
                walk_min = top_itin.get("walk_time_minutes", 0)
                transfers = top_itin.get("transfers", 0)
                modes = list(set(l.get("mode") for l in top_itin.get("legs", [])))
                transit_lines = [l.get("route_short_name") for l in top_itin.get("legs", []) if l.get("mode") != "WALK"]
                
                # Check specific assertions
                notes = []
                if test.get("check_line"):
                    req_line = test["check_line"]
                    if any(req_line in (l or "") for l in transit_lines):
                        notes.append(f"✔ {req_line} doğrudan bulundu!")
                        if "141M" in req_line:
                            direct_141m_passed = True
                    else:
                        notes.append(f"⚠ {req_line} ilk seçenekte yok (hatlar: {transit_lines})")
                        
                if is_scenic:
                    has_ferry = any(l.get("mode") == "FERRY" for l in top_itin.get("legs", []))
                    if has_ferry:
                        notes.append("✔ Manzaralı Vapur Garantilendi!")
                        scenic_success += 1
                    else:
                        notes.append("❌ Vapur bulunamadı")
                
                note_str = f" | {', '.join(notes)}" if notes else ""
                print(f"[{idx:03d}/100] ✔ {name}: {dur_min} dk | {transfers} aktarma | Yürüme: {walk_min} dk | Hatlar: {' -> '.join(transit_lines)}{note_str}")
            else:
                print(f"[{idx:03d}/100] ❌ {name}: Rota bulunamadı!")
                
        except Exception as e:
            print(f"[{idx:03d}/100] ❌ {name}: HATA: {e}")
            
    total_time = time.time() - t_start
    print("\n=======================================================")
    print("📊 100 KONUM ÇİFTİ BENCHMARK SONUÇ RAPORU")
    print("=======================================================")
    print(f"Toplam Test Edilen Konum Çifti : {len(BENCHMARK_PAIRS)}")
    print(f"Başarıyla Rota Üretilenler     : {success_count} / {len(BENCHMARK_PAIRS)} (%{success_count / len(BENCHMARK_PAIRS) * 100:.1f})")
    print(f"Altınbaş -> Mecidiyeköy 141M  : {'✔ BAŞARILI' if direct_141m_passed else '❌ BAŞARISIZ'}")
    print(f"Karasal Manzaralı Vapur Testi : {'✔ BAŞARILI' if scenic_success > 0 else '❌ BAŞARISIZ'}")
    print(f"Toplam Test Süresi            : {total_time:.2f} saniye ({total_time / len(BENCHMARK_PAIRS):.2f}s / test)")
    print("=======================================================\n")

if __name__ == "__main__":
    run_benchmark()
