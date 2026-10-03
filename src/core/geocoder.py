import urllib.request
import urllib.parse
import ssl
import json
import re
from typing import Optional, Dict, Any, List

ISTANBUL_BOUNDS = {
    "min_lat": 40.75,
    "max_lat": 41.60,
    "min_lon": 28.00,
    "max_lon": 29.95
}

def is_in_istanbul(lat: float, lon: float) -> bool:
    return (
        ISTANBUL_BOUNDS["min_lat"] <= lat <= ISTANBUL_BOUNDS["max_lat"]
        and ISTANBUL_BOUNDS["min_lon"] <= lon <= ISTANBUL_BOUNDS["max_lon"]
    )

class PrecisionGeocoder:
    """
    Multi-Tiered Istanbul Precision Geocoder at 0 TL cost:
    - Tier 1: DuckDuckGo / Apple Maps POI Search (Resolves small cafes, shops, local businesses)
    - Tier 2: Google Maps Web Inspection (Redirect & Center coordinates extraction)
    - Tier 3: OpenStreetMap Nominatim with Istanbul viewbox bounding
    """

    def __init__(self):
        self.ssl_ctx = ssl._create_unverified_context()
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8"
        }

    def resolve_apple_ddg(self, query: str) -> List[Dict[str, Any]]:
        """Queries DuckDuckGo Local endpoint (backed by Apple Maps POI database)."""
        q = query.strip()
        if "istanbul" not in q.lower():
            q += " istanbul"

        url = f"https://duckduckgo.com/local.js?q={urllib.parse.quote(q)}&cb=ddg&s=0"
        req = urllib.request.Request(url, headers=self.headers)
        results = []

        try:
            with urllib.request.urlopen(req, context=self.ssl_ctx, timeout=4) as resp:
                raw = resp.read().decode("utf-8", errors="replace")

            m = re.search(r"ddg\((.*)\)", raw)
            if not m:
                return []

            data = json.loads(m.group(1))
            items = data.get("results", [])
            for it in items[:4]:
                name = it.get("name", "")
                coords = it.get("coordinates", {})
                lat = coords.get("latitude")
                lon = coords.get("longitude")
                addr = it.get("address", "")

                if lat is not None and lon is not None:
                    lat_f = float(lat)
                    lon_f = float(lon)
                    if is_in_istanbul(lat_f, lon_f):
                        # Determine icon
                        q_low = (name + " " + q).lower()
                        if any(w in q_low for w in ["dessert", "tatlı", "cafe", "kafe", "kahve", "drink", "pasta", "fırın"]):
                            icon = "☕"
                        elif any(w in q_low for w in ["döner", "kebap", "restoran", "lokanta", "köfte", "burger"]):
                            icon = "🍽️"
                        elif any(w in q_low for w in ["eczane", "sağlık", "klinik", "hastane"]):
                            icon = "💊"
                        else:
                            icon = "📍"

                        sub = addr if addr else "İstanbul • Doğrulanmış Mekan"
                        results.append({
                            "title": name,
                            "subtitle": sub,
                            "category": "poi",
                            "icon": icon,
                            "lat": lat_f,
                            "lon": lon_f
                        })
        except Exception:
            pass

        return results

    def resolve_google_maps(self, query: str) -> Optional[Dict[str, Any]]:
        """Queries Google Maps public URL and inspects redirected coordinates."""
        q = query.strip()
        if "istanbul" not in q.lower():
            q += " istanbul"

        url = f"https://www.google.com/maps/search/?api=1&query={urllib.parse.quote(q)}"
        req = urllib.request.Request(url, headers=self.headers)

        try:
            with urllib.request.urlopen(req, context=self.ssl_ctx, timeout=4) as resp:
                final_url = resp.geturl()
                content = resp.read().decode("utf-8", errors="replace")

            # Try extracting @lat,lon from URL
            m = re.search(r"@([0-9]{2}\.[0-9]{4,8}),([0-9]{2}\.[0-9]{4,8})", final_url)
            if m:
                lat, lon = float(m.group(1)), float(m.group(2))
                if is_in_istanbul(lat, lon):
                    return {
                        "title": query.title(),
                        "subtitle": "Google Haritalar • Doğrulanmış Konum",
                        "category": "poi",
                        "icon": "📍",
                        "lat": lat,
                        "lon": lon
                    }

            # Try extracting center=lat%2Clon
            m2 = re.search(r"center=([0-9]{2}\.[0-9]{4,8})%2C([0-9]{2}\.[0-9]{4,8})", content)
            if m2:
                lat, lon = float(m2.group(1)), float(m2.group(2))
                if is_in_istanbul(lat, lon):
                    return {
                        "title": query.title(),
                        "subtitle": "Google Haritalar • Mekan / İşletme",
                        "category": "poi",
                        "icon": "📍",
                        "lat": lat,
                        "lon": lon
                    }
        except Exception:
            pass

        return None

    def resolve_nominatim(self, query: str, limit: int = 4) -> List[Dict[str, Any]]:
        """Queries OpenStreetMap Nominatim strictly bounded to Istanbul viewbox."""
        q = urllib.parse.quote(query.strip())
        url = f"https://nominatim.openstreetmap.org/search?q={q}&format=json&addressdetails=1&countrycodes=tr&bounded=1&viewbox=27.95,40.75,29.95,41.60&limit={limit}"
        headers = dict(self.headers)
        from src.config import USER_AGENT
        headers["User-Agent"] = USER_AGENT
        req = urllib.request.Request(url, headers=headers)
        results = []

        try:
            with urllib.request.urlopen(req, context=self.ssl_ctx, timeout=4) as resp:
                items = json.load(resp)
                for it in items:
                    try:
                        lat = float(it["lat"])
                        lon = float(it["lon"])
                        if not is_in_istanbul(lat, lon):
                            continue
                        disp = it.get("display_name", "")
                        name = it.get("name") or disp.split(",")[0]
                        results.append({
                            "title": name,
                            "subtitle": disp[:55] + "...",
                            "category": "poi",
                            "icon": "📍",
                            "lat": lat,
                            "lon": lon
                        })
                    except (KeyError, ValueError, TypeError):
                        continue
        except Exception:
            pass

        return results

    def geocode(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Cascades through Apple Maps / DDG, Google Maps, and Nominatim."""
        results = []
        seen = set()

        # 1. Apple Maps / DDG Local (Best for commercial businesses and cafes)
        ddg_matches = self.resolve_apple_ddg(query)
        for m in ddg_matches:
            k = (round(m["lat"], 4), round(m["lon"], 4))
            if k not in seen:
                seen.add(k)
                results.append(m)

        # 2. Google Maps redirect (if DDG returned nothing)
        if not results:
            g_match = self.resolve_google_maps(query)
            if g_match:
                k = (round(g_match["lat"], 4), round(g_match["lon"], 4))
                if k not in seen:
                    seen.add(k)
                    results.append(g_match)

        # 3. Nominatim Istanbul Bounded
        if len(results) < limit:
            nom_matches = self.resolve_nominatim(query, limit=limit - len(results))
            for m in nom_matches:
                k = (round(m["lat"], 4), round(m["lon"], 4))
                if k not in seen:
                    seen.add(k)
                    results.append(m)

        return results[:limit]

geocoder = PrecisionGeocoder()
