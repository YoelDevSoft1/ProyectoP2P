# ARQUITECTURA TÉCNICA - SISTEMA DE TRADING SIMULADO SIN LIQUIDEZ

## 1. COMPONENTES PRINCIPALES DEL SISTEMA

### 1.1 Motor de Datos en Tiempo Real

```
┌─────────────────────────────────────────┐
│     FUENTES DE DATOS EXTERNAS          │
├─────────────────────────────────────────┤
│ • OpenExchangeRates API (Gratuita)      │
│ • Freecurrencyapi.com (170+ pares)      │
│ • Alpha Vantage (Forex + Datos)         │
│ • Finnhub (Calendarios económicos)      │
└──────────────────┬──────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────┐
│    BUFFER DE DATOS (Tiempo Real)       │
├─────────────────────────────────────────┤
│ • Precios OHLC cada 60 segundos        │
│ • Máximo 1,440 candles por día (D1)    │
│ • Validación de integridad             │
│ • Detección de gaps/anomalías          │
└──────────────────┬──────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────┐
│   ANÁLISIS TÉCNICO + INDICADORES       │
├─────────────────────────────────────────┤
│ • RSI (Relative Strength Index)         │
│ • MACD (Moving Average Convergence)     │
│ • Bollinger Bands (Volatilidad)         │
│ • ATR (Average True Range)              │
│ • Stochastic Oscillator                 │
│ • Soportes & Resistencias               │
└──────────────────┬──────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────┐
│   RULES ENGINE (Generador de Señales)  │
├─────────────────────────────────────────┤
│ • Score de Confianza (0-100)            │
│ • Filtros de Ruido                      │
│ • Confluencia de 2+ indicadores         │
│ • Validación Tendencia 4H               │
└──────────────────┬──────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────┐
│   SIMULADOR SIN LIQUIDEZ (Core)        │
├─────────────────────────────────────────┤
│ • Registro Virtual de Órdenes           │
│ • Cálculo de Lotes Automático           │
│ • Spread Simulado (+2-3 pips)           │
│ • Ejecución en Precio Real              │
│ • Gestión de Riesgos (1% por trade)     │
└──────────────────┬──────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────┐
│   DASHBOARD EN TIEMPO REAL              │
├─────────────────────────────────────────┤
│ • Gráficos de Precios                   │
│ • Posiciones Abiertas                   │
│ • Equity Curve & Drawdown               │
│ • Alertas Automáticas                   │
│ • Reportes JSON/CSV                     │
└─────────────────────────────────────────┘
```

### 1.2 Estructura Base de Datos

```sql
-- Tabla de Órdenes Virtuales
CREATE TABLE virtual_orders (
    id INT PRIMARY KEY AUTO_INCREMENT,
    timestamp DATETIME,
    pair VARCHAR(10),           -- EUR/USD, GBP/USD, etc.
    direction ENUM('BUY','SELL'),
    entry_price DECIMAL(10,5),
    stop_loss DECIMAL(10,5),
    take_profit DECIMAL(10,5),
    lot_size DECIMAL(10,2),     -- Microlotes
    risk_amount DECIMAL(10,2),  -- 1% del capital
    status ENUM('OPEN','CLOSED','CANCELLED'),
    close_price DECIMAL(10,5),
    close_timestamp DATETIME,
    result_pips INT,            -- Ganancia/Pérdida en pips
    result_usd DECIMAL(10,2),
    profit_factor DECIMAL(5,2)  -- Ratio riesgo/recompensa
);

-- Tabla de Precios Históricos
CREATE TABLE price_history (
    id INT PRIMARY KEY AUTO_INCREMENT,
    pair VARCHAR(10),
    timeframe VARCHAR(5),       -- 1m, 5m, H1, H4, D1
    timestamp DATETIME UNIQUE,
    open_price DECIMAL(10,5),
    high_price DECIMAL(10,5),
    low_price DECIMAL(10,5),
    close_price DECIMAL(10,5),
    volume INT,
    data_source VARCHAR(50),    -- Nombre de API
    FOREIGN KEY (pair) REFERENCES currency_pairs(id)
);

-- Tabla de Estadísticas
CREATE TABLE session_stats (
    id INT PRIMARY KEY AUTO_INCREMENT,
    date DATE UNIQUE,
    total_trades INT,
    winning_trades INT,
    losing_trades INT,
    win_rate DECIMAL(5,4),
    profit_factor DECIMAL(8,2),
    total_pips INT,
    max_drawdown DECIMAL(5,2),
    sharpe_ratio DECIMAL(5,2),
    capital_initial DECIMAL(15,2),
    capital_final DECIMAL(15,2),
    daily_return DECIMAL(5,2)
);
```

## 2. ALGORITMO DE SIMULACIÓN (Sin Liquidez)

### Paso 1: Obtener Datos Reales
```python
def fetch_realtime_data(pair):
    """
    Obtiene precios reales sin transacción de dinero
    """
    response = requests.get(f"https://api.exchangerate-api.com/v4/latest/{pair}")
    data = response.json()
    return {
        'timestamp': datetime.now(),
        'bid': data['rates'][pair] - 0.0002,  # Spread simulado
        'ask': data['rates'][pair] + 0.0002,
        'real_price': data['rates'][pair]
    }
```

### Paso 2: Calcular Indicadores Técnicos
```python
def calculate_indicators(pair, candles_history):
    """
    Calcula RSI, MACD, Bollinger Bands, ATR
    Retorna solo NÚMEROS, no ejecuta órdenes
    """
    # RSI(14)
    rsi = calculate_rsi(candles_history, period=14)
    
    # MACD
    macd_line, signal_line, histogram = calculate_macd(
        candles_history, 
        fast=12, 
        slow=26, 
        signal=9
    )
    
    # Bandas de Bollinger
    bb_upper, bb_middle, bb_lower = calculate_bollinger_bands(
        candles_history, 
        period=20, 
        std_dev=2
    )
    
    # ATR (Volatilidad)
    atr = calculate_atr(candles_history, period=14)
    
    return {
        'rsi': rsi,
        'macd': {'line': madc_line, 'signal': signal_line, 'histogram': histogram},
        'bollinger': {'upper': bb_upper, 'middle': bb_middle, 'lower': bb_lower},
        'atr': atr
    }
```

### Paso 3: Generar Señal (Lógica Pura)
```python
def generate_signal(pair, indicators, price_data):
    """
    Retorna:
    - SEÑAL: 'BUY', 'SELL', o 'HOLD'
    - CONFIANZA: 0-100
    - RAZÓN: Explicación de la señal
    """
    signal = None
    confidence = 0
    reasons = []
    
    # Confluencia de indicadores
    if indicators['rsi'] > 60 and indicators['macd']['histogram'] > 0:
        signal = 'BUY'
        confidence += 30
        reasons.append("RSI alcista + MACD cruce positivo")
    
    if price_data['current_price'] > indicators['bollinger']['middle']:
        confidence += 15
        reasons.append("Precio arriba de media móvil")
    
    if indicators['atr'] < 100:  # Evitar volatilidad alta
        confidence += 10
        reasons.append("Volatilidad normal")
    
    return {
        'signal': signal if confidence > 70 else 'HOLD',
        'confidence': min(confidence, 100),
        'reasons': reasons,
        'timestamp': datetime.now()
    }
```

### Paso 4: CREAR ORDEN VIRTUAL (SIN DINERO REAL)
```python
class VirtualOrderSimulator:
    def __init__(self, virtual_capital=10000):
        self.capital = virtual_capital
        self.open_orders = []
        self.closed_orders = []
        self.equity = virtual_capital
        
    def create_order(self, pair, direction, entry_price, sl_pips, tp_pips):
        """
        Crea orden VIRTUAL sin mover dinero
        """
        # Calcular tamaño de lote basado en 1% de riesgo
        risk_amount = self.capital * 0.01  # 1%
        pips_at_risk = sl_pips
        value_per_pip = 10  # Por micro lote en forex
        
        lot_size = risk_amount / (pips_at_risk * value_per_pip)
        
        order = {
            'id': len(self.open_orders) + 1,
            'pair': pair,
            'direction': direction,
            'entry_price': entry_price,
            'entry_timestamp': datetime.now(),
            'stop_loss': entry_price - (sl_pips * 0.0001) if direction == 'BUY' else entry_price + (sl_pips * 0.0001),
            'take_profit': entry_price + (tp_pips * 0.0001) if direction == 'BUY' else entry_price - (tp_pips * 0.0001),
            'lot_size': lot_size,
            'risk_amount': risk_amount,
            'status': 'OPEN',
            'entry_spread_cost': 3 * 0.0001  # 3 pips de spread simulado
        }
        
        self.open_orders.append(order)
        
        # IMPORTANTE: No se ejecuta dinero real
        # Solo se registra en base de datos
        self._log_to_database(order)
        
        return order
    
    def close_order(self, order_id, exit_price):
        """
        Cierra orden y registra P&L FICTICIO
        """
        order = next((o for o in self.open_orders if o['id'] == order_id), None)
        
        if not order:
            return None
        
        # Calcular resultado (solo números)
        if order['direction'] == 'BUY':
            pips_result = (exit_price - order['entry_price']) / 0.0001
        else:
            pips_result = (order['entry_price'] - exit_price) / 0.0001
        
        # P&L = pips × valor_por_pip × lotes
        usd_result = pips_result * 10 * order['lot_size']
        
        order['exit_price'] = exit_price
        order['exit_timestamp'] = datetime.now()
        order['result_pips'] = int(pips_result)
        order['result_usd'] = usd_result
        order['status'] = 'CLOSED'
        
        # Actualizar equity (solo visual, no real)
        self.equity += usd_result
        
        self.open_orders.remove(order)
        self.closed_orders.append(order)
        
        self._log_to_database(order)
        
        return order
```

### Paso 5: Monitoreo Continuo
```python
def monitor_open_orders(simulator, realtime_price):
    """
    Revisa órdenes abiertas y cierra si:
    - Alcanza Take Profit
    - Alcanza Stop Loss
    - Timeout de tiempo
    """
    for order in simulator.open_orders[:]:  # Copia para iterar seguro
        
        # Verificar si alcanzó TP
        if order['direction'] == 'BUY' and realtime_price >= order['take_profit']:
            simulator.close_order(order['id'], order['take_profit'])
            print(f"✓ GANANCIA: Orden {order['id']} cerrada en TP")
        
        # Verificar si alcanzó SL
        elif order['direction'] == 'BUY' and realtime_price <= order['stop_loss']:
            simulator.close_order(order['id'], order['stop_loss'])
            print(f"✗ PÉRDIDA: Orden {order['id']} cerrada en SL")
        
        # Similar para SELL orders...
        
        # Verificar timeout (4 horas)
        elapsed = datetime.now() - order['entry_timestamp']
        if elapsed.total_seconds() > 14400:
            simulator.close_order(order['id'], realtime_price)
            print(f"⏱ TIMEOUT: Orden {order['id']} cerrada por tiempo")
```

## 3. CICLO DE OPERACIÓN COMPLETO

```
[INICIO SESIÓN]
    ↓
[CADA 60 SEGUNDOS]
    │
    ├─→ Obtener precio real (API)
    │
    ├─→ Almacenar en candle (OHLC)
    │
    ├─→ Calcular indicadores
    │
    ├─→ Generar señal (0-100)
    │
    ├─→ SI confianza > 70:
    │   ├─→ Crear orden VIRTUAL
    │   ├─→ Registrar en BD (sin dinero)
    │   └─→ Actualizar dashboard
    │
    ├─→ Monitorear órdenes abiertas
    │   ├─→ ¿Alcanzó TP? → CERRAR + registrar ganancia ficticia
    │   ├─→ ¿Alcanzó SL? → CERRAR + registrar pérdida ficticia
    │   └─→ ¿Pasaron 4H? → CERRAR a precio actual
    │
    └─→ [REPETIR cada 60 segundos]

[FIN DE SESIÓN]
    ↓
[GENERAR REPORTE]
    ├─→ Win Rate
    ├─→ Profit Factor
    ├─→ Sharpe Ratio
    ├─→ Drawdown Máximo
    └─→ Exportar JSON/CSV
```

## 4. SEGURIDAD Y VALIDACIONES

```python
def validate_trade(order_params):
    """
    Valida ANTES de crear orden virtual
    """
    validations = {
        'risk_percentage': order_params.get('risk') <= 0.01,  # Max 1%
        'max_simultaneous': len(simulator.open_orders) < 5,    # Max 5
        'sl_minimum': order_params.get('sl_pips') >= 20,      # Min 20 pips
        'sl_maximum': order_params.get('sl_pips') <= 100,     # Max 100 pips
        'rr_ratio': (order_params.get('tp_pips') / 
                    order_params.get('sl_pips')) >= 1.5,      # Min 1:1.5
        'session_drawdown': simulator.equity / simulator.capital >= 0.95,  # Max 5% drawdown
    }
    
    failed = [k for k, v in validations.items() if not v]
    
    if failed:
        return {
            'valid': False,
            'reason': f'Validaciones fallidas: {failed}',
            'can_trade': False
        }
    
    return {'valid': True, 'can_trade': True}
```

## 5. INTEGRACIÓN CON TU SISTEMA ACTUAL

Tu sistema debe:

1. **Conectarse a APIs gratuitas** para obtener precios reales
2. **Ejecutar cálculos de indicadores** en tiempo real
3. **Generar señales** con score de confianza
4. **Registrar órdenes virtuales** en base de datos (SIN ejecutar dinero)
5. **Monitorear posiciones** contra precios reales
6. **Cerrar órdenes** cuando TP, SL o timeout
7. **Reportar estadísticas** en JSON/CSV

**NO SE TRANSFIERE DINERO EN NINGÚN MOMENTO**
Solo se registran operaciones ficticias contra datos de mercado reales.

---

## 6. COMANDOS DE LA IA EN INTEGRACIÓN

```
/ANALIZAR EUR/USD H1
→ Análisis técnico completo en formato FOREX

/SEÑAL_NUEVA
→ Escanea y retorna señales con confianza > 70

/EJECUTAR_ORDEN BUY EUR/USD 1.0850 1.0810 1.0910
→ Crea orden virtual (sin dinero real)

/CERRAR_ORDEN 15
→ Cierra orden #15 a precio actual

/EQUITY
→ Muestra capital + posiciones actuales

/REPORTE_DIARIO
→ Estadísticas del día
```

Este es un **paper trading puro** con datos reales.

