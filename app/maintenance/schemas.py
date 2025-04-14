from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List, Union
from datetime import datetime, date as DateType

# Esquemas para visualizar
class MaintenanceStatusSchema(BaseModel):
    id: int
    name: str
    
    class Config:
        from_attributes = True

class TypeFailureSchema(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    
    class Config:
        from_attributes = True

class FailureSolutionSchema(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    
    class Config:
        from_attributes = True

class UserSchema(BaseModel):
    id: int
    name: Optional[str] = None
    first_last_name: Optional[str] = None
    second_last_name: Optional[str] = None
    document_number: Optional[int] = None
    email: Optional[str] = None
    
    class Config:
        from_attributes = True

class LotSchema(BaseModel):
    id: int
    name: Optional[str] = None
    
    class Config:
        from_attributes = True

class PropertySchema(BaseModel):
    id: int
    name: Optional[str] = None
    
    class Config:
        from_attributes = True

class DeviceIotSchema(BaseModel):
    id: int
    serial_number: Optional[int] = None
    model: Optional[str] = None
    
    class Config:
        from_attributes = True

# Esquemas para la creación de mantenimientos
class TechnicianAssignmentCreate(BaseModel):
    user_id: int
    assignment_date: Optional[datetime] = None
    
class MaintenanceCreate(BaseModel):
    device_iot_id: int
    type_failure_id: int
    description_failure: str
    date: Optional[DateType] = None
    maintenance_status_id: int
    
class MaintenanceAssignCreate(BaseModel):
    property_id: int
    lot_id: int
    technician_id: int
    revision_date: DateType
    revision_time: str
    
# Esquemas para la actualización de mantenimientos
class MaintenanceUpdate(BaseModel):
    device_iot_id: Optional[int] = None
    type_failure_id: Optional[int] = None
    description_failure: Optional[str] = None
    date: Optional[DateType] = None
    maintenance_status_id: Optional[int] = None
    
class TechnicianAssignmentUpdate(BaseModel):
    user_id: Optional[int] = None
    assignment_date: Optional[datetime] = None
    
class MaintenanceAssignUpdate(BaseModel):
    property_id: Optional[int] = None
    lot_id: Optional[int] = None
    technician_id: Optional[int] = None
    revision_date: Optional[DateType] = None
    revision_time: Optional[str] = None
    
# Esquemas para las respuestas
class MaintenanceResponse(BaseModel):
    id: int
    device_iot_id: Optional[int] = None
    type_failure_id: Optional[int] = None
    description_failure: Optional[str] = None
    date: Optional[DateType] = None
    maintenance_status_id: Optional[int] = None
    device: Optional[DeviceIotSchema] = None
    type_failure: Optional[TypeFailureSchema] = None
    status: Optional[MaintenanceStatusSchema] = None
    
    class Config:
        from_attributes = True

class TechnicianAssignmentResponse(BaseModel):
    id: int
    maintenance_id: int
    user_id: int
    assignment_date: Optional[datetime] = None
    technician: Optional[UserSchema] = None
    maintenance: Optional[MaintenanceResponse] = None
    
    class Config:
        from_attributes = True

class MaintenanceDetailResponse(BaseModel):
    id: int
    technician_assignment_id: Optional[int] = None
    fault_remarks: Optional[str] = None
    evidence_failure: Optional[str] = None
    failure_solution_id: Optional[int] = None
    solution_remarks: Optional[str] = None
    evidence_solution: Optional[str] = None
    assignment: Optional[TechnicianAssignmentResponse] = None
    solution: Optional[FailureSolutionSchema] = None
    
    class Config:
        from_attributes = True

class MaintenanceReportResponse(BaseModel):
    id: int
    property_id: Optional[int] = None
    lot_id: Optional[int] = None
    document_number: Optional[int] = None
    device_type: Optional[str] = None
    failure_type: Optional[str] = None
    description: Optional[str] = None
    report_date: Optional[DateType] = None
    status: Optional[str] = None
    technician_name: Optional[str] = None
    property_name: Optional[str] = None
    lot_name: Optional[str] = None
    
    class Config:
        from_attributes = True

# Esquema para la respuesta general
class ResponseModel(BaseModel):
    success: bool
    data: Any
    errors: Optional[List[Dict[str, Any]]] = None
