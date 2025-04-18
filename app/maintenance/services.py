# app/maintenance/services.py

from datetime import datetime
from fastapi import HTTPException
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session, aliased

from app.maintenance.models import (
    Maintenance,
    MaintenanceReport,
    TechnicianAssignment,
    TypeFailure,
    Vars,
    DeviceIot,
    Lot,
    PropertyLot,
    PropertyUser,
    User,
    user_role_table,
    role_permission_table,
)

class MaintenanceService:
    def __init__(self, db: Session):
        self.db = db

    def get_maintenances(self):
        """
        Obtener todos los mantenimientos (tabla maintenance), incluyendo
        property_id y owner_document.
        """
        try:
            Owner = aliased(User, name="owner")

            rows = (
                self.db.query(
                    Maintenance.id.label("id"),
                    PropertyLot.property_id.label("property_id"),
                    Owner.document_number.label("owner_document"),
                    TypeFailure.name.label("failure_type"),
                    Maintenance.description_failure,
                    Maintenance.date,
                    Vars.name.label("status"),
                )
                .join(DeviceIot, Maintenance.device_iot_id == DeviceIot.id)
                .join(Lot, DeviceIot.lot_id == Lot.id)
                .join(PropertyLot, PropertyLot.lot_id == Lot.id)
                .join(PropertyUser, PropertyUser.property_id == PropertyLot.property_id)
                .join(Owner, Owner.id == PropertyUser.user_id)
                .join(TypeFailure, Maintenance.type_failure_id == TypeFailure.id)
                .join(Vars, Maintenance.maintenance_status_id == Vars.id)
                .all()
            )

            data = [
                {
                    "id": r.id,
                    "property_id": r.property_id,
                    "owner_document": r.owner_document,
                    "failure_type": r.failure_type,
                    "description_failure": r.description_failure,
                    "date": r.date,
                    "status": r.status,
                }
                for r in rows
            ]

            return JSONResponse(
                status_code=200,
                content=jsonable_encoder({"success": True, "data": data})
            )
        except Exception as e:
            return JSONResponse(status_code=500, content={"success": False, "data": str(e)})

    def create_maintenance(self, data):
        try:
            payload = data.dict()
            payload['maintenance_status_id'] = 24
            obj = Maintenance(**payload)
            self.db.add(obj)
            self.db.commit()
            self.db.refresh(obj)
            return JSONResponse(status_code=200, content=jsonable_encoder({"success": True, "data": obj}))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error al crear mantenimiento: {e}")

    def assign_technician(self, maintenance_id: int, user_id: int):
        # 1) permiso 80
        ok = (
            self.db.query(user_role_table)
            .join(role_permission_table, user_role_table.c.rol_id == role_permission_table.c.rol_id)
            .filter(
                user_role_table.c.user_id == user_id,
                role_permission_table.c.permission_id == 80
            )
            .first()
        )
        if not ok:
            raise HTTPException(status_code=403, detail="Usuario sin permiso 80")

        # 2) existe el mantenimiento?
        maint = self.db.get(Maintenance, maintenance_id)
        if not maint:
            raise HTTPException(status_code=404, detail="Mantenimiento no encontrado")

        # 3) ya asignado?
        if self.db.query(TechnicianAssignment).filter_by(maintenance_id=maintenance_id).first():
            raise HTTPException(status_code=400, detail="Ya existe técnico asignado")

        # 4) asignar y actualizar estado
        assignment = TechnicianAssignment(maintenance_id=maintenance_id, user_id=user_id)
        maint.maintenance_status_id = 23
        self.db.add(assignment)
        self.db.commit()
        self.db.refresh(assignment)

        result = {
            "id":              assignment.id,
            "maintenance_id":  assignment.maintenance_id,
            "user_id":         assignment.user_id,
            "assignment_date": assignment.assignment_date
        }
        return JSONResponse(status_code=200, content=jsonable_encoder({"success": True, "data": result}))

    def get_reports(self):
        """
        Obtener todos los reportes por lote (tabla maintenance_report), incluyendo
        property_id y owner_document.
        """
        try:
            Owner = aliased(User, name="owner")

            rows = (
                self.db.query(
                    MaintenanceReport.id.label("id"),
                    PropertyLot.property_id.label("property_id"),
                    MaintenanceReport.lot_id.label("lot_id"),
                    Owner.document_number.label("owner_document"),
                    TypeFailure.name.label("failure_type"),
                    MaintenanceReport.description_failure,
                    MaintenanceReport.date,
                    Vars.name.label("status"),
                )
                .join(PropertyLot, PropertyLot.lot_id == MaintenanceReport.lot_id)
                .join(PropertyUser, PropertyUser.property_id == PropertyLot.property_id)
                .join(Owner, Owner.id == PropertyUser.user_id)
                .join(TypeFailure, MaintenanceReport.type_failure_id == TypeFailure.id)
                .join(Vars, MaintenanceReport.maintenance_status_id == Vars.id)
                .all()
            )

            data = [
                {
                    "id": r.id,
                    "property_id": r.property_id,
                    "lot_id": r.lot_id,
                    "owner_document": r.owner_document,
                    "failure_type": r.failure_type,
                    "description_failure": r.description_failure,
                    "date": r.date,
                    "status": r.status,
                }
                for r in rows
            ]

            return JSONResponse(
                status_code=200,
                content=jsonable_encoder({"success": True, "data": data})
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    def create_report(self, data):
        try:
            payload = data.dict()
            payload['maintenance_status_id'] = 24
            obj = MaintenanceReport(**payload)
            self.db.add(obj)
            self.db.commit()
            self.db.refresh(obj)
            return JSONResponse(status_code=200, content=jsonable_encoder({"success": True, "data": obj}))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error al crear reporte: {e}")

    def assign_report_technician(self, report_id: int, user_id: int):
        ok = (
            self.db.query(user_role_table)
            .join(role_permission_table, user_role_table.c.rol_id == role_permission_table.c.rol_id)
            .filter(
                user_role_table.c.user_id == user_id,
                role_permission_table.c.permission_id == 80
            )
            .first()
        )
        if not ok:
            raise HTTPException(status_code=403, detail="Usuario sin permiso 80")

        report = self.db.get(MaintenanceReport, report_id)
        if not report:
            raise HTTPException(status_code=404, detail="Reporte no encontrado")

        if self.db.query(TechnicianAssignment).filter_by(report_id=report_id).first():
            raise HTTPException(status_code=400, detail="Ya existe técnico asignado")

        assignment = TechnicianAssignment(report_id=report_id, user_id=user_id)
        report.maintenance_status_id = 23
        self.db.add(assignment)
        self.db.commit()
        self.db.refresh(assignment)

        result = {
            "id":              assignment.id,
            "report_id":       assignment.report_id,
            "user_id":         assignment.user_id,
            "assignment_date": assignment.assignment_date
        }
        return JSONResponse(status_code=200, content=jsonable_encoder({"success": True, "data": result}))

    def get_users_with_permission(self, permission_id: int = 80):
        users = (
            self.db.query(User)
            .join(user_role_table, User.id == user_role_table.c.user_id)
            .join(role_permission_table, user_role_table.c.rol_id == role_permission_table.c.rol_id)
            .filter(role_permission_table.c.permission_id == permission_id)
            .distinct()
            .all()
        )
        data = [
            {
                "id":               u.id,
                "name":             u.name,
                "first_last_name":  u.first_last_name,
                "second_last_name": u.second_last_name,
                "document_number":  u.document_number
            }
            for u in users
        ]
        return JSONResponse(status_code=200, content=jsonable_encoder({"success": True, "data": data}))
