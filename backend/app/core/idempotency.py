"""
Idempotency Service

Asegura que operaciones críticas solo se ejecuten una vez, incluso si se reciben múltiples requests.
"""
from typing import Optional, Any, Callable
from datetime import datetime, timedelta
import asyncio
import hashlib
import json
import structlog

from app.core.database import get_redis

logger = structlog.get_logger()


class IdempotencyService:
    """
    Servicio de idempotencia para operaciones críticas.
    
    Usa Redis para almacenar resultados de operaciones idempotentes.
    """
    
    def __init__(self, ttl_seconds: int = 3600):
        """
        Inicializar servicio de idempotencia.
        
        Args:
            ttl_seconds: Tiempo de vida de las claves en Redis (default: 1 hora)
        """
        self.ttl_seconds = ttl_seconds
        self._redis = None
    
    async def _get_redis(self):
        """Obtener cliente Redis"""
        if self._redis is None:
            from app.core.database import redis_client
            self._redis = await redis_client.get_client()
        return self._redis
    
    def _generate_key(self, idempotency_key: str, operation: str) -> str:
        """
        Generar clave única para operación idempotente.
        
        Args:
            idempotency_key: Clave de idempotencia proporcionada por el cliente
            operation: Nombre de la operación
            
        Returns:
            Clave única
        """
        key_string = f"idempotency:{operation}:{idempotency_key}"
        return hashlib.sha256(key_string.encode()).hexdigest()
    
    async def execute(
        self,
        idempotency_key: str,
        operation: str,
        func: Callable,
        *args,
        **kwargs
    ) -> Any:
        """
        Ejecutar operación de forma idempotente.
        
        Args:
            idempotency_key: Clave única proporcionada por el cliente
            operation: Nombre de la operación
            func: Función a ejecutar
            *args: Argumentos posicionales
            **kwargs: Argumentos nombrados
            
        Returns:
            Resultado de la operación (puede ser de cache o ejecución)
        """
        redis = await self._get_redis()
        cache_key = self._generate_key(idempotency_key, operation)
        
        # Verificar si ya existe resultado
        cached_result = await redis.get(cache_key)
        if cached_result:
            logger.info(
                "Idempotency cache hit",
                operation=operation,
                idempotency_key=idempotency_key
            )
            return json.loads(cached_result)
        
        # Verificar si hay una operación en progreso
        lock_key = f"{cache_key}:lock"
        lock_acquired = await redis.set(
            lock_key,
            "1",
            nx=True,
            ex=300  # 5 minutos timeout
        )
        
        if not lock_acquired:
            # Operación en progreso, esperar y retry
            logger.info(
                "Operation in progress, waiting",
                operation=operation,
                idempotency_key=idempotency_key
            )
            await asyncio.sleep(0.5)
            # Retry obtener resultado
            cached_result = await redis.get(cache_key)
            if cached_result:
                return json.loads(cached_result)
            # Si aún no hay resultado, lanzar error
            raise Exception("Operation in progress, please retry later")
        
        try:
            # Ejecutar operación
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)
            
            # Guardar resultado
            result_json = json.dumps(result, default=str)
            await redis.setex(
                cache_key,
                self.ttl_seconds,
                result_json
            )
            
            logger.info(
                "Idempotency result cached",
                operation=operation,
                idempotency_key=idempotency_key
            )
            
            return result
            
        except Exception as e:
            # En caso de error, no cachear
            logger.error(
                "Idempotency operation failed",
                operation=operation,
                idempotency_key=idempotency_key,
                error=str(e)
            )
            raise
        finally:
            # Liberar lock
            await redis.delete(lock_key)
    
    async def clear(self, idempotency_key: str, operation: str):
        """
        Limpiar resultado cacheado (útil para testing).
        
        Args:
            idempotency_key: Clave de idempotencia
            operation: Nombre de la operación
        """
        redis = await self._get_redis()
        cache_key = self._generate_key(idempotency_key, operation)
        await redis.delete(cache_key)
        logger.info(
            "Idempotency cache cleared",
            operation=operation,
            idempotency_key=idempotency_key
        )


# Instancia global
idempotency_service = IdempotencyService()


# Helper para FastAPI
from fastapi import Header, HTTPException

async def get_idempotency_key(
    x_idempotency_key: Optional[str] = Header(None, alias="X-Idempotency-Key")
) -> str:
    """
    Dependency para obtener idempotency key del header.
    
    Usage:
        @router.post("/trades")
        async def create_trade(
            trade: TradeCreate,
            idempotency_key: str = Depends(get_idempotency_key)
        ):
            ...
    """
    if not x_idempotency_key:
        raise HTTPException(
            status_code=400,
            detail="X-Idempotency-Key header is required"
        )
    return x_idempotency_key

