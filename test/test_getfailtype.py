import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import get_db
from app.maintenance.models import TypeFailure


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


def test_get_failure_types(db_session, client):
    """
    Test para obtener todos los tipos de fallo (type_failure) existentes.
    """
    # Realiza la solicitud GET al endpoint que recupera todos los tipos de fallo
    response = client.get("/maintenance/failure-types")

    # Verifica que la respuesta tenga código 200
    assert response.status_code == 200, f"Se esperaba código 200, pero se recibió {response.status_code}"

    # Verifica que la respuesta contenga los datos de los tipos de fallo
    data = response.json().get("data", [])
    assert isinstance(data, list), "La respuesta no contiene una lista de tipos de fallo"
    
    # Verifica que los tipos de fallo obtenidos de la base de datos coincidan con los existentes
    types_in_db = db_session.query(TypeFailure).all()
    
    # Verifica que los tipos de fallo obtenidos coincidan con los tipos en la base de datos
    for type_failure in types_in_db:
        assert any(
            t["id"] == type_failure.id and t["name"] == type_failure.name and t["description"] == type_failure.description
            for t in data
        ), f"El tipo de fallo con id {type_failure.id} no se encuentra en la respuesta."
