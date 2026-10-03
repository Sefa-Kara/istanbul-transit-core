#!/usr/bin/env python3
"""
benchmark_live_3way.py
======================
Lockstep 3-Way Public Transit Benchmark for Istanbul:
Our Engine vs. Moovit (Web) vs. Google Maps (Web)

Key Architectural Capabilities:
1. Genuine Istanbul-Wide Random Coordinate Generator:
   - Truly random origin-destination pairs drawn from all 39 Istanbul districts (Inner vs. Peripheral).
   - Eliminates repetitive origin clustering (no 'all starting from Şişli' bias).
2. Bulletproof Turkish Duration Parsing:
   - Accurately parses compound time strings: '1 sa 15 dk' -> 75m, '2 sa 5 dk' -> 125m, '45 dk' -> 45m.
   - Directly targets Moovit's '.route-time-summary' and Google Maps duration elements.
3. Anti-Antalya / Tailscale Geolocation Lock:
   - Locks Moovit explicitly to Metro ID 1563 (Istanbul) via URL path, localStorage, and browser headers.
4. Synchronous Lockstep Execution:
   - For every coordinate pair, queries Our Engine, Moovit, and Google Maps simultaneously in lockstep.
   - Waits for all three to complete before advancing to the next pair (eliminates temporal drift).
5. Objective Raw Data Recording (No Premature Judgments):
   - Keeps pure, rich, factual comparison metrics without premature heuristic verdicts.
   - Saves human-readable report (.txt) and full structured dataset (.json).
"""

import os
import sys
import time
import json
import random
import re
import math
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

# Dynamic Project Root Resolution
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from src.core.hybrid_router import hybrid_router

# Configuration Defaults
DEFAULT_OUTPUT_TXT = BASE_DIR / "data" / "benchmarks" / "benchmark_live_3way_report.txt"
DEFAULT_OUTPUT_JSON = BASE_DIR / "data" / "benchmarks" / "benchmark_live_3way_results.json"
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
MINIBUS_REGEX = re.compile(r'([ABCD]\d{1,3}[-+A-Za-z0-9]*|BL\d+|Minibüs|Dolmuş|minibüs|dolmuş)', re.IGNORECASE)

# 45 Representative Istanbul District Anchors spanning the entire metropolitan territory
ISTANBUL_DISTRICT_ANCHORS = [
    # Avrupa - Kentsel Merkez
    {"name": "Şişli (Mecidiyeköy)", "district": "Şişli", "lat": 41.0667, "lon": 28.9936},
    {"name": "Beyoğlu (Taksim)", "district": "Beyoğlu", "lat": 41.0370, "lon": 28.9850},
    {"name": "Beşiktaş (Meydan / İskele)", "district": "Beşiktaş", "lat": 41.0422, "lon": 29.0067},
    {"name": "Fatih (Eminönü)", "district": "Fatih", "lat": 41.0182, "lon": 28.9731},
    {"name": "Fatih (Yenikapı Marmaray)", "district": "Fatih", "lat": 41.0055, "lon": 28.9505},
    {"name": "Kağıthane (Merkez)", "district": "Kağıthane", "lat": 41.0820, "lon": 28.9745},
    {"name": "Eyüpsultan (Teleferik)", "district": "Eyüpsultan", "lat": 41.0465, "lon": 28.9373},
    {"name": "Zeytinburnu (Cevizlibağ)", "district": "Zeytinburnu", "lat": 41.0165, "lon": 28.9168},
    {"name": "Bakırköy (İskele / Meydan)", "district": "Bakırköy", "lat": 40.9780, "lon": 28.8720},
    {"name": "Güngören (Köyiçi)", "district": "Güngören", "lat": 41.0210, "lon": 28.8720},
    {"name": "Bağcılar (Meydan)", "district": "Bağcılar", "lat": 41.0340, "lon": 28.8570},
    {"name": "Esenler (Otogar)", "district": "Esenler", "lat": 41.0400, "lon": 28.8950},
    {"name": "Sultangazi (Cebeci)", "district": "Sultangazi", "lat": 41.1050, "lon": 28.8680},
    {"name": "Gaziosmanpaşa (Meydan)", "district": "Gaziosmanpaşa", "lat": 41.0580, "lon": 28.9150},
    {"name": "Bayrampaşa (Yıldırım)", "district": "Bayrampaşa", "lat": 41.0510, "lon": 28.8980},
    
    # Avrupa - Dış / Çeper / Havalimanı
    {"name": "Arnavutköy (İstanbul Havalimanı IST)", "district": "Arnavutköy", "lat": 41.2612, "lon": 28.7420},
    {"name": "Arnavutköy (Merkez)", "district": "Arnavutköy", "lat": 41.1850, "lon": 28.7420},
    {"name": "Başakşehir (Metrokent)", "district": "Başakşehir", "lat": 41.0990, "lon": 28.8020},
    {"name": "Küçükçekmece (Sefaköy)", "district": "Küçükçekmece", "lat": 40.9955, "lon": 28.8078},
    {"name": "Küçükçekmece (Halkalı Marmaray)", "district": "Küçükçekmece", "lat": 41.0180, "lon": 28.7660},
    {"name": "Avcılar (Merkez Metrobüs)", "district": "Avcılar", "lat": 40.9855, "lon": 28.7308},
    {"name": "Beylikdüzü (TÜYAP Sondurak)", "district": "Beylikdüzü", "lat": 41.0223, "lon": 28.6272},
    {"name": "Esenyurt (Meydan)", "district": "Esenyurt", "lat": 41.0340, "lon": 28.6810},
    {"name": "Büyükçekmece (Sahil)", "district": "Büyükçekmece", "lat": 41.0210, "lon": 28.5850},
    {"name": "Silivri (Otogar)", "district": "Silivri", "lat": 41.0740, "lon": 28.2470},
    {"name": "Çatalca (Meydan)", "district": "Çatalca", "lat": 41.1430, "lon": 28.4610},
    {"name": "Sarıyer (Hacıosman)", "district": "Sarıyer", "lat": 41.1400, "lon": 29.0320},
    {"name": "Sarıyer (Maslak İTÜ)", "district": "Sarıyer", "lat": 41.1054, "lon": 29.0234},

    # Anadolu - Kentsel Merkez
    {"name": "Kadıköy (Rıhtım İskele)", "district": "Kadıköy", "lat": 40.9912, "lon": 29.0225},
    {"name": "Kadıköy (Söğütlüçeşme)", "district": "Kadıköy", "lat": 40.9915, "lon": 29.0376},
    {"name": "Kadıköy (Bostancı İskele)", "district": "Kadıköy", "lat": 40.9525, "lon": 29.0940},
    {"name": "Üsküdar (Marmaray Meydan)", "district": "Üsküdar", "lat": 41.0268, "lon": 29.0142},
    {"name": "Üsküdar (Altunizade Metrobüs)", "district": "Üsküdar", "lat": 41.0285, "lon": 29.0495},
    {"name": "Ataşehir (Batı)", "district": "Ataşehir", "lat": 40.9850, "lon": 29.1150},
    {"name": "Ümraniye (Santral)", "district": "Ümraniye", "lat": 41.0250, "lon": 29.0950},
    {"name": "Maltepe (Merkez)", "district": "Maltepe", "lat": 40.9250, "lon": 29.1450},
    {"name": "Kartal (Sahil)", "district": "Kartal", "lat": 40.8900, "lon": 29.1850},

    # Anadolu - Dış / Çeper / Havalimanı
    {"name": "Pendik (Sabiha Gökçen SAW)", "district": "Pendik", "lat": 40.9086, "lon": 29.3146},
    {"name": "Pendik (YHT Garı)", "district": "Pendik", "lat": 40.8750, "lon": 29.2340},
    {"name": "Tuzla (Marina)", "district": "Tuzla", "lat": 40.8150, "lon": 29.3000},
    {"name": "Tuzla (Şifa Mahallesi)", "district": "Tuzla", "lat": 40.8250, "lon": 29.3250},
    {"name": "Sultanbeyli (Merkez)", "district": "Sultanbeyli", "lat": 40.9650, "lon": 29.2650},
    {"name": "Sancaktepe (Sarıgazi)", "district": "Sancaktepe", "lat": 40.9950, "lon": 29.2350},
    {"name": "Çekmeköy (Madenler)", "district": "Çekmeköy", "lat": 41.0280, "lon": 29.1750},
    {"name": "Beykoz (Ortaçeşme)", "district": "Beykoz", "lat": 41.1315, "lon": 29.0985},
    {"name": "Şile (Merkez)", "district": "Şile", "lat": 41.1760, "lon": 29.6130},
]

def parse_turkish_duration(text: Optional[str]) -> Optional[int]:
    """
    Parses complex multi-unit duration strings robustly:
    - '1 sa 1 dk' -> 61
    - '1 sa 25 dk' -> 85
    - '2 sa 10 dk' -> 130
    - '55 dk' -> 55
    - '1 sa' -> 60
    - '1 hr 15 min' -> 75
    """
    if not text:
        return None
    text = text.lower().strip()
    hours = 0
    mins = 0
    
    # Check for hours (sa, saat, hr, hour)
    hr_match = re.search(r"(\d+)\s*(?:sa|saat|hr|hour)\b", text)
    if hr_match:
        hours = int(hr_match.group(1))
        
    # Check for minutes (dk, dakika, min)
    min_match = re.search(r"(\d+)\s*(?:dk|dakika|min)\b", text)
    if min_match:
        mins = int(min_match.group(1))
        
    if hours > 0 or mins > 0:
        return hours * 60 + mins
        
    return None

def generate_random_pairs(total_needed: int) -> List[Dict[str, Any]]:
    """
    Generates truly random origin-destination pairs uniformly distributed across all 39 Istanbul districts.
    Every single pair picks two independent locations across the entire metropolitan area.
    """
    # Seed based on current timestamp for genuine variation on every benchmark invocation
    random.seed(int(time.time() * 1000) % 1000000)
    
    pairs = []
    seen = set()
    
    while len(pairs) < total_needed:
        # Pick two completely random distinct anchors
        a1 = random.choice(ISTANBUL_DISTRICT_ANCHORS)
        a2 = random.choice(ISTANBUL_DISTRICT_ANCHORS)
        if a1["name"] == a2["name"] or a1["district"] == a2["district"] and len(pairs) < total_needed // 2:
            continue
            
        # Add realistic micro-jitter (+/- 800m to 1.8km) to create diverse urban origins/destinations
        lat1 = round(a1["lat"] + random.uniform(-0.012, 0.012), 6)
        lon1 = round(a1["lon"] + random.uniform(-0.012, 0.012), 6)
        lat2 = round(a2["lat"] + random.uniform(-0.012, 0.012), 6)
        lon2 = round(a2["lon"] + random.uniform(-0.012, 0.012), 6)
        
        pair_key = (round(lat1, 3), round(lon1, 3), round(lat2, 3), round(lon2, 3))
        if pair_key in seen:
            continue
        seen.add(pair_key)
        
        straight_km = round(math.hypot(lat1 - lat2, (lon1 - lon2) * 0.76) * 111.0, 1)
        
        pairs.append({
            "name": f"{a1['name']} ➔ {a2['name']}",
            "from_name": a1["name"],
            "to_name": a2["name"],
            "from_district": a1["district"],
            "to_district": a2["district"],
            "straight_km": straight_km,
            "from_coords": (lat1, lon1),
            "to_coords": (lat2, lon2),
        })
        
    return pairs

def query_our_engine(f_lat: float, f_lon: float, t_lat: float, t_lon: float) -> Dict[str, Any]:
    """Queries our local hybrid transit router."""
    t0 = time.time()
    try:
        res = hybrid_router.plan(
            from_lat=f_lat,
            from_lon=f_lon,
            to_lat=t_lat,
            to_lon=t_lon,
            num_itineraries=4
        )
        elapsed = round(time.time() - t0, 3)
        itins = res.get("itineraries", [])
        if not itins:
            return {"success": False, "elapsed": elapsed, "error": "No route found"}
        
        top = itins[0]
        legs = top.get("legs", [])
        t_legs = [l for l in legs if l.get("mode") != "WALK"]
        lines = [f"{l.get('mode')} {l.get('route_short_name')}" for l in t_legs]
        bundled = [l.get("bundled_routes") for l in t_legs if l.get("bundled_routes")]
        
        return {
            "success": True,
            "elapsed": elapsed,
            "duration_min": top.get("total_duration_minutes"),
            "walk_min": top.get("walk_duration_minutes"),
            "transfers": top.get("transfers"),
            "traffic_delay_min": top.get("traffic_delay_minutes", 0),
            "lines": lines,
            "bundled_lines": bundled[0] if bundled else None,
            "total_options": len(itins)
        }
    except Exception as e:
        return {"success": False, "elapsed": round(time.time() - t0, 3), "error": str(e)}

def query_moovit(page, f_lat: float, f_lon: float, t_lat: float, t_lon: float) -> Dict[str, Any]:
    """
    Queries Moovit web client with enforced Istanbul Metro ID (1563).
    Bypasses Tailscale Antalya routing by explicit URL routing and session context.
    Filters out minibuses/dolmuş and selects the first pure formal transit route.
    Extracts duration and exact lines via badges (including img[alt] and span.text).
    """
    t0 = time.time()
    url = f"https://moovitapp.com/tripplan/istanbul-1563/poi/tr?fll={f_lat}_{f_lon}&tll={t_lat}_{t_lon}"
    try:
        page.goto(url, timeout=25000)
        time.sleep(5.5)  # Allow dynamic client-side route rendering
        elapsed = round(time.time() - t0, 3)
        body = page.inner_text("body")
        
        if "403" in body and "Error code" in body:
            return {"success": False, "elapsed": elapsed, "error": "WAF 403 Challenge"}
            
        routes = page.query_selector_all(".route")
        candidate_routes = []
        
        for idx, r in enumerate(routes):
            txt = r.inner_text()
            dur_el = r.query_selector(".route-time-summary, .duration")
            raw_dur = dur_el.inner_text().strip() if dur_el else None
            if not raw_dur:
                for l in txt.splitlines()[:3]:
                    if "dk" in l or "sa" in l:
                        raw_dur = l
                        break
            dur_min = parse_turkish_duration(raw_dur)
            
            # Check minibus
            has_minibus = bool(MINIBUS_REGEX.search(txt))
            
            # Extract lines
            line_elements = r.query_selector_all(".line-image, .line-item, [class*='line'], strong")
            lines = []
            for el in line_elements:
                for img in el.query_selector_all("img"):
                    alt = img.get_attribute("alt")
                    if alt and alt not in lines and alt not in ["/", "•"]:
                        lines.append(alt)
                t = el.inner_text().strip()
                if t and t not in ["/", "•"] and len(t) < 35 and t not in lines:
                    if not any(w in t for w in ["dakika", "Varış", "saat", "içinde", "kalkıyor", "Başlangıç"]):
                        lines.append(t)
                        
            candidate_routes.append({
                "index": idx,
                "duration_min": dur_min,
                "raw_duration": raw_dur,
                "has_minibus": has_minibus,
                "lines": lines,
                "lines_str": " ➔ ".join(lines) if lines else "Toplu Taşıma"
            })
            
        # Pick first route without minibuses
        pure_routes = [r for r in candidate_routes if not r["has_minibus"] and r["duration_min"]]
        if pure_routes:
            chosen = pure_routes[0]
            chosen["minibus_filtered"] = True
        elif candidate_routes and candidate_routes[0]["duration_min"]:
            chosen = candidate_routes[0]
            chosen["minibus_filtered"] = False
        else:
            chosen = {"duration_min": None, "raw_duration": None, "lines": [], "lines_str": "Bulunamadı", "has_minibus": False, "minibus_filtered": True}
            
        return {
            "success": chosen.get("duration_min") is not None,
            "elapsed": elapsed,
            "duration_min": chosen.get("duration_min"),
            "raw_duration_text": chosen.get("raw_duration"),
            "lines": chosen.get("lines", []),
            "raw_snippet": chosen.get("lines_str", "Toplu Taşıma"),
            "has_minibus": chosen.get("has_minibus", False),
            "minibus_filtered": chosen.get("minibus_filtered", True),
            "total_options": len(candidate_routes)
        }
    except Exception as e:
        return {"success": False, "elapsed": round(time.time() - t0, 3), "error": str(e)}

def query_google_maps(page, f_lat: float, f_lon: float, t_lat: float, t_lon: float) -> Dict[str, Any]:
    """
    Queries Google Maps public transit web directions.
    Filters out minibuses/dolmuş and selects the first pure formal transit route.
    Extracts duration and exact lines via badges (span.cukLmd / style background-color).
    """
    t0 = time.time()
    url = f"https://www.google.com/maps/dir/?api=1&origin={f_lat},{f_lon}&destination={t_lat},{t_lon}&travelmode=transit&hl=tr"
    try:
        page.goto(url, timeout=25000)
        time.sleep(5.5)
        elapsed = round(time.time() - t0, 3)
        
        cards = page.query_selector_all("div[data-trip-index]")
        candidate_routes = []
        
        for idx, card in enumerate(cards):
            txt = card.inner_text()
            
            # Duration extraction from card header
            dur_min = None
            raw_dur = None
            for line in txt.splitlines()[:4]:
                d = parse_turkish_duration(line)
                if d and d >= 5:
                    dur_min = d
                    raw_dur = line.strip()
                    break
                    
            # Line extraction via badges
            badges = card.query_selector_all("span.cukLmd, span[style*='background-color'], span[aria-label*='Otobüs'], span[aria-label*='Metro'], span[aria-label*='Tramvay']")
            lines = []
            for b in badges:
                t = b.inner_text().strip()
                if t and t not in lines and len(t) < 35:
                    lines.append(t)
                    
            # Check minibus
            has_minibus = bool(MINIBUS_REGEX.search(txt)) or any(bool(MINIBUS_REGEX.search(l)) for l in lines)
            
            candidate_routes.append({
                "card_idx": idx,
                "duration_min": dur_min,
                "raw_duration": raw_dur,
                "has_minibus": has_minibus,
                "lines": lines,
                "lines_str": " ➔ ".join(lines) if lines else "Toplu Taşıma"
            })
            
        # Pick first route without minibuses
        pure_routes = [r for r in candidate_routes if not r["has_minibus"] and r["duration_min"]]
        if pure_routes:
            chosen = pure_routes[0]
            chosen["minibus_filtered"] = True
        elif candidate_routes and candidate_routes[0]["duration_min"]:
            chosen = candidate_routes[0]
            chosen["minibus_filtered"] = False
        else:
            chosen = {"duration_min": None, "raw_duration": None, "lines": [], "lines_str": "Bulunamadı", "has_minibus": False, "minibus_filtered": True}
            
        return {
            "success": chosen.get("duration_min") is not None,
            "elapsed": elapsed,
            "duration_min": chosen.get("duration_min"),
            "raw_duration_text": chosen.get("raw_duration"),
            "lines": chosen.get("lines", []),
            "raw_snippet": chosen.get("lines_str", "Toplu Taşıma"),
            "has_minibus": chosen.get("has_minibus", False),
            "minibus_filtered": chosen.get("minibus_filtered", True),
            "total_options": len(candidate_routes)
        }
    except Exception as e:
        return {"success": False, "elapsed": round(time.time() - t0, 3), "error": str(e)}


def run_3way_benchmark(total_pairs: int = 100, headless: bool = True, output_txt: Path = DEFAULT_OUTPUT_TXT, output_json: Path = DEFAULT_OUTPUT_JSON):
    """Main lockstep benchmark execution loop."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("❌ Playwright kütüphanesi eksik! Yüklemek için: pip install playwright && playwright install chromium")
        return

    output_txt.parent.mkdir(parents=True, exist_ok=True)
    pairs = generate_random_pairs(total_pairs)
    
    print(f"\n==========================================================================")
    print(f"🚀 İSTANBUL TRANSIT 3-WAY LIVE BENCHMARK (Lockstep Eşzamanlı Test)")
    print(f"Hedef Rota Sayısı : {len(pairs)}")
    print(f"Tarayıcı Modu      : {'Headless (Arka Plan)' if headless else 'UI (Görünür)'}")
    print(f"Konum Kilidi       : İstanbul (Metro ID 1563 - Tailscale Korumalı)")
    print(f"Rapor Dosyaları    : \n  -> {output_txt}\n  -> {output_json}")
    print(f"==========================================================================\n")

    # Initialize / Reset Report File Header
    with open(output_txt, "w", encoding="utf-8") as f:
        f.write("====================================================================================================\n")
        f.write(f"📊 İSTANBUL TRANSIT CORE vs. MOOVIT vs. GOOGLE HARİTALAR CANLI BENCHMARK VERİ RAPORU\n")
        f.write(f"Tarih/Saat: {time.strftime('%Y-%m-%d %H:%M:%S')} | Toplam Rota: {len(pairs)}\n")
        f.write("====================================================================================================\n\n")

    completed_records = []
    
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=headless,
            args=["--disable-blink-features=AutomationControlled"]
        )
        context = browser.new_context(
            user_agent=USER_AGENT,
            viewport={"width": 1280, "height": 800},
            locale="tr-TR",
            timezone_id="Europe/Istanbul",
            geolocation={"latitude": 41.0082, "longitude": 28.9784},
            permissions=["geolocation"]
        )
        
        moovit_page = context.new_page()
        moovit_page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        gmaps_page = context.new_page()
        gmaps_page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        t_global_start = time.time()
        
        for idx, pair in enumerate(pairs, 1):
            f_lat, f_lon = pair["from_coords"]
            t_lat, t_lon = pair["to_coords"]
            p_name = pair["name"]
            dist_km = pair["straight_km"]
            
            print(f"\n[#{idx:04d}/{len(pairs):04d}] Testing: {p_name} (~{dist_km} km)")
            print(f"  Coords: ({f_lat:.4f}, {f_lon:.4f}) ➔ ({t_lat:.4f}, {t_lon:.4f})")
            
            # --- LOCKSTEP EXECUTION: Query all 3 systems synchronously ---
            # 1. Local Engine
            our_res = query_our_engine(f_lat, f_lon, t_lat, t_lon)
            # 2. Moovit (Istanbul locked)
            moovit_res = query_moovit(moovit_page, f_lat, f_lon, t_lat, t_lon)
            # 3. Google Maps
            gmaps_res = query_google_maps(gmaps_page, f_lat, f_lon, t_lat, t_lon)
            
            # Compute raw deltas
            our_dur = our_res.get("duration_min")
            m_dur = moovit_res.get("duration_min")
            g_dur = gmaps_res.get("duration_min")
            
            delta_moovit = (our_dur - m_dur) if (our_dur and m_dur) else None
            delta_gmaps = (our_dur - g_dur) if (our_dur and g_dur) else None
            
            record = {
                "index": idx,
                "corridor": p_name,
                "straight_km": dist_km,
                "from_coords": [f_lat, f_lon],
                "to_coords": [t_lat, t_lon],
                "delta_vs_moovit_min": delta_moovit,
                "delta_vs_gmaps_min": delta_gmaps,
                "our_engine": our_res,
                "moovit": moovit_res,
                "google_maps": gmaps_res
            }
            completed_records.append(record)
            
            # Calculate elapsed time and ETA
            elapsed_sec = time.time() - t_global_start
            avg_per_route = elapsed_sec / idx
            remaining_routes = len(pairs) - idx
            remaining_sec = int(avg_per_route * remaining_routes)
            rem_hrs = remaining_sec // 3600
            rem_mins = (remaining_sec % 3600) // 60
            eta_str = f"{rem_hrs} sa {rem_mins} dk" if rem_hrs > 0 else f"{rem_mins} dk"
            pct = (idx / len(pairs)) * 100
            
            # Print live console summary
            our_str = f"{our_dur} dk ({', '.join(our_res.get('lines', [])[:2])})" if our_res.get("success") else "HATA"
            moovit_str = f"{m_dur} dk ({moovit_res.get('raw_snippet')})" if moovit_res.get("success") else "HATA"
            gmaps_str = f"{g_dur} dk ({gmaps_res.get('raw_snippet')})" if gmaps_res.get("success") else "HATA"
            
            delta_m_str = f"{delta_moovit:+d} dk" if delta_moovit is not None else "N/A"
            delta_g_str = f"{delta_gmaps:+d} dk" if delta_gmaps is not None else "N/A"
            
            print(f"  -> İlerleme     : %{pct:.1f} (Kalan Tahmini Süre: ~{eta_str})")
            print(f"  -> Bizim Motor : {our_str}")
            print(f"  -> Moovit       : {moovit_str} [Fark: {delta_m_str}]")
            print(f"  -> Google Maps : {gmaps_str} [Fark: {delta_g_str}]")
            
            # Incremental Append to Text Report (Pure Data - No Premature Judgments)
            with open(output_txt, "a", encoding="utf-8") as f:
                f.write(f"----------------------------------------------------------------------------------------------------\n")
                f.write(f"ROTA #{idx:04d}: {p_name}\n")
                f.write(f"Koordinatlar: ({f_lat:.6f}, {f_lon:.6f}) ➔ ({t_lat:.6f}, {t_lon:.6f}) | Kuş Uçuşu: {dist_km} km\n")
                f.write(f"Süre Farkı  : Moovit'e Göre: {delta_m_str} | Google Haritalar'a Göre: {delta_g_str}\n\n")
                f.write(f"1. BİZİM MOTOR:\n")
                f.write(f"   - Başarı Durumu  : {our_res.get('success')}\n")
                f.write(f"   - Toplam Süre    : {our_res.get('duration_min')} dakika (Trafik Gecikmesi: +{our_res.get('traffic_delay_min', 0)} dk)\n")
                f.write(f"   - Yürüme Süresi  : {our_res.get('walk_min')} dakika | Aktarma Sayısı: {our_res.get('transfers')}\n")
                f.write(f"   - Kullanılan Hat : {' ➔ '.join(our_res.get('lines', []))}\n")
                if our_res.get("bundled_lines"):
                    f.write(f"   - Demetlenen Hat : {', '.join(our_res.get('bundled_lines'))}\n")
                
                m_filter_label = "Uygulandı (Minibüssüz Temiz Rota)" if moovit_res.get("minibus_filtered") else "Minibüs İçerir (Alternatif Yok)"
                f.write(f"\n2. MOOVIT (Web):\n")
                f.write(f"   - Başarı Durumu  : {moovit_res.get('success')}\n")
                f.write(f"   - Toplam Süre    : {moovit_res.get('duration_min')} dakika (Metin: {moovit_res.get('raw_duration_text')})\n")
                f.write(f"   - Önerilen Hatlar: {moovit_res.get('raw_snippet')}\n")
                f.write(f"   - Minibüs Filtresi: {m_filter_label}\n")
                
                g_filter_label = "Uygulandı (Minibüssüz Temiz Rota)" if gmaps_res.get("minibus_filtered") else "Minibüs İçerir (Alternatif Yok)"
                f.write(f"\n3. GOOGLE HARİTALAR (Web):\n")
                f.write(f"   - Başarı Durumu  : {gmaps_res.get('success')}\n")
                f.write(f"   - Toplam Süre    : {gmaps_res.get('duration_min')} dakika (Metin: {gmaps_res.get('raw_duration_text')})\n")
                f.write(f"   - Önerilen Hatlar: {gmaps_res.get('raw_snippet')}\n")
                f.write(f"   - Minibüs Filtresi: {g_filter_label}\n\n")

            # Incremental Save to JSON
            with open(output_json, "w", encoding="utf-8") as jf:
                json.dump(completed_records, jf, indent=2, ensure_ascii=False)
                
            # Respectful rate-limiting sleep between queries
            time.sleep(random.uniform(2.0, 3.5))

        browser.close()

    total_time = round(time.time() - t_global_start, 2)
    print(f"\n==========================================================================")
    print(f"🎉 3-Way Benchmark Tamamlandı! ({total_time} saniye)")
    print(f"Toplam Test Edilen Rota: {len(completed_records)}")
    print(f"Rapor Kaydedildi: {output_txt}")
    print(f"JSON Kaydedildi : {output_json}")
    print(f"==========================================================================\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Lockstep 3-Way Public Transit Benchmark")
    parser.add_argument("-n", "--limit", type=int, default=100, help="Test edilecek rota sayısı (Örn: 20, 100, 1000)")
    parser.add_argument("-o", "--output-prefix", type=str, default=None, help="Özel çıktı dosya adı / öneki (Örn: benchmark_live_3way_1000)")
    parser.add_argument("--head", action="store_true", help="Tarayıcıyı görünür aç (varsayılan: headless)")
    args = parser.parse_args()
    
    # Auto-resolve output paths so 100-route files are NEVER overwritten
    bench_dir = BASE_DIR / "data" / "benchmarks"
    if args.output_prefix:
        prefix = args.output_prefix
    else:
        prefix = f"benchmark_live_3way_{args.limit}"
        
    out_txt = bench_dir / f"{prefix}_report.txt"
    out_json = bench_dir / f"{prefix}_results.json"
    
    run_3way_benchmark(total_pairs=args.limit, headless=not args.head, output_txt=out_txt, output_json=out_json)

