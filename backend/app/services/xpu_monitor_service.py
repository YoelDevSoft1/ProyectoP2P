"""
Servicio para monitorear GPU Intel Arc usando Intel XPU Manager.
Este servicio se conecta a XPU Manager (si está disponible) para obtener métricas de la GPU.
"""
import logging
import os
from typing import Optional, Dict, Any
import requests
from requests.exceptions import RequestException, ConnectionError, Timeout

logger = logging.getLogger(__name__)

# URL por defecto de XPU Manager (si está corriendo en el host o contenedor)
XPU_MANAGER_URL = os.getenv("XPU_MANAGER_URL", "http://xpu-manager:12788")


class XPUMonitorService:
    """
    Servicio para monitorear GPU Intel Arc usando Intel XPU Manager.
    """
    
    def __init__(self, base_url: str = XPU_MANAGER_URL):
        """
        Inicializa el servicio de monitoreo XPU.
        
        Args:
            base_url: URL base de XPU Manager
        """
        self.base_url = base_url.rstrip('/')
        self.available = False
        self._check_availability()
    
    def _check_availability(self):
        """
        Verifica si XPU Manager está disponible.
        """
        try:
            response = requests.get(
                f"{self.base_url}/api/v1/health",
                timeout=5
            )
            if response.status_code == 200:
                self.available = True
                logger.info("Intel XPU Manager está disponible")
            else:
                logger.warning(f"XPU Manager respondió con código {response.status_code}")
        except (ConnectionError, Timeout, RequestException) as e:
            logger.debug(f"XPU Manager no está disponible: {e}")
            self.available = False
    
    def get_gpu_list(self) -> Optional[Dict[str, Any]]:
        """
        Obtiene la lista de GPUs disponibles.
        
        Returns:
            Dict con información de GPUs o None si no está disponible
        """
        if not self.available:
            return None
        
        try:
            response = requests.get(
                f"{self.base_url}/api/v1/xpum/device",
                timeout=10
            )
            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"Error al obtener lista de GPUs: {response.status_code}")
                return None
        except (ConnectionError, Timeout, RequestException) as e:
            logger.error(f"Error al conectar con XPU Manager: {e}")
            return None
    
    def get_gpu_health(self, device_id: int = 0) -> Optional[Dict[str, Any]]:
        """
        Obtiene el estado de salud de una GPU específica.
        
        Args:
            device_id: ID del dispositivo GPU
            
        Returns:
            Dict con información de salud o None si no está disponible
        """
        if not self.available:
            return None
        
        try:
            response = requests.get(
                f"{self.base_url}/api/v1/xpum/device/{device_id}/health",
                timeout=10
            )
            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"Error al obtener salud de GPU {device_id}: {response.status_code}")
                return None
        except (ConnectionError, Timeout, RequestException) as e:
            logger.error(f"Error al conectar con XPU Manager: {e}")
            return None
    
    def get_gpu_metrics(self, device_id: int = 0) -> Optional[Dict[str, Any]]:
        """
        Obtiene métricas de telemetría de una GPU específica.
        
        Args:
            device_id: ID del dispositivo GPU
            
        Returns:
            Dict con métricas (temperatura, uso, memoria, etc.) o None si no está disponible
        """
        if not self.available:
            return None
        
        try:
            response = requests.get(
                f"{self.base_url}/api/v1/xpum/device/{device_id}/metrics",
                timeout=10
            )
            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"Error al obtener métricas de GPU {device_id}: {response.status_code}")
                return None
        except (ConnectionError, Timeout, RequestException) as e:
            logger.error(f"Error al conectar con XPU Manager: {e}")
            return None
    
    def get_gpu_info(self) -> Dict[str, Any]:
        """
        Obtiene información completa de la GPU (si está disponible).
        
        Returns:
            Dict con información de GPU
        """
        info = {
            "available": self.available,
            "xpu_manager_url": self.base_url,
            "gpus": []
        }
        
        if not self.available:
            return info
        
        # Obtener lista de GPUs
        gpu_list = self.get_gpu_list()
        if gpu_list and "devices" in gpu_list:
            for device in gpu_list["devices"]:
                device_id = device.get("device_id", 0)
                device_info = {
                    "device_id": device_id,
                    "device_name": device.get("device_name", "Unknown"),
                    "health": self.get_gpu_health(device_id),
                    "metrics": self.get_gpu_metrics(device_id)
                }
                info["gpus"].append(device_info)
        
        return info


# Instancia global del servicio
_xpu_monitor_service: Optional[XPUMonitorService] = None


def get_xpu_monitor_service() -> XPUMonitorService:
    """
    Obtiene la instancia global del servicio de monitoreo XPU.
    
    Returns:
        Instancia de XPUMonitorService
    """
    global _xpu_monitor_service
    if _xpu_monitor_service is None:
        _xpu_monitor_service = XPUMonitorService()
    return _xpu_monitor_service

