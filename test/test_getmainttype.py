import pytest
from fastapi.testclient import TestClient
from app.main import app  # Asumiendo que el archivo de FastAPI es 'main.py'
from app.database import SessionLocal


# Fixture para crear una sesión de base de datos
@pytest.fixture(scope="module")
def db_session():
    # Crear una nueva sesión de base de datos
    db = SessionLocal()
    yield db
    # Cerrar la sesión después de la prueba
    db.close()

# Fixture para el cliente de prueba de FastAPI
@pytest.fixture(scope="module")
def client():
    return TestClient(app)

def test_get_maintenance_types(client, db_session):
    """
    Prueba que verifica la respuesta de la ruta '/maintenance/maintenance-types'
    asegurándose de que los tipos de mantenimiento con ID 1 y 2 sean devueltos correctamente.
    """
    # Realizar la solicitud GET al endpoint de mantenimiento
    response = client.get("/maintenance/maintenance-types")
    
    # Verificar que la respuesta sea exitosa (código 200)
    assert response.status_code == 200
    
    # Obtener la lista de tipos de mantenimiento (ahora asumimos que es directamente una lista)
    data = response.json()
    
    # Verificar que la respuesta sea una lista
    assert isinstance(data, list), "La respuesta no es una lista de tipos de mantenimiento"
    
    # Verificar que la lista no esté vacía (debe tener al menos dos tipos de mantenimiento)
    assert len(data) >= 2, "Se esperaba que la lista de tipos de mantenimiento tuviera al menos dos elementos"

    # Verificar que los datos de la respuesta contienen la información esperada para los tipos 1 y 2
    maintenance_types = [t["name"] for t in data]
    
    # Verificar que los tipos de mantenimiento con nombre esperado estén en la respuesta
    assert "Correctivo" in maintenance_types, "Falta el tipo de mantenimiento 'Correctivo'"
    assert "Preventivo" in maintenance_types, "Falta el tipo de mantenimiento 'Preventivo'"
    
    # Verificar que los IDs coincidan con los tipos existentes en la base de datos (1 y 2)
    maintenance_type_1 = next(t for t in data if t["name"] == "Correctivo")
    maintenance_type_2 = next(t for t in data if t["name"] == "Preventivo")
    
    assert maintenance_type_1["id"] == 1, f"Se esperaba ID 1 para 'Correctivo', pero se obtuvo {maintenance_type_1['id']}"
    assert maintenance_type_2["id"] == 2, f"Se esperaba ID 2 para 'Preventivo', pero se obtuvo {maintenance_type_2['id']}"
