"""
Servicio de notificaciones mejorado.
Alertas instantáneas con enlaces directos accionables.
"""
import structlog
from typing import Dict, Optional, List
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
        profit_percentage = opportunity.get('potential_profit_percent', spread)
        rank = opportunity.get('rank', 1)
        buy_available = opportunity.get('buy_available', 0)
        sell_available = opportunity.get('sell_available', 0)
        buy_merchant = opportunity.get('buy_merchant') or 'Desconocido'
        sell_merchant = opportunity.get('sell_merchant') or 'Desconocido'
        buy_methods = opportunity.get('buy_payment_methods') or []
        sell_methods = opportunity.get('sell_payment_methods') or []

        # Generar enlace directo a Binance P2P
        p2p_link = self._generate_p2p_link(asset, fiat, "BUY")

        buy_methods_text = ', '.join(buy_methods) if buy_methods else 'Diversos'
        sell_methods_text = ', '.join(sell_methods) if sell_methods else 'Diversos'

        # Mensaje formateado
        message = f"""
🚀 *OPORTUNIDAD P2P DETECTADA* 🚀

💰 Par: {asset}/{fiat}
📊 Spread: {spread}%
💸 Ganancia potencial: {profit_percentage}%
🏅 Ranking: #{rank}

💵 Precios:
   • Compra: ${buy_price:,.2f} {fiat}
     👤 {buy_merchant} | Métodos: {buy_methods_text}
     📦 Disponible: {buy_available:,.2f} {asset}
   • Venta: ${sell_price:,.2f} {fiat}
     👤 {sell_merchant} | Métodos: {sell_methods_text}
     📦 Demanda: {sell_available:,.2f} {asset}

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

    async def send_arbitrage_digest(
        self,
        opportunities: List[Dict]
    ) -> bool:
        """Enviar resumen con las mejores oportunidades de arbitraje."""
        if not opportunities:
            return False

        def _format_percent(value: Optional[float]) -> str:
            try:
                if value is None:
                    return "0.00%"
                return f"{float(value):.2f}%"
            except (TypeError, ValueError):  # pragma: no cover - defensivo
                return "0.00%"

        def _format_price(value: Optional[float], suffix: str = "", decimals: int = 2) -> str:
            try:
                if value is None:
                    return f"{0:.{decimals}f}{suffix}"
                return f"{float(value):,.{decimals}f}{suffix}"
            except (TypeError, ValueError):
                return f"{0:.{decimals}f}{suffix}"

        lines = ["📈 *TOP OPORTUNIDADES DE ARBITRAJE* 📈", ""]

        for idx, opportunity in enumerate(opportunities, start=1):
            strategy = opportunity.get("strategy", "desconocida").replace("_", " ").title()
            label = opportunity.get("label") or opportunity.get("asset", "N/A")
            profit_value = (
                opportunity.get("net_profit_percentage")
                or opportunity.get("profit_percentage")
                or opportunity.get("score")
            )
            liquidity_value = opportunity.get("liquidity")
            liquidity_asset = opportunity.get("liquidity_asset") or opportunity.get("asset", "USDT")
            liquidity_text = ""
            if liquidity_value and liquidity_value > 0:
                liquidity_text = f" | Liquidez: {float(liquidity_value):,.2f} {liquidity_asset}"

            lines.append(f"{idx}. *{label}* — {strategy}\n   Profit estimado: {_format_percent(profit_value)}{liquidity_text}")

            details = opportunity.get("details", {})
            if opportunity.get("strategy") == "spot_to_p2p":
                spot_price = details.get("spot_price_usd")
                lines.append(
                    "   Spot: "
                    + f"${_format_price(spot_price, decimals=4)} | P2P: "
                    + _format_price(details.get('p2p_sell_price_fiat'), f" {opportunity.get('fiat', '')}")
                )
            elif opportunity.get("strategy") == "cross_currency":
                buy = details.get("buy_quote", {})
                sell = details.get("sell_quote", {})
                fiat_from = details.get("fiat_from")
                fiat_to = details.get("fiat_to")
                lines.append(
                    "   Comprar en "
                    + f"{fiat_from}: {_format_price(buy.get('price'), f' {fiat_from}')}"
                    + " | Vender en "
                    + f"{fiat_to}: {_format_price(sell.get('price'), f' {fiat_to}')}"
                )
            elif opportunity.get("strategy") == "triangle_arbitrage":
                lines.append(f"   Ruta: {opportunity.get('label')}")

            lines.append("")

        lines.append(f"⏰ Actualizado: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")

        message = "\n".join(lines)

        if self.telegram_enabled:
            return await self._send_telegram_message(message)

        logger.info("Arbitrage digest", opportunities=opportunities)
        return True

    async def send_spread_digest(
        self,
        opportunities: List[Dict]
    ) -> bool:
        """Enviar resumen con los mejores spreads encontrados en P2P."""
        if not opportunities:
            return False

        def _format_percent(value: Optional[float]) -> str:
            try:
                if value is None:
                    return "0.00%"
                return f"{float(value):.2f}%"
            except (TypeError, ValueError):
                return "0.00%"

        def _format_price(value: Optional[float], fiat: str = "") -> str:
            try:
                suffix = f" {fiat}" if fiat else ""
                if value is None:
                    return f"0.00{suffix}"
                return f"{float(value):,.2f}{suffix}"
            except (TypeError, ValueError):
                suffix = f" {fiat}" if fiat else ""
                return f"0.00{suffix}"

        def _extract_data(item: Dict) -> Dict:
            data = {
                "asset": item.get("asset"),
                "fiat": item.get("fiat"),
                "spread": item.get("spread"),
                "op": item.get("opportunity_data") or item,
            }
            if not data["asset"]:
                data["asset"] = data["op"].get("asset")
            if not data["fiat"]:
                data["fiat"] = data["op"].get("fiat")
            if data["spread"] is None:
                data["spread"] = data["op"].get("spread")
            data["rank"] = data["op"].get("rank")
            return data

        sorted_ops: List[Dict] = []
        for item in opportunities:
            data = _extract_data(item)
            if not data.get("asset") or not data.get("fiat"):
                continue
            sorted_ops.append({"data": data, "raw": item})

        if not sorted_ops:
            return False

        sorted_ops.sort(key=lambda entry: entry["data"].get("spread") or 0, reverse=True)

        top_limit = max(1, settings.P2P_TOP_SPREADS)
        selected: List[Dict] = []
        seen_pairs = set()

        for entry in sorted_ops:
            data = entry["data"]
            pair_key = (data["asset"], data["fiat"])
            if pair_key in seen_pairs:
                continue
            seen_pairs.add(pair_key)
            selected.append(entry)
            if len(selected) >= top_limit:
                break

        if not selected:
            return False

        lines = ["📊 *TOP SPREADS BINANCE P2P* 📊", ""]

        for idx, entry in enumerate(selected, start=1):
            data = entry["data"]
            op = entry["raw"].get("opportunity_data") or entry["raw"]
            spread = _format_percent(data.get("spread"))
            buy_price = _format_price(op.get("buy_price"), data.get("fiat"))
            sell_price = _format_price(op.get("sell_price"), data.get("fiat"))
            buy_merchant = op.get("buy_merchant") or "Desconocido"
            sell_merchant = op.get("sell_merchant") or "Desconocido"
            try:
                buy_available = float(op.get("buy_available") or 0)
            except (TypeError, ValueError):
                buy_available = 0.0
            try:
                sell_available = float(op.get("sell_available") or 0)
            except (TypeError, ValueError):
                sell_available = 0.0
            lines.append(
                f"{idx}. *{data['asset']}/{data['fiat']}* — Spread {spread}"
            )
            lines.append(
                "   Compra: "
                + f"{buy_price} (👤 {buy_merchant}, 📦 {buy_available:.2f} {data['asset']})"
            )
            lines.append(
                "   Venta: "
                + f"{sell_price} (👤 {sell_merchant}, 📦 {sell_available:.2f} {data['asset']})"
            )
            lines.append("")

        lines.append(f"🔄 Pares analizados: {len(seen_pairs)}")
        lines.append(f"⏰ {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")

        message = "\n".join(lines)

        if self.telegram_enabled:
            return await self._send_telegram_message(message)

        logger.info("Spread digest", opportunities=selected)
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
