from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime

class Vars(Base):
    __tablename__ = 'vars'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    document_number = Column(String, nullable=False)

class Property(Base):
    __tablename__ = 'property'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    
class PropertyLot(Base):
    __tablename__ = 'property_lot'
    property_id = Column(Integer, ForeignKey('property.id'), primary_key=True)
    lot_id = Column(Integer, ForeignKey('lot.id'), primary_key=True)

class PropertyUser(Base):
    __tablename__ = 'user_property'
    property_id = Column(Integer, ForeignKey('property.id'), primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), primary_key=True)

    property = relationship("Property", backref="property_users")
    user = relationship("User", backref="property_users")

class Lot(Base):
    __tablename__ = 'lot'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)

class DeviceIot(Base):
    __tablename__ = 'device_iot'
    id = Column(Integer, primary_key=True, index=True)
    lot_id = Column(Integer, ForeignKey('lot.id'))
    lot = relationship("Lot")

class TechnicianAssignment(Base):
    __tablename__ = 'technician_assignment'
    id = Column(Integer, primary_key=True, index=True)
    technician_user_id = Column(Integer, ForeignKey('users.id'))
    technician_user = relationship("User")

class TypeFailure(Base):
    __tablename__ = 'type_failure'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)

class FailureSolution(Base):
    __tablename__ = 'failure_solution'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)

class Maintenance(Base):
    __tablename__ = 'maintenance'
    id = Column(Integer, primary_key=True, index=True)
    device_iot_id = Column(Integer, ForeignKey('device_iot.id'))
    type_failure_id = Column(Integer, ForeignKey('type_failure.id'))
    description_failure = Column(String)
    date = Column(DateTime, default=datetime.utcnow)
    status = Column(Integer, ForeignKey('vars.id'))

    device_iot = relationship("DeviceIot")
    type_failure = relationship("TypeFailure")
    status_var = relationship("Vars")

class MaintenanceDetail(Base):
    __tablename__ = 'maintenance_detail'
    id = Column(Integer, primary_key=True, index=True)
    maintenance_id = Column(Integer, ForeignKey('maintenance.id'))
    technician_assignment_id = Column(Integer, ForeignKey('technician_assignment.id'))
    fault_remarks = Column(String)
    evidence_failure = Column(String)
    failure_solution_id = Column(Integer, ForeignKey('failure_solution.id'))
    solution_remarks = Column(String)
    evidence_solution = Column(String)

    maintenance = relationship("Maintenance", back_populates="details")
    technician_assignment = relationship("TechnicianAssignment")
    failure_solution = relationship("FailureSolution")

Maintenance.details = relationship("MaintenanceDetail", back_populates="maintenance")
