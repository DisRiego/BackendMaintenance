import pytest
from fastapi.testclient import TestClient
from datetime import datetime
from app.main import app  # Asegúrate de importar tu app FastAPI aquí
from app.database import SessionLocal
from app.maintenance.models import User, MaintenanceReport, TechnicianAssignment, Role, Vars, Permission, user_role_table, role_permission_table
from sqlalchemy.orm import Session
import random
import string

# Crear una sesión de prueba
@pytest.fixture
def db_session():
    db = SessionLocal()
    yield db
    db.close()

# Crear usuario con permiso 80
@pytest.fixture
def test_user(db_session: Session):
    # Generar un número de documento único aleatorio (simula un documento único)
    document_number = ''.join(random.choices(string.digits, k=9))  # Genera un número de 9 dígitos
    
    # Generar un correo electrónico único aleatorio
    email = f"test{random.randint(1000, 9999)}@example.com"  # Correo único con un número aleatorio

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

    # Asignar el permiso 80 al usuario
    assign_permission_to_user(user.id, 80)

    return user

# Crear un reporte de mantenimiento
@pytest.fixture
def test_report(db_session: Session):
    # Usamos el ID 6 del lote que ya existe en la base de datos
    report = MaintenanceReport(
        lot_id=6,  # Cambié el ID a 6
        type_failure_id=1,  # Usa un tipo de fallo válido
        description_failure="Fallo de prueba",
        maintenance_status_id=24
    )
    db_session.add(report)
    db_session.commit()
    db_session.refresh(report)
    return report

# Función para asignar permiso al usuario (permiso 80)
def assign_permission_to_user(user_id: int, permission_id: int):
    db = SessionLocal()

    # Obtener el usuario
    user = db.query(User).filter_by(id=user_id).first()

    if not user:
        print(f"Usuario con ID {user_id} no encontrado.")
        db.close()
        return

    # Obtener el rol que tiene el permiso con ID 80
    role_with_permission = db.query(Role).join(role_permission_table).filter(role_permission_table.c.permission_id == permission_id).first()

    if not role_with_permission:
        print(f"No se encontró un rol con el permiso ID {permission_id}.")
        db.close()
        return

    # Asignar el rol al usuario si aún no lo tiene
    if not db.query(user_role_table).filter_by(user_id=user_id, rol_id=role_with_permission.id).first():
        user_role = user_role_table.insert().values(user_id=user_id, rol_id=role_with_permission.id)
        db.execute(user_role)
        db.commit()
        print(f"Rol con permiso {permission_id} asignado al usuario {user_id}.")

    db.close()

# Prueba para asignar un técnico a un reporte de mantenimiento
def test_assign_report_technician(db_session: Session, test_user, test_report):
    # URL de asignación de técnico
    client = TestClient(app)

    # Crear un payload para la asignación
    payload = {
        "user_id": test_user.id,
        "assignment_date": datetime.now().isoformat()
    }

    # Llamar al servicio para asignar el técnico
    response = client.post(
        f"/maintenance/reports/{test_report.id}/assign", json=payload
    )

    # Verificar el estado de la respuesta
    print(f"Response status code: {response.status_code}")
    assert response.status_code == 200
    data = response.json()

    # Comprobar que el técnico ha sido asignado correctamente
    assert data['success'] is True
    assert data['data']['user_id'] == test_user.id
    assert data['data']['report_id'] == test_report.id
    assert data['data']['assignment_date'] is not None

    # Verificar que el estado del reporte se ha actualizado a 24
    updated_report = db_session.query(MaintenanceReport).get(test_report.id)
    assert updated_report.maintenance_status_id == 24

    # Verificar que la asignación del técnico está presente en la base de datos
    technician_assignment = db_session.query(TechnicianAssignment).filter_by(report_id=test_report.id).first()
    assert technician_assignment is not None
    assert technician_assignment.user_id == test_user.id
