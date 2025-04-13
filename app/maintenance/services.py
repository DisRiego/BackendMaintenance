from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import text
from fastapi import HTTPException
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from app.maintenance.models import Maintenance, MaintenanceDetail, DeviceIot, Lot, PropertyLot, Property, PropertyUser, User, TechnicianAssignment, TypeFailure, FailureSolution, Vars
from app.maintenance.schemas import MaintenanceDetailResponseSchema

class MaintenenceService:
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
            
    def get_maintenance_details(self, maintenance_id: int) -> MaintenanceDetailResponseSchema:
        maintenance = self.db.query(Maintenance).filter(Maintenance.id == maintenance_id).first()

        if not maintenance:
            raise HTTPException(status_code=404, detail="Mantenimiento no encontrado")

        detail = self.db.query(MaintenanceDetail).filter(MaintenanceDetail.maintenance_id == maintenance_id).first()

        device = maintenance.device_iot
        lot = device.lot if device else None

        property_lot = self.db.query(PropertyLot).filter(PropertyLot.lot_id == lot.id).first() if lot else None
        property_obj = self.db.query(Property).filter(Property.id == property_lot.property_id).first() if property_lot else None

        property_user = self.db.query(PropertyUser).filter(PropertyUser.property_id == property_obj.id).first() if property_obj else None
        owner = self.db.query(User).filter(User.id == property_user.user_id).first() if property_user else None

        technician_user = None
        if detail and detail.technician_assignment_id:
            assignment = self.db.query(TechnicianAssignment).filter(TechnicianAssignment.id == detail.technician_assignment_id).first()
            if assignment:
                technician_user = assignment.technician_user

        return MaintenanceDetailResponseSchema(
            fecha_revision=maintenance.date,
            fecha_finalizacion=maintenance.date if maintenance.status == 2 else None,  # Suponiendo que 2 es "Finalizado"
            predio_nombre=property_obj.name if property_obj else None,
            lote_nombre=lot.name if lot else None,
            documento_usuario_reporto=owner.document_number if owner else None,
            nombre_propietario=owner.name if owner else None,
            fecha_reporte=maintenance.date,
            observaciones=maintenance.description_failure,
            nombre_tecnico_asignado=technician_user.name if technician_user else None,
            documento_tecnico_asignado=technician_user.document_number if technician_user else None,
            tipo_mantenimiento=maintenance.type_failure.name if maintenance.type_failure else None,
            fallo_detectado=maintenance.description_failure,
            observaciones_fallo=detail.fault_remarks if detail else None,
            solucion=detail.failure_solution.name if detail and detail.failure_solution else None,
            observaciones_solucion=detail.solution_remarks if detail else None,
            evidencia_fallo=detail.evidence_failure if detail else None,
            evidencia_solucion=detail.evidence_solution if detail else None
        )