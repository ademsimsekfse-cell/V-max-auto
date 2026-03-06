"""
Database initialization script for V-MAX OTOMOTİV.
Creates all tables, default users, sample data, and settings.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import date, datetime
from app import create_app
from models import (db, Unit, User, SharedExpenseCategory, Customer, Vehicle,
                    ServiceRecord, AppSetting)


def init_db():
    app = create_app()
    with app.app_context():
        print("Tablolar oluşturuluyor...")
        db.create_all()
        print("  ✓ Tablolar oluşturuldu.")

        # ── Units ────────────────────────────────────────────────────────────
        if Unit.query.count() == 0:
            unit_names = ['Kaporta', 'Boya', 'Mekanik', 'Elektrik']
            units = []
            for name in unit_names:
                u = Unit(name=name)
                db.session.add(u)
                units.append(u)
            db.session.flush()
            print(f"  ✓ {len(unit_names)} birim eklendi: {', '.join(unit_names)}")
        else:
            units = Unit.query.all()
            print("  ℹ Birimler zaten mevcut.")

        # ── Users ────────────────────────────────────────────────────────────
        if User.query.count() == 0:
            admin = User(username='admin', full_name='Sistem Yöneticisi', role='admin', is_active=True)
            admin.set_password('admin123')

            usta = User(username='usta1', full_name='Ahmet Yılmaz', role='usta', is_active=True)
            usta.set_password('usta123')
            if units:
                usta.unit_id = units[0].id

            muhasebe = User(username='muhasebe', full_name='Fatma Demir', role='muhasebe', is_active=True)
            muhasebe.set_password('muhasebe123')

            db.session.add_all([admin, usta, muhasebe])
            db.session.flush()
            print("  ✓ Kullanıcılar eklendi: admin, usta1, muhasebe")
        else:
            print("  ℹ Kullanıcılar zaten mevcut.")

        # ── Shared Expense Categories ─────────────────────────────────────────
        if SharedExpenseCategory.query.count() == 0:
            cat_names = ['Su', 'Elektrik', 'Telefon', 'İnternet', 'Kira',
                         'Temizlik', 'Sigorta', 'Vergi']
            for name in cat_names:
                c = SharedExpenseCategory(name=name)
                db.session.add(c)
            db.session.flush()
            print(f"  ✓ Gider kategorileri eklendi: {', '.join(cat_names)}")
        else:
            print("  ℹ Gider kategorileri zaten mevcut.")

        # ── Sample Customers & Vehicles ───────────────────────────────────────
        if Customer.query.count() == 0:
            sample_customers = [
                {'full_name': 'Mehmet Kaya', 'phone': '05321234567', 'email': 'mehmet.kaya@email.com',
                 'address': 'Kadıköy, İstanbul'},
                {'full_name': 'Ayşe Çelik', 'phone': '05439876543', 'email': 'ayse.celik@email.com',
                 'address': 'Çankaya, Ankara'},
                {'full_name': 'Mustafa Demir', 'phone': '05557654321', 'email': 'mustafa.demir@email.com',
                 'address': 'Konak, İzmir'},
                {'full_name': 'Zeynep Arslan', 'phone': '05064432100', 'email': 'zeynep.arslan@email.com',
                 'address': 'Nilüfer, Bursa'},
            ]
            customers = []
            for cd in sample_customers:
                c = Customer(**cd)
                db.session.add(c)
                customers.append(c)
            db.session.flush()
            print(f"  ✓ {len(customers)} örnek müşteri eklendi.")

            sample_vehicles = [
                {'plate': '34ABC123', 'brand': 'Toyota', 'model': 'Corolla', 'year': 2019,
                 'color': 'Beyaz', 'owner': customers[0],
                 'insurance_expiry': date(2025, 6, 15), 'inspection_expiry': date(2024, 11, 20)},
                {'plate': '06DEF456', 'brand': 'Ford', 'model': 'Focus', 'year': 2020,
                 'color': 'Siyah', 'owner': customers[1],
                 'insurance_expiry': date(2025, 3, 10), 'inspection_expiry': date(2025, 2, 28)},
                {'plate': '35GHI789', 'brand': 'Volkswagen', 'model': 'Passat', 'year': 2018,
                 'color': 'Gri', 'owner': customers[2],
                 'insurance_expiry': date(2025, 8, 5), 'inspection_expiry': date(2025, 7, 14)},
                {'plate': '16JKL012', 'brand': 'Renault', 'model': 'Megane', 'year': 2021,
                 'color': 'Mavi', 'owner': customers[3],
                 'insurance_expiry': date(2025, 12, 1), 'inspection_expiry': date(2025, 10, 30)},
                {'plate': '34MNO345', 'brand': 'Hyundai', 'model': 'Tucson', 'year': 2022,
                 'color': 'Beyaz', 'owner': customers[0],
                 'insurance_expiry': date(2026, 1, 15), 'inspection_expiry': date(2025, 12, 31)},
            ]
            vehicles = []
            for vd in sample_vehicles:
                owner = vd.pop('owner')
                v = Vehicle(**vd, owner_id=owner.id)
                db.session.add(v)
                vehicles.append(v)
            db.session.flush()
            print(f"  ✓ {len(vehicles)} örnek araç eklendi.")

            # Sample service record
            admin_user = User.query.filter_by(username='admin').first()
            first_unit = units[2] if len(units) > 2 else units[0]
            rec = ServiceRecord(
                record_no='SRV-20240101-0001',
                vehicle_id=vehicles[0].id,
                unit_id=first_unit.id,
                accepted_by=admin_user.id if admin_user else None,
                status='in_progress',
                complaint='Motor sesi var, yağ değişimi gerekli.',
                mileage=87500,
                fuel_level='1/2'
            )
            db.session.add(rec)
            db.session.flush()
            print("  ✓ 1 örnek servis kaydı eklendi.")
        else:
            print("  ℹ Müşteriler ve araçlar zaten mevcut.")

        # ── App Settings ──────────────────────────────────────────────────────
        default_settings = {
            'company_name': 'V-MAX OTOMOTİV',
            'company_phone': '0212 555 0000',
            'company_address': 'Sanayi Mah. Oto Sanayi Sitesi No:42, İstanbul',
            'tax_no': '1234567890',
        }
        for key, value in default_settings.items():
            if not AppSetting.query.filter_by(key=key).first():
                db.session.add(AppSetting(key=key, value=value))
        db.session.flush()
        print("  ✓ Uygulama ayarları eklendi.")

        db.session.commit()
        print()
        print("=" * 55)
        print("  ✅  V-MAX OTOMOTİV veritabanı başarıyla oluşturuldu!")
        print("=" * 55)
        print()
        print("  Giriş Bilgileri:")
        print("  ┌─────────────┬──────────────────┬────────────────┐")
        print("  │ Kullanıcı   │ Şifre            │ Rol            │")
        print("  ├─────────────┼──────────────────┼────────────────┤")
        print("  │ admin       │ admin123         │ Yönetici       │")
        print("  │ usta1       │ usta123          │ Usta           │")
        print("  │ muhasebe    │ muhasebe123      │ Muhasebe       │")
        print("  └─────────────┴──────────────────┴────────────────┘")
        print()
        print("  Uygulamayı başlatmak için: python run.py")
        print("  Adres: http://localhost:5000")
        print()


if __name__ == '__main__':
    init_db()
