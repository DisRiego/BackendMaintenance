import pytest
from app.main import app
from app.database import SessionLocal, engine
from fastapi.testclient import TestClient
from app.maintenance.models import Base, User, MaintenanceReport, TechnicianAssignment
from sqlalchemy.exc import IntegrityError

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
    """Fixture para crear el cliente de pruebas."""
    app.dependency_overrides[SessionLocal] = lambda: dbsession
    with TestClient(app) as c:
        yield c

@pytest.fixture
def prepare_test_data(dbsession):
    """Fixture para preparar datos de prueba en la base de datos."""
    
    # Verificar si el técnico ya existe, de no ser así, crear un nuevo usuario
    technician = dbsession.query(User).filter_by(id=7).first()
    if not technician:
        technician = User(id=7, name="Test Technician", first_last_name="Test", second_last_name="Technician", document_number="123456789", email="test@domain.com", phone="987654321")
        dbsession.add(technician)

    # Verificar si el reporte de mantenimiento ya existe, si no, crear uno nuevo con id único
    maintenance_report = dbsession.query(MaintenanceReport).filter_by(id=1).first()
    if not maintenance_report:
        maintenance_report = MaintenanceReport(id=1, lot_id=1, type_failure_id=1, description_failure="Test failure", maintenance_status_id=24, date="2025-07-05")
        dbsession.add(maintenance_report)

    # Asignar el reporte al técnico
    technician_assignment = dbsession.query(TechnicianAssignment).filter_by(id=1).first()
    if not technician_assignment:
        technician_assignment = TechnicianAssignment(id=1, report_id=maintenance_report.id, user_id=technician.id, assignment_date="2025-07-05")
        dbsession.add(technician_assignment)
    
    dbsession.commit()
    
    yield dbsession  # Datos de prueba preparados


def test_get_assigned_reports_for_technician(client, prepare_test_data):
    technician_id = 7  # ID del técnico con reportes asignados
    response = client.get(f"/maintenance/assigned/{technician_id}/reports")
    assert response.status_code == 200
    response_data = response.json()
    assert len(response_data["data"]) > 0  # Debería haber al menos un reporte asignado





