import pytest
from fastapi.testclient import TestClient
from app.main import app  # Asegúrate de importar tu app FastAPI aquí
from app.database import SessionLocal
from app.maintenance.models import User, Role, Permission, user_role_table, role_permission_table
from sqlalchemy.orm import Session
import random
import string

# Crear una sesión de prueba
@pytest.fixture
def db_session():
    db = SessionLocal()
    yield db
    db.close()

# Crear un usuario con un rol asignado
@pytest.fixture
def test_user_with_permission(db_session: Session):
    # Generar un número de documento único aleatorio (simula un documento único)
    document_number = ''.join(random.choices(string.digits, k=9))  # Genera un número de 9 dígitos
    
    # Generar un correo electrónico único aleatorio
    email = f"test{random.randint(1000, 9999)}@example.com"  # Correo único con un número aleatorio

    # Crear el usuario
    user = User(
        name="Test",
        first_last_name="User",
        second_last_name="Test",
        document_number=document_number,  # Asigna el número de documento aleatorio
        email=email,  # Asigna el correo electrónico aleatorio
        phone="1234567890"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    
    # Crear el permiso 80 (si no existe)
    permission_80 = db_session.query(Permission).filter_by(id=80).first()
    if not permission_80:
        permission_80 = Permission(id=80, name="Technician Permission", description="Permiso para asignación de técnicos")
        db_session.add(permission_80)
        db_session.commit()

    # Crear el rol que tiene el permiso 80
    role_with_permission = Role(name="Technician", description="Rol para técnicos", status=1)
    db_session.add(role_with_permission)
    db_session.commit()

    # Asignar el permiso al rol
    db_session.execute(role_permission_table.insert().values(rol_id=role_with_permission.id, permission_id=80))
    db_session.commit()

    # Asignar el rol al usuario
    db_session.execute(user_role_table.insert().values(user_id=user.id, rol_id=role_with_permission.id))
    db_session.commit()

    return user

# Crear un cliente de prueba y hacer una solicitud GET a la API
def test_get_users_with_permission(db_session: Session, test_user_with_permission):
    # URL de obtener usuarios con permiso
    client = TestClient(app)

    # Llamar al servicio para obtener los usuarios con el permiso 80
    response = client.get("/maintenance/technicians/permission")

    # Verificar el estado de la respuesta
    assert response.status_code == 200
    data = response.json()

    # Verificar que el usuario creado esté en la respuesta
    assert any(user["id"] == test_user_with_permission.id for user in data["data"])

    # Verificar que el usuario tenga los datos correctos
    user_data = next(user for user in data["data"] if user["id"] == test_user_with_permission.id)
    assert user_data["name"] == "Test"
    assert user_data["first_last_name"] == "User"
    assert user_data["second_last_name"] == "Test"
    assert user_data["document_number"] == test_user_with_permission.document_number
