import os
import sqlite3
import csv
import urllib.request
import urllib.parse
import ssl
import json
import re
from typing import List, Dict, Any

from src.config import BASE_DIR
STOPS_FILE = os.path.join(BASE_DIR, "data", "gtfs_temp", "stops.txt")
CACHE_FILE = os.path.join(BASE_DIR, "data", "cache", "stop_trip_counts.json")

from src.utils.text_utils import repair_turkish_mojibake

# Major Istanbul Landmarks, Malls, Universities, Airports with pinpoint coordinates
ISTANBUL_POIS = [
    {"name": "İstanbul Havalimanı (IST)", "sub": "Arnavutköy (M11 & Otobüs Hub)", "cat": "airport", "icon": "✈️", "lat": 41.2612, "lon": 28.7420},
    {"name": "Sabiha Gökçen Havalimanı (SAW)", "sub": "Pendik / Kurtköy (M4 & Havabüs)", "cat": "airport", "icon": "✈️", "lat": 40.9086, "lon": 29.2840},
    {"name": "Zeytinburnu Cevizlibağ", "sub": "Zeytinburnu (Metrobüs & T1 Tramvay Hub)", "cat": "transit_hub", "icon": "🚊", "lat": 41.0182, "lon": 28.9145},
    {"name": "Pendik YHT Tren Garı", "sub": "Pendik (YHT Hızlı Tren & Marmaray Garı)", "cat": "rail", "icon": "🚆", "lat": 40.8750, "lon": 29.2340},
    {"name": "Halkalı Tren Garı (YHT & Marmaray)", "sub": "Küçükçekmece (YHT & Marmaray Garı)", "cat": "rail", "icon": "🚆", "lat": 41.0180, "lon": 28.7660},
    {"name": "Söğütlüçeşme YHT & Metrobüs Garı", "sub": "Kadıköy (YHT, Metrobüs & Marmaray Hub)", "cat": "rail", "icon": "🚆", "lat": 40.9915, "lon": 29.0376},
    {"name": "Bostancı YHT & Marmaray Garı", "sub": "Kadıköy / Bostancı (YHT, Marmaray & İskele)", "cat": "rail", "icon": "🚆", "lat": 40.9525, "lon": 29.0940},
    {"name": "Sirkeci Garı & Marmaray", "sub": "Fatih / Sirkeci (Marmaray & T1)", "cat": "rail", "icon": "🚆", "lat": 41.0150, "lon": 28.9770},
    {"name": "Haydarpaşa Garı", "sub": "Kadıköy / Rasimpaşa", "cat": "rail", "icon": "🚆", "lat": 40.9965, "lon": 29.0195},
    {"name": "Bakırköy Tren Garı & Meydan", "sub": "Bakırköy (Marmaray & İDO)", "cat": "rail", "icon": "🚆", "lat": 40.9780, "lon": 28.8720},
    {"name": "Yenikapı Transfer Merkezi", "sub": "Fatih (M1, M2 & Marmaray Hub)", "cat": "transit_hub", "icon": "🚇", "lat": 41.0055, "lon": 28.9505},
    {"name": "Zorlu Center AVM", "sub": "Beşiktaş / Levazım", "cat": "poi", "icon": "🛍️", "lat": 41.0665, "lon": 29.0180},
    {"name": "Cevahir AVM", "sub": "Şişli / Mecidiyeköy", "cat": "poi", "icon": "🛍️", "lat": 41.0601, "lon": 28.9933},
    {"name": "Kanyon AVM", "sub": "Levent / Şişli", "cat": "poi", "icon": "🛍️", "lat": 41.0784, "lon": 29.0112},
    {"name": "Akasya AVM", "sub": "Üsküdar / Acıbadem", "cat": "poi", "icon": "🛍️", "lat": 41.0006, "lon": 29.0539},
    {"name": "Emaar Square Mall", "sub": "Üsküdar / Ünalan", "cat": "poi", "icon": "🛍️", "lat": 41.0028, "lon": 29.0722},
    {"name": "Mall of İstanbul", "sub": "Başakşehir / İkitelli", "cat": "poi", "icon": "🛍️", "lat": 41.0631, "lon": 28.8078},
    {"name": "İstinyePark AVM", "sub": "Sarıyer / Pınar", "cat": "poi", "icon": "🛍️", "lat": 41.1118, "lon": 29.0335},
    {"name": "Vadistanbul AVM", "sub": "Sarıyer / Ayazağa", "cat": "poi", "icon": "🛍️", "lat": 41.1070, "lon": 28.9882},
    {"name": "Kadıköy Boğa Heykeli", "sub": "Kadıköy / Altıyol", "cat": "poi", "icon": "📍", "lat": 40.9908, "lon": 29.0298},
    {"name": "Taksim Meydanı & Gezi Parkı", "sub": "Beyoğlu", "cat": "poi", "icon": "📍", "lat": 41.0370, "lon": 28.9850},
    {"name": "Galata Kulesi", "sub": "Beyoğlu / Bereketzade", "cat": "poi", "icon": "🗼", "lat": 41.0256, "lon": 28.9741},
    {"name": "Sultanahmet Meydanı & Ayasofya", "sub": "Fatih", "cat": "poi", "icon": "🕌", "lat": 41.0086, "lon": 28.9802},
    {"name": "Eminönü Mısır Çarşısı", "sub": "Fatih / Rüstempaşa", "cat": "poi", "icon": "🛍️", "lat": 41.0166, "lon": 28.9706},
    {"name": "Ortaköy Camii & Meydanı", "sub": "Beşiktaş / Mecidiye", "cat": "poi", "icon": "📍", "lat": 41.0474, "lon": 29.0270},
    {"name": "Bebek Parkı & Sahili", "sub": "Beşiktaş / Bebek", "cat": "poi", "icon": "🌊", "lat": 41.0772, "lon": 29.0435},
    {"name": "Moda Sahili", "sub": "Kadıköy / Caferağa", "cat": "poi", "icon": "🌊", "lat": 40.9806, "lon": 29.0251},
    {"name": "Bağdat Caddesi", "sub": "Kadıköy / Suadiye - Şaşkınbakkal", "cat": "poi", "icon": "🛍️", "lat": 40.9632, "lon": 29.0838},
    {"name": "Boğaziçi Üniversitesi", "sub": "Sarıyer / Hisarüstü", "cat": "uni", "icon": "🎓", "lat": 41.0835, "lon": 29.0506},
    {"name": "İstanbul Teknik Üniversitesi (İTÜ Ayazağa)", "sub": "Sarıyer / Maslak", "cat": "uni", "icon": "🎓", "lat": 41.1054, "lon": 29.0234},
    {"name": "Yıldız Teknik Üniversitesi (YTÜ Davutpaşa)", "sub": "Esenler", "cat": "uni", "icon": "🎓", "lat": 41.0255, "lon": 28.8911},
    {"name": "Marmara Üniversitesi (Göztepe Kampüsü)", "sub": "Kadıköy", "cat": "uni", "icon": "🎓", "lat": 40.9856, "lon": 29.0543},
    {"name": "Acıbadem Altunizade Hastanesi", "sub": "Üsküdar / Altunizade", "cat": "hospital", "icon": "🏥", "lat": 41.0215, "lon": 29.0416},
    {"name": "Çam ve Sakura Şehir Hastanesi", "sub": "Başakşehir", "cat": "hospital", "icon": "🏥", "lat": 41.1175, "lon": 28.7885},
]

def normalize_tr(text: str) -> str:
    if not text:
        return ""
    t = text.replace("İ", "i").replace("I", "ı")
    return (
        t.lower()
        .replace("\u0307", "")
        .replace("ı", "i")
        .replace("ğ", "g")
        .replace("ü", "u")
        .replace("ş", "s")
        .replace("ö", "o")
        .replace("ç", "c")
        .strip()
    )

SYNONYM_GROUPS = [
    {"gar", "gari", "istasyon", "istasyonu", "tren", "yht"},
    {"havalimani", "havaalani"},
    {"iskele", "iskelesi", "vapur", "ferry"},
    {"metrobus", "metrobus"}
]

ISTANBUL_DISTRICTS = {
    "adalar", "arnavutkoy", "atasehir", "avcilar", "bagcilar", "bahcelievler",
    "bakirkoy", "basaksehir", "bayrampasa", "besiktas", "beykoz", "beylikduzu",
    "beyoglu", "buyukcekmece", "catalca", "cekmekoy", "esenler", "esenyurt",
    "eyupsultan", "eyup", "fatih", "gaziosmanpasa", "gungoren", "kadikoy",
    "kagithane", "kartal", "kucukcekmece", "maltepe", "pendik", "sancaktepe",
    "sariyer", "silivri", "sultanbeyli", "sultangazi", "sile", "sisli",
    "tuzla", "umraniye", "uskudar", "zeytinburnu"
}

def token_matches_text(tok: str, text: str) -> bool:
    if tok in text:
        return True
    for grp in SYNONYM_GROUPS:
        if tok in grp:
            return any(syn in text for syn in grp)
    return False

def clean_name(text: str) -> str:
    return repair_turkish_mojibake(text)

class SearchEngine:
    def __init__(self):
        self.conn = sqlite3.connect(":memory:", check_same_thread=False)
        self.ssl_ctx = ssl._create_unverified_context()
        self._init_db()

    def close(self):
        if hasattr(self, "conn") and self.conn:
            try:
                self.conn.close()
            except Exception:
                pass
            self.conn = None

    def __del__(self):
        self.close()

    def _init_db(self):
        cur = self.conn.cursor()
        cur.execute("""
            CREATE TABLE stops (
                stop_id TEXT,
                name TEXT,
                name_clean TEXT,
                lat REAL,
                lon REAL,
                type TEXT,
                trip_count INTEGER DEFAULT 0
            )
        """)
        cur.execute("CREATE INDEX idx_stop_name ON stops(name_clean)")
        cur.execute("CREATE INDEX idx_stop_type ON stops(type)")

        trip_counts = {}
        if os.path.exists(CACHE_FILE):
            try:
                with open(CACHE_FILE, "r") as cf:
                    trip_counts = json.load(cf)
            except Exception:
                pass

        if not os.path.exists(STOPS_FILE):
            return

        rows = []
        seen = set()
        with open(STOPS_FILE, "r", encoding="utf-8", errors="replace") as f:
            for r in csv.DictReader(f):
                raw_name = clean_name(r.get("stop_name", ""))
                if not raw_name:
                    continue
                try:
                    lat = float(r.get("stop_lat", 0))
                    lon = float(r.get("stop_lon", 0))
                except (ValueError, TypeError):
                    continue

                sid = r.get("stop_id", "")
                tc = trip_counts.get(sid, 0)

                # Determine rapid transit vs local bus
                n_up = raw_name.upper()
                if sid.startswith("mb_") or "METROB" in n_up:
                    stype = "metrobus"
                    tc = max(tc, 800)
                elif sid.startswith("m11_") or any(w in n_up for w in ["METRO", "M1", "M2", "M3", "M4", "M5", "M6", "M7", "M8", "M9", "M11"]):
                    stype = "metro"
                    tc = max(tc, 600)
                elif any(w in n_up for w in ["MARMARAY", "BANLİYÖ"]):
                    stype = "marmaray"
                    tc = max(tc, 600)
                elif any(w in n_up for w in ["İSKELE", "VAPUR", "ŞH", "DENTUR", "TURYOL", "İDO"]):
                    stype = "ferry"
                    tc = max(tc, 300)
                elif any(w in n_up for w in ["TRAMVAY", "T1", "T3", "T4", "T5"]):
                    stype = "tram"
                    tc = max(tc, 400)
                else:
                    stype = "bus"
                    # Filter ghost/deprecated stops with < 3 trips
                    if trip_counts and tc < 3:
                        continue

                key = (raw_name.upper(), round(lat, 4), round(lon, 4))
                if key in seen:
                    continue
                seen.add(key)

                norm = normalize_tr(raw_name)
                rows.append((sid, raw_name, norm, lat, lon, stype, tc))

        cur.executemany("INSERT INTO stops VALUES (?, ?, ?, ?, ?, ?, ?)", rows)
        self.conn.commit()

    def search(self, query: str, limit: int = 8) -> List[Dict[str, Any]]:
        query = query.strip()
        if not query or len(query) < 2:
            return []

        norm_query = normalize_tr(query)
        tokens = [t for t in norm_query.split() if len(t) >= 2]
        if not tokens:
            tokens = [norm_query]

        venue_keywords = ["avm", "center", "mall", "hastane", "universite", "kampus", "otel", "cafe", "kafe", "restaurant", "meydan", "park", "cami", "drink", "dessert", "bar"]
        is_venue_intent = any(k in norm_query for k in venue_keywords)

        results = []
        seen_keys = set()

        def is_nearby_dup(title, lat, lon, stype):
            base_word = title.split()[0].upper()
            for r in results:
                r_base = r["title"].split()[0].upper()
                dist = ((lat - r["lat"])**2 + (lon - r["lon"])**2)**0.5
                if base_word == r_base and dist < 0.0035: # ~350m
                    if r.get("category") == "metrobus" and stype == "bus":
                        return True
                    if r.get("category") == stype:
                        return True
            return False

        # --- TIER 0: POIs & Major Rail Hubs (Exact / Synonym Match) ---
        for poi in ISTANBUL_POIS:
            norm_poi = normalize_tr(poi["name"] + " " + poi["sub"])
            # Match if all tokens match directly or via synonym
            if all(token_matches_text(t, norm_poi) for t in tokens):
                seen_keys.add(poi["name"])
                results.append({
                    "title": poi["name"],
                    "subtitle": poi["sub"],
                    "category": poi["cat"],
                    "icon": poi["icon"],
                    "lat": poi["lat"],
                    "lon": poi["lon"]
                })
                if len(results) >= (3 if is_venue_intent else 2):
                    break

        # --- TIER 1: Rapid Transit & High-Frequency Stops (Google Maps / Moovit Hierarchy) ---
        cur = self.conn.cursor()

        def build_sql_for_tokens(target_tokens):
            expanded_clauses = []
            params = []
            for t in target_tokens:
                syns = [t]
                for grp in SYNONYM_GROUPS:
                    if t in grp:
                        syns = list(grp)
                        break
                clause = "(" + " OR ".join(["name_clean LIKE ?" for _ in syns]) + ")"
                expanded_clauses.append(clause)
                params.extend([f"%{s}%" for s in syns])
            return " AND ".join(expanded_clauses), params

        sql_conditions, params = build_sql_for_tokens(tokens)

        # Prioritization Formula:
        # Tier 1: Metrobüs, Metro, Marmaray (+100,000)
        # Tier 2: Ferry, Tram (+80,000)
        # Tier 3: Buses (+ trip_count)
        # Match boost: exact prefix (+50,000)
        order_clause = f"""
            (CASE 
                WHEN type IN ('metrobus', 'metro', 'marmaray') THEN 100000
                WHEN type IN ('ferry', 'tram') THEN 80000
                ELSE 10000
            END 
            + CASE WHEN name_clean LIKE ? THEN 50000 ELSE 0 END
            + MIN(trip_count * 2, 20000)
            - LENGTH(name) * 15) DESC
        """
        exec_params = list(params)
        exec_params.append(f"{tokens[0]}%")
        exec_params.append(limit * 3)

        cur.execute(f"""
            SELECT name, lat, lon, type, trip_count FROM stops
            WHERE {sql_conditions}
            ORDER BY {order_clause}
            LIMIT ?
        """, exec_params)
        stop_rows = cur.fetchall()

        # If zero stops found and query contains a district name (e.g. 'Zeytinburnu Cevizlibağ'), retry without district
        if not stop_rows and len(tokens) > 1 and any(t in ISTANBUL_DISTRICTS for t in tokens):
            non_dist_tokens = [t for t in tokens if t not in ISTANBUL_DISTRICTS]
            if non_dist_tokens:
                sql_conditions, params = build_sql_for_tokens(non_dist_tokens)
                exec_params = list(params)
                exec_params.append(f"{non_dist_tokens[0]}%")
                exec_params.append(limit * 3)
                cur.execute(f"""
                    SELECT name, lat, lon, type, trip_count FROM stops
                    WHERE {sql_conditions}
                    ORDER BY {order_clause}
                    LIMIT ?
                """, exec_params)
                stop_rows = cur.fetchall()

        for name, lat, lon, stype, tc in stop_rows:
            if name in seen_keys or is_nearby_dup(name, lat, lon, stype):
                continue
            seen_keys.add(name)

            if stype == "metrobus":
                icon = "🚊"
                badge = f"Metrobüs İstasyonu • 7/24 Aktif"
            elif stype in ["metro", "marmaray"]:
                icon = "🚇"
                badge = f"Metro & Raylı Sistem İstasyonu"
            elif stype == "ferry":
                icon = "🚢"
                badge = f"Şehir Hatları Vapur İskelesi"
            elif stype == "tram":
                icon = "🚊"
                badge = f"Tramvay Hattı"
            else:
                icon = "🚌"
                badge = f"İETT Otobüs Durağı"

            results.append({
                "title": name,
                "subtitle": badge,
                "category": stype,
                "icon": icon,
                "lat": lat,
                "lon": lon
            })
            if len(results) >= limit:
                break

        # --- TIER 2: Curated POIs / Malls / Landmarks (If not already added in Tier 0) ---
        if len(results) < limit:
            for poi in ISTANBUL_POIS:
                norm_poi = normalize_tr(poi["name"] + " " + poi["sub"])
                if all(t in norm_poi for t in tokens) and poi["name"] not in seen_keys:
                    seen_keys.add(poi["name"])
                    results.append({
                        "title": poi["name"],
                        "subtitle": poi["sub"],
                        "category": poi["cat"],
                        "icon": poi["icon"],
                        "lat": poi["lat"],
                        "lon": poi["lon"]
                    })
                    if len(results) >= limit:
                        break

        # --- TIER 3: Precision Geocoder & External Venues (Google Maps Style) ---
        if len(results) < limit:
            try:
                from src.core.geocoder import geocoder
                geo_matches = geocoder.geocode(query, limit=limit - len(results))
                for g in geo_matches:
                    if g["title"] in seen_keys:
                        continue
                    seen_keys.add(g["title"])
                    results.append(g)

                    try:
                        norm = normalize_tr(g["title"])
                        cur.execute("INSERT INTO stops VALUES (?, ?, ?, ?, ?, ?, ?)", (
                            f"poi_{len(seen_keys)}", g["title"], norm, g["lat"], g["lon"], "poi", 100
                        ))
                        self.conn.commit()
                    except Exception:
                        pass

                    if len(results) >= limit:
                        break
            except Exception:
                pass

        return results[:limit]

search_engine = SearchEngine()
