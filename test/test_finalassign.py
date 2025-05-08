import pytest
import random
from io import BytesIO
from datetime import datetime
from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal, engine
from app.maintenance.models import Base, Maintenance, TechnicianAssignment, MaintenanceDetail, User

# Crear las tablas en la base de datos de pruebas
Base.metadata.create_all(bind=engine)

@pytest.fixture(scope="module")
def dbsession():
    """Fixture para crear una sesión de base de datos para las pruebas."""
    db = SessionLocal()
    yield db
    db.close()

@pytest.fixture
def client(dbsession):
    """Fixture para crear el cliente de pruebas usando TestClient."""
    app.dependency_overrides[SessionLocal] = lambda: dbsession
    with TestClient(app) as c:
        yield c

@pytest.fixture
def prepare_test_data(dbsession):
    """Fixture para preparar datos de prueba en la base de datos."""

    # Verificar si el técnico ya existe en la base de datos
    technician = dbsession.query(User).filter_by(id=7).first()
    if not technician:
        technician = User(id=7, name="Test Technician", first_last_name="Test", second_last_name="Technician", document_number="123456789", email="test@domain.com", phone="987654321")
        dbsession.add(technician)

    # Generar un ID aleatorio para el mantenimiento y la asignación
    random_maintenance_id = random.randint(100, 9999)  # Generamos un ID aleatorio para mantenimiento
    random_technician_assignment_id = random.randint(1000, 9999)  # Generamos un ID aleatorio para la asignación

    # Crear un mantenimiento con un ID aleatorio 
    maintenance = Maintenance(id=random_maintenance_id, device_iot_id=1, type_failure_id=1, description_failure="Test failure", maintenance_status_id=25, date=datetime(2025, 7, 5))
    dbsession.add(maintenance)

    # Crear una asignación de técnico con un ID aleatorio
    technician_assignment = TechnicianAssignment(id=random_technician_assignment_id, report_id=None, maintenance_id=random_maintenance_id, user_id=7, assignment_date=datetime(2025, 7, 5))
    dbsession.add(technician_assignment)

    dbsession.commit()

    yield dbsession, random_maintenance_id  # Devuelve el dbsession y el random_maintenance_id para usarlo en el test


def test_finalize_assignment(client, prepare_test_data):
    """Prueba para finalizar un mantenimiento o reporte asignado."""
    # Datos de entrada
    technician_assignment_id = 1  # ID de la asignación
    fault_remarks = "Fault found during test."
    type_failure_id = 1  # ID del tipo de fallo
    type_maintenance_id = 1  # ID del tipo de mantenimiento
    failure_solution_id = 1  # ID de la solución
    solution_remarks = "Solution applied during test."

    # Simulando la subida de archivos (evidencia de fallo y solución)
    evidence_failure = BytesIO(b"Fake failure evidence content")
    evidence_solution = BytesIO(b"Fake solution evidence content")

    # Realizamos la solicitud POST
    response = client.post(
        "/maintenance/finalize",
        files={
            "evidence_failure": ("evidence_failure.jpg", evidence_failure, "image/jpeg"),
            "evidence_solution": ("evidence_solution.jpg", evidence_solution, "image/jpeg"),
        },
        data={
            "technician_assignment_id": technician_assignment_id,
            "fault_remarks": fault_remarks,
            "type_failure_id": type_failure_id,
            "type_maintenance_id": type_maintenance_id,
            "failure_solution_id": failure_solution_id,
            "solution_remarks": solution_remarks,
        }
    )

    # Verificamos que la respuesta sea correcta
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["success"] is True
    assert "data" in response_data

    # Verificar que el estado del mantenimiento se haya actualizado a 25 (finalizado)
    dbsession, random_maintenance_id = prepare_test_data  # Recibimos también el random_maintenance_id
    maintenance = dbsession.query(Maintenance).filter_by(id=random_maintenance_id).first()
    assert maintenance.maintenance_status_id == 25  # Verificamos que el estado sea "Finalizado" (25)

    # Verificar que se haya creado un registro en maintenance_detail
    maintenance_detail = dbsession.query(MaintenanceDetail).filter_by(technician_assignment_id=technician_assignment_id).first()
    assert maintenance_detail is not None
    assert maintenance_detail.fault_remarks == fault_remarks
    assert maintenance_detail.solution_remarks == solution_remarks
