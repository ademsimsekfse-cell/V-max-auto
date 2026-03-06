from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class Unit(db.Model):
    __tablename__ = 'units'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(255))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    users = db.relationship('User', backref='unit', lazy=True)
    service_records = db.relationship('ServiceRecord', backref='unit', lazy=True)


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(150), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='usta')  # admin, usta, muhasebe
    unit_id = db.Column(db.Integer, db.ForeignKey('units.id'), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def role_display(self):
        roles = {'admin': 'Yönetici', 'usta': 'Usta', 'muhasebe': 'Muhasebe'}
        return roles.get(self.role, self.role)


class SharedExpenseCategory(db.Model):
    __tablename__ = 'shared_expense_categories'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(255))
    is_active = db.Column(db.Boolean, default=True)
    expenses = db.relationship('SharedExpense', backref='category', lazy=True)


class SharedExpense(db.Model):
    __tablename__ = 'shared_expenses'
    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey('shared_expense_categories.id'))
    amount = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(255))
    date = db.Column(db.Date, default=datetime.utcnow().date)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class UnitExpense(db.Model):
    __tablename__ = 'unit_expenses'
    id = db.Column(db.Integer, primary_key=True)
    unit_id = db.Column(db.Integer, db.ForeignKey('units.id'), nullable=False)
    category = db.Column(db.String(100))
    amount = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(255))
    date = db.Column(db.Date, default=datetime.utcnow().date)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    unit_ref = db.relationship('Unit', backref='unit_expenses', foreign_keys=[unit_id])


class Customer(db.Model):
    __tablename__ = 'customers'
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(150), nullable=False)
    phone = db.Column(db.String(20))
    email = db.Column(db.String(120))
    address = db.Column(db.Text)
    id_number = db.Column(db.String(20))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    vehicles = db.relationship('Vehicle', backref='owner', lazy=True)


class Vehicle(db.Model):
    __tablename__ = 'vehicles'
    id = db.Column(db.Integer, primary_key=True)
    plate = db.Column(db.String(20), unique=True, nullable=False)
    brand = db.Column(db.String(100))
    model = db.Column(db.String(100))
    year = db.Column(db.Integer)
    color = db.Column(db.String(50))
    engine_no = db.Column(db.String(100))
    chassis_no = db.Column(db.String(100))
    owner_id = db.Column(db.Integer, db.ForeignKey('customers.id'))
    insurance_expiry = db.Column(db.Date)
    inspection_expiry = db.Column(db.Date)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    service_records = db.relationship('ServiceRecord', backref='vehicle', lazy=True)


class ServiceRecord(db.Model):
    __tablename__ = 'service_records'
    id = db.Column(db.Integer, primary_key=True)
    record_no = db.Column(db.String(20), unique=True)
    vehicle_id = db.Column(db.Integer, db.ForeignKey('vehicles.id'), nullable=False)
    unit_id = db.Column(db.Integer, db.ForeignKey('units.id'))
    accepted_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    status = db.Column(db.String(20), default='waiting')  # waiting, in_progress, completed, delivered
    complaint = db.Column(db.Text)
    delivery_person_name = db.Column(db.String(150))
    delivery_person_phone = db.Column(db.String(20))
    mileage = db.Column(db.Integer)
    fuel_level = db.Column(db.String(20))
    estimated_delivery = db.Column(db.DateTime)
    actual_delivery = db.Column(db.DateTime)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    acceptor = db.relationship('User', backref='accepted_records', foreign_keys=[accepted_by])
    tasks = db.relationship('ServiceTask', backref='service_record', lazy=True)
    quotes = db.relationship('Quote', backref='service_record', lazy=True)
    invoices = db.relationship('Invoice', backref='service_record', lazy=True)


class ServiceTask(db.Model):
    __tablename__ = 'service_tasks'
    id = db.Column(db.Integer, primary_key=True)
    service_record_id = db.Column(db.Integer, db.ForeignKey('service_records.id'), nullable=False)
    description = db.Column(db.Text, nullable=False)
    technician_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    status = db.Column(db.String(20), default='pending')
    labor_hours = db.Column(db.Float, default=0)
    parts_cost = db.Column(db.Float, default=0)
    labor_cost = db.Column(db.Float, default=0)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    technician = db.relationship('User', foreign_keys=[technician_id])


class Quote(db.Model):
    __tablename__ = 'quotes'
    id = db.Column(db.Integer, primary_key=True)
    quote_no = db.Column(db.String(20), unique=True)
    service_record_id = db.Column(db.Integer, db.ForeignKey('service_records.id'), nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    total_amount = db.Column(db.Float, default=0)
    tax_rate = db.Column(db.Float, default=18)
    tax_amount = db.Column(db.Float, default=0)
    discount = db.Column(db.Float, default=0)
    final_amount = db.Column(db.Float, default=0)
    status = db.Column(db.String(20), default='draft')
    notes = db.Column(db.Text)
    valid_until = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    creator = db.relationship('User', foreign_keys=[created_by])
    items = db.relationship('QuoteItem', backref='quote', lazy=True, cascade='all, delete-orphan')


class QuoteItem(db.Model):
    __tablename__ = 'quote_items'
    id = db.Column(db.Integer, primary_key=True)
    quote_id = db.Column(db.Integer, db.ForeignKey('quotes.id'), nullable=False)
    description = db.Column(db.String(255), nullable=False)
    quantity = db.Column(db.Float, default=1)
    unit_price = db.Column(db.Float, default=0)
    total_price = db.Column(db.Float, default=0)
    item_type = db.Column(db.String(20), default='service')


class Invoice(db.Model):
    __tablename__ = 'invoices'
    id = db.Column(db.Integer, primary_key=True)
    invoice_no = db.Column(db.String(20), unique=True)
    service_record_id = db.Column(db.Integer, db.ForeignKey('service_records.id'), nullable=False)
    quote_id = db.Column(db.Integer, db.ForeignKey('quotes.id'), nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    subtotal = db.Column(db.Float, default=0)
    tax_rate = db.Column(db.Float, default=18)
    tax_amount = db.Column(db.Float, default=0)
    discount = db.Column(db.Float, default=0)
    final_amount = db.Column(db.Float, default=0)
    status = db.Column(db.String(20), default='draft')
    payment_method = db.Column(db.String(50))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    paid_at = db.Column(db.DateTime)
    creator = db.relationship('User', foreign_keys=[created_by])
    items = db.relationship('InvoiceItem', backref='invoice', lazy=True, cascade='all, delete-orphan')


class InvoiceItem(db.Model):
    __tablename__ = 'invoice_items'
    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoices.id'), nullable=False)
    description = db.Column(db.String(255), nullable=False)
    quantity = db.Column(db.Float, default=1)
    unit_price = db.Column(db.Float, default=0)
    total_price = db.Column(db.Float, default=0)
    item_type = db.Column(db.String(20), default='service')


class SyncLog(db.Model):
    __tablename__ = 'sync_logs'
    id = db.Column(db.Integer, primary_key=True)
    sync_time = db.Column(db.DateTime, default=datetime.utcnow)
    sync_type = db.Column(db.String(50))
    status = db.Column(db.String(20))
    records_synced = db.Column(db.Integer, default=0)
    notes = db.Column(db.Text)
    performed_by = db.Column(db.Integer, db.ForeignKey('users.id'))


class AppSetting(db.Model):
    __tablename__ = 'app_settings'
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.Text)
    description = db.Column(db.String(255))
