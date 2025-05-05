# app/maintenance/routes.py
from datetime import datetime
from fastapi import APIRouter, Depends, Body, Form, File, UploadFile
from typing import List, Dict, Any
from sqlalchemy.orm import Session

from app.database import get_db
from app.maintenance.services import MaintenanceService
from app.maintenance.schemas import (
    MaintenanceCreate,
    MaintenanceReportCreate,
    MaintenanceReportResponse,
    MaintenanceDetailCreate,
    MaintenanceDetailResponse,
    FailureSolutionSchema,
    TypeFailureSchema,
    ReportDetailSchema,
    MaintenanceReportAssign,
    MaintenanceDetailUpdate,
    MaintenanceReportUpdate,
    MaintenanceTypeSchema,
    MaintenanceUpdate,
    AssignmentUpdate
    
)

router = APIRouter(prefix="/maintenance", tags=["Maintenance"])

@router.get("/", response_model=Dict)
def get_maintenances(db: Session = Depends(get_db)) -> Any:
    """Obtener todos los mantenimientos (tabla maintenance)."""
    return MaintenanceService(db).get_maintenances()

@router.get("/maintenance-types", response_model=List[MaintenanceTypeSchema])
def list_maintenance_types(db: Session = Depends(get_db)):
    return MaintenanceService(db).get_maintenance_types()


@router.post("/", response_model=Dict)
def create_maintenance(
    report: MaintenanceCreate,
    db:     Session = Depends(get_db)
) -> Any:
    """Crear un nuevo mantenimiento (tabla maintenance)."""
    return MaintenanceService(db).create_maintenance(report)

@router.post(
    "/{maintenance_id}/assign",
    response_model=Dict
)
def assign_maintenance(
    maintenance_id: int,
    user_id:        int = Body(..., embed=True, description="ID del técnico a asignar"),
    assignment_date:datetime = Body(..., embed=True, description="Fecha de asignación (ISO)"),
    db:             Session = Depends(get_db)
) -> Any:
    """Asignar técnico a un mantenimiento existente."""
    return MaintenanceService(db).assign_technician(maintenance_id, user_id, assignment_date)

@router.get("/reports", response_model=List[MaintenanceReportResponse])
def get_reports(db: Session = Depends(get_db)) -> Any:
    """Obtener todos los reportes por lote (tabla maintenance_report)."""
    return MaintenanceService(db).get_reports()

@router.post(
    "/reports",
    response_model=MaintenanceReportResponse
)
def create_report(
    report: MaintenanceReportCreate,
    db:     Session = Depends(get_db)
) -> Any:
    """Crear un nuevo reporte por lote."""
    return MaintenanceService(db).create_report(report)

@router.post("/reports/{report_id}/assign", response_model=Dict)
def assign_report(report_id: int, assign: MaintenanceReportAssign = Body(...), db: Session = Depends(get_db)) -> Any:
    return MaintenanceService(db).assign_report_technician(report_id, assign.user_id)

@router.get("/technicians/permission", response_model=Dict)
def get_technicians(db: Session = Depends(get_db)) -> Any:
    """Obtener todos los usuarios con permiso 80 (técnicos)."""
    return MaintenanceService(db).get_users_with_permission()

@router.get("/assigned/{technician_id}/maintenances", response_model=Dict[str, Any])
def get_assigned_maintenances(
    technician_id: int,
    db:             Session = Depends(get_db)
) -> Any:
    return MaintenanceService(db).get_assigned_maintenances_for_technician(technician_id)

@router.get("/assigned/{technician_id}/reports", response_model=Dict[str, Any])
def get_assigned_reports(
    technician_id: int,
    db:             Session = Depends(get_db)
) -> Any:
    return MaintenanceService(db).get_assigned_reports_for_technician(technician_id)

@router.post(
    "/finalize",
    response_model=MaintenanceDetailResponse
)
async def finalize_assignment(
    technician_assignment_id: int        = Form(..., description="ID de la asignación"),
    fault_remarks:            str        = Form(..., description="Observaciones del fallo"),
    type_failure_id:          int        = Form(..., description="ID del tipo de fallo"),
    type_maintenance_id:      int        = Form(..., description="ID del tipo de mantenimiento aplicado"),
    failure_solution_id:      int        = Form(..., description="ID de la solución aplicada"),
    solution_remarks:         str        = Form(..., description="Observaciones de la solución"),
    evidence_failure:         UploadFile = File(..., description="Imagen de evidencia del fallo"),
    evidence_solution:        UploadFile = File(..., description="Imagen de evidencia de la solución"),
    db:                       Session    = Depends(get_db)
) -> Any:
    """
    Finalizar un mantenimiento o reporte asignado:
      - Sube evidencias a Firebase
      - Crea registro en maintenance_detail
      - Cambia el estado a 25 (Finalizado)
    """
    svc = MaintenanceService(db)

    detail_in = MaintenanceDetailCreate(
        technician_assignment_id = technician_assignment_id,
        fault_remarks            = fault_remarks,
        type_failure_id          = type_failure_id,
        type_maintenance_id      = type_maintenance_id,  # <- int
        failure_solution_id      = failure_solution_id,
        solution_remarks         = solution_remarks
    )

    return await svc.finalize_assignment(detail_in, evidence_failure, evidence_solution)



@router.get("/failure-solutions", response_model=List[FailureSolutionSchema])
def list_failure_solutions(db: Session = Depends(get_db)) -> Any:
    """Obtener todos los tipos de solución."""
    return MaintenanceService(db).get_failure_solutions()

@router.get("/failure-solutions/by-maintenance-type/{maintenance_type_id}", response_model=List[FailureSolutionSchema])
def list_failure_solutions_by_maintenance_type(
    maintenance_type_id: int,
    db: Session = Depends(get_db)
) -> Any:
    """Obtener soluciones filtradas por tipo de mantenimiento (correctivo o preventivo)."""
    return MaintenanceService(db).get_failure_solutions_by_maintenance_type(maintenance_type_id)

@router.get("/failure-types", response_model=List[TypeFailureSchema])
def list_failure_types(db: Session = Depends(get_db)) -> Any:
    """Obtener todos los tipos de fallo."""
    return MaintenanceService(db).get_failure_types()

@router.get(
    "/reports/{report_id}/detail",
    response_model=ReportDetailSchema
)
def report_detail(
    report_id: int,
    db:        Session = Depends(get_db)
) -> Any:
    """
    Obtener información completa de un reporte por lote,
    incluyendo asignación y datos de finalización.
    """
    return MaintenanceService(db).get_report_detail(report_id)


@router.get(
    "/{maintenance_id}/detail",
    response_model=ReportDetailSchema
)
def maintenance_detail(
    maintenance_id: int,
    db:             Session = Depends(get_db)
) -> Any:
    """
    Obtener información completa de un mantenimiento IoT,
    incluyendo asignación y datos de finalización.
    """
    return MaintenanceService(db).get_maintenance_detail(maintenance_id)


@router.get(
    "/user/{user_id}/maintenances",
    response_model=Dict[str, Any]
)
def get_user_maintenances(
    user_id: int,
    db:      Session = Depends(get_db)
) -> Any:
    """
    GET /maintenance/user/{user_id}/maintenances
    Obtiene todos los mantenimientos IoT creados en predios del usuario.
    """
    return MaintenanceService(db).get_maintenances_by_user(user_id)

@router.get(
    "/user/{user_id}/reports",
    response_model=Dict[str, Any]
)
def get_user_reports(
    user_id: int,
    db:      Session = Depends(get_db)
) -> Any:
    """
    GET /maintenance/user/{user_id}/reports
    Obtiene todos los reportes por lote creados en predios del usuario.
    """
    return MaintenanceService(db).get_reports_by_user(user_id)



@router.put("/reports/{report_id}", response_model=Dict)
def edit_report(
    report_id: int,
    body:      MaintenanceReportUpdate,
    db:        Session = Depends(get_db)
) -> Any:
    return MaintenanceService(db).update_report(report_id, body)

@router.put(
    "/finalize/{detail_id}",
    response_model=MaintenanceDetailResponse
)
async def edit_finalization(
    detail_id:            int,
    fault_remarks:        str        = Form(..., description="Observaciones del fallo"),
    type_failure_id:      int        = Form(..., description="ID del tipo de fallo detectado"),
    type_maintenance_id:  int        = Form(..., description="ID del tipo de mantenimiento aplicado"),
    failure_solution_id:  int        = Form(..., description="ID de la solución aplicada"),
    solution_remarks:     str        = Form(..., description="Observaciones de la solución"),
    evidence_failure:     UploadFile | None = File(None, description="Imagen de evidencia del fallo"),
    evidence_solution:    UploadFile | None = File(None, description="Imagen de evidencia de la solución"),
    db:                   Session    = Depends(get_db)
) -> Any:
    """
    Permite modificar un registro de maintenance_detail usando 
    los mismos campos que la creación de finalize.
    """
    svc = MaintenanceService(db)
    update_data = MaintenanceDetailUpdate(
        fault_remarks       = fault_remarks,
        type_failure_id     = type_failure_id,
        type_maintenance_id = type_maintenance_id,
        failure_solution_id = failure_solution_id,
        solution_remarks    = solution_remarks
    )
    return await svc.update_finalization(
        detail_id,
        update_data,
        evidence_failure,
        evidence_solution
    )

# ——— EDIT REPORT ———

@router.put("/reports/{report_id}", response_model=Dict)
def edit_report(
    report_id: int,
    body:      MaintenanceReportUpdate,
    db:        Session = Depends(get_db)
) -> Any:
    return MaintenanceService(db).update_report(report_id, body)

@router.put("/reports/{report_id}/assign", response_model=Dict)
def edit_report_assignment(
    report_id: int,
    assign:    AssignmentUpdate = Body(...),
    db:        Session        = Depends(get_db)
) -> Any:
    return MaintenanceService(db).update_report_assignment(
        report_id,
        assign.user_id,
        assign.assignment_date
    )

@router.put("/reports/finalize/{detail_id}", response_model=Dict)
async def edit_report_finalization(
    detail_id:           int,
    body:                MaintenanceDetailUpdate = Depends(),
    evidence_failure:    UploadFile | None      = File(None),
    evidence_solution:   UploadFile | None      = File(None),
    db:                  Session                 = Depends(get_db)
) -> Any:
    return await MaintenanceService(db).update_finalization(
        detail_id,
        body,
        evidence_failure,
        evidence_solution
    )


# ——— EDIT MAINTENANCE ———

@router.put("/{maintenance_id}", response_model=Dict)
def edit_maintenance(
    maintenance_id: int,
    body:           MaintenanceUpdate,
    db:             Session           = Depends(get_db)
) -> Any:
    return MaintenanceService(db).update_maintenance(maintenance_id, body)

@router.put("/{maintenance_id}/assign", response_model=Dict)
def edit_maintenance_assignment(
    maintenance_id: int,
    assign:         AssignmentUpdate = Body(...),
    db:              Session           = Depends(get_db)
) -> Any:
    return MaintenanceService(db).update_maintenance_assignment(
        maintenance_id,
        assign.user_id,
        assign.assignment_date
    )

@router.put("/{maintenance_id}/finalize/{detail_id}", response_model=Dict)
async def edit_maintenance_finalization(
    maintenance_id:      int,
    detail_id:           int,
    body:                MaintenanceDetailUpdate = Depends(),
    evidence_failure:    UploadFile | None        = File(None),
    evidence_solution:   UploadFile | None        = File(None),
    db:                  Session                 = Depends(get_db)
) -> Any:
    return await MaintenanceService(db).update_finalization(
        detail_id,
        body,
        evidence_failure,
        evidence_solution
    )