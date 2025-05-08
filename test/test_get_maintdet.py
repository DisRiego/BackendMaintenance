import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import get_db, SessionLocal
from app.maintenance.models import Maintenance, TechnicianAssignment, MaintenanceDetail, DeviceIot, Lot, Property, User
from app.maintenance.schemas import MaintenanceDetailCreate
from datetime import datetime

# Fixture para la sesión de base de datos (db_session)
@pytest.fixture(scope="function")
def db_session():
    # Inicia la sesión de la base de datos
    db = SessionLocal()
    
    # Usamos los datos preexistentes en lugar de generar datos aleatorios
    maintenance_id = 11  # Usamos el ID de mantenimiento preexistente con status_id correcto
    device_iot_id = 20  # ID de dispositivo IoT preexistente
    lot_id = 1  # ID de lote preexistente
    property_id = 8  # ID de propiedad preexistente
    user_id = 2  # ID de usuario preexistente
    
    # Verifica que el mantenimiento con el ID proporcionado exista
    maintenance = db.query(Maintenance).filter(Maintenance.id == maintenance_id).first()
    if not maintenance:
        raise ValueError("Mantenimiento no encontrado.")
    
    # Verifica que el dispositivo IoT con el ID proporcionado exista
    device = db.query(DeviceIot).filter(DeviceIot.id == device_iot_id).first()
    if not device:
        raise ValueError("Dispositivo IoT no encontrado.")
    
    # Verifica que el lote con el ID proporcionado exista
    lot = db.query(Lot).filter(Lot.id == lot_id).first()
    if not lot:
        raise ValueError("Lote no encontrado.")
    
    # Verifica que la propiedad con el ID proporcionado exista
    property_ = db.query(Property).filter(Property.id == property_id).first()
    if not property_:
        raise ValueError("Propiedad no encontrada.")
    
    # Verifica que el usuario con el ID proporcionado exista
    owner = db.query(User).filter(User.id == user_id).first()
    if not owner:
        raise ValueError("Usuario no encontrado.")
    
    # Vuelve a cargar los datos después de las verificaciones
    yield db  # Proporciona la sesión para la prueba

    db.rollback()  # Revierte los cambios realizados en la base de datos después de la prueba
    db.close()


# Fixture para el cliente de prueba (client)
@pytest.fixture(scope="function")
def client(db_session):
    # Crea un cliente para realizar las peticiones
    client = TestClient(app)
    return client


# Prueba de la funcionalidad de obtener detalles del mantenimiento
def test_get_maintenance_detail(client, db_session):
    # Usamos el ID de mantenimiento preexistente (11)
    maintenance_id = 11
    
    # Realizar la solicitud GET
    response = client.get(f"/maintenance/{maintenance_id}/detail")
    
    # Verificar que el estado de la respuesta sea 200 (OK)
    assert response.status_code == 200
    
    # Verificar que los datos recibidos en la respuesta son correctos
    data = response.json()["data"]
    
    # Validaciones según el servicio
    assert data["property_id"] == 8  # ID de la propiedad preexistente
    assert data["property_name"] is not None
    assert data["lot_id"] == 1  # ID del lote preexistente
    assert data["lot_name"] is not None
    assert data["status"] is not None
    assert data["status_id"] is not None
    assert data["failure_type_report"] is not None
    
    assert data["owner_document"] is not None
    assert data["owner_name"] is not None
    assert data["owner_email"] is not None
    assert data["owner_phone"] is not None
    
    # Verificar si un técnico está asignado
    technician_name = data.get("technician_name")
    technician_id = data.get("technician_id")
    assert technician_name is None or technician_id is None  # En este caso, no hay técnico asignado, así que deberían ser None

    # Validación de campos que dependen del detalle del mantenimiento
    if data["technician_assignment_id"]:
        assert data["assignment_date"] is not None
        assert data["technician_name"] is not None
        assert data["finalized"] is True
        assert data["finalization_date"] is not None
    else:
        assert data["assignment_date"] is None
        assert data["finalized"] is False
