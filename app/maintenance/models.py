from sqlalchemy import TIMESTAMP, Column, Date, Integer, String, DateTime, JSON, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime

class Vars(Base):
    __tablename__ = 'vars'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    type = Column(String)
    description = Column(String, nullable=True)

class MaintenanceStatus(Base):
    __tablename__ = 'maintenance_status'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(45))

class TypeFailure(Base):
    __tablename__ = 'type_failure'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100))
    description = Column(String(45), nullable=True)

class FailureSolution(Base):
    __tablename__ = 'failure_solution'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(45))
    description = Column(String(255), nullable=True)

class DeviceIot(Base):
    __tablename__ = 'device_iot'
    
    id = Column(Integer, primary_key=True, index=True)
    serial_number = Column(Integer)
    model = Column(String(45), nullable=True)
    lot_id = Column(Integer, nullable=True)
    installation_date = Column(DateTime, nullable=True)
    maintenance_interval_id = Column(Integer, nullable=True)
    estimated_maintenance_date = Column(DateTime, nullable=True)
    status = Column(Integer, nullable=True)
    devices_id = Column(Integer, nullable=True)
    price_device = Column(JSON, nullable=True)
    data_devices = Column(JSON, nullable=True)
    
class Lot(Base):
    __tablename__ = 'lot'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(60), nullable=True)
    real_estate_registration_number = Column(String(255), nullable=True)
    extension = Column(Integer, nullable=True)
    latitude = Column(Integer, nullable=True)
    longitude = Column(Integer, nullable=True)
    public_deed = Column(String(255), nullable=True)
    freedom_tradition_certificate = Column(String(255), nullable=True)
    payment_interval = Column(Integer, nullable=True)
    type_crop_id = Column(Integer, nullable=True)
    planting_date = Column(Date, nullable=True)
    estimated_harvest_date = Column(Date, nullable=True)
    State = Column(Integer, default=5)
    
class Property(Base):
    __tablename__ = 'property'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(60), nullable=True)
    latitude = Column(Integer, nullable=True)
    longitude = Column(Integer, nullable=True)
    extension = Column(Integer, nullable=True)
    real_estate_registration_number = Column(Integer, nullable=True)
    public_deed = Column(String(255), nullable=True)
    freedom_tradition_certificate = Column(String(255), nullable=True)
    State = Column(Integer, default=3)
    
class Users(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(60), nullable=True)
    first_last_name = Column(String(60), nullable=True)
    second_last_name = Column(String(60), nullable=True)
    document_number = Column(Integer, nullable=True)
    email = Column(String(50), nullable=True)
    status_id = Column(Integer, nullable=True)
    # Otros campos no incluidos para simplificar

class Maintenance(Base):
    __tablename__ = 'maintenance'
    
    id = Column(Integer, primary_key=True, index=True)
    device_iot_id = Column(Integer, ForeignKey("device_iot.id"), nullable=True)
    type_failure_id = Column(Integer, ForeignKey("type_failure.id"), nullable=True)
    description_failure = Column(String(255), nullable=True)
    date = Column(Date, nullable=True)
    maintenance_status_id = Column(Integer, ForeignKey("maintenance_status.id"), nullable=True)
    
    device = relationship("DeviceIot", foreign_keys=[device_iot_id])
    type_failure = relationship("TypeFailure", foreign_keys=[type_failure_id])
    status = relationship("MaintenanceStatus", foreign_keys=[maintenance_status_id])

class TechnicianAssignment(Base):
    __tablename__ = 'technician_assignment'
    
    id = Column(Integer, primary_key=True, index=True)
    maintenance_id = Column(Integer, ForeignKey("maintenance.id"), nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    assignment_date = Column(DateTime, nullable=True)
    
    maintenance = relationship("Maintenance", foreign_keys=[maintenance_id])
    technician = relationship("Users", foreign_keys=[user_id])

class MaintenanceDetail(Base):
    __tablename__ = 'maintenance_detail'
    
    id = Column(Integer, primary_key=True, index=True)
    technician_assignment_id = Column(Integer, ForeignKey("technician_assignment.id"), nullable=True)
    fault_remarks = Column(String(255), nullable=True)
    evidence_failure = Column(String(255), nullable=True)
    failure_solution_id = Column(Integer, ForeignKey("failure_solution.id"), nullable=True)
    solution_remarks = Column(String(45), nullable=True)
    evidence_solution = Column(String(255), nullable=True)
    
    assignment = relationship("TechnicianAssignment", foreign_keys=[technician_assignment_id])
    solution = relationship("FailureSolution", foreign_keys=[failure_solution_id])
