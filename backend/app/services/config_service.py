"""
Servicio para manejar la configuración persistente de la aplicación.
"""
from sqlalchemy.orm import Session
from typing import Any, Optional, Dict
import logging

from app.models.app_config import AppConfig
from app.core.config import settings

logger = logging.getLogger(__name__)


class ConfigService:
    """Servicio para gestionar configuración persistente"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_config(self, key: str, default: Any = None) -> Any:
        """
        Obtener un valor de configuración.
        
        Args:
            key: Clave de configuración (ej: "trading.mode")
            default: Valor por defecto si no existe
        
        Returns:
            Valor de la configuración o default
        """
        try:
            config = self.db.query(AppConfig).filter(AppConfig.key == key).first()
            if config:
                return config.get_value()
            return default
        except Exception as e:
            logger.error(f"Error getting config {key}: {e}", exc_info=True)
            return default
    
    def set_config(self, key: str, value: Any, description: Optional[str] = None, is_sensitive: bool = False) -> AppConfig:
        """
        Establecer un valor de configuración.
        
        Args:
            key: Clave de configuración
            value: Valor a guardar
            description: Descripción de la configuración
            is_sensitive: Si es sensible (no se muestra en logs)
        
        Returns:
            AppConfig actualizado o creado
        """
        try:
            config = self.db.query(AppConfig).filter(AppConfig.key == key).first()
            
            if config:
                # Actualizar existente
                config.set_value(value)
                if description:
                    config.description = description
                config.is_sensitive = is_sensitive
            else:
                # Crear nuevo
                config = AppConfig(
                    key=key,
                    description=description,
                    is_sensitive=is_sensitive
                )
                config.set_value(value)
                self.db.add(config)
            
            self.db.commit()
            self.db.refresh(config)
            
            if not is_sensitive:
                logger.info(f"Config updated: {key} = {value}")
            
            return config
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error setting config {key}: {e}", exc_info=True)
            raise
    
    def delete_config(self, key: str) -> bool:
        """
        Eliminar una configuración.
        
        Args:
            key: Clave de configuración
        
        Returns:
            True si se eliminó, False si no existía
        """
        try:
            config = self.db.query(AppConfig).filter(AppConfig.key == key).first()
            if config:
                self.db.delete(config)
                self.db.commit()
                logger.info(f"Config deleted: {key}")
                return True
            return False
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error deleting config {key}: {e}", exc_info=True)
            return False
    
    def get_all_configs(self) -> Dict[str, Any]:
        """
        Obtener todas las configuraciones.
        
        Returns:
            Diccionario con todas las configuraciones
        """
        try:
            configs = self.db.query(AppConfig).all()
            return {config.key: config.get_value() for config in configs}
        except Exception as e:
            logger.error(f"Error getting all configs: {e}", exc_info=True)
            return {}
    
    def load_trading_config_to_settings(self):
        """
        Cargar configuración de trading desde la base de datos a settings.
        Se ejecuta al iniciar la aplicación.
        """
        try:
            # Cargar modo de trading
            trading_mode = self.get_config("trading.mode", settings.TRADING_MODE)
            if trading_mode and trading_mode in ["manual", "auto", "hybrid"]:
                settings.TRADING_MODE = trading_mode
                logger.info(f"Loaded trading mode from DB: {trading_mode}")
            
            # Cargar márgenes de ganancia
            profit_margin_cop = self.get_config("trading.profit_margin_cop", settings.PROFIT_MARGIN_COP)
            if profit_margin_cop is not None:
                settings.PROFIT_MARGIN_COP = float(profit_margin_cop)
            
            profit_margin_ves = self.get_config("trading.profit_margin_ves", settings.PROFIT_MARGIN_VES)
            if profit_margin_ves is not None:
                settings.PROFIT_MARGIN_VES = float(profit_margin_ves)
            
            # Cargar límites de trade
            min_trade_amount = self.get_config("trading.min_trade_amount", settings.MIN_TRADE_AMOUNT)
            if min_trade_amount is not None:
                settings.MIN_TRADE_AMOUNT = float(min_trade_amount)
            
            max_trade_amount = self.get_config("trading.max_trade_amount", settings.MAX_TRADE_AMOUNT)
            if max_trade_amount is not None:
                settings.MAX_TRADE_AMOUNT = float(max_trade_amount)
            
            # Cargar límites diarios
            max_daily_trades = self.get_config("trading.max_daily_trades", settings.MAX_DAILY_TRADES)
            if max_daily_trades is not None:
                settings.MAX_DAILY_TRADES = int(max_daily_trades)
            
            # Cargar stop loss
            stop_loss = self.get_config("trading.stop_loss_percentage", settings.STOP_LOSS_PERCENTAGE)
            if stop_loss is not None:
                settings.STOP_LOSS_PERCENTAGE = float(stop_loss)
            
            logger.info("Trading configuration loaded from database")
        except Exception as e:
            logger.error(f"Error loading trading config from DB: {e}", exc_info=True)
    
    def save_trading_config_from_settings(self):
        """
        Guardar configuración de trading desde settings a la base de datos.
        """
        try:
            self.set_config("trading.mode", settings.TRADING_MODE, "Modo de trading (manual, auto, hybrid)")
            self.set_config("trading.profit_margin_cop", settings.PROFIT_MARGIN_COP, "Margen de ganancia para COP (%)")
            self.set_config("trading.profit_margin_ves", settings.PROFIT_MARGIN_VES, "Margen de ganancia para VES (%)")
            self.set_config("trading.min_trade_amount", settings.MIN_TRADE_AMOUNT, "Monto mínimo de trade (USD)")
            self.set_config("trading.max_trade_amount", settings.MAX_TRADE_AMOUNT, "Monto máximo de trade (USD)")
            self.set_config("trading.max_daily_trades", settings.MAX_DAILY_TRADES, "Máximo de trades por día")
            self.set_config("trading.stop_loss_percentage", settings.STOP_LOSS_PERCENTAGE, "Stop loss (%)")
            logger.info("Trading configuration saved to database")
        except Exception as e:
            logger.error(f"Error saving trading config to DB: {e}", exc_info=True)
            raise

