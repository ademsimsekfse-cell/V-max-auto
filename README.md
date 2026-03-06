# V-max Auto 🔧
**Oto Servis Otomasyon & Muhasebe Yönetim Sistemi**

Python / Flask ile geliştirilmiş tam işlevli bir oto servis otomasyon ve muhasebe uygulaması.

---

## Özellikler

| Modül | Açıklama |
|---|---|
| 👥 **Müşteri Yönetimi** | Müşteri ekleme, düzenleme, silme |
| 🚗 **Araç Yönetimi** | Müşteriye araç atama, plaka/marka/model/KM takibi |
| 🛠️ **Servis Emirleri** | İş emri oluşturma, durum takibi (Açık / Devam / Tamamlandı / İptal), işçilik ve parça maliyeti |
| 🧾 **Fatura** | Servis emirlerinden otomatik fatura oluşturma, ödeme işlemi |
| 💸 **Gider Takibi** | Kategori bazlı gider girişi (Kira, Personel, Yakıt, vb.) |
| 📊 **Dashboard** | Anlık özet: müşteri sayısı, açık emirler, toplam gelir, toplam gider, net kâr |
| 🔌 **REST API** | Tüm modüller için JSON API (GET / POST / PUT / DELETE) |

---

## Kurulum

### 1. Gereksinimleri Yükle

```bash
pip install -r requirements.txt
```

### 2. Uygulamayı Başlat

```bash
python run.py
```

Tarayıcıda şu adrese git: **http://localhost:5000**

---

## Testler — Nasıl Test Ederim?

### Otomatik Testleri Çalıştır

```bash
pytest
```

ya da daha ayrıntılı çıktı için:

```bash
pytest -v
```

Kapsam raporuyla:

```bash
pytest --cov=app --cov-report=term-missing
```

> 40 test, tüm modülleri kapsar: Müşteri, Araç, Servis Emri, Fatura, Gider, Dashboard.

### Manuel Test — REST API

```bash
# Müşteri ekle
curl -X POST http://localhost:5000/customers/api/customers \
  -H "Content-Type: application/json" \
  -d '{"name":"Ali Yılmaz","phone":"0532 000 0000"}'

# Tüm müşterileri listele
curl http://localhost:5000/customers/api/customers

# Araç ekle (customer_id=1 için)
curl -X POST http://localhost:5000/vehicles/api/vehicles \
  -H "Content-Type: application/json" \
  -d '{"customer_id":1,"plate":"34 ABC 01","brand":"Toyota","model":"Corolla","year":2020}'

# Servis emri aç
curl -X POST http://localhost:5000/service-orders/api/service-orders \
  -H "Content-Type: application/json" \
  -d '{"vehicle_id":1,"description":"Yağ değişimi","labor_cost":150,"parts_cost":200}'

# Fatura oluştur ve öde
curl -X POST http://localhost:5000/invoices/api/invoices \
  -H "Content-Type: application/json" \
  -d '{"service_order_id":1,"amount":350}'

curl -X POST http://localhost:5000/invoices/api/invoices/1/pay
```

---

## Proje Yapısı

```
V-max-auto/
├── run.py                  # Uygulama başlangıç noktası
├── requirements.txt
├── pyproject.toml          # pytest konfigürasyonu
├── app/
│   ├── __init__.py         # create_app factory
│   ├── models.py           # SQLAlchemy modelleri
│   ├── routes/
│   │   ├── main.py         # Dashboard
│   │   ├── customers.py    # Müşteri rotaları + API
│   │   ├── vehicles.py     # Araç rotaları + API
│   │   ├── service_orders.py
│   │   ├── invoices.py
│   │   └── expenses.py
│   ├── templates/          # Jinja2 HTML şablonları
│   └── static/css/         # CSS stilleri
└── tests/
    ├── conftest.py
    ├── test_customers.py
    ├── test_vehicles.py
    ├── test_service_orders.py
    ├── test_invoices_expenses.py
    └── test_models.py
```

---

## Nasıl Daha Geliştirebilirsin?

- 🔐 **Kullanıcı girişi** (Flask-Login ile çalışan / yönetici rolleri)
- 📄 **PDF Fatura** oluşturma (WeasyPrint veya ReportLab)
- 📅 **Randevu Sistemi** (müşteri portal üzerinden servis randevusu)
- 📦 **Stok / Parça Yönetimi** (depodaki parçaları takip et)
- 📊 **Grafikler** (aylık gelir/gider grafikleri, Chart.js)
- 📱 **Mobil uyumlu tasarım** iyileştirmeleri
- 🐳 **Docker** ile konteynerize dağıtım
- ☁️ **Bulut dağıtımı** (Heroku, Railway, Render)

