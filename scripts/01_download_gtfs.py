from pathlib import Path
import os
import ssl
import urllib.request
import json
import csv

BASE_DIR = str(Path(__file__).resolve().parent.parent)
RAW_DIR = os.path.join(BASE_DIR, "data", "raw")
PT_DIR = os.path.join(RAW_DIR, "ibb_pt")
IETT_DIR = os.path.join(RAW_DIR, "ibb_iett")

os.makedirs(PT_DIR, exist_ok=True)
os.makedirs(IETT_DIR, exist_ok=True)

ctx = ssl._create_unverified_context()

def get_package_resources(pkg_id):
    url = f"https://data.ibb.gov.tr/api/3/action/package_show?id={pkg_id}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, context=ctx) as resp:
        data = json.load(resp)["result"]
        return data.get("resources", [])

def download_file(url, dest_path):
    print(f"Downloading {url} -> {dest_path}...")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, context=ctx) as resp, open(dest_path, "wb") as f:
        while chunk := resp.read(1024 * 1024):
            f.write(chunk)
    print(f"Done: {dest_path} ({os.path.getsize(dest_path)} bytes)")

print("=== 1. Fetching Public Transport GTFS Resources (Metro, Ferries, Marmaray) ===")
pt_resources = get_package_resources("121a9892-7945-419a-9b89-49f6083926df")
for r in pt_resources:
    name = r["name"].strip()
    fmt = r.get("format", "").upper()
    url = r["url"]
    if fmt == "CSV" or name.endswith(".csv"):
        filename = f"{name}.csv" if not name.endswith(".csv") else name
        download_file(url, os.path.join(PT_DIR, filename))

print("\n=== 2. Fetching IETT GTFS Resources (Buses, Metrobus) ===")
iett_resources = get_package_resources("8540e256-6df5-4719-85bc-e64e91508ede")
for r in iett_resources:
    name = r["name"].strip()
    fmt = r.get("format", "").upper()
    url = r["url"]
    # Download CSVs directly; skip stop_times.zip if stop_times.csv is already available
    if (fmt == "CSV" or name.endswith(".csv")) and not name.endswith(".zip"):
        filename = f"{name}.csv" if not name.endswith(".csv") else name
        download_file(url, os.path.join(IETT_DIR, filename))

print("\nAll raw GTFS datasets downloaded successfully!")
