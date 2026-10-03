# PROJECT STATE — ISTANBUL TRANSIT CORE
**Son Güncelleme:** 2026-10-03 (Final Production Release)
**Dizin:** `.` (istanbul-transit-core root)

---

## 1. PROJE ÖZETİ & MİMARİ
İstanbul için sıfır bulut API bağımlılığı (100% local-first) ile çalışan, Google Maps ve Moovit alternatifi multimodal toplu taşıma navigasyon motoru.

* **Backend Engine:** OpenTripPlanner 2.6 (OTP) + Java 21 (`bin/otp-2.6.0-shaded.jar`)
* **API Katmanı:** Python FastAPI (`src/api/`, `main.py`)
* **Frontend UI:** Modern Leaflet & Vanilla JS (`static/`), anlık durak/mekan otomatik tamamlama, tek tıkla canlı GPS, renk kodlu polylines, vapur/otobüs/metro hat filtreleme.
* **Sentetik GTFS & Graph:** 
  * 7/24 Metrobüs, M11 Gayrettepe-İstanbul Havalimanı, M4 Sabiha Gökçen ve Havaist sentetik sefer enjeksiyonları (`data/gtfs/`).
  * `transfers.txt` ve yürüme yetişme (catchable) kontrolleri derlendi.
* **Trafik & Radar:** 3000+ İETT aracından gerçek zamanlı FCD trafik yoğunluğu (TCC) ve canlı araç radarı (`src/traffic/`).

---

## 2. TAMAMLANAN KRİTİK AŞAMALAR
1. OTP 2.6 graph derlemesi ve 8000/8080 port yapılandırması tamamlandı ve doğrulandı.
2. Havalimanı (M11) ve Sabiha Gökçen bağlantı körlükleri sentetik GTFS ile çözüldü.
3. Moovit kalitesinde koridor hat gruplama ve mikro-aktarma budaması eklendi.
4. Modern kullanıcı arayüzü (Autocomplete + Geolocation + Hat Renkleri) stabilize edildi.
5. 1000 rastgele koordinat çiftinde Google Maps & Moovit kıyaslama benchmark test altyapısı (`scripts/benchmark_1000.py`) kuruldu.

---

## 3. MEVCUT AÇIK GÖREVLER & SIRADAKİ ADIMLAR
* **Adım 1:** 1000'li koordinat benchmark test sonuçlarının detaylı metrik analizi ve uç nokta rota doğrulaması.
* **Adım 2:** GitHub açık kaynak yayını hazırlığı (Lisans, README, Dockerfile veya standalone servis paketleme).
* **Adım 3:** Mobil/PWA uyumluluğu için responsive UI rötuşları.

---

## 4. ÇALIŞTIRMA & TEST KOMUTLARI
* **Sistemi Başlat:** `./start.sh` (OTP 8080 + FastAPI 8000 başlatır)
* **Sistemi Durdur:** `./stop.sh`
* **Testleri Koş:** `pytest tests/ -v`
* **Benchmark:** `python3 scripts/benchmark_1000.py`

---
> **Not:** Yeni bir sohbete geçildiğinde bu dosya okunarak hiçbir bağlam kaybı olmadan doğrudan Sıradaki Adımlardan devam edilebilir.
