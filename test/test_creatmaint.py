import pytest
from datetime import datetime
from fastapi.testclient import TestClient
from app.main import app  # Asegúrate de que 'main' es el archivo correcto
from app.database import get_db
from app.maintenance.models import Maintenance, DeviceIot, TypeFailure, Vars
from app.database import SessionLocal
import random


@pytest.fixture(scope="function")
def db_session():
    # Fixture para la sesión de base de datos
    db = next(get_db())  # Asegúrate de que get_db esté correctamente definido
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
        maintenance_status_id=24  # Estado "Sin asignar"
    )

    db.add(new_maintenance)
    db.commit()  # Commit para guardar el mantenimiento
    db.refresh(new_maintenance)  # Asegura que el objeto se refresca con la base de datos

    test_maintenance_ids.append(new_maintenance.id)
    yield db

    # Limpiar después de la prueba eliminando el mantenimiento creado
    for maintenance_id in test_maintenance_ids:
        maintenance = db.query(Maintenance).get(maintenance_id)

    db.commit()


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


def test_create_maintenance(client, db_session):
    """
    Prueba que verifica la creación de un mantenimiento con estado 24 (Sin asignar).
    """
    # Datos de entrada para el mantenimiento
    maintenance_data = {
        "device_iot_id": 20,
        "type_failure_id": 3,
        "description_failure": "el medidor no esta enviando datos",
    }

    # Realizar la solicitud POST al endpoint de creación de mantenimiento
    response = client.post("/maintenance/", json=maintenance_data)
    
    # Verificar que la respuesta tenga el código de estado 200
    assert response.status_code == 200
    
    # Obtener los datos de la respuesta
    data = response.json()
    
    # Verificar que la respuesta contiene éxito
    assert data["success"] is True, "El mantenimiento no fue creado exitosamente"
    
    # Verificar que el mantenimiento creado tiene el estado correcto (24: 'Sin asignar')
    created_maintenance = data["data"]
    assert created_maintenance["maintenance_status_id"] == 24, "El estado del mantenimiento no es el esperado (24 - Sin asignar)"
    
    # Verificar que el resto de los datos estén correctos
    assert created_maintenance["device_iot_id"] == maintenance_data["device_iot_id"]
    assert created_maintenance["type_failure_id"] == maintenance_data["type_failure_id"]
    assert created_maintenance["description_failure"] == maintenance_data["description_failure"]
