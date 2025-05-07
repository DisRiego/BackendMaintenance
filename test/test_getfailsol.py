import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import get_db
from app.maintenance.models import FailureSolution


@pytest.fixture(scope="module")
def db_session():
    """Fixture para la sesión de base de datos"""
    # Conéctate a la base de datos y configura la sesión
    db = next(get_db())
    yield db
    # Limpieza si es necesario


@pytest.fixture(scope="module")
def client():
    """Fixture para la configuración del cliente de prueba"""
    with TestClient(app) as client:
        yield client


def test_get_failure_solutions(db_session, client):
    """
    Test para obtener todas las soluciones de fallo (failure_solutions) existentes.
    """
    # Realiza la solicitud GET al endpoint que recupera todas las soluciones
    response = client.get("/maintenance/failure-solutions")

    # Verifica que la respuesta tenga código 200
    assert response.status_code == 200, f"Se esperaba código 200, pero se recibió {response.status_code}"

    # Verifica que la respuesta contenga los datos de las soluciones de fallo
    data = response.json().get("data", [])
    assert isinstance(data, list), "La respuesta no contiene una lista de soluciones de fallo"
    
    # Verifica que las soluciones obtenidas de la base de datos coincidan con las existentes
    solutions_in_db = db_session.query(FailureSolution).all()
    
    # Verifica que las soluciones obtenidas coincidan con las soluciones en la base de datos
    for solution in solutions_in_db:
        assert any(
            s["id"] == solution.id and s["name"] == solution.name and s["description"] == solution.description
            for s in data
        ), f"La solución con id {solution.id} no se encuentra en la respuesta."

