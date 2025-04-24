from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

# --- MANTENIMIENTOS BÁSICOS ---

class MaintenanceBase(BaseModel):
    device_iot_id:       int    = Field(..., description="ID del dispositivo IoT")
    type_failure_id:     int    = Field(..., description="ID del tipo de fallo")
    description_failure: str   = Field(..., description="Descripción del fallo")
    maintenance_status_id: int = Field(..., description="ID del estado de mantenimiento")

class MaintenanceCreate(MaintenanceBase):
    date: datetime = Field(default_factory=datetime.now, description="Fecha del reporte")

class MaintenanceResponse(MaintenanceBase):
    id:   int
    date: datetime

    class Config:
        orm_mode = True

# --- REPORTE DETALLADO PARA MANTENIMIENTOS IoT ---

class MaintenanceReportDetailed(BaseModel):
    property_id:      int
    lot_id:           int
    owner_document:   str
    device_type:      str
    failure_type:     str
    technician_name:  Optional[str]
    date:             datetime
    status:           str

    class Config:
        orm_mode = True

# --- MANTENIMIENTO POR LOTE ---

class MaintenanceReportBase(BaseModel):
    lot_id:               int
    type_failure_id:      int
    description_failure:  Optional[str]
    maintenance_status_id:int

# --- MANTENIMIENTO POR LOTE: CREACIÓN ---

class MaintenanceReportCreate(BaseModel):
    lot_id:               int            = Field(..., description="ID del lote")
    type_failure_id:      int            = Field(..., description="ID del tipo de fallo")
    description_failure:  Optional[str]  = Field(None, description="Observaciones del fallo")

# --- ASIGNACIÓN DE REPORTE ---

class MaintenanceReportAssign(BaseModel):
    user_id:         int       = Field(..., description="ID del técnico a asignar")
    assignment_date: datetime = Field(..., description="Fecha de asignación (ISO)")

# --- RESPUESTA DE REPORTE POR LOTE ---

class MaintenanceReportResponse(BaseModel):
    id:                  int       = Field(..., description="ID del reporte")
    property_id:         int       = Field(..., description="ID del predio")
    lot_id:              int       = Field(..., description="ID del lote")
    owner_document:      str       = Field(..., description="Documento del dueño del predio")
    failure_type:        str       = Field(..., description="Tipo de fallo (texto)")
    description_failure: Optional[str] = Field(None, description="Descripción del fallo")
    date:                datetime  = Field(..., description="Fecha del reporte")
    status:              str       = Field(..., description="Estado (texto)")

    class Config:
        orm_mode = True

# --- FINALIZACIÓN DE MANTENIMIENTO ---

class MaintenanceDetailCreate(BaseModel):
    technician_assignment_id: int   = Field(..., description="ID de la asignación en technician_assignment")
    fault_remarks:            str   = Field(..., description="Observaciones del fallo")
    type_failure_id:          int   = Field(..., description="ID del tipo de fallo detectado")
    type_maintenance:         str   = Field(..., description="Correctivo o Preventivo")
    failure_solution_id:      int   = Field(..., description="ID de la solución aplicada")
    solution_remarks:         str   = Field(..., description="Observaciones de la solución")

class MaintenanceDetailResponse(BaseModel):
    id:                        int
    technician_assignment_id:  int
    fault_remarks:             Optional[str]
    evidence_failure_url:      Optional[str]
    type_failure_id:           int
    type_maintenance:          str
    failure_solution_id:       int
    solution_remarks:          Optional[str]
    evidence_solution_url:     Optional[str]
    date:                      datetime

    class Config:
        orm_mode = True

# --- CATÁLOGOS ---

class FailureSolutionSchema(BaseModel):
    id:          int            = Field(..., description="ID de la solución")
    name:        str            = Field(..., description="Nombre de la solución")
    description: Optional[str]  = Field(None, description="Descripción de la solución")

    class Config:
        orm_mode = True

class TypeFailureSchema(BaseModel):
    id:          int   = Field(..., description="ID del tipo de fallo")
    name:        str   = Field(..., description="Nombre del tipo de fallo")
    description: str   = Field(..., description="Descripción del tipo de fallo")

    class Config:
        orm_mode = True

# --- DETALLE COMPLETO DE REPORTE POR LOTE ---
class ReportDetailSchema(BaseModel):
    # Info base
    property_id:         int       = Field(..., description="ID del predio")
    property_name:       str       = Field(..., description="Nombre del predio")       # 🆕
    lot_id:              int       = Field(..., description="ID del lote")
    lot_name:            str       = Field(..., description="Nombre del lote")         # 🆕
    owner_document:      str       = Field(..., description="Documento del propietario")
    owner_name:          str       = Field(..., description="Nombre completo del propietario")
    report_date:         datetime  = Field(..., description="Fecha del reporte")
    failure_type:        str       = Field(..., description="Tipo de fallo")
    description_failure: Optional[str] = Field(None, description="Descripción del fallo")

    # Opcional: exponer también el estado actual
    status:              str       = Field(..., description="Estado del mantenimiento o reporte")  # 🆕

    # Asignación
    assignment_date:     Optional[datetime] = Field(None, description="Fecha de asignación")

    # Finalización
    finalized:           bool      = Field(..., description="Indica si está finalizado")
    finalization_date:   Optional[datetime] = Field(None, description="Fecha de finalización")

    # Detalle técnico (si finalizado)
    technician_name:     Optional[str]     = Field(None, description="Nombre del técnico")
    technician_document: Optional[str]     = Field(None, description="Documento del técnico")
    type_maintenance:    Optional[str]     = Field(None, description="Tipo de mantenimiento aplicado")
    fault_remarks:       Optional[str]     = Field(None, description="Observaciones del fallo detectado")
    solution_name:       Optional[str]     = Field(None, description="Nombre de la solución aplicada")
    solution_remarks:    Optional[str]     = Field(None, description="Observaciones de la solución")
    evidence_failure_url:  Optional[str]   = Field(None, description="URL de la evidencia del fallo")
    evidence_solution_url: Optional[str]   = Field(None, description="URL de la evidencia de la solución")

    class Config:
        orm_mode = True



class MaintenanceReportUpdate(BaseModel):
    type_failure_id:      Optional[int]
    description_failure:  Optional[str]
    maintenance_status_id:Optional[int]

class MaintenanceDetailUpdate(BaseModel):
    fault_remarks:       Optional[str]
    type_failure_id:     Optional[int]
    type_maintenance:    Optional[str]
    failure_solution_id: Optional[int]
    solution_remarks:    Optional[str]