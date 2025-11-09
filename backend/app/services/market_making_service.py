"""
Market Making Service - Sistema de market making automatizado

Funcionalidades:
1. Publicación automática de órdenes en Binance P2P
2. Gestión de inventario inteligente
3. Ajuste automático de precios
4. Balanceo de liquidez
5. Monitoreo de órdenes activas
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import asyncio
from app.services.binance_service import BinanceService
from app.services.binance_spot_service import BinanceSpotService
from app.services.dynamic_pricing_service import DynamicPricingService
from app.services.liquidity_analysis_service import LiquidityAnalysisService
from app.core.config import settings
from app.core.database import SessionLocal
from app.models.trade import Trade, TradeType, TradeStatus
import logging

logger = logging.getLogger(__name__)


class MarketMakingService:
    """
    Servicio de market making que publica órdenes continuamente
    para crear liquidez propia.
    """

    def __init__(self):
        self.p2p_service = BinanceService()
        self.spot_service = BinanceSpotService()
        self.dynamic_pricing = DynamicPricingService()
        self.liquidity_service = LiquidityAnalysisService()

        # Configuración
        self.MIN_SPREAD_PCT = 0.5  # Spread mínimo 0.5%
        self.MAX_SPREAD_PCT = 2.0  # Spread máximo 2.0%
        self.TARGET_SPREAD_PCT = 1.0  # Spread objetivo 1.0%

        # Inventario objetivo
        self.TARGET_INVENTORY_RATIO = 0.5  # 50% USDT, 50% Fiat
        self.INVENTORY_TOLERANCE = 0.2  # Tolerancia ±20%

        # Órdenes activas
        self.active_orders: Dict[str, Dict] = {}

    async def start_market_making(
        self,
        asset: str = "USDT",
        fiat: str = "COP",
        update_interval_seconds: int = 30
    ) -> Dict:
        """
        Inicia market making para un par de activos.

        Args:
            asset: Criptomoneda (USDT)
            fiat: Moneda fiat (COP, VES, etc.)
            update_interval_seconds: Intervalo de actualización en segundos

        Returns:
            Estado de inicio
        """

        try:
            logger.info(
                f"Starting market making for {asset}/{fiat}",
                update_interval=update_interval_seconds
            )

            # 1. Verificar inventario
            inventory_status = await self._check_inventory(asset, fiat)

            if not inventory_status["has_sufficient_inventory"]:
                return {
                    "success": False,
                    "error": "Inventario insuficiente",
                    "details": inventory_status
                }

            # 2. Calcular precios iniciales
            prices = await self._calculate_market_making_prices(asset, fiat)

            if not prices.get("success"):
                return {
                    "success": False,
                    "error": "No se pudieron calcular precios",
                    "details": prices
                }

            # 3. Publicar órdenes iniciales
            buy_order = await self._publish_buy_order(
                asset=asset,
                fiat=fiat,
                price=prices["buy_price"],
                amount=prices["buy_amount"]
            )

            sell_order = await self._publish_sell_order(
                asset=asset,
                fiat=fiat,
                price=prices["sell_price"],
                amount=prices["sell_amount"]
            )

            # 4. Guardar órdenes activas
            key = f"{asset}_{fiat}"
            self.active_orders[key] = {
                "asset": asset,
                "fiat": fiat,
                "buy_order": buy_order,
                "sell_order": sell_order,
                "last_update": datetime.utcnow(),
                "update_interval": update_interval_seconds
            }

            return {
                "success": True,
                "asset": asset,
                "fiat": fiat,
                "buy_order": buy_order,
                "sell_order": sell_order,
                "spread_pct": prices["spread_pct"],
                "message": "Market making iniciado correctamente"
            }

        except Exception as e:
            logger.error(f"Error starting market making: {str(e)}")
            return {"success": False, "error": str(e)}

    async def update_market_making_orders(
        self,
        asset: str = "USDT",
        fiat: str = "COP"
    ) -> Dict:
        """
        Actualiza órdenes de market making según condiciones del mercado.
        """

        try:
            key = f"{asset}_{fiat}"

            if key not in self.active_orders:
                return {
                    "success": False,
                    "error": "Market making no está activo para este par"
                }

            # 1. Verificar estado de órdenes actuales
            current_orders = self.active_orders[key]
            buy_order = current_orders.get("buy_order")
            sell_order = current_orders.get("sell_order")

            # 2. Recalcular precios
            prices = await self._calculate_market_making_prices(asset, fiat)

            if not prices.get("success"):
                return {
                    "success": False,
                    "error": "No se pudieron calcular nuevos precios"
                }

            # 3. Verificar si necesitamos actualizar
            needs_update = False

            # Verificar si precios cambiaron significativamente (> 0.1%)
            if buy_order and abs(prices["buy_price"] - buy_order.get("price", 0)) / buy_order.get("price", 1) > 0.001:
                needs_update = True

            if sell_order and abs(prices["sell_price"] - sell_order.get("price", 0)) / sell_order.get("price", 1) > 0.001:
                needs_update = True

            # 4. Actualizar si es necesario
            if needs_update:
                # Cancelar órdenes antiguas (si es posible)
                # TODO: Implementar cancelación de órdenes en Binance P2P

                # Publicar nuevas órdenes
                new_buy_order = await self._publish_buy_order(
                    asset=asset,
                    fiat=fiat,
                    price=prices["buy_price"],
                    amount=prices["buy_amount"]
                )

                new_sell_order = await self._publish_sell_order(
                    asset=asset,
                    fiat=fiat,
                    price=prices["sell_price"],
                    amount=prices["sell_amount"]
                )

                # Actualizar órdenes activas
                self.active_orders[key].update({
                    "buy_order": new_buy_order,
                    "sell_order": new_sell_order,
                    "last_update": datetime.utcnow()
                })

                return {
                    "success": True,
                    "updated": True,
                    "buy_order": new_buy_order,
                    "sell_order": new_sell_order,
                    "spread_pct": prices["spread_pct"],
                    "reason": "Precios actualizados"
                }
            else:
                return {
                    "success": True,
                    "updated": False,
                    "message": "Precios aún competitivos, no se requiere actualización"
                }

        except Exception as e:
            logger.error(f"Error updating market making orders: {str(e)}")
            return {"success": False, "error": str(e)}

    async def _calculate_market_making_prices(
        self,
        asset: str,
        fiat: str
    ) -> Dict:
        """Calcula precios óptimos para market making"""

        try:
            # 1. Obtener precio dinámico
            buy_price_data = await self.dynamic_pricing.calculate_dynamic_price(
                asset=asset,
                fiat=fiat,
                trade_type="BUY",
                amount_usd=5000.0  # Volumen estándar
            )

            sell_price_data = await self.dynamic_pricing.calculate_dynamic_price(
                asset=asset,
                fiat=fiat,
                trade_type="SELL",
                amount_usd=5000.0
            )

            if not buy_price_data.get("success") or not sell_price_data.get("success"):
                return {"success": False, "error": "Error calculando precios dinámicos"}

            buy_price = buy_price_data["final_price"]
            sell_price = sell_price_data["final_price"]

            # 2. Verificar spread
            spread = sell_price - buy_price
            spread_pct = (spread / buy_price * 100) if buy_price > 0 else 0

            # 3. Ajustar si spread está fuera de rango
            if spread_pct < self.MIN_SPREAD_PCT:
                # Spread muy bajo, aumentar
                mid_price = (buy_price + sell_price) / 2
                target_spread = mid_price * (self.TARGET_SPREAD_PCT / 100)
                buy_price = mid_price - target_spread / 2
                sell_price = mid_price + target_spread / 2
                spread_pct = self.TARGET_SPREAD_PCT
            elif spread_pct > self.MAX_SPREAD_PCT:
                # Spread muy alto, reducir
                mid_price = (buy_price + sell_price) / 2
                target_spread = mid_price * (self.TARGET_SPREAD_PCT / 100)
                buy_price = mid_price - target_spread / 2
                sell_price = mid_price + target_spread / 2
                spread_pct = self.TARGET_SPREAD_PCT

            # 4. Calcular cantidades según inventario
            inventory_status = await self._check_inventory(asset, fiat)
            buy_amount, sell_amount = self._calculate_order_amounts(
                inventory_status,
                asset,
                fiat
            )

            return {
                "success": True,
                "buy_price": round(buy_price, 2),
                "sell_price": round(sell_price, 2),
                "spread": round(spread, 2),
                "spread_pct": round(spread_pct, 2),
                "buy_amount": round(buy_amount, 2),
                "sell_amount": round(sell_amount, 2),
                "mid_price": round((buy_price + sell_price) / 2, 2)
            }

        except Exception as e:
            logger.error(f"Error calculating market making prices: {str(e)}")
            return {"success": False, "error": str(e)}

    async def _check_inventory(
        self,
        asset: str,
        fiat: str
    ) -> Dict:
        """Verifica inventario disponible"""

        try:
            # Obtener balances de Spot
            balances = await self.spot_service.get_all_balances()

            usdt_balance = balances.get("USDT", 0.0)

            # TODO: Obtener balance de fiat (requiere integración con sistema de fiat)
            # Por ahora, asumir que tenemos suficiente
            fiat_balance_usd_equivalent = 10000.0  # Placeholder

            total_balance_usd = usdt_balance + fiat_balance_usd_equivalent
            usdt_ratio = usdt_balance / total_balance_usd if total_balance_usd > 0 else 0

            # Verificar si tenemos inventario suficiente
            min_inventory_usd = 1000.0  # Mínimo $1000 USD
            has_sufficient = total_balance_usd >= min_inventory_usd

            # Verificar balance
            is_balanced = abs(usdt_ratio - self.TARGET_INVENTORY_RATIO) <= self.INVENTORY_TOLERANCE

            return {
                "usdt_balance": usdt_balance,
                "fiat_balance_usd_equivalent": fiat_balance_usd_equivalent,
                "total_balance_usd": total_balance_usd,
                "usdt_ratio": usdt_ratio,
                "target_ratio": self.TARGET_INVENTORY_RATIO,
                "is_balanced": is_balanced,
                "has_sufficient_inventory": has_sufficient,
                "recommendation": self._generate_inventory_recommendation(
                    usdt_ratio,
                    is_balanced,
                    has_sufficient
                )
            }

        except Exception as e:
            logger.error(f"Error checking inventory: {str(e)}")
            return {
                "usdt_balance": 0.0,
                "fiat_balance_usd_equivalent": 0.0,
                "total_balance_usd": 0.0,
                "usdt_ratio": 0.0,
                "is_balanced": False,
                "has_sufficient_inventory": False,
                "error": str(e)
            }

    def _calculate_order_amounts(
        self,
        inventory_status: Dict,
        asset: str,
        fiat: str
    ) -> Tuple[float, float]:
        """Calcula cantidades de órdenes según inventario"""

        usdt_balance = inventory_status.get("usdt_balance", 0.0)
        fiat_balance = inventory_status.get("fiat_balance_usd_equivalent", 0.0)
        usdt_ratio = inventory_status.get("usdt_ratio", 0.5)

        # Cantidad base por orden
        base_amount_usd = 5000.0

        # Ajustar según inventario
        if usdt_ratio < self.TARGET_INVENTORY_RATIO - self.INVENTORY_TOLERANCE:
            # Poco USDT, priorizar compras
            buy_amount = min(base_amount_usd * 1.5, fiat_balance * 0.1)
            sell_amount = min(base_amount_usd * 0.5, usdt_balance * 0.1)
        elif usdt_ratio > self.TARGET_INVENTORY_RATIO + self.INVENTORY_TOLERANCE:
            # Mucho USDT, priorizar ventas
            buy_amount = min(base_amount_usd * 0.5, fiat_balance * 0.1)
            sell_amount = min(base_amount_usd * 1.5, usdt_balance * 0.1)
        else:
            # Balanceado
            buy_amount = min(base_amount_usd, fiat_balance * 0.1)
            sell_amount = min(base_amount_usd, usdt_balance * 0.1)

        return buy_amount, sell_amount

    def _generate_inventory_recommendation(
        self,
        usdt_ratio: float,
        is_balanced: bool,
        has_sufficient: bool
    ) -> str:
        """Genera recomendación sobre inventario"""

        if not has_sufficient:
            return "⚠️ INVENTARIO INSUFICIENTE - Aumentar capital"
        elif not is_balanced:
            if usdt_ratio < self.TARGET_INVENTORY_RATIO:
                return "📊 POCOS USDT - Priorizar compras"
            else:
                return "📊 MUCHO USDT - Priorizar ventas"
        else:
            return "✅ INVENTARIO BALANCEADO - Operar normalmente"

    async def _publish_buy_order(
        self,
        asset: str,
        fiat: str,
        price: float,
        amount: float
    ) -> Dict:
        """
        Publica orden de compra en Binance P2P.

        NOTA: Esto requiere integración con Binance P2P API para publicar órdenes.
        Por ahora, simulamos la publicación.
        """

        try:
            # TODO: Implementar publicación real en Binance P2P
            # Por ahora, retornamos simulación

            order_id = f"MM_BUY_{asset}_{fiat}_{datetime.utcnow().timestamp()}"

            logger.info(
                f"Publishing buy order: {order_id}",
                asset=asset,
                fiat=fiat,
                price=price,
                amount=amount
            )

            return {
                "order_id": order_id,
                "type": "BUY",
                "asset": asset,
                "fiat": fiat,
                "price": price,
                "amount": amount,
                "status": "active",
                "created_at": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Error publishing buy order: {str(e)}")
            return {
                "order_id": None,
                "error": str(e),
                "status": "failed"
            }

    async def _publish_sell_order(
        self,
        asset: str,
        fiat: str,
        price: float,
        amount: float
    ) -> Dict:
        """
        Publica orden de venta en Binance P2P.

        NOTA: Esto requiere integración con Binance P2P API para publicar órdenes.
        Por ahora, simulamos la publicación.
        """

        try:
            # TODO: Implementar publicación real en Binance P2P
            # Por ahora, retornamos simulación

            order_id = f"MM_SELL_{asset}_{fiat}_{datetime.utcnow().timestamp()}"

            logger.info(
                f"Publishing sell order: {order_id}",
                asset=asset,
                fiat=fiat,
                price=price,
                amount=amount
            )

            return {
                "order_id": order_id,
                "type": "SELL",
                "asset": asset,
                "fiat": fiat,
                "price": price,
                "amount": amount,
                "status": "active",
                "created_at": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Error publishing sell order: {str(e)}")
            return {
                "order_id": None,
                "error": str(e),
                "status": "failed"
            }

    async def stop_market_making(
        self,
        asset: str,
        fiat: str
    ) -> Dict:
        """Detiene market making para un par"""

        try:
            key = f"{asset}_{fiat}"

            if key not in self.active_orders:
                return {
                    "success": False,
                    "error": "Market making no está activo para este par"
                }

            # TODO: Cancelar órdenes activas en Binance P2P

            # Remover de órdenes activas
            del self.active_orders[key]

            return {
                "success": True,
                "message": f"Market making detenido para {asset}/{fiat}"
            }

        except Exception as e:
            logger.error(f"Error stopping market making: {str(e)}")
            return {"success": False, "error": str(e)}

    async def get_market_making_status(
        self,
        asset: str = "USDT",
        fiat: str = "COP"
    ) -> Dict:
        """Obtiene estado actual de market making"""

        try:
            key = f"{asset}_{fiat}"

            if key not in self.active_orders:
                return {
                    "success": False,
                    "active": False,
                    "message": "Market making no está activo"
                }

            orders = self.active_orders[key]
            inventory = await self._check_inventory(asset, fiat)

            return {
                "success": True,
                "active": True,
                "asset": asset,
                "fiat": fiat,
                "buy_order": orders.get("buy_order"),
                "sell_order": orders.get("sell_order"),
                "last_update": orders.get("last_update").isoformat() if orders.get("last_update") else None,
                "inventory": inventory,
                "update_interval_seconds": orders.get("update_interval")
            }

        except Exception as e:
            logger.error(f"Error getting market making status: {str(e)}")
            return {"success": False, "error": str(e)}

    async def get_all_active_market_making(self) -> Dict:
        """Obtiene todos los pares con market making activo"""

        try:
            active_pairs = []

            for key, orders in self.active_orders.items():
                status = await self.get_market_making_status(
                    asset=orders["asset"],
                    fiat=orders["fiat"]
                )
                if status.get("active"):
                    active_pairs.append(status)

            return {
                "success": True,
                "active_pairs": active_pairs,
                "total_pairs": len(active_pairs),
                "timestamp": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Error getting all active market making: {str(e)}")
            return {"success": False, "error": str(e)}

