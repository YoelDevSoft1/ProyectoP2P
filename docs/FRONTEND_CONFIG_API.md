# API de Configuración - Documentación para Frontend

## 📋 Índice

1. [Resumen](#resumen)
2. [Endpoints](#endpoints)
3. [Estructuras de Datos](#estructuras-de-datos)
4. [Ejemplos de Uso](#ejemplos-de-uso)
5. [Validaciones](#validaciones)
6. [Notas de Seguridad](#notas-de-seguridad)

---

## 📖 Resumen

La API de configuración permite leer y actualizar la configuración de la aplicación. Los cambios se aplican en memoria durante la ejecución. Para cambios permanentes, se debe modificar el archivo `.env` y reiniciar el servidor.

**Base URL**: `/api/v1/config`

---

## 🔌 Endpoints

### 1. Obtener Configuración Completa

**GET** `/api/v1/config`

Obtiene toda la configuración actual de la aplicación.

**Respuesta**: `AppConfigResponse`

**Ejemplo de respuesta**:
```json
{
  "trading": {
    "trading_mode": "hybrid",
    "profit_margin_cop": 2.5,
    "profit_margin_ves": 3.0,
    "min_trade_amount": 50.0,
    "max_trade_amount": 1000.0,
    "max_daily_trades": 50,
    "stop_loss_percentage": 1.5
  },
  "p2p": {
    "monitored_assets": ["USDT", "BTC"],
    "monitored_fiats": ["COP", "VES", "BRL", "ARS"],
    "analysis_rows": 20,
    "top_spreads": 3,
    "price_cache_seconds": 30,
    "min_surplus_usdt": 50.0
  },
  "arbitrage": {
    "monitored_assets": ["USDT", "BTC", "ETH"],
    "monitored_fiats": ["COP", "VES", "BRL", "ARS"],
    "top_opportunities": 5,
    "min_liquidity_usdt": 100.0,
    "min_profit": 1.0,
    "update_price_interval": 10
  },
  "notifications": {
    "enable_notifications": true,
    "telegram_bot_token": "12345678...",
    "telegram_chat_id": "123456789",
    "email_smtp_server": "smtp.gmail.com",
    "email_smtp_port": 587,
    "email_from": "user@example.com"
  },
  "ml": {
    "retrain_interval": 86400,
    "min_data_points": 1000,
    "confidence_threshold": 0.75,
    "spread_threshold": 0.5
  },
  "alpha_vantage": {
    "api_key": "A828MZ96...",
    "enabled": true,
    "cache_ttl": 900
  },
  "fx": {
    "cache_ttl_seconds": 120,
    "trm_update_interval": 300,
    "ves_update_interval": 300,
    "fallback_rates": {
      "COP": 4000.0,
      "VES": 36.5,
      "USD": 1.0,
      "BRL": 5.0,
      "ARS": 900.0,
      "CLP": 900.0,
      "PEN": 3.8,
      "MXN": 17.0
    }
  },
  "rate_limiting": {
    "rate_limit_per_minute": 60,
    "rate_limit_binance_api": 1200
  },
  "browser": {
    "headless": true,
    "timeout": 30000,
    "pool_size": 1
  },
  "environment": "development",
  "version": "1.0.0",
  "debug": true
}
```

---

### 2. Actualizar Configuración

**PUT** `/api/v1/config`

Actualiza la configuración de la aplicación. Solo se actualizan las secciones que se envían en el request.

**Request Body**: `ConfigUpdateRequest`

**Ejemplo de request**:
```json
{
  "trading": {
    "trading_mode": "auto",
    "profit_margin_cop": 3.0,
    "profit_margin_ves": 3.5,
    "min_trade_amount": 100.0,
    "max_trade_amount": 2000.0,
    "max_daily_trades": 100,
    "stop_loss_percentage": 2.0
  },
  "p2p": {
    "monitored_assets": ["USDT", "BTC", "ETH"],
    "monitored_fiats": ["COP", "VES"],
    "analysis_rows": 30,
    "top_spreads": 5,
    "price_cache_seconds": 60,
    "min_surplus_usdt": 100.0
  }
}
```

**Respuesta**: `AppConfigResponse` (configuración actualizada)

**⚠️ Nota Importante**: Los cambios solo se aplican en memoria. Para cambios permanentes, modificar el archivo `.env` y reiniciar el servidor.

---

### 3. Obtener Secciones de Configuración

**GET** `/api/v1/config/sections`

Obtiene la lista de secciones de configuración disponibles con sus metadatos. Útil para construir la UI dinámicamente.

**Respuesta**:
```json
{
  "sections": [
    {
      "id": "trading",
      "name": "Trading",
      "description": "Configuración de trading y márgenes de ganancia",
      "icon": "💰",
      "fields": [
        "trading_mode",
        "profit_margin_cop",
        "profit_margin_ves",
        "min_trade_amount",
        "max_trade_amount",
        "max_daily_trades",
        "stop_loss_percentage"
      ]
    },
    {
      "id": "p2p",
      "name": "P2P",
      "description": "Configuración de monitoreo P2P",
      "icon": "🔄",
      "fields": [
        "monitored_assets",
        "monitored_fiats",
        "analysis_rows",
        "top_spreads",
        "price_cache_seconds",
        "min_surplus_usdt"
      ]
    }
    // ... más secciones
  ]
}
```

---

## 📊 Estructuras de Datos

### TradingConfig

```typescript
interface TradingConfig {
  trading_mode: "manual" | "auto" | "hybrid";
  profit_margin_cop: number;  // 0-10 (%)
  profit_margin_ves: number;  // 0-10 (%)
  min_trade_amount: number;   // >= 0 (USD)
  max_trade_amount: number;   // >= 0 (USD)
  max_daily_trades: number;   // 1-1000
  stop_loss_percentage: number; // 0-10 (%)
}
```

### P2PConfig

```typescript
interface P2PConfig {
  monitored_assets: string[];  // ej: ["USDT", "BTC"]
  monitored_fiats: string[];   // ej: ["COP", "VES"]
  analysis_rows: number;       // 1-100
  top_spreads: number;         // 1-20
  price_cache_seconds: number; // 1-3600
  min_surplus_usdt: number;    // >= 0
}
```

### ArbitrageConfig

```typescript
interface ArbitrageConfig {
  monitored_assets: string[];
  monitored_fiats: string[];
  top_opportunities: number;     // 1-50
  min_liquidity_usdt: number;    // >= 0
  min_profit: number;            // >= 0 (%)
  update_price_interval: number; // 1-3600 (segundos)
}
```

### NotificationConfig

```typescript
interface NotificationConfig {
  enable_notifications: boolean;
  telegram_bot_token: string | null;  // Oculto: solo se muestra "12345678..."
  telegram_chat_id: string | null;
  email_smtp_server: string | null;
  email_smtp_port: number;            // 1-65535
  email_from: string | null;
}
```

### MLConfig

```typescript
interface MLConfig {
  retrain_interval: number;      // >= 3600 (segundos)
  min_data_points: number;       // >= 100
  confidence_threshold: number;  // 0-1
  spread_threshold: number;      // 0-10 (%)
}
```

### AlphaVantageConfig

```typescript
interface AlphaVantageConfig {
  api_key: string | null;  // Oculto: solo se muestra "A828MZ96..."
  enabled: boolean;
  cache_ttl: number;       // 60-3600 (segundos)
}
```

### FXConfig

```typescript
interface FXConfig {
  cache_ttl_seconds: number;    // 60-3600
  trm_update_interval: number;  // 60-3600
  ves_update_interval: number;  // 60-3600
  fallback_rates: {
    [key: string]: number;  // ej: { "COP": 4000.0, "VES": 36.5 }
  };
}
```

### RateLimitConfig

```typescript
interface RateLimitConfig {
  rate_limit_per_minute: number;     // 1-1000
  rate_limit_binance_api: number;    // 1-10000
}
```

### BrowserConfig

```typescript
interface BrowserConfig {
  headless: boolean;
  timeout: number;        // 1000-300000 (ms)
  pool_size: number;      // 1-10
}
```

### AppConfigResponse

```typescript
interface AppConfigResponse {
  trading: TradingConfig;
  p2p: P2PConfig;
  arbitrage: ArbitrageConfig;
  notifications: NotificationConfig;
  ml: MLConfig;
  alpha_vantage: AlphaVantageConfig;
  fx: FXConfig;
  rate_limiting: RateLimitConfig;
  browser: BrowserConfig;
  environment: string;    // "development" | "staging" | "production"
  version: string;
  debug: boolean;
}
```

### ConfigUpdateRequest

```typescript
interface ConfigUpdateRequest {
  trading?: TradingConfig;
  p2p?: P2PConfig;
  arbitrage?: ArbitrageConfig;
  notifications?: NotificationConfig;
  ml?: MLConfig;
  alpha_vantage?: AlphaVantageConfig;
  fx?: FXConfig;
  rate_limiting?: RateLimitConfig;
  browser?: BrowserConfig;
}
```

---

## 💡 Ejemplos de Uso

### TypeScript/React Example

```typescript
import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Obtener configuración
export async function getConfiguration() {
  const response = await axios.get(`${API_BASE_URL}/api/v1/config`);
  return response.data;
}

// Actualizar configuración
export async function updateConfiguration(config: ConfigUpdateRequest) {
  const response = await axios.put(`${API_BASE_URL}/api/v1/config`, config);
  return response.data;
}

// Obtener secciones
export async function getConfigSections() {
  const response = await axios.get(`${API_BASE_URL}/api/v1/config/sections`);
  return response.data;
}

// Ejemplo de uso en componente React
function ConfigurationPage() {
  const [config, setConfig] = useState<AppConfigResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadConfig() {
      try {
        const data = await getConfiguration();
        setConfig(data);
      } catch (error) {
        console.error('Error loading configuration:', error);
      } finally {
        setLoading(false);
      }
    }
    loadConfig();
  }, []);

  const handleUpdate = async (updates: ConfigUpdateRequest) => {
    try {
      const updated = await updateConfiguration(updates);
      setConfig(updated);
      alert('Configuración actualizada exitosamente');
    } catch (error) {
      console.error('Error updating configuration:', error);
      alert('Error al actualizar configuración');
    }
  };

  if (loading) return <div>Cargando...</div>;
  if (!config) return <div>Error al cargar configuración</div>;

  return (
    <div>
      <TradingConfigSection
        config={config.trading}
        onUpdate={(trading) => handleUpdate({ trading })}
      />
      <P2PConfigSection
        config={config.p2p}
        onUpdate={(p2p) => handleUpdate({ p2p })}
      />
      {/* ... más secciones */}
    </div>
  );
}
```

---

## ✅ Validaciones

### Trading
- `trading_mode`: Debe ser "manual", "auto" o "hybrid"
- `profit_margin_cop`: 0-10 (%)
- `profit_margin_ves`: 0-10 (%)
- `min_trade_amount`: >= 0 (USD)
- `max_trade_amount`: >= 0 (USD), debe ser >= min_trade_amount
- `max_daily_trades`: 1-1000
- `stop_loss_percentage`: 0-10 (%)

### P2P
- `monitored_assets`: Array de strings (ej: ["USDT", "BTC"])
- `monitored_fiats`: Array de strings (ej: ["COP", "VES"])
- `analysis_rows`: 1-100
- `top_spreads`: 1-20
- `price_cache_seconds`: 1-3600
- `min_surplus_usdt`: >= 0

### Arbitrage
- `monitored_assets`: Array de strings
- `monitored_fiats`: Array de strings
- `top_opportunities`: 1-50
- `min_liquidity_usdt`: >= 0
- `min_profit`: >= 0 (%)
- `update_price_interval`: 1-3600 (segundos)

### Notifications
- `enable_notifications`: boolean
- `telegram_chat_id`: string | null
- `email_smtp_server`: string | null
- `email_smtp_port`: 1-65535
- `email_from`: string | null (debe ser un email válido)

### ML
- `retrain_interval`: >= 3600 (segundos)
- `min_data_points`: >= 100
- `confidence_threshold`: 0-1
- `spread_threshold`: 0-10 (%)

### Alpha Vantage
- `enabled`: boolean
- `cache_ttl`: 60-3600 (segundos)
- `api_key`: string | null (no se actualiza via API por seguridad)

### FX
- `cache_ttl_seconds`: 60-3600
- `trm_update_interval`: 60-3600
- `ves_update_interval`: 60-3600
- `fallback_rates`: Object con tasas de cambio (números positivos)

### Rate Limiting
- `rate_limit_per_minute`: 1-1000
- `rate_limit_binance_api`: 1-10000

### Browser
- `headless`: boolean
- `timeout`: 1000-300000 (ms)
- `pool_size`: 1-10

---

## 🔒 Notas de Seguridad

1. **Tokens y Contraseñas**: Los tokens sensibles (como `telegram_bot_token` y `alpha_vantage_api_key`) se muestran parcialmente ocultos (solo los primeros 8 caracteres). No se pueden actualizar via API por seguridad.

2. **Cambios Temporales**: Los cambios realizados via API solo se aplican en memoria durante la ejecución del servidor. Para cambios permanentes, se debe modificar el archivo `.env` y reiniciar el servidor.

3. **Validación**: Todas las actualizaciones son validadas antes de aplicarse. Si una validación falla, se retorna un error 422 (Unprocessable Entity).

4. **Logging**: Todas las actualizaciones de configuración se registran en los logs del servidor.

5. **Permisos**: En el futuro, se implementará un sistema de permisos para restringir quién puede actualizar la configuración.

---

## 🎨 Recomendaciones para el Frontend

1. **UI por Secciones**: Usa el endpoint `/config/sections` para construir la UI dinámicamente.

2. **Validación en Cliente**: Implementa validación en el frontend antes de enviar los datos al backend para mejorar la UX.

3. **Feedback Visual**: Muestra mensajes claros cuando se actualiza la configuración exitosamente o cuando hay errores.

4. **Campos Sensibles**: Para campos sensibles (tokens), muestra un input de tipo "password" y permite actualizarlos solo si el usuario confirma (con una acción separada).

5. **Confirmación**: Para cambios importantes (como cambiar el modo de trading), solicita confirmación al usuario.

6. **Dirty State**: Mantén un estado "dirty" para saber qué secciones han sido modificadas y necesitan guardarse.

7. **Reset**: Proporciona una opción para resetear los cambios a los valores por defecto.

8. **Help Text**: Muestra ayuda contextual para cada campo explicando qué hace y cuáles son los valores recomendados.

---

## 📝 Ejemplo Completo de Componente React

```typescript
import { useState, useEffect } from 'react';
import { getConfiguration, updateConfiguration, getConfigSections } from '@/lib/api/config';

interface ConfigPageProps {
  // props
}

export function ConfigPage({}: ConfigPageProps) {
  const [config, setConfig] = useState<AppConfigResponse | null>(null);
  const [sections, setSections] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [dirty, setDirty] = useState<Set<string>>(new Set());
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    async function load() {
      try {
        const [configData, sectionsData] = await Promise.all([
          getConfiguration(),
          getConfigSections(),
        ]);
        setConfig(configData);
        setSections(sectionsData.sections);
      } catch (error) {
        console.error('Error loading configuration:', error);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  const handleUpdate = async (sectionId: string, sectionData: any) => {
    setSaving(true);
    try {
      const updates = { [sectionId]: sectionData };
      const updated = await updateConfiguration(updates);
      setConfig(updated);
      setDirty((prev) => {
        const next = new Set(prev);
        next.delete(sectionId);
        return next;
      });
      alert('Configuración actualizada exitosamente');
    } catch (error) {
      console.error('Error updating configuration:', error);
      alert('Error al actualizar configuración');
    } finally {
      setSaving(false);
    }
  };

  const markDirty = (sectionId: string) => {
    setDirty((prev) => new Set(prev).add(sectionId));
  };

  if (loading) {
    return <div>Cargando configuración...</div>;
  }

  if (!config) {
    return <div>Error al cargar configuración</div>;
  }

  return (
    <div className="config-page">
      <h1>Configuración de la Aplicación</h1>
      
      {sections.map((section) => (
        <ConfigSection
          key={section.id}
          section={section}
          data={config[section.id]}
          dirty={dirty.has(section.id)}
          onUpdate={(data) => handleUpdate(section.id, data)}
          onDirty={() => markDirty(section.id)}
        />
      ))}
      
      {dirty.size > 0 && (
        <div className="dirty-warning">
          Tienes cambios sin guardar en {dirty.size} sección(es)
        </div>
      )}
    </div>
  );
}
```

---

## 🚀 Próximos Pasos

1. Implementar persistencia en base de datos para cambios permanentes
2. Agregar sistema de permisos
3. Implementar historial de cambios
4. Agregar validación avanzada
5. Implementar rollback de configuraciones
6. Agregar exportar/importar configuración

---

## 📞 Soporte

Para preguntas o problemas, contactar al equipo de backend o revisar la documentación de la API en `/api/v1/docs`.

