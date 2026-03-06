import os
from datetime import datetime, date
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

    return app
