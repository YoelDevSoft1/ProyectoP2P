"""
Servicio para Binance Spot API.
Trading automático oficial con API documentada.
"""
from binance.spot import Spot
from binance.error import ClientError, ServerError
from typing import Optional, Dict, List
import structlog
from decimal import Decimal

from app.core.config import settings

logger = structlog.get_logger()


class BinanceSpotService:
    """
    Servicio para operar en Binance Spot usando API oficial.

    Funcionalidades:
    - Trading automático de cripto
    - Consulta de balances
    - Histórico de precios
    - Órdenes market y limit
    """

    def __init__(self):
        """Inicializar cliente de Binance Spot"""
        self.client = Spot(
            api_key=settings.BINANCE_API_KEY,
            api_secret=settings.BINANCE_API_SECRET,
            base_url='https://api.binance.com' if not settings.BINANCE_TESTNET else 'https://testnet.binance.vision'
        )

    async def get_account_balance(self, asset: str = "USDT") -> float:
        """
        Obtener balance de una moneda específica.

        Args:
            asset: Símbolo de la moneda (USDT, BTC, etc.)

        Returns:
            Balance disponible
        """
        try:
            account = self.client.account()

            for balance in account['balances']:
                if balance['asset'] == asset:
                    return float(balance['free'])

            return 0.0

        except ClientError as e:
            logger.error("Error getting account balance", error=str(e))
            return 0.0

    async def get_spot_price(self, symbol: str = "USDTUSDC") -> float:
        """
        Obtener precio actual en Spot.

        Args:
            symbol: Par de trading (ej: USDTUSDC, BTCUSDT)

        Returns:
            Precio actual
        """
        try:
            ticker = self.client.ticker_price(symbol=symbol)
            return float(ticker['price'])

        except ClientError as e:
            logger.error("Error getting spot price", symbol=symbol, error=str(e))
            return 0.0

    async def get_all_balances(self) -> Dict[str, float]:
        """
        Obtener todos los balances de la cuenta.

        Returns:
            Dict con asset: balance
        """
        try:
            account = self.client.account()
            balances = {}

            for balance in account['balances']:
                free = float(balance['free'])
                if free > 0:
                    balances[balance['asset']] = free

            return balances

        except ClientError as e:
            logger.error("Error getting all balances", error=str(e))
            return {}

    async def create_market_order(
        self,
        symbol: str,
        side: str,
        quantity: float
    ) -> Optional[Dict]:
        """
        Crear orden de mercado (ejecución inmediata).

        Args:
            symbol: Par (ej: BTCUSDT)
            side: BUY o SELL
            quantity: Cantidad a operar

        Returns:
            Datos de la orden o None si falla
        """
        try:
            order = self.client.new_order(
                symbol=symbol,
                side=side,
                type='MARKET',
                quantity=quantity
            )

            logger.info(
                "Market order created",
                symbol=symbol,
                side=side,
                quantity=quantity,
                order_id=order['orderId']
            )

            return order

        except ClientError as e:
            logger.error(
                "Error creating market order",
                symbol=symbol,
                side=side,
                error=str(e),
                error_code=e.error_code
            )
            return None

    async def create_limit_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        price: float
    ) -> Optional[Dict]:
        """
        Crear orden limit (se ejecuta al alcanzar el precio).

        Args:
            symbol: Par (ej: BTCUSDT)
            side: BUY o SELL
            quantity: Cantidad
            price: Precio límite

        Returns:
            Datos de la orden o None si falla
        """
        try:
            order = self.client.new_order(
                symbol=symbol,
                side=side,
                type='LIMIT',
                timeInForce='GTC',  # Good Till Cancelled
                quantity=quantity,
                price=price
            )

            logger.info(
                "Limit order created",
                symbol=symbol,
                side=side,
                quantity=quantity,
                price=price,
                order_id=order['orderId']
            )

            return order

        except ClientError as e:
            logger.error(
                "Error creating limit order",
                symbol=symbol,
                side=side,
                error=str(e)
            )
            return None

    async def cancel_order(self, symbol: str, order_id: int) -> bool:
        """
        Cancelar una orden abierta.

        Args:
            symbol: Par
            order_id: ID de la orden

        Returns:
            True si se canceló exitosamente
        """
        try:
            self.client.cancel_order(symbol=symbol, orderId=order_id)
            logger.info("Order cancelled", symbol=symbol, order_id=order_id)
            return True

        except ClientError as e:
            logger.error("Error cancelling order", order_id=order_id, error=str(e))
            return False

    async def get_open_orders(self, symbol: Optional[str] = None) -> List[Dict]:
        """
        Obtener órdenes abiertas.

        Args:
            symbol: Par específico o None para todas

        Returns:
            Lista de órdenes abiertas
        """
        try:
            if symbol:
                orders = self.client.get_open_orders(symbol=symbol)
            else:
                orders = self.client.get_open_orders()

            return orders

        except ClientError as e:
            logger.error("Error getting open orders", error=str(e))
            return []

    async def get_order_status(self, symbol: str, order_id: int) -> Optional[Dict]:
        """
        Consultar estado de una orden.

        Args:
            symbol: Par
            order_id: ID de la orden

        Returns:
            Estado de la orden
        """
        try:
            order = self.client.get_order(symbol=symbol, orderId=order_id)
            return order

        except ClientError as e:
            logger.error("Error getting order status", order_id=order_id, error=str(e))
            return None

    async def get_24h_ticker(self, symbol: str) -> Optional[Dict]:
        """
        Obtener estadísticas de 24 horas.

        Args:
            symbol: Par

        Returns:
            Estadísticas (precio, volumen, cambio %)
        """
        try:
            ticker = self.client.ticker_24hr(symbol=symbol)
            return {
                'symbol': ticker['symbol'],
                'price_change': float(ticker['priceChange']),
                'price_change_percent': float(ticker['priceChangePercent']),
                'last_price': float(ticker['lastPrice']),
                'volume': float(ticker['volume']),
                'high': float(ticker['highPrice']),
                'low': float(ticker['lowPrice'])
            }

        except ClientError as e:
            logger.error("Error getting 24h ticker", symbol=symbol, error=str(e))
            return None

    async def get_symbol_info(self, symbol: str) -> Optional[Dict]:
        """
        Obtener información del par de trading.

        Args:
            symbol: Par

        Returns:
            Info del símbolo (límites, precisión, etc.)
        """
        try:
            exchange_info = self.client.exchange_info(symbol=symbol)

            if exchange_info['symbols']:
                symbol_info = exchange_info['symbols'][0]

                # Extraer límites importantes
                filters = {f['filterType']: f for f in symbol_info['filters']}

                return {
                    'symbol': symbol_info['symbol'],
                    'status': symbol_info['status'],
                    'base_asset': symbol_info['baseAsset'],
                    'quote_asset': symbol_info['quoteAsset'],
                    'min_qty': float(filters.get('LOT_SIZE', {}).get('minQty', 0)),
                    'max_qty': float(filters.get('LOT_SIZE', {}).get('maxQty', 0)),
                    'step_size': float(filters.get('LOT_SIZE', {}).get('stepSize', 0)),
                    'min_notional': float(filters.get('MIN_NOTIONAL', {}).get('minNotional', 0))
                }

            return None

        except ClientError as e:
            logger.error("Error getting symbol info", symbol=symbol, error=str(e))
            return None

    async def check_api_connection(self) -> bool:
        """
        Verificar conexión con API de Binance.

        Returns:
            True si la conexión es exitosa
        """
        try:
            self.client.ping()
            return True

        except Exception as e:
            logger.error("Binance Spot API connection failed", error=str(e))
            return False

    async def get_server_time(self) -> int:
        """
        Obtener tiempo del servidor de Binance.

        Returns:
            Timestamp en milisegundos
        """
        try:
            time_data = self.client.time()
            return time_data['serverTime']

        except ClientError as e:
            logger.error("Error getting server time", error=str(e))
            return 0

    def calculate_quantity(
        self,
        price: float,
        notional: float,
        step_size: float
    ) -> float:
        """
        Calcular cantidad válida según restricciones del símbolo.

        Args:
            price: Precio actual
            notional: Cantidad en USD que quieres operar
            step_size: Tamaño de paso del símbolo

        Returns:
            Cantidad ajustada válida
        """
        # Calcular cantidad base
        quantity = notional / price

        # Ajustar al step_size
        precision = len(str(step_size).split('.')[-1].rstrip('0'))
        quantity = round(quantity - (quantity % step_size), precision)

        return quantity
