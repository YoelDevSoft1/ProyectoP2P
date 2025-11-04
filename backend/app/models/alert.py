"""
Modelo de alertas y notificaciones.
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Enum, Boolean, Text
from sqlalchemy.sql import func
import enum

from app.core.database import Base


class AlertType(str, enum.Enum):
    """Tipo de alerta"""
    PRICE_CHANGE = "price_change"
    SPREAD_OPPORTUNITY = "spread_opportunity"
    ARBITRAGE_OPPORTUNITY = "arbitrage_opportunity"
    TRADE_COMPLETED = "trade_completed"
    TRADE_FAILED = "trade_failed"
    SYSTEM_ERROR = "system_error"
    ML_PREDICTION = "ml_prediction"
    HIGH_VOLUME = "high_volume"


class AlertPriority(str, enum.Enum):
    """Prioridad de la alerta"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Alert(Base):
    """Modelo de alertas del sistema"""
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)

    # Tipo y prioridad
    alert_type = Column(Enum(AlertType), nullable=False, index=True)
    priority = Column(Enum(AlertPriority), default=AlertPriority.MEDIUM, nullable=False)

    # Contenido
    title = Column(String, nullable=False)
    message = Column(Text, nullable=False)

    # Datos asociados
    asset = Column(String, nullable=True)
    fiat = Column(String, nullable=True)
    price = Column(Float, nullable=True)
    percentage = Column(Float, nullable=True)

    # Estado
    is_read = Column(Boolean, default=False)
    is_sent = Column(Boolean, default=False)  # Si fue enviada por Telegram/Email

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    read_at = Column(DateTime(timezone=True), nullable=True)
    sent_at = Column(DateTime(timezone=True), nullable=True)

    def __repr__(self):
        return f"<Alert {self.alert_type.value}: {self.title}>"
