import pytest
from datetime import datetime
from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal, engine
from app.maintenance.models import TechnicianAssignment, MaintenanceReport, User

# Fixture para la sesión de la base de datos
@pytest.fixture(scope="module")
def db_session():
    # Establece la sesión de base de datos
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Fixture para el cliente de pruebas
@pytest.fixture(scope="module")
def client():
    # Configura el cliente de FastAPI para las pruebas
    return TestClient(app)

# Prueba para el servicio `update_report_assignment`
def test_update_report_assignment(client, db_session):
    # Datos proporcionados
    report_id = 14
    user_id = 7
    assignment_date = datetime.strptime("2025-04-30 13:15:22.471725", "%Y-%m-%d %H:%M:%S.%f")

    # Comprobamos si el reporte y el usuario existen en la base de datos
    report = db_session.query(MaintenanceReport).filter_by(id=report_id).first()
    user = db_session.query(User).filter_by(id=user_id).first()

    assert report is not None, "Reporte no encontrado"
    assert user is not None, "Usuario no encontrado"

    # Realizar la solicitud PUT para actualizar la asignación
    response = client.put(
        f"/maintenance/reports/{report_id}/assign", 
        json={"user_id": user_id, "assignment_date": assignment_date.isoformat()}
    )

    # Validamos la respuesta
    assert response.status_code == 200, f"Error en la asignación: {response.text}"
    data = response.json()

    # Validamos los campos de la respuesta
    assert data["success"] is True
    assert data["data"]["report_id"] == report_id
    assert data["data"]["user_id"] == user_id
    assert data["data"]["assignment_date"] == assignment_date.isoformat()

    # Verificamos que la asignación fue registrada en la base de datos
    asgmt = db_session.query(TechnicianAssignment).filter_by(report_id=report_id).first()
    assert asgmt is not None, "Asignación no registrada en la base de datos"
    assert asgmt.user_id == user_id, "El usuario asignado no es el correcto"
    assert asgmt.assignment_date == assignment_date, "La fecha de asignación no es la correcta"
