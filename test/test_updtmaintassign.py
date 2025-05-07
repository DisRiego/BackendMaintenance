import pytest
from datetime import datetime
from fastapi.testclient import TestClient
from app.main import app  # Ajusta esta importación según tu archivo principal de FastAPI
from app.database import SessionLocal
from app.maintenance.models import Maintenance, TechnicianAssignment
from app.maintenance.schemas import AssignmentUpdate


# Fixture para la sesión de la base de datos
@pytest.fixture(scope="module")
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Fixture para el cliente de prueba (TestClient)
@pytest.fixture(scope="module")
def client():
    with TestClient(app) as client:
        yield client


def test_update_maintenance_assignment(client, db_session):
    maintenance_id = 27
    technician_assignment_id = 25
    user_id = 34
    assignment_date = datetime(2025, 5, 6, 18, 11, 17, 938488)

    # Verificar que la asignación de técnico existe antes de la actualización
    asgmt = db_session.query(TechnicianAssignment).filter(TechnicianAssignment.maintenance_id == maintenance_id).first()
    assert asgmt is not None, f"Asignación con ID {maintenance_id} no encontrada"

    # Realizar la actualización de la asignación de técnico
    response = client.put(
        f"/maintenance/{maintenance_id}/assign",
        json={"user_id": user_id, "assignment_date": assignment_date.isoformat()}
    )

    # Verificar la respuesta
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["success"] is True
    updated_assignment = response_data["data"]
    assert updated_assignment["maintenance_id"] == maintenance_id
    assert updated_assignment["user_id"] == user_id
    assert updated_assignment["assignment_date"] == assignment_date.isoformat()

    # Verificar que la actualización se ha realizado en la base de datos
    updated_assignment_db = db_session.query(TechnicianAssignment).filter(TechnicianAssignment.maintenance_id == maintenance_id).first()
    assert updated_assignment_db is not None
    assert updated_assignment_db.assignment_date == assignment_date
    assert updated_assignment_db.user_id == user_id
