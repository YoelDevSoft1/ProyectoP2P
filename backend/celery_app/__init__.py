"""
Inicialización de Celery app.
"""
from celery_app.worker import celery_app

__all__ = ["celery_app"]
