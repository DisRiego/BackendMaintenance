# app/maintenance/services.py
from typing import List
from datetime import datetime
from uuid import uuid4
from fastapi import HTTPException, UploadFile
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session, aliased  

from app.maintenance.models import (
    Maintenance,
    MaintenanceReport,
    TechnicianAssignment,
    MaintenanceDetail,
    FailureSolution,
    User,
    DeviceIot,
    Lot,
    PropertyLot,
    PropertyUser,
    TypeFailure,
    Vars,
    Property,
    MaintenanceType,
    bucket,
    user_role_table,
    role_permission_table,
)
from app.maintenance.schemas import MaintenanceDetailCreate , MaintenanceTypeSchema , MaintenanceUpdate

def _upload(file: UploadFile, folder: str) -> str:
    """
    Sube un UploadFile a Firebase Storage en la carpeta indicada
    y devuelve la URL pública.
    """
    ext = file.filename.rsplit('.', 1)[-1]
    blob_name = f"{folder}/{uuid4()}.{ext}"
    blob = bucket.blob(blob_name)
    content = file.file.read()
    blob.upload_from_string(content, content_type=file.content_type)
    return blob.public_url

class MaintenanceService:
    def __init__(self, db: Session):
        self.db = db

    def get_maintenances(self):
        """
        Obtener todos los mantenimientos (tabla maintenance), incluyendo
        property_id, owner_document, técnico asignado.
        """
        try:
            Owner = aliased(User, name="owner")
            TA    = aliased(TechnicianAssignment, name="ta")
            Tech  = aliased(User, name="tech")

            rows = (
                self.db.query(
                    Maintenance.id.label("id"),
                    PropertyLot.property_id.label("property_id"),
                    Owner.document_number.label("owner_document"),
                    TypeFailure.name.label("failure_type"),
                    Maintenance.description_failure,
                    Maintenance.date,
                    Vars.name.label("status"),
                    TA.user_id.label("technician_id"),
                    Tech.name.label("tech_name"),
                    Tech.first_last_name.label("tech_last1"),
                    Tech.second_last_name.label("tech_last2"),
                )
                .join(DeviceIot, Maintenance.device_iot_id == DeviceIot.id)
                .join(Lot, DeviceIot.lot_id == Lot.id)
                .join(PropertyLot, PropertyLot.lot_id == Lot.id)
                .join(PropertyUser, PropertyUser.property_id == PropertyLot.property_id)
                .join(Owner, Owner.id == PropertyUser.user_id)
                .join(TypeFailure, Maintenance.type_failure_id == TypeFailure.id)
                .join(Vars, Maintenance.maintenance_status_id == Vars.id)
                .outerjoin(TA, TA.maintenance_id == Maintenance.id)
                .outerjoin(Tech, Tech.id == TA.user_id)
                .all()
            )
            data = []
            for r in rows:
                full_name = None
                if r.technician_id:
                    parts = [r.tech_name, r.tech_last1, r.tech_last2]
                    full_name = " ".join(filter(None, parts))

                data.append({
                    "id": r.id,
                    "property_id": r.property_id,
                    "owner_document": r.owner_document,
                    "failure_type": r.failure_type,
                    "description_failure": r.description_failure,
                    "date": r.date,
                    "status": r.status,
                    "technician_id": r.technician_id,
                    "technician_name": full_name,
                })

            return JSONResponse(status_code=200, content=jsonable_encoder({"success": True, "data": data}))
        except Exception as e:
            return JSONResponse(status_code=500, content={"success": False, "data": str(e)})
        
    def get_maintenance_types(self) -> List[MaintenanceTypeSchema]:
            """
            Obtener todos los tipos de mantenimiento y devolver como lista de MaintenanceTypeSchema.
            """
            types = self.db.query(MaintenanceType).all()  
            return [MaintenanceTypeSchema.from_orm(t) for t in types]  

    def create_maintenance(self, data):
        """
        Crear un nuevo registro en maintenance con status = 24 (Sin asignar).
        """
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

    def assign_technician(self, maintenance_id: int, user_id: int, assignment_date: datetime):
        """
        Asignar un técnico a un maintenance:
        - valida permiso 80
        - comprueba existencia de maintenance
        - evita duplicados
        - cambia status a 23
        - guarda fecha de asignación
        """
        has_perm = (
            self.db.query(user_role_table)
            .join(role_permission_table, user_role_table.c.rol_id == role_permission_table.c.rol_id)
            .filter(
                user_role_table.c.user_id == user_id,
                role_permission_table.c.permission_id == 80
            )
            .first()
        )
        if not has_perm:
            raise HTTPException(status_code=403, detail="Usuario sin permiso 80")

        maint = self.db.get(Maintenance, maintenance_id)
        if not maint:
            raise HTTPException(status_code=404, detail="Mantenimiento no encontrado")

        if self.db.query(TechnicianAssignment).filter_by(maintenance_id=maintenance_id).first():
            raise HTTPException(status_code=400, detail="Ya existe técnico asignado")

        assignment = TechnicianAssignment(
            maintenance_id=maintenance_id,
            user_id=user_id,
            assignment_date=assignment_date
        )
        maint.maintenance_status_id = 23
        self.db.add(assignment)
        self.db.commit()
        self.db.refresh(assignment)

        result = {
            "id": assignment.id,
            "maintenance_id": assignment.maintenance_id,
            "user_id": assignment.user_id,
            "assignment_date": assignment.assignment_date
        }
        return JSONResponse(status_code=200, content=jsonable_encoder({"success": True, "data": result}))

    def get_reports(self):
        """
        Obtener todos los reportes por lote, incluyendo:
        - property_id + property_name
        - lot_id      + lot_name
        - owner_document, tipo de fallo, fecha y estado
        - technician_id y technician_name (si está asignado)
        """
        try:
            Owner = aliased(User, name="owner")
            TA    = aliased(TechnicianAssignment, name="ta")
            Tech  = aliased(User, name="tech")

            rows = (
                self.db.query(
                    MaintenanceReport.id.label("id"),
                    PropertyLot.property_id.label("property_id"),
                    Property.name.label("property_name"),
                    MaintenanceReport.lot_id.label("lot_id"),
                    Lot.name.label("lot_name"),
                    Owner.document_number.label("owner_document"),
                    TypeFailure.name.label("failure_type"),
                    MaintenanceReport.description_failure,
                    MaintenanceReport.date,
                    Vars.name.label("status"),
                    TA.user_id.label("technician_id"),
                    Tech.name.label("tech_name"),
                    Tech.first_last_name.label("tech_last1"),
                    Tech.second_last_name.label("tech_last2"),
                )
                .join(PropertyLot, PropertyLot.lot_id == MaintenanceReport.lot_id)
                .join(Property,    Property.id == PropertyLot.property_id)
                .join(Lot,         Lot.id == MaintenanceReport.lot_id)
                .join(PropertyUser, PropertyUser.property_id == PropertyLot.property_id)
                .join(Owner,        Owner.id == PropertyUser.user_id)
                .join(TypeFailure,  MaintenanceReport.type_failure_id == TypeFailure.id)
                .join(Vars,         MaintenanceReport.maintenance_status_id == Vars.id)
                .outerjoin(TA,    TA.report_id == MaintenanceReport.id)
                .outerjoin(Tech,  Tech.id == TA.user_id)
                .all()
            )

            data = []
            for r in rows:
                # Si no hay técnico asignado: technician_id = None, name = None
                if r.technician_id:
                    parts = [r.tech_name, r.tech_last1, r.tech_last2]
                    # filter(None, ...) quita None o cadenas vacías
                    full_name = " ".join(filter(None, parts))
                else:
                    full_name = None

                data.append({
                    "id":                   r.id,
                    "property_id":          r.property_id,
                    "property_name":        r.property_name,
                    "lot_id":               r.lot_id,
                    "lot_name":             r.lot_name,
                    "owner_document":       r.owner_document,
                    "failure_type":         r.failure_type,
                    "description_failure":  r.description_failure,
                    "date":                 r.date,
                    "status":               r.status,
                    "technician_id":        r.technician_id,
                    "technician_name":      full_name,
                })

            return JSONResponse(status_code=200, content=jsonable_encoder({"success": True, "data": data}))
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    def create_report(self, data):
        """
        Crear un nuevo registro en maintenance_report con status = 24.
        """
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
        """
        Asignar un técnico a un maintenance_report:
          - valida permiso 80
          - comprueba existencia de report
          - evita duplicados
          - cambia status a 23
        """
        has_perm = (
            self.db.query(user_role_table)
            .join(role_permission_table, user_role_table.c.rol_id == role_permission_table.c.rol_id)
            .filter(
                user_role_table.c.user_id == user_id,
                role_permission_table.c.permission_id == 80
            )
            .first()
        )
        if not has_perm:
            raise HTTPException(status_code=403, detail="Usuario sin permiso 80")

        rpt = self.db.get(MaintenanceReport, report_id)
        if not rpt:
            raise HTTPException(status_code=404, detail="Reporte no encontrado")

        if self.db.query(TechnicianAssignment).filter_by(report_id=report_id).first():
            raise HTTPException(status_code=400, detail="Ya existe técnico asignado")

        assignment = TechnicianAssignment(report_id=report_id, user_id=user_id)
        rpt.maintenance_status_id = 23
        self.db.add(assignment)
        self.db.commit()
        self.db.refresh(assignment)

        result = {
            "id":        assignment.id,
            "report_id": assignment.report_id,
            "user_id":   assignment.user_id,
            "assignment_date": assignment.assignment_date
        }
        return JSONResponse(status_code=200, content=jsonable_encoder({"success": True, "data": result}))

    def get_users_with_permission(self, permission_id: int = 80):
        """
        Obtener todos los usuarios que tengan el permiso indicado.
        """
        users = (
            self.db.query(User)
            .join(user_role_table, User.id == user_role_table.c.user_id)
            .join(role_permission_table, user_role_table.c.rol_id == role_permission_table.c.rol_id)
            .filter(role_permission_table.c.permission_id == permission_id)
            .distinct()
            .all()
        )
        data = [{
            "id":               u.id,
            "name":             u.name,
            "first_last_name":  u.first_last_name,
            "second_last_name": u.second_last_name,
            "document_number":  u.document_number
        } for u in users]
        return JSONResponse(status_code=200, content=jsonable_encoder({"success": True, "data": data}))

    def get_assigned_maintenances_for_technician(self, technician_id: int):
        tech = self.db.get(User, technician_id)
        if not tech:
            raise HTTPException(status_code=404, detail="Técnico no encontrado")

        Owner = aliased(User, name="owner")
        A = aliased(TechnicianAssignment, name="asgmt")
        rows = (
            self.db.query(
                A.id.label("technician_assignment_id"),
                Maintenance.id.label("maintenance_id"),
                DeviceIot.id.label("device_iot_id"),
                Lot.id.label("lot_id"),
                Lot.name.label("lot_name"),                     
                PropertyLot.property_id.label("property_id"),
                Property.name.label("property_name"),            
                Maintenance.date.label("report_date"),
                TypeFailure.name.label("failure_type"),
                Maintenance.description_failure,
                Vars.name.label("status"),
                A.assignment_date.label("assigned_at"),
            )
            .select_from(A)
            .join(Maintenance,   A.maintenance_id == Maintenance.id)
            .join(DeviceIot,     Maintenance.device_iot_id == DeviceIot.id)
            .join(Lot,           DeviceIot.lot_id == Lot.id)
            .join(PropertyLot,   PropertyLot.lot_id == Lot.id)
            .join(Property,      Property.id == PropertyLot.property_id)     
            .join(PropertyUser,  PropertyUser.property_id == PropertyLot.property_id)
            .join(Owner,         Owner.id == PropertyUser.user_id)
            .join(TypeFailure,   Maintenance.type_failure_id == TypeFailure.id)
            .join(Vars,          Maintenance.maintenance_status_id == Vars.id)
            .filter(A.user_id == technician_id, A.maintenance_id.isnot(None))
            .all()
        )
        data = [{
            "technician_assignment_id": r.technician_assignment_id,
            "maintenance_id":      r.maintenance_id,
            "device_iot_id":       r.device_iot_id,
            "lot_id":              r.lot_id,
            "lot_name":            r.lot_name,                 
            "property_id":         r.property_id,
            "property_name":       r.property_name,           
            "report_date":         r.report_date,
            "failure_type":        r.failure_type,
            "description_failure": r.description_failure,
            "status":              r.status,
            "assigned_at":         r.assigned_at,
        } for r in rows]
        return JSONResponse(content=jsonable_encoder({"success": True, "data": data}), status_code=200)

    def get_assigned_reports_for_technician(self, technician_id: int):
        tech = self.db.get(User, technician_id)
        if not tech:
            raise HTTPException(status_code=404, detail="Técnico no encontrado")

        Owner = aliased(User, name="owner")
        A = aliased(TechnicianAssignment, name="asgmt")
        rows = (
            self.db.query(
                A.id.label("technician_assignment_id"),
                MaintenanceReport.id.label("report_id"),
                MaintenanceReport.lot_id.label("lot_id"),
                Lot.name.label("lot_name"),                      
                PropertyLot.property_id.label("property_id"),
                Property.name.label("property_name"),            
                MaintenanceReport.date.label("report_date"),
                TypeFailure.name.label("failure_type"),
                MaintenanceReport.description_failure,
                Vars.name.label("status"),
                A.assignment_date.label("assigned_at"),
            )
            .select_from(A)
            .join(MaintenanceReport, A.report_id == MaintenanceReport.id)
            .join(Lot,              Lot.id == MaintenanceReport.lot_id)     
            .join(PropertyLot,      PropertyLot.lot_id == MaintenanceReport.lot_id)
            .join(Property,         Property.id == PropertyLot.property_id)  
            .join(PropertyUser,     PropertyUser.property_id == PropertyLot.property_id)
            .join(Owner,            Owner.id == PropertyUser.user_id)
            .join(TypeFailure,      MaintenanceReport.type_failure_id == TypeFailure.id)
            .join(Vars,             MaintenanceReport.maintenance_status_id == Vars.id)
            .filter(A.user_id == technician_id, A.report_id.isnot(None))
            .all()
        )
        data = [{
            "technician_assignment_id": r.technician_assignment_id,
            "report_id":           r.report_id,
            "lot_id":              r.lot_id,
            "lot_name":            r.lot_name,                 
            "property_id":         r.property_id,
            "property_name":       r.property_name,           
            "report_date":         r.report_date,
            "failure_type":        r.failure_type,
            "description_failure": r.description_failure,
            "status":              r.status,
            "assigned_at":         r.assigned_at,
        } for r in rows]
        return JSONResponse(content=jsonable_encoder({"success": True, "data": data}), status_code=200)

    async def finalize_assignment(
            self,
            data: MaintenanceDetailCreate,
            evidence_failure: UploadFile,
            evidence_solution: UploadFile
        ):
            """
            Finaliza un mantenimiento o reporte asignado:
            - Sube evidencias a Firebase
            - Crea registro en maintenance_detail
            - Cambia el estado a 25 (Finalizado)
            """
            asgmt = self.db.get(TechnicianAssignment, data.technician_assignment_id)
            if not asgmt:
                raise HTTPException(status_code=404, detail="Asignación no encontrada")

            url_fail = _upload(evidence_failure, "failures")
            url_sol  = _upload(evidence_solution, "solutions")

            detail = MaintenanceDetail(
                technician_assignment_id = data.technician_assignment_id,
                fault_remarks            = data.fault_remarks,
                evidence_failure_url     = url_fail,
                type_failure_id          = data.type_failure_id,
                type_maintenance_id      = data.type_maintenance_id,  # <- importante
                failure_solution_id      = data.failure_solution_id,
                solution_remarks         = data.solution_remarks,
                evidence_solution_url    = url_sol
            )
            self.db.add(detail)

            if asgmt.maintenance_id:
                obj = self.db.get(Maintenance, asgmt.maintenance_id)
            else:
                obj = self.db.get(MaintenanceReport, asgmt.report_id)
            obj.maintenance_status_id = 25

            self.db.commit()
            self.db.refresh(detail)

            return JSONResponse(status_code=200, content=jsonable_encoder({"success": True, "data": detail}))

    
    def get_failure_solutions(self):
        """
        Obtener todos los tipos de solución (failure_solution).
        """
        sols = self.db.query(FailureSolution).all()
        data = [{"id": s.id, "name": s.name, "description": s.description} for s in sols]
        return JSONResponse(status_code=200, content=jsonable_encoder({"success": True, "data": data}))

    def get_failure_types(self):
        """
        Obtener todos los tipos de fallo (type_failure).
        """
        types = self.db.query(TypeFailure).all()
        data = [{"id": t.id, "name": t.name, "description": t.description} for t in types]
        return JSONResponse(status_code=200, content=jsonable_encoder({"success": True, "data": data}))

    def get_report_detail(self, report_id: int):
        """
        Detalle completo de un reporte por lote, ahora incluye:
        - NOMBRE de estado, predio y lote
        """
        rpt = self.db.get(MaintenanceReport, report_id)
        if not rpt:
            raise HTTPException(status_code=404, detail="Reporte no encontrado")

        # Predio y dueño
        prop_id = (
            self.db.query(PropertyLot.property_id)
            .filter(PropertyLot.lot_id == rpt.lot_id)
            .scalar()
        )
        prop = self.db.get(Property, prop_id)                       
        owner = (
            self.db.query(User)
            .join(PropertyUser, PropertyUser.user_id == User.id)
            .filter(PropertyUser.property_id == prop_id)
            .first()
        )

        # Asignación y detalle (si existen)
        asgmt = (
            self.db.query(TechnicianAssignment)
            .filter(TechnicianAssignment.report_id == report_id)
            .first()
        )
        detail = (
            self.db.query(MaintenanceDetail)
            .filter(MaintenanceDetail.technician_assignment_id == asgmt.id)
            .first()
        ) if asgmt else None

        data = {
            
            "property_id":    prop_id,
            "property_name":  prop.name,
            "property_latitude":  prop.latitude,
            "property_longitude":  prop.longitude,
            "lot_id":         rpt.lot_id,
            "lot_name":       rpt.lot.name,
            "lot_latitude":       rpt.lot.latitude,
            "lot_longitude":       rpt.lot.longitude,
            "status":         rpt.status.name,
            "status_id":      rpt.maintenance_status_id,
            "owner_document":      owner.document_number,
            "owner_name":          f"{owner.name} {owner.first_last_name} {owner.second_last_name}",
            "owner_email":      owner.email,
            "owner_phone":      owner.phone,
            "report_date":         rpt.date,
            "failure_type":        rpt.type_failure.name,
            "description_failure": rpt.description_failure,
            
            "assignment_date":   asgmt.assignment_date if asgmt else None,
            "finalized":         bool(detail),
            "finalization_date": detail.date if detail else None,
            "technician_id": asgmt.user_id if asgmt else None,
            "technician_name":     detail.assignment.technician.name if detail else None,
            "type_maintenance":    detail.type_maintenance if detail else None,
            "fault_remarks":       detail.fault_remarks if detail else None,
            "solution_name":       detail.failure_solution.name if detail else None,
            "solution_remarks":    detail.solution_remarks if detail else None,
            "evidence_failure_url":  detail.evidence_failure_url if detail else None,
            "evidence_solution_url": detail.evidence_solution_url if detail else None,
        }
        return JSONResponse(status_code=200, content=jsonable_encoder({"success": True, "data": data}))
    
    def get_maintenance_detail(self, maintenance_id: int):
        """
        Obtener detalle completo de un mantenimiento IoT,
        incluyendo nombre de predio, nombre de lote y estado.
        """
        maint = self.db.get(Maintenance, maintenance_id)
        if not maint:
            raise HTTPException(status_code=404, detail="Mantenimiento no encontrado")

        # lote y predio
        lot_id = self.db.query(DeviceIot.lot_id) \
                        .filter(DeviceIot.id == maint.device_iot_id) \
                        .scalar()
        prop_id = self.db.query(PropertyLot.property_id) \
                         .filter(PropertyLot.lot_id == lot_id) \
                         .scalar()

        prop = self.db.get(Property, prop_id)
        lot  = self.db.get(Lot, lot_id)

        owner = self.db.query(User) \
                       .join(PropertyUser, PropertyUser.user_id == User.id) \
                       .filter(PropertyUser.property_id == prop_id) \
                       .first()

        # asignación y detalle
        asgmt = self.db.query(TechnicianAssignment) \
                      .filter(TechnicianAssignment.maintenance_id == maintenance_id) \
                      .first()
        assign_date = asgmt.assignment_date if asgmt else None

        detail = None
        if asgmt:
            detail = self.db.query(MaintenanceDetail) \
                            .filter(MaintenanceDetail.technician_assignment_id == asgmt.id) \
                            .first()

        data = {
            "property_id":         prop_id,
            "property_name":       prop.name,                
            "lot_id":              lot_id,
            "lot_name":            lot.name,                
            "owner_document":      owner.document_number,
            "owner_name":          f"{owner.name} {owner.first_last_name} {owner.second_last_name}",
            "report_date":         maint.date,
            "failure_type":        maint.type_failure.name,
            "description_failure": maint.description_failure,
            "status":              maint.status.name,
            "status_id":      maint.maintenance_status_id,      
            "assignment_date":     assign_date,
            "finalized":           bool(detail),
            "finalization_date":   detail.date if detail else None,
            "technician_name":     detail.assignment.technician.name if detail else None,
            "technician_document": detail.assignment.technician.document_number if detail else None,
            "type_maintenance":    detail.type_maintenance if detail else None,
            "fault_remarks":       detail.fault_remarks if detail else None,
            "solution_name":       detail.failure_solution.name if detail else None,
            "solution_remarks":    detail.solution_remarks if detail else None,
            "evidence_failure_url":  detail.evidence_failure_url if detail else None,
            "evidence_solution_url": detail.evidence_solution_url if detail else None,
        }
        return JSONResponse(status_code=200, content=jsonable_encoder({"success": True, "data": data}))
    

    def get_maintenances_by_user(self, user_id: int):
        """
        Obtener todos los mantenimientos IoT de un usuario,
        incluyendo nombre de predio, nombre de lote y estado.
        """
        if not self.db.get(User, user_id):
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        rows = (
            self.db.query(
                Maintenance.id.label("maintenance_id"),
                DeviceIot.id.label("device_iot_id"),
                Lot.id.label("lot_id"),
                Lot.name.label("lot_name"),                    
                PropertyLot.property_id.label("property_id"),
                Property.name.label("property_name"),          
                Maintenance.date.label("report_date"),
                Maintenance.maintenance_status_id.label("status_id"),
                TypeFailure.name.label("failure_type"),
                Maintenance.description_failure,
                Vars.name.label("status"),                     
            )
            .join(DeviceIot, Maintenance.device_iot_id == DeviceIot.id)
            .join(Lot, DeviceIot.lot_id == Lot.id)
            .join(PropertyLot, PropertyLot.lot_id == Lot.id)
            .join(Property, Property.id == PropertyLot.property_id)
            .join(PropertyUser, PropertyUser.property_id == PropertyLot.property_id)
            .join(TypeFailure, Maintenance.type_failure_id == TypeFailure.id)
            .join(Vars, Maintenance.maintenance_status_id == Vars.id)
            .filter(PropertyUser.user_id == user_id)
            .all()
        )
        data = [
            {
                "maintenance_id":      r.maintenance_id,
                "device_iot_id":       r.device_iot_id,
                "lot_id":              r.lot_id,
                "lot_name":            r.lot_name,              
                "property_id":         r.property_id,
                "property_name":       r.property_name,         
                "report_date":         r.report_date,
                "failure_type":        r.failure_type,
                "description_failure": r.description_failure,
                "status":              r.status,
                "status_id":           r.status_id                
            }
            for r in rows
        ]
        return JSONResponse(
            status_code=200,
            content=jsonable_encoder({"success": True, "data": data})
        )
    
    def get_reports_by_user(self, user_id: int):
        """
        Obtener todos los reportes por lote de un usuario,
        incluyendo nombre de predio, nombre de lote y estado.
        """
        if not self.db.get(User, user_id):
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        rows = (
            self.db.query(
                MaintenanceReport.id.label("report_id"),
                MaintenanceReport.lot_id.label("lot_id"),
                Lot.name.label("lot_name"),                     
                PropertyLot.property_id.label("property_id"),
                Property.name.label("property_name"),           
                MaintenanceReport.date.label("report_date"),
                TypeFailure.name.label("failure_type"),
                MaintenanceReport.description_failure,
                Vars.name.label("status"),
                MaintenanceReport.maintenance_status_id.label("status_id")                      
            )
            .join(Lot, Lot.id == MaintenanceReport.lot_id)
            .join(PropertyLot, PropertyLot.lot_id == MaintenanceReport.lot_id)
            .join(Property, Property.id == PropertyLot.property_id)
            .join(PropertyUser, PropertyUser.property_id == PropertyLot.property_id)
            .join(TypeFailure, MaintenanceReport.type_failure_id == TypeFailure.id)
            .join(Vars, MaintenanceReport.maintenance_status_id == Vars.id)
            .filter(PropertyUser.user_id == user_id)
            .all()
        )
        data = [
            {
                "report_id":           r.report_id,
                "lot_id":              r.lot_id,
                "lot_name":            r.lot_name,              
                "property_id":         r.property_id,
                "property_name":       r.property_name,         
                "report_date":         r.report_date,
                "failure_type":        r.failure_type,
                "description_failure": r.description_failure,
                "status":              r.status,
                "status_id":           r.status_id     
                           
            }
            for r in rows
        ]
        return JSONResponse(
            status_code=200,
            content=jsonable_encoder({"success": True, "data": data})
        )

    def update_report(self, report_id: int, data):
        """
        Edición parcial del reporte (maintenance_report).
        Acepta cualquiera de los campos del body.
        """
        rpt = self.db.get(MaintenanceReport, report_id)
        if not rpt:
            raise HTTPException(status_code=404, detail="Reporte no encontrado")

        payload = data.dict(exclude_unset=True)
        for k, v in payload.items():
            setattr(rpt, k, v)

        self.db.commit()
        self.db.refresh(rpt)
        return JSONResponse(status_code=200, content=jsonable_encoder({"success": True, "data": rpt}))


    async def update_finalization(
        self,
        detail_id: int,
        data,
        evidence_failure: UploadFile | None = None,
        evidence_solution: UploadFile | None = None,
    ):
        """
        Modifica un registro de maintenance_detail.
        Evidencias nuevas (si vienen) se suben y reemplazan URLs.
        """
        detail = self.db.get(MaintenanceDetail, detail_id)
        if not detail:
            raise HTTPException(status_code=404, detail="Detalle no encontrado")

        payload = data.dict(exclude_unset=True)
        for k, v in payload.items():
            setattr(detail, k, v)

        if evidence_failure:
            detail.evidence_failure_url = _upload(evidence_failure, "failures")
        if evidence_solution:
            detail.evidence_solution_url = _upload(evidence_solution, "solutions")

        self.db.commit()
        self.db.refresh(detail)
        return JSONResponse(status_code=200, content=jsonable_encoder({"success": True, "data": detail}))
    


    def update_maintenance(self, maintenance_id: int, data: MaintenanceUpdate):
        maint = self.db.get(Maintenance, maintenance_id)
        if not maint:
            raise HTTPException(status_code=404, detail="Mantenimiento no encontrado")
        payload = data.dict(exclude_unset=True)
        for k, v in payload.items():
            setattr(maint, k, v)
        self.db.commit()
        self.db.refresh(maint)
        return JSONResponse(status_code=200, content=jsonable_encoder({"success": True, "data": maint}))

    def update_maintenance_assignment(self, maintenance_id: int, user_id: int, assignment_date: datetime):
        asgmt = (
            self.db.query(TechnicianAssignment)
            .filter_by(maintenance_id=maintenance_id)
            .first()
        )
        if not asgmt:
            raise HTTPException(status_code=404, detail="Asignación no encontrada")
        asgmt.user_id = user_id
        asgmt.assignment_date = assignment_date
        self.db.commit()
        self.db.refresh(asgmt)
        result = {
            "id":               asgmt.id,
            "maintenance_id":   asgmt.maintenance_id,
            "user_id":          asgmt.user_id,
            "assignment_date":  asgmt.assignment_date
        }
        return JSONResponse(status_code=200, content=jsonable_encoder({"success": True, "data": result}))

    def update_report_assignment(self, report_id: int, user_id: int, assignment_date: datetime):
        asgmt = (
            self.db.query(TechnicianAssignment)
            .filter_by(report_id=report_id)
            .first()
        )
        if not asgmt:
            raise HTTPException(status_code=404, detail="Asignación no encontrada")
        asgmt.user_id = user_id
        asgmt.assignment_date = assignment_date
        self.db.commit()
        self.db.refresh(asgmt)
        result = {
            "id":               asgmt.id,
            "report_id":        asgmt.report_id,
            "user_id":          asgmt.user_id,
            "assignment_date":  asgmt.assignment_date
        }
        return JSONResponse(status_code=200, content=jsonable_encoder({"success": True, "data": result}))
