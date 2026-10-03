import urllib.request
import json
import argparse
from datetime import datetime

LOCATIONS = {
    "kadikoy": {"name": "Kadıköy Rıhtım", "lat": 40.9904, "lon": 29.0253},
    "besiktas": {"name": "Beşiktaş İskele", "lat": 41.0422, "lon": 29.0067},
    "uskudar": {"name": "Üsküdar Meydan", "lat": 41.0267, "lon": 29.0153},
    "eminonu": {"name": "Eminönü", "lat": 41.0175, "lon": 28.9733},
    "mecidiyekoy": {"name": "Mecidiyeköy Metrobüs", "lat": 41.0667, "lon": 28.9936},
    "taksim": {"name": "Taksim Meydanı", "lat": 41.0370, "lon": 28.9850},
    "beylikduzu": {"name": "Beylikdüzü Metrobüs", "lat": 41.0028, "lon": 28.6534},
    "bostanci": {"name": "Bostancı İskele", "lat": 40.9525, "lon": 29.0945},
}

def resolve_location(loc_str):
    loc_lower = loc_str.strip().lower()
    if loc_lower in LOCATIONS:
        return LOCATIONS[loc_lower]["lat"], LOCATIONS[loc_lower]["lon"], LOCATIONS[loc_lower]["name"]
    try:
        parts = [float(p.strip()) for p in loc_str.split(",")]
        if len(parts) == 2:
            return parts[0], parts[1], f"({parts[0]:.4f}, {parts[1]:.4f})"
    except ValueError:
        pass
    raise ValueError(f"Bilinmeyen konum: '{loc_str}'. Bilinenler: {list(LOCATIONS.keys())} veya 'lat,lon'")

def clean_display_text(text):
    if not text: return ""
    try:
        if any(c in text for c in ["Ã", "Å", "Ä", "â", "Â"]):
            return text.encode("latin1").decode("utf-8")
    except Exception:
        pass
    return text

def plan_journey(from_str, to_str, allow_minibus=False, prefer_ferry=False, force_ferry=False, date_str=None, time_str=None, num_routes=5):
    from_lat, from_lon, from_name = resolve_location(from_str)
    to_lat, to_lon, to_name = resolve_location(to_str)

    now = datetime.now()
    if not date_str:
        date_str = now.strftime("%Y-%m-%d")
    if not time_str:
        time_str = now.strftime("%H:%M:00")

    # Banned agencies: '1:37,1:19' bans Minibüs and Taksi Dolmuş
    banned_clause = ""
    if not allow_minibus:
        banned_clause = 'banned: { agencies: "1:37,1:19" }'

    # Mode weights: ferry priority
    weight_clause = ""
    if prefer_ferry or force_ferry:
        weight_clause = 'modeWeight: { FERRY: 0.05, SUBWAY: 2.0, RAIL: 2.0, BUS: 2.0 }'

    # If force_ferry, fetch more to find ferry combinations
    fetch_count = max(num_routes, 10 if force_ferry else num_routes)

    query = f"""
    {{
      plan(
        from: {{lat: {from_lat}, lon: {from_lon}}}
        to: {{lat: {to_lat}, lon: {to_lon}}}
        date: "{date_str}"
        time: "{time_str}"
        numItineraries: {fetch_count}
        {banned_clause}
        {weight_clause}
        transportModes: [{{mode: WALK}}, {{mode: TRANSIT}}]
      ) {{
        itineraries {{
          duration
          walkTime
          legs {{
            mode
            duration
            distance
            from {{ name }}
            to {{ name }}
            route {{
              shortName
              longName
              agency {{ name }}
            }}
          }}
        }}
      }}
    }}
    """

    req = urllib.request.Request(
        "http://localhost:8080/otp/routers/default/index/graphql",
        data=json.dumps({"query": query}).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.load(resp)
    except Exception as e:
        print(f"Bağlantı Hatası: OTP sunucusuna ulaşılamadı ({e})")
        return

    itineraries = (data.get("data") or {}).get("plan", {}).get("itineraries", [])
    if not itineraries:
        print(f"'{from_name}' -> '{to_name}' arasında uygun rota bulunamadı.")
        return

    if force_ferry:
        itineraries = [itin for itin in itineraries if any(leg["mode"] == "FERRY" for leg in itin["legs"])]
        if not itineraries:
            print(f"'{from_name}' -> '{to_name}' arasında vapur içeren bir rota bulunamadı.")
            return

    itineraries = itineraries[:num_routes]

    print("=" * 70)
    print(f"📍 ROTA ARAMASI: {from_name} -> {to_name}")
    print(f"🕒 Tarih / Saat : {date_str} {time_str}")
    minibus_status = 'AÇIK' if allow_minibus else 'KAPALI (Hariç tutuldu)'
    ferry_status = 'ZORUNLU (Sadece vapur rotaları)' if force_ferry else ('ÖNCELİKLİ' if prefer_ferry else 'NORMAL')
    print(f"⚙️ Filtreler    : Minibüs={minibus_status} | Vapur Durumu={ferry_status}")
    print("=" * 70)

    for idx, itin in enumerate(itineraries, 1):
        total_min = int(itin["duration"] // 60)
        walk_min = int(itin["walkTime"] // 60)
        legs = itin["legs"]
        transit_count = sum(1 for leg in legs if leg["mode"] != "WALK")
        transfers = max(0, transit_count - 1)

        print(f"\n🏷️  SEÇENEK #{idx}: Toplam Süre: {total_min} dk | Aktarma: {transfers} | Yürüme: {walk_min} dk")
        print("-" * 70)

        for l_idx, leg in enumerate(legs, 1):
            mode = leg["mode"]
            leg_min = int(round(leg["duration"] / 60))
            from_stop = clean_display_text(leg["from"]["name"])
            to_stop = clean_display_text(leg["to"]["name"])

            if mode == "WALK":
                dist = int(round(leg.get("distance", 0)))
                print(f"  🚶 {l_idx}. Adım [YÜRÜYÜŞ]: {from_stop} ➔ {to_stop} ({dist} metre, ~{leg_min} dk)")
            else:
                route_info = leg.get("route") or {}
                sname = clean_display_text(route_info.get("shortName") or "")
                lname = clean_display_text(route_info.get("longName") or "")
                agency_name = clean_display_text((route_info.get("agency") or {}).get("name") or "")
                emoji = "🚢" if mode == "FERRY" else "🚇" if mode in ["SUBWAY", "RAIL"] else "🚊" if mode == "TRAM" else "🚌"
                print(f"  {emoji} {l_idx}. Adım [{mode} - {sname}]: {from_stop} ➔ {to_stop} (~{leg_min} dk) [{agency_name}]")
                if lname and lname != sname:
                    print(f"      Hat: {lname}")

    print("\n" + "=" * 70)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="İstanbul Bağımsız Toplu Taşıma Rota Motoru")
    parser.add_argument("--from-place", default="kadikoy", help="Başlangıç (örn: kadikoy, mecidiyekoy, beylikduzu veya lat,lon)")
    parser.add_argument("--to-place", default="besiktas", help="Varış (örn: besiktas, uskudar, taksim veya lat,lon)")
    parser.add_argument("--allow-minibus", action="store_true", help="Minibüs/Dolmuşları rotaya dahil et")
    parser.add_argument("--prefer-ferry", action="store_true", help="Vapur hatlarına öncelik ver")
    parser.add_argument("--force-ferry", action="store_true", help="Rotada mutlaka vapur kullanılsın")
    parser.add_argument("--num-routes", type=int, default=3, help="Listelenecek maksimum rota sayısı")
    parser.add_argument("--time", default="15:00:00", help="Kalkış saati (HH:MM:SS)")
    parser.add_argument("--date", default="2026-09-24", help="Tarih (YYYY-MM-DD)")
    args = parser.parse_args()

    plan_journey(
        args.from_place,
        args.to_place,
        allow_minibus=args.allow_minibus,
        prefer_ferry=args.prefer_ferry,
        force_ferry=args.force_ferry,
        num_routes=args.num_routes,
        date_str=args.date,
        time_str=args.time
    )
