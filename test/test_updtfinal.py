import pytest
from fastapi.testclient import TestClient
from app.main import app  # Importa tu aplicación FastAPI
from app.database import SessionLocal

@pytest.fixture
def db_session():
    # Configura la sesión de la base de datos, similar a la prueba anterior
    session = SessionLocal()
    yield session
    session.close()

@pytest.fixture
def client():
    # Configura el cliente de prueba
    client = TestClient(app)
    yield client

def test_update_finalization(client, db_session):
    # Datos de la prueba
    detail_id = 1
    type_failure_id = 2
    failure_solution_id = 3
    type_maintenance_id = 2
    
    # Datos de la solicitud
    data = {
        "fault_remarks": "Nueva observación del fallo",
        "type_failure_id": type_failure_id,
        "type_maintenance_id": type_maintenance_id,
        "failure_solution_id": failure_solution_id,
        "solution_remarks": "Nueva observación de la solución"
    }

    # Simulación de archivos de evidencia con las rutas proporcionadas
    files = {
        "evidence_failure": ("failure_image.png", open(r"C:\Users\albar\BackendMaintenance\upload\failure.png", "rb"), "image/png"),
        "evidence_solution": ("solution_image.png", open(r"C:\Users\albar\BackendMaintenance\upload\solution.png", "rb"), "image/png")
    }

    # Hacer la solicitud PUT para actualizar la finalización
    response = client.put(
        f"/maintenance/finalize/{detail_id}",
        data=data,
        files=files,
        follow_redirects=True
    )

    # Verificar el código de estado
    assert response.status_code == 200

    # Verificar que la respuesta contenga datos actualizados
    response_data = response.json()
    assert response_data["success"] is True
    assert response_data["data"]["fault_remarks"] == data["fault_remarks"]
    assert response_data["data"]["solution_remarks"] == data["solution_remarks"]
    assert response_data["data"]["type_failure_id"] == type_failure_id
    assert response_data["data"]["failure_solution_id"] == failure_solution_id
    assert response_data["data"]["type_maintenance_id"] == type_maintenance_id
    assert "evidence_failure_url" in response_data["data"]
    assert "evidence_solution_url" in response_data["data"]
    
    # Cerrar archivos después de la prueba
    files["evidence_failure"][1].close()
    files["evidence_solution"][1].close()
