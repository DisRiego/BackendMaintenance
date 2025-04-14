from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Union
from datetime import datetime, date

# Esquemas básicos
class StatusBase(BaseModel):
    id: int
    name: str
    
    class Config:
        from_attributes = True

class FailureTypeBase(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    
    class Config:
        from_attributes = True

class DeviceBase(BaseModel):
    id: int
    serial_number: Optional[int] = None
    model: Optional[str] = None
    
    class Config:
        from_attributes = True

class UserBase(BaseModel):
    id: int
    name: str
    first_last_name: str
    second_last_name: Optional[str] = None
    email: str
    
    class Config:
        from_attributes = True

class SolutionBase(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    
    class Config:
        from_attributes = True

# Esquemas para mantenimientos
class MaintenanceDetailBase(BaseModel):
    id: int
    fault_remarks: Optional[str] = None
    evidence_failure: Optional[str] = None
    solution_remarks: Optional[str] = None
    evidence_solution: Optional[str] = None
    solution: Optional[SolutionBase] = None
    
    class Config:
        from_attributes = True

class TechnicianAssignmentBase(BaseModel):
    id: int
    assignment_date: Optional[datetime] = None
    user: UserBase
    details: Optional[List[MaintenanceDetailBase]] = None
    
    class Config:
        from_attributes = True

class MaintenanceBase(BaseModel):
    id: int
    device: DeviceBase
    failure_type: FailureTypeBase
    description_failure: Optional[str] = None
    date: Optional[str] = None  # Usando str en lugar de date para evitar errores
    status: StatusBase
    
    class Config:
        from_attributes = True

class MaintenanceDetailResponseModel(BaseModel):
    id: int
    device: DeviceBase
    failure_type: FailureTypeBase
    description_failure: Optional[str] = None
    date: Optional[str] = None  # Usando str en lugar de date para evitar errores
    status: StatusBase
    technician_assignments: List[TechnicianAssignmentBase]
    
    class Config:
        from_attributes = True

class StatusCount(BaseModel):
    status_id: int
    status_name: str
    count: int
    
    class Config:
        from_attributes = True

class MaintenanceStatistics(BaseModel):
    total: int
    by_status: List[StatusCount]
    
    class Config:
        from_attributes = True

# Esquemas para respuestas
class MaintenanceListResponse(BaseModel):
    total: int
    page: int
    limit: int
    total_pages: int
    maintenances: List[Dict[str, Any]]
    
    class Config:
        from_attributes = True

class StatusListResponse(BaseModel):
    data: List[Dict[str, Any]]
    
    class Config:
        from_attributes = True

class FailureTypeListResponse(BaseModel):
    data: List[Dict[str, Any]]
    
    class Config:
        from_attributes = True

# Esquemas para validación de parámetros
class PaginationParams(BaseModel):
    page: int = Field(1, ge=1, description="Número de página")
    limit: int = Field(10, ge=1, le=100, description="Elementos por página")

class StatusFilterParams(BaseModel):
    status_id: Optional[int] = Field(None, description="ID del estado para filtrar")