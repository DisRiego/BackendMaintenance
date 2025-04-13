from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import text
from fastapi import HTTPException
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from app.maintenance.models import Vars

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