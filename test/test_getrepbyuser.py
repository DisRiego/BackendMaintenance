import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal
from app.maintenance.models import User, MaintenanceReport, TypeFailure, Maintenance, Property, Lot, TechnicianAssignment, MaintenanceDetail
from datetime import datetime
from io import BytesIO

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
    
    # Verificar si el usuario con ID 2 ya existe
    user = dbsession.query(User).filter_by(id=2).first()
    if not user:
        user = User(id=2, name="Test User", first_last_name="Test", second_last_name="User", document_number="987654321", email="testuser@domain.com", phone="987654321")
        dbsession.add(user)

    # Verificar si el reporte de mantenimiento con ID 9 ya existe
    report = dbsession.query(MaintenanceReport).filter_by(id=9).first()
    if not report:
        report = MaintenanceReport(id=9, lot_id=2, type_failure_id=3, description_failure="Test failure", maintenance_status_id=25, date=datetime(2025, 7, 5))
        dbsession.add(report)

    # Verificar si el lote con ID 2 ya existe
    lot = dbsession.query(Lot).filter_by(id=2).first()
    if not lot:
        lot = Lot(id=2, name="Test Lot", longitude=123.456, latitude=78.901, extension=100, real_estate_registration_number=123456789)
        dbsession.add(lot)

    # Verificar si la propiedad con ID 7 ya existe
    property_ = dbsession.query(Property).filter_by(id=7).first()
    if not property_:
        property_ = Property(id=7, name="Test Property", longitude=123.456, latitude=78.901, extension=100, real_estate_registration_number=987654321)
        dbsession.add(property_)

    # Verificar si la asignación de técnico con ID 1 ya existe
    technician_assignment = dbsession.query(TechnicianAssignment).filter_by(id=1).first()
    if not technician_assignment:
        technician_assignment = TechnicianAssignment(id=1, report_id=9, maintenance_id=None, user_id=2, assignment_date=datetime(2025, 7, 5))
        dbsession.add(technician_assignment)

    dbsession.commit()

    yield dbsession



def test_get_reports_by_user(client, prepare_test_data):
    """Prueba para obtener todos los reportes por lote de un usuario."""
    user_id = 2  # Usuario existente con ID 2

    # Realizamos la solicitud GET
    response = client.get(f"/maintenance/user/{user_id}/reports")

    # Verificamos que la respuesta sea correcta
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["success"] is True
    assert "data" in response_data
    assert len(response_data["data"]) > 0

   