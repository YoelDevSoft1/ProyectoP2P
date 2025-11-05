"""
Punto de entrada principal de la aplicación FastAPI.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from contextlib import asynccontextmanager
import structlog

from app.core.config import settings
from app.core.database import init_db, close_db_connections
from app.api.endpoints import health, trades, prices, analytics, spot, arbitrage, advanced_arbitrage

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
    init_db()
    logger.info("Database initialized")

    yield

    # Shutdown
    logger.info("Shutting down application")
    await close_db_connections()
    logger.info("Database connections closed")


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
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware de compresión
app.add_middleware(GZipMiddleware, minimum_size=1000)


# Incluir routers
app.include_router(
    health.router,
    prefix=settings.API_V1_STR,
    tags=["health"]
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
    arbitrage.router,
    prefix=f"{settings.API_V1_STR}/arbitrage",
    tags=["arbitrage"]
)

app.include_router(
    advanced_arbitrage.router,
    prefix=f"{settings.API_V1_STR}/advanced-arbitrage",
    tags=["advanced-arbitrage"]
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
