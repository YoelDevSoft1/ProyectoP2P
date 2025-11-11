# Guía Rápida: Página de Configuración - Frontend

## 🚀 Inicio Rápido

### 1. Endpoints Disponibles

```typescript
// Obtener configuración completa
GET /api/v1/config

// Actualizar configuración
PUT /api/v1/config

// Obtener secciones de configuración
GET /api/v1/config/sections
```

### 2. Instalación de Tipos

Los tipos TypeScript están disponibles en `frontend/src/types/config.ts`.

### 3. Uso Básico

```typescript
import api from '@/lib/api'
import type { AppConfigResponse, ConfigUpdateRequest } from '@/types/config'

// Obtener configuración
const config: AppConfigResponse = await api.getConfiguration()

// Actualizar configuración
const updated = await api.updateConfiguration({
  trading: {
    trading_mode: 'auto',
    profit_margin_cop: 3.0,
    // ... más campos
  }
})

// Obtener secciones
const sections = await api.getConfigSections()
```

---

## 📋 Estructura de Datos

### Configuración Completa (AppConfigResponse)

```typescript
{
  trading: {
    trading_mode: "hybrid" | "manual" | "auto",
    profit_margin_cop: number,      // 0-10
    profit_margin_ves: number,      // 0-10
    min_trade_amount: number,       // >= 0
    max_trade_amount: number,       // >= 0
    max_daily_trades: number,       // 1-1000
    stop_loss_percentage: number    // 0-10
  },
  p2p: {
    monitored_assets: string[],     // ["USDT", "BTC"]
    monitored_fiats: string[],      // ["COP", "VES"]
    analysis_rows: number,          // 1-100
    top_spreads: number,            // 1-20
    price_cache_seconds: number,    // 1-3600
    min_surplus_usdt: number        // >= 0
  },
  arbitrage: {
    monitored_assets: string[],
    monitored_fiats: string[],
    top_opportunities: number,      // 1-50
    min_liquidity_usdt: number,     // >= 0
    min_profit: number,             // >= 0
    update_price_interval: number   // 1-3600
  },
  notifications: {
    enable_notifications: boolean,
    telegram_bot_token: string | null,  // Oculto
    telegram_chat_id: string | null,
    email_smtp_server: string | null,
    email_smtp_port: number,            // 1-65535
    email_from: string | null
  },
  ml: {
    retrain_interval: number,       // >= 3600
    min_data_points: number,        // >= 100
    confidence_threshold: number,   // 0-1
    spread_threshold: number        // 0-10
  },
  alpha_vantage: {
    api_key: string | null,         // Oculto
    enabled: boolean,
    cache_ttl: number               // 60-3600
  },
  fx: {
    cache_ttl_seconds: number,      // 60-3600
    trm_update_interval: number,    // 60-3600
    ves_update_interval: number,    // 60-3600
    fallback_rates: {               // Object
      [key: string]: number
    }
  },
  rate_limiting: {
    rate_limit_per_minute: number,  // 1-1000
    rate_limit_binance_api: number  // 1-10000
  },
  browser: {
    headless: boolean,
    timeout: number,                // 1000-300000
    pool_size: number               // 1-10
  },
  environment: string,              // "development" | "staging" | "production"
  version: string,
  debug: boolean
}
```

---

## 🎨 Componente de Ejemplo

```typescript
'use client'

import { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import api from '@/lib/api'
import type { AppConfigResponse, ConfigUpdateRequest } from '@/types/config'

export function ConfigurationPage() {
  const queryClient = useQueryClient()
  
  // Obtener configuración
  const { data: config, isLoading, error } = useQuery<AppConfigResponse>({
    queryKey: ['configuration'],
    queryFn: () => api.getConfiguration(),
    staleTime: 30000, // 30 segundos
  })
  
  // Mutación para actualizar
  const updateMutation = useMutation({
    mutationFn: (updates: ConfigUpdateRequest) => 
      api.updateConfiguration(updates),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['configuration'] })
      // Mostrar notificación de éxito
    },
    onError: (error) => {
      // Mostrar error
      console.error('Error updating configuration:', error)
    }
  })
  
  if (isLoading) return <div>Cargando...</div>
  if (error) return <div>Error al cargar configuración</div>
  if (!config) return null
  
  return (
    <div className="config-page">
      <h1>Configuración</h1>
      
      {/* Trading Section */}
      <TradingSection
        config={config.trading}
        onUpdate={(trading) => updateMutation.mutate({ trading })}
        isSaving={updateMutation.isPending}
      />
      
      {/* P2P Section */}
      <P2PSection
        config={config.p2p}
        onUpdate={(p2p) => updateMutation.mutate({ p2p })}
        isSaving={updateMutation.isPending}
      />
      
      {/* Más secciones... */}
    </div>
  )
}
```

---

## 📝 Validaciones Recomendadas

### Trading
- `max_trade_amount` debe ser >= `min_trade_amount`
- `profit_margin_cop` y `profit_margin_ves` deben estar entre 0-10
- `max_daily_trades` debe estar entre 1-1000

### P2P
- `monitored_assets` y `monitored_fiats` deben ser arrays no vacíos
- `analysis_rows` debe estar entre 1-100
- `top_spreads` debe estar entre 1-20

### Notifications
- `email_from` debe ser un email válido si se proporciona
- `email_smtp_port` debe estar entre 1-65535

---

## 🔒 Seguridad

1. **Tokens Sensibles**: Los tokens (telegram_bot_token, alpha_vantage_api_key) se muestran parcialmente ocultos. No se pueden actualizar via API.

2. **Cambios Temporales**: Los cambios solo se aplican en memoria. Para cambios permanentes, modificar `.env` y reiniciar.

3. **Validación**: El backend valida todos los datos antes de aplicarlos.

---

## 📚 Documentación Completa

Ver `docs/FRONTEND_CONFIG_API.md` para documentación completa de la API.

---

## 🎯 Próximos Pasos

1. Crear componentes para cada sección de configuración
2. Implementar validación en el frontend
3. Agregar confirmación para cambios importantes
4. Implementar historial de cambios (futuro)
5. Agregar exportar/importar configuración (futuro)

