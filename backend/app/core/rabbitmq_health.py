"""
Health check y monitoreo para RabbitMQ.
"""
import aio_pika
from aio_pika import connect_robust, Message
from typing import Optional
import structlog
from datetime import datetime

from app.core.config import settings
from app.core.metrics import rabbitmq_connection_status

logger = structlog.get_logger()


class RabbitMQHealth:
    """
    Cliente para verificar salud de RabbitMQ.
    """
    
    def __init__(self):
        self._connection: Optional[aio_pika.RobustConnection] = None
        self._is_healthy = False
        self._last_check: Optional[datetime] = None
    
    async def check_health(self) -> dict:
        """
        Verificar salud de RabbitMQ.
        
        Returns:
            dict con información del estado de RabbitMQ
        """
        try:
            start_time = datetime.utcnow()
            
            # Intentar conectar
            connection = await connect_robust(
                settings.RABBITMQ_URL,
                client_properties={
                    "connection_name": "health_check",
                }
            )
            
            # Verificar que la conexión está abierta
            if connection.is_closed:
                raise ConnectionError("RabbitMQ connection is closed")
            
            # Obtener canal
            channel = await connection.channel()
            
            # Verificar que podemos crear una cola temporal
            queue = await channel.declare_queue("health_check_temp", auto_delete=True, durable=False)
            
            # Publicar y consumir un mensaje de prueba
            test_message = Message(b"health_check")
            await channel.default_exchange.publish(test_message, routing_key=queue.name)
            
            # Consumir el mensaje con timeout
            async with queue.iterator() as queue_iter:
                async for message in queue_iter:
                    await message.ack()
                    break
            
            # Cerrar recursos
            await queue.delete()
            await channel.close()
            await connection.close()
            
            duration = (datetime.utcnow() - start_time).total_seconds()
            
            self._is_healthy = True
            self._last_check = datetime.utcnow()
            
            rabbitmq_connection_status.set(1)
            
            return {
                "status": "healthy",
                "latency_ms": round(duration * 1000, 2),
                "checked_at": self._last_check.isoformat(),
            }
            
        except Exception as e:
            logger.error("RabbitMQ health check failed", error=str(e))
            self._is_healthy = False
            self._last_check = datetime.utcnow()
            
            rabbitmq_connection_status.set(0)
            
            return {
                "status": "unhealthy",
                "error": str(e),
                "checked_at": self._last_check.isoformat(),
            }
    
    @property
    def is_healthy(self) -> bool:
        """Verificar si RabbitMQ está saludable"""
        return self._is_healthy
    
    @property
    def last_check(self) -> Optional[datetime]:
        """Obtener última verificación"""
        return self._last_check


# Instancia global
rabbitmq_health = RabbitMQHealth()

