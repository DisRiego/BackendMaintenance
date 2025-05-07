import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal, engine
from app.maintenance.models import Maintenance, DeviceIot, Lot, Property, TypeFailure, User, Vars
from app.maintenance.services import MaintenanceService

@pytest.fixture(scope="module")
def dbsession():
    # Crear una nueva sesión para cada test
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture(scope="module")
def client():
    # Crear un cliente de prueba de FastAPI
    return TestClient(app)

def test_get_maintenances_by_user(client: TestClient, dbsession):
    # Datos preexistentes
    user_id = 2
    maintenance_id = 10
    device_iot_id = 20
    lot_id = 1
    property_id = 8
    type_failure_id = 3

    # Validar si los datos existen en la base de datos
    maintenance = dbsession.query(Maintenance).filter(Maintenance.id == maintenance_id).first()
    assert maintenance is not None, f"El mantenimiento con ID {maintenance_id} no existe en la base de datos."

    device_iot = dbsession.query(DeviceIot).filter(DeviceIot.id == device_iot_id).first()
    assert device_iot is not None, f"El dispositivo IoT con ID {device_iot_id} no existe en la base de datos."

    lot = dbsession.query(Lot).filter(Lot.id == lot_id).first()
    assert lot is not None, f"El lote con ID {lot_id} no existe en la base de datos."

    property_ = dbsession.query(Property).filter(Property.id == property_id).first()
    assert property_ is not None, f"La propiedad con ID {property_id} no existe en la base de datos."

    type_failure = dbsession.query(TypeFailure).filter(TypeFailure.id == type_failure_id).first()
    assert type_failure is not None, f"El tipo de fallo con ID {type_failure_id} no existe en la base de datos."

    # Realizar la solicitud al endpoint de mantenimientos por usuario
    response = client.get(f"/maintenance/user/{user_id}/maintenances")
    
    # Verificar que la respuesta sea correcta
    assert response.status_code == 200
    data = response.json().get('data', [])
        # Verificar los campos clave en la respuesta
    for maintenance in data:
        assert 'maintenance_id' in maintenance
        assert 'device_iot_id' in maintenance
        assert 'lot_id' in maintenance
        assert 'lot_name' in maintenance
        assert 'property_id' in maintenance
        assert 'property_name' in maintenance
        assert 'report_date' in maintenance
        assert 'failure_type' in maintenance
        assert 'description_failure' in maintenance
        assert 'status' in maintenance
        assert 'status_id' in maintenance

    # Asegurarse de que el mantenimiento correspondiente al usuario esté presente en la lista
    assert any(maintenance['device_iot_id'] == device_iot_id for maintenance in data), "El mantenimiento no está relacionado con el dispositivo IoT correcto."
