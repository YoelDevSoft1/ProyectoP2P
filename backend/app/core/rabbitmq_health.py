"""
Health check y monitoreo para RabbitMQ.
"""
import asyncio
from typing import Optional
from datetime import datetime

from aio_pika import connect_robust, Message
import structlog

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
        connection = None
        channel = None
        try:
            start_time = datetime.utcnow()
            timeout_seconds = 5

            connection = await connect_robust(
                settings.RABBITMQ_URL,
                client_properties={"connection_name": "health_check"},
                timeout=timeout_seconds,
            )

            if connection.is_closed:
                raise ConnectionError("RabbitMQ connection is closed")

            channel = await connection.channel()

            queue = await channel.declare_queue(
                name="",
                exclusive=True,
                auto_delete=True,
                durable=False,
            )

            test_message = Message(b"health_check")
            await channel.default_exchange.publish(test_message, routing_key=queue.name)

            try:
                message = await queue.get(timeout=timeout_seconds)
            except asyncio.TimeoutError as exc:
                raise TimeoutError("Timeout waiting for health check message") from exc

            await message.ack()

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
        finally:
            if channel and not channel.is_closed:
                await channel.close()
            if connection and not connection.is_closed:
                await connection.close()
    
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

