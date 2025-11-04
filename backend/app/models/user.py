"""
Modelo de Usuario.
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float
from sqlalchemy.sql import func
from app.core.database import Base


class User(Base):
    """Modelo de usuario del sistema"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)

    # Información personal
    full_name = Column(String, nullable=True)
    phone = Column(String, nullable=True)

    # Estado
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)

    # Configuración de trading
    trading_enabled = Column(Boolean, default=False)
    max_daily_amount = Column(Float, default=1000.0)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)

    def __repr__(self):
        return f"<User {self.username}>"
