"""
Configuración central de la aplicación.
Lee variables de entorno y proporciona configuración tipada.
"""
from typing import Any, Dict, List, Literal, Union
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator, Field


class Settings(BaseSettings):
    """Configuración de la aplicación usando Pydantic Settings v2"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        env_ignore_empty=True,
        extra="ignore"
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

    # CORS - Usar modelo personalizado para evitar problemas con parsing automático
    # El validator procesará strings, listas o None y retornará siempre List[str]
    BACKEND_CORS_ORIGINS: str = Field(
        default="http://localhost:3000,https://proyecto-p2p.vercel.app",
        description="Lista de orígenes permitidos para CORS (separados por comas o JSON array)"
    )

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Any) -> str:
        """
        Normalizar BACKEND_CORS_ORIGINS a string antes de procesarlo.
        Esto evita que Pydantic intente parsear valores vacíos como JSON.
        """
        default_origins = "http://localhost:3000,https://proyecto-p2p.vercel.app"
        
        # Si es None, retornar default como string
        if v is None:
            return default_origins
        
        # Si ya es string, verificar si está vacío
        if isinstance(v, str):
            v = v.strip()
            if not v or v == "":
                return default_origins
            # Retornar el string tal cual (será procesado después)
            return v
        
        # Si es lista, convertir a string separado por comas
        if isinstance(v, list):
            if not v or len(v) == 0:
                return default_origins
            return ",".join(str(o).strip() for o in v if str(o) and str(o).strip())
        
        # Cualquier otro tipo, convertir a string
        return str(v) if v else default_origins
    
    @property
    def cors_origins_list(self) -> List[str]:
        """
        Propiedad que retorna BACKEND_CORS_ORIGINS como lista procesada.
        Esto se usa en lugar de acceder directamente a BACKEND_CORS_ORIGINS.
        """
        import json
        
        default_origins = ["http://localhost:3000", "https://proyecto-p2p.vercel.app"]
        cors_str = self.BACKEND_CORS_ORIGINS.strip()
        
        if not cors_str:
            return default_origins
        
        try:
            # Intentar parsear como JSON si parece un array JSON
            if cors_str.startswith("[") and cors_str.endswith("]"):
                try:
                    parsed = json.loads(cors_str)
                    if isinstance(parsed, list):
                        origins = [str(o).strip() for o in parsed if str(o) and str(o).strip()]
                        if not origins:
                            return default_origins
                        if any("*" in str(o) or "ngrok" in str(o).lower() for o in origins):
                            return ["*"]
                        return origins
                except (json.JSONDecodeError, ValueError, TypeError):
                    pass
            
            # Tratar como string separada por comas
            origins = [i.strip() for i in cors_str.split(",") if i.strip()]
            if not origins:
                return default_origins
            if "*" in origins or any("ngrok" in o.lower() for o in origins):
                return ["*"]
            return origins
            
        except Exception:
            return default_origins

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
