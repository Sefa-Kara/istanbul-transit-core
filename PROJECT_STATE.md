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
7. **Canlı Hugging Face Space & GitHub Doğrulaması (100% Başarılı):**
   - GitHub `origin/main` README dosyası YAML tablosundan tamamen arındırıldı; `scripts/verify_github_readme.py` ile görsel olarak temiz (`CLEAN`) olduğu kanıtlandı (`github_readme_view.png`).
   - Hugging Face Spaces (`space/main`) sıfır hata ile `Stage: RUNNING` durumuna geçti (`dc76231` / `3eac5c3`).
   - `scripts/test_navigation_buttons.py` ile Playwright üzerinde tüm butonlar (4 strateji pili, 5 mod çipi, 4 zaman çipi, FAB çekmece butonu, tutma kolu ve rota otomatik doldurma) canlı Space üzerinde tek tek tıklanarak %100 doğrulandı (`mobile_pwa_verified.png`).
   - Canlı `/api/plan` rotalama motoru test edildi ve anlık rota hesaplaması başarıyla teyit edildi.

---

## 3. MEVCUT AÇIK GÖREVLER & SIRADAKİ ADIMLAR
* **Adım 1:** Kullanıcının telefonundan (iPhone / Android) PWA uygulamasını "Ana Ekrana Ekle" diyerek yerel mobil uygulama olarak deneyimlemesi.
* **Adım 2:** İsteğe bağlı push notification veya çevrimdışı önbellekleme genişletmeleri.

---

## 4. ÇALIŞTIRMA & TEST KOMUTLARI
* **Sistemi Başlat:** `./start.sh` (OTP 8080 + FastAPI 8000 başlatır)
* **Sistemi Durdur:** `./stop.sh`
* **PWA & UI Testleri:** `python3 -m unittest tests/test_pwa_integration.py tests/test_api_static_pwa.py`
* **E2E Dokunmatik Buton Testi:** `python3 scripts/test_navigation_buttons.py`
* **GitHub Görsel Doğrulama:** `python3 scripts/verify_github_readme.py`
* **Deploy Space:** `git push space hf-space:main`
