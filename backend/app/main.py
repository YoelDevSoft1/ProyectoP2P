"""
Punto de entrada principal de la aplicación FastAPI.
"""
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from contextlib import asynccontextmanager
import structlog
import time

from app.core.config import settings
from app.core.database import init_db, close_db_connections, SessionLocal
from app.core.database_async import init_async_db, close_async_db_connections
from app.core.redis_pool import redis_pool
from app.core.metrics import metrics, initialize_metrics
from app.services.config_service import ConfigService
from app.api.endpoints import (
    advanced_arbitrage,
    analytics,
    config,
    health,
    market_making,
    order_execution,
    p2p_trading,
    prices,
    spot,
    trades,
    dynamic_pricing,
    forex,
)

# Configurar logging estructurado
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ]
)

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gestión del ciclo de vida de la aplicación.
    Se ejecuta al inicio y al cierre.
    """
    # Startup
    logger.info("Starting application", environment=settings.ENVIRONMENT)
    
    # Inicializar base de datos síncrona
    init_db()
    logger.info("Synchronous database initialized")
    
    # Cargar configuración persistente desde la base de datos
    try:
        db = SessionLocal()
        try:
            config_service = ConfigService(db)
            config_service.load_trading_config_to_settings()
            logger.info("Persistent configuration loaded from database")
        except Exception as e:
            logger.warning(f"Could not load persistent configuration: {e}", exc_info=True)
        finally:
            db.close()
    except Exception as e:
        logger.warning(f"Error loading persistent configuration: {e}", exc_info=True)
    
    # Inicializar base de datos asíncrona
    await init_async_db()
    logger.info("Asynchronous database initialized")
    
    # Inicializar Redis pool
    await redis_pool.initialize()
    logger.info("Redis pool initialized")
    
    # Inicializar métricas con valores por defecto
    initialize_metrics()
    logger.info("Metrics initialized")
    
    yield

    # Shutdown
    logger.info("Shutting down application")
    
    # Cerrar conexiones de base de datos
    await close_db_connections()
    await close_async_db_connections()
    logger.info("Database connections closed")
    
    # Cerrar Redis pool
    await redis_pool.close()
    logger.info("Redis pool closed")


# Crear aplicación FastAPI
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
    lifespan=lifespan
)

# Middleware CORS
# Usar la propiedad cors_origins_list que procesa correctamente el valor
cors_origins = settings.cors_origins_list
# Si está en desarrollo, permitir todos los orígenes (necesario para ngrok y Vercel)
if settings.ENVIRONMENT == "development" or "*" in cors_origins:
    cors_origins = ["*"]
else:
    # Agregar Vercel si no está ya incluido
    vercel_origin = "https://proyecto-p2p.vercel.app"
    if vercel_origin not in cors_origins:
        cors_origins = cors_origins + [vercel_origin]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Middleware de compresión
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Middleware para métricas Prometheus
@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    """
    Middleware para capturar métricas de requests HTTP.
    """
    start_time = time.time()
    
    # Manejar OPTIONS (preflight requests) - no registrar métricas
    if request.method == "OPTIONS":
        response = Response()
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "*"
        response.headers["Access-Control-Allow-Credentials"] = "true"
        return response
    
    # Procesar request
    try:
        response = await call_next(request)
        status_code = response.status_code
    except Exception as e:
        status_code = 500
        raise
    finally:
        # Calcular duración
        duration = time.time() - start_time
        
        # Registrar métricas (solo si no es el endpoint de métricas para evitar loops)
        if request.url.path != "/api/v1/metrics" and not request.url.path.startswith("/api/v1/metrics"):
            metrics.track_request(
                method=request.method,
                endpoint=request.url.path,
                status_code=status_code,
                duration=duration
            )
    
    # Agregar headers CORS a todas las respuestas si estamos en desarrollo
    if settings.ENVIRONMENT == "development":
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Credentials"] = "true"
    
    return response

# Middleware para manejar ngrok interceptor page
@app.middleware("http")
async def ngrok_cors_middleware(request: Request, call_next):
    """
    Middleware para manejar requests de ngrok y CORS preflight.
    """
    response = await call_next(request)
    return response


# Incluir routers
# Incluir router de health (que incluye métricas)
app.include_router(
    health.router,
    prefix=settings.API_V1_STR,
    tags=["health", "metrics"]
)

app.include_router(
    trades.router,
    prefix=f"{settings.API_V1_STR}/trades",
    tags=["trades"]
)

app.include_router(
    prices.router,
    prefix=f"{settings.API_V1_STR}/prices",
    tags=["prices"]
)

app.include_router(
    analytics.router,
    prefix=f"{settings.API_V1_STR}/analytics",
    tags=["analytics"]
)

app.include_router(
    spot.router,
    prefix=f"{settings.API_V1_STR}/spot",
    tags=["spot"]
)

app.include_router(
    advanced_arbitrage.router,
    prefix=f"{settings.API_V1_STR}/advanced-arbitrage",
    tags=["advanced-arbitrage"]
)

app.include_router(
    dynamic_pricing.router,
    prefix=f"{settings.API_V1_STR}",
    tags=["dynamic-pricing"]
)

app.include_router(
    market_making.router,
    prefix=f"{settings.API_V1_STR}",
    tags=["market-making"]
)

app.include_router(
    order_execution.router,
    prefix=f"{settings.API_V1_STR}",
    tags=["order-execution"]
)

app.include_router(
    p2p_trading.router,
    prefix=f"{settings.API_V1_STR}",
    tags=["p2p-trading"]
)

app.include_router(
    forex.router,
    prefix=f"{settings.API_V1_STR}",
    tags=["forex"]
)

app.include_router(
    config.router,
    prefix=f"{settings.API_V1_STR}",
    tags=["config"]
)


@app.get("/")
async def root():
    """Endpoint raíz"""
    return {
        "name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "docs": f"{settings.API_V1_STR}/docs"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
