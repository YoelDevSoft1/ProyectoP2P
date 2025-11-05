"""
Punto de entrada principal de la aplicación FastAPI.
"""
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from contextlib import asynccontextmanager
import structlog

from app.core.config import settings
from app.core.database import init_db, close_db_connections
from app.api.endpoints import health, trades, prices, analytics, spot, advanced_arbitrage

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
# En desarrollo, permitir todos los orígenes (necesario para ngrok y Vercel)
cors_origins = settings.BACKEND_CORS_ORIGINS
# Si está en desarrollo o producción, permitir todos los orígenes para flexibilidad
if settings.ENVIRONMENT == "development" or "*" in cors_origins:
    cors_origins = ["*"]
else:
    # Agregar Vercel si no está ya incluido
    vercel_origin = "https://proyecto-p2p.vercel.app"
    if vercel_origin not in cors_origins:
        cors_origins = list(cors_origins) + [vercel_origin]

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

# Middleware para manejar ngrok interceptor page y OPTIONS requests
@app.middleware("http")
async def ngrok_cors_middleware(request: Request, call_next):
    """
    Middleware para manejar requests de ngrok y CORS preflight.
    """
    # Manejar OPTIONS (preflight requests)
    if request.method == "OPTIONS":
        response = Response()
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "*"
        response.headers["Access-Control-Allow-Credentials"] = "true"
        return response
    
    response = await call_next(request)
    
    # Agregar headers CORS a todas las respuestas si estamos en desarrollo
    if settings.ENVIRONMENT == "development":
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Credentials"] = "true"
    
    return response


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
