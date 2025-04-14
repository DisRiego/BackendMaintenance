from fastapi import APIRouter, Depends, Query, Path
from sqlalchemy.orm import Session
from typing import Dict, Optional
from app.database import get_db
from app.maintenance.services import MaintenanceService

router = APIRouter(prefix="/maintenance", tags=["Maintenance"])

@router.get("/", response_model=Dict)
def get_maintenances(
    status_id: Optional[int] = Query(None, description="ID del estado para filtrar mantenimientos"),
    page: int = Query(1, ge=1, description="Número de página"),
    limit: int = Query(10, ge=1, le=100, description="Cantidad de registros por página"),
    db: Session = Depends(get_db)
):
    """
    Obtener lista de mantenimientos con posibilidad de filtrar por estado.
    
    Permite la paginación de resultados y filtrado por estado de mantenimiento.
    """
    maintenance_service = MaintenanceService(db)
    return maintenance_service.get_maintenances(status_id, page, limit)

@router.get("/status", response_model=Dict)
def get_maintenance_status_list(db: Session = Depends(get_db)):
    """
    Obtener lista de estados posibles para mantenimientos.
    
    Devuelve el catálogo de estados disponibles para los mantenimientos.
    """
    maintenance_service = MaintenanceService(db)
    return maintenance_service.get_maintenance_status_list()

@router.get("/failure-types", response_model=Dict)
def get_failure_types(db: Session = Depends(get_db)):
    """
    Obtener lista de tipos de fallas para mantenimientos.
    
    Devuelve el catálogo de tipos de fallas disponibles para los mantenimientos.
    """
    maintenance_service = MaintenanceService(db)
    return maintenance_service.get_failure_types()

@router.get("/statistics", response_model=Dict)
def get_maintenance_statistics(db: Session = Depends(get_db)):
    """
    Obtener estadísticas de mantenimientos.
    
    Devuelve el total de mantenimientos y el conteo por cada estado.
    """
    maintenance_service = MaintenanceService(db)
    return maintenance_service.get_maintenance_statistics()

@router.get("/{maintenance_id}", response_model=Dict)
def get_maintenance_by_id(
    maintenance_id: int = Path(..., description="ID del mantenimiento a consultar"),
    db: Session = Depends(get_db)
):
    """
    Obtener detalle completo de un mantenimiento específico.
    
    Devuelve toda la información del mantenimiento, incluyendo asignaciones de técnicos y detalles.
    """
    maintenance_service = MaintenanceService(db)
    return maintenance_service.get_maintenance_by_id(maintenance_id)