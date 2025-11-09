"""
Configuración de base de datos asíncrona con SQLAlchemy 2.0.
Mejora el rendimiento con conexiones asíncronas y mejor pooling.
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import QueuePool
from typing import AsyncGenerator
import structlog

from app.core.config import settings

logger = structlog.get_logger()

# Convertir DATABASE_URL a formato asíncrono si es necesario
def get_async_database_url() -> str:
    """Convertir DATABASE_URL a formato asíncrono"""
    db_url = settings.DATABASE_URL
    if db_url.startswith("postgresql://"):
        # Reemplazar postgresql:// con postgresql+asyncpg://
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    elif db_url.startswith("postgres://"):
        # Reemplazar postgres:// con postgresql+asyncpg://
        db_url = db_url.replace("postgres://", "postgresql+asyncpg://", 1)
    return db_url


# Engine asíncrono para PostgreSQL
async_engine = create_async_engine(
    get_async_database_url(),
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_pre_ping=True,  # Verificar conexiones antes de usarlas
    pool_recycle=3600,  # Reciclar conexiones cada hora
    echo=settings.DEBUG,  # Log de SQL en modo debug
    future=True,
)

# Session factory asíncrona
AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Base para modelos (compartida con la versión síncrona)
from app.core.database import Base

# Alias para compatibilidad
AsyncBase = Base


async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency que proporciona una sesión de base de datos asíncrona.
    Se cierra automáticamente al finalizar la request.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_async_db():
    """Crear todas las tablas en la base de datos (asíncrono)"""
    # Importar todos los modelos aquí para que SQLAlchemy los conozca
    from app.models import user, trade, price_history, alert
    
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    logger.info("Async database initialized")


async def close_async_db_connections():
    """Cerrar todas las conexiones de base de datos asíncronas"""
    await async_engine.dispose()
    logger.info("Async database connections closed")


# Health check asíncrono
async def check_db_health() -> dict:
    """
    Verificar salud de la base de datos.
    
    Returns:
        dict con información del estado de la base de datos
    """
    try:
        async with AsyncSessionLocal() as session:
            from sqlalchemy import text
            result = await session.execute(text("SELECT 1"))
            result.scalar()
            
            # Obtener información del pool
            pool = async_engine.pool
            pool_size = pool.size() if hasattr(pool, 'size') else 0
            checked_in = pool.checkedin() if hasattr(pool, 'checkedin') else 0
            checked_out = pool.checkedout() if hasattr(pool, 'checkedout') else 0
            overflow = pool.overflow() if hasattr(pool, 'overflow') else 0
            
            return {
                "status": "healthy",
                "pool_size": pool_size,
                "checked_in": checked_in,
                "checked_out": checked_out,
                "overflow": overflow,
            }
    except Exception as e:
        logger.error("Database health check failed", error=str(e))
        return {
            "status": "unhealthy",
            "error": str(e)
        }

