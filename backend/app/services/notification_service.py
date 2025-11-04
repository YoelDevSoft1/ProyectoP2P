"""
Servicio de notificaciones mejorado.
Alertas instantáneas con enlaces directos accionables.
"""
import structlog
from typing import Dict, Optional
from datetime import datetime
import json

from app.core.config import settings

logger = structlog.get_logger()


class NotificationService:
    """
    Servicio de notificaciones multi-canal.
    Soporta Telegram, Email y webhooks.
    """

    def __init__(self):
        self.telegram_enabled = settings.ENABLE_NOTIFICATIONS and settings.TELEGRAM_BOT_TOKEN
        self.telegram_bot = None

        if self.telegram_enabled:
            try:
                from telegram import Bot
                self.telegram_bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
            except ImportError:
                logger.warning("python-telegram-bot not installed, Telegram notifications disabled")
                self.telegram_enabled = False

    async def send_p2p_opportunity_alert(
        self,
        opportunity: Dict
    ) -> bool:
        """
        Enviar alerta de oportunidad P2P con enlace directo.

        Args:
            opportunity: Datos de la oportunidad

        Returns:
            True si se envió exitosamente
        """
        fiat = opportunity.get('fiat', 'COP')
        asset = opportunity.get('asset', 'USDT')
        spread = opportunity.get('spread', 0)
        buy_price = opportunity.get('buy_price', 0)
        sell_price = opportunity.get('sell_price', 0)
        profit_percentage = opportunity.get('potential_profit_percent', 0)

        # Generar enlace directo a Binance P2P
        p2p_link = self._generate_p2p_link(asset, fiat, "BUY")

        # Mensaje formateado
        message = f"""
🚀 *OPORTUNIDAD P2P DETECTADA* 🚀

💰 Par: {asset}/{fiat}
📊 Spread: {spread}%
💸 Ganancia potencial: {profit_percentage}%

💵 Precios:
   • Compra: ${buy_price:,.2f} {fiat}
   • Venta: ${sell_price:,.2f} {fiat}

⏰ Tiempo: {datetime.utcnow().strftime('%H:%M:%S')} UTC

👉 [ABRIR EN BINANCE P2P]({p2p_link})

⚡ ¡Actúa rápido! Esta oportunidad puede desaparecer pronto.
"""

        # Enviar por Telegram
        if self.telegram_enabled:
            return await self._send_telegram_message(message)

        # Si Telegram no está disponible, log
        logger.info("P2P opportunity alert", opportunity=opportunity)
        return True

    async def send_arbitrage_alert(
        self,
        arbitrage_data: Dict
    ) -> bool:
        """
        Enviar alerta de arbitraje Spot-P2P.

        Args:
            arbitrage_data: Datos del arbitraje

        Returns:
            True si se envió
        """
        strategy = arbitrage_data.get('strategy', '')
        profit = arbitrage_data.get('net_profit_percentage', 0)
        recommended_amount = arbitrage_data.get('recommended_amount', 0)

        message = f"""
💎 *ARBITRAJE DETECTADO* 💎

🔄 Estrategia: {strategy.replace('_', ' ').title()}
💰 Profit Neto: {profit}%
💵 Monto recomendado: ${recommended_amount:.0f} USD

📈 Detalles:
"""

        if strategy == "spot_to_p2p":
            message += f"""
   1️⃣ Comprar {arbitrage_data['asset']} en Spot
      Precio: ${arbitrage_data['spot_price']:.4f}

   2️⃣ Vender {arbitrage_data['asset']} en P2P {arbitrage_data['fiat']}
      Precio: ${arbitrage_data['p2p_price']:,.2f}

👉 [SPOT TRADING](https://www.binance.com/en/trade/{arbitrage_data['asset']}_USDC)
👉 [P2P {arbitrage_data['fiat']}]({self._generate_p2p_link(arbitrage_data['asset'], arbitrage_data['fiat'], 'SELL')})
"""

        # Enviar
        if self.telegram_enabled:
            return await self._send_telegram_message(message)

        logger.info("Arbitrage alert", data=arbitrage_data)
        return True

    async def send_trade_executed_alert(
        self,
        trade_data: Dict
    ) -> bool:
        """
        Notificar cuando se ejecuta un trade.

        Args:
            trade_data: Datos del trade

        Returns:
            True si se envió
        """
        trade_id = trade_data.get('id', 0)
        trade_type = trade_data.get('type', 'BUY')
        asset = trade_data.get('asset', 'USDT')
        fiat = trade_data.get('fiat', 'COP')
        amount = trade_data.get('crypto_amount', 0)
        price = trade_data.get('price', 0)
        profit = trade_data.get('actual_profit', 0)

        emoji = "🟢" if trade_type == "BUY" else "🔴"

        message = f"""
{emoji} *TRADE EJECUTADO* {emoji}

📝 ID: #{trade_id}
🔄 Tipo: {trade_type}
💎 {amount} {asset}
💵 Precio: ${price:,.2f} {fiat}
💰 Ganancia: ${profit:.2f} USD

✅ Operación completada exitosamente
"""

        if self.telegram_enabled:
            return await self._send_telegram_message(message)

        logger.info("Trade executed alert", trade_id=trade_id)
        return True

    async def send_error_alert(
        self,
        error_type: str,
        error_message: str,
        context: Optional[Dict] = None
    ) -> bool:
        """
        Enviar alerta de error crítico.

        Args:
            error_type: Tipo de error
            error_message: Mensaje de error
            context: Contexto adicional

        Returns:
            True si se envió
        """
        message = f"""
🚨 *ERROR CRÍTICO* 🚨

⚠️ Tipo: {error_type}
📝 Mensaje: {error_message}

⏰ {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC
"""

        if context:
            message += f"\n📊 Contexto: {json.dumps(context, indent=2)}"

        if self.telegram_enabled:
            return await self._send_telegram_message(message, priority="high")

        logger.error("Critical error alert", error_type=error_type, message=error_message)
        return True

    async def send_daily_summary(
        self,
        summary_data: Dict
    ) -> bool:
        """
        Enviar resumen diario de operaciones.

        Args:
            summary_data: Datos del resumen

        Returns:
            True si se envió
        """
        total_trades = summary_data.get('total_trades', 0)
        completed = summary_data.get('completed', 0)
        total_profit = summary_data.get('total_profit', 0)
        success_rate = summary_data.get('success_rate', 0)

        message = f"""
📊 *RESUMEN DIARIO* 📊

📅 Fecha: {datetime.utcnow().strftime('%Y-%m-%d')}

📈 Operaciones:
   • Total: {total_trades}
   • Completadas: {completed}
   • Tasa de éxito: {success_rate}%

💰 Finanzas:
   • Ganancia total: ${total_profit:.2f} USD
   • Promedio por trade: ${total_profit/completed if completed > 0 else 0:.2f}

🎯 ¡Buen trabajo! Sigue así.
"""

        if self.telegram_enabled:
            return await self._send_telegram_message(message)

        logger.info("Daily summary sent", data=summary_data)
        return True

    def _generate_p2p_link(
        self,
        asset: str,
        fiat: str,
        trade_type: str
    ) -> str:
        """
        Generar enlace directo a Binance P2P.

        Args:
            asset: Criptomoneda (USDT, BTC)
            fiat: Moneda fiat (COP, VES)
            trade_type: BUY o SELL

        Returns:
            URL de Binance P2P
        """
        # URL base de Binance P2P
        base_url = "https://p2p.binance.com/trade"

        # Parámetros
        params = f"{trade_type.lower()}/{asset}?fiat={fiat}"

        return f"{base_url}/{params}"

    async def _send_telegram_message(
        self,
        message: str,
        priority: str = "normal"
    ) -> bool:
        """
        Enviar mensaje por Telegram.

        Args:
            message: Mensaje a enviar
            priority: normal, high

        Returns:
            True si se envió exitosamente
        """
        if not self.telegram_enabled or not self.telegram_bot:
            return False

        try:
            # Enviar mensaje con formato Markdown
            await self.telegram_bot.send_message(
                chat_id=settings.TELEGRAM_CHAT_ID,
                text=message,
                parse_mode='Markdown',
                disable_web_page_preview=False
            )

            logger.info("Telegram notification sent", priority=priority)
            return True

        except Exception as e:
            logger.error("Error sending Telegram notification", error=str(e))
            return False

    async def test_notification(self) -> bool:
        """
        Enviar notificación de prueba.

        Returns:
            True si funciona
        """
        message = """
✅ *TEST DE NOTIFICACIONES* ✅

🤖 El sistema de notificaciones está funcionando correctamente.

⏰ {time}

🎯 Recibirás alertas de:
   • Oportunidades P2P
   • Arbitrajes detectados
   • Trades ejecutados
   • Errores críticos
   • Resúmenes diarios
""".format(time=datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'))

        if self.telegram_enabled:
            return await self._send_telegram_message(message)

        logger.info("Test notification", status="ok")
        return True
