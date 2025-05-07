import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal
from app.maintenance.models import MaintenanceType, FailureSolution
from app.maintenance.services import MaintenanceService
from sqlalchemy.orm import Session


@pytest.fixture
def db_session():
    # Crear la sesión de la base de datos para las pruebas
    db: Session = SessionLocal()
    yield db
    db.close()


@pytest.fixture
def maintenance_type(db_session):
    # Asegurarse de que existe un tipo de mantenimiento con ID 1
    maintenance_type = db_session.query(MaintenanceType).filter_by(id=1).first()
    if not maintenance_type:
        maintenance_type = MaintenanceType(id=1, name="Correctivo")
        db_session.add(maintenance_type)
        db_session.commit()
    return maintenance_type


@pytest.fixture
def failure_solution(db_session, maintenance_type):
    # Asegurarse de que existe una solución de fallo con ID 1 y asociarla al tipo de mantenimiento
    failure_solution = db_session.query(FailureSolution).filter_by(id=1).first()
    if not failure_solution:
        failure_solution = FailureSolution(id=1, name="Reparación de tubería", description="Reparar tramo dañado de la tubería sin reemplazo total.")
        db_session.add(failure_solution)
        db_session.commit()

    # Asociar la solución con el tipo de mantenimiento
    db_session.execute(
        """
        INSERT INTO failure_solution_maintenance_type (failure_solution_id, maintenance_type_id)
        VALUES (:failure_solution_id, :maintenance_type_id)
        """,
        {
            "failure_solution_id": failure_solution.id,
            "maintenance_type_id": maintenance_type.id,
        }
    )
    db_session.commit()


def test_get_failure_solutions_by_maintenance_type(db_session, maintenance_type):
    # Crear el cliente para la prueba
    client = TestClient(app)

    # Hacer la solicitud al endpoint con el ID del tipo de mantenimiento 1
    response = client.get(f"/maintenance/failure-solutions/by-maintenance-type/{maintenance_type.id}")

    # Verificar el estado de la respuesta
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True

    # Verificar que las soluciones de fallo están en la respuesta
    assert len(data["data"]) > 0
    assert data["data"][0]["id"] == 1  # Verificar que la solución de fallo con ID 1 está presente
    assert data["data"][0]["name"] == "Reparación de tubería"
    assert data["data"][0]["description"] == "Reparar tramo dañado de la tubería sin reemplazo total."


def test_get_failure_solutions_by_invalid_maintenance_type(db_session):
    # Crear el cliente para la prueba
    client = TestClient(app)

    # Hacer la solicitud con un tipo de mantenimiento que no existe
    response = client.get("/maintenance/failure-solutions/by-maintenance-type/9999")

    # Verificar que el estado es 404
    assert response.status_code == 404
    assert response.json() == {"detail": "Tipo de mantenimiento no encontrado."}
