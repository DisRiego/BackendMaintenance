from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import text, and_, or_
from fastapi import HTTPException
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder

from app.maintenance.models import (
    Vars, 
    Maintenance, 
    MaintenanceStatus, 
    TypeFailure, 
    TechnicianAssignment, 
    MaintenanceDetail,
    DeviceIot,
    Lot,
    Property,
    Users,
    FailureSolution
)
from app.maintenance.schemas import (
    MaintenanceCreate, 
    MaintenanceUpdate, 
    TechnicianAssignmentCreate,
    MaintenanceAssignCreate,
    MaintenanceAssignUpdate
)

class MaintenanceService:
    def __init__(self, db: Session):
        self.db = db
    
    def get_maintenence(self):
        """Obtener todos los mantenimientos"""
        try:
            # Obtener todos los mantenimientos con el query
            maintenence = self.db.query(Vars).all()

            if not maintenence:
                return JSONResponse(
                    status_code=404,
                    content={
                        "success": False,
                        "data": {
                            "title": "Mantenimiento",
                            "message": "No se encontraron mantenimientos."
                        }
                    }
                )

            # Convertir la respuesta a un formato JSON válido
            maintenence_data = jsonable_encoder(maintenence)

            return JSONResponse(
                status_code=200,
                content={"success": True, "data": maintenence_data}
            )
        except Exception as e:
            # Aquí capturamos cualquier excepción inesperada
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "data": {
                        "title": "Error al obtener mantenimientos",
                        "message": f"Ocurrió un error al intentar obtener los mantenimientos: {str(e)}"
                    }
                }
            )
    
    def get_type_open(self):
        """Obtener todos los tipos de apertura"""
        try:
            return JSONResponse(
                status_code=200,
                content={"success": True, "data": {}}
            )
        except Exception as e:
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "data": {
                        "title": "Error al obtener tipos de apertura",
                        "message": f"Ocurrió un error: {str(e)}"
                    }
                }
            )
    
    def get_all_maintenances(self):
        """Obtener todos los mantenimientos con sus estados"""
        try:
            maintenances = self.db.query(
                Maintenance,
                MaintenanceStatus.name.label("status_name"),
                DeviceIot,
                TypeFailure.name.label("failure_type"),
                Lot,
                Property,
                Users
            ).join(
                MaintenanceStatus, 
                Maintenance.maintenance_status_id == MaintenanceStatus.id, 
                isouter=True
            ).join(
                DeviceIot, 
                Maintenance.device_iot_id == DeviceIot.id, 
                isouter=True
            ).join(
                TypeFailure, 
                Maintenance.type_failure_id == TypeFailure.id, 
                isouter=True
            ).join(
                Lot, 
                DeviceIot.lot_id == Lot.id, 
                isouter=True
            ).join(
                Property, 
                and_(
                    Lot.id == self.db.query(Lot.id)
                    .filter(Lot.id == DeviceIot.lot_id)
                    .scalar_subquery()
                ),
                isouter=True
            ).outerjoin(
                TechnicianAssignment, 
                Maintenance.id == TechnicianAssignment.maintenance_id
            ).outerjoin(
                Users, 
                TechnicianAssignment.user_id == Users.id
            ).all()

            if not maintenances:
                return {
                    "success": True,
                    "data": []
                }

            result = []
            for maintenance, status_name, device, failure_type, lot, property, technician in maintenances:
                result.append({
                    "id": maintenance.id,
                    "property_id": property.id if property else None,
                    "lot_id": lot.id if lot else None,
                    "document_number": technician.document_number if technician else None,
                    "device_type": device.model if device else None,
                    "failure_type": failure_type,
                    "description": maintenance.description_failure,
                    "report_date": maintenance.date,
                    "status": status_name,
                    "technician_name": f"{technician.name} {technician.first_last_name}" if technician else None,
                    "property_name": property.name if property else None,
                    "lot_name": lot.name if lot else None
                })

            return {
                "success": True,
                "data": result
            }
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error al obtener los mantenimientos por estado: {str(e)}"
            )
    
    def get_technicians(self):
        """Obtener lista de técnicos disponibles"""
        try:
            technicians = self.db.query(Users).all()
            
            if not technicians:
                return {
                    "success": True,
                    "data": []
                }
            
            result = []
            for tech in technicians:
                result.append({
                    "id": tech.id,
                    "name": tech.name,
                    "first_last_name": tech.first_last_name,
                    "second_last_name": tech.second_last_name,
                    "document_number": tech.document_number,
                    "email": tech.email
                })
            
            return {
                "success": True,
                "data": result
            }
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error al obtener los técnicos: {str(e)}"
            )
    
    def get_maintenance_status(self):
        """Obtener todos los estados de mantenimiento"""
        try:
            statuses = self.db.query(MaintenanceStatus).all()
            
            if not statuses:
                return {
                    "success": True,
                    "data": []
                }
            
            result = []
            for status in statuses:
                result.append({
                    "id": status.id,
                    "name": status.name
                })
            
            return {
                "success": True,
                "data": result
            }
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error al obtener los estados de mantenimiento: {str(e)}"
            )