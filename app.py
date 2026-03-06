import os
from datetime import datetime, date, timedelta
from functools import wraps
from flask import Flask, render_template, redirect, url_for, flash, request, jsonify, abort
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from sqlalchemy import func
from models import (db, User, Unit, Customer, Vehicle, ServiceRecord, ServiceTask,
                    Quote, QuoteItem, Invoice, InvoiceItem, SharedExpense,
                    SharedExpenseCategory, UnitExpense, SyncLog, AppSetting)


def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'vmax-secret-key-2024')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///vmax_auto.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['WTF_CSRF_ENABLED'] = False

    db.init_app(app)

    login_manager = LoginManager(app)
    login_manager.login_view = 'login'
    login_manager.login_message = 'Lütfen giriş yapın.'
    login_manager.login_message_category = 'warning'

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    def role_required(*roles):
        def decorator(f):
            @wraps(f)
            def decorated(*args, **kwargs):
                if not current_user.is_authenticated:
                    return redirect(url_for('login'))
                if current_user.role not in roles:
                    flash('Bu sayfaya erişim yetkiniz yok.', 'danger')
                    return redirect(url_for('dashboard'))
                return f(*args, **kwargs)
            return decorated
        return decorator

    def generate_record_no(prefix, model_class, field_name):
        today = datetime.utcnow().strftime('%Y%m%d')
        base = f"{prefix}-{today}-"
        count = db.session.query(model_class).filter(
            getattr(model_class, field_name).like(f"{base}%")
        ).count()
        return f"{base}{(count + 1):04d}"

    # ─── AUTH ────────────────────────────────────────────────────────────────

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
        if request.method == 'POST':
            username = request.form.get('username', '').strip()
            password = request.form.get('password', '')
            user = User.query.filter_by(username=username, is_active=True).first()
            if user and user.check_password(password):
                login_user(user)
                flash(f'Hoş geldiniz, {user.full_name}!', 'success')
                return redirect(url_for('dashboard'))
            flash('Kullanıcı adı veya şifre hatalı.', 'danger')
        return render_template('login.html')

    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        flash('Çıkış yapıldı.', 'info')
        return redirect(url_for('login'))

    # ─── DASHBOARD ───────────────────────────────────────────────────────────

    @app.route('/')
    @login_required
    def dashboard():
        today = date.today()
        active_services = ServiceRecord.query.filter(
            ServiceRecord.status.in_(['waiting', 'in_progress'])
        ).count()
        waiting = ServiceRecord.query.filter_by(status='waiting').count()
        completed = ServiceRecord.query.filter_by(status='completed').count()
        today_revenue = db.session.query(func.sum(Invoice.final_amount)).filter(
            Invoice.status == 'paid',
            func.date(Invoice.paid_at) == today
        ).scalar() or 0
        recent_records = ServiceRecord.query.order_by(ServiceRecord.created_at.desc()).limit(10).all()
        units = Unit.query.filter_by(is_active=True).all()
        return render_template('dashboard.html',
                               active_services=active_services,
                               waiting=waiting,
                               completed=completed,
                               today_revenue=today_revenue,
                               recent_records=recent_records,
                               units=units)

    # ─── CUSTOMERS ───────────────────────────────────────────────────────────

    @app.route('/customers')
    @login_required
    def customers():
        q = request.args.get('q', '').strip()
        query = Customer.query
        if q:
            query = query.filter(
                (Customer.full_name.ilike(f'%{q}%')) |
                (Customer.phone.ilike(f'%{q}%')) |
                (Customer.email.ilike(f'%{q}%'))
            )
        customers_list = query.order_by(Customer.full_name).all()
        return render_template('customers/list.html', customers=customers_list, q=q)

    @app.route('/customers/new', methods=['GET', 'POST'])
    @login_required
    def customer_new():
        if request.method == 'POST':
            c = Customer(
                full_name=request.form['full_name'].strip(),
                phone=request.form.get('phone', '').strip(),
                email=request.form.get('email', '').strip(),
                address=request.form.get('address', '').strip(),
                id_number=request.form.get('id_number', '').strip(),
                notes=request.form.get('notes', '').strip()
            )
            db.session.add(c)
            db.session.commit()
            flash('Müşteri başarıyla oluşturuldu.', 'success')
            return redirect(url_for('customers'))
        return render_template('customers/form.html', customer=None)

    @app.route('/customers/<int:cid>/edit', methods=['GET', 'POST'])
    @login_required
    def customer_edit(cid):
        c = Customer.query.get_or_404(cid)
        if request.method == 'POST':
            c.full_name = request.form['full_name'].strip()
            c.phone = request.form.get('phone', '').strip()
            c.email = request.form.get('email', '').strip()
            c.address = request.form.get('address', '').strip()
            c.id_number = request.form.get('id_number', '').strip()
            c.notes = request.form.get('notes', '').strip()
            db.session.commit()
            flash('Müşteri güncellendi.', 'success')
            return redirect(url_for('customers'))
        return render_template('customers/form.html', customer=c)

    # ─── VEHICLES ────────────────────────────────────────────────────────────

    @app.route('/vehicles')
    @login_required
    def vehicles():
        q = request.args.get('q', '').strip()
        query = Vehicle.query
        if q:
            query = query.join(Customer, isouter=True).filter(
                (Vehicle.plate.ilike(f'%{q}%')) |
                (Vehicle.brand.ilike(f'%{q}%')) |
                (Vehicle.model.ilike(f'%{q}%')) |
                (Customer.full_name.ilike(f'%{q}%'))
            )
        vehicles_list = query.order_by(Vehicle.plate).all()
        return render_template('vehicles/list.html', vehicles=vehicles_list, q=q)

    @app.route('/vehicles/new', methods=['GET', 'POST'])
    @login_required
    def vehicle_new():
        customers_list = Customer.query.order_by(Customer.full_name).all()
        if request.method == 'POST':
            plate = request.form['plate'].strip().upper().replace(' ', '')
            existing = Vehicle.query.filter_by(plate=plate).first()
            if existing:
                flash('Bu plaka zaten kayıtlı.', 'warning')
                return render_template('vehicles/form.html', vehicle=None, customers=customers_list)

            owner_id = request.form.get('owner_id') or None
            new_owner_name = request.form.get('new_owner_name', '').strip()
            if not owner_id and new_owner_name:
                owner = Customer(
                    full_name=new_owner_name,
                    phone=request.form.get('new_owner_phone', '').strip()
                )
                db.session.add(owner)
                db.session.flush()
                owner_id = owner.id

            ins_exp = request.form.get('insurance_expiry') or None
            insp_exp = request.form.get('inspection_expiry') or None
            v = Vehicle(
                plate=plate,
                brand=request.form.get('brand', '').strip(),
                model=request.form.get('model', '').strip(),
                year=request.form.get('year') or None,
                color=request.form.get('color', '').strip(),
                engine_no=request.form.get('engine_no', '').strip(),
                chassis_no=request.form.get('chassis_no', '').strip(),
                owner_id=owner_id,
                insurance_expiry=datetime.strptime(ins_exp, '%Y-%m-%d').date() if ins_exp else None,
                inspection_expiry=datetime.strptime(insp_exp, '%Y-%m-%d').date() if insp_exp else None,
                notes=request.form.get('notes', '').strip()
            )
            db.session.add(v)
            db.session.commit()
            flash('Araç başarıyla oluşturuldu.', 'success')
            return redirect(url_for('vehicles'))
        return render_template('vehicles/form.html', vehicle=None, customers=customers_list)

    @app.route('/vehicles/<int:vid>/edit', methods=['GET', 'POST'])
    @login_required
    def vehicle_edit(vid):
        v = Vehicle.query.get_or_404(vid)
        customers_list = Customer.query.order_by(Customer.full_name).all()
        if request.method == 'POST':
            plate = request.form['plate'].strip().upper().replace(' ', '')
            existing = Vehicle.query.filter(Vehicle.plate == plate, Vehicle.id != vid).first()
            if existing:
                flash('Bu plaka başka bir araçta kayıtlı.', 'warning')
                return render_template('vehicles/form.html', vehicle=v, customers=customers_list)
            v.plate = plate
            v.brand = request.form.get('brand', '').strip()
            v.model = request.form.get('model', '').strip()
            v.year = request.form.get('year') or None
            v.color = request.form.get('color', '').strip()
            v.engine_no = request.form.get('engine_no', '').strip()
            v.chassis_no = request.form.get('chassis_no', '').strip()
            v.owner_id = request.form.get('owner_id') or None
            ins_exp = request.form.get('insurance_expiry') or None
            insp_exp = request.form.get('inspection_expiry') or None
            v.insurance_expiry = datetime.strptime(ins_exp, '%Y-%m-%d').date() if ins_exp else None
            v.inspection_expiry = datetime.strptime(insp_exp, '%Y-%m-%d').date() if insp_exp else None
            v.notes = request.form.get('notes', '').strip()
            db.session.commit()
            flash('Araç güncellendi.', 'success')
            return redirect(url_for('vehicle_detail', vid=vid))
        return render_template('vehicles/form.html', vehicle=v, customers=customers_list)

    @app.route('/vehicles/<int:vid>')
    @login_required
    def vehicle_detail(vid):
        v = Vehicle.query.get_or_404(vid)
        records = ServiceRecord.query.filter_by(vehicle_id=vid).order_by(ServiceRecord.created_at.desc()).all()
        return render_template('vehicles/detail.html', vehicle=v, records=records)

    # ─── SERVICE ─────────────────────────────────────────────────────────────

    @app.route('/service')
    @login_required
    def service_list():
        status_filter = request.args.get('status', '')
        unit_filter = request.args.get('unit_id', '')
        query = ServiceRecord.query
        if status_filter:
            query = query.filter_by(status=status_filter)
        if unit_filter:
            query = query.filter_by(unit_id=int(unit_filter))
        records = query.order_by(ServiceRecord.created_at.desc()).all()
        units = Unit.query.filter_by(is_active=True).all()
        return render_template('service/list.html', records=records, units=units,
                               status_filter=status_filter, unit_filter=unit_filter)

    @app.route('/service/new', methods=['GET', 'POST'])
    @login_required
    def service_new():
        units = Unit.query.filter_by(is_active=True).all()
        if request.method == 'POST':
            plate = request.form.get('plate', '').strip().upper().replace(' ', '')
            vehicle = Vehicle.query.filter_by(plate=plate).first()

            if not vehicle:
                # Create new vehicle and possibly customer
                owner_name = request.form.get('owner_name', '').strip()
                owner_phone = request.form.get('owner_phone', '').strip()
                owner = None
                if owner_name:
                    owner = Customer(full_name=owner_name, phone=owner_phone)
                    db.session.add(owner)
                    db.session.flush()
                vehicle = Vehicle(
                    plate=plate,
                    brand=request.form.get('brand', '').strip(),
                    model=request.form.get('model', '').strip(),
                    year=request.form.get('year') or None,
                    color=request.form.get('color', '').strip(),
                    owner_id=owner.id if owner else None
                )
                db.session.add(vehicle)
                db.session.flush()

            record_no = generate_record_no('SRV', ServiceRecord, 'record_no')
            est_del = request.form.get('estimated_delivery') or None
            rec = ServiceRecord(
                record_no=record_no,
                vehicle_id=vehicle.id,
                unit_id=request.form.get('unit_id') or None,
                accepted_by=current_user.id,
                complaint=request.form.get('complaint', '').strip(),
                delivery_person_name=request.form.get('delivery_person_name', '').strip(),
                delivery_person_phone=request.form.get('delivery_person_phone', '').strip(),
                mileage=request.form.get('mileage') or None,
                fuel_level=request.form.get('fuel_level', '').strip(),
                estimated_delivery=datetime.strptime(est_del, '%Y-%m-%dT%H:%M') if est_del else None,
                notes=request.form.get('notes', '').strip()
            )
            db.session.add(rec)
            db.session.commit()
            flash(f'Servis kaydı {record_no} oluşturuldu.', 'success')
            return redirect(url_for('service_detail', rid=rec.id))
        return render_template('service/form.html', units=units)

    @app.route('/service/<int:rid>')
    @login_required
    def service_detail(rid):
        rec = ServiceRecord.query.get_or_404(rid)
        technicians = User.query.filter(User.role.in_(['admin', 'usta']), User.is_active == True).all()
        return render_template('service/detail.html', record=rec, technicians=technicians)

    @app.route('/service/<int:rid>/status', methods=['POST'])
    @login_required
    def service_status(rid):
        rec = ServiceRecord.query.get_or_404(rid)
        new_status = request.form.get('status')
        valid = ['waiting', 'in_progress', 'completed', 'delivered']
        if new_status in valid:
            rec.status = new_status
            if new_status == 'delivered':
                rec.actual_delivery = datetime.utcnow()
            db.session.commit()
            status_names = {'waiting': 'Bekliyor', 'in_progress': 'İşlemde',
                            'completed': 'Tamamlandı', 'delivered': 'Teslim Edildi'}
            flash(f'Durum "{status_names.get(new_status)}" olarak güncellendi.', 'success')
        else:
            flash('Geçersiz durum.', 'danger')
        return redirect(url_for('service_detail', rid=rid))

    @app.route('/service/<int:rid>/tasks', methods=['GET', 'POST'])
    @login_required
    def service_tasks(rid):
        rec = ServiceRecord.query.get_or_404(rid)
        if request.method == 'POST':
            task = ServiceTask(
                service_record_id=rid,
                description=request.form['description'].strip(),
                technician_id=request.form.get('technician_id') or None,
                labor_hours=float(request.form.get('labor_hours') or 0),
                parts_cost=float(request.form.get('parts_cost') or 0),
                labor_cost=float(request.form.get('labor_cost') or 0),
                notes=request.form.get('notes', '').strip()
            )
            db.session.add(task)
            db.session.commit()
            flash('Görev eklendi.', 'success')
        return redirect(url_for('service_detail', rid=rid))

    @app.route('/service/<int:rid>/quote', methods=['GET', 'POST'])
    @login_required
    def service_quote(rid):
        rec = ServiceRecord.query.get_or_404(rid)
        if request.method == 'POST':
            quote_no = generate_record_no('QT', Quote, 'quote_no')
            total = float(request.form.get('total_amount') or 0)
            tax_rate = float(request.form.get('tax_rate') or 18)
            discount = float(request.form.get('discount') or 0)
            tax_amount = total * tax_rate / 100
            final_amount = total + tax_amount - discount
            valid_until = request.form.get('valid_until') or None
            q = Quote(
                quote_no=quote_no,
                service_record_id=rid,
                created_by=current_user.id,
                total_amount=total,
                tax_rate=tax_rate,
                tax_amount=tax_amount,
                discount=discount,
                final_amount=final_amount,
                status=request.form.get('status', 'draft'),
                notes=request.form.get('notes', '').strip(),
                valid_until=datetime.strptime(valid_until, '%Y-%m-%d').date() if valid_until else None
            )
            db.session.add(q)
            db.session.flush()

            descriptions = request.form.getlist('item_description[]')
            types = request.form.getlist('item_type[]')
            quantities = request.form.getlist('item_quantity[]')
            prices = request.form.getlist('item_unit_price[]')
            totals = request.form.getlist('item_total_price[]')
            for i, desc in enumerate(descriptions):
                if desc.strip():
                    item = QuoteItem(
                        quote_id=q.id,
                        description=desc.strip(),
                        item_type=types[i] if i < len(types) else 'service',
                        quantity=float(quantities[i]) if i < len(quantities) else 1,
                        unit_price=float(prices[i]) if i < len(prices) else 0,
                        total_price=float(totals[i]) if i < len(totals) else 0
                    )
                    db.session.add(item)
            db.session.commit()
            flash(f'Teklif {quote_no} oluşturuldu.', 'success')
            return redirect(url_for('service_detail', rid=rid))
        return render_template('service/quote_form.html', record=rec)

    @app.route('/service/<int:rid>/invoice', methods=['GET', 'POST'])
    @login_required
    def service_invoice(rid):
        rec = ServiceRecord.query.get_or_404(rid)
        if request.method == 'POST':
            invoice_no = generate_record_no('INV', Invoice, 'invoice_no')
            subtotal = float(request.form.get('total_amount') or 0)
            tax_rate = float(request.form.get('tax_rate') or 18)
            discount = float(request.form.get('discount') or 0)
            tax_amount = subtotal * tax_rate / 100
            final_amount = subtotal + tax_amount - discount
            status = request.form.get('status', 'draft')
            inv = Invoice(
                invoice_no=invoice_no,
                service_record_id=rid,
                quote_id=request.form.get('quote_id') or None,
                created_by=current_user.id,
                subtotal=subtotal,
                tax_rate=tax_rate,
                tax_amount=tax_amount,
                discount=discount,
                final_amount=final_amount,
                status=status,
                payment_method=request.form.get('payment_method', '').strip(),
                notes=request.form.get('notes', '').strip(),
                paid_at=datetime.utcnow() if status == 'paid' else None
            )
            db.session.add(inv)
            db.session.flush()

            descriptions = request.form.getlist('item_description[]')
            types = request.form.getlist('item_type[]')
            quantities = request.form.getlist('item_quantity[]')
            prices = request.form.getlist('item_unit_price[]')
            totals = request.form.getlist('item_total_price[]')
            for i, desc in enumerate(descriptions):
                if desc.strip():
                    item = InvoiceItem(
                        invoice_id=inv.id,
                        description=desc.strip(),
                        item_type=types[i] if i < len(types) else 'service',
                        quantity=float(quantities[i]) if i < len(quantities) else 1,
                        unit_price=float(prices[i]) if i < len(prices) else 0,
                        total_price=float(totals[i]) if i < len(totals) else 0
                    )
                    db.session.add(item)
            db.session.commit()
            flash(f'Fatura {invoice_no} oluşturuldu.', 'success')
            return redirect(url_for('service_detail', rid=rid))
        return render_template('service/invoice_form.html', record=rec)

    # ─── ACCOUNTING ──────────────────────────────────────────────────────────

    @app.route('/accounting')
    @login_required
    def accounting():
        if current_user.role not in ('admin', 'muhasebe'):
            flash('Bu sayfaya erişim yetkiniz yok.', 'danger')
            return redirect(url_for('dashboard'))
        today = date.today()
        month_start = today.replace(day=1)
        monthly_revenue = db.session.query(func.sum(Invoice.final_amount)).filter(
            Invoice.status == 'paid',
            func.date(Invoice.paid_at) >= month_start
        ).scalar() or 0
        monthly_shared = db.session.query(func.sum(SharedExpense.amount)).filter(
            SharedExpense.date >= month_start
        ).scalar() or 0
        monthly_unit_exp = db.session.query(func.sum(UnitExpense.amount)).filter(
            UnitExpense.date >= month_start
        ).scalar() or 0
        net_profit = monthly_revenue - monthly_shared - monthly_unit_exp
        units = Unit.query.filter_by(is_active=True).all()
        unit_data = []
        for unit in units:
            rev = db.session.query(func.sum(Invoice.final_amount)).join(
                ServiceRecord, Invoice.service_record_id == ServiceRecord.id
            ).filter(
                Invoice.status == 'paid',
                ServiceRecord.unit_id == unit.id,
                func.date(Invoice.paid_at) >= month_start
            ).scalar() or 0
            exp = db.session.query(func.sum(UnitExpense.amount)).filter(
                UnitExpense.unit_id == unit.id,
                UnitExpense.date >= month_start
            ).scalar() or 0
            unit_data.append({'unit': unit, 'revenue': rev, 'expense': exp, 'net': rev - exp})
        recent_invoices = Invoice.query.order_by(Invoice.created_at.desc()).limit(10).all()
        return render_template('accounting/dashboard.html',
                               monthly_revenue=monthly_revenue,
                               monthly_shared=monthly_shared,
                               monthly_unit_exp=monthly_unit_exp,
                               net_profit=net_profit,
                               unit_data=unit_data,
                               recent_invoices=recent_invoices)

    @app.route('/accounting/expenses', methods=['GET', 'POST'])
    @login_required
    def accounting_expenses():
        if current_user.role not in ('admin', 'muhasebe'):
            flash('Bu sayfaya erişim yetkiniz yok.', 'danger')
            return redirect(url_for('dashboard'))
        if request.method == 'POST':
            exp_type = request.form.get('exp_type', 'unit')
            amt = float(request.form.get('amount') or 0)
            exp_date = request.form.get('date') or None
            exp_date = datetime.strptime(exp_date, '%Y-%m-%d').date() if exp_date else date.today()
            if exp_type == 'shared':
                exp = SharedExpense(
                    category_id=request.form.get('category_id') or None,
                    amount=amt,
                    description=request.form.get('description', '').strip(),
                    date=exp_date,
                    created_by=current_user.id
                )
            else:
                exp = UnitExpense(
                    unit_id=request.form['unit_id'],
                    category=request.form.get('category', '').strip(),
                    amount=amt,
                    description=request.form.get('description', '').strip(),
                    date=exp_date,
                    created_by=current_user.id
                )
            db.session.add(exp)
            db.session.commit()
            flash('Gider kaydedildi.', 'success')
            return redirect(url_for('accounting_expenses'))
        unit_expenses = UnitExpense.query.order_by(UnitExpense.date.desc()).all()
        shared_expenses = SharedExpense.query.order_by(SharedExpense.date.desc()).all()
        units = Unit.query.filter_by(is_active=True).all()
        categories = SharedExpenseCategory.query.filter_by(is_active=True).all()
        return render_template('accounting/expenses.html',
                               unit_expenses=unit_expenses,
                               shared_expenses=shared_expenses,
                               units=units,
                               categories=categories)

    @app.route('/accounting/revenues')
    @login_required
    def accounting_revenues():
        if current_user.role not in ('admin', 'muhasebe'):
            flash('Bu sayfaya erişim yetkiniz yok.', 'danger')
            return redirect(url_for('dashboard'))
        invoices = Invoice.query.order_by(Invoice.created_at.desc()).all()
        return render_template('accounting/revenues.html', invoices=invoices)

    @app.route('/accounting/reports')
    @login_required
    def accounting_reports():
        if current_user.role not in ('admin', 'muhasebe'):
            flash('Bu sayfaya erişim yetkiniz yok.', 'danger')
            return redirect(url_for('dashboard'))
        start_str = request.args.get('start', '')
        end_str = request.args.get('end', '')
        today = date.today()
        start_date = datetime.strptime(start_str, '%Y-%m-%d').date() if start_str else today.replace(day=1)
        end_date = datetime.strptime(end_str, '%Y-%m-%d').date() if end_str else today
        units = Unit.query.filter_by(is_active=True).all()
        report_data = []
        for unit in units:
            rev = db.session.query(func.sum(Invoice.final_amount)).join(
                ServiceRecord, Invoice.service_record_id == ServiceRecord.id
            ).filter(
                Invoice.status == 'paid',
                ServiceRecord.unit_id == unit.id,
                func.date(Invoice.paid_at) >= start_date,
                func.date(Invoice.paid_at) <= end_date
            ).scalar() or 0
            exp = db.session.query(func.sum(UnitExpense.amount)).filter(
                UnitExpense.unit_id == unit.id,
                UnitExpense.date >= start_date,
                UnitExpense.date <= end_date
            ).scalar() or 0
            report_data.append({'unit': unit, 'revenue': rev, 'expense': exp, 'net': rev - exp})
        shared_total = db.session.query(func.sum(SharedExpense.amount)).filter(
            SharedExpense.date >= start_date,
            SharedExpense.date <= end_date
        ).scalar() or 0
        total_rev = sum(r['revenue'] for r in report_data)
        total_exp = sum(r['expense'] for r in report_data) + shared_total
        return render_template('accounting/reports.html',
                               report_data=report_data,
                               shared_total=shared_total,
                               total_rev=total_rev,
                               total_exp=total_exp,
                               net=total_rev - total_exp,
                               start_date=start_date,
                               end_date=end_date)

    # ─── SETTINGS ────────────────────────────────────────────────────────────

    @app.route('/settings', methods=['GET', 'POST'])
    @login_required
    def settings():
        if current_user.role != 'admin':
            flash('Bu sayfaya erişim yetkiniz yok.', 'danger')
            return redirect(url_for('dashboard'))
        if request.method == 'POST':
            action = request.form.get('action')

            if action == 'add_unit':
                u = Unit(name=request.form['name'].strip(),
                         description=request.form.get('description', '').strip())
                db.session.add(u)
                db.session.commit()
                flash('Birim eklendi.', 'success')

            elif action == 'toggle_unit':
                unit = Unit.query.get_or_404(int(request.form['unit_id']))
                unit.is_active = not unit.is_active
                db.session.commit()
                flash('Birim durumu güncellendi.', 'success')

            elif action == 'add_user':
                if User.query.filter_by(username=request.form['username']).first():
                    flash('Bu kullanıcı adı zaten kullanılıyor.', 'warning')
                else:
                    new_user = User(
                        username=request.form['username'].strip(),
                        full_name=request.form['full_name'].strip(),
                        role=request.form['role'],
                        unit_id=request.form.get('unit_id') or None
                    )
                    new_user.set_password(request.form['password'])
                    db.session.add(new_user)
                    db.session.commit()
                    flash('Kullanıcı eklendi.', 'success')

            elif action == 'toggle_user':
                user = User.query.get_or_404(int(request.form['user_id']))
                if user.id != current_user.id:
                    user.is_active = not user.is_active
                    db.session.commit()
                    flash('Kullanıcı durumu güncellendi.', 'success')

            elif action == 'add_category':
                cat = SharedExpenseCategory(
                    name=request.form['name'].strip(),
                    description=request.form.get('description', '').strip()
                )
                db.session.add(cat)
                db.session.commit()
                flash('Kategori eklendi.', 'success')

            elif action == 'toggle_category':
                cat = SharedExpenseCategory.query.get_or_404(int(request.form['category_id']))
                cat.is_active = not cat.is_active
                db.session.commit()
                flash('Kategori durumu güncellendi.', 'success')

            elif action == 'save_settings':
                for key in ['company_name', 'company_phone', 'company_address', 'tax_no']:
                    val = request.form.get(key, '')
                    s = AppSetting.query.filter_by(key=key).first()
                    if s:
                        s.value = val
                    else:
                        db.session.add(AppSetting(key=key, value=val))
                db.session.commit()
                flash('Ayarlar kaydedildi.', 'success')

            return redirect(url_for('settings'))

        units = Unit.query.order_by(Unit.name).all()
        users = User.query.order_by(User.full_name).all()
        categories = SharedExpenseCategory.query.order_by(SharedExpenseCategory.name).all()
        app_settings = {s.key: s.value for s in AppSetting.query.all()}
        return render_template('settings/index.html', units=units, users=users,
                               categories=categories, app_settings=app_settings)

    # ─── API ─────────────────────────────────────────────────────────────────

    @app.route('/api/vehicles/search')
    @login_required
    def api_vehicle_search():
        plate = request.args.get('plate', '').strip().upper().replace(' ', '')
        if not plate:
            return jsonify({'found': False})
        v = Vehicle.query.filter_by(plate=plate).first()
        if not v:
            return jsonify({'found': False})
        return jsonify({
            'found': True,
            'id': v.id,
            'plate': v.plate,
            'brand': v.brand or '',
            'model': v.model or '',
            'year': v.year or '',
            'color': v.color or '',
            'owner_name': v.owner.full_name if v.owner else '',
            'owner_phone': v.owner.phone if v.owner else ''
        })

    @app.route('/api/service/list')
    @login_required
    def api_service_list():
        records = ServiceRecord.query.order_by(ServiceRecord.created_at.desc()).limit(50).all()
        return jsonify([{
            'id': r.id,
            'record_no': r.record_no,
            'plate': r.vehicle.plate,
            'status': r.status,
            'created_at': r.created_at.isoformat()
        } for r in records])

    @app.route('/api/service/new', methods=['POST'])
    @login_required
    def api_service_new():
        data = request.get_json()
        plate = data.get('plate', '').strip().upper()
        v = Vehicle.query.filter_by(plate=plate).first()
        if not v:
            return jsonify({'success': False, 'message': 'Araç bulunamadı'}), 404
        record_no = generate_record_no('SRV', ServiceRecord, 'record_no')
        rec = ServiceRecord(
            record_no=record_no,
            vehicle_id=v.id,
            accepted_by=current_user.id,
            complaint=data.get('complaint', '')
        )
        db.session.add(rec)
        db.session.commit()
        return jsonify({'success': True, 'record_no': record_no, 'id': rec.id})

    # ─── SYNC ────────────────────────────────────────────────────────────────

    @app.route('/sync', methods=['GET', 'POST'])
    @login_required
    def sync():
        if current_user.role != 'admin':
            flash('Bu sayfaya erişim yetkiniz yok.', 'danger')
            return redirect(url_for('dashboard'))
        if request.method == 'POST':
            log = SyncLog(
                sync_type='manual',
                status='success',
                records_synced=0,
                notes='Manuel senkronizasyon tamamlandı.',
                performed_by=current_user.id
            )
            db.session.add(log)
            db.session.commit()
            flash('Senkronizasyon tamamlandı.', 'success')
            return redirect(url_for('sync'))
        logs = SyncLog.query.order_by(SyncLog.sync_time.desc()).limit(20).all()
        return render_template('sync.html', logs=logs)

    # ─── CONTEXT PROCESSORS ──────────────────────────────────────────────────

    @app.context_processor
    def inject_globals():
        app_settings = {}
        try:
            app_settings = {s.key: s.value for s in AppSetting.query.all()}
        except Exception:
            pass
        return {'app_settings': app_settings, 'now': datetime.utcnow()}

    # ─── SMART API ───────────────────────────────────────────────────────────

    @app.route('/api/smart/diagnostics', methods=['POST'])
    @login_required
    def smart_diagnostics():
        """AI-like diagnostic suggestions based on complaint keywords."""
        complaint = request.json.get('complaint', '').lower()
        suggestions = []

        diagnosis_map = {
            'fren': ['Fren balatası aşınması', 'Fren diski kontrolü', 'Fren hidroliği seviyesi', 'El freni ayarı'],
            'brake': ['Fren balatası aşınması', 'Fren diski kontrolü', 'Fren hidroliği seviyesi'],
            'motor': ['Motor yağı değişimi', 'Ateşleme sistemi kontrolü', 'Hava filtresi değişimi', 'Yakıt filtresi kontrolü'],
            'engine': ['Motor yağı değişimi', 'Ateşleme sistemi kontrolü', 'Hava filtresi değişimi'],
            'yağ': ['Motor yağı değişimi', 'Yağ kaçağı tespiti', 'Yağ filtresi değişimi'],
            'titreşim': ['Balans ayarı', 'Amortisör kontrolü', 'Rot-balans', 'Tekerlek balansı'],
            'ses': ['Egzoz sistemi kontrolü', 'Süspansiyon kontrolü', 'Rulman kontrolü', 'Kavrama diski'],
            'çalışmıyor': ['Akü testi', 'Marş motoru kontrolü', 'Kontak sistemi', 'Yakıt pompası kontrolü'],
            'aküsü': ['Akü şarj testi', 'Akü değişimi', 'Alternatör kontrolü'],
            'klima': ['Klima gazı dolumu', 'Klima filtresi değişimi', 'Kompresör kontrolü'],
            'lastik': ['Lastik değişimi', 'Lastik tamiri', 'Rot-balans ayarı'],
            'ateşleme': ['Buji değişimi', 'Distribütör kontrolü', 'Ateşleme kabloları'],
            'yakıt': ['Yakıt filtresi', 'Enjektör temizliği', 'Yakıt pompası', 'Karbüratör ayarı'],
            'soğutma': ['Antifriz değişimi', 'Termostat kontrolü', 'Su pompası', 'Radyatör temizliği'],
            'şanzıman': ['Şanzıman yağı kontrolü', 'Vites mekanizması', 'Kavrama ayarı'],
            'elektrik': ['Elektrik tesisatı kontrolü', 'Sigorta paneli', 'Alternatör testi', 'Akü kontrolü'],
            'far': ['Far ayarı', 'Ampul değişimi', 'Far camı temizliği'],
            'direksiyon': ['Direksiyon pompası', 'Rot başı kontrolü', 'Balans ayarı'],
            'egzoz': ['Egzoz muayenesi', 'Katalitik konvertör', 'Lambda sensörü'],
            'debriyaj': ['Debriyaj balatası', 'Debriyaj silindiri', 'Kavrama ayarı'],
        }

        found = set()
        for keyword, items in diagnosis_map.items():
            if keyword in complaint:
                for item in items:
                    if item not in found:
                        found.add(item)
                        suggestions.append(item)

        cost_estimates = {
            'Fren balatası aşınması': (300, 800),
            'Motor yağı değişimi': (200, 500),
            'Balans ayarı': (150, 300),
            'Akü testi': (50, 100),
            'Klima gazı dolumu': (400, 800),
            'Lastik değişimi': (500, 2000),
            'Rot-balans': (200, 400),
        }

        result = []
        for s in suggestions[:8]:
            est = cost_estimates.get(s)
            result.append({
                'suggestion': s,
                'min_cost': est[0] if est else None,
                'max_cost': est[1] if est else None,
            })

        return jsonify({'suggestions': result, 'count': len(result)})

    @app.route('/api/smart/alerts')
    @login_required
    def smart_alerts():
        """Smart alerts: expiring insurance/inspections, overdue services."""
        alerts = []
        today = date.today()

        vehicles = Vehicle.query.filter(Vehicle.insurance_expiry.isnot(None)).all()
        for v in vehicles:
            if v.insurance_expiry:
                days = (v.insurance_expiry - today).days
                if 0 <= days <= 30:
                    alerts.append({
                        'type': 'warning',
                        'icon': 'shield-exclamation',
                        'title': f'{v.plate} - Sigorta Süresi Dolmak Üzere',
                        'message': f'{days} gün içinde sigorta bitiyor',
                        'link': url_for('vehicle_detail', vid=v.id),
                        'priority': 2 if days <= 7 else 1
                    })
                elif days < 0:
                    alerts.append({
                        'type': 'danger',
                        'icon': 'shield-x',
                        'title': f'{v.plate} - Sigorta Süresi Doldu!',
                        'message': f'{abs(days)} gün önce sigorta bitti',
                        'link': url_for('vehicle_detail', vid=v.id),
                        'priority': 3
                    })

        for v in vehicles:
            if v.inspection_expiry:
                days = (v.inspection_expiry - today).days
                if 0 <= days <= 30:
                    alerts.append({
                        'type': 'warning',
                        'icon': 'clipboard-check',
                        'title': f'{v.plate} - Muayene Süresi Dolmak Üzere',
                        'message': f'{days} gün içinde muayene bitiyor',
                        'link': url_for('vehicle_detail', vid=v.id),
                        'priority': 2 if days <= 7 else 1
                    })

        overdue_threshold = datetime.utcnow() - timedelta(days=3)
        overdue = ServiceRecord.query.filter(
            ServiceRecord.status == 'waiting',
            ServiceRecord.created_at < overdue_threshold
        ).all()
        for sr in overdue:
            alerts.append({
                'type': 'danger',
                'icon': 'clock-history',
                'title': f'{sr.record_no} - Gecikmiş Servis',
                'message': f'{sr.vehicle.plate} aracı {(datetime.utcnow() - sr.created_at).days} gündür bekliyor',
                'link': url_for('service_detail', rid=sr.id),
                'priority': 3
            })

        completed_threshold = datetime.utcnow() - timedelta(days=1)
        stuck = ServiceRecord.query.filter(
            ServiceRecord.status == 'completed',
            ServiceRecord.updated_at < completed_threshold
        ).all()
        for sr in stuck:
            alerts.append({
                'type': 'info',
                'icon': 'check-circle',
                'title': f'{sr.record_no} - Teslim Bekliyor',
                'message': f'{sr.vehicle.plate} tamamlandı, teslim bekleniyor',
                'link': url_for('service_detail', rid=sr.id),
                'priority': 1
            })

        alerts.sort(key=lambda x: x['priority'], reverse=True)
        return jsonify({'alerts': alerts[:20], 'count': len(alerts)})

    @app.route('/api/smart/search')
    @login_required
    def smart_search():
        """Global search across all entities."""
        q = request.args.get('q', '').strip()
        if len(q) < 2:
            return jsonify({'results': []})

        results = []
        ql = f'%{q}%'

        vehicles = Vehicle.query.filter(
            db.or_(Vehicle.plate.ilike(ql), Vehicle.brand.ilike(ql), Vehicle.model.ilike(ql))
        ).limit(5).all()
        for v in vehicles:
            results.append({
                'type': 'vehicle',
                'icon': 'car-front',
                'title': v.plate,
                'subtitle': f'{v.brand} {v.model} {v.year or ""}',
                'link': url_for('vehicle_detail', vid=v.id)
            })

        customers = Customer.query.filter(
            db.or_(Customer.full_name.ilike(ql), Customer.phone.ilike(ql))
        ).limit(5).all()
        for c in customers:
            results.append({
                'type': 'customer',
                'icon': 'person',
                'title': c.full_name,
                'subtitle': c.phone or '',
                'link': url_for('customer_edit', cid=c.id)
            })

        records = ServiceRecord.query.filter(
            db.or_(ServiceRecord.record_no.ilike(ql), ServiceRecord.complaint.ilike(ql))
        ).limit(5).all()
        for r in records:
            results.append({
                'type': 'service',
                'icon': 'tools',
                'title': r.record_no,
                'subtitle': f'{r.vehicle.plate} - {r.complaint[:50] if r.complaint else ""}',
                'link': url_for('service_detail', rid=r.id)
            })

        return jsonify({'results': results})

    @app.route('/api/smart/dashboard')
    @login_required
    def smart_dashboard_data():
        """Real-time dashboard stats and chart data."""
        today = date.today()

        revenue_data = []
        labels = []
        for i in range(5, -1, -1):
            month_start = today.replace(day=1) - timedelta(days=i*30)
            month_end = (month_start.replace(day=28) + timedelta(days=4)).replace(day=1)
            rev = db.session.query(func.sum(Invoice.final_amount)).filter(
                Invoice.status == 'paid',
                func.date(Invoice.paid_at) >= month_start,
                func.date(Invoice.paid_at) < month_end
            ).scalar() or 0
            revenue_data.append(float(rev))
            labels.append(month_start.strftime('%b %Y'))

        status_counts = db.session.query(
            ServiceRecord.status, func.count(ServiceRecord.id)
        ).group_by(ServiceRecord.status).all()
        status_data = {s: c for s, c in status_counts}

        units = Unit.query.filter_by(is_active=True).all()
        unit_data = []
        for u in units:
            count = ServiceRecord.query.filter_by(unit_id=u.id).count()
            unit_rev = db.session.query(func.sum(Invoice.final_amount)).join(
                ServiceRecord, Invoice.service_record_id == ServiceRecord.id
            ).filter(
                ServiceRecord.unit_id == u.id,
                Invoice.status == 'paid'
            ).scalar() or 0
            unit_data.append({'name': u.name, 'count': count, 'revenue': float(unit_rev)})

        today_services = ServiceRecord.query.filter(
            func.date(ServiceRecord.created_at) == today
        ).count()

        completed = ServiceRecord.query.filter(
            ServiceRecord.status.in_(['completed', 'delivered']),
            ServiceRecord.actual_delivery.isnot(None)
        ).all()
        avg_time = 0
        if completed:
            total_hours = sum(
                (sr.actual_delivery - sr.created_at).total_seconds() / 3600
                for sr in completed if sr.actual_delivery
            )
            avg_time = round(total_hours / len(completed), 1)

        total_vehicles = Vehicle.query.count()
        total_customers = Customer.query.count()
        total_invoices = Invoice.query.filter_by(status='paid').count()
        total_revenue = db.session.query(func.sum(Invoice.final_amount)).filter(
            Invoice.status == 'paid'
        ).scalar() or 0

        return jsonify({
            'revenue_chart': {'labels': labels, 'data': revenue_data},
            'status_chart': {
                'waiting': status_data.get('waiting', 0),
                'in_progress': status_data.get('in_progress', 0),
                'completed': status_data.get('completed', 0),
                'delivered': status_data.get('delivered', 0),
            },
            'unit_data': unit_data,
            'today_services': today_services,
            'avg_completion_hours': avg_time,
            'total_vehicles': total_vehicles,
            'total_customers': total_customers,
            'total_invoices': total_invoices,
            'total_revenue': float(total_revenue),
        })

    @app.route('/api/smart/suggestions')
    @login_required
    def smart_suggestions():
        """Autocomplete for services and parts catalog."""
        q = request.args.get('q', '').lower()
        catalog = [
            {'name': 'Yağ Değişimi', 'type': 'service', 'price': 350},
            {'name': 'Yağ Filtresi', 'type': 'part', 'price': 120},
            {'name': 'Hava Filtresi', 'type': 'part', 'price': 150},
            {'name': 'Polen Filtresi', 'type': 'part', 'price': 200},
            {'name': 'Yakıt Filtresi', 'type': 'part', 'price': 180},
            {'name': 'Fren Balatası (Ön)', 'type': 'part', 'price': 450},
            {'name': 'Fren Balatası (Arka)', 'type': 'part', 'price': 380},
            {'name': 'Fren Diski', 'type': 'part', 'price': 600},
            {'name': 'Rot Balans', 'type': 'service', 'price': 250},
            {'name': 'Lastik Değişimi (4 Adet)', 'type': 'service', 'price': 200},
            {'name': 'Muayene Hazırlık', 'type': 'service', 'price': 300},
            {'name': 'Aks Körüğü', 'type': 'part', 'price': 280},
            {'name': 'Amortisör (Ön)', 'type': 'part', 'price': 800},
            {'name': 'Amortisör (Arka)', 'type': 'part', 'price': 700},
            {'name': 'Triger Seti', 'type': 'part', 'price': 1200},
            {'name': 'Klima Gazı Dolumu', 'type': 'service', 'price': 600},
            {'name': 'Akü Değişimi', 'type': 'part', 'price': 900},
            {'name': 'Buji Takımı', 'type': 'part', 'price': 400},
            {'name': 'Distribütör Kapağı', 'type': 'part', 'price': 200},
            {'name': 'Termostat', 'type': 'part', 'price': 250},
            {'name': 'Su Pompası', 'type': 'part', 'price': 450},
            {'name': 'Radyatör Temizliği', 'type': 'service', 'price': 200},
            {'name': 'Antifriz Değişimi', 'type': 'service', 'price': 150},
            {'name': 'Şanzıman Yağı', 'type': 'service', 'price': 300},
            {'name': 'Diferansiyel Yağı', 'type': 'service', 'price': 250},
            {'name': 'Egzoz Kontrolü', 'type': 'service', 'price': 100},
            {'name': 'Far Ayarı', 'type': 'service', 'price': 100},
            {'name': 'Direksiyon Kutusu', 'type': 'part', 'price': 1500},
            {'name': 'Debriyaj Seti', 'type': 'part', 'price': 1800},
            {'name': 'Elektrik Tesisatı Kontrolü', 'type': 'service', 'price': 200},
            {'name': 'Motor Temizliği', 'type': 'service', 'price': 300},
            {'name': 'Klima Filtresi', 'type': 'part', 'price': 200},
            {'name': 'Silecek Takımı', 'type': 'part', 'price': 180},
            {'name': 'Kablosuz Kilitleme Tamiri', 'type': 'service', 'price': 150},
            {'name': 'OBD Diagnostik Tarama', 'type': 'service', 'price': 200},
            {'name': 'İşçilik Ücreti', 'type': 'service', 'price': 100},
        ]

        if q:
            filtered = [item for item in catalog if q in item['name'].lower()]
        else:
            filtered = catalog

        return jsonify({'items': filtered[:15]})

    @app.route('/api/smart/kanban')
    @login_required
    def smart_kanban():
        """Service kanban board data."""
        records = ServiceRecord.query.filter(
            ServiceRecord.status != 'delivered'
        ).order_by(ServiceRecord.created_at.desc()).limit(50).all()

        result = {
            'waiting': [],
            'in_progress': [],
            'completed': [],
        }

        for r in records:
            item = {
                'id': r.id,
                'record_no': r.record_no,
                'plate': r.vehicle.plate,
                'vehicle': f'{r.vehicle.brand} {r.vehicle.model}',
                'complaint': (r.complaint or '')[:80],
                'unit': r.unit.name if r.unit else None,
                'accepted_by': r.acceptor.full_name if r.acceptor else None,
                'created_at': r.created_at.strftime('%d.%m %H:%M'),
                'hours_ago': round((datetime.utcnow() - r.created_at).total_seconds() / 3600, 1),
                'link': url_for('service_detail', rid=r.id),
            }
            if r.status in result:
                result[r.status].append(item)

        return jsonify(result)

    @app.route('/api/vehicles/<int:vid>/health')
    @login_required
    def vehicle_health(vid):
        """Smart vehicle health score based on service history."""
        v = db.session.get(Vehicle, vid)
        if not v:
            abort(404)

        score = 100
        warnings = []
        today = date.today()

        if v.insurance_expiry:
            days = (v.insurance_expiry - today).days
            if days < 0:
                score -= 20
                warnings.append({'level': 'danger', 'msg': f'Sigorta {abs(days)} gün önce bitti!'})
            elif days < 30:
                score -= 10
                warnings.append({'level': 'warning', 'msg': f'Sigorta {days} gün sonra bitiyor'})
        else:
            score -= 10
            warnings.append({'level': 'info', 'msg': 'Sigorta tarihi girilmemiş'})

        if v.inspection_expiry:
            days = (v.inspection_expiry - today).days
            if days < 0:
                score -= 20
                warnings.append({'level': 'danger', 'msg': f'Muayene {abs(days)} gün önce bitti!'})
            elif days < 30:
                score -= 10
                warnings.append({'level': 'warning', 'msg': f'Muayene {days} gün sonra bitiyor'})
        else:
            score -= 10
            warnings.append({'level': 'info', 'msg': 'Muayene tarihi girilmemiş'})

        total_services = len(v.service_records)
        if total_services == 0:
            warnings.append({'level': 'info', 'msg': 'Henüz servis kaydı yok'})
        else:
            last_service = max(v.service_records, key=lambda x: x.created_at)
            days_since = (datetime.utcnow() - last_service.created_at).days
            if days_since > 365:
                score -= 15
                warnings.append({'level': 'warning', 'msg': f'Son servis {days_since} gün önce'})

        score = max(0, min(100, score))

        if score >= 80:
            health_label = 'İyi'
            health_color = 'success'
        elif score >= 60:
            health_label = 'Orta'
            health_color = 'warning'
        else:
            health_label = 'Kritik'
            health_color = 'danger'

        return jsonify({
            'score': score,
            'label': health_label,
            'color': health_color,
            'warnings': warnings,
            'total_services': total_services,
        })

    return app
