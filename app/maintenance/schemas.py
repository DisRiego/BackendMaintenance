from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class MaintenanceDetailResponseSchema(BaseModel):
    fecha_revision: datetime
    fecha_finalizacion: Optional[datetime]
    predio_nombre: str
    lote_nombre: str
    documento_usuario_reporto: str
    nombre_propietario: str
    fecha_reporte: datetime
    observaciones: Optional[str]
    nombre_tecnico_asignado: Optional[str]
    documento_tecnico_asignado: Optional[str]
    tipo_mantenimiento: Optional[str]
    fallo_detectado: Optional[str]
    observaciones_fallo: Optional[str]
    solucion: Optional[str]
    observaciones_solucion: Optional[str]
    evidencia_fallo: Optional[str]
    evidencia_solucion: Optional[str]

    class Config:
        orm_mode = True