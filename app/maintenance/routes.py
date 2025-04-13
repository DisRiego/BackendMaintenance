from fastapi import APIRouter, Body, Depends, Form, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
from datetime import datetime
from app.database import get_db
from app.maintenance.services import MaintenenceService

router = APIRouter(prefix="/maintenence", tags=["Maintenence"])

@router.get("/", response_model=Dict)
def get_maintenence(db: Session = Depends(get_db)):
    """Obtener todos los mantenimientos"""
    device_service = MaintenenceService(db)
    return device_service.get_type_open()
