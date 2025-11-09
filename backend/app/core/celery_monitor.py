"""
Monitoreo y health checks para Celery.
"""
from celery.result import AsyncResult
from typing import Optional, Dict, Any
import structlog
from datetime import datetime

from app.core.metrics import metrics, celery_tasks_active

logger = structlog.get_logger()


class CeleryMonitor:
    """
    Monitor para verificar estado de Celery workers y tasks.
    """

    def __init__(self):
        self._last_check: Optional[datetime] = None
        self._celery_app = None

    def _get_celery_app(self):
        """Lazy load de la app de Celery para evitar imports circulares"""
        if self._celery_app is None:
            try:
                from celery_app.worker import celery_app
                self._celery_app = celery_app
            except Exception as e:
                logger.warning("Failed to import celery_app", error=str(e))
                # Fallback a current_app si no se puede importar
                from celery import current_app
                self._celery_app = current_app
        return self._celery_app

    def check_health(self) -> dict:
        """
        Verificar salud de Celery.

        Returns:
            dict con información del estado de Celery
        """
        try:
            # Obtener inspect para workers activos
            app = self._get_celery_app()
            inspect = app.control.inspect(timeout=2.0)
            
            # Verificar workers activos (sin timeout, la API de Celery lo maneja internamente)
            active_workers = inspect.active() or {}
            registered_tasks = inspect.registered() or {}
            stats = inspect.stats() or {}
            
            # Contar workers
            worker_count = len(active_workers)
            
            # Contar tasks activas
            active_tasks = sum(len(tasks) for tasks in active_workers.values())
            
            # Obtener información de colas
            active_queues = inspect.active_queues() or {}
            queue_count = len(active_queues)
            
            self._last_check = datetime.utcnow()
            
            # Actualizar métricas
            for worker_name, tasks in active_workers.items():
                for task in tasks:
                    task_name = task.get("name", "unknown")
                    celery_tasks_active.labels(task_name=task_name).set(1)
            
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
            app = self._get_celery_app()
            result = AsyncResult(task_id, app=app)
            
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

