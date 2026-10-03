<div align="center">

# 🚆 Istanbul Transit Navigator (Yerel Toplu Taşıma Motoru)

**İstanbul İçin 100% Yerel, Açık Kaynaklı Multimodal Rotalama Motoru ve Canlı Araç Radarı**

[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![OpenTripPlanner](https://img.shields.io/badge/OpenTripPlanner-2.6.0-blue.svg)](https://www.opentripplanner.org/)
[![Lisans: MIT](https://img.shields.io/badge/Lisans-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB.svg?logo=python&logoColor=white)](https://python.org)
[![Docker](https://img.shields.io/badge/Docker-Hazır-2496ED.svg?logo=docker&logoColor=white)](https://www.docker.com/)
[![Sıfır Ücretli API](https://img.shields.io/badge/API-100%25%20Ücretsiz%20%26%20Yerel-success.svg)](#temel-ozellikler)

*İstanbul'un karmaşık toplu taşıma ağını (Metro, Metrobüs, Marmaray, Tramvay, Şehir Hatları Vapurları, İETT Otobüsleri ve Havaist) ücretli bulut API'lerine (Google Maps, Moovit vb.) kuruş ödemeden, gizliliği koruyarak ve sıfır gecikmeyle çözen açık kaynaklı navigasyon platformu.*

[🇹🇷 Türkçe Dokümantasyon](README_TR.md) • [🇬🇧 English Documentation](README.md) • [🚀 Canlı Demo](https://huggingface.co/spaces/Th3G3nt13man/istanbul-transit-core) • [📊 Benchmark Raporu](#benchmark-raporu) • [⚡ Hızlı Kurulum](#hizli-kurulum) • [📱 REST API](#rest-api-referansi)

</div>

---

<a id="temel-ozellikler" name="temel-ozellikler"></a>
## 🌟 Temel Özellikler ve İnovasyonlar

- **Birleşik Multimodal Ağ Grafı**: 11 Metro hattı, 7/24 Metrobüs, kıtalararası Marmaray omurgası, 5 Tramvay hattı, 4 Füniküler/Teleferik sistemi, Şehir Hatları ve özel Boğaz vapurları (Turyol, Dentur), 800+ İETT otobüs hattı ve Havalimanı servislerini (Havaist ve H-2) tek bir hibrit graf üzerinde birbirine bağlar.
- **Sıfır Maliyetli Dinamik Trafik Katmanı (FCD)**: Google Maps Distance Matrix için aylık binlerce dolar fatura ödemek yerine; her 10 saniyede bir 3.000'den fazla aktif İETT otobüsünden gelen Canlı Filo Telemetrisini (Floating Car Data - FCD) işleyerek güzergah bazlı Trafik Yoğunluk Katsayısını (TCC) dinamik olarak yolculuk sürelerine yansıtır.
- **Yetişilebilir Canlı Araç Radarı**: Kullanıcının yürüme hızını yaklaşan aracın anlık GPS konumu ve yönüyle vektörel olarak karşılaştırır. Durağa doğru yaklaşan araçla duraktan uzaklaşan aracı ayırt eder; *"Yetişilebilir"* veya *"Yetişilemez (Kaçtı / Çok Hızlı)"* ikazı üretir.
- **Yürüme Engeli Kalkanı (Anti-Walk Shield)**: OpenStreetMap (OSM) yaya bariyerlerinin (örneğin E-5 otoyol çitleri gibi yaya geçidi olmayan yerlerde klasik navigasyonların 10-15 km yürüme hatasına düşmesi) önüne geçer; kullanıcıyı 1.200m yarıçapındaki en erişilebilir toplu taşıma hub'ına akıllıca bağlar.
- **Kırsal ve Çevresel İlçe Bağlantıları**: İstanbul'un en uç ilçeleri için (Silivri `303A`, Çatalca `401`, Şile `139A`, Tuzla `130Ş`) gerçekçi aktarma koridorları oluşturur; yapay koordinat ışınlanmalarını engeller.
- **Moovit Kalitesinde Koridor Hat Gruplama**: Aynı duraktan kalkıp aynı koridorda ilerleyen otobüsleri tek bir temiz bacakta birleştirir (örneğin: `[93M / 50M]`) ve anlamsız 1 duraklık mikro-otobüs aktarmalarını otomatik olarak budar.
- **Manzaralı Rota & Boğaz Vapuru Sentezleyici**: Kullanıcı "Manzaralı / Vapur" tercihi yaptığında, aktarmaları optimize ederek yolcuyu Boğaz kıyısı otobüslerine veya vapur iskelelerine (Eminönü, Karaköy, Beşiktaş, Kadıköy, Üsküdar) yönlendirir.
- **Sıfır CDN Bağımlı Modern Arayüz**: Yerel Leaflet, vektörel hat renkleri, cam efektli modern arama paneli ve tamamen çevrimdışı çalışabilen hafif web arayüzü sunar.

---

<a id="benchmark-raporu" name="benchmark-raporu"></a>
## 📊 1.000 Rotalık ve Canlı Adli Kıyaslama Raporu

Motorun performansını ve doğruluğunu ölçmek amacıyla; tüm İstanbul il sınırları içinde (Silivri'den Tuzla'ya, Çatalca'dan Pendik'e) rastgele üretilen **1.000 koordinat çiftinde** bizim motorumuz, **Moovit** ve **Google Maps** eşzamanlı olarak test edilmiştir:

### 1. Genel İl Geneli Kıyaslama (1.000 Rastgele Rota)

| Metrik | Istanbul Transit Core | Moovit (Canlı Web) | Google Maps |
| :--- | :---: | :---: | :---: |
| **Rota Başarı Oranı** | **%95.5** (955/1000) | **%99.8** (998/1000) | **%99.5** (995/1000) |
| **Kağıt Üstünde "Hızlı"** | **594 rota (%62.3)** | **349 rota (%36.6)** | — |
| **Tam Eşit ($\pm 0$ dk)** | **10 rota (%1.0)** | **10 rota (%1.0)** | — |
| **Ortalama Yanıt Süresi** | **1.82 sn** | 7.45 sn (Tarayıcı botu) | 4.91 sn (Tarayıcı botu) |

### 2. Canlı Adli Teşhis (Durakta Bekleme Süresi & Trafik Dahil)

Önceki testlerde durakta bekleme süresi hesaba katılmadığı için sistemimizin hızlı çıktığı **47 kritik rotada** yapılan canlı denetimde:
* **21 Rotada (%44.7):** Motorumuz Moovit'ten **ortalama 18 dakika daha hızlıdır**. (Moovit'in yolcuyu 4 farklı metroya indirip çıkardığı yerlerde doğrudan ekspres hatları veya M4 kesintisiz terminal bağlantısını seçtiğimiz için).
* **3 Rotada (%6.4):** Moovit ile **tam başa baş (0 dakika fark)** sonuç vermiştir.
* **23 Rotada (%48.9):** Canlı saatte durağa otobüsün gelmesine 25-35 dakika olduğu anlarda, Moovit sık geçen Metro/Metrobüs omurgası sayesinde öne geçmiştir.
* **Genel Ortalama:** 47 koridorun tamamında sistemimiz ile Moovit arasındaki süre farkı sadece **+2.5 dakikadır** (kafa kafaya rekabet).

---

<a id="hizli-kurulum" name="hizli-kurulum"></a>
## 🚀 Hızlı Başlangıç & Kurulum

### 1. Yerel Çalıştırma (Mac & Linux)

Sistemi kendi bilgisayarınızda tek bir komutla başlatabilirsiniz:

```bash
# Projeyi klonlayın
git clone https://github.com/Sefa-Kara/istanbul-transit-core.git
cd istanbul-transit-core

# Python bağımlılıklarını kurun
pip install -r requirements.txt

# Sistemi (OTP 2.6 ve FastAPI) tek tıkla başlatın
./start.sh
```

Tarayıcınız otomatik olarak `http://localhost:8000` adresinde açılacaktır.

Sistemi durdurmak için:
```bash
./stop.sh
```

---

### 2. Docker ile Çalıştırma

```bash
docker compose up -d --build
```
* **Web Arayüzü:** `http://localhost:8000`
* **OTP GraphQL Gezgini:** `http://localhost:8080/otp/routers/default/index/graphql`

---

### 3. Hugging Face Spaces Üzerinde Ücretsiz Canlı Demo (Gradio SDK)

Hugging Face Spaces üzerinde **16 GB RAM ve 2 vCPU** kapasitesinde **%100 ücretsiz** canlı web yayını yapmak için:

1. [Hugging Face Spaces](https://huggingface.co/spaces) adresine gidin ve **"Create new Space"** butonuna tıklayın.
2. Space adını belirleyin: `istanbul-transit-core`
3. SDK olarak **Gradio** seçeneğini seçin (Blank şablonu).
4. Donanım olarak **Free tier (CPU Basic · 16 GB RAM)** seçeneğini seçin.
5. Hazırladığımız `packages.txt` dosyası Debian üzerinden Java 17'yi ücretsiz kuracak, `app.py` ise OTP ve Leaflet arayüzünü otomatik başlatacaktır.
6. Kodları Hugging Face deponuza pushlayın:
   ```bash
   git remote add space https://huggingface.co/spaces/<kullanıcı-adınız>/istanbul-transit-core.git
   git push space main
   ```

---

<a id="rest-api-referansi" name="rest-api-referansi"></a>
## 📱 Mobil & Web Geliştiricileri İçin REST API Referansı

Bu altyapıyı kullanarak Flutter, React Native, Swift veya web tabanlı kendi özel ulaşım uygulamalarınızı geliştirebilirsiniz:

### 1. Otomatik Tamamlama & Durak Arama
```http
GET /api/search?q={arama_terimi}&limit=5
```
**Örnek Yanıt:**
```json
[
  {
    "title": "Kadıköy Rıhtım",
    "subtitle": "Kadıköy (M4 Metro, Marmaray & Vapur Hub)",
    "category": "transit_hub",
    "icon": "🚇",
    "lat": 40.9904,
    "lon": 29.0253
  }
]
```

### 2. Güzergah ve Rota Hesaplama
```http
GET /api/plan?from_lat=41.0667&from_lon=28.9936&to_lat=40.9086&to_lon=29.2840&target=FASTEST
```
**Parametreler:**
* `target`: `FASTEST` (En Hızlı) | `LEAST_TRANSFERS` (Az Aktarma) | `LEAST_WALKING` (Az Yürüme) | `SCENIC_WATER` (Manzaralı / Vapur)
* `prefer_modes`: `SUBWAY,METROBUS,FERRY`
* `allow_minibus`: `true` | `false`

### 3. Canlı İETT Otobüs Radarı
```http
GET /api/live/buses/{hat_kodu}
```
**Örnek:** `/api/live/buses/500T`
```json
{
  "line_code": "500T",
  "active_count": 28,
  "buses": [
    {
      "door_code": "B-1204",
      "lat": 40.9823,
      "lon": 29.1105,
      "speed_kmh": 42.5,
      "direction": "GİDİŞ"
    }
  ]
}
```

---

<a id="lisans" name="lisans"></a>
## ⚖️ Lisans

Bu proje **[MIT Lisansı](LICENSE)** ile lisanslanmıştır. Ticari ve kişisel projelerde serbestçe kullanılabilir, çatallanabilir (fork) ve dağıtılabilir.
