"""
Servicio de arbitraje entre Binance Spot y P2P.
Detecta y ejecuta oportunidades de ganancia.
"""
from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Any, Dict, Optional, List, Tuple

import structlog

from app.core.config import settings
from app.services.binance_service import BinanceService
from app.services.binance_spot_service import BinanceSpotService
from app.services.fx_service import FXService
from app.services.trm_service import TRMService

logger = structlog.get_logger()


class ArbitrageService:
    """
    Detecta oportunidades de arbitraje entre:
    1. Spot (cripto-cripto)
    2. P2P (cripto-fiat)
    3. Cross-currency (COP vs VES)
    """

    def __init__(
        self,
        spot_service: Optional[BinanceSpotService] = None,
        p2p_service: Optional[BinanceService] = None,
        fx_service: Optional[FXService] = None,
        trm_service: Optional[TRMService] = None,
    ) -> None:
        self.spot_service = spot_service or BinanceSpotService()
        self._owns_p2p = p2p_service is None
        self.p2p_service = p2p_service or BinanceService()
        self.trm_service = trm_service or TRMService()
        self.fx_service = fx_service or FXService(
            p2p_service=self.p2p_service,
            spot_service=self.spot_service,
            trm_service=self.trm_service,
        )

    async def aclose(self) -> None:
        """Cerrar recursos asíncronos asociados al servicio."""
        if self._owns_p2p and hasattr(self.p2p_service, "aclose"):
            try:
                await self.p2p_service.aclose()
            except Exception as exc:  # noqa: BLE001
                logger.warning("Error closing BinanceService client", error=str(exc))

    async def analyze_spot_to_p2p_arbitrage(
        self,
        asset: str = "USDT",
        fiat: str = "COP",
    ) -> Dict[str, Any]:
        """
        Analizar arbitraje: Comprar en Spot -> Vender en P2P.

        Flujo:
        1. Comprar USDT en Spot con USDC (~1 USD)
        2. Vender USDT en P2P por COP/VES
        3. Calcular profit real considerando tasa de mercado
        """
        asset_code = asset.upper()
        fiat_code = fiat.upper()

        try:
            (
                spot_price,
                p2p_sell_quote,
                p2p_buy_quote,
                exchange_rate,
            ) = await asyncio.gather(
                self.spot_service.get_spot_price("USDCUSDT"),
                self.p2p_service.get_best_price(
                    asset=asset_code,
                    fiat=fiat_code,
                    trade_type="SELL",
                    return_details=True,
                ),
                self.p2p_service.get_best_price(
                    asset=asset_code,
                    fiat=fiat_code,
                    trade_type="BUY",
                    return_details=True,
                ),
                self.fx_service.get_rate(fiat_code),
            )

            if spot_price is None or spot_price <= 0:
                spot_price = 1.0

            if exchange_rate is None or exchange_rate <= 0:
                exchange_rate = settings.FX_FALLBACK_RATES.get(fiat_code, 1.0)

            p2p_sell_price = p2p_sell_quote["price"] if isinstance(p2p_sell_quote, dict) else 0.0
            p2p_buy_price = p2p_buy_quote["price"] if isinstance(p2p_buy_quote, dict) else 0.0
            sell_available = p2p_sell_quote.get("available") if isinstance(p2p_sell_quote, dict) else 0.0

            cost_usd = spot_price
            revenue_usd = p2p_sell_price / exchange_rate if exchange_rate else 0.0
            profit_per_unit = revenue_usd - cost_usd
            profit_percentage = (profit_per_unit / cost_usd) * 100 if cost_usd > 0 else 0.0

            spot_fee = 0.001  # 0.1% Binance Spot
            net_profit_percentage = profit_percentage - (spot_fee * 100)

            recommended_amount = self._calculate_recommended_amount(net_profit_percentage)
            liquidity_warning: Optional[str] = None

            if recommended_amount > 0:
                if not sell_available or sell_available <= 0:
                    liquidity_warning = "Sin liquidez suficiente en el mejor anuncio P2P."
                    recommended_amount = 0
                elif sell_available < recommended_amount:
                    liquidity_warning = (
                        f"Liquidez disponible limitada a {sell_available:.2f} {asset_code}. "
                        "Monto recomendado ajustado."
                    )
                    recommended_amount = sell_available

            p2p_spread = 0.0
            if p2p_sell_price > 0 and p2p_buy_price > 0:
                p2p_spread = ((p2p_buy_price - p2p_sell_price) / p2p_sell_price) * 100

            opportunity = {
                "strategy": "spot_to_p2p",
                "asset": asset_code,
                "fiat": fiat_code,
                "spot_price_usd": round(spot_price, 4),
                "p2p_sell_price_fiat": round(p2p_sell_price, 2),
                "p2p_buy_price_fiat": round(p2p_buy_price, 2),
                "p2p_sell_available": round(sell_available or 0.0, 2),
                "p2p_spread_percentage": round(abs(p2p_spread), 2),
                "exchange_rate_used": round(exchange_rate, 4),
                "cost_usd": round(cost_usd, 4),
                "revenue_usd": round(revenue_usd, 4),
                "profit_per_unit_usd": round(profit_per_unit, 4),
                "profit_percentage": round(profit_percentage, 2),
                "net_profit_percentage": round(net_profit_percentage, 2),
                "fees_percentage": round(spot_fee * 100, 2),
                "is_profitable": net_profit_percentage > settings.ARBITRAGE_MIN_PROFIT,
                "recommended_amount": round(recommended_amount, 2),
                "liquidity_warning": liquidity_warning,
                "timestamp": datetime.utcnow().isoformat(),
            }

            if opportunity["is_profitable"]:
                logger.info(
                    "Profitable arbitrage found",
                    strategy="spot_to_p2p",
                    profit=net_profit_percentage,
                    fiat=fiat_code,
                    exchange_rate=exchange_rate,
                )
            else:
                logger.debug(
                    "No profitable arbitrage",
                    strategy="spot_to_p2p",
                    profit=net_profit_percentage,
                    fiat=fiat_code,
                )

            return opportunity

        except Exception as exc:  # noqa: BLE001
            logger.error("Error analyzing spot to p2p arbitrage", error=str(exc))
            return {
                "strategy": "spot_to_p2p",
                "is_profitable": False,
                "error": str(exc),
            }

    async def analyze_p2p_cross_currency(self) -> Dict[str, Any]:
        """
        Analizar arbitraje entre COP y VES en P2P.

        Flujo:
        1. Comprar USDT con COP en P2P
        2. Vender USDT por VES en P2P
        """
        try:
            (
                cop_buy_price,
                cop_sell_price,
                ves_buy_price,
                ves_sell_price,
                cop_rate,
                ves_rate,
            ) = await asyncio.gather(
                self.p2p_service.get_best_price("USDT", "COP", "BUY"),
                self.p2p_service.get_best_price("USDT", "COP", "SELL"),
                self.p2p_service.get_best_price("USDT", "VES", "BUY"),
                self.p2p_service.get_best_price("USDT", "VES", "SELL"),
                self.fx_service.get_rate("COP"),
                self.fx_service.get_rate("VES"),
            )

            strategy_1_profit = self._calculate_cross_profit(
                buy_price_cop=cop_buy_price,
                sell_price_ves=ves_sell_price,
                cop_rate=cop_rate,
                ves_rate=ves_rate,
            )

            strategy_2_profit = self._calculate_cross_profit(
                buy_price_ves=ves_buy_price,
                sell_price_cop=cop_sell_price,
                cop_rate=cop_rate,
                ves_rate=ves_rate,
            )

            best_strategy = (
                strategy_1_profit
                if strategy_1_profit["profit_percentage"] > strategy_2_profit["profit_percentage"]
                else strategy_2_profit
            )

            best_strategy["is_profitable"] = best_strategy["profit_percentage"] > settings.ARBITRAGE_MIN_PROFIT
            best_strategy["cop_rate"] = round(cop_rate or 0.0, 4)
            best_strategy["ves_rate"] = round(ves_rate or 0.0, 4)

            return best_strategy

        except Exception as exc:  # noqa: BLE001
            logger.error("Error analyzing cross currency arbitrage", error=str(exc))
            return {
                "strategy": "cross_currency",
                "is_profitable": False,
                "error": str(exc),
            }

    async def analyze_spot_to_p2p_bulk(
        self,
        assets: List[str],
        fiats: List[str],
    ) -> List[Dict[str, Any]]:
        """
        Analizar oportunidades de arbitraje Spot-P2P para múltiples pares.
        Filtra pares inválidos antes de procesarlos para evitar errores de API.
        """
        combinations: List[Tuple[str, str]] = []
        tasks = []

        unique_assets = list(dict.fromkeys(asset.upper() for asset in assets))
        unique_fiats = list(dict.fromkeys(fiat.upper() for fiat in fiats))

        # Filtrar pares inválidos antes de crear tareas
        for asset in unique_assets:
            for fiat in unique_fiats:
                # Validar par antes de agregarlo
                if self.p2p_service.is_valid_pair(asset, fiat):
                    combinations.append((asset, fiat))
                    tasks.append(self.analyze_spot_to_p2p_arbitrage(asset, fiat))
                else:
                    logger.debug(
                        "Skipping invalid pair in arbitrage analysis",
                        asset=asset,
                        fiat=fiat
                    )

        if not tasks:
            return []

        results: List[Dict[str, Any]] = []
        responses = await asyncio.gather(*tasks, return_exceptions=True)

        for (asset, fiat), response in zip(combinations, responses):
            if isinstance(response, Exception):  # noqa: BLE001
                logger.error(
                    "Error analyzing spot to p2p pair",
                    asset=asset,
                    fiat=fiat,
                    error=str(response),
                )
                continue

            if response:
                response.setdefault("asset", asset)
                response.setdefault("fiat", fiat)
                results.append(response)

        return results

    async def analyze_cross_currency_pairs(
        self,
        fiats: List[str],
    ) -> List[Dict[str, Any]]:
        """Analizar oportunidades P2P comprando en una moneda fiat y vendiendo en otra."""
        unique_fiats = list(dict.fromkeys(fiat.upper() for fiat in fiats))
        if len(unique_fiats) < 2:
            return []

        rate_tasks = {
            fiat: asyncio.create_task(self.fx_service.get_rate(fiat))
            for fiat in unique_fiats
        }

        rates: Dict[str, float] = {}
        for fiat, task in rate_tasks.items():
            try:
                rates[fiat] = await task
            except Exception as exc:  # noqa: BLE001
                logger.error("Error fetching FX rate", fiat=fiat, error=str(exc))
                rates[fiat] = 0.0

        combinations: List[Tuple[str, str]] = []
        tasks = []
        for base in unique_fiats:
            for quote in unique_fiats:
                if base == quote:
                    continue
                combinations.append((base, quote))
                tasks.append(self._analyze_cross_currency_pair(base, quote, rates))

        if not tasks:
            return []

        results: List[Dict[str, Any]] = []
        responses = await asyncio.gather(*tasks, return_exceptions=True)

        for (fiat_from, fiat_to), response in zip(combinations, responses):
            if isinstance(response, Exception):  # noqa: BLE001
                logger.error(
                    "Error analyzing cross currency pair",
                    fiat_from=fiat_from,
                    fiat_to=fiat_to,
                    error=str(response),
                )
                continue

            if response:
                results.append(response)

        results.sort(
            key=lambda item: self._to_float(
                item.get("net_profit_percentage") or item.get("profit_percentage")
            ),
            reverse=True,
        )
        return results

    async def _analyze_cross_currency_pair(
        self,
        fiat_from: str,
        fiat_to: str,
        rates: Dict[str, float],
    ) -> Optional[Dict[str, Any]]:
        """Analizar ruta P2P fiat_from -> USDT -> fiat_to."""
        rate_from = self._to_float(rates.get(fiat_from))
        rate_to = self._to_float(rates.get(fiat_to))

        if rate_from <= 0 or rate_to <= 0:
            return None

        rows = settings.P2P_ANALYSIS_ROWS
        buy_task = self.p2p_service.get_best_price(
            asset="USDT",
            fiat=fiat_from,
            trade_type="BUY",
            return_details=True,
            rows=rows,
        )
        sell_task = self.p2p_service.get_best_price(
            asset="USDT",
            fiat=fiat_to,
            trade_type="SELL",
            return_details=True,
            rows=rows,
        )

        buy_quote, sell_quote = await asyncio.gather(buy_task, sell_task)

        if not buy_quote or not sell_quote:
            return None

        buy_price = self._to_float(buy_quote.get("price"))
        sell_price = self._to_float(sell_quote.get("price"))

        if buy_price <= 0 or sell_price <= 0:
            return None

        cost_usd = buy_price / rate_from if rate_from else 0.0
        revenue_usd = sell_price / rate_to if rate_to else 0.0

        if cost_usd <= 0:
            return None

        profit_per_unit = revenue_usd - cost_usd
        profit_percentage = (profit_per_unit / cost_usd) * 100 if cost_usd > 0 else 0.0
        spread_percentage = ((sell_price - buy_price) / buy_price) * 100 if buy_price > 0 else 0.0

        available_buy = self._to_float(buy_quote.get("available"))
        available_sell = self._to_float(sell_quote.get("available"))
        max_volume = min(available_buy, available_sell) if available_buy and available_sell else 0.0

        return {
            "strategy": "cross_currency",
            "asset": "USDT",
            "fiat_from": fiat_from,
            "fiat_to": fiat_to,
            "profit_percentage": round(profit_percentage, 2),
            "net_profit_percentage": round(profit_percentage, 2),
            "spread_percentage": round(spread_percentage, 2),
            "cost_usd": round(cost_usd, 4),
            "revenue_usd": round(revenue_usd, 4),
            "buy_quote": buy_quote,
            "sell_quote": sell_quote,
            "max_volume": round(max_volume, 4),
            "is_profitable": profit_percentage > settings.ARBITRAGE_MIN_PROFIT,
        }

    async def get_ranked_opportunities(
        self,
        assets: List[str],
        fiats: List[str],
        top_n: int = 5,
        include_triangle: bool = True,
    ) -> List[Dict[str, Any]]:
        """Obtener oportunidades ordenadas por score combinando múltiples estrategias."""
        normalized: List[Dict[str, Any]] = []

        spot_results = await self.analyze_spot_to_p2p_bulk(assets, fiats)
        for result in spot_results:
            normalized.append(self._normalize_spot_opportunity(result))

        cross_results = await self.analyze_cross_currency_pairs(fiats)
        for result in cross_results:
            normalized.append(self._normalize_cross_currency_opportunity(result))

        if include_triangle:
            try:
                from app.services.triangle_arbitrage_service import TriangleArbitrageService

                triangle_assets = [asset for asset in assets if asset.upper() not in {"USD"}]
                if triangle_assets:
                    triangle_service = TriangleArbitrageService(
                        p2p_service=self.p2p_service,
                        spot_service=self.spot_service,
                    )
                    triangle_results = await triangle_service.find_best_triangle_routes(
                        assets=triangle_assets,
                        fiats=fiats,
                    )
                    for result in triangle_results:
                        normalized.append(self._normalize_triangle_opportunity(result))
            except Exception as exc:  # noqa: BLE001
                logger.error("Error analyzing triangle arbitrage", error=str(exc))

        dedup: Dict[Tuple[str, str], Dict[str, Any]] = {}
        for opportunity in normalized:
            label = opportunity.get("label") or ""
            key = (opportunity.get("strategy", "unknown"), label)
            score = self._to_float(opportunity.get("score"))
            opportunity["score"] = score
            existing = dedup.get(key)
            if not existing or score > self._to_float(existing.get("score")):
                dedup[key] = opportunity

        min_liquidity = settings.ARBITRAGE_MIN_LIQUIDITY_USDT

        filtered: List[Dict[str, Any]] = []
        for value in dedup.values():
            score_value = self._to_float(value.get("score"))
            if score_value <= 0:
                continue

            if min_liquidity > 0 and not self._passes_liquidity_threshold(value, min_liquidity):
                continue

            filtered.append(value)

        filtered.sort(key=lambda item: self._to_float(item.get("score")), reverse=True)

        top_limit = max(1, top_n)
        result = filtered[:top_limit]
        
        # Actualizar métrica de oportunidades activas de arbitraje
        try:
            from app.core.metrics import active_arbitrage_opportunities
            # Contar por estrategia
            strategies = {}
            for opp in result:
                strategy = opp.get("strategy", "unknown")
                strategies[strategy] = strategies.get(strategy, 0) + 1
            
            # Actualizar gauge para cada estrategia
            for strategy, count in strategies.items():
                active_arbitrage_opportunities.labels(strategy=strategy).set(count)
            
            # Si no hay oportunidades, establecer a 0 para todas las estrategias conocidas
            if not strategies:
                for strategy in ["spot_to_p2p", "cross_currency", "triangle_arbitrage"]:
                    active_arbitrage_opportunities.labels(strategy=strategy).set(0)
        except Exception:
            pass  # No fallar si las métricas fallan
        
        return result

    def _calculate_cross_profit(
        self,
        buy_price_cop: float = 0.0,
        sell_price_ves: float = 0.0,
        buy_price_ves: float = 0.0,
        sell_price_cop: float = 0.0,
        cop_rate: float = 0.0,
        ves_rate: float = 0.0,
    ) -> Dict[str, Any]:
        """Calcular profit de arbitraje cross-currency."""

        if buy_price_cop and sell_price_ves and cop_rate and ves_rate:
            cost_usd = buy_price_cop / cop_rate
            revenue_usd = sell_price_ves / ves_rate
            direction = "COP -> VES"
        elif buy_price_ves and sell_price_cop and cop_rate and ves_rate:
            cost_usd = buy_price_ves / ves_rate
            revenue_usd = sell_price_cop / cop_rate
            direction = "VES -> COP"
        else:
            return {
                "strategy": "cross_currency",
                "profit_percentage": 0.0,
                "cost_usd": 0.0,
                "revenue_usd": 0.0,
                "direction": "N/A",
            }

        profit = revenue_usd - cost_usd
        profit_percentage = (profit / cost_usd) * 100 if cost_usd > 0 else 0.0

        return {
            "strategy": "cross_currency",
            "direction": direction,
            "cost_usd": round(cost_usd, 4),
            "revenue_usd": round(revenue_usd, 4),
            "profit_percentage": round(profit_percentage, 2),
        }

    @staticmethod
    def _to_float(value: Any, default: float = 0.0) -> float:
        """Convertir valores a float de forma segura."""
        try:
            if value is None:
                return default
            return float(value)
        except (TypeError, ValueError):  # pragma: no cover - defensive
            return default

    def _normalize_spot_opportunity(self, opportunity: Dict[str, Any]) -> Dict[str, Any]:
        """Normalizar datos de arbitraje Spot -> P2P."""
        asset = opportunity.get("asset", "USDT")
        fiat = opportunity.get("fiat", "USD")

        return {
            "strategy": "spot_to_p2p",
            "label": f"{asset}/{fiat}",
            "asset": asset,
            "fiat": fiat,
            "score": self._to_float(opportunity.get("net_profit_percentage")),
            "profit_percentage": self._to_float(opportunity.get("profit_percentage")),
            "net_profit_percentage": self._to_float(opportunity.get("net_profit_percentage")),
            "spread_percentage": self._to_float(opportunity.get("p2p_spread_percentage")),
            "liquidity": self._to_float(opportunity.get("p2p_sell_available")),
            "liquidity_asset": asset,
            "recommended_amount": self._to_float(opportunity.get("recommended_amount")),
            "details": opportunity,
        }

    def _normalize_cross_currency_opportunity(self, opportunity: Dict[str, Any]) -> Dict[str, Any]:
        """Normalizar datos de arbitraje cross currency."""
        asset = opportunity.get("asset", "USDT")
        fiat_from = opportunity.get("fiat_from", "USD")
        fiat_to = opportunity.get("fiat_to", "USD")

        return {
            "strategy": "cross_currency",
            "label": f"{fiat_from} → {fiat_to}",
            "asset": asset,
            "fiat": fiat_from,
            "secondary_fiat": fiat_to,
            "score": self._to_float(opportunity.get("net_profit_percentage") or opportunity.get("profit_percentage")),
            "profit_percentage": self._to_float(opportunity.get("profit_percentage")),
            "net_profit_percentage": self._to_float(opportunity.get("net_profit_percentage")),
            "spread_percentage": self._to_float(opportunity.get("spread_percentage")),
            "liquidity": self._to_float(opportunity.get("max_volume")),
            "liquidity_asset": asset,
            "details": opportunity,
        }

    def _normalize_triangle_opportunity(self, opportunity: Dict[str, Any]) -> Dict[str, Any]:
        """Normalizar datos de arbitraje triangular."""
        route = opportunity.get("route", "")
        parts = [segment.strip() for segment in route.split("->") if segment.strip()]
        fiat_from = parts[0] if parts else opportunity.get("fiat_from", "")
        fiat_to = parts[-1] if parts else opportunity.get("fiat_to", "")
        asset = opportunity.get("asset", parts[1] if len(parts) > 1 else "USDT")
        profit_data = opportunity.get("profit", {})
        roi = self._to_float(
            profit_data.get("roi_percentage") or opportunity.get("roi_percentage")
        )

        return {
            "strategy": "triangle_arbitrage",
            "label": route or f"{fiat_from} → {asset} → {fiat_to}",
            "asset": asset,
            "fiat": fiat_from or opportunity.get("fiat", ""),
            "secondary_fiat": fiat_to,
            "score": roi,
            "profit_percentage": roi,
            "net_profit_percentage": roi,
            "liquidity": self._to_float(opportunity.get("liquidity", {}).get("max_executable_amount")),
            "liquidity_asset": asset,
            "details": opportunity,
        }

    def _passes_liquidity_threshold(self, opportunity: Dict[str, Any], min_liquidity_usd: float) -> bool:
        """Comprobar si la oportunidad tiene liquidez suficiente en términos de USD."""
        liquidity = self._to_float(opportunity.get("liquidity"))
        if liquidity <= 0:
            return False

        asset = (opportunity.get("liquidity_asset") or opportunity.get("asset") or "USDT").upper()

        if asset == "USDT":
            return liquidity >= min_liquidity_usd

        details = opportunity.get("details", {})
        # Intentar derivar precio en USD usando información disponible.
        price_usd = None

        if opportunity.get("strategy") == "spot_to_p2p":
            price_fiat = self._to_float(details.get("p2p_sell_price_fiat"))
            exchange_rate = self._to_float(details.get("exchange_rate_used"), default=1.0)
            if price_fiat > 0 and exchange_rate > 0:
                price_usd = price_fiat / exchange_rate
        elif opportunity.get("strategy") == "cross_currency":
            sell_quote = details.get("sell_quote", {})
            price_fiat = self._to_float(sell_quote.get("price"))
            fiat_to = details.get("fiat_to", "USD")
            fx_rate = settings.FX_FALLBACK_RATES.get(fiat_to, 1.0)
            if price_fiat > 0 and fx_rate > 0:
                price_usd = price_fiat / fx_rate
        elif opportunity.get("strategy") == "triangle_arbitrage":
            step2 = details.get("step_2", {})
            price_fiat = self._to_float(step2.get("price"))
            fiat_to = details.get("final_position", {}).get("currency") or opportunity.get("secondary_fiat")
            fx_rate = settings.FX_FALLBACK_RATES.get((fiat_to or "USD").upper(), 1.0)
            if price_fiat > 0 and fx_rate > 0:
                price_usd = price_fiat / fx_rate

        if price_usd is None or price_usd <= 0:
            # Si no podemos estimar el valor, asumir que la liquidez es adecuada para no perder la señal.
            return True

        notional_usd = liquidity * price_usd
        return notional_usd >= min_liquidity_usd

    def _calculate_recommended_amount(self, profit_percentage: float) -> float:
        """
        Calcular monto recomendado segun profit.
        """
        if profit_percentage < settings.ARBITRAGE_MIN_PROFIT:
            return 0.0

        if profit_percentage >= 5.0:
            return settings.MAX_TRADE_AMOUNT
        if profit_percentage >= 3.0:
            return settings.MAX_TRADE_AMOUNT * 0.7
        if profit_percentage >= 2.0:
            return settings.MAX_TRADE_AMOUNT * 0.5
        return settings.MIN_TRADE_AMOUNT

    async def execute_spot_trade(
        self,
        symbol: str,
        side: str,
        amount_usd: float,
    ) -> Optional[Dict[str, Any]]:
        """
        Ejecutar trade en Spot.
        """
        try:
            symbol_info = await self.spot_service.get_symbol_info(symbol)

            if not symbol_info:
                logger.error("Symbol info not found", symbol=symbol)
                return None

            price = await self.spot_service.get_spot_price(symbol)

            quantity = self.spot_service.calculate_quantity(
                price=price,
                notional=amount_usd,
                step_size=symbol_info["step_size"],
            )

            order = await self.spot_service.create_market_order(
                symbol=symbol,
                side=side,
                quantity=quantity,
            )

            if order:
                logger.info(
                    "Spot trade executed successfully",
                    symbol=symbol,
                    side=side,
                    quantity=quantity,
                    order_id=order["orderId"],
                )

            return order

        except Exception as exc:  # noqa: BLE001
            logger.error("Error executing spot trade", symbol=symbol, error=str(exc))
            return None

    async def get_inventory_status(self) -> Dict[str, Any]:
        """
        Obtener estado del inventario de criptomonedas.
        """
        balances = await self.spot_service.get_all_balances()

        total_usd = 0.0
        for asset_code, amount in balances.items():
            if asset_code == "USDT":
                total_usd += amount
            # TODO: Agregar conversiones adicionales si se operan otros activos.

        return {
            "balances": balances,
            "total_usd": round(total_usd, 2),
            "timestamp": datetime.utcnow().isoformat(),
        }
