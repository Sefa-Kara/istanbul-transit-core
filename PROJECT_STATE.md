# PROJECT STATE — ISTANBUL TRANSIT CORE
**Son Güncelleme:** 2026-10-14 (Mobile PWA & Touch UI Transformation)
**Dizin:** `.` (istanbul-transit-core root)

---

## 1. PROJE ÖZETİ & MİMARİ
İstanbul için sıfır bulut API bağımlılığı (100% local-first) ile çalışan, Google Maps ve Moovit alternatifi multimodal toplu taşıma navigasyon motoru ve Progressive Web App (PWA).

* **Backend Engine:** OpenTripPlanner 2.6 (OTP) + Java 21 (`bin/otp-2.6.0-shaded.jar`)
* **API Katmanı:** Python FastAPI (`src/api/`, `src/api/main.py`)
* **Frontend UI & PWA:** Modern Leaflet & Vanilla JS (`static/`), Swipeable Bottom Sheet (Peek / Half / Full snap states), tek dokunuşla canlı GPS FAB, Service Worker (`sw.js`), Web App Manifest (`manifest.json`), Apple Touch ve Retina ikonlar.
* **Sentetik GTFS & Graph:** 
  * 7/24 Metrobüs, M11 Gayrettepe-İstanbul Havalimanı, M4 Sabiha Gökçen ve Havaist sentetik sefer enjeksiyonları (`data/gtfs/`).
  * `transfers.txt` ve yürüme yetişme (catchable) kontrolleri derlendi.
* **Trafik & Radar:** 3000+ İETT aracından gerçek zamanlı FCD trafik yoğunluğu (TCC) ve canlı araç radarı (`src/traffic/`).
* **Canlı Dağıtım:** Hugging Face Spaces (16 GB RAM, 7/24 kesintisiz canlı):
  👉 `https://th3g3nt13man-istanbul-transit-core.hf.space/`

---

## 2. TAMAMLANAN KRİTİK AŞAMALAR
1. OTP 2.6 graph derlemesi ve 8000/8080 port yapılandırması tamamlandı ve doğrulandı.
2. Havalimanı (M11) ve Sabiha Gökçen bağlantı körlükleri sentetik GTFS ile çözüldü.
3. Moovit kalitesinde koridor hat gruplama ve mikro-aktarma budaması eklendi.
4. Modern kullanıcı arayüzü (Autocomplete + Geolocation + Hat Renkleri) stabilize edildi.
5. 1000 rastgele koordinat çiftinde Google Maps & Moovit kıyaslama benchmark test altyapısı (`scripts/benchmark_1000.py`) kuruldu.
6. **Mobile PWA & Swipeable Bottom Sheet Dönüşümü (Tamamlandı):**
   - `manifest.json` (standalone display, portrait-primary, theme_color, app shortcuts) oluşturuldu.
   - iOS Safari (`apple-mobile-web-app-capable`, `apple-touch-icon`, `viewport-fit=cover`) ve Android Chrome desteği eklendi.
   - Çevrimdışı kabuk ve hızlı açılış için `sw.js` Service Worker devreye alındı.
   - Parmakla kaydırılabilen (Swipeable Touch Drag) 3 seviyeli modern Bottom Sheet (`peek`, `half`, `full`) ve yüzen FAB kontrolleri (`mobileLocateFab`, `mobileSheetFab`) eklendi.
   - PWA ve statik endpoint testleri (`tests/test_pwa_integration.py`, `tests/test_api_static_pwa.py`) 100% başarıyla geçti.

---

## 3. MEVCUT AÇIK GÖREVLER & SIRADAKİ ADIMLAR
* **Adım 1:** Hugging Face Spaces üzerindeki canlı PWA deneyiminin mobil cihazlarda (iOS Safari / Android Chrome) kullanıcı tarafından test edilmesi.
* **Adım 2:** İsteğe bağlı push notification (İETT sefer gecikmeleri ve hat uyarıları) altyapısının eklenmesi.

---

## 4. ÇALIŞTIRMA & TEST KOMUTLARI
* **Sistemi Başlat:** `./start.sh` (OTP 8080 + FastAPI 8000 başlatır)
* **Sistemi Durdur:** `./stop.sh`
* **PWA & UI Testleri:** `python3 -m unittest tests/test_pwa_integration.py tests/test_api_static_pwa.py`
* **Benchmark:** `python3 scripts/benchmark_1000.py`
* **Deploy Space:** `git push space main`
