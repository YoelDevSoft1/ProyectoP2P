"""
Circuit Breaker Pattern Implementation

Protege contra fallos en cascada cuando servicios externos fallan.
"""
from enum import Enum
from typing import Callable, Optional, Any
from datetime import datetime, timedelta
import asyncio
import structlog

logger = structlog.get_logger()


class CircuitState(Enum):
    """Estados del circuit breaker"""
    CLOSED = "closed"  # Funcionando normal
    OPEN = "open"  # Fallando, rechazar requests
    HALF_OPEN = "half_open"  # Probando si se recuperó


class CircuitBreaker:
    """
    Circuit Breaker para proteger contra fallos en cascada.
    
    Attributes:
        failure_threshold: Número de fallos antes de abrir
        recovery_timeout: Segundos antes de intentar recuperar
        expected_exception: Excepción esperada que cuenta como fallo
        name: Nombre del circuit breaker (para logging)
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exception: type = Exception,
        name: str = "default"
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self.name = name
        
        self.failure_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.state = CircuitState.CLOSED
        self.success_count = 0
        self._lock = asyncio.Lock()
    
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Ejecutar función con circuit breaker.
        
        Args:
            func: Función a ejecutar
            *args: Argumentos posicionales
            **kwargs: Argumentos nombrados
            
        Returns:
            Resultado de la función
            
        Raises:
            CircuitBreakerOpenError: Si el circuit está abierto
            Exception: Si la función falla
        """
        async with self._lock:
            # Verificar estado
            if self.state == CircuitState.OPEN:
                # Verificar si es tiempo de intentar recuperar
                if self._should_attempt_recovery():
                    self.state = CircuitState.HALF_OPEN
                    self.success_count = 0
                    logger.info(
                        "Circuit breaker transitioning to HALF_OPEN",
                        circuit=self.name
                    )
                else:
                    raise CircuitBreakerOpenError(
                        f"Circuit breaker {self.name} is OPEN. "
                        f"Will retry after {self.recovery_timeout} seconds"
                    )
            
            # Ejecutar función
            try:
                if asyncio.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)
                
                # Éxito
                await self._on_success()
                return result
                
            except self.expected_exception as e:
                # Fallo
                await self._on_failure()
                raise
    
    def _should_attempt_recovery(self) -> bool:
        """Verificar si es tiempo de intentar recuperar"""
        if self.last_failure_time is None:
            return True
        
        time_since_failure = (datetime.utcnow() - self.last_failure_time).total_seconds()
        return time_since_failure >= self.recovery_timeout
    
    async def _on_success(self):
        """Manejar éxito"""
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            # Si tenemos suficientes éxitos, cerrar el circuit
            if self.success_count >= 3:
                self.state = CircuitState.CLOSED
                self.failure_count = 0
                self.success_count = 0
                logger.info(
                    "Circuit breaker CLOSED after recovery",
                    circuit=self.name
                )
        elif self.state == CircuitState.CLOSED:
            # Reset failure count en estado cerrado
            self.failure_count = 0
    
    async def _on_failure(self):
        """Manejar fallo"""
        self.failure_count += 1
        self.last_failure_time = datetime.utcnow()
        
        if self.state == CircuitState.HALF_OPEN:
            # Si falla en half-open, volver a abrir
            self.state = CircuitState.OPEN
            self.success_count = 0
            logger.warning(
                "Circuit breaker OPENED after failure in HALF_OPEN state",
                circuit=self.name,
                failure_count=self.failure_count
            )
        elif self.state == CircuitState.CLOSED:
            # Si alcanzamos el threshold, abrir el circuit
            if self.failure_count >= self.failure_threshold:
                self.state = CircuitState.OPEN
                logger.error(
                    "Circuit breaker OPENED",
                    circuit=self.name,
                    failure_count=self.failure_count,
                    threshold=self.failure_threshold
                )
    
    def get_state(self) -> CircuitState:
        """Obtener estado actual"""
        return self.state
    
    def reset(self):
        """Resetear circuit breaker manualmente"""
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        logger.info("Circuit breaker RESET", circuit=self.name)


class CircuitBreakerOpenError(Exception):
    """Excepción cuando el circuit breaker está abierto"""
    pass


# Instancias globales de circuit breakers
binance_circuit_breaker = CircuitBreaker(
    failure_threshold=5,
    recovery_timeout=60,
    name="binance_api"
)

redis_circuit_breaker = CircuitBreaker(
    failure_threshold=3,
    recovery_timeout=30,
    name="redis"
)

database_circuit_breaker = CircuitBreaker(
    failure_threshold=5,
    recovery_timeout=60,
    name="database"
)


def circuit_breaker(name: str = "default", **kwargs):
    """
    Decorator para circuit breaker.
    
    Usage:
        @circuit_breaker(name="binance", failure_threshold=5)
        async def call_binance_api():
            ...
    """
    def decorator(func: Callable):
        breaker = CircuitBreaker(name=name, **kwargs)
        
        async def wrapper(*args, **kwargs):
            return await breaker.call(func, *args, **kwargs)
        
        return wrapper
    return decorator

