from pathlib import Path
import os
import csv
import zipfile
import re
from datetime import datetime

import sys

BASE_DIR = str(Path(__file__).resolve().parent.parent)
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from src.utils.text_utils import repair_turkish_mojibake, MOJIBAKE_MAP

RAW_DIR = os.path.join(BASE_DIR, "data", "raw")
PT_DIR = os.path.join(RAW_DIR, "ibb_pt")
IETT_DIR = os.path.join(RAW_DIR, "ibb_iett")
ROUTER_DIR = os.path.join(BASE_DIR, "data", "router")
OUTPUT_ZIP = os.path.join(ROUTER_DIR, "gtfs-istanbul.zip")
TEMP_DIR = os.path.join(BASE_DIR, "data", "gtfs_temp")

os.makedirs(TEMP_DIR, exist_ok=True)

def fix_mojibake(text):
    return repair_turkish_mojibake(text)


def sanitize_coord(val, is_lat=True):
    val = str(val or "").strip().replace(" ", "")
    digits = val.replace(".", "").replace(",", "")
    if is_lat:
        if digits.startswith("40") or digits.startswith("41"):
            return f"{digits[:2]}.{digits[2:8]}"
    else:
        if digits.startswith("28") or digits.startswith("29") or digits.startswith("27") or digits.startswith("30"):
            return f"{digits[:2]}.{digits[2:8]}"
    return None

def parse_time(t_str):
    if not t_str or not t_str.strip():
        return None
    parts = t_str.strip().split(":")
    if len(parts) >= 3:
        try:
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(float(parts[2]))
        except ValueError:
            return None
    elif len(parts) == 2:
        try:
            return int(parts[0]) * 3600 + int(parts[1]) * 60
        except ValueError:
            return None
    return None

def format_time(sec):
    h = sec // 3600
    m = (sec % 3600) // 60
    s = sec % 60
    return f"{h:02d}:{m:02d}:{s:02d}"

def write_gtfs_csv(filename, fieldnames, rows):
    out_path = os.path.join(TEMP_DIR, filename)
    with open(out_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=",")
        writer.writeheader()
        writer.writerows(rows)
    print(f"  Wrote {filename}: {len(rows)} records")

def process():
    print("=== Processing & Merging GTFS Datasets ===")

    # 1. AGENCIES
    agencies = [
        {"agency_id": "11", "agency_name": "Metro İstanbul", "agency_url": "https://www.metro.istanbul", "agency_timezone": "Europe/Istanbul", "agency_lang": "tr"},
        {"agency_id": "4", "agency_name": "TCDD Taşımacılık (Marmaray)", "agency_url": "https://www.marmaray.gov.tr", "agency_timezone": "Europe/Istanbul", "agency_lang": "tr"},
        {"agency_id": "6", "agency_name": "Şehir Hatları", "agency_url": "https://sehirhatlari.istanbul", "agency_timezone": "Europe/Istanbul", "agency_lang": "tr"},
        {"agency_id": "20", "agency_name": "İDO", "agency_url": "https://www.ido.com.tr", "agency_timezone": "Europe/Istanbul", "agency_lang": "tr"},
        {"agency_id": "48", "agency_name": "Turyol", "agency_url": "https://www.turyol.com", "agency_timezone": "Europe/Istanbul", "agency_lang": "tr"},
        {"agency_id": "33", "agency_name": "Dentur Avrasya", "agency_url": "https://www.denturavrasya.com", "agency_timezone": "Europe/Istanbul", "agency_lang": "tr"},
        {"agency_id": "37", "agency_name": "İstanbul Minibüsleri", "agency_url": "https://tuhim.ibb.gov.tr", "agency_timezone": "Europe/Istanbul", "agency_lang": "tr"},
        {"agency_id": "19", "agency_name": "Taksi Dolmuş", "agency_url": "https://tuhim.ibb.gov.tr", "agency_timezone": "Europe/Istanbul", "agency_lang": "tr"},
        {"agency_id": "iett", "agency_name": "İETT Genel Müdürlüğü", "agency_url": "https://iett.istanbul", "agency_timezone": "Europe/Istanbul", "agency_lang": "tr"},
    ]
    write_gtfs_csv("agency.txt", ["agency_id", "agency_name", "agency_url", "agency_timezone", "agency_lang"], agencies)

    # 2. CALENDAR (Active across 2026 - 2027)
    calendars = []
    seen_services = set()
    for s_id, m, tu, w, th, f, sa, su in [
        ("WEEKDAYS", 1, 1, 1, 1, 1, 0, 0),
        ("SATURDAY", 0, 0, 0, 0, 0, 1, 0),
        ("SUNDAY", 0, 0, 0, 0, 0, 0, 1),
        ("ALL_WEEK", 1, 1, 1, 1, 1, 1, 1),
        ("0", 1, 1, 1, 1, 1, 0, 0),
        ("6", 0, 0, 0, 0, 0, 1, 0),
        ("7", 0, 0, 0, 0, 0, 0, 1),
    ]:
        calendars.append({
            "service_id": s_id,
            "monday": m, "tuesday": tu, "wednesday": w, "thursday": th, "friday": f,
            "saturday": sa, "sunday": su,
            "start_date": "20260101", "end_date": "20271231"
        })
        seen_services.add(s_id)

    # Read existing services from PT calendar
    pt_cal_file = os.path.join(PT_DIR, "calendar.csv")
    if os.path.exists(pt_cal_file):
        with open(pt_cal_file, "r", encoding="iso-8859-9", errors="replace") as fp:
            for r in csv.DictReader(fp):
                sid = (r.get("service_id") or "").strip()
                if sid and sid not in seen_services:
                    seen_services.add(sid)
                    calendars.append({
                        "service_id": sid,
                        "monday": r.get("monday", "1"),
                        "tuesday": r.get("tuesday", "1"),
                        "wednesday": r.get("wednesday", "1"),
                        "thursday": r.get("thursday", "1"),
                        "friday": r.get("friday", "1"),
                        "saturday": r.get("saturday", "1"),
                        "sunday": r.get("sunday", "1"),
                        "start_date": "20260101",
                        "end_date": "20271231"
                    })
    write_gtfs_csv("calendar.txt", ["service_id", "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday", "start_date", "end_date"], calendars)

    # 3. ROUTES
    routes = []
    seen_routes = set()

    # PT Routes (Metro, Tramway, Funicular, Ferries, etc.)
    with open(os.path.join(PT_DIR, "routes.csv"), "r", encoding="iso-8859-9", errors="replace") as fp:
        for r in csv.DictReader(fp):
            rid = (r.get("route_id") or "").strip()
            aid = (r.get("agency_id") or "").strip()
            sname = fix_mojibake(r.get("route_short_name") or "")
            lname = fix_mojibake(r.get("route_long_name") or "")
            if rid == "1294":
                sname = "M4"
                lname = "Kadıköy - Sabiha Gökçen Havalimanı"
            elif not sname and not lname:
                sname = rid
                lname = rid
            elif not sname:
                sname = lname
            elif not lname:
                lname = sname
            rtype = (r.get("route_type") or "3").strip()
            if rtype not in ["0", "1", "2", "3", "4", "5", "6", "7", "11", "12"]:
                rtype = "3"
            if rid and rid not in seen_routes:
                seen_routes.add(rid)
                routes.append({
                    "route_id": rid,
                    "agency_id": aid if aid in ["4", "6", "11", "19", "20", "33", "37", "48"] else "11",
                    "route_short_name": sname,
                    "route_long_name": lname,
                    "route_type": rtype,
                    "route_color": (r.get("route_color") or "0055AA").strip(),
                    "route_text_color": (r.get("route_text_color") or "FFFFFF").strip()
                })

    # IETT Routes (Buses & Metrobus)
    with open(os.path.join(IETT_DIR, "routes.csv"), "r", encoding="utf-8-sig", errors="replace") as fp:
        for r in csv.DictReader(fp, delimiter=";"):
            rid = (r.get("route_id") or "").strip()
            if not rid: continue
            rid_full = f"iett_{rid}"
            sname = fix_mojibake(r.get("route_short_name") or "")
            lname = fix_mojibake(r.get("route_long_name") or "")
            if not sname and not lname:
                sname = rid
                lname = rid
            elif not sname:
                sname = lname
            elif not lname:
                lname = sname
            if rid_full not in seen_routes:
                seen_routes.add(rid_full)
                is_metrobus = sname.startswith("34") and len(sname) <= 4
                color = "E60000" if is_metrobus else "FFCC00"
                routes.append({
                    "route_id": rid_full,
                    "agency_id": "iett",
                    "route_short_name": sname,
                    "route_long_name": lname,
                    "route_type": "3",
                    "route_color": color,
                    "route_text_color": "FFFFFF" if is_metrobus else "000000"
                })
    write_gtfs_csv("routes.txt", ["route_id", "agency_id", "route_short_name", "route_long_name", "route_type", "route_color", "route_text_color"], routes)

    # 4. STOPS
    stops = []
    seen_stops = set()

    with open(os.path.join(PT_DIR, "stops.csv"), "r", encoding="iso-8859-9", errors="replace") as fp:
        for r in csv.DictReader(fp):
            sid = (r.get("stop_id") or "").strip()
            lat = sanitize_coord(r.get("stop_lat"), is_lat=True)
            lon = sanitize_coord(r.get("stop_lon"), is_lat=False)
            name = fix_mojibake(r.get("stop_name") or "") or f"Durak {sid}"
            if sid and sid not in seen_stops and lat and lon:
                seen_stops.add(sid)
                stops.append({
                    "stop_id": sid,
                    "stop_name": name,
                    "stop_lat": lat,
                    "stop_lon": lon,
                    "location_type": (r.get("location_type") or "0").strip()
                })

    with open(os.path.join(IETT_DIR, "stops.csv"), "r", encoding="utf-8-sig", errors="replace") as fp:
        for r in csv.DictReader(fp, delimiter=";"):
            sid = (r.get("stop_id") or "").strip()
            lat = sanitize_coord(r.get("stop_lat"), is_lat=True)
            lon = sanitize_coord(r.get("stop_lon"), is_lat=False)
            name = fix_mojibake(r.get("stop_name") or "") or f"Durak {sid}"
            if sid and lat and lon:
                sid_full = f"iett_{sid}"
                if sid_full not in seen_stops:
                    seen_stops.add(sid_full)
                    stops.append({
                        "stop_id": sid_full,
                        "stop_name": name,
                        "stop_lat": lat,
                        "stop_lon": lon,
                        "location_type": "0"
                    })
    write_gtfs_csv("stops.txt", ["stop_id", "stop_name", "stop_lat", "stop_lon", "location_type"], stops)

    # 5. TRIPS
    trips = []
    seen_trips = set()
    trip_to_route = {}

    with open(os.path.join(PT_DIR, "trips.csv"), "r", encoding="iso-8859-9", errors="replace") as fp:
        for r in csv.DictReader(fp):
            tid = (r.get("trip_id") or "").strip()
            rid = (r.get("route_id") or "").strip()
            sid = (r.get("service_id") or "").strip()
            if rid == "1294":
                continue  # Full 23-station schedule injected in 04_inject_airport_and_transfers.py
            headsign = fix_mojibake(r.get("trip_headsign") or "") or "İstanbul"
            if tid and rid in seen_routes:
                seen_trips.add(tid)
                trip_to_route[tid] = rid
                trips.append({
                    "route_id": rid,
                    "service_id": sid if sid in seen_services else "ALL_WEEK",
                    "trip_id": tid,
                    "trip_headsign": headsign,
                    "direction_id": (r.get("direction_id") or "0").strip(),
                    "shape_id": (r.get("shape_id") or "").strip()
                })

    with open(os.path.join(IETT_DIR, "trips.csv"), "r", encoding="utf-8-sig", errors="replace") as fp:
        for r in csv.DictReader(fp, delimiter=";"):
            tid = (r.get("trip_id") or "").strip()
            rid = (r.get("route_id") or "").strip()
            sid = (r.get("service_id") or "").strip()
            rid_full = f"iett_{rid}"
            tid_full = f"iett_{tid}"
            headsign = fix_mojibake(r.get("trip_headsign") or "") or "İstanbul"
            if tid_full and rid_full in seen_routes:
                seen_trips.add(tid_full)
                trip_to_route[tid_full] = rid_full
                trips.append({
                    "route_id": rid_full,
                    "service_id": sid if sid in seen_services else "0",
                    "trip_id": tid_full,
                    "trip_headsign": headsign,
                    "direction_id": (r.get("direction_id") or "0").strip(),
                    "shape_id": ""
                })
    write_gtfs_csv("trips.txt", ["route_id", "service_id", "trip_id", "trip_headsign", "direction_id", "shape_id"], trips)

    # 6. STOP TIMES (With Linear Interpolation for IETT)
    print("  Processing Stop Times...")
    out_st_path = os.path.join(TEMP_DIR, "stop_times.txt")
    total_st = 0

    with open(out_st_path, "w", encoding="utf-8", newline="") as out_fp:
        writer = csv.DictWriter(out_fp, fieldnames=["trip_id", "arrival_time", "departure_time", "stop_id", "stop_sequence"], delimiter=",")
        writer.writeheader()

        # Stream PT stop_times directly
        with open(os.path.join(PT_DIR, "stop_times.csv"), "r", encoding="iso-8859-9", errors="replace") as fp:
            for r in csv.DictReader(fp):
                tid = (r.get("trip_id") or "").strip()
                sid = (r.get("stop_id") or "").strip()
                arr = (r.get("arrival_time") or "").strip()
                dep = (r.get("departure_time") or "").strip()
                seq = (r.get("stop_sequence") or "1").strip()
                if tid in seen_trips and sid in seen_stops and arr and dep:
                    writer.writerow({
                        "trip_id": tid,
                        "arrival_time": arr,
                        "departure_time": dep,
                        "stop_id": sid,
                        "stop_sequence": seq
                    })
                    total_st += 1

        # Process IETT stop_times with interpolation
        print("  Interpolating IETT intermediate bus stop times...")
        current_trip_id = None
        current_trip_stops = []

        def flush_trip(t_rows):
            nonlocal total_st
            if not t_rows:
                return
            # Crucial: Sort by stop_sequence so sequence 1 is always at index 0
            t_rows.sort(key=lambda x: int(x.get("stop_sequence", 0)))
            n = len(t_rows)
            t_start = parse_time(t_rows[0].get("departure_time") or t_rows[0].get("arrival_time"))
            t_end = parse_time(t_rows[-1].get("arrival_time") or t_rows[-1].get("departure_time"))

            if t_start is None:
                return
            if t_end is None or t_end <= t_start:
                # Default 90s per stop if no end time
                t_end = t_start + max(1, n - 1) * 90

            total_duration = t_end - t_start
            for idx, item in enumerate(t_rows):
                fraction = idx / max(1, n - 1)
                sec = int(t_start + fraction * total_duration)
                time_str = format_time(sec)
                writer.writerow({
                    "trip_id": item["trip_id"],
                    "arrival_time": time_str,
                    "departure_time": time_str,
                    "stop_id": item["stop_id"],
                    "stop_sequence": item["stop_sequence"]
                })
                total_st += 1

        iett_st_txt = os.path.join(IETT_DIR, "stop_times.txt")
        iett_st_file = iett_st_txt if os.path.exists(iett_st_txt) else os.path.join(IETT_DIR, "stop_times.csv")
        delimiter = "," if iett_st_file.endswith(".txt") else ";"
        print(f"  Reading IETT stop times from {os.path.basename(iett_st_file)} (delimiter: '{delimiter}')...")

        with open(iett_st_file, "r", encoding="utf-8-sig", errors="replace") as fp:
            for r in csv.DictReader(fp, delimiter=delimiter):
                raw_tid = (r.get("trip_id") or "").strip()
                if not raw_tid: continue
                tid = f"iett_{raw_tid}"
                raw_sid = (r.get("stop_id") or "").strip()
                sid = f"iett_{raw_sid}"
                seq = (r.get("stop_sequence") or "1").strip()
                arr = (r.get("arrival_time") or "").strip()
                dep = (r.get("departure_time") or "").strip()

                if tid not in seen_trips or sid not in seen_stops:
                    continue

                if tid != current_trip_id:
                    flush_trip(current_trip_stops)
                    current_trip_id = tid
                    current_trip_stops = []

                current_trip_stops.append({
                    "trip_id": tid,
                    "stop_id": sid,
                    "stop_sequence": seq,
                    "arrival_time": arr,
                    "departure_time": dep
                })

            flush_trip(current_trip_stops)

    print(f"  Wrote stop_times.txt: {total_st} records")

    # 7. SHAPES (Optional, copy from PT)
    pt_shapes_file = os.path.join(PT_DIR, "shapes.csv")
    if os.path.exists(pt_shapes_file):
        out_shapes_path = os.path.join(TEMP_DIR, "shapes.txt")
        shapes_count = 0
        with open(pt_shapes_file, "r", encoding="iso-8859-9", errors="replace") as in_fp, \
             open(out_shapes_path, "w", encoding="utf-8", newline="") as out_fp:
            writer = csv.DictWriter(out_fp, fieldnames=["shape_id", "shape_pt_lat", "shape_pt_lon", "shape_pt_sequence"], delimiter=",")
            writer.writeheader()
            for r in csv.DictReader(in_fp):
                writer.writerow({
                    "shape_id": (r.get("shape_id") or "").strip(),
                    "shape_pt_lat": (r.get("shape_pt_lat") or "").strip(),
                    "shape_pt_lon": (r.get("shape_pt_lon") or "").strip(),
                    "shape_pt_sequence": (r.get("shape_pt_sequence") or "").strip()
                })
                shapes_count += 1
        print(f"  Wrote shapes.txt: {shapes_count} records")

    # 7b. FREQUENCIES (Metro & Marmaray headways)
    pt_freq_file = os.path.join(PT_DIR, "frequencies.csv")
    if os.path.exists(pt_freq_file):
        out_freq_path = os.path.join(TEMP_DIR, "frequencies.txt")
        freq_count = 0
        with open(pt_freq_file, "r", encoding="iso-8859-9", errors="replace") as in_fp, \
             open(out_freq_path, "w", encoding="utf-8", newline="") as out_fp:
            writer = csv.DictWriter(out_fp, fieldnames=["trip_id", "start_time", "end_time", "headway_secs", "exact_times"], delimiter=",")
            writer.writeheader()
            for r in csv.DictReader(in_fp):
                tid = (r.get("trip_id") or "").strip()
                if tid in seen_trips:
                    writer.writerow({
                        "trip_id": tid,
                        "start_time": (r.get("start_time") or "").strip(),
                        "end_time": (r.get("end_time") or "").strip(),
                        "headway_secs": (r.get("headway_secs") or "300").strip(),
                        "exact_times": (r.get("exact_times") or "0").strip()
                    })
                    freq_count += 1
        print(f"  Wrote frequencies.txt: {freq_count} records")

    # 8. BUNDLE INTO FINAL GTFS ZIP
    print(f"\nCompressing into {OUTPUT_ZIP}...")
    files_to_zip = ["agency.txt", "calendar.txt", "routes.txt", "stops.txt", "trips.txt", "stop_times.txt"]
    if os.path.exists(os.path.join(TEMP_DIR, "shapes.txt")):
        files_to_zip.append("shapes.txt")
    if os.path.exists(os.path.join(TEMP_DIR, "frequencies.txt")):
        files_to_zip.append("frequencies.txt")

    with zipfile.ZipFile(OUTPUT_ZIP, "w", zipfile.ZIP_DEFLATED) as zf:
        for fname in files_to_zip:
            fpath = os.path.join(TEMP_DIR, fname)
            if os.path.exists(fpath):
                zf.write(fpath, arcname=fname)
    print(f"Success! Generated {OUTPUT_ZIP} ({os.path.getsize(OUTPUT_ZIP) / (1024*1024):.2f} MB)")

if __name__ == "__main__":
    process()
