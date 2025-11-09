"""
Retry Logic with Exponential Backoff

Implementa retry inteligente con exponential backoff para operaciones que pueden fallar temporalmente.
"""
from typing import Callable, Optional, Type, Tuple, Any
from datetime import datetime
import asyncio
import random
import structlog

logger = structlog.get_logger()


class RetryConfig:
    """Configuración para retry"""
    
    def __init__(
        self,
        max_attempts: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True,
        retryable_exceptions: Tuple[Type[Exception], ...] = (Exception,)
    ):
        self.max_attempts = max_attempts
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter
        self.retryable_exceptions = retryable_exceptions


class RetryHandler:
    """
    Manejador de retry con exponential backoff.
    """
    
    def __init__(self, config: RetryConfig):
        self.config = config
    
    async def execute(
        self,
        func: Callable,
        *args,
        **kwargs
    ) -> Any:
        """
        Ejecutar función con retry.
        
        Args:
            func: Función a ejecutar
            *args: Argumentos posicionales
            **kwargs: Argumentos nombrados
            
        Returns:
            Resultado de la función
            
        Raises:
            Exception: Si todos los intentos fallan
        """
        last_exception = None
        
        for attempt in range(1, self.config.max_attempts + 1):
            try:
                if asyncio.iscoroutinefunction(func):
                    return await func(*args, **kwargs)
                else:
                    return func(*args, **kwargs)
                    
            except self.config.retryable_exceptions as e:
                last_exception = e
                
                # Si es el último intento, no esperar
                if attempt >= self.config.max_attempts:
                    logger.error(
                        "Retry exhausted",
                        function=func.__name__,
                        attempts=attempt,
                        error=str(e)
                    )
                    raise
                
                # Calcular delay
                delay = self._calculate_delay(attempt)
                
                logger.warning(
                    "Retry attempt",
                    function=func.__name__,
                    attempt=attempt,
                    max_attempts=self.config.max_attempts,
                    delay=delay,
                    error=str(e)
                )
                
                await asyncio.sleep(delay)
            
            except Exception as e:
                # Excepción no retryable, lanzar inmediatamente
                logger.error(
                    "Non-retryable exception",
                    function=func.__name__,
                    error=str(e)
                )
                raise
        
        # Esto no debería alcanzarse, pero por seguridad
        if last_exception:
            raise last_exception
    
    def _calculate_delay(self, attempt: int) -> float:
        """
        Calcular delay con exponential backoff.
        
        Args:
            attempt: Número de intento actual
            
        Returns:
            Delay en segundos
        """
        # Exponential backoff: initial_delay * (base ^ (attempt - 1))
        delay = self.config.initial_delay * (
            self.config.exponential_base ** (attempt - 1)
        )
        
        # Aplicar max delay
        delay = min(delay, self.config.max_delay)
        
        # Aplicar jitter para evitar thundering herd
        if self.config.jitter:
            jitter = random.uniform(0, delay * 0.1)
            delay = delay + jitter
        
        return delay


def retry(
    max_attempts: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    retryable_exceptions: Tuple[Type[Exception], ...] = (Exception,)
):
    """
    Decorator para retry con exponential backoff.
    
    Usage:
        @retry(max_attempts=3, initial_delay=1.0)
        async def call_api():
            ...
    """
    def decorator(func: Callable):
        config = RetryConfig(
            max_attempts=max_attempts,
            initial_delay=initial_delay,
            max_delay=max_delay,
            exponential_base=exponential_base,
            jitter=jitter,
            retryable_exceptions=retryable_exceptions
        )
        handler = RetryHandler(config)
        
        async def wrapper(*args, **kwargs):
            return await handler.execute(func, *args, **kwargs)
        
        return wrapper
    return decorator


# Configuraciones predefinidas
BINANCE_RETRY_CONFIG = RetryConfig(
    max_attempts=3,
    initial_delay=1.0,
    max_delay=10.0,
    retryable_exceptions=(ConnectionError, TimeoutError,)
)

DATABASE_RETRY_CONFIG = RetryConfig(
    max_attempts=3,
    initial_delay=0.5,
    max_delay=5.0,
    retryable_exceptions=(ConnectionError,)
)

REDIS_RETRY_CONFIG = RetryConfig(
    max_attempts=2,
    initial_delay=0.1,
    max_delay=1.0,
    retryable_exceptions=(ConnectionError,)
)

