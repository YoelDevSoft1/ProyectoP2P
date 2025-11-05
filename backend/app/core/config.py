"""
Configuración central de la aplicación.
Lee variables de entorno y proporciona configuración tipada.
"""
from typing import Dict, List, Literal
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import validator, Field


class Settings(BaseSettings):
    """Configuración de la aplicación usando Pydantic Settings v2"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )

    # Información del proyecto
    PROJECT_NAME: str = "Casa de Cambio P2P"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    # Base de datos
    DATABASE_URL: str
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20

    # Redis
    REDIS_URL: str
    REDIS_CACHE_TTL: int = 300

    # RabbitMQ
    RABBITMQ_URL: str

    # Binance API
    BINANCE_API_KEY: str
    BINANCE_API_SECRET: str
    BINANCE_TESTNET: bool = False

    # Trading Configuration
    TRADING_MODE: Literal["manual", "auto", "hybrid"] = "hybrid"
    PROFIT_MARGIN_COP: float = 2.5
    PROFIT_MARGIN_VES: float = 3.0
    MIN_TRADE_AMOUNT: float = 50.0
    MAX_TRADE_AMOUNT: float = 1000.0
    MAX_DAILY_TRADES: int = 50
    STOP_LOSS_PERCENTAGE: float = 1.5

    # TRM (Colombia)
    TRM_API_URL: str = "https://www.datos.gov.co/resource/32sa-8pi3.json"
    TRM_UPDATE_INTERVAL: int = 300

    # FX y tasas de cambio
    FX_CACHE_TTL_SECONDS: int = 120
    FX_FALLBACK_RATES: Dict[str, float] = Field(default_factory=lambda: {
        "COP": 4000.0,
        "VES": 36.5,
        "USD": 1.0,
        "BRL": 5.0,
        "ARS": 900.0,
        "CLP": 900.0,
        "PEN": 3.8,
        "MXN": 17.0,
    })

    # Tasa Venezuela
    VES_RATE_SOURCE: str = "bcv"
    VES_UPDATE_INTERVAL: int = 300

    # JWT y Seguridad
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # CORS
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:3000", "https://proyecto-p2p.vercel.app"]

    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v):
        if isinstance(v, str):
            origins = [i.strip() for i in v.split(",")]
            # Si contiene "*" o está en modo desarrollo, permitir todos los orígenes
            if "*" in origins or any("ngrok" in o.lower() for o in origins):
                return ["*"]
            return origins
        # Si es una lista y contiene ngrok o wildcard, permitir todos
        if isinstance(v, list):
            for origin in v:
                if "*" in origin or "ngrok" in origin.lower():
                    return ["*"]
        return v

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE_PATH: str = "/app/logs/app.log"

    # ML Settings
    ML_RETRAIN_INTERVAL: int = 86400
    ML_MIN_DATA_POINTS: int = 1000
    ML_CONFIDENCE_THRESHOLD: float = 0.75

    # Notificaciones
    ENABLE_NOTIFICATIONS: bool = True
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_CHAT_ID: str = ""
    EMAIL_SMTP_SERVER: str = ""
    EMAIL_SMTP_PORT: int = 587
    EMAIL_FROM: str = ""
    EMAIL_PASSWORD: str = ""

    # Análisis
    SPREAD_THRESHOLD: float = 0.5
    P2P_MONITORED_ASSETS: List[str] = Field(default_factory=lambda: ["USDT"])
    P2P_MONITORED_FIATS: List[str] = Field(default_factory=lambda: ["COP", "VES", "BRL", "ARS", "CLP", "PEN", "MXN"])
    P2P_ANALYSIS_ROWS: int = 20
    P2P_TOP_SPREADS: int = 3
    ARBITRAGE_MONITORED_ASSETS: List[str] = Field(default_factory=lambda: ["USDT", "BTC", "ETH"])
    ARBITRAGE_MONITORED_FIATS: List[str] = Field(default_factory=lambda: ["USD", "COP", "VES", "BRL", "ARS", "CLP", "PEN", "MXN"])
    ARBITRAGE_TOP_OPPORTUNITIES: int = 5
    ARBITRAGE_MIN_LIQUIDITY_USDT: float = 100.0
    ARBITRAGE_MIN_PROFIT: float = 1.0
    UPDATE_PRICE_INTERVAL: int = 10

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_BINANCE_API: int = 1200
    P2P_PRICE_CACHE_SECONDS: int = 15
    P2P_MIN_SURPLUS_USDT: float = 50.0

    # Entorno
    DEBUG: bool = True
    ENVIRONMENT: Literal["development", "staging", "production"] = "development"

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"

    @property
    def binance_base_url(self) -> str:
        if self.BINANCE_TESTNET:
            return "https://testnet.binance.vision"
        return "https://api.binance.com"


# Instancia global de settings
settings = Settings()
