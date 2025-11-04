"""
Modelo de historial de precios.
Almacena datos de series temporales para análisis.
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Index
from sqlalchemy.sql import func

from app.core.database import Base


class PriceHistory(Base):
    """
    Historial de precios para análisis.
    Se convierte en hypertable de TimescaleDB.
    """
    __tablename__ = "price_history"

    id = Column(Integer, primary_key=True, index=True)

    # Par de divisas
    asset = Column(String, nullable=False, index=True)  # USDT, BTC
    fiat = Column(String, nullable=False, index=True)  # COP, VES

    # Precios
    bid_price = Column(Float, nullable=False)  # Mejor precio de compra
    ask_price = Column(Float, nullable=False)  # Mejor precio de venta
    avg_price = Column(Float, nullable=False)  # Precio promedio
    spread = Column(Float, nullable=False)  # Diferencia bid-ask (porcentaje)

    # Volumen (si está disponible)
    volume_24h = Column(Float, nullable=True)

    # Fuente de datos
    source = Column(String, default="binance_p2p", nullable=False)

    # TRM para COP (si aplica)
    trm_rate = Column(Float, nullable=True)

    # Timestamp
    timestamp = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True
    )

    # Índice compuesto para queries rápidas
    __table_args__ = (
        Index('idx_price_asset_fiat_time', 'asset', 'fiat', 'timestamp'),
    )

    def __repr__(self):
        return f"<PriceHistory {self.asset}/{self.fiat} @ {self.timestamp}>"

    @property
    def spread_percentage(self) -> float:
        """Spread en porcentaje"""
        if self.bid_price > 0:
            return ((self.ask_price - self.bid_price) / self.bid_price) * 100
        return 0.0
