"""Browser automation helpers for Binance P2P flows."""
from __future__ import annotations

import asyncio
import time
from typing import Dict, List, Optional

import structlog
from playwright.async_api import (
    Browser,
    BrowserContext,
    Page,
    TimeoutError as PlaywrightTimeoutError,
    async_playwright,
)

from app.core.config import settings

logger = structlog.get_logger()


class BrowserAutomationService:
    """Automatiza interacciones básicas con Binance P2P usando Playwright."""

    def __init__(self) -> None:
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.playwright = None
        self._initialized = False
        self._init_lock = asyncio.Lock()
        self._default_timeout = max(5000, settings.BROWSER_TIMEOUT)

    async def initialize(self) -> None:
        """Inicia Playwright y crea un contexto de navegador reutilizable."""
        if self._initialized:
            return

        async with self._init_lock:
            if self._initialized:
                return

            try:
                self.playwright = await async_playwright().start()
                self.browser = await self.playwright.chromium.launch(
                    headless=settings.BROWSER_HEADLESS,
                    args=[
                        "--disable-blink-features=AutomationControlled",
                        "--disable-dev-shm-usage",
                        "--disable-infobars",
                        "--ignore-certificate-errors",
                        "--no-sandbox",
                    ],
                )
                self.context = await self.browser.new_context(
                    viewport={"width": 1920, "height": 1080},
                    user_agent=(
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/120.0.0.0 Safari/537.36"
                    ),
                )
                self.context.set_default_timeout(self._default_timeout)
                self.page = await self.context.new_page()
                self.page.set_default_timeout(self._default_timeout)
                self._initialized = True
                logger.info(
                    "browser_automation.initialized",
                    headless=settings.BROWSER_HEADLESS,
                    timeout_ms=self._default_timeout,
                    pool_size=settings.BROWSER_POOL_SIZE,
                )
            except Exception as exc:  # pragma: no cover - defensive
                logger.error("browser_automation.init_failed", error=str(exc))
                await self.close()
                raise

    async def login(self, email: str, password: str, two_fa_code: Optional[str] = None) -> bool:
        """Realiza login en Binance."""
        await self._ensure_ready()

        if not email or not password:
            logger.error("browser_automation.missing_credentials")
            raise ValueError("Se requieren credenciales de Binance P2P para iniciar sesión")

        try:
            await self.page.goto("https://www.binance.com/en/login", wait_until="networkidle")
            await self.page.wait_for_selector('input[type="email"]')
            await self.page.fill('input[type="email"]', email)
            await self.page.fill('input[type="password"]', password)
            await self.page.click('button[type="submit"]')
            await asyncio.sleep(3)

            if settings.BINANCE_2FA_ENABLED:
                if not two_fa_code:
                    logger.warning("browser_automation.2fa_required")
                else:
                    await self.page.fill('input[placeholder*="code" i]', two_fa_code)
                    await self.page.click('button[type="submit"]')
                    await asyncio.sleep(3)

            await self.page.wait_for_url("https://www.binance.com/**", timeout=self._default_timeout)
            logger.info("browser_automation.login_success")
            return True
        except PlaywrightTimeoutError as exc:
            logger.error("browser_automation.login_timeout", error=str(exc))
            return False
        except Exception as exc:  # pragma: no cover - network/UI dependent
            logger.error("browser_automation.login_failed", error=str(exc))
            return False

    async def navigate_to_p2p(self) -> bool:
        """Abre la sección principal de Binance P2P."""
        await self._ensure_ready()
        try:
            await self.page.goto("https://www.binance.com/en/p2p", wait_until="networkidle")
            await asyncio.sleep(2)
            logger.info("browser_automation.opened_p2p")
            return True
        except Exception as exc:  # pragma: no cover - network/UI dependent
            logger.error("browser_automation.open_p2p_failed", error=str(exc))
            return False

    async def create_p2p_order(
        self,
        *,
        asset: str,
        fiat: str,
        trade_type: str,
        price: float,
        amount: float,
        payment_methods: List[str],
        min_amount: Optional[float] = None,
        max_amount: Optional[float] = None,
    ) -> Dict:
        """Publica una orden en Binance P2P."""
        await self._ensure_ready()

        try:
            if not await self.navigate_to_p2p():
                raise RuntimeError("No se pudo abrir la página de P2P")

            await self.page.click('button:has-text("Post an Ad")', timeout=self._default_timeout)
            await asyncio.sleep(2)

            order_type_button = "Buy" if trade_type.upper() == "BUY" else "Sell"
            await self.page.click(f'button:has-text("{order_type_button}")')
            await asyncio.sleep(1)

            await self._select_dropdown_value(asset)
            await self._select_dropdown_value(fiat)

            price_input = await self.page.wait_for_selector('input[placeholder*="Price" i]')
            await price_input.fill(str(price))

            amount_input = await self.page.wait_for_selector('input[placeholder*="Amount" i]')
            await amount_input.fill(str(amount))

            for method in payment_methods or []:
                await self._select_dropdown_value(method.strip(), strict=False)

            if min_amount is not None:
                min_input = await self.page.wait_for_selector('input[placeholder*="Min" i]')
                await min_input.fill(str(min_amount))

            if max_amount is not None:
                max_input = await self.page.wait_for_selector('input[placeholder*="Max" i]')
                await max_input.fill(str(max_amount))

            await self.page.click('button:has-text("Post")', timeout=self._default_timeout)
            await asyncio.sleep(3)

            confirmation = await self.page.wait_for_selector('div:has-text("success" i)', timeout=self._default_timeout)
            if not confirmation:
                raise RuntimeError("Binance no confirmó la publicación del anuncio")

            order_id = await self._fetch_last_order_id()
            logger.info(
                "browser_automation.order_created",
                asset=asset,
                fiat=fiat,
                trade_type=trade_type,
                order_id=order_id,
            )
            return {
                "success": True,
                "order_id": order_id,
                "message": "Orden P2P creada correctamente",
            }
        except Exception as exc:  # pragma: no cover - network/UI dependent
            logger.error("browser_automation.order_failed", error=str(exc))
            return {
                "success": False,
                "error": str(exc),
            }

    async def cancel_p2p_order(self, order_id: str) -> Dict:
        """Cancela una orden en la sección "My Ads"."""
        await self._ensure_ready()
        try:
            if not await self.navigate_to_p2p():
                raise RuntimeError("No se pudo abrir Binance P2P")

            await self.page.click('a:has-text("My Ads")', timeout=self._default_timeout)
            await asyncio.sleep(2)

            order_selector = f'div[data-order-id="{order_id}"]'
            await self.page.wait_for_selector(order_selector, timeout=self._default_timeout)
            cancel_button = self.page.locator(f"{order_selector} button:has-text(\"Cancel\")")
            await cancel_button.click()
            await asyncio.sleep(1)
            await self.page.click('button:has-text("Confirm")', timeout=self._default_timeout)
            await asyncio.sleep(2)
            logger.info("browser_automation.order_cancelled", order_id=order_id)
            return {"success": True, "message": "Orden cancelada correctamente"}
        except Exception as exc:  # pragma: no cover - network/UI dependent
            logger.error("browser_automation.cancel_failed", order_id=order_id, error=str(exc))
            return {"success": False, "error": str(exc)}

    async def get_p2p_orders(self) -> List[Dict]:
        """Devuelve el listado básico de anuncios activos."""
        await self._ensure_ready()
        try:
            if not await self.navigate_to_p2p():
                return []

            await self.page.click('a:has-text("My Ads")', timeout=self._default_timeout)
            await asyncio.sleep(2)
            orders: List[Dict] = []
            for element in await self.page.query_selector_all('div[data-order-id]'):
                order_id = await element.get_attribute("data-order-id")
                if not order_id:
                    continue
                orders.append({
                    "order_id": order_id,
                    "raw_html": await element.inner_text(),
                })
            return orders
        except Exception as exc:  # pragma: no cover - network/UI dependent
            logger.error("browser_automation.orders_failed", error=str(exc))
            return []

    async def close(self) -> None:
        """Libera recursos de Playwright."""
        try:
            if self.page:
                await self.page.close()
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
        finally:
            self.browser = None
            self.context = None
            self.page = None
            self.playwright = None
            self._initialized = False

    async def _ensure_ready(self) -> None:
        if not self._initialized or not self.page:
            await self.initialize()

    async def _select_dropdown_value(self, label: str, *, strict: bool = True) -> None:
        if not label:
            return
        selector = f'div:has-text("{label}")'
        try:
            await self.page.click(selector, timeout=self._default_timeout)
            await asyncio.sleep(0.3)
        except Exception:
            if strict:
                raise

    async def _fetch_last_order_id(self) -> Optional[str]:
        """Intenta leer el ID del anuncio más reciente."""
        try:
            orders = await self.get_p2p_orders()
            if orders:
                return orders[0].get("order_id") or f"p2p-{int(time.time()*1000)}"
        except Exception:
            pass
        return f"p2p-{int(time.time()*1000)}"
