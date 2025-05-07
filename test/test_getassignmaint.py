import random
import pytest
from fastapi.testclient import TestClient
from datetime import datetime
from app.main import app
from app.maintenance.models import User, Maintenance, TechnicianAssignment, TypeFailure, Vars, Lot, DeviceIot
from app.database import SessionLocal
import string


# Fixture para la sesión de base de datos
@pytest.fixture
def db_session():
    with SessionLocal() as session:
        yield session
        session.rollback()

# Fixture para crear un usuario de prueba con document_number aleatorio
@pytest.fixture
def test_user(db_session):
    # Generar un número de documento aleatorio de 9 dígitos
    document_number = str(random.randint(100000000, 999999999))
    
    # Generar un correo electrónico aleatorio
    random_email = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10)) + "@example.com"
    
    # Crear un usuario con el documento y el email aleatorio
    user = User(
        name="John",
        first_last_name="Doe",
        second_last_name="Smith",
        document_number=document_number,
        email=random_email,  # Correo electrónico aleatorio
        phone="1234567890"
    )
    db_session.add(user)
    db_session.commit()
    return user

# Fixture para crear un mantenimiento de prueba
@pytest.fixture
def test_maintenance(db_session):
    maintenance = Maintenance(
        device_iot_id=1,
        type_failure_id=1,
        description_failure="Fallo en la tubería",
        maintenance_status_id=1,
        date=datetime.now()
    )
    db_session.add(maintenance)
    db_session.commit()
    db_session.refresh(maintenance)
    return maintenance

# Fixture para crear una asignación de técnico
@pytest.fixture
def test_assignment(db_session, test_user, test_maintenance):
    assignment = TechnicianAssignment(
        maintenance_id=test_maintenance.id,
        user_id=test_user.id,
        assignment_date=datetime.now()
    )
    db_session.add(assignment)
    db_session.commit()
    db_session.refresh(assignment)
    return assignment

# Cliente de prueba
@pytest.fixture
def client():
    return TestClient(app)

# Prueba para obtener los mantenimientos asignados a un técnico
def test_get_assigned_maintenances_for_technician(client, test_user, test_maintenance, test_assignment):
    response = client.get(f"/maintenance/assigned/{test_user.id}/maintenances")

    assert response.status_code == 200  # Verifica que la respuesta sea exitosa
    assert "success" in response.json()  # Verifica que la respuesta tenga la clave "success"
    assert response.json()["success"] is True  # Verifica que "success" sea verdadero
    assert isinstance(response.json()["data"], list)  # Verifica que los datos sean una lista

    # Verifica que los datos contengan la información esperada
    data = response.json()["data"]
    assert len(data) > 0  # Verifica que haya al menos un mantenimiento asignado
    assert "technician_assignment_id" in data[0]  # Verifica que los mantenimientos tengan el ID de asignación
    assert "maintenance_id" in data[0]  # Verifica que los mantenimientos tengan el ID de mantenimiento
    assert data[0]["technician_assignment_id"] == test_assignment.id  # Verifica que el ID de la asignación sea correcto
    assert data[0]["maintenance_id"] == test_maintenance.id  # Verifica que el ID del mantenimiento sea correcto

    assert data[0]["failure_type"] == "Fallo en la tubería"  # Verifica que el tipo de fallo esté presente y sea correcto
    assert "assigned_at" in data[0]  # Verifica que la fecha de asignación esté presente
