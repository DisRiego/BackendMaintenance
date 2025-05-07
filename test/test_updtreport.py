import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal
from app.maintenance.models import MaintenanceReport, TypeFailure, Vars

@pytest.fixture
def db_session():
    """Fixture para la sesión de base de datos."""
    # Creamos una nueva sesión local de base de datos
    db = SessionLocal()
    try:
        yield db  # Pasamos la sesión a las pruebas
    finally:
        db.close()  # Cerramos la sesión al finalizar

@pytest.fixture
def client(db_session):
    """Fixture para el cliente de la API."""
    return TestClient(app)

def test_update_report(client, db_session):
    # Datos de entrada para la actualización
    report_id = 1
    updated_data = {
        "type_failure_id": 3,
        "description_failure": "Nuevo fallo de mantenimiento",
        "maintenance_status_id": 24
    }
    
    # Ejecutamos el endpoint PUT /maintenance/reports/{report_id} para actualizar el reporte
    response = client.put(f"/maintenance/reports/{report_id}", json=updated_data)
    
    # Verificamos el código de estado de la respuesta
    assert response.status_code == 200
    
    # Verificamos que el reporte se haya actualizado correctamente
    response_data = response.json()
    assert response_data["success"] is True
    assert response_data["data"]["id"] == report_id
    assert response_data["data"]["type_failure_id"] == 3
    assert response_data["data"]["description_failure"] == "Nuevo fallo de mantenimiento"
    assert response_data["data"]["maintenance_status_id"] == 24
    
    # Comprobamos en la base de datos si el reporte fue actualizado correctamente
    updated_report = db_session.query(MaintenanceReport).filter_by(id=report_id).first()
    assert updated_report is not None
    assert updated_report.type_failure_id == 3
    assert updated_report.description_failure == "Nuevo fallo de mantenimiento"
    assert updated_report.maintenance_status_id == 24
