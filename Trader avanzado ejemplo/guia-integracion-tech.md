# GUÍA COMPLETA DE INTEGRACIÓN - SISTEMA EXPERTO DE TRADING SIMULADO

## 📋 ÍNDICE RÁPIDO

1. [Setup Inicial](#setup-inicial)
2. [Integración del Prompt](#integración-del-prompt)
3. [APIs y Datos Reales](#apis-y-datos-reales)
4. [Base de Datos](#base-de-datos)
5. [Lógica de Simulación](#lógica-de-simulación)
6. [Testing y Validación](#testing-y-validación)
7. [Deployment](#deployment)

---

## Setup Inicial

### Requisitos del Sistema

```bash
# Backend
- Python 3.9+
- Node.js 16+ (si usas TypeScript/JavaScript)
- PostgreSQL o MySQL

# Frontend
- React 18+ o Vue 3+
- WebSocket para actualizaciones tiempo real

# APIs Externas (Gratuitas)
- OpenExchangeRates (forex en tiempo real)
- Freecurrencyapi.com (histórico)
- Finnhub (calendarios económicos)
```

### Instalación Base

```bash
# Clonar o crear proyecto
mkdir trading-expert-system
cd trading-expert-system

# Backend
mkdir backend
cd backend
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
pip install -r requirements.txt

# Frontend
cd ../frontend
npm create react-app trading-dashboard
cd trading-dashboard
npm install axios chart.js react-chartjs-2 websocket
```

---

## Integración del Prompt

### Paso 1: Cargar Prompt Maestro en tu LLM

El prompt maestro debe estar disponible para la IA de dos formas:

**OPCIÓN A: Como archivo del sistema**
```python
# config/prompts.py
MASTER_TRADING_PROMPT = """
[AQUÍ VA EL CONTENIDO COMPLETO DEL PROMPT EXPERTO]
...[ver archivo prompt-trading-expert.md]...
"""

def initialize_ai_context():
    """Inicializa el contexto del LLM con el prompt maestro"""
    return {
        'system_prompt': MASTER_TRADING_PROMPT,
        'model': 'gpt-4-turbo',  # O Claude, Gemini, etc.
        'temperature': 0.2,  # Bajo para consistencia
        'max_tokens': 2000
    }
```

**OPCIÓN B: Como inyección en cada llamada**
```python
import openai

def call_trading_expert(user_query, previous_context=None):
    """
    Llama al modelo de IA con contexto de experto
    """
    messages = [
        {
            "role": "system",
            "content": MASTER_TRADING_PROMPT  # El prompt maestro
        }
    ]
    
    # Agregar contexto previo (historial de operaciones)
    if previous_context:
        messages.append({
            "role": "assistant",
            "content": previous_context
        })
    
    # Consulta del usuario
    messages.append({
        "role": "user",
        "content": user_query
    })
    
    response = openai.ChatCompletion.create(
        model="gpt-4-turbo",
        messages=messages,
        temperature=0.2
    )
    
    return response.choices[0].message.content
```

### Paso 2: Integraciones de Comandos

```python
# trading/commands.py
class TradingCommands:
    def __init__(self, ai_context):
        self.ai = ai_context
        self.db = Database()
    
    def ANALIZAR(self, pair, timeframe):
        """
        Ejecuta: /ANALIZAR EUR/USD H1
        Retorna análisis técnico completo del pair
        """
        query = f"""
        Realiza análisis técnico completo de {pair} en timeframe {timeframe}.
        Incluye: RSI, MACD, Soportes/Resistencias, Tendencia.
        Formato: <ANÁLISIS_FOREX> ... </ANÁLISIS_FOREX>
        """
        result = call_trading_expert(query)
        return self.parse_forex_analysis(result)
    
    def SEÑAL_NUEVA(self):
        """
        Ejecuta: /SEÑAL_NUEVA
        Escanea todos los pares y retorna señales > 70 confianza
        """
        pares = ['EUR/USD', 'GBP/USD', 'USD/JPY', 'AUD/USD', 'USD/CAD']
        query = f"""
        Escanea estos pares y genera señales de trading:
        {', '.join(pares)}
        
        Retorna SOLO señales con confianza >= 70.
        Formato: JSON con pair, signal, confidence, entry, stop_loss, take_profit
        """
        result = call_trading_expert(query)
        return json.loads(self.extract_json(result))
    
    def EJECUTAR_ORDEN(self, direction, pair, entry, stop_loss, take_profit):
        """
        Ejecuta: /EJECUTAR_ORDEN BUY EUR/USD 1.0850 1.0810 1.0910
        Crea orden VIRTUAL en el simulador
        """
        # Validaciones
        sl_pips = abs((entry - stop_loss) / 0.0001)
        tp_pips = abs((take_profit - entry) / 0.0001)
        ratio = tp_pips / sl_pips
        
        if not self.validate_order(sl_pips, tp_pips, ratio):
            return {'error': 'Orden no válida', 'reason': 'Falló validación'}
        
        # Crear orden VIRTUAL
        order = self.create_virtual_order(
            direction=direction,
            pair=pair,
            entry_price=entry,
            stop_loss=stop_loss,
            take_profit=take_profit
        )
        
        # Registrar en BD
        self.db.insert('virtual_orders', order)
        
        return {
            'status': 'OPEN',
            'order_id': order['id'],
            'message': f'Orden virtual {direction} creada'
        }
    
    def validate_order(self, sl_pips, tp_pips, ratio):
        """Valida reglas de riesgo"""
        return (
            sl_pips >= 20 and
            sl_pips <= 100 and
            ratio >= 1.5 and
            len(self.open_orders) < 5
        )
```

---

## APIs y Datos Reales

### Integración de Fuentes de Datos

```python
# data/forex_api.py
import requests
import json
from datetime import datetime

class ForexDataProvider:
    def __init__(self):
        self.openexchange_url = "https://api.exchangerate-api.com/v4/latest"
        self.freecurrency_url = "https://api.freecurrencyapi.com/latest"
        self.cache = {}  # Cache local
    
    def get_realtime_rate(self, base_currency, target_currency):
        """
        Obtiene tipo de cambio en tiempo real
        Parámetro: base_currency = 'EUR', target_currency = 'USD'
        Retorna: 1.0850 (ejemplo EUR/USD)
        """
        try:
            pair_key = f"{base_currency}{target_currency}"
            
            # Verificar cache
            if pair_key in self.cache:
                cached_time = self.cache[pair_key]['timestamp']
                if (datetime.now() - cached_time).seconds < 60:
                    return self.cache[pair_key]['rate']
            
            # Obtener de OpenExchangeRates
            response = requests.get(
                f"{self.openexchange_url}/{base_currency}",
                timeout=5
            )
            data = response.json()
            
            rate = data['rates'].get(target_currency)
            
            if rate:
                # Cachear
                self.cache[pair_key] = {
                    'rate': rate,
                    'timestamp': datetime.now()
                }
                return rate
            
        except Exception as e:
            print(f"Error obteniendo {pair_key}: {e}")
            return None
    
    def get_historical_data(self, pair, days=30):
        """
        Obtiene datos históricos para backtesting
        Retorna: Array de candles OHLC
        """
        # Simulación: en producción usarías Alpha Vantage o similar
        return self._generate_historical_candles(pair, days)
    
    def get_economic_calendar(self):
        """
        Obtiene próximos eventos económicos importantes
        Retorna: Array de eventos [{"time": "13:30", "impact": "HIGH", "event": "NFP"}]
        """
        events = [
            {
                "time": "13:30 UTC",
                "impact": "HIGH",
                "event": "NFP USA",
                "actual": None,
                "forecast": 215000
            },
            {
                "time": "19:00 UTC",
                "impact": "MEDIUM",
                "event": "ECB Decision",
                "actual": None,
                "forecast": 4.5
            }
        ]
        return events

# Inicializar proveedor de datos
forex_provider = ForexDataProvider()
```

### Obtención de Datos en Tiempo Real

```python
# data/real_time_feed.py
import asyncio
import websockets
import json
from datetime import datetime

class RealtimeFeed:
    def __init__(self):
        self.current_prices = {}
        self.price_history = {}
        self.subscribers = []
    
    async def start_feed(self):
        """Inicia la alimentación de datos en tiempo real"""
        while True:
            # Cada 60 segundos
            await asyncio.sleep(60)
            
            for pair in ['EUR/USD', 'GBP/USD', 'USD/JPY', 'AUD/USD', 'USD/CAD']:
                # Obtener precio real
                base, target = pair.split('/')
                price = forex_provider.get_realtime_rate(base, target)
                
                if price:
                    # Crear candle OHLC simulado
                    candle = self.create_candle(pair, price)
                    
                    # Guardar en histórico
                    if pair not in self.price_history:
                        self.price_history[pair] = []
                    self.price_history[pair].append(candle)
                    
                    # Notificar a suscriptores
                    await self.broadcast({
                        'type': 'PRICE_UPDATE',
                        'pair': pair,
                        'price': price,
                        'candle': candle
                    })
    
    def create_candle(self, pair, current_price):
        """Crea candle OHLC para el período"""
        # En producción, usarías datos OHLC reales
        return {
            'timestamp': datetime.now().isoformat(),
            'open': current_price * 0.998,
            'high': current_price * 1.002,
            'low': current_price * 0.997,
            'close': current_price,
            'volume': 1000
        }
    
    async def broadcast(self, message):
        """Envía actualización a todos los clientes WebSocket"""
        # Aquí se conectaría con WebSocket del frontend
        for subscriber in self.subscribers:
            await subscriber.send(json.dumps(message))
```

---

## Base de Datos

### Esquema SQL Completo

```sql
-- Tabla de Pares de Divisas
CREATE TABLE currency_pairs (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(10) NOT NULL UNIQUE,
    base_currency VARCHAR(3),
    target_currency VARCHAR(3),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO currency_pairs (name, base_currency, target_currency) VALUES
('EUR/USD', 'EUR', 'USD'),
('GBP/USD', 'GBP', 'USD'),
('USD/JPY', 'USD', 'JPY'),
('AUD/USD', 'AUD', 'USD'),
('USD/CAD', 'USD', 'CAD');

-- Tabla de Órdenes Virtuales
CREATE TABLE virtual_orders (
    id INT PRIMARY KEY AUTO_INCREMENT,
    pair_id INT NOT NULL,
    direction ENUM('BUY', 'SELL') NOT NULL,
    entry_price DECIMAL(10, 5) NOT NULL,
    stop_loss DECIMAL(10, 5) NOT NULL,
    take_profit DECIMAL(10, 5) NOT NULL,
    lot_size DECIMAL(10, 4) NOT NULL,
    risk_amount DECIMAL(10, 2) NOT NULL,
    status ENUM('OPEN', 'CLOSED', 'CANCELLED') DEFAULT 'OPEN',
    entry_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    exit_price DECIMAL(10, 5),
    exit_timestamp DATETIME,
    result_pips INT,
    result_usd DECIMAL(10, 2),
    close_reason ENUM('TP', 'SL', 'MANUAL', 'TIMEOUT'),
    FOREIGN KEY (pair_id) REFERENCES currency_pairs(id)
) ENGINE=InnoDB;

-- Tabla de Precios Históricos
CREATE TABLE price_history (
    id INT PRIMARY KEY AUTO_INCREMENT,
    pair_id INT NOT NULL,
    timeframe VARCHAR(5) NOT NULL,
    timestamp DATETIME NOT NULL,
    open DECIMAL(10, 5),
    high DECIMAL(10, 5),
    low DECIMAL(10, 5),
    close DECIMAL(10, 5),
    volume INT,
    UNIQUE KEY unique_price (pair_id, timeframe, timestamp),
    FOREIGN KEY (pair_id) REFERENCES currency_pairs(id)
) ENGINE=InnoDB;

-- Tabla de Estadísticas de Sesión
CREATE TABLE session_stats (
    id INT PRIMARY KEY AUTO_INCREMENT,
    date DATE NOT NULL UNIQUE,
    total_trades INT DEFAULT 0,
    winning_trades INT DEFAULT 0,
    losing_trades INT DEFAULT 0,
    win_rate DECIMAL(5, 4),
    profit_factor DECIMAL(8, 2),
    total_pips INT,
    max_drawdown DECIMAL(5, 2),
    sharpe_ratio DECIMAL(8, 2),
    capital_initial DECIMAL(15, 2),
    capital_final DECIMAL(15, 2),
    daily_return DECIMAL(5, 2)
);

-- Tabla de Eventos Económicos
CREATE TABLE economic_events (
    id INT PRIMARY KEY AUTO_INCREMENT,
    event_name VARCHAR(100),
    impact ENUM('LOW', 'MEDIUM', 'HIGH'),
    scheduled_time DATETIME,
    currency VARCHAR(3),
    forecast DECIMAL(10, 4),
    actual DECIMAL(10, 4),
    previous DECIMAL(10, 4)
);
```

### Clase de Conexión a BD

```python
# database/db.py
import mysql.connector
from contextlib import contextmanager

class Database:
    def __init__(self, config):
        self.config = config
        self.connection = None
    
    @contextmanager
    def get_connection(self):
        """Context manager para conexiones seguras"""
        try:
            conn = mysql.connector.connect(**self.config)
            yield conn
            conn.commit()
        except Exception as e:
            print(f"Error de BD: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    def insert_order(self, order_data):
        """Inserta orden virtual"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            query = """
                INSERT INTO virtual_orders 
                (pair_id, direction, entry_price, stop_loss, take_profit, 
                 lot_size, risk_amount)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(query, (
                order_data['pair_id'],
                order_data['direction'],
                order_data['entry_price'],
                order_data['stop_loss'],
                order_data['take_profit'],
                order_data['lot_size'],
                order_data['risk_amount']
            ))
            return cursor.lastrowid
    
    def close_order(self, order_id, exit_price, close_reason):
        """Cierra una orden"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            query = """
                UPDATE virtual_orders
                SET status = 'CLOSED',
                    exit_price = %s,
                    exit_timestamp = NOW(),
                    close_reason = %s
                WHERE id = %s
            """
            cursor.execute(query, (exit_price, close_reason, order_id))
    
    def get_session_stats(self):
        """Obtiene estadísticas de la sesión"""
        with self.get_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            query = """
                SELECT
                    COUNT(*) as total_trades,
                    SUM(CASE WHEN result_usd > 0 THEN 1 ELSE 0 END) as winning_trades,
                    SUM(CASE WHEN result_usd <= 0 THEN 1 ELSE 0 END) as losing_trades,
                    SUM(result_pips) as total_pips,
                    AVG(result_pips) as avg_pips,
                    SUM(result_usd) as total_usd
                FROM virtual_orders
                WHERE DATE(entry_timestamp) = CURDATE()
                AND status = 'CLOSED'
            """
            cursor.execute(query)
            return cursor.fetchone()

# Inicializar BD
db_config = {
    'host': 'localhost',
    'user': 'trading_user',
    'password': 'secure_password',
    'database': 'trading_simulator'
}
db = Database(db_config)
```

---

## Lógica de Simulación

### Motor de Monitoreo de Órdenes

```python
# trading/order_monitor.py
import threading
from datetime import datetime, timedelta

class OrderMonitor:
    def __init__(self, db, data_provider):
        self.db = db
        self.data_provider = data_provider
        self.running = False
        self.thread = None
    
    def start(self):
        """Inicia monitoreo de órdenes abiertas"""
        self.running = True
        self.thread = threading.Thread(target=self._monitor_loop)
        self.thread.start()
    
    def _monitor_loop(self):
        """Loop de monitoreo cada 60 segundos"""
        while self.running:
            self._check_open_orders()
            threading.Event().wait(60)  # Esperar 60 segundos
    
    def _check_open_orders(self):
        """Verifica órdenes abiertas contra precios actuales"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            
            # Obtener órdenes abiertas
            query = """
                SELECT vo.*, cp.name as pair_name
                FROM virtual_orders vo
                JOIN currency_pairs cp ON vo.pair_id = cp.id
                WHERE vo.status = 'OPEN'
            """
            cursor.execute(query)
            open_orders = cursor.fetchall()
            
            for order in open_orders:
                # Obtener precio actual
                pair_name = order['pair_name']
                base, target = pair_name.split('/')
                current_price = self.data_provider.get_realtime_rate(base, target)
                
                if not current_price:
                    continue
                
                # Verificar si alcanzó TP
                if self._check_take_profit(order, current_price):
                    self._close_order(order['id'], order['take_profit'], 'TP')
                    print(f"✓ GANANCIA: Orden {order['id']} cerrada en TP")
                
                # Verificar si alcanzó SL
                elif self._check_stop_loss(order, current_price):
                    self._close_order(order['id'], order['stop_loss'], 'SL')
                    print(f"✗ PÉRDIDA: Orden {order['id']} cerrada en SL")
                
                # Verificar timeout (4 horas)
                elif self._check_timeout(order):
                    self._close_order(order['id'], current_price, 'TIMEOUT')
                    print(f"⏱ TIMEOUT: Orden {order['id']} cerrada por tiempo")
    
    def _check_take_profit(self, order, current_price):
        """Verifica si el precio alcanzó TP"""
        if order['direction'] == 'BUY':
            return current_price >= order['take_profit']
        else:
            return current_price <= order['take_profit']
    
    def _check_stop_loss(self, order, current_price):
        """Verifica si el precio alcanzó SL"""
        if order['direction'] == 'BUY':
            return current_price <= order['stop_loss']
        else:
            return current_price >= order['stop_loss']
    
    def _check_timeout(self, order):
        """Verifica si pasaron 4 horas desde entrada"""
        elapsed = datetime.now() - order['entry_timestamp']
        return elapsed > timedelta(hours=4)
    
    def _close_order(self, order_id, exit_price, close_reason):
        """Cierra orden y calcula P&L"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            
            # Obtener datos de orden
            query = "SELECT * FROM virtual_orders WHERE id = %s"
            cursor.execute(query, (order_id,))
            order = cursor.fetchone()
            
            # Calcular pips
            if order['direction'] == 'BUY':
                pips = (exit_price - order['entry_price']) / 0.0001
            else:
                pips = (order['entry_price'] - exit_price) / 0.0001
            
            # Calcular USD
            usd_pnl = pips * 10 * order['lot_size']
            
            # Actualizar orden
            update_query = """
                UPDATE virtual_orders
                SET status = 'CLOSED',
                    exit_price = %s,
                    exit_timestamp = NOW(),
                    result_pips = %s,
                    result_usd = %s,
                    close_reason = %s
                WHERE id = %s
            """
            cursor.execute(update_query, (exit_price, int(pips), usd_pnl, close_reason, order_id))
            
            # Broadcast a clientes
            self._notify_clients(order_id, close_reason, pips, usd_pnl)
    
    def _notify_clients(self, order_id, reason, pips, usd):
        """Notifica a clientes WebSocket sobre cierre de orden"""
        # Aquí iría código para enviar WebSocket a frontend
        pass
```

---

## Testing y Validación

### Test Suite Básico

```python
# tests/test_trading_logic.py
import unittest
from trading.simulator import TradingSimulator
from data.forex_api import ForexDataProvider

class TestTradingLogic(unittest.TestCase):
    def setUp(self):
        self.simulator = TradingSimulator(virtual_capital=10000)
        self.provider = ForexDataProvider()
    
    def test_create_order(self):
        """Test: Crear orden virtual"""
        order = self.simulator.create_order(
            pair='EUR/USD',
            direction='BUY',
            entry=1.0850,
            sl=1.0810,
            tp=1.0910
        )
        
        self.assertEqual(order['status'], 'OPEN')
        self.assertEqual(order['pair'], 'EUR/USD')
        self.assertEqual(order['lot_size'], 0.25)  # Calculado
    
    def test_validate_sl_range(self):
        """Test: SL debe estar entre 20 y 100 pips"""
        # SL < 20 pips debe fallar
        with self.assertRaises(ValueError):
            self.simulator.create_order(
                pair='EUR/USD',
                direction='BUY',
                entry=1.0850,
                sl=1.0835,  # Solo 15 pips
                tp=1.0910
            )
        
        # SL > 100 pips debe fallar
        with self.assertRaises(ValueError):
            self.simulator.create_order(
                pair='EUR/USD',
                direction='BUY',
                entry=1.0850,
                sl=1.0740,  # 110 pips
                tp=1.0910
            )
    
    def test_risk_reward_ratio(self):
        """Test: R:R debe ser mínimo 1:1.5"""
        # R:R = 1:1 debe fallar
        with self.assertRaises(ValueError):
            self.simulator.create_order(
                pair='EUR/USD',
                direction='BUY',
                entry=1.0850,
                sl=1.0810,  # 40 pips de riesgo
                tp=1.0890   # 40 pips de ganancia (ratio 1:1)
            )
    
    def test_max_concurrent_orders(self):
        """Test: Máximo 5 órdenes simultáneas"""
        # Crear 5 órdenes OK
        for i in range(5):
            self.simulator.create_order(
                pair=f'PAIR{i}',
                direction='BUY',
                entry=1.0850,
                sl=1.0810,
                tp=1.0910
            )
        
        # La 6ta debe fallar
        with self.assertRaises(ValueError):
            self.simulator.create_order(
                pair='PAIR6',
                direction='BUY',
                entry=1.0850,
                sl=1.0810,
                tp=1.0910
            )

if __name__ == '__main__':
    unittest.main()
```

---

## Deployment

### Docker Compose

```yaml
# docker-compose.yml
version: '3.8'

services:
  mysql:
    image: mysql:8.0
    environment:
      MYSQL_ROOT_PASSWORD: root_password
      MYSQL_DATABASE: trading_simulator
      MYSQL_USER: trading_user
      MYSQL_PASSWORD: secure_password
    ports:
      - "3306:3306"
    volumes:
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql

  backend:
    build: ./backend
    ports:
      - "5000:5000"
    environment:
      DB_HOST: mysql
      DB_USER: trading_user
      DB_PASSWORD: secure_password
      DB_NAME: trading_simulator
    depends_on:
      - mysql
    command: python app.py

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      REACT_APP_API_URL: http://localhost:5000
    depends_on:
      - backend

volumes:
  mysql_data:
```

### Deployment en producción

```bash
# Build
docker-compose build

# Run
docker-compose up -d

# Logs
docker-compose logs -f backend

# Stop
docker-compose down
```

---

## ✅ CHECKLIST DE IMPLEMENTACIÓN

- [ ] Copiar MASTER_TRADING_PROMPT al sistema
- [ ] Configurar APIs de datos (OpenExchangeRates, etc.)
- [ ] Crear BD según esquema SQL
- [ ] Implementar TradingSimulator sin transferencia de fondos
- [ ] Integrar WebSocket para tiempo real
- [ ] Crear Dashboard React/Vue
- [ ] Implementar Order Monitor
- [ ] Completar test suite
- [ ] Documentar API REST
- [ ] Desplegar en producción

**El sistema está listo para comenzar a operar virtualmente con datos reales sin riesgo de pérdida de capital.**

