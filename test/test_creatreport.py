import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.maintenance.models import MaintenanceReport
from app.database import get_db
from sqlalchemy.orm import Session

@pytest.fixture
def db_session():
    # Aquí puedes configurar tu base de datos de prueba o usar una base de datos en memoria
    db = next(get_db())
    yield db
    db.rollback()

@pytest.fixture
def valid_report_data():
    # Datos válidos para el reporte
    return {
        "lot_id": 1,
        "type_failure_id": 2,
        "description_failure": "Fallo de prueba"
    }

def test_create_report(db_session: Session, valid_report_data: dict):
    # Crea el cliente de prueba para hacer peticiones a la API
    client = TestClient(app)
    
    # Realiza una petición POST para crear el reporte
    response = client.post("/maintenance/reports", json=valid_report_data)

    # Asegúrate de que la respuesta sea exitosa (código de estado 200)
    assert response.status_code == 200
    
    # Verifica que la respuesta contenga el campo "success" como True
    response_data = response.json()
    assert response_data["success"] is True
    
    # Verifica que el reporte se haya creado correctamente en la base de datos
    created_report = db_session.query(MaintenanceReport).order_by(MaintenanceReport.id.desc()).first()
    
    # Asegúrate de que el reporte creado tiene el estado 24
    assert created_report.maintenance_status_id == 24
    


def test_create_report_failure(db_session: Session, valid_report_data: dict):
    # Crea el cliente de prueba
    client = TestClient(app)
    
    # Deja fuera el "lot_id" para provocar un error de validación
    invalid_data = valid_report_data.copy()
    del invalid_data["lot_id"]
    
    # Realiza una petición POST para crear el reporte con datos inválidos
    response = client.post("/maintenance/reports", json=invalid_data)

    # Asegúrate de que la respuesta sea un error (código de estado 422)
    assert response.status_code == 422

    # Verifica que el mensaje de error sea el esperado
    response_data = response.json()
    assert "detail" in response_data
    assert "loc" in response_data["detail"][0]
    assert response_data["detail"][0]["loc"] == ["body", "lot_id"]
