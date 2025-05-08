import pytest
import random
from datetime import datetime
from fastapi.testclient import TestClient
from app.main import app  # Asegúrate de importar tu aplicación FastAPI correctamente
from app.database import SessionLocal, engine
from app.maintenance.models import Base, Maintenance, User, Role

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
def prepare_user(dbsession):
    """Fixture para preparar un usuario con rol de técnico en la base de datos."""
    # Obtener el usuario con id=7
    user = dbsession.query(User).filter_by(id=7).first()
    if not user:
        raise ValueError("El usuario con ID 7 no existe en la base de datos.")

    # Obtener el rol de técnico (id=3) y asignárselo al usuario si no lo tiene
    technician_role = dbsession.query(Role).filter_by(id=3).first()
    if technician_role not in user.roles:
        user.roles.append(technician_role)
        dbsession.commit()

    yield user  # Devolver el usuario para su uso en la prueba


@pytest.fixture
def prepare_non_technician_user(dbsession):
    """Fixture para crear un usuario sin el rol de técnico (causa error 403)."""
    # Crear un usuario con id aleatorio, documento y correo
    random_user_id = random.randint(1000, 9999)
    random_document = str(random.randint(100000000, 999999999))
    random_email = f"user{random_user_id}@example.com"

    new_user = User(
        id=random_user_id,
        name="Non Technician User",
        first_last_name="Non",
        second_last_name="Technician",
        document_number=random_document,
        email=random_email,
        phone="1234567890"
    )
    dbsession.add(new_user)
    dbsession.commit()

    # Asegurarnos de que este usuario no tenga el rol de técnico
    technician_role = dbsession.query(Role).filter_by(id=3).first()
    if technician_role in new_user.roles:
        new_user.roles.remove(technician_role)
        dbsession.commit()

    yield new_user  # Devolver el usuario sin rol de técnico

@pytest.fixture
def prepare_existing_maintenance(dbsession):
    """Fixture para asegurarse de que el mantenimiento con id 32 existe en la base de datos."""
    # Asegúrate de que el mantenimiento con id 32 existe en la base de datos
    maintenance = dbsession.query(Maintenance).filter_by(id=32).first()
    if not maintenance:
        # Si el mantenimiento con id 32 no existe, lo creamos
        maintenance = Maintenance(id=32, device_iot_id=1, type_failure_id=1, description_failure="Test failure", maintenance_status_id=24)
        dbsession.add(maintenance)
        dbsession.commit()

    yield maintenance  # Devolver el mantenimiento preexistente


@pytest.fixture
def prepare_random_maintenance(dbsession):
    """Fixture para crear un mantenimiento con id aleatorio para las pruebas."""
    random_maintenance_id = random.randint(1000, 9999)  # ID aleatorio
    new_maintenance = Maintenance(
        id=random_maintenance_id,
        device_iot_id=1,
        type_failure_id=1,
        description_failure="Random test failure",
        maintenance_status_id=24
    )
    dbsession.add(new_maintenance)
    dbsession.commit()

    yield random_maintenance_id  # Devolver el ID aleatorio generado


def test_assign_technician(client, prepare_user, prepare_non_technician_user, prepare_existing_maintenance, prepare_random_maintenance):
    maintenance_id = 32  # Usar el mantenimiento con id 32 preexistente
    technician_user = prepare_user  # Usuario con rol de técnico
    non_technician_user = prepare_non_technician_user  # Usuario sin rol de técnico
    random_maintenance_id = prepare_random_maintenance  # Usar el mantenimiento con id aleatorio
    assignment_date = "2025-07-05 19:49:00"

    # Primero, probamos el caso de error 400 (ya existe técnico asignado)
    response = client.post(
        f"/maintenance/{maintenance_id}/assign",
        json={"user_id": technician_user.id, "assignment_date": assignment_date}
    )
    # Verificamos que la respuesta sea un error 400
    assert response.status_code == 400
    response_data = response.json()
    assert response_data["detail"] == "Ya existe técnico asignado"

    # Ahora, probamos el caso de error 403 con un usuario sin el permiso 80
    response = client.post(
        f"/maintenance/{maintenance_id}/assign",
        json={"user_id": non_technician_user.id, "assignment_date": assignment_date}
    )
    # Verificamos que la respuesta sea un error 403
    assert response.status_code == 403
    response_data = response.json()
    assert response_data["detail"] == "Usuario sin permiso 80"

    # Ahora, probamos el caso de error 404 (mantenimiento no encontrado)
    non_existent_maintenance_id = 99999  # Un ID que no existe en la base de datos
    response = client.post(
        f"/maintenance/{non_existent_maintenance_id}/assign",
        json={"user_id": technician_user.id, "assignment_date": assignment_date}
    )
    # Verificamos que la respuesta sea un error 404
    assert response.status_code == 404
    response_data = response.json()
    assert response_data["detail"] == "Mantenimiento no encontrado"

    # Finalmente, probamos el caso exitoso con el nuevo mantenimiento aleatorio
    response = client.post(
        f"/maintenance/{random_maintenance_id}/assign",
        json={"user_id": technician_user.id, "assignment_date": assignment_date}
    )
    # Verificamos que la respuesta sea 200
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["success"] is True
    assert response_data["data"]["maintenance_id"] == random_maintenance_id
    assert response_data["data"]["user_id"] == technician_user.id
    
