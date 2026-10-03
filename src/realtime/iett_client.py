import urllib.request
import ssl
import json
import re
import time
from typing import List, Dict, Optional

SOAP_URL = "https://api.ibb.gov.tr/iett/FiloDurum/SeferGerceklesme.asmx"
CACHE_TTL_SECONDS = 8 # Live bus locations are updated every ~10-15s

def is_valid_bus_query(line_code: str) -> bool:
    if not line_code:
        return False
    lc = line_code.strip().upper()
    if lc in ("WALK", "FERRY", "TRANSIT", "MARMARAY") or "MARMARAY" in lc:
        return False
    # Rail lines: M1, M1A, M1B, M2..M11, T1..T5, F1..F4
    if re.match(r"^[MTF]\d+[A-Z]?$", lc):
        return False
    return True

class IETTRealtimeClient:
    def __init__(self):
        self._cache: Dict[str, Dict] = {}

    def get_live_buses(self, line_code: str) -> List[Dict]:
        """
        Fetches live vehicle locations for a given bus or metrobus line (e.g. 129T, 500T, 34AS).
        Returns a list of dicts with:
        - kapino: Vehicle door/fleet ID (e.g. 'A-1546', 'M4625')
        - lat: float latitude
        - lon: float longitude
        - line_code: str
        - route_code: str
        - direction: str (headsign direction)
        - nearest_stop_code: str
        - timestamp: str
        - age_seconds: int
        """
        if not is_valid_bus_query(line_code):
            return []

        norm_code = line_code.strip().upper()
        now = time.time()

        # Check cache
        if norm_code in self._cache:
            entry = self._cache[norm_code]
            if now - entry["timestamp"] < CACHE_TTL_SECONDS:
                return entry["data"]

        soap_body = f"""<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
  <soap:Body>
    <GetHatOtoKonum_json xmlns="http://tempuri.org/">
      <HatKodu>{norm_code}</HatKodu>
    </GetHatOtoKonum_json>
  </soap:Body>
</soap:Envelope>"""

        req = urllib.request.Request(
            SOAP_URL,
            data=soap_body.encode("utf-8"),
            headers={
                "Content-Type": "text/xml; charset=utf-8",
                "SOAPAction": '"http://tempuri.org/GetHatOtoKonum_json"',
                "User-Agent": "IstanbulTransitCore/1.0"
            }
        )

        ctx = ssl._create_unverified_context()
        try:
            with urllib.request.urlopen(req, context=ctx, timeout=6) as resp:
                content = resp.read().decode("utf-8", errors="replace")
        except Exception as e:
            # If network error or timeout, return stale cache if available
            if norm_code in self._cache:
                return self._cache[norm_code]["data"]
            return []

        match = re.search(r"<GetHatOtoKonum_jsonResult>(.*?)</GetHatOtoKonum_jsonResult>", content)
        if not match:
            return []

        raw_json_str = match.group(1)
        if not raw_json_str or raw_json_str == "[]" or raw_json_str == "null":
            self._cache[norm_code] = {"timestamp": now, "data": []}
            return []

        try:
            raw_data = json.loads(raw_json_str)
        except Exception:
            return []

        buses = []
        for item in raw_data:
            try:
                lat = float(str(item.get("enlem", "")).replace(",", "."))
                lon = float(str(item.get("boylam", "")).replace(",", "."))
                if not (40.0 <= lat <= 42.0 and 27.0 <= lon <= 30.5):
                    continue
            except (ValueError, TypeError):
                continue

            buses.append({
                "kapino": str(item.get("kapino", "")).strip(),
                "lat": lat,
                "lon": lon,
                "line_code": norm_code,
                "route_code": str(item.get("guzergahkodu", "")).strip(),
                "direction": str(item.get("yon", "")).strip(),
                "nearest_stop_code": str(item.get("yakinDurakKodu", "")).strip(),
                "timestamp": str(item.get("son_konum_zamani", "")).strip(),
            })

        self._cache[norm_code] = {"timestamp": now, "data": buses}
        return buses

# Singleton instance
iett_client = IETTRealtimeClient()
