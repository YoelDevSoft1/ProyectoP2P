"""
Monitoreo y health checks para Celery.
"""
from celery import current_app
from celery.result import AsyncResult
from typing import Optional, Dict, Any
import structlog
from datetime import datetime

from app.core.metrics import metrics

logger = structlog.get_logger()


class CeleryMonitor:
    """
    Monitor para verificar estado de Celery workers y tasks.
    """
    
    def __init__(self):
        self._last_check: Optional[datetime] = None
    
    def check_health(self) -> dict:
        """
        Verificar salud de Celery.
        
        Returns:
            dict con información del estado de Celery
        """
        try:
            # Obtener inspect para workers activos
            inspect = current_app.control.inspect()
            
            # Verificar workers activos (con timeout)
            active_workers = inspect.active(timeout=5) or {}
            registered_tasks = inspect.registered(timeout=5) or {}
            stats = inspect.stats(timeout=5) or {}
            
            # Contar workers
            worker_count = len(active_workers)
            
            # Contar tasks activas
            active_tasks = sum(len(tasks) for tasks in active_workers.values())
            
            # Obtener información de colas
            active_queues = inspect.active_queues(timeout=5) or {}
            queue_count = len(active_queues)
            
            self._last_check = datetime.utcnow()
            
            # Actualizar métricas
            for worker_name, tasks in active_workers.items():
                for task in tasks:
                    task_name = task.get("name", "unknown")
                    metrics.celery_tasks_active.labels(task_name=task_name).set(1)
            
            return {
                "status": "healthy" if worker_count > 0 else "degraded",
                "worker_count": worker_count,
                "active_tasks": active_tasks,
                "queue_count": queue_count,
                "workers": list(active_workers.keys()),
                "registered_tasks_count": sum(len(tasks) for tasks in registered_tasks.values()),
                "checked_at": self._last_check.isoformat(),
            }
            
        except Exception as e:
            logger.error("Celery health check failed", error=str(e))
            self._last_check = datetime.utcnow()
            
            return {
                "status": "unhealthy",
                "error": str(e),
                "checked_at": self._last_check.isoformat(),
            }
    
    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """
        Obtener estado de una tarea específica.
        
        Args:
            task_id: ID de la tarea
            
        Returns:
            dict con información de la tarea
        """
        try:
            result = AsyncResult(task_id, app=current_app)
            
            return {
                "task_id": task_id,
                "status": result.status,
                "result": result.result if result.ready() else None,
                "traceback": result.traceback if result.failed() else None,
            }
            
        except Exception as e:
            logger.error("Failed to get task status", task_id=task_id, error=str(e))
            return {
                "task_id": task_id,
                "status": "UNKNOWN",
                "error": str(e),
            }
    
    @property
    def last_check(self) -> Optional[datetime]:
        """Obtener última verificación"""
        return self._last_check


# Instancia global
celery_monitor = CeleryMonitor()

