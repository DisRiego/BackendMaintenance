# app/maintenance/models.py
from datetime import datetime
from sqlalchemy import (
    Table, Column, Integer, String, DateTime, JSON, ForeignKey,
    Float, Date, Boolean, Numeric, func, CheckConstraint
)
from sqlalchemy.orm import relationship, validates
from app.database import Base
import json
import os
import firebase_admin
from firebase_admin import credentials, storage
from dotenv import load_dotenv


# Carga de variables de entorno
load_dotenv()

# 1) Leer las credenciales JSON desde la variable de entorno
raw = os.getenv("FIREBASE_CREDENTIALS")
if not raw:
    raise ValueError("FIREBASE_CREDENTIALS no está definido en .env o está vacío.")
raw = raw.strip()
if (raw.startswith("'") and raw.endswith("'")) or (raw.startswith('"') and raw.endswith('"')):
    raw = raw[1:-1]
unescaped = raw.encode("utf-8").decode("unicode_escape")
firebase_credentials = json.loads(unescaped)

# Asegurar que la private_key tenga saltos de línea correctos
firebase_credentials["private_key"] = firebase_credentials["private_key"].replace("\\n", "\n").strip()

# 2) Inicializar Firebase Admin con el bucket de Storage
storage_bucket = os.getenv("FIREBASE_STORAGE_BUCKET")
if not storage_bucket:
    raise ValueError("FIREBASE_STORAGE_BUCKET no está definido en .env o está vacío.")
storage_bucket = storage_bucket.strip()

if not firebase_admin._apps:
    cred = credentials.Certificate(firebase_credentials)
    firebase_admin.initialize_app(cred, {"storageBucket": storage_bucket})

# 3) Objeto bucket global
bucket = storage.bucket()

# Tablas de autenticación
user_role_table = Table(
    "user_rol", Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id"), primary_key=True),
    Column("rol_id",  Integer, ForeignKey("rol.id"),   primary_key=True),
    extend_existing=True
)
role_permission_table = Table(
    "rol_permission", Base.metadata,
    Column("rol_id",        Integer, ForeignKey("rol.id"),        primary_key=True),
    Column("permission_id", Integer, ForeignKey("permission.id"), primary_key=True),
    extend_existing=True
)

class Role(Base):
    __tablename__ = "rol"
    __table_args__ = {'extend_existing': True}

    id          = Column(Integer, primary_key=True, index=True)
    name        = Column(String, unique=True, index=True)
    description = Column(String, index=True)
    status      = Column(Integer, ForeignKey('vars.id'), nullable=False)

    permissions = relationship("Permission", secondary=role_permission_table, back_populates="roles")
    users       = relationship("User",       secondary=user_role_table,      back_populates="roles")
    vars        = relationship('Vars', back_populates='role')

class Permission(Base):
    __tablename__ = "permission"
    __table_args__ = {'extend_existing': True}

    id          = Column(Integer, primary_key=True, index=True)
    name        = Column(String, unique=True, index=True)
    description = Column(String, index=True)
    category    = Column(String, index=True)

    roles = relationship("Role", secondary=role_permission_table, back_populates="permissions")

class Vars(Base):
    __tablename__ = 'vars'

    id   = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)

    role = relationship('Role', back_populates='vars')

# Modelos de IoT y dispositivos
class DeviceCategories(Base):
    __tablename__ = 'device_categories'
    __table_args__ = {'extend_existing': True}

    id          = Column(Integer, primary_key=True, index=True)
    name        = Column(String, nullable=False)
    description = Column(String)

    device_types = relationship('DeviceType', back_populates='device_category')

class DeviceType(Base):
    __tablename__ = 'device_type'
    __table_args__ = {'extend_existing': True}

    id                 = Column(Integer, primary_key=True, index=True)
    name               = Column(String(30), nullable=False)
    device_category_id = Column(Integer, ForeignKey('device_categories.id'))

    device_category = relationship('DeviceCategories', back_populates='device_types')
    devices         = relationship('Device', back_populates='device_type')

class Device(Base):
    __tablename__ = 'devices'
    __table_args__ = {'extend_existing': True}

    id               = Column(Integer, primary_key=True, index=True)
    device_type_id   = Column(Integer, ForeignKey('device_type.id'))
    properties       = Column(JSON)

    device_type = relationship('DeviceType', back_populates='devices')
    device_iot  = relationship('DeviceIot', back_populates='device', uselist=False)

class Lot(Base):
    __tablename__ = 'lot'

    id                              = Column(Integer, primary_key=True, index=True)
    name                            = Column(String, nullable=False)
    longitude                       = Column(Float, nullable=False)
    latitude                        = Column(Float, nullable=False)
    extension                       = Column(Float, nullable=False)
    real_estate_registration_number = Column(Integer, nullable=False)
    public_deed                     = Column(String, nullable=True)
    freedom_tradition_certificate   = Column(String, nullable=True)
    payment_interval                = Column(Integer, ForeignKey('payment_interval.id'), nullable=True)
    type_crop_id                    = Column(Integer, ForeignKey('type_crop.id'),       nullable=True)
    planting_date                   = Column(Date,    nullable=True)
    estimated_harvest_date          = Column(Date,    nullable=True)
    state                           = Column('State', Integer, ForeignKey('vars.id'), default=18, nullable=False)

    def __repr__(self):
        return f"<Lot(id={self.id}, name={self.name}, state={self.state})>"

class MaintenanceInterval(Base):
    __tablename__ = 'maintenance_intervals'

    id   = Column(Integer, primary_key=True, index=True)
    name = Column(String(30))
    days = Column(Integer)

class DeviceIot(Base):
    __tablename__ = 'device_iot'
    __table_args__ = {'extend_existing': True}

    id                         = Column(Integer, primary_key=True, index=True)
    serial_number              = Column(Integer, nullable=True)
    model                      = Column(String(45), nullable=True)
    lot_id                     = Column(Integer, ForeignKey('lot.id'), nullable=True)
    installation_date          = Column(DateTime, nullable=True)
    maintenance_interval_id    = Column(Integer, ForeignKey('maintenance_intervals.id'), nullable=True)
    estimated_maintenance_date = Column(DateTime, nullable=True)
    status                     = Column(Integer, ForeignKey('vars.id'), nullable=True)
    device_id                  = Column('devices_id', Integer, ForeignKey('devices.id'), nullable=True)
    price_device               = Column(JSON, nullable=True)
    data_devices               = Column(JSON, nullable=True)

    lot                  = relationship('Lot')
    maintenance_interval = relationship('MaintenanceInterval')
    status_var           = relationship('Vars', foreign_keys=[status])
    device               = relationship('Device', back_populates='device_iot')
    maintenances         = relationship('Maintenance', back_populates='device_iot')

    @validates('status')
    def validate_status(self, key, value):
        valid_ids = [11, 12, 15, 16, 20, 21]
        if value not in valid_ids:
            raise ValueError(f"Estado {value} no válido. Válidos: {valid_ids}")
        return value

# Relaciones predio ↔ usuarios y lotes
class Property(Base):
    __tablename__ = 'property'

    id                              = Column(Integer, primary_key=True, index=True)
    name                            = Column(String, nullable=False)
    longitude                       = Column(Float, nullable=False)
    latitude                        = Column(Float, nullable=False)
    extension                       = Column(Float, nullable=False)
    real_estate_registration_number = Column(Integer, nullable=False)
    public_deed                     = Column(String, nullable=True)
    freedom_tradition_certificate   = Column(String, nullable=True)
    state                           = Column('State', Integer, ForeignKey('vars.id'), default=16, nullable=False)

    property_users = relationship('PropertyUser', back_populates='property')

class PropertyLot(Base):
    __tablename__ = 'property_lot'

    property_id = Column(Integer, ForeignKey('property.id'), primary_key=True)
    lot_id      = Column(Integer, ForeignKey('lot.id'),      primary_key=True)

class PropertyUser(Base):
    __tablename__ = 'user_property'

    property_id = Column(Integer, ForeignKey('property.id'), primary_key=True)
    user_id     = Column(Integer, ForeignKey('users.id'),    primary_key=True)

    property = relationship('Property', back_populates='property_users')
    user     = relationship('User',     back_populates='property_users')

class User(Base):
    __tablename__ = 'users'

    id               = Column(Integer, primary_key=True, index=True)
    name             = Column(String, nullable=False)
    first_last_name  = Column(String, nullable=False)
    second_last_name = Column(String, nullable=False)
    document_number  = Column(String, nullable=False)

    roles           = relationship('Role', secondary=user_role_table, back_populates='users')
    property_users  = relationship('PropertyUser', back_populates='user')
    assignments     = relationship('TechnicianAssignment', back_populates='technician', cascade='all, delete-orphan')

class TypeFailure(Base):
    __tablename__ = 'type_failure'

    id          = Column(Integer, primary_key=True, index=True)
    name        = Column(String(100), nullable=False)
    description = Column(String(45), nullable=False)

class Maintenance(Base):
    __tablename__ = 'maintenance'

    id                    = Column(Integer, primary_key=True, index=True)
    device_iot_id         = Column(Integer, ForeignKey('device_iot.id'), nullable=False)
    type_failure_id       = Column(Integer, ForeignKey('type_failure.id'), nullable=False)
    description_failure   = Column(String, nullable=True)
    date                  = Column(DateTime, default=datetime.now)
    maintenance_status_id = Column(Integer, ForeignKey('vars.id'), nullable=False)

    device_iot   = relationship('DeviceIot', back_populates='maintenances')
    type_failure = relationship('TypeFailure')
    status       = relationship('Vars')
    assignments  = relationship('TechnicianAssignment', back_populates='maintenance', cascade='all, delete-orphan')

class MaintenanceReport(Base):
    __tablename__ = 'maintenance_report'

    id                    = Column(Integer, primary_key=True, index=True)
    lot_id                = Column(Integer, ForeignKey('lot.id'), nullable=False)
    type_failure_id       = Column(Integer, ForeignKey('type_failure.id'), nullable=False)
    description_failure   = Column(String, nullable=True)
    date                  = Column(DateTime, default=datetime.now)
    maintenance_status_id = Column(Integer, ForeignKey('vars.id'), nullable=False)

    lot          = relationship('Lot')
    type_failure = relationship('TypeFailure')
    status       = relationship('Vars')
    assignments  = relationship('TechnicianAssignment', back_populates='report', cascade='all, delete-orphan')

class TechnicianAssignment(Base):
    __tablename__ = 'technician_assignment'

    id              = Column(Integer, primary_key=True, index=True)
    maintenance_id  = Column(Integer, ForeignKey('maintenance.id'), nullable=True)
    report_id       = Column(Integer, ForeignKey('maintenance_report.id'), nullable=True)
    user_id         = Column(Integer, ForeignKey('users.id'), nullable=False)
    assignment_date = Column(DateTime, default=datetime.now)

    __table_args__ = (
        CheckConstraint(
          "(maintenance_id IS NOT NULL AND report_id IS NULL) OR "
          "(maintenance_id IS NULL AND report_id IS NOT NULL)",
          name="ck_assignment_one_fk"
        ),
    )

    maintenance = relationship('Maintenance', back_populates='assignments')
    report      = relationship('MaintenanceReport', back_populates='assignments')
    detail      = relationship('MaintenanceDetail', back_populates='assignment', uselist=False)
    technician  = relationship('User', back_populates='assignments')

class FailureSolution(Base):
    __tablename__ = 'failure_solution'

    id          = Column(Integer, primary_key=True, index=True)
    name        = Column(String, nullable=False)
    description = Column(String)

class MaintenanceDetail(Base):
    __tablename__ = 'maintenance_detail'

    id                          = Column(Integer, primary_key=True, index=True)
    technician_assignment_id    = Column(Integer, ForeignKey('technician_assignment.id'), nullable=False, unique=True)
    fault_remarks               = Column(String, nullable=True)
    evidence_failure_url        = Column(String, nullable=True)
    type_failure_id             = Column(Integer, ForeignKey('type_failure.id'), nullable=False)
    type_maintenance_id        = Column(Integer, ForeignKey('maintenance_type.id'), nullable=False)
    failure_solution_id         = Column(Integer, ForeignKey('failure_solution.id'), nullable=False)
    solution_remarks            = Column(String, nullable=True)
    evidence_solution_url       = Column(String, nullable=True)
    date                        = Column(DateTime, default=datetime.now)

    assignment      = relationship('TechnicianAssignment', back_populates='detail')
    type_failure    = relationship('TypeFailure')
    failure_solution= relationship('FailureSolution')
    maintenance_type = relationship('MaintenanceType', back_populates='details')

class MaintenanceType(Base):
    __tablename__ = 'maintenance_type'
    id   = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False)

    details = relationship('MaintenanceDetail', back_populates='maintenance_type')