from sqlalchemy import TIMESTAMP, Column, Date, Integer, String, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class Vars(Base):
    __tablename__ = 'vars'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)
    description = Column(String)

class MaintenanceStatus(Base):
    __tablename__ = 'maintenance_status'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(45))
    
    maintenance = relationship("Maintenance", back_populates="status")

class TypeFailure(Base):
    __tablename__ = 'type_failure'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100))
    description = Column(String(45))
    
    maintenance = relationship("Maintenance", back_populates="failure_type")

class DeviceIot(Base):
    __tablename__ = 'device_iot'
    
    id = Column(Integer, primary_key=True, index=True)
    serial_number = Column(Integer)
    model = Column(String(45))
    lot_id = Column(Integer)
    installation_date = Column(DateTime)
    maintenance_interval_id = Column(Integer)
    estimated_maintenance_date = Column(DateTime)
    status = Column(Integer)
    devices_id = Column(Integer)
    price_device = Column(JSON)
    data_devices = Column(JSON)
    
    maintenance = relationship("Maintenance", back_populates="device")

class Maintenance(Base):
    __tablename__ = 'maintenance'
    
    id = Column(Integer, primary_key=True, index=True)
    device_iot_id = Column(Integer, ForeignKey('device_iot.id'))
    type_failure_id = Column(Integer, ForeignKey('type_failure.id'))
    description_failure = Column(String(255))
    date = Column(Date)
    maintenance_status_id = Column(Integer, ForeignKey('maintenance_status.id'))
    
    device = relationship("DeviceIot", back_populates="maintenance")
    failure_type = relationship("TypeFailure", back_populates="maintenance")
    status = relationship("MaintenanceStatus", back_populates="maintenance")
    technician_assignments = relationship("TechnicianAssignment", back_populates="maintenance")

class TechnicianAssignment(Base):
    __tablename__ = 'technician_assignment'
    
    id = Column(Integer, primary_key=True, index=True)
    maintenance_id = Column(Integer, ForeignKey('maintenance.id'))
    user_id = Column(Integer, ForeignKey('users.id'))
    assignment_date = Column(DateTime)
    
    maintenance = relationship("Maintenance", back_populates="technician_assignments")
    user = relationship("User", back_populates="technician_assignments")
    maintenance_details = relationship("MaintenanceDetail", back_populates="technician_assignment")

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(60))
    first_last_name = Column(String(60))
    second_last_name = Column(String(60))
    email = Column(String(50), unique=True)
    
    technician_assignments = relationship("TechnicianAssignment", back_populates="user")

class FailureSolution(Base):
    __tablename__ = 'failure_solution'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(45))
    description = Column(String(255))
    
    maintenance_details = relationship("MaintenanceDetail", back_populates="solution")

class MaintenanceDetail(Base):
    __tablename__ = 'maintenance_detail'
    
    id = Column(Integer, primary_key=True, index=True)
    technician_assignment_id = Column(Integer, ForeignKey('technician_assignment.id'))
    fault_remarks = Column(String(255))
    evidence_failure = Column(String(255))
    failure_solution_id = Column(Integer, ForeignKey('failure_solution.id'))
    solution_remarks = Column(String(45))
    evidence_solution = Column(String(255))
    
    technician_assignment = relationship("TechnicianAssignment", back_populates="maintenance_details")
    solution = relationship("FailureSolution", back_populates="maintenance_details")