"""
Modelo para guardar configuración de la aplicación de forma persistente.
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean
from sqlalchemy.sql import func
import json

from app.core.database import Base


class AppConfig(Base):
    """Modelo para guardar configuración de la aplicación"""
    __tablename__ = "app_config"

    id = Column(Integer, primary_key=True, index=True)
    
    # Clave de configuración (ej: "trading.mode", "trading.profit_margin_cop")
    key = Column(String, unique=True, nullable=False, index=True)
    
    # Valor de configuración (guardado como JSON string para soportar diferentes tipos)
    value = Column(Text, nullable=False)
    
    # Tipo de dato (para parsing correcto)
    value_type = Column(String, nullable=False, default="str")  # str, int, float, bool, dict, list
    
    # Descripción de la configuración
    description = Column(Text, nullable=True)
    
    # Si la configuración es sensible (no se muestra en logs)
    is_sensitive = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<AppConfig {self.key}={self.value}>"
    
    def get_value(self):
        """Obtener el valor parseado según su tipo"""
        if self.value_type == "int":
            return int(self.value)
        elif self.value_type == "float":
            return float(self.value)
        elif self.value_type == "bool":
            return self.value.lower() in ("true", "1", "yes", "on")
        elif self.value_type == "dict":
            return json.loads(self.value)
        elif self.value_type == "list":
            return json.loads(self.value)
        else:
            return self.value
    
    def set_value(self, value):
        """Establecer el valor y determinar su tipo"""
        if isinstance(value, bool):
            self.value_type = "bool"
            self.value = str(value).lower()
        elif isinstance(value, int):
            self.value_type = "int"
            self.value = str(value)
        elif isinstance(value, float):
            self.value_type = "float"
            self.value = str(value)
        elif isinstance(value, dict):
            self.value_type = "dict"
            self.value = json.dumps(value)
        elif isinstance(value, list):
            self.value_type = "list"
            self.value = json.dumps(value)
        else:
            self.value_type = "str"
            self.value = str(value)

