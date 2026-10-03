from pathlib import Path
import os
import csv
import zipfile

BASE_DIR = str(Path(__file__).resolve().parent.parent)
TEMP_DIR = os.path.join(BASE_DIR, "data", "gtfs_temp")
ROUTER_ZIP = os.path.join(BASE_DIR, "data", "router", "gtfs-istanbul.zip")

METROBUS_STATIONS = [
    ("mb_01", "Beylikdüzü Sondurak (TÜYAP) Metrobüs", 41.0223, 28.6272),
    ("mb_02", "Hadımköy Metrobüs", 41.0189, 28.6368),
    ("mb_03", "Cumhuriyet Mahallesi Metrobüs", 41.0152, 28.6455),
    ("mb_04", "Beylikdüzü Belediye Metrobüs", 41.0118, 28.6542),
    ("mb_05", "Beylikdüzü Metrobüs", 41.0085, 28.6631),
    ("mb_06", "Güzelyurt Metrobüs", 41.0052, 28.6720),
    ("mb_07", "Haramidere Metrobüs", 41.0021, 28.6815),
    ("mb_08", "Haramidere Sanayi Metrobüs", 40.9998, 28.6925),
    ("mb_09", "Saadetdere Mahallesi Metrobüs", 40.9965, 28.7032),
    ("mb_10", "Mustafa Kemal Paşa Metrobüs", 40.9928, 28.7121),
    ("mb_11", "Cihangir - Üniversite Mah. Metrobüs", 40.9892, 28.7215),
    ("mb_12", "Avcılar Merkez Kampüs Metrobüs", 40.9855, 28.7308),
    ("mb_13", "Şükrübey Metrobüs", 40.9821, 28.7402),
    ("mb_14", "İBB Sosyal Tesisleri Metrobüs", 40.9788, 28.7511),
    ("mb_15", "Küçükçekmece Metrobüs", 40.9792, 28.7695),
    ("mb_16", "Cennet Mahallesi Metrobüs", 40.9832, 28.7845),
    ("mb_17", "Florya Metrobüs", 40.9875, 28.7942),
    ("mb_18", "Beşyol Metrobüs", 40.9912, 28.8005),
    ("mb_19", "Sefaköy Metrobüs", 40.9955, 28.8078),
    ("mb_20", "Yenibosna Metrobüs", 40.9925, 28.8352),
    ("mb_21", "Şirinevler (Ataköy) Metrobüs", 40.9915, 28.8475),
    ("mb_22", "Bahçelievler Metrobüs", 40.9942, 28.8595),
    ("mb_23", "İncirli (Ömür) Metrobüs", 40.9985, 28.8715),
    ("mb_24", "Zeytinburnu Metrobüs", 41.0052, 28.8955),
    ("mb_25", "Merter Metrobüs", 41.0112, 28.9052),
    ("mb_26", "Cevizlibağ Metrobüs", 41.0165, 28.9168),
    ("mb_27", "Topkapı Metrobüs", 41.0225, 28.9282),
    ("mb_28", "Bayrampaşa - Maltepe Metrobüs", 41.0285, 28.9345),
    ("mb_29", "Edirnekapı Metrobüs", 41.0345, 28.9392),
    ("mb_30", "Ayvansaray - Eyüpsultan Metrobüs", 41.0425, 28.9425),
    ("mb_31", "Halıcıoğlu Metrobüs", 41.0485, 28.9455),
    ("mb_32", "Okmeydanı Metrobüs", 41.0542, 28.9552),
    ("mb_33", "Darülaceze - Perpa Metrobüs", 41.0585, 28.9665),
    ("mb_34", "Okmeydanı Hastane Metrobüs", 41.0621, 28.9745),
    ("mb_35", "Çağlayan Metrobüs", 41.0655, 28.9832),
    ("mb_36", "Mecidiyeköy Metrobüs", 41.0667, 28.9936),
    ("mb_37", "Zincirlikuyu Metrobüs", 41.0682, 29.0118),
    ("mb_38", "15 Temmuz Şehitler Köprüsü Metrobüs", 41.0465, 29.0315),
    ("mb_39", "Burhaniye Metrobüs", 41.0365, 29.0425),
    ("mb_40", "Altunizade Metrobüs", 41.0285, 29.0495),
    ("mb_41", "Acıbadem Metrobüs", 41.0125, 29.0552),
    ("mb_42", "Uzunçayır Metrobüs", 41.0025, 29.0585),
    ("mb_43", "Fikirtepe Metrobüs", 40.9952, 29.0495),
    ("mb_44", "Söğütlüçeşme Metrobüs", 40.9915, 29.0376)
]

def append_unique_csv(filename, fieldnames, rows, id_field):
    path = os.path.join(TEMP_DIR, filename)
    existing_ids = set()
    file_exists = os.path.exists(path)
    
    if file_exists and id_field:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            reader = csv.DictReader(f)
            for r in reader:
                val = r.get(id_field)
                if val:
                    existing_ids.add(val)
                    
    to_write = [r for r in rows if not id_field or r.get(id_field) not in existing_ids]
    if not to_write:
        print(f"  ℹ {filename}: Tüm kayıtlar zaten mevcut.")
        return len(existing_ids)

    with open(path, "a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerows(to_write)
    print(f"  ✔ {filename}: +{len(to_write)} yeni kayıt eklendi.")
    return len(existing_ids) + len(to_write)

def inject_metrobus():
    print("=== 7/24 Kesintisiz Metrobüs Omurgası Enjeksiyonu Başlıyor ===")
    os.makedirs(TEMP_DIR, exist_ok=True)

    # 1. ROUTE: 34G (24 Saat Kesintisiz Metrobüs)
    routes = [
        {
            "route_id": "34G",
            "agency_id": "iett",
            "route_short_name": "34G",
            "route_long_name": "Beylikdüzü - Söğütlüçeşme (7/24 Metrobüs)",
            "route_type": "3",
            "route_color": "E66B00",
            "route_text_color": "FFFFFF"
        }
    ]
    append_unique_csv("routes.txt", ["route_id", "agency_id", "route_short_name", "route_long_name", "route_type", "route_color", "route_text_color"], routes, "route_id")

    # 2. STOPS: All 44 stations
    stops = []
    for sid, name, lat, lon in METROBUS_STATIONS:
        stops.append({
            "stop_id": sid,
            "stop_name": name,
            "stop_lat": f"{lat:.6f}",
            "stop_lon": f"{lon:.6f}",
            "location_type": "0"
        })
    append_unique_csv("stops.txt", ["stop_id", "stop_name", "stop_lat", "stop_lon", "location_type"], stops, "stop_id")

    # 3. TRIPS & STOP TIMES (Daytime 3 min headway, Nighttime 10 min headway, 24/7, Bidirectional)
    # Total stations: 44. Running time between adjacent stations: ~110s (~1.83 min) -> total ~80 min
    fwd_sequence = [(sid, i * 110) for i, (sid, _, _, _) in enumerate(METROBUS_STATIONS)] # Beylikdüzü -> Söğütlüçeşme
    total_run_secs = fwd_sequence[-1][1]
    rev_sequence = [(sid, total_run_secs - offset) for sid, offset in reversed(fwd_sequence)] # Söğütlüçeşme -> Beylikdüzü

    trips = []
    stop_times = []
    trip_counter = 1

    # Loop 24 hours: 00:00 to 24:00
    for hour in range(0, 24):
        # 00:30 to 05:30 -> night interval = 10 min
        # 05:30 to 00:30 -> daytime interval = 3 min
        is_night = (1 <= hour <= 4)
        interval_mins = 10 if is_night else 3

        for minute in range(0, 60, interval_mins):
            base_s = hour * 3600 + minute * 60

            # Direction 0: Beylikdüzü -> Söğütlüçeşme
            tid_0 = f"mb_fwd_{trip_counter:05d}"
            trips.append({
                "route_id": "34G",
                "service_id": "ALL_WEEK",
                "trip_id": tid_0,
                "trip_headsign": "Söğütlüçeşme (Metrobüs)",
                "direction_id": "0",
                "shape_id": ""
            })
            for s_idx, (sid, off_sec) in enumerate(fwd_sequence, 1):
                arr_sec = base_s + off_sec
                arr_str = f"{(arr_sec // 3600):02d}:{(arr_sec % 3600) // 60:02d}:{(arr_sec % 60):02d}"
                stop_times.append({
                    "trip_id": tid_0,
                    "arrival_time": arr_str,
                    "departure_time": arr_str,
                    "stop_id": sid,
                    "stop_sequence": str(s_idx)
                })

            # Direction 1: Söğütlüçeşme -> Beylikdüzü
            tid_1 = f"mb_rev_{trip_counter:05d}"
            trips.append({
                "route_id": "34G",
                "service_id": "ALL_WEEK",
                "trip_id": tid_1,
                "trip_headsign": "Beylikdüzü Sondurak TÜYAP",
                "direction_id": "1",
                "shape_id": ""
            })
            for s_idx, (sid, off_sec) in enumerate(rev_sequence, 1):
                arr_sec = base_s + off_sec
                arr_str = f"{(arr_sec // 3600):02d}:{(arr_sec % 3600) // 60:02d}:{(arr_sec % 60):02d}"
                stop_times.append({
                    "trip_id": tid_1,
                    "arrival_time": arr_str,
                    "departure_time": arr_str,
                    "stop_id": sid,
                    "stop_sequence": str(s_idx)
                })

            trip_counter += 1

    append_unique_csv("trips.txt", ["route_id", "service_id", "trip_id", "trip_headsign", "direction_id", "shape_id"], trips, "trip_id")
    append_unique_csv("stop_times.txt", ["trip_id", "arrival_time", "departure_time", "stop_id", "stop_sequence"], stop_times, None)

    # 4. TRANSFERS: Connect mb stations to other transit lines
    transfers = [
        # Mecidiyeköy: mb_36 <-> H-2 / HVIST <-> M2 <-> M7
        {"from_stop_id": "mb_36", "to_stop_id": "h2_mecidiyekoy", "transfer_type": "2", "min_transfer_time": "120"},
        {"from_stop_id": "h2_mecidiyekoy", "to_stop_id": "mb_36", "transfer_type": "2", "min_transfer_time": "120"},
        {"from_stop_id": "mb_36", "to_stop_id": "91618", "transfer_type": "2", "min_transfer_time": "300"}, # M2
        {"from_stop_id": "91618", "to_stop_id": "mb_36", "transfer_type": "2", "min_transfer_time": "300"},
        {"from_stop_id": "mb_36", "to_stop_id": "272168", "transfer_type": "2", "min_transfer_time": "300"}, # M7
        {"from_stop_id": "272168", "to_stop_id": "mb_36", "transfer_type": "2", "min_transfer_time": "300"},

        # Zincirlikuyu: mb_37 <-> Gayrettepe M2 <-> Gayrettepe M11
        {"from_stop_id": "mb_37", "to_stop_id": "m11_gayrettepe", "transfer_type": "2", "min_transfer_time": "420"},
        {"from_stop_id": "m11_gayrettepe", "to_stop_id": "mb_37", "transfer_type": "2", "min_transfer_time": "420"},
        {"from_stop_id": "mb_37", "to_stop_id": "19018", "transfer_type": "2", "min_transfer_time": "360"}, # M2
        {"from_stop_id": "19018", "to_stop_id": "mb_37", "transfer_type": "2", "min_transfer_time": "360"},

        # Altunizade: mb_40 <-> M5
        {"from_stop_id": "mb_40", "to_stop_id": "87259", "transfer_type": "2", "min_transfer_time": "180"},
        {"from_stop_id": "87259", "to_stop_id": "mb_40", "transfer_type": "2", "min_transfer_time": "180"},

        # Uzunçayır: mb_42 <-> M4 Ünalan
        {"from_stop_id": "mb_42", "to_stop_id": "18995", "transfer_type": "2", "min_transfer_time": "240"},
        {"from_stop_id": "18995", "to_stop_id": "mb_42", "transfer_type": "2", "min_transfer_time": "240"},

        # Küçükçekmece: mb_15 <-> Marmaray
        {"from_stop_id": "mb_15", "to_stop_id": "iett_510069", "transfer_type": "2", "min_transfer_time": "180"},
        {"from_stop_id": "iett_510069", "to_stop_id": "mb_15", "transfer_type": "2", "min_transfer_time": "180"},

        # Söğütlüçeşme: mb_44 <-> Marmaray
        {"from_stop_id": "mb_44", "to_stop_id": "40098", "transfer_type": "2", "min_transfer_time": "180"},
        {"from_stop_id": "40098", "to_stop_id": "mb_44", "transfer_type": "2", "min_transfer_time": "180"},

        # Merter: mb_25 <-> M1A
        {"from_stop_id": "mb_25", "to_stop_id": "18960", "transfer_type": "2", "min_transfer_time": "180"},
        {"from_stop_id": "18960", "to_stop_id": "mb_25", "transfer_type": "2", "min_transfer_time": "180"},

        # Zeytinburnu: mb_24 <-> M1A & T1
        {"from_stop_id": "mb_24", "to_stop_id": "18959", "transfer_type": "2", "min_transfer_time": "180"},
        {"from_stop_id": "18959", "to_stop_id": "mb_24", "transfer_type": "2", "min_transfer_time": "180"},
        {"from_stop_id": "mb_24", "to_stop_id": "19080", "transfer_type": "2", "min_transfer_time": "180"},
        {"from_stop_id": "19080", "to_stop_id": "mb_24", "transfer_type": "2", "min_transfer_time": "180"},

        # Şirinevler: mb_21 <-> M1A
        {"from_stop_id": "mb_21", "to_stop_id": "18974", "transfer_type": "2", "min_transfer_time": "180"},
        {"from_stop_id": "18974", "to_stop_id": "mb_21", "transfer_type": "2", "min_transfer_time": "180"},

        # TÜYAP: mb_01 <-> 300/401 Suburban bus
        {"from_stop_id": "mb_01", "to_stop_id": "iett_290488", "transfer_type": "2", "min_transfer_time": "180"},
        {"from_stop_id": "iett_290488", "to_stop_id": "mb_01", "transfer_type": "2", "min_transfer_time": "180"},

        # Halıcıoğlu: mb_31 <-> HALICIOĞLU Bus stop
        {"from_stop_id": "mb_31", "to_stop_id": "88781", "transfer_type": "2", "min_transfer_time": "120"},
        {"from_stop_id": "88781", "to_stop_id": "mb_31", "transfer_type": "2", "min_transfer_time": "120"},
    ]
    append_unique_csv("transfers.txt", ["from_stop_id", "to_stop_id", "transfer_type", "min_transfer_time"], transfers, None)

    # 5. REPACK gtfs-istanbul.zip
    print("  📦 gtfs-istanbul.zip güncelleniyor...")
    with zipfile.ZipFile(ROUTER_ZIP, "w", zipfile.ZIP_DEFLATED) as zf:
        for fname in ["agency.txt", "calendar.txt", "routes.txt", "stops.txt", "trips.txt", "stop_times.txt", "shapes.txt", "frequencies.txt", "transfers.txt"]:
            fpath = os.path.join(TEMP_DIR, fname)
            if os.path.exists(fpath):
                zf.write(fpath, arcname=fname)
    print(f"  ✔ {ROUTER_ZIP} başarıyla güncellendi ({os.path.getsize(ROUTER_ZIP) // 1024 // 1024} MB).")

if __name__ == "__main__":
    inject_metrobus()
