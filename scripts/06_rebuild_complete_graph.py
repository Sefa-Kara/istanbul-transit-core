from pathlib import Path
import os
import sys
import subprocess
import time

BASE_DIR = str(Path(__file__).resolve().parent.parent)
ROUTER_DIR = os.path.join(BASE_DIR, "data", "router")
JAR_PATH = os.path.join(BASE_DIR, "bin", "otp-2.6.0-shaded.jar")

def run_step(step_name, cmd):
    print(f"\n=======================================================")
    print(f"▶ {step_name}")
    print(f"=======================================================")
    t0 = time.time()
    env = os.environ.copy()
    env["PYTHONPATH"] = BASE_DIR
    res = subprocess.run(cmd, shell=True, cwd=BASE_DIR, env=env)
    if res.returncode != 0:
        print(f"❌ HATA: {step_name} başarısız oldu (kod: {res.returncode})")
        sys.exit(res.returncode)
    print(f"✔ {step_name} tamamlandı ({time.time() - t0:.1f}s)")

def main():
    print("🚀 TÜM İSTANBUL GTFS VE OTP GRAFİK DERLEMESİ BAŞLATILIYOR")
    t_start = time.time()

    # Step 1: Merge raw datasets (with complete stop_times and sequence sorting)
    run_step("1. GTFS Birleştirme (6.1M Satır & 135K Sefer)", "python3 scripts/02_merge_gtfs.py")

    # Step 2: Inject M11 Metro, Havaist, H-2 and Transfers
    run_step("2. Havalimanı (M11, Havaist, H-2) & İstasyon İçi Yürüme Enjeksiyonu", "python3 scripts/04_inject_airport_and_transfers.py")

    # Step 3: Inject 7/24 Metrobüs Corridor
    run_step("3. 7/24 Metrobüs (34G) Enjeksiyonu ve GTFS ZIP Paketleme", "python3 scripts/05_inject_metrobus_24_7.py")

    # Step 4: Build OTP graph
    print(f"\n=======================================================")
    print("▶ 4. OTP Grafiği Derleniyor (graph.obj)...")
    print(f"=======================================================")
    t_otp = time.time()
    otp_cmd = f"java -Xmx6G -jar {JAR_PATH} --build --save {ROUTER_DIR}"
    res = subprocess.run(otp_cmd, shell=True, cwd=BASE_DIR)
    if res.returncode != 0:
        print(f"❌ OTP Graf derleme başarısız oldu (kod: {res.returncode})")
        sys.exit(res.returncode)
    print(f"✔ OTP Grafiği derlendi ({time.time() - t_otp:.1f}s)")

    print(f"\n🎉 TÜM GRAF DERLEME İŞLEMİ BAŞARIYLA TAMAMLANDI! (Toplam süre: {time.time() - t_start:.1f}s)")

if __name__ == "__main__":
    main()
