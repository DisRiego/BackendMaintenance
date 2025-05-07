from datetime import datetime
from fastapi.testclient import TestClient
from app.main import app  # Asegúrate de tener la instancia de FastAPI llamada 'app'

from fastapi.testclient import TestClient
from app.main import app  # Asegúrate de importar la instancia de tu aplicación FastAPI

client = TestClient(app)  # Esto crea un cliente de prueba para tu aplicación FastAPI

def test_get_reports():
    """
    Verifica que la función `get_reports` devuelve correctamente los reportes
    de mantenimiento asociados a un predio y lote específico, y que los datos
    devueltos son correctos, incluyendo los datos del técnico asignado si está presente.
    """
    # Hacemos la petición GET a la ruta de los reportes
    response = client.get("/maintenance/reports")

    # Verificar que la respuesta tenga el código de estado 200
    assert response.status_code == 200

    # Verificar que la respuesta contenga la clave 'success' y sea True
    data = response.json()
    assert data["success"] == True

    # Verificar que los datos contienen una lista de reportes
    assert "data" in data, "La respuesta no contiene la clave 'data'"
    assert isinstance(data["data"], list), "La clave 'data' no contiene una lista de reportes"

    # Verificar que cada reporte tenga las claves esperadas
    for report in data["data"]:
        assert "id" in report
        assert "property_id" in report
        assert "property_name" in report
        assert "lot_id" in report
        assert "lot_name" in report
        assert "owner_document" in report
        assert "failure_type" in report
        assert "description_failure" in report
        assert "date" in report
        assert "status" in report
        assert "technician_id" in report
        assert "technician_name" in report

        # Si hay técnico asignado, verificar que el nombre esté completo
        if report["technician_id"]:
            assert report["technician_name"] is not None, f"El nombre del técnico para el reporte {report['id']} es None"

        # Verificar que los datos numéricos como 'property_id', 'lot_id' sean enteros
        assert isinstance(report["property_id"], int)
        assert isinstance(report["lot_id"], int)

        # Verificar que el 'status' sea un string, ya que se espera un nombre de estado
        assert isinstance(report["status"], str)
