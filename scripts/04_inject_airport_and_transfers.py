from pathlib import Path
import os
import csv
import zipfile

BASE_DIR = str(Path(__file__).resolve().parent.parent)
TEMP_DIR = os.path.join(BASE_DIR, "data", "gtfs_temp")
ROUTER_ZIP = os.path.join(BASE_DIR, "data", "router", "gtfs-istanbul.zip")

def safe_append_csv(filename, fieldnames, rows, id_field=None):
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
        print(f"  ℹ {filename}: Eklenmesi gereken kayıtlar zaten mevcut.")
        return

    with open(path, "a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerows(to_write)
    print(f"  ✔ {filename}: +{len(to_write)} yeni kayıt eklendi.")

def inject_all():
    print("=== M11 Metrosu, M4 Sabiha Gökçen Uzatması, Havaist, H-2 ve transfers.txt Enjeksiyonu ===")
    os.makedirs(TEMP_DIR, exist_ok=True)

    # 1. AGENCIES
    new_agencies = [
        {"agency_id": "tcdd_uab", "agency_name": "TCDD Taşımacılık / UAB (M11 Metrosu)", "agency_url": "https://www.tcddtasimacilik.gov.tr", "agency_timezone": "Europe/Istanbul", "agency_lang": "tr"},
        {"agency_id": "havaist", "agency_name": "HAVAİST Havalimanı Otobüsleri", "agency_url": "https://www.hava.ist", "agency_timezone": "Europe/Istanbul", "agency_lang": "tr"}
    ]
    safe_append_csv("agency.txt", ["agency_id", "agency_name", "agency_url", "agency_timezone", "agency_lang"], new_agencies, "agency_id")

    # 2. ROUTES
    new_routes = [
        {"route_id": "M11", "agency_id": "tcdd_uab", "route_short_name": "M11", "route_long_name": "Gayrettepe - İstanbul Havalimanı - Arnavutköy", "route_type": "1", "route_color": "9E1B32", "route_text_color": "FFFFFF"},
        {"route_id": "1294", "agency_id": "11", "route_short_name": "M4", "route_long_name": "Kadıköy - Sabiha Gökçen Havalimanı (M4)", "route_type": "1", "route_color": "E30613", "route_text_color": "FFFFFF"},
        {"route_id": "HVIST_5", "agency_id": "havaist", "route_short_name": "HVİST-5", "route_long_name": "Mecidiyeköy - İstanbul Havalimanı", "route_type": "3", "route_color": "0055AA", "route_text_color": "FFFFFF"},
        {"route_id": "HVIST_8", "agency_id": "havaist", "route_short_name": "HVİST-8", "route_long_name": "Beylikdüzü - İstanbul Havalimanı", "route_type": "3", "route_color": "0055AA", "route_text_color": "FFFFFF"},
        {"route_id": "HVIST_10", "agency_id": "havaist", "route_short_name": "HVİST-10", "route_long_name": "Bakırköy - İstanbul Havalimanı", "route_type": "3", "route_color": "0055AA", "route_text_color": "FFFFFF"},
        {"route_id": "HVIST_14", "agency_id": "havaist", "route_short_name": "HVİST-14", "route_long_name": "Kadıköy - İstanbul Havalimanı", "route_type": "3", "route_color": "0055AA", "route_text_color": "FFFFFF"},
        {"route_id": "HVIST_16", "agency_id": "havaist", "route_short_name": "HVİST-16", "route_long_name": "Taksim - İstanbul Havalimanı", "route_type": "3", "route_color": "0055AA", "route_text_color": "FFFFFF"},
        {"route_id": "H-2", "agency_id": "iett", "route_short_name": "H-2", "route_long_name": "Mecidiyeköy Metrobüs - Kağıthane - İstanbul Havalimanı", "route_type": "3", "route_color": "FFCC00", "route_text_color": "000000"}
    ]
    safe_append_csv("routes.txt", ["route_id", "agency_id", "route_short_name", "route_long_name", "route_type", "route_color", "route_text_color"], new_routes, "route_id")

    # 3. STOPS
    new_stops = [
        # M11 Stations
        {"stop_id": "m11_gayrettepe", "stop_name": "Gayrettepe M11", "stop_lat": "41.068300", "stop_lon": "29.011700", "location_type": "0"},
        {"stop_id": "m11_kagithane", "stop_name": "Kağıthane M11", "stop_lat": "41.082000", "stop_lon": "28.974500", "location_type": "0"},
        {"stop_id": "m11_hasdal", "stop_name": "Hasdal M11", "stop_lat": "41.109800", "stop_lon": "28.953200", "location_type": "0"},
        {"stop_id": "m11_kemerburgaz", "stop_name": "Kemerburgaz M11", "stop_lat": "41.171100", "stop_lon": "28.919800", "location_type": "0"},
        {"stop_id": "m11_gokturk", "stop_name": "Göktürk M11", "stop_lat": "41.184300", "stop_lon": "28.891100", "location_type": "0"},
        {"stop_id": "m11_ihsaniye", "stop_name": "İhsaniye M11", "stop_lat": "41.241500", "stop_lon": "28.790200", "location_type": "0"},
        {"stop_id": "m11_havalimani", "stop_name": "İstanbul Havalimanı M11", "stop_lat": "41.261200", "stop_lon": "28.742000", "location_type": "0"},
        {"stop_id": "m11_kargo", "stop_name": "Kargo Terminali M11", "stop_lat": "41.272100", "stop_lon": "28.730200", "location_type": "0"},
        {"stop_id": "m11_arnavutkoy", "stop_name": "Arnavutköy Hastane M11", "stop_lat": "41.205200", "stop_lon": "28.736000", "location_type": "0"},

        # M4 Sabiha Gökçen Extension Stations (Pinned within OSM road graph)
        {"stop_id": "m4_fevzi_cakmak", "stop_name": "Fevzi Çakmak - Hastane M4", "stop_lat": "40.893100", "stop_lon": "29.273600", "location_type": "0"},
        {"stop_id": "m4_yayalar", "stop_name": "Yayalar - Şeyhli M4", "stop_lat": "40.902300", "stop_lon": "29.280000", "location_type": "0"},
        {"stop_id": "m4_kurtkoy", "stop_name": "Kurtköy M4", "stop_lat": "40.911200", "stop_lon": "29.282000", "location_type": "0"},
        {"stop_id": "m4_saw", "stop_name": "Sabiha Gökçen Havalimanı M4", "stop_lat": "40.908621", "stop_lon": "29.284000", "location_type": "0"},
        
        # Airport Buses (Co-located with terminal for zero walk barrier)
        {"stop_id": "h2_mecidiyekoy", "stop_name": "Mecidiyeköy Metrobüs (H-2 / HVİST)", "stop_lat": "41.066700", "stop_lon": "28.993600", "location_type": "0"},
        {"stop_id": "h2_ist_havalimani", "stop_name": "İstanbul Havalimanı Otobüs Peronları", "stop_lat": "41.261200", "stop_lon": "28.742000", "location_type": "0"},
        {"stop_id": "hvist_taksim", "stop_name": "Taksim Havaist", "stop_lat": "41.039200", "stop_lon": "28.986500", "location_type": "0"},
        {"stop_id": "hvist_kadikoy", "stop_name": "Kadıköy Rıhtım Havaist", "stop_lat": "40.990400", "stop_lon": "29.025300", "location_type": "0"},
        {"stop_id": "hvist_bakirkoy", "stop_name": "Bakırköy İDO Havaist", "stop_lat": "40.973077", "stop_lon": "28.878101", "location_type": "0"},
        {"stop_id": "hvist_beylikduzu", "stop_name": "Beylikdüzü TÜYAP Havaist", "stop_lat": "41.022300", "stop_lon": "28.627200", "location_type": "0"}
    ]
    safe_append_csv("stops.txt", ["stop_id", "stop_name", "stop_lat", "stop_lon", "location_type"], new_stops, "stop_id")

    # 4. TRIPS & STOP TIMES (Bidirectional with GTFS-compliant >24:00 monotonic timestamps)
    trips = []
    stop_times = []

    def format_gtfs_time(seconds):
        h = seconds // 3600
        m = (seconds % 3600) // 60
        s = seconds % 60
        return f"{h:02d}:{m:02d}:{s:02d}"

    def build_bidirectional_timetables(prefix, route_id, headsign_fwd, headsign_rev, seq_fwd, interval_mins, start_h=0, end_h=24):
        seq_rev = []
        total_time = seq_fwd[-1][1]
        for sid, off in reversed(seq_fwd):
            seq_rev.append((sid, total_time - off))

        counter = 1
        for h in range(start_h, end_h):
            for m in range(0, 60, interval_mins):
                base_s = h * 3600 + m * 60

                # Direction 0 (Forward)
                tid_0 = f"{prefix}_0_{counter:04d}"
                trips.append({
                    "route_id": route_id, "service_id": "ALL_WEEK", "trip_id": tid_0,
                    "trip_headsign": headsign_fwd, "direction_id": "0", "shape_id": ""
                })
                for sidx, (sid, off_m) in enumerate(seq_fwd, 1):
                    s_secs = base_s + off_m * 60
                    s_str = format_gtfs_time(s_secs)
                    stop_times.append({"trip_id": tid_0, "arrival_time": s_str, "departure_time": s_str, "stop_id": sid, "stop_sequence": str(sidx)})

                # Direction 1 (Reverse)
                tid_1 = f"{prefix}_1_{counter:04d}"
                trips.append({
                    "route_id": route_id, "service_id": "ALL_WEEK", "trip_id": tid_1,
                    "trip_headsign": headsign_rev, "direction_id": "1", "shape_id": ""
                })
                for sidx, (sid, off_m) in enumerate(seq_rev, 1):
                    s_secs = base_s + off_m * 60
                    s_str = format_gtfs_time(s_secs)
                    stop_times.append({"trip_id": tid_1, "arrival_time": s_str, "departure_time": s_str, "stop_id": sid, "stop_sequence": str(sidx)})

                counter += 1

    # M11 Metro: every 15 min from 06:00 to 24:00 (29 min to Havalimanı)
    m11_seq = [
        ("m11_gayrettepe", 0),
        ("m11_kagithane", 5),
        ("m11_hasdal", 9),
        ("m11_kemerburgaz", 15),
        ("m11_gokturk", 19),
        ("m11_ihsaniye", 25),
        ("m11_havalimani", 29),
        ("m11_kargo", 33),
        ("m11_arnavutkoy", 43)
    ]
    build_bidirectional_timetables("m11", "M11", "İstanbul Havalimanı / Arnavutköy", "Gayrettepe Metrosu", m11_seq, interval_mins=15, start_h=6, end_h=24)

    # M4 Unified Metro: Full 23 Stations Kadıköy <-> Sabiha Gökçen Havalimanı (24/7, peak 4m, night 15m)
    m4_full_seq = [
        ("19007", 0),             # Kadıköy
        ("94911", 2),             # Ayrılık Çeşmesi (Marmaray aktarma)
        ("19024", 5),             # Acıbadem
        ("18995", 7),             # Ünalan (Metrobüs Uzunçayır aktarma)
        ("18976", 10),            # Göztepe
        ("18997", 12),            # Yenisahra
        ("18977", 15),            # Kozyatağı (M8 aktarma)
        ("18975", 17),            # Bostancı
        ("18991", 20),            # Küçükyalı
        ("19015", 22),            # Maltepe
        ("19022", 24),            # Huzurevi
        ("19021", 26),            # Gülsuyu
        ("19016", 28),            # Esenkent
        ("19001", 30),            # Hastane - Adliye
        ("19019", 33),            # Soğanlık
        ("19012", 36),            # Kartal
        ("94913", 38),            # Yakacık - Adnan Kahveci
        ("53121", 41),            # Pendik
        ("53122", 44),            # Tavşantepe
        ("m4_fevzi_cakmak", 47),   # Fevzi Çakmak - Hastane
        ("m4_yayalar", 50),        # Yayalar - Şeyhli
        ("m4_kurtkoy", 53),        # Kurtköy
        ("m4_saw", 56)            # Sabiha Gökçen Havalimanı M4
    ]
    build_bidirectional_timetables("m4_day", "1294", "Sabiha Gökçen Havalimanı", "Kadıköy", m4_full_seq, interval_mins=4, start_h=6, end_h=24)
    build_bidirectional_timetables("m4_ngt", "1294", "Sabiha Gökçen Havalimanı", "Kadıköy", m4_full_seq, interval_mins=15, start_h=0, end_h=6)

    # H-2 Express Bus: every 30 min 24/7 (45 min Mecidiyeköy -> Havalimanı)
    h2_seq = [("h2_mecidiyekoy", 0), ("m11_kagithane", 10), ("m11_kemerburgaz", 25), ("h2_ist_havalimani", 45)]
    build_bidirectional_timetables("h2", "H-2", "İstanbul Havalimanı", "Mecidiyeköy Metrobüs", h2_seq, interval_mins=30, start_h=0, end_h=24)

    # HVİST-5 Mecidiyeköy: every 30 min 24/7
    h5_seq = [("h2_mecidiyekoy", 0), ("h2_ist_havalimani", 45)]
    build_bidirectional_timetables("hv5", "HVIST_5", "İstanbul Havalimanı", "Mecidiyeköy", h5_seq, interval_mins=30, start_h=0, end_h=24)

    # HVİST-16 Taksim: every 30 min 24/7
    h16_seq = [("hvist_taksim", 0), ("h2_ist_havalimani", 65)]
    build_bidirectional_timetables("hv16", "HVIST_16", "İstanbul Havalimanı", "Taksim", h16_seq, interval_mins=30, start_h=0, end_h=24)

    # HVİST-14 Kadıköy: every 30 min 24/7
    h14_seq = [("hvist_kadikoy", 0), ("h2_ist_havalimani", 85)]
    build_bidirectional_timetables("hv14", "HVIST_14", "İstanbul Havalimanı", "Kadıköy Rıhtım", h14_seq, interval_mins=30, start_h=0, end_h=24)

    # HVİST-10 Bakırköy: every 45 min 24/7
    h10_seq = [("hvist_bakirkoy", 0), ("h2_ist_havalimani", 60)]
    build_bidirectional_timetables("hv10", "HVIST_10", "İstanbul Havalimanı", "Bakırköy İDO", h10_seq, interval_mins=45, start_h=0, end_h=24)

    # HVİST-8 Beylikdüzü: every 45 min 24/7
    h8_seq = [("hvist_beylikduzu", 0), ("h2_ist_havalimani", 50)]
    build_bidirectional_timetables("hv8", "HVIST_8", "İstanbul Havalimanı", "Beylikdüzü TÜYAP", h8_seq, interval_mins=45, start_h=0, end_h=24)

    # E-10 Express (Kadıköy - Sabiha Gökçen Havalimanı): every 20 min 24/7
    e10_seq = [("19007", 0), ("18995", 10), ("53122", 30), ("m4_saw", 50)]
    build_bidirectional_timetables("e10", "iett_3770", "Sabiha Gökçen Havalimanı", "Kadıköy", e10_seq, interval_mins=20, start_h=0, end_h=24)

    safe_append_csv("trips.txt", ["route_id", "service_id", "trip_id", "trip_headsign", "direction_id", "shape_id"], trips, "trip_id")
    safe_append_csv("stop_times.txt", ["trip_id", "arrival_time", "departure_time", "stop_id", "stop_sequence"], stop_times)

    # 5. TRANSFERS.TXT (Verified Major Interchange Network)
    transfers = [
        # --- Gayrettepe / Zincirlikuyu Hub ---
        {"from_stop_id": "19018", "to_stop_id": "m11_gayrettepe", "transfer_type": "2", "min_transfer_time": "360"}, # M2 <-> M11 (6 min via travelator)
        {"from_stop_id": "m11_gayrettepe", "to_stop_id": "19018", "transfer_type": "2", "min_transfer_time": "360"},
        {"from_stop_id": "mb_37", "to_stop_id": "m11_gayrettepe", "transfer_type": "2", "min_transfer_time": "420"}, # Metrobüs <-> M11 (7 min)
        {"from_stop_id": "m11_gayrettepe", "to_stop_id": "mb_37", "transfer_type": "2", "min_transfer_time": "420"},
        {"from_stop_id": "mb_37", "to_stop_id": "19018", "transfer_type": "2", "min_transfer_time": "360"},          # Metrobüs <-> M2 (6 min)
        {"from_stop_id": "19018", "to_stop_id": "mb_37", "transfer_type": "2", "min_transfer_time": "360"},

        # --- Kağıthane Hub ---
        {"from_stop_id": "272170", "to_stop_id": "m11_kagithane", "transfer_type": "2", "min_transfer_time": "180"}, # M7 Kağıthane <-> M11 Kağıthane (3 min viaduct)
        {"from_stop_id": "m11_kagithane", "to_stop_id": "272170", "transfer_type": "2", "min_transfer_time": "180"},

        # --- Mecidiyeköy Hub ---
        {"from_stop_id": "mb_36", "to_stop_id": "h2_mecidiyekoy", "transfer_type": "2", "min_transfer_time": "120"}, # Metrobüs <-> H-2 Peron (2 min)
        {"from_stop_id": "h2_mecidiyekoy", "to_stop_id": "mb_36", "transfer_type": "2", "min_transfer_time": "120"},
        {"from_stop_id": "mb_36", "to_stop_id": "91618", "transfer_type": "2", "min_transfer_time": "300"},          # Metrobüs <-> M2 (5 min)
        {"from_stop_id": "91618", "to_stop_id": "mb_36", "transfer_type": "2", "min_transfer_time": "300"},
        {"from_stop_id": "mb_36", "to_stop_id": "272168", "transfer_type": "2", "min_transfer_time": "300"},         # Metrobüs <-> M7 (5 min)
        {"from_stop_id": "272168", "to_stop_id": "mb_36", "transfer_type": "2", "min_transfer_time": "300"},
        {"from_stop_id": "91618", "to_stop_id": "272168", "transfer_type": "2", "min_transfer_time": "180"},         # M2 <-> M7 (3 min)
        {"from_stop_id": "272168", "to_stop_id": "91618", "transfer_type": "2", "min_transfer_time": "180"},

        # --- Yenikapı Hub (18988: M1, 19233: M2, 12261: Marmaray) ---
        {"from_stop_id": "18988", "to_stop_id": "19233", "transfer_type": "2", "min_transfer_time": "180"},          # M1 <-> M2 (3 min)
        {"from_stop_id": "19233", "to_stop_id": "18988", "transfer_type": "2", "min_transfer_time": "180"},
        {"from_stop_id": "18988", "to_stop_id": "12261", "transfer_type": "2", "min_transfer_time": "240"},          # M1 <-> Marmaray (4 min)
        {"from_stop_id": "12261", "to_stop_id": "18988", "transfer_type": "2", "min_transfer_time": "240"},
        {"from_stop_id": "19233", "to_stop_id": "12261", "transfer_type": "2", "min_transfer_time": "240"},          # M2 <-> Marmaray (4 min)
        {"from_stop_id": "12261", "to_stop_id": "19233", "transfer_type": "2", "min_transfer_time": "240"},

        # --- Ayrılık Çeşmesi Hub (94911: M4, 12258: Marmaray) ---
        {"from_stop_id": "94911", "to_stop_id": "12258", "transfer_type": "2", "min_transfer_time": "180"},          # M4 <-> Marmaray (3 min)
        {"from_stop_id": "12258", "to_stop_id": "94911", "transfer_type": "2", "min_transfer_time": "180"},

        # --- Üsküdar Hub (87256: M5, 12259: Marmaray, 18909: ŞH Vapur, 94971: Turyol, 64438: Dentur) ---
        {"from_stop_id": "87256", "to_stop_id": "12259", "transfer_type": "2", "min_transfer_time": "150"},          # M5 <-> Marmaray (2.5 min)
        {"from_stop_id": "12259", "to_stop_id": "87256", "transfer_type": "2", "min_transfer_time": "150"},
        {"from_stop_id": "12259", "to_stop_id": "18909", "transfer_type": "2", "min_transfer_time": "240"},          # Marmaray <-> Vapur (4 min)
        {"from_stop_id": "18909", "to_stop_id": "12259", "transfer_type": "2", "min_transfer_time": "240"},
        {"from_stop_id": "87256", "to_stop_id": "18909", "transfer_type": "2", "min_transfer_time": "240"},          # M5 <-> Vapur (4 min)
        {"from_stop_id": "18909", "to_stop_id": "87256", "transfer_type": "2", "min_transfer_time": "240"},
        {"from_stop_id": "12259", "to_stop_id": "94971", "transfer_type": "2", "min_transfer_time": "240"},
        {"from_stop_id": "94971", "to_stop_id": "12259", "transfer_type": "2", "min_transfer_time": "240"},

        # --- Söğütlüçeşme Hub (40098: Marmaray, mb_44: Metrobüs) ---
        {"from_stop_id": "40098", "to_stop_id": "mb_44", "transfer_type": "2", "min_transfer_time": "180"},          # Marmaray <-> Metrobüs (3 min)
        {"from_stop_id": "mb_44", "to_stop_id": "40098", "transfer_type": "2", "min_transfer_time": "180"},

        # --- Altunizade Hub (87259: M5, mb_40: Metrobüs) ---
        {"from_stop_id": "87259", "to_stop_id": "mb_40", "transfer_type": "2", "min_transfer_time": "180"},          # M5 <-> Metrobüs (3 min)
        {"from_stop_id": "mb_40", "to_stop_id": "87259", "transfer_type": "2", "min_transfer_time": "180"},

        # --- Uzunçayır / Ünalan Hub (18995: M4, mb_42: Metrobüs) ---
        {"from_stop_id": "18995", "to_stop_id": "mb_42", "transfer_type": "2", "min_transfer_time": "240"},          # M4 <-> Metrobüs (4 min)
        {"from_stop_id": "mb_42", "to_stop_id": "18995", "transfer_type": "2", "min_transfer_time": "240"},

        # --- Merter Hub (18960: M1A, mb_25: Metrobüs) ---
        {"from_stop_id": "18960", "to_stop_id": "mb_25", "transfer_type": "2", "min_transfer_time": "180"},          # M1A <-> Metrobüs (3 min)
        {"from_stop_id": "mb_25", "to_stop_id": "18960", "transfer_type": "2", "min_transfer_time": "180"},

        # --- Zeytinburnu Hub (18959: M1A, 19080: T1, mb_24: Metrobüs) ---
        {"from_stop_id": "18959", "to_stop_id": "mb_24", "transfer_type": "2", "min_transfer_time": "180"},          # M1A <-> Metrobüs (3 min)
        {"from_stop_id": "mb_24", "to_stop_id": "18959", "transfer_type": "2", "min_transfer_time": "180"},
        {"from_stop_id": "19080", "to_stop_id": "mb_24", "transfer_type": "2", "min_transfer_time": "180"},          # T1 <-> Metrobüs (3 min)
        {"from_stop_id": "mb_24", "to_stop_id": "19080", "transfer_type": "2", "min_transfer_time": "180"},
        {"from_stop_id": "18959", "to_stop_id": "19080", "transfer_type": "2", "min_transfer_time": "120"},          # M1A <-> T1 (2 min)
        {"from_stop_id": "19080", "to_stop_id": "18959", "transfer_type": "2", "min_transfer_time": "120"},

        # --- Şirinevler / Ataköy Hub (18974: M1A, mb_21: Metrobüs) ---
        {"from_stop_id": "18974", "to_stop_id": "mb_21", "transfer_type": "2", "min_transfer_time": "180"},          # M1A <-> Metrobüs (3 min)
        {"from_stop_id": "mb_21", "to_stop_id": "18974", "transfer_type": "2", "min_transfer_time": "180"},

        # --- Bostancı Hub (214375: Marmaray, 272186: M8, 18913: ŞH Vapur) ---
        {"from_stop_id": "214375", "to_stop_id": "272186", "transfer_type": "2", "min_transfer_time": "180"},        # Marmaray <-> M8 (3 min)
        {"from_stop_id": "272186", "to_stop_id": "214375", "transfer_type": "2", "min_transfer_time": "180"},
        {"from_stop_id": "214375", "to_stop_id": "18913", "transfer_type": "2", "min_transfer_time": "240"},         # Marmaray <-> Vapur (4 min)
        {"from_stop_id": "18913", "to_stop_id": "214375", "transfer_type": "2", "min_transfer_time": "240"},
        {"from_stop_id": "272186", "to_stop_id": "18913", "transfer_type": "2", "min_transfer_time": "240"},         # M8 <-> Vapur (4 min)
        {"from_stop_id": "18913", "to_stop_id": "272186", "transfer_type": "2", "min_transfer_time": "240"},

        # --- Kabataş Hub (19069: F1, 18954: T1, 18918: ŞH Vapur) ---
        {"from_stop_id": "19069", "to_stop_id": "18954", "transfer_type": "2", "min_transfer_time": "120"},          # F1 <-> T1 (2 min)
        {"from_stop_id": "18954", "to_stop_id": "19069", "transfer_type": "2", "min_transfer_time": "120"},
        {"from_stop_id": "19069", "to_stop_id": "18918", "transfer_type": "2", "min_transfer_time": "180"},          # F1 <-> Vapur (3 min)
        {"from_stop_id": "18918", "to_stop_id": "19069", "transfer_type": "2", "min_transfer_time": "180"},
        {"from_stop_id": "18954", "to_stop_id": "18918", "transfer_type": "2", "min_transfer_time": "180"},          # T1 <-> Vapur (3 min)
        {"from_stop_id": "18918", "to_stop_id": "18954", "transfer_type": "2", "min_transfer_time": "180"},

        # --- Aksaray Hub (18957: M1, 19073: T1) ---
        {"from_stop_id": "18957", "to_stop_id": "19073", "transfer_type": "2", "min_transfer_time": "300"},          # M1 <-> T1 (5 min)
        {"from_stop_id": "19073", "to_stop_id": "18957", "transfer_type": "2", "min_transfer_time": "300"},

        # --- TÜYAP Suburban Link (iett_290488: 300/401, mb_01: Metrobüs) ---
        {"from_stop_id": "iett_290488", "to_stop_id": "mb_01", "transfer_type": "2", "min_transfer_time": "180"},
        {"from_stop_id": "mb_01", "to_stop_id": "iett_290488", "transfer_type": "2", "min_transfer_time": "180"},

        # --- Istanbul Havalimanı (IST) Terminal Links ---
        {"from_stop_id": "m11_havalimani", "to_stop_id": "h2_ist_havalimani", "transfer_type": "2", "min_transfer_time": "120"},
        {"from_stop_id": "h2_ist_havalimani", "to_stop_id": "m11_havalimani", "transfer_type": "2", "min_transfer_time": "120"},
        {"from_stop_id": "iett_5251000", "to_stop_id": "h2_ist_havalimani", "transfer_type": "2", "min_transfer_time": "180"},   # Garaj lines (H-1, H-3, H-6, H-9, H-11)
        {"from_stop_id": "h2_ist_havalimani", "to_stop_id": "iett_5251000", "transfer_type": "2", "min_transfer_time": "180"},

        # --- Sabiha Gökçen Havalimanı (SAW) Terminal Links ---
        {"from_stop_id": "m4_saw", "to_stop_id": "iett_897", "transfer_type": "2", "min_transfer_time": "120"},                   # M4 <-> İETT Bus Terminus
        {"from_stop_id": "iett_897", "to_stop_id": "m4_saw", "transfer_type": "2", "min_transfer_time": "120"},
        {"from_stop_id": "m4_saw", "to_stop_id": "iett_6171326", "transfer_type": "2", "min_transfer_time": "120"},
        {"from_stop_id": "iett_6171326", "to_stop_id": "m4_saw", "transfer_type": "2", "min_transfer_time": "120"}
    ]
    safe_append_csv("transfers.txt", ["from_stop_id", "to_stop_id", "transfer_type", "min_transfer_time"], transfers)

    # 6. REPACKAGE gtfs-istanbul.zip
    print("  📦 gtfs-istanbul.zip yeniden paketleniyor...")
    with zipfile.ZipFile(ROUTER_ZIP, "w", zipfile.ZIP_DEFLATED) as zf:
        for fname in ["agency.txt", "calendar.txt", "routes.txt", "stops.txt", "trips.txt", "stop_times.txt", "shapes.txt", "frequencies.txt", "transfers.txt"]:
            fpath = os.path.join(TEMP_DIR, fname)
            if os.path.exists(fpath):
                zf.write(fpath, arcname=fname)
    print(f"  ✔ {ROUTER_ZIP} başarıyla güncellendi ({os.path.getsize(ROUTER_ZIP) // 1024 // 1024} MB).")

if __name__ == "__main__":
    inject_all()
