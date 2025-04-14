from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import text, func
from fastapi import HTTPException
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder

class MaintenanceService:
    def __init__(self, db: Session):
        self.db = db
    
    def get_maintenances(self, status_id: Optional[int] = None, page: int = 1, limit: int = 10):
        """Obtener listado de mantenimientos con posibilidad de filtrar por estado"""
        try:
            # Construir la parte de la consulta SQL para el filtro de estado
            status_filter = ""
            params = {"limit": limit, "offset": (page - 1) * limit}
            
            if status_id is not None:
                status_filter = "WHERE m.maintenance_status_id = :status_id"
                params["status_id"] = status_id
            
            # Consulta SQL para obtener mantenimientos
            query = text(f"""
                SELECT m.id, m.device_iot_id, m.type_failure_id, m.description_failure, 
                       m.date, m.maintenance_status_id, ms.name as status_name,
                       d.serial_number, d.model, tf.name as failure_type_name
                FROM maintenance m
                LEFT JOIN maintenance_status ms ON m.maintenance_status_id = ms.id
                LEFT JOIN device_iot d ON m.device_iot_id = d.id
                LEFT JOIN type_failure tf ON m.type_failure_id = tf.id
                {status_filter}
                ORDER BY m.id DESC
                LIMIT :limit OFFSET :offset
            """)
            
            # Ejecutar consulta con parámetros
            result = self.db.execute(query, params).fetchall()
            
            # Consulta para obtener el total de registros (para paginación)
            count_query = text(f"""
                SELECT COUNT(*) as total
                FROM maintenance m
                {status_filter}
            """)
            
            total = self.db.execute(count_query, params).scalar()
            
            if not result:
                return JSONResponse(
                    status_code=404,
                    content={
                        "success": False,
                        "data": {
                            "title": "Mantenimientos",
                            "message": "No se encontraron mantenimientos con los criterios especificados."
                        }
                    }
                )
            
            # Transformar resultado a formato JSON
            maintenances = []
            for row in result:
                maintenances.append({
                    "id": row.id,
                    "device": {
                        "id": row.device_iot_id,
                        "serial_number": row.serial_number,
                        "model": row.model
                    },
                    "failure_type": {
                        "id": row.type_failure_id,
                        "name": row.failure_type_name
                    },
                    "description_failure": row.description_failure,
                    "date": row.date.isoformat() if row.date else None,
                    "status": {
                        "id": row.maintenance_status_id,
                        "name": row.status_name
                    }
                })
            
            # Formato para respuesta
            maintenance_data = {
                "total": total,
                "page": page,
                "limit": limit,
                "total_pages": (total + limit - 1) // limit,
                "maintenances": maintenances
            }
            
            return JSONResponse(
                status_code=200,
                content={"success": True, "data": maintenance_data}
            )
        except Exception as e:
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "data": {
                        "title": "Error al obtener mantenimientos",
                        "message": f"Ocurrió un error: {str(e)}"
                    }
                }
            )
    
    def get_maintenance_by_id(self, maintenance_id: int):
        """Obtener detalle de un mantenimiento específico por ID"""
        try:
            # Consulta principal para obtener datos del mantenimiento
            query = text("""
                SELECT m.id, m.device_iot_id, m.type_failure_id, m.description_failure, 
                       m.date, m.maintenance_status_id, ms.name as status_name,
                       d.serial_number, d.model, tf.name as failure_type_name
                FROM maintenance m
                LEFT JOIN maintenance_status ms ON m.maintenance_status_id = ms.id
                LEFT JOIN device_iot d ON m.device_iot_id = d.id
                LEFT JOIN type_failure tf ON m.type_failure_id = tf.id
                WHERE m.id = :maintenance_id
            """)
            
            maintenance = self.db.execute(query, {"maintenance_id": maintenance_id}).first()
            
            if not maintenance:
                return JSONResponse(
                    status_code=404,
                    content={
                        "success": False,
                        "data": {
                            "title": "Mantenimiento",
                            "message": f"No se encontró el mantenimiento con ID {maintenance_id}."
                        }
                    }
                )
            
            # Consulta para obtener asignaciones de técnicos
            technicians_query = text("""
                SELECT ta.id, ta.assignment_date, u.id as user_id, u.name, 
                       u.first_last_name, u.second_last_name, u.email
                FROM technician_assignment ta
                JOIN users u ON ta.user_id = u.id
                WHERE ta.maintenance_id = :maintenance_id
            """)
            
            technicians = self.db.execute(technicians_query, {"maintenance_id": maintenance_id}).fetchall()
            
            # Construir datos de técnicos asignados
            technician_data = []
            for tech in technicians:
                # Consulta para obtener detalles del mantenimiento
                details_query = text("""
                    SELECT md.id, md.fault_remarks, md.evidence_failure, 
                           md.failure_solution_id, fs.name as solution_name,
                           fs.description as solution_description,
                           md.solution_remarks, md.evidence_solution
                    FROM maintenance_detail md
                    LEFT JOIN failure_solution fs ON md.failure_solution_id = fs.id
                    WHERE md.technician_assignment_id = :assignment_id
                """)
                
                details = self.db.execute(details_query, {"assignment_id": tech.id}).fetchall()
                
                # Construir datos de detalles
                detail_data = []
                for detail in details:
                    detail_data.append({
                        "id": detail.id,
                        "fault_remarks": detail.fault_remarks,
                        "evidence_failure": detail.evidence_failure,
                        "solution_remarks": detail.solution_remarks,
                        "evidence_solution": detail.evidence_solution,
                        "solution": {
                            "id": detail.failure_solution_id,
                            "name": detail.solution_name,
                            "description": detail.solution_description
                        } if detail.failure_solution_id else None
                    })
                
                technician_data.append({
                    "id": tech.id,
                    "assignment_date": tech.assignment_date.isoformat() if tech.assignment_date else None,
                    "user": {
                        "id": tech.user_id,
                        "name": tech.name,
                        "first_last_name": tech.first_last_name,
                        "second_last_name": tech.second_last_name,
                        "email": tech.email
                    },
                    "details": detail_data
                })
            
            # Construir respuesta detallada
            maintenance_detail = {
                "id": maintenance.id,
                "device": {
                    "id": maintenance.device_iot_id,
                    "serial_number": maintenance.serial_number,
                    "model": maintenance.model
                },
                "failure_type": {
                    "id": maintenance.type_failure_id,
                    "name": maintenance.failure_type_name
                },
                "description_failure": maintenance.description_failure,
                "date": maintenance.date.isoformat() if maintenance.date else None,
                "status": {
                    "id": maintenance.maintenance_status_id,
                    "name": maintenance.status_name
                },
                "technician_assignments": technician_data
            }
            
            return JSONResponse(
                status_code=200,
                content={"success": True, "data": maintenance_detail}
            )
        except Exception as e:
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "data": {
                        "title": "Error al obtener detalle de mantenimiento",
                        "message": f"Ocurrió un error: {str(e)}"
                    }
                }
            )
    
    def get_maintenance_statistics(self):
        """Obtener estadísticas de mantenimientos por estado"""
        try:
            # Consulta para obtener conteo por estado
            query = text("""
                SELECT m.maintenance_status_id as status_id, ms.name as status_name, 
                       COUNT(m.id) as count
                FROM maintenance m
                JOIN maintenance_status ms ON m.maintenance_status_id = ms.id
                GROUP BY m.maintenance_status_id, ms.name
                ORDER BY m.maintenance_status_id
            """)
            
            status_counts = self.db.execute(query).fetchall()
            
            # Consulta para obtener total
            total_query = text("SELECT COUNT(*) as total FROM maintenance")
            total = self.db.execute(total_query).scalar()
            
            # Formato para respuesta
            status_data = []
            for item in status_counts:
                status_data.append({
                    "status_id": item.status_id,
                    "status_name": item.status_name,
                    "count": item.count
                })
            
            statistics = {
                "total": total,
                "by_status": status_data
            }
            
            return JSONResponse(
                status_code=200,
                content={"success": True, "data": statistics}
            )
        except Exception as e:
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "data": {
                        "title": "Error al obtener estadísticas de mantenimientos",
                        "message": f"Ocurrió un error: {str(e)}"
                    }
                }
            )
    
    def get_maintenance_status_list(self):
        """Obtener lista de estados de mantenimiento"""
        try:
            query = text("SELECT id, name FROM maintenance_status ORDER BY id")
            
            status_list = self.db.execute(query).fetchall()
            
            if not status_list:
                return JSONResponse(
                    status_code=404,
                    content={
                        "success": False,
                        "data": {
                            "title": "Estados de mantenimiento",
                            "message": "No se encontraron estados de mantenimiento."
                        }
                    }
                )
            
            # Transformar resultado a formato JSON
            statuses = []
            for row in status_list:
                statuses.append({
                    "id": row.id,
                    "name": row.name
                })
            
            return JSONResponse(
                status_code=200,
                content={"success": True, "data": statuses}
            )
        except Exception as e:
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "data": {
                        "title": "Error al obtener estados de mantenimiento",
                        "message": f"Ocurrió un error: {str(e)}"
                    }
                }
            )
    
    def get_failure_types(self):
        """Obtener lista de tipos de fallas"""
        try:
            query = text("SELECT id, name, description FROM type_failure ORDER BY id")
            
            failure_types = self.db.execute(query).fetchall()
            
            if not failure_types:
                return JSONResponse(
                    status_code=404,
                    content={
                        "success": False,
                        "data": {
                            "title": "Tipos de fallas",
                            "message": "No se encontraron tipos de fallas."
                        }
                    }
                )
            
            # Transformar resultado a formato JSON
            types = []
            for row in failure_types:
                types.append({
                    "id": row.id,
                    "name": row.name,
                    "description": row.description
                })
            
            return JSONResponse(
                status_code=200,
                content={"success": True, "data": types}
            )
        except Exception as e:
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "data": {
                        "title": "Error al obtener tipos de fallas",
                        "message": f"Ocurrió un error: {str(e)}"
                    }
                }
            )