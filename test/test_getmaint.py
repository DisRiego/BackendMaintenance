import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import get_db
from app.maintenance.models import Maintenance, TypeFailure, Vars, Lot
from datetime import datetime
import random


@pytest.fixture(scope="function")
def db_session():
    # Fixture para la sesión de base de datos
    db = next(get_db())
    test_maintenance_ids = []

    # Generar un ID aleatorio para el mantenimiento
    random_maintenance_id = random.randint(1000, 9999)  # ID aleatorio entre 1000 y 9999

    # Crear un nuevo mantenimiento con un ID aleatorio
    new_maintenance = Maintenance(
        id=random_maintenance_id,
        device_iot_id=20,  # El id del dispositivo (usa el id correcto si es necesario)
        type_failure_id=3,  # El id del tipo de fallo (no lo cambiamos)
        description_failure="el medidor no esta enviando datos",  # Descripción del fallo
        date=datetime(2025, 5, 1),  # Fecha del mantenimiento
        maintenance_status_id=23      # Estado "Finalizado" 
    )
    
    # Insertar el mantenimiento en la base de datos
    db.add(new_maintenance)
    db.commit()
    
    # Guardar el ID del mantenimiento para futuras referencias
    test_maintenance_ids.append(new_maintenance.id)

    yield db, test_maintenance_ids

    # Los datos no se borran después de la prueba; el mantenimiento permanecerá en la base de datos.
    # test_maintenance_ids se usa solo para verificar que el mantenimiento se insertó correctamente.


@pytest.fixture(scope="module")
def client():
    # Fixture para el cliente de pruebas (TestClient)
    return TestClient(app)


@pytest.mark.asyncio
async def test_get_maintenances(client, db_session):
    db, test_maintenance_ids = db_session

    # Obtener estado de mantenimiento "Sin asignar"
    status = db.query(Vars).filter_by(id=24, name="Sin asignar").first()
    assert status, "El estado de mantenimiento 'Sin asignar' no se encontró en la base de datos"

    # Obtener tipo de fallo "Fallo en el medidor" (tipo de fallo con ID=3)
    failure_type = db.query(TypeFailure).filter_by(id=3).first()
    assert failure_type, "El tipo de fallo 'Fallo en el medidor' no se encontró en la base de datos"

    # Usar el lote con ID 2 (asegurarse de que el lote existe)
    lot_id = 2
    lot = db.query(Lot).filter_by(id=lot_id).first()
    assert lot, f"No se encontró el lote con id {lot_id}"

    # Usar el mantenimiento con el ID aleatorio generado
    maintenance_id = test_maintenance_ids[0]  # Usar el ID generado aleatoriamente
    maintenance = db.query(Maintenance).filter_by(id=maintenance_id).first()
    assert maintenance, f"No se encontró el mantenimiento con id {maintenance_id}"
    
    # Llamar al endpoint
    response = client.get("/maintenance/")

    # Comprobamos que la respuesta fue exitosa
    assert response.status_code == 200
    data = response.json().get("data", [])

    # Comprobamos que los datos tengan la estructura esperada
    assert isinstance(data, list)
    assert len(data) > 0, "Se esperaba que la lista de mantenimientos no estuviera vacía"

    # Verificar que el mantenimiento devuelto tiene la información correcta
    maintenance_data = data[0]
    assert "id" in maintenance_data
    assert "property_id" in maintenance_data
    assert "lot_id" in maintenance_data
    assert "failure_type" in maintenance_data
    assert "description_failure" in maintenance_data
    assert "status" in maintenance_data
    assert "date" in maintenance_data


    # Verificar que el mantenimiento devuelto corresponde al "Pendiente" y "Fallo en el medidor"
    assert maintenance_data["status"] == "Sin asignar", "El estado de mantenimiento no es el esperado"
    assert maintenance_data["failure_type"] == "Fallo en el medidor", "El tipo de fallo no es el esperado"
    
