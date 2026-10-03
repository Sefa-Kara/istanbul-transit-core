import urllib.request
import urllib.parse
import json
import sys
from datetime import datetime

# Sample coordinates in Istanbul:
LOCATIONS = {
    "kadikoy": {"name": "Kadıköy Rıhtım", "lat": 40.9904, "lon": 29.0253},
    "besiktas": {"name": "Beşiktaş İskele", "lat": 41.0422, "lon": 29.0067},
    "uskudar": {"name": "Üsküdar Meydan", "lat": 41.0267, "lon": 29.0153},
    "eminonu": {"name": "Eminönü", "lat": 41.0175, "lon": 28.9733},
    "mecidiyekoy": {"name": "Mecidiyeköy Metrobüs", "lat": 41.0667, "lon": 28.9936},
    "taksim": {"name": "Taksim Meydanı", "lat": 41.0370, "lon": 28.9850},
    "beylikduzu": {"name": "Beylikdüzü Metrobüs", "lat": 41.0028, "lon": 28.6534},
}

def query_route(from_coord, to_coord, date_str=None, time_str=None, banned_agencies="37,19", force_ferry=False):
    """
    Queries OpenTripPlanner for routes between from_coord and to_coord.
    banned_agencies: '37,19' bans Minibus & Taksi Dolmus by default.
    force_ferry: forces the search to route via Ferry or prioritize ferry.
    """
    now = datetime.now()
    if not date_str:
        date_str = now.strftime("%m-%d-%Y")
    if not time_str:
        time_str = now.strftime("%I:%M%p") # e.g. 03:30pm

    params = {
        "fromPlace": f"{from_coord[0]},{from_coord[1]}",
        "toPlace": f"{to_coord[0]},{to_coord[1]}",
        "time": time_str,
        "date": date_str,
        "mode": "TRANSIT,WALK",
        "maxTransfers": 5,
        "numItineraries": 5,
        "walkSpeed": 1.33,
        "bannedAgencies": banned_agencies
    }

    url = f"http://localhost:8080/otp/routers/default/plan?{urllib.parse.urlencode(params)}"
    print(f"Requesting: {url}\n")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "IstanbulTransitClient/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.load(resp)
            return parse_and_display_itineraries(data, force_ferry)
    except Exception as e:
        print(f"Query error: {e}")
        return None

def parse_and_display_itineraries(data, force_ferry=False):
    plan = data.get("plan", {})
    itineraries = plan.get("itineraries", [])
    if not itineraries:
        print("No route found.")
        return []

    print(f"Found {len(itineraries)} alternative route(s):\n" + "="*60)
    for idx, itin in enumerate(itineraries, 1):
        duration_min = round(itin.get("duration", 0) / 60)
        walk_time_min = round(itin.get("walkTime", 0) / 60)
        transfers = itin.get("transfers", 0)
        start_time = datetime.fromtimestamp(itin.get("startTime", 0) / 1000).strftime("%H:%M")
        end_time = datetime.fromtimestamp(itin.get("endTime", 0) / 1000).strftime("%H:%M")

        legs = itin.get("legs", [])
        has_ferry = any(leg.get("mode") == "FERRY" for leg in legs)
        if force_ferry and not has_ferry:
            continue

        print(f"--- Rota #{idx}: {start_time} -> {end_time} ({duration_min} dk) | Aktarma: {transfers} | Yürüme: {walk_time_min} dk ---")
        for l_idx, leg in enumerate(legs, 1):
            mode = leg.get("mode")
            from_name = leg.get("from", {}).get("name", "Bilinmeyen Durak")
            to_name = leg.get("to", {}).get("name", "Bilinmeyen Durak")
            leg_duration = round(leg.get("duration", 0) / 60)
            route_name = leg.get("routeShortName") or leg.get("routeLongName") or ""
            headsign = leg.get("headsign") or ""
            agency = leg.get("agencyName") or ""

            if mode == "WALK":
                dist = round(leg.get("distance", 0))
                print(f"  {l_idx}. [YÜRÜME] {from_name} -> {to_name} ({dist}m, {leg_duration} dk)")
            else:
                extra = f" | Yön: {headsign}" if headsign else ""
                agency_tag = f" [{agency}]" if agency else ""
                print(f"  {l_idx}. [{mode}] {route_name}{agency_tag}: {from_name} -> {to_name} ({leg_duration} dk){extra}")
        print()

if __name__ == "__main__":
    # Test: Kadıköy -> Beşiktaş
    kdk = (LOCATIONS["kadikoy"]["lat"], LOCATIONS["kadikoy"]["lon"])
    bsk = (LOCATIONS["besiktas"]["lat"], LOCATIONS["besiktas"]["lon"])
    print(f"Testing route from Kadıköy to Beşiktaş:")
    query_route(kdk, bsk)
