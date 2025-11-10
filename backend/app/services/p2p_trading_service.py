"""Servicios para trading P2P real usando automatización de navegador."""
from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Dict, List, Optional

import structlog
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import SessionLocal
from app.models.trade import Trade, TradeStatus, TradeType
from app.services.browser_automation_service import BrowserAutomationService

logger = structlog.get_logger()


class P2PTradingService:
    """Orquestador de órdenes P2P ejecutadas vía navegador."""

    def __init__(self, *, db_session: Optional[Session] = None) -> None:
        self.browser_service = BrowserAutomationService()
        self.db: Session = db_session or SessionLocal()
        self._initialized = False
        self._init_lock = asyncio.Lock()

    async def initialize(self, *, two_fa_code: Optional[str] = None) -> None:
        """Inicializa el navegador y realiza login en Binance."""
        if self._initialized:
            return

        async with self._init_lock:
            if self._initialized:
                return

            await self.browser_service.initialize()
            logged = await self.browser_service.login(
                email=settings.BINANCE_EMAIL,
                password=settings.BINANCE_PASSWORD,
                two_fa_code=two_fa_code,
            )
            if not logged:
                raise RuntimeError("No se pudo iniciar sesión en Binance P2P")

            self._initialized = True
            logger.info("p2p_trading.initialized")

    async def execute_trade(
        self,
        *,
        asset: str,
        fiat: str,
        trade_type: str,
        amount: float,
        price: float,
        payment_methods: Optional[List[str]] = None,
        min_amount: Optional[float] = None,
        max_amount: Optional[float] = None,
    ) -> Dict:
        """Crea una orden en Binance P2P y registra el trade localmente."""
        await self.initialize()

        trade_enum = self._normalize_trade_type(trade_type)
        payments = payment_methods or []

        if amount <= 0 or price <= 0:
            raise ValueError("Los valores de amount y price deben ser positivos")

        trade = Trade(
            trade_type=trade_enum,
            status=TradeStatus.PENDING,
            asset=asset.upper(),
            fiat=fiat.upper(),
            crypto_amount=amount,
            fiat_amount=amount * price,
            price=price,
            profit_margin=0.0,
            is_automated=True,
            payment_method=",".join(payments),
        )

        try:
            self.db.add(trade)
            self.db.commit()
            self.db.refresh(trade)
        except SQLAlchemyError as exc:
            self.db.rollback()
            logger.error("p2p_trading.db_error", error=str(exc))
            raise

        try:
            result = await self.browser_service.create_p2p_order(
                asset=asset.upper(),
                fiat=fiat.upper(),
                trade_type=trade_enum.name.upper(),
                price=price,
                amount=amount,
                payment_methods=payments,
                min_amount=min_amount,
                max_amount=max_amount,
            )
        except Exception as exc:  # pragma: no cover - network/UI dependent
            logger.error("p2p_trading.browser_error", trade_id=trade.id, error=str(exc))
            self._mark_trade_failed(trade, str(exc))
            return {"success": False, "trade_id": trade.id, "error": str(exc)}

        if result.get("success"):
            order_id = result.get("order_id")
            trade.status = TradeStatus.IN_PROGRESS
            trade.binance_order_id = order_id
            trade.updated_at = datetime.utcnow()
            self.db.commit()
            logger.info(
                "p2p_trading.trade_started",
                trade_id=trade.id,
                order_id=order_id,
                trade_type=trade_enum.value,
            )
            return {
                "success": True,
                "trade_id": trade.id,
                "order_id": order_id,
                "message": result.get("message", "Orden P2P creada"),
            }

        error_msg = result.get("error") or result.get("message") or "Error desconocido"
        self._mark_trade_failed(trade, error_msg)
        return {"success": False, "trade_id": trade.id, "error": error_msg}

    async def cancel_trade(self, trade_id: int) -> Dict:
        """Cancela una orden P2P existente."""
        await self.initialize()
        trade = self.db.query(Trade).filter(Trade.id == trade_id).first()

        if not trade:
            return {"success": False, "error": "Trade no encontrado"}
        if not trade.binance_order_id:
            return {"success": False, "error": "La operación no tiene order_id asociado"}

        result = await self.browser_service.cancel_p2p_order(trade.binance_order_id)
        if result.get("success"):
            trade.status = TradeStatus.CANCELLED
            trade.updated_at = datetime.utcnow()
            self.db.commit()
            logger.info("p2p_trading.trade_cancelled", trade_id=trade.id)
            return {"success": True, "message": result.get("message", "Trade cancelado")}

        error_msg = result.get("error", "No se pudo cancelar la orden")
        logger.error("p2p_trading.cancel_failed", trade_id=trade.id, error=error_msg)
        return {"success": False, "error": error_msg}

    async def get_active_orders(self) -> List[Dict]:
        """Devuelve las órdenes P2P activas según la vista web de Binance."""
        await self.initialize()
        return await self.browser_service.get_p2p_orders()

    async def close(self) -> None:
        """Libera la sesión de navegador y la conexión a la base de datos."""
        if self.browser_service:
            await self.browser_service.close()
        if self.db:
            self.db.close()
        self._initialized = False

    def _normalize_trade_type(self, trade_type: str) -> TradeType:
        mapped = (trade_type or "").upper()
        if mapped not in {"BUY", "SELL"}:
            raise ValueError("trade_type debe ser BUY o SELL")
        return TradeType.BUY if mapped == "BUY" else TradeType.SELL

    def _mark_trade_failed(self, trade: Trade, error: str) -> None:
        trade.status = TradeStatus.FAILED
        trade.error_message = error
        trade.updated_at = datetime.utcnow()
        self.db.commit()
