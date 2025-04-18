from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime


class MaintenanceBase(BaseModel):
    device_iot_id:       int     = Field(..., description="ID del dispositivo IoT")
    type_failure_id:     int     = Field(..., description="ID del tipo de fallo")
    description_failure: str     = Field(..., description="Descripción del fallo")
    maintenance_status_id: int   = Field(..., description="ID del estado de mantenimiento")

class MaintenanceCreate(MaintenanceBase):
    date: datetime = Field(default_factory=datetime.now, description="Fecha del reporte")

class MaintenanceResponse(MaintenanceBase):
    id:   int
    date: datetime

    class Config:
        orm_mode = True



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




class MaintenanceReportBase(BaseModel):
    lot_id:               int
    type_failure_id:      int
    description_failure:  Optional[str]
    maintenance_status_id:int

class MaintenanceReportCreate(MaintenanceReportBase):
    date: datetime = Field(default_factory=datetime.now)

class MaintenanceReportResponse(BaseModel):
    id:                  int        = Field(..., description="ID del reporte")
    property_id:         int        = Field(..., description="ID del predio")
    lot_id:              int        = Field(..., description="ID del lote")
    owner_document:      str        = Field(..., description="Documento del dueño del predio")
    failure_type:        str        = Field(..., description="Tipo de fallo (texto)")
    description_failure: Optional[str] = Field(None, description="Descripción del fallo")
    date:                datetime   = Field(..., description="Fecha del reporte")
    status:              str        = Field(..., description="Estado (texto)")

    class Config:
        orm_mode = True