"""
Modelo de operaciones de trading.
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Enum, ForeignKey, Text, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum

from app.core.database import Base


class TradeType(str, enum.Enum):
    """Tipo de operación"""
    BUY = "buy"
    SELL = "sell"


class TradeStatus(str, enum.Enum):
    """Estado de la operación"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"


class Trade(Base):
    """Modelo de operación de trading"""
    __tablename__ = "trades"

    id = Column(Integer, primary_key=True, index=True)

    # Referencia a Binance
    binance_order_id = Column(String, unique=True, index=True, nullable=True)

    # Tipo y estado
    trade_type = Column(Enum(TradeType), nullable=False)
    status = Column(Enum(TradeStatus), default=TradeStatus.PENDING, nullable=False, index=True)

    # Par de divisas
    asset = Column(String, default="USDT", nullable=False)  # USDT, BTC, etc.
    fiat = Column(String, nullable=False, index=True)  # COP, VES

    # Cantidades
    crypto_amount = Column(Float, nullable=False)  # Cantidad de cripto
    fiat_amount = Column(Float, nullable=False)  # Cantidad de fiat
    price = Column(Float, nullable=False)  # Precio unitario

    # Comisiones y ganancia
    fee = Column(Float, default=0.0)
    profit_margin = Column(Float, nullable=False)  # Porcentaje de ganancia esperado
    actual_profit = Column(Float, nullable=True)  # Ganancia real obtenida

    # Método de pago
    payment_method = Column(String, nullable=True)

    # Modo de ejecución
    is_automated = Column(Boolean, default=False)  # True si fue ejecutado automáticamente

    # Información adicional
    notes = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)

    # Contraparte (nombre del trader en Binance)
    counterparty = Column(String, nullable=True)

    # Usuario que realizó la operación
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)

    def __repr__(self):
        return f"<Trade {self.id} {self.trade_type.value} {self.crypto_amount} {self.asset}/{self.fiat}>"

    @property
    def duration_seconds(self) -> float:
        """Duración de la operación en segundos"""
        if self.completed_at and self.created_at:
            return (self.completed_at - self.created_at).total_seconds()
        return 0.0
