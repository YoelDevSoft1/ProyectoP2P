"""
Integración de circuit breakers con métricas Prometheus.
"""
from app.core.circuit_breaker import CircuitBreaker, CircuitState
from app.core.metrics import metrics
import structlog

logger = structlog.get_logger()


class MonitoredCircuitBreaker(CircuitBreaker):
    """
    Circuit Breaker con integración de métricas Prometheus.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Registrar estado inicial
        metrics.update_circuit_breaker_state(self.name, self._get_state_value())
    
    def _get_state_value(self) -> int:
        """Convertir estado a valor numérico para métricas (0=closed, 1=half-open, 2=open)"""
        if self.state == CircuitState.CLOSED:
            return 0
        elif self.state == CircuitState.HALF_OPEN:
            return 1
        elif self.state == CircuitState.OPEN:
            return 2
        return 0
    
    async def _on_failure(self):
        """Manejar fallo con métricas"""
        await super()._on_failure()
        metrics.track_circuit_breaker_failure(self.name)
        metrics.update_circuit_breaker_state(self.name, self._get_state_value())
        
        # Si se abrió el circuit, registrar
        if self.state == CircuitState.OPEN:
            metrics.track_circuit_breaker_open(self.name)
    
    async def _on_success(self):
        """Manejar éxito con métricas"""
        old_state = self.state
        await super()._on_success()
        
        # Si cambió el estado, actualizar métricas
        if old_state != self.state:
            metrics.update_circuit_breaker_state(self.name, self._get_state_value())
    
    def reset(self):
        """Resetear circuit breaker con métricas"""
        super().reset()
        metrics.update_circuit_breaker_state(self.name, self._get_state_value())

