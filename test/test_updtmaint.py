import pytest
from fastapi.testclient import TestClient
from app.main import app  # Asumiendo que tu FastAPI app está en app.main
from app.database import SessionLocal
from app.maintenance.models import Maintenance
from app.maintenance.schemas import MaintenanceUpdate


@pytest.fixture
def db_session():
    # Configuración de la base de datos para las pruebas, debes adaptarlo a tu configuración
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def client():
    with TestClient(app) as client:
        yield client


def test_update_maintenance_description_failure(client, db_session):
    maintenance_id = 10
    new_description_failure = "Descripción actualizada del fallo"

    # Verificar que el mantenimiento existe antes de la actualización
    maintenance = db_session.query(Maintenance).filter(Maintenance.id == maintenance_id).first()
    assert maintenance is not None, f"Mantenimiento con ID {maintenance_id} no encontrado"

    # Realizar la actualización de description_failure
    data = MaintenanceUpdate(description_failure=new_description_failure)
    response = client.put(f"/maintenance/{maintenance_id}", json=data.dict())

    # Verificar la respuesta
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["success"] is True
    updated_maintenance = response_data["data"]
    assert updated_maintenance["id"] == maintenance_id
    assert updated_maintenance["description_failure"] == new_description_failure

    # Verificar que la actualización se ha realizado en la base de datos
    updated_maintenance_db = db_session.query(Maintenance).filter(Maintenance.id == maintenance_id).first()
    assert updated_maintenance_db.description_failure == new_description_failure
