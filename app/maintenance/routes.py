# app/maintenance/routes.py

from fastapi import APIRouter, Depends, Body
from typing import List, Dict
from sqlalchemy.orm import Session
from app.database import get_db
from app.maintenance.services import MaintenanceService
from app.maintenance.schemas import (
    MaintenanceCreate,
    MaintenanceReportCreate,
    MaintenanceReportResponse,
)

router = APIRouter(prefix="/maintenance", tags=["Maintenance"])

@router.get("/", response_model=Dict)
def get_maintenances(db: Session = Depends(get_db)):
    return MaintenanceService(db).get_maintenances()

@router.post("/", response_model=Dict)
def create_maintenance(
    report: MaintenanceCreate,
    db:     Session = Depends(get_db)
):
    return MaintenanceService(db).create_maintenance(report)

@router.post("/{maintenance_id}/assign", response_model=Dict)
def assign_maintenance(
    maintenance_id: int,
    user_id:        int = Body(..., embed=True, description="ID del técnico a asignar"),
    db:             Session = Depends(get_db)
):
    return MaintenanceService(db).assign_technician(maintenance_id, user_id)

@router.get("/reports", response_model=List[MaintenanceReportResponse])
def get_reports(db: Session = Depends(get_db)):
    return MaintenanceService(db).get_reports()

@router.post("/reports", response_model=MaintenanceReportResponse)
def create_report(
    report: MaintenanceReportCreate,
    db:     Session = Depends(get_db)
):
    return MaintenanceService(db).create_report(report)

@router.post("/reports/{report_id}/assign", response_model=Dict)
def assign_report(
    report_id: int,
    user_id:   int = Body(..., embed=True, description="ID del técnico a asignar"),
    db:        Session = Depends(get_db)
):
    return MaintenanceService(db).assign_report_technician(report_id, user_id)

@router.get("/technicians/permission", response_model=Dict)
def get_technicians(db: Session = Depends(get_db)):
    return MaintenanceService(db).get_users_with_permission()
