"""
Bot de trading automatizado para Binance P2P.

IMPORTANTE:
Este bot realiza análisis y puede sugerir operaciones.
Las operaciones automáticas requieren configuración adicional
y cumplimiento de términos de servicio de Binance.
"""
import structlog
from typing import Dict, Optional
from datetime import datetime

from app.core.database import SessionLocal
from app.core.config import settings
from app.services.binance_service import BinanceService
from app.models.trade import Trade, TradeType, TradeStatus
from app.models.alert import Alert, AlertType, AlertPriority

logger = structlog.get_logger()


class TradingBot:
    """
    Bot de trading para operaciones P2P.

    Modos de operación:
    - manual: Solo análisis y alertas
    - auto: Ejecuta operaciones automáticamente
    - hybrid: Requiere confirmación para operaciones grandes
    """

    def __init__(self):
        self.binance_service = BinanceService()
        self.db = SessionLocal()
        self.mode = settings.TRADING_MODE

    def __del__(self):
        """Cerrar conexión a DB"""
        if hasattr(self, 'db'):
            self.db.close()

    async def execute_trading_cycle(self) -> Dict:
        """
        Ejecutar un ciclo completo de trading.

        Returns:
            Resultado del ciclo
        """
        logger.info("Trading cycle started", mode=self.mode)

        try:
            # 1. Verificar límites diarios
            if not self._check_daily_limits():
                logger.warning("Daily trading limits reached")
                return {"status": "skipped", "reason": "daily_limit_reached"}

            # 2. Analizar mercado
            opportunities = await self._analyze_market()

            if not opportunities:
                logger.info("No trading opportunities found")
                return {"status": "completed", "opportunities": 0}

            # 3. Evaluar y ejecutar oportunidades
            executed = 0
            for opportunity in opportunities:
                if self.mode == "manual":
                    # Solo crear alerta
                    self._create_opportunity_alert(opportunity)
                elif self.mode == "auto":
                    # Ejecutar automáticamente
                    success = await self._execute_trade(opportunity)
                    if success:
                        executed += 1
                elif self.mode == "hybrid":
                    # Ejecutar solo si es menor al límite
                    if opportunity["amount"] <= settings.MIN_TRADE_AMOUNT * 2:
                        success = await self._execute_trade(opportunity)
                        if success:
                            executed += 1
                    else:
                        self._create_opportunity_alert(opportunity)

            logger.info(
                "Trading cycle completed",
                opportunities=len(opportunities),
                executed=executed
            )

            return {
                "status": "completed",
                "opportunities": len(opportunities),
                "executed": executed
            }

        except Exception as e:
            logger.error("Error in trading cycle", error=str(e))
            return {"status": "error", "error": str(e)}

    async def _analyze_market(self) -> list:
        """
        Analizar mercado para detectar oportunidades.

        Returns:
            Lista de oportunidades de trading
        """
        opportunities = []

        for fiat in ["COP", "VES"]:
            try:
                depth = await self.binance_service.get_market_depth("USDT", fiat)

                best_buy = depth.get("best_buy")
                best_sell = depth.get("best_sell")

                if not best_buy or not best_sell:
                    continue

                spread = depth.get("spread_percent", 0)

                # Verificar si el spread es favorable
                min_margin = settings.PROFIT_MARGIN_COP if fiat == "COP" else settings.PROFIT_MARGIN_VES

                if spread >= min_margin:
                    # Calcular ganancia potencial
                    potential_profit = (spread - min_margin) / 100

                    opportunity = {
                        "asset": "USDT",
                        "fiat": fiat,
                        "buy_price": best_buy["price"],
                        "sell_price": best_sell["price"],
                        "spread": spread,
                        "potential_profit_percent": potential_profit * 100,
                        "amount": min(best_buy["available"], best_sell["available"], settings.MAX_TRADE_AMOUNT),
                        "merchant_buy": best_buy["merchant"],
                        "merchant_sell": best_sell["merchant"]
                    }

                    opportunities.append(opportunity)

                    logger.info(
                        "Opportunity detected",
                        fiat=fiat,
                        spread=spread,
                        profit=potential_profit
                    )

            except Exception as e:
                logger.error("Error analyzing market for fiat", fiat=fiat, error=str(e))

        # Ordenar por profit potencial
        opportunities.sort(key=lambda x: x["potential_profit_percent"], reverse=True)

        return opportunities

    async def _execute_trade(self, opportunity: Dict) -> bool:
        """
        Ejecutar una operación de trading.

        NOTA: Esta es una implementación de ejemplo.
        En producción, necesitarías integración completa con Binance API.

        Args:
            opportunity: Datos de la oportunidad

        Returns:
            True si la operación fue exitosa
        """
        try:
            # Calcular cantidad
            amount = min(
                opportunity["amount"],
                settings.MAX_TRADE_AMOUNT
            )

            if amount < settings.MIN_TRADE_AMOUNT:
                logger.warning("Amount below minimum", amount=amount)
                return False

            # Crear registro de trade
            trade = Trade(
                trade_type=TradeType.BUY,  # Ejemplo: siempre compramos primero
                status=TradeStatus.PENDING,
                asset=opportunity["asset"],
                fiat=opportunity["fiat"],
                crypto_amount=amount,
                fiat_amount=amount * opportunity["buy_price"],
                price=opportunity["buy_price"],
                profit_margin=opportunity["potential_profit_percent"],
                is_automated=True,
                notes=f"Auto-trade: Spread {opportunity['spread']}%"
            )

            self.db.add(trade)
            self.db.commit()

            logger.info(
                "Trade created",
                trade_id=trade.id,
                fiat=opportunity["fiat"],
                amount=amount
            )

            # TODO: Implementar ejecución real en Binance
            # Por ahora, solo simulamos
            # En producción:
            # 1. Crear orden en Binance P2P
            # 2. Monitorear estado de la orden
            # 3. Confirmar pago
            # 4. Actualizar estado del trade

            # Simular operación exitosa
            trade.status = TradeStatus.COMPLETED
            trade.completed_at = datetime.utcnow()
            trade.actual_profit = (amount * opportunity["buy_price"]) * (opportunity["potential_profit_percent"] / 100)

            self.db.commit()

            # Crear alerta de operación completada
            alert = Alert(
                alert_type=AlertType.TRADE_COMPLETED,
                priority=AlertPriority.HIGH,
                title=f"Operación completada: {opportunity['fiat']}",
                message=f"Trade #{trade.id} completado exitosamente. "
                        f"Ganancia: ${trade.actual_profit:.2f}",
                asset=trade.asset,
                fiat=trade.fiat
            )
            self.db.add(alert)
            self.db.commit()

            return True

        except Exception as e:
            logger.error("Error executing trade", error=str(e))
            self.db.rollback()
            return False

    def _check_daily_limits(self) -> bool:
        """
        Verificar si no se han excedido los límites diarios.

        Returns:
            True si está dentro de los límites
        """
        from datetime import datetime, timedelta

        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

        trades_today = self.db.query(Trade).filter(
            Trade.created_at >= today,
            Trade.is_automated == True
        ).count()

        if trades_today >= settings.MAX_DAILY_TRADES:
            return False

        return True

    def _create_opportunity_alert(self, opportunity: Dict):
        """
        Crear alerta de oportunidad de trading.

        Args:
            opportunity: Datos de la oportunidad
        """
        alert = Alert(
            alert_type=AlertType.SPREAD_OPPORTUNITY,
            priority=AlertPriority.HIGH,
            title=f"Oportunidad en {opportunity['fiat']}",
            message=f"Spread de {opportunity['spread']:.2f}% detectado. "
                    f"Ganancia potencial: {opportunity['potential_profit_percent']:.2f}%. "
                    f"Compra: ${opportunity['buy_price']:.2f}, Venta: ${opportunity['sell_price']:.2f}",
            asset=opportunity["asset"],
            fiat=opportunity["fiat"],
            price=opportunity["buy_price"],
            percentage=opportunity["potential_profit_percent"]
        )

        self.db.add(alert)
        self.db.commit()

        logger.info("Opportunity alert created", fiat=opportunity["fiat"])
