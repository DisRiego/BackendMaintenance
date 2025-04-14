from fastapi import APIRouter, Body, Depends, Form, HTTPException, Query, Path
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional, List
from datetime import datetime, date
from app.database import get_db
from app.maintenance.services import MaintenanceService
from app.maintenance.schemas import (
    MaintenanceCreate, 
    MaintenanceUpdate, 
    TechnicianAssignmentCreate,
    MaintenanceAssignCreate,
    MaintenanceAssignUpdate,
    ResponseModel
)

router = APIRouter(prefix="/maintenance", tags=["Maintenance"])

@router.get("/", response_model=ResponseModel)
def get_all_maintenances(db: Session = Depends(get_db)):
    """Obtener todos los mantenimientos"""
    maintenance_service = MaintenanceService(db)
    return maintenance_service.get_all_maintenances()

@router.get("/status", response_model=ResponseModel)
def get_maintenance_status(db: Session = Depends(get_db)):
    """Obtener todos los estados de mantenimiento"""
    maintenance_service = MaintenanceService(db)
    return maintenance_service.get_maintenance_status()

@router.get("/technicians", response_model=ResponseModel)
def get_technicians(db: Session = Depends(get_db)):
    """Obtener lista de técnicos disponibles"""
    maintenance_service = MaintenanceService(db)
    return maintenance_service.get_technicians()

@router.get("/by-status", response_model=ResponseModel)
def get_maintenance_by_status(
    status_id: Optional[int] = Query(None, description="ID del estado de mantenimiento"),
    db: Session = Depends(get_db)
):
    """Obtener mantenimientos filtrados por estado"""
    maintenance_service = MaintenanceService(db)
    return maintenance_service.get_maintenance_by_status(status_id)

@router.get("/{maintenance_id}", response_model=ResponseModel)
def get_maintenance_by_id(
    maintenance_id: int = Path(..., description="ID del mantenimiento a obtener"),
    db: Session = Depends(get_db)
):
    """Obtener un mantenimiento específico por su ID"""
    maintenance_service = MaintenanceService(db)
    return maintenance_service.get_maintenance_by_id(maintenance_id)

@router.post("/{maintenance_id}/assign", response_model=ResponseModel)
def assign_technician(
    maintenance_id: int = Path(..., description="ID del mantenimiento a asignar"),
    tech_assignment: MaintenanceAssignCreate = Body(...),
    db: Session = Depends(get_db)
):
    """Asignar un técnico a un mantenimiento"""
    maintenance_service = MaintenanceService(db)
    return maintenance_service.assign_technician(maintenance_id, tech_assignment)

@router.put("/{maintenance_id}", response_model=ResponseModel)
def update_maintenance(
    maintenance_id: int = Path(..., description="ID del mantenimiento a actualizar"),
    maintenance_data: MaintenanceAssignUpdate = Body(...),
    db: Session = Depends(get_db)
):
    """Actualizar un mantenimiento"""
    maintenance_service = MaintenanceService(db)
    return maintenance_service.update_maintenance(maintenance_id, maintenance_data)

@router.delete("/{maintenance_id}", response_model=ResponseModel)
def delete_maintenance(
    maintenance_id: int = Path(..., description="ID del mantenimiento a eliminar"),
    db: Session = Depends(get_db)
):
    """Eliminar un mantenimiento"""
    maintenance_service = MaintenanceService(db)
    return maintenance_service.delete_maintenance(maintenance_id)
