"""
Configuración de la base de datos con SQLAlchemy.
"""
from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool
from typing import Generator
import redis.asyncio as aioredis
import time

from app.core.config import settings
from app.core.metrics import metrics

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


# Event listener para trackear queries de base de datos
@event.listens_for(engine, "before_cursor_execute")
def receive_before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    """Registrar inicio de query"""
    conn.info.setdefault('query_start_time', []).append(time.time())


@event.listens_for(engine, "after_cursor_execute")
def receive_after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    """Registrar fin de query y métricas"""
    total = conn.info.get('query_start_time', [])
    if total:
        start_time = total.pop()
        duration = time.time() - start_time
        
        # Determinar tipo de query
        query_type = "SELECT"
        if statement.strip().upper().startswith("INSERT"):
            query_type = "INSERT"
        elif statement.strip().upper().startswith("UPDATE"):
            query_type = "UPDATE"
        elif statement.strip().upper().startswith("DELETE"):
            query_type = "DELETE"
        elif statement.strip().upper().startswith("CREATE"):
            query_type = "CREATE"
        elif statement.strip().upper().startswith("ALTER"):
            query_type = "ALTER"
        elif statement.strip().upper().startswith("DROP"):
            query_type = "DROP"
        
        # Extraer nombre de tabla si es posible
        table = "unknown"
        statement_upper = statement.upper()
        for keyword in ["FROM", "INTO", "UPDATE", "DELETE FROM"]:
            if keyword in statement_upper:
                parts = statement_upper.split(keyword, 1)
                if len(parts) > 1:
                    table_part = parts[1].strip().split()[0]
                    # Limpiar caracteres especiales
                    table = table_part.strip(";(),").lower()
                    break
        
        # Registrar métricas
        try:
            metrics.track_db_query(
                query_type=query_type,
                table=table,
                duration=duration,
                status="success"
            )
        except Exception:
            pass  # No fallar si las métricas fallan


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
