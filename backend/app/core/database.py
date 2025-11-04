"""
Configuración de la base de datos con SQLAlchemy.
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool
from typing import Generator
import redis.asyncio as aioredis

from app.core.config import settings

# Engine para PostgreSQL
engine = create_engine(
    settings.DATABASE_URL,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_pre_ping=True,  # Verificar conexiones antes de usarlas
    echo=settings.DEBUG,  # Log de SQL en modo debug
)

# Session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Base para modelos
Base = declarative_base()


# Redis client
class RedisClient:
    """Cliente Redis singleton"""
    _instance = None
    _client = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(RedisClient, cls).__new__(cls)
        return cls._instance

    async def get_client(self) -> aioredis.Redis:
        """Obtener cliente Redis"""
        if self._client is None:
            self._client = await aioredis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True
            )
        return self._client

    async def close(self):
        """Cerrar conexión Redis"""
        if self._client:
            await self._client.close()
            self._client = None


redis_client = RedisClient()


# Dependency para obtener session de DB
def get_db() -> Generator[Session, None, None]:
    """
    Dependency que proporciona una sesión de base de datos.
    Se cierra automáticamente al finalizar la request.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_redis() -> aioredis.Redis:
    """
    Dependency que proporciona cliente Redis.
    """
    return await redis_client.get_client()


# Funciones para inicialización y cierre
def init_db():
    """Crear todas las tablas en la base de datos"""
    # Importar todos los modelos aquí para que SQLAlchemy los conozca
    from app.models import user, trade, price_history, alert
    Base.metadata.create_all(bind=engine)


async def close_db_connections():
    """Cerrar todas las conexiones de base de datos"""
    engine.dispose()
    await redis_client.close()
