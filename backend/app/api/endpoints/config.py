"""
Endpoints para gestión de configuración de la aplicación.
Permite leer y actualizar configuraciones (solo las que son seguras de modificar).
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Literal, Dict
from sqlalchemy.orm import Session
import os
import logging

from app.core.config import settings
from app.core.database import get_db
from app.services.config_service import ConfigService

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================================
# MODELS (Pydantic Schemas)
# ============================================================================

class TradingConfig(BaseModel):
    """Configuración de trading"""
    trading_mode: Literal["manual", "auto", "hybrid"] = Field(..., description="Modo de trading")
    profit_margin_cop: float = Field(..., ge=0, le=10, description="Margen de ganancia para COP (%)")
    profit_margin_ves: float = Field(..., ge=0, le=10, description="Margen de ganancia para VES (%)")
    min_trade_amount: float = Field(..., ge=0, description="Monto mínimo de trade (USD)")
    max_trade_amount: float = Field(..., ge=0, description="Monto máximo de trade (USD)")
    max_daily_trades: int = Field(..., ge=1, le=1000, description="Máximo de trades por día")
    stop_loss_percentage: float = Field(..., ge=0, le=10, description="Stop loss (%)")


class P2PConfig(BaseModel):
    """Configuración de P2P"""
    monitored_assets: List[str] = Field(..., description="Assets monitoreados (ej: USDT, BTC)")
    monitored_fiats: List[str] = Field(..., description="Fiats monitoreados (ej: COP, VES)")
    analysis_rows: int = Field(..., ge=1, le=100, description="Número de filas a analizar")
    top_spreads: int = Field(..., ge=1, le=20, description="Top spreads a mostrar")
    price_cache_seconds: int = Field(..., ge=1, le=3600, description="Tiempo de caché de precios (segundos)")
    min_surplus_usdt: float = Field(..., ge=0, description="Excedente mínimo en USDT")


class ArbitrageConfig(BaseModel):
    """Configuración de arbitraje"""
    monitored_assets: List[str] = Field(..., description="Assets para arbitraje")
    monitored_fiats: List[str] = Field(..., description="Fiats para arbitraje")
    top_opportunities: int = Field(..., ge=1, le=50, description="Top oportunidades a mostrar")
    min_liquidity_usdt: float = Field(..., ge=0, description="Liquidez mínima en USDT")
    min_profit: float = Field(..., ge=0, description="Ganancia mínima (%)")
    update_price_interval: int = Field(..., ge=1, le=3600, description="Intervalo de actualización de precios (segundos)")


class NotificationConfig(BaseModel):
    """Configuración de notificaciones"""
    enable_notifications: bool = Field(..., description="Habilitar notificaciones")
    telegram_bot_token: Optional[str] = Field(None, description="Token del bot de Telegram (oculto por seguridad)")
    telegram_chat_id: Optional[str] = Field(None, description="Chat ID de Telegram")
    email_smtp_server: Optional[str] = Field(None, description="Servidor SMTP")
    email_smtp_port: int = Field(587, ge=1, le=65535, description="Puerto SMTP")
    email_from: Optional[str] = Field(None, description="Email de origen")


class MLConfig(BaseModel):
    """Configuración de Machine Learning"""
    retrain_interval: int = Field(..., ge=3600, description="Intervalo de re-entrenamiento (segundos)")
    min_data_points: int = Field(..., ge=100, description="Puntos de datos mínimos")
    confidence_threshold: float = Field(..., ge=0, le=1, description="Umbral de confianza")
    spread_threshold: float = Field(..., ge=0, le=10, description="Umbral de spread (%)")


class AlphaVantageConfig(BaseModel):
    """Configuración de Alpha Vantage"""
    api_key: Optional[str] = Field(None, description="API Key de Alpha Vantage (oculto por seguridad)")
    enabled: bool = Field(..., description="Habilitar Alpha Vantage")
    cache_ttl: int = Field(..., ge=60, le=3600, description="Tiempo de caché (segundos)")


class FXConfig(BaseModel):
    """Configuración de FX y tasas de cambio"""
    cache_ttl_seconds: int = Field(..., ge=60, le=3600, description="Tiempo de caché (segundos)")
    trm_update_interval: int = Field(..., ge=60, le=3600, description="Intervalo de actualización TRM (segundos)")
    ves_update_interval: int = Field(..., ge=60, le=3600, description="Intervalo de actualización VES (segundos)")
    fallback_rates: Dict[str, float] = Field(..., description="Tasas de cambio por defecto")


class RateLimitConfig(BaseModel):
    """Configuración de rate limiting"""
    rate_limit_per_minute: int = Field(..., ge=1, le=1000, description="Rate limit por minuto")
    rate_limit_binance_api: int = Field(..., ge=1, le=10000, description="Rate limit para API de Binance")


class BrowserConfig(BaseModel):
    """Configuración de browser automation"""
    headless: bool = Field(..., description="Ejecutar browser en modo headless")
    timeout: int = Field(..., ge=1000, le=300000, description="Timeout del browser (ms)")
    pool_size: int = Field(..., ge=1, le=10, description="Tamaño del pool de browsers")


class AppConfigResponse(BaseModel):
    """Respuesta completa de configuración"""
    trading: TradingConfig
    p2p: P2PConfig
    arbitrage: ArbitrageConfig
    notifications: NotificationConfig
    ml: MLConfig
    alpha_vantage: AlphaVantageConfig
    fx: FXConfig
    rate_limiting: RateLimitConfig
    browser: BrowserConfig
    environment: str
    version: str
    debug: bool


class ConfigUpdateRequest(BaseModel):
    """Request para actualizar configuración"""
    trading: Optional[TradingConfig] = None
    p2p: Optional[P2PConfig] = None
    arbitrage: Optional[ArbitrageConfig] = None
    notifications: Optional[NotificationConfig] = None
    ml: Optional[MLConfig] = None
    alpha_vantage: Optional[AlphaVantageConfig] = None
    fx: Optional[FXConfig] = None
    rate_limiting: Optional[RateLimitConfig] = None
    browser: Optional[BrowserConfig] = None


class ConfigSection(BaseModel):
    """Sección de configuración con metadatos"""
    id: str
    name: str
    description: str
    icon: str
    fields: List[str]


class ConfigSectionsResponse(BaseModel):
    """Respuesta con lista de secciones"""
    sections: List[ConfigSection]


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.get("/config", response_model=AppConfigResponse)
async def get_configuration():
    """
    Obtener la configuración actual de la aplicación.
    
    Nota: Las contraseñas y tokens sensibles se ocultan por seguridad.
    Solo se muestran si están configurados (valor booleano).
    """
    try:
        # Ocultar tokens y contraseñas sensibles
        telegram_token_masked = None
        if settings.TELEGRAM_BOT_TOKEN:
            telegram_token_masked = f"{settings.TELEGRAM_BOT_TOKEN[:8]}..." if len(settings.TELEGRAM_BOT_TOKEN) > 8 else "***"
        
        alpha_vantage_key_masked = None
        if settings.ALPHA_VANTAGE_API_KEY:
            alpha_vantage_key_masked = f"{settings.ALPHA_VANTAGE_API_KEY[:8]}..." if len(settings.ALPHA_VANTAGE_API_KEY) > 8 else "***"
        
        return AppConfigResponse(
            trading=TradingConfig(
                trading_mode=settings.TRADING_MODE,
                profit_margin_cop=settings.PROFIT_MARGIN_COP,
                profit_margin_ves=settings.PROFIT_MARGIN_VES,
                min_trade_amount=settings.MIN_TRADE_AMOUNT,
                max_trade_amount=settings.MAX_TRADE_AMOUNT,
                max_daily_trades=settings.MAX_DAILY_TRADES,
                stop_loss_percentage=settings.STOP_LOSS_PERCENTAGE,
            ),
            p2p=P2PConfig(
                monitored_assets=settings.p2p_monitored_assets_list,
                monitored_fiats=settings.p2p_monitored_fiats_list,
                analysis_rows=settings.P2P_ANALYSIS_ROWS,
                top_spreads=settings.P2P_TOP_SPREADS,
                price_cache_seconds=settings.P2P_PRICE_CACHE_SECONDS,
                min_surplus_usdt=settings.P2P_MIN_SURPLUS_USDT,
            ),
            arbitrage=ArbitrageConfig(
                monitored_assets=settings.arbitrage_monitored_assets_list,
                monitored_fiats=settings.arbitrage_monitored_fiats_list,
                top_opportunities=settings.ARBITRAGE_TOP_OPPORTUNITIES,
                min_liquidity_usdt=settings.ARBITRAGE_MIN_LIQUIDITY_USDT,
                min_profit=settings.ARBITRAGE_MIN_PROFIT,
                update_price_interval=settings.UPDATE_PRICE_INTERVAL,
            ),
            notifications=NotificationConfig(
                enable_notifications=settings.ENABLE_NOTIFICATIONS,
                telegram_bot_token=telegram_token_masked,
                telegram_chat_id=settings.TELEGRAM_CHAT_ID if settings.TELEGRAM_CHAT_ID else None,
                email_smtp_server=settings.EMAIL_SMTP_SERVER if settings.EMAIL_SMTP_SERVER else None,
                email_smtp_port=settings.EMAIL_SMTP_PORT,
                email_from=settings.EMAIL_FROM if settings.EMAIL_FROM else None,
            ),
            ml=MLConfig(
                retrain_interval=settings.ML_RETRAIN_INTERVAL,
                min_data_points=settings.ML_MIN_DATA_POINTS,
                confidence_threshold=settings.ML_CONFIDENCE_THRESHOLD,
                spread_threshold=settings.SPREAD_THRESHOLD,
            ),
            alpha_vantage=AlphaVantageConfig(
                api_key=alpha_vantage_key_masked,
                enabled=settings.ALPHA_VANTAGE_ENABLED,
                cache_ttl=settings.ALPHA_VANTAGE_CACHE_TTL,
            ),
            fx=FXConfig(
                cache_ttl_seconds=settings.FX_CACHE_TTL_SECONDS,
                trm_update_interval=settings.TRM_UPDATE_INTERVAL,
                ves_update_interval=settings.VES_UPDATE_INTERVAL,
                fallback_rates=settings.FX_FALLBACK_RATES,
            ),
            rate_limiting=RateLimitConfig(
                rate_limit_per_minute=settings.RATE_LIMIT_PER_MINUTE,
                rate_limit_binance_api=settings.RATE_LIMIT_BINANCE_API,
            ),
            browser=BrowserConfig(
                headless=settings.BROWSER_HEADLESS,
                timeout=settings.BROWSER_TIMEOUT,
                pool_size=settings.BROWSER_POOL_SIZE,
            ),
            environment=settings.ENVIRONMENT,
            version=settings.VERSION,
            debug=settings.DEBUG,
        )
    except Exception as e:
        logger.error(f"Error getting configuration: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error obteniendo configuración: {str(e)}")


@router.put("/config", response_model=AppConfigResponse)
async def update_configuration(config: ConfigUpdateRequest, db: Session = Depends(get_db)):
    """
    Actualizar configuración de la aplicación.
    
    ✅ CONFIGURACIÓN PERSISTENTE:
    - Los cambios se guardan en la base de datos y persisten después de reiniciar
    - La configuración de trading se carga automáticamente desde la base de datos al iniciar
    - Los cambios se aplican inmediatamente en memoria y se guardan permanentemente
    
    ⚠️ NOTA DE SEGURIDAD:
    - Las configuraciones sensibles (tokens, contraseñas) NO se pueden modificar via API
    - Para cambiar tokens/contraseñas, modifica el archivo .env y reinicia el servidor
    """
    try:
        config_service = ConfigService(db)
        
        # Actualizar solo las secciones que se envían
        if config.trading:
            # Actualizar configuración de trading en memoria
            settings.TRADING_MODE = config.trading.trading_mode
            settings.PROFIT_MARGIN_COP = config.trading.profit_margin_cop
            settings.PROFIT_MARGIN_VES = config.trading.profit_margin_ves
            settings.MIN_TRADE_AMOUNT = config.trading.min_trade_amount
            settings.MAX_TRADE_AMOUNT = config.trading.max_trade_amount
            settings.MAX_DAILY_TRADES = config.trading.max_daily_trades
            settings.STOP_LOSS_PERCENTAGE = config.trading.stop_loss_percentage
            
            # Guardar en base de datos (persistente)
            config_service.set_config("trading.mode", config.trading.trading_mode, "Modo de trading (manual, auto, hybrid)")
            config_service.set_config("trading.profit_margin_cop", config.trading.profit_margin_cop, "Margen de ganancia para COP (%)")
            config_service.set_config("trading.profit_margin_ves", config.trading.profit_margin_ves, "Margen de ganancia para VES (%)")
            config_service.set_config("trading.min_trade_amount", config.trading.min_trade_amount, "Monto mínimo de trade (USD)")
            config_service.set_config("trading.max_trade_amount", config.trading.max_trade_amount, "Monto máximo de trade (USD)")
            config_service.set_config("trading.max_daily_trades", config.trading.max_daily_trades, "Máximo de trades por día")
            config_service.set_config("trading.stop_loss_percentage", config.trading.stop_loss_percentage, "Stop loss (%)")
            
            logger.info(f"Trading configuration updated and persisted: mode={config.trading.trading_mode}")
        
        if config.p2p:
            # Actualizar configuración P2P
            settings.P2P_MONITORED_ASSETS = ",".join(config.p2p.monitored_assets)
            settings.P2P_MONITORED_FIATS = ",".join(config.p2p.monitored_fiats)
            settings.P2P_ANALYSIS_ROWS = config.p2p.analysis_rows
            settings.P2P_TOP_SPREADS = config.p2p.top_spreads
            settings.P2P_PRICE_CACHE_SECONDS = config.p2p.price_cache_seconds
            settings.P2P_MIN_SURPLUS_USDT = config.p2p.min_surplus_usdt
        
        if config.arbitrage:
            # Actualizar configuración de arbitraje
            settings.ARBITRAGE_MONITORED_ASSETS = ",".join(config.arbitrage.monitored_assets)
            settings.ARBITRAGE_MONITORED_FIATS = ",".join(config.arbitrage.monitored_fiats)
            settings.ARBITRAGE_TOP_OPPORTUNITIES = config.arbitrage.top_opportunities
            settings.ARBITRAGE_MIN_LIQUIDITY_USDT = config.arbitrage.min_liquidity_usdt
            settings.ARBITRAGE_MIN_PROFIT = config.arbitrage.min_profit
            settings.UPDATE_PRICE_INTERVAL = config.arbitrage.update_price_interval
        
        if config.notifications:
            # Actualizar configuración de notificaciones
            # NOTA: No actualizamos tokens sensibles por seguridad
            settings.ENABLE_NOTIFICATIONS = config.notifications.enable_notifications
            if config.notifications.telegram_chat_id:
                settings.TELEGRAM_CHAT_ID = config.notifications.telegram_chat_id
            if config.notifications.email_smtp_server:
                settings.EMAIL_SMTP_SERVER = config.notifications.email_smtp_server
            if config.notifications.email_smtp_port:
                settings.EMAIL_SMTP_PORT = config.notifications.email_smtp_port
            if config.notifications.email_from:
                settings.EMAIL_FROM = config.notifications.email_from
        
        if config.ml:
            # Actualizar configuración de ML
            settings.ML_RETRAIN_INTERVAL = config.ml.retrain_interval
            settings.ML_MIN_DATA_POINTS = config.ml.min_data_points
            settings.ML_CONFIDENCE_THRESHOLD = config.ml.confidence_threshold
            settings.SPREAD_THRESHOLD = config.ml.spread_threshold
        
        if config.alpha_vantage:
            # Actualizar configuración de Alpha Vantage
            settings.ALPHA_VANTAGE_ENABLED = config.alpha_vantage.enabled
            settings.ALPHA_VANTAGE_CACHE_TTL = config.alpha_vantage.cache_ttl
            # NOTA: No actualizamos API key por seguridad (debe hacerse via .env)
        
        if config.fx:
            # Actualizar configuración de FX
            settings.FX_CACHE_TTL_SECONDS = config.fx.cache_ttl_seconds
            settings.TRM_UPDATE_INTERVAL = config.fx.trm_update_interval
            settings.VES_UPDATE_INTERVAL = config.fx.ves_update_interval
            settings.FX_FALLBACK_RATES = config.fx.fallback_rates
        
        if config.rate_limiting:
            # Actualizar configuración de rate limiting
            settings.RATE_LIMIT_PER_MINUTE = config.rate_limiting.rate_limit_per_minute
            settings.RATE_LIMIT_BINANCE_API = config.rate_limiting.rate_limit_binance_api
        
        if config.browser:
            # Actualizar configuración de browser
            settings.BROWSER_HEADLESS = config.browser.headless
            settings.BROWSER_TIMEOUT = config.browser.timeout
            settings.BROWSER_POOL_SIZE = config.browser.pool_size
        
        logger.info("Configuration updated successfully")
        
        # Retornar configuración actualizada
        return await get_configuration()
        
    except Exception as e:
        logger.error(f"Error updating configuration: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error actualizando configuración: {str(e)}")


@router.get("/config/sections", response_model=ConfigSectionsResponse)
async def get_config_sections():
    """
    Obtener lista de secciones de configuración disponibles.
    Útil para el frontend para construir la UI dinámicamente.
    """
    sections = [
        ConfigSection(
            id="trading",
            name="Trading",
            description="Configuración de trading y márgenes de ganancia",
            icon="💰",
            fields=[
                "trading_mode", "profit_margin_cop", "profit_margin_ves",
                "min_trade_amount", "max_trade_amount", "max_daily_trades", "stop_loss_percentage"
            ]
        ),
        ConfigSection(
            id="p2p",
            name="P2P",
            description="Configuración de monitoreo P2P",
            icon="🔄",
            fields=[
                "monitored_assets", "monitored_fiats", "analysis_rows",
                "top_spreads", "price_cache_seconds", "min_surplus_usdt"
            ]
        ),
        ConfigSection(
            id="arbitrage",
            name="Arbitraje",
            description="Configuración de arbitraje",
            icon="⚡",
            fields=[
                "monitored_assets", "monitored_fiats", "top_opportunities",
                "min_liquidity_usdt", "min_profit", "update_price_interval"
            ]
        ),
        ConfigSection(
            id="notifications",
            name="Notificaciones",
            description="Configuración de notificaciones (Telegram, Email)",
            icon="📧",
            fields=[
                "enable_notifications", "telegram_bot_token", "telegram_chat_id",
                "email_smtp_server", "email_smtp_port", "email_from"
            ]
        ),
        ConfigSection(
            id="ml",
            name="Machine Learning",
            description="Configuración de modelos ML",
            icon="🤖",
            fields=[
                "retrain_interval", "min_data_points", "confidence_threshold", "spread_threshold"
            ]
        ),
        ConfigSection(
            id="alpha_vantage",
            name="Alpha Vantage",
            description="Configuración de Alpha Vantage API",
            icon="📊",
            fields=[
                "api_key", "enabled", "cache_ttl"
            ]
        ),
        ConfigSection(
            id="fx",
            name="FX y Tasas",
            description="Configuración de tasas de cambio",
            icon="💱",
            fields=[
                "cache_ttl_seconds", "trm_update_interval", "ves_update_interval", "fallback_rates"
            ]
        ),
        ConfigSection(
            id="rate_limiting",
            name="Rate Limiting",
            description="Configuración de límites de tasa",
            icon="⏱️",
            fields=[
                "rate_limit_per_minute", "rate_limit_binance_api"
            ]
        ),
        ConfigSection(
            id="browser",
            name="Browser Automation",
            description="Configuración de automatización de navegador",
            icon="🌐",
            fields=[
                "headless", "timeout", "pool_size"
            ]
        )
    ]
    
    return ConfigSectionsResponse(sections=sections)

